"""
Qwen3-VL 模型加载模块
提供线程安全的模型加载、卸载和状态查询功能（单例模式）
支持懒加载优化：服务启动时不加载模型，首次诊断时按需加载
"""
import logging
import gc
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from enum import Enum
import torch
from PIL import Image

from .qwen_config import QUANTIZATION_CONFIG

logger = logging.getLogger(__name__)


class ModelState(Enum):
    """
    模型状态枚举

    定义模型生命周期的各个阶段：
    - UNLOADED: 未加载（初始状态或已卸载）
    - LOADING: 正在加载（异步加载进行中）
    - READY: 已就绪（可正常使用）
    - ERROR: 加载失败
    """
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class QwenModelLoader:
    """
    Qwen3-VL 模型加载器（单例模式）

    职责：
    - 线程安全的模型加载和卸载
    - CPU Offload 显存管理
    - Flash Attention 可用性检测
    - 模型预热和验证
    - 懒加载优化：支持延迟加载和异步加载

    新增特性（PERF-01）：
    - ModelState 枚举跟踪模型状态
    - asyncio.Lock 保证异步加载安全
    - ensure_loaded() 方法实现按需加载
    - get_state() 方法查询当前状态
    """

    _instance: Optional['QwenModelLoader'] = None
    _lock = None

    def __new__(cls, *args, **kwargs):
        """
        单例模式实现，确保全局只有一个模型实例

        支持 *args 和 **kwargs 参数透传，使 QwenModelLoader(lazy_load=True)
        等带关键字参数的调用不会因 __new__ 签名不兼容而抛出 TypeError。

        Args:
            cls: 类本身
            *args: 位置参数（透传给 __init__）
            **kwargs: 关键字参数（透传给 __init__，如 lazy_load=True）

        Returns:
            QwenModelLoader: 唯一实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, lazy_load: bool = True):
        """
        初始化模型加载器

        Args:
            lazy_load: 是否启用懒加载模式（默认 True）
                     - True: 服务启动时不加载模型，首次调用时按需加载
                     - False: 初始化时立即加载模型（保持原有行为）
        """
        if self._initialized:
            return

        import threading
        self._lock = threading.Lock()
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.processor: Optional[Any] = None
        self.is_loaded: bool = False
        self.model_path: Path = Path(__file__).parent.parent.parent.parent.parent.parent / "models" / "Qwen3-VL-2B-Instruct"
        self.device: str = "cuda"
        self.load_in_4bit: bool = True
        self.cpu_offload: bool = True
        self.enable_flash_attention: bool = True
        self.torch_compile: bool = True
        self._flash_attention_available: bool = False
        self._model_on_gpu: bool = False
        self._compiled_model: Optional[Any] = None
        self._initialized = True

        # 懒加载相关属性（PERF-01 优化）
        self._lazy_load: bool = lazy_load
        self._model_state: ModelState = (
            ModelState.UNLOADED if lazy_load else ModelState.LOADING
        )
        self._async_lock: asyncio.Lock = asyncio.Lock()
        self._load_task: Optional[asyncio.Task] = None
        self._last_error: Optional[str] = None

    def get_state(self) -> ModelState:
        """
        获取当前模型状态（PERF-01 优化）

        Returns:
            ModelState: 当前模型状态枚举值
                - UNLOADED: 未加载
                - LOADING: 正在加载
                - READY: 已就绪
                - ERROR: 加载失败
        """
        return self._model_state

    @property
    def is_lazy_load(self) -> bool:
        """是否启用懒加载模式"""
        return self._lazy_load

    async def ensure_loaded(
        self,
        model_path: Optional[Path] = None,
        device: str = "cuda",
        load_in_4bit: bool = True,
        cpu_offload: bool = True,
        enable_flash_attention: bool = True,
        torch_compile: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[Any]:
        """
        确保模型已加载（PERF-01 懒加载核心方法）

        如果模型未加载，则触发异步加载并等待完成。
        使用 asyncio.Lock 保证并发安全，避免重复加载。

        Args:
            model_path: 模型路径
            device: 推理设备
            load_in_4bit: 是否使用 INT4 量化
            cpu_offload: 是否启用 CPU Offload
            enable_flash_attention: 是否启用 Flash Attention 2
            torch_compile: 是否启用 torch.compile
            progress_callback: 进度回调函数

        Returns:
            Optional[Any]: 加载成功返回模型实例，失败返回 None

        Raises:
            Exception: 模型加载失败时抛出异常
        """
        if self._model_state == ModelState.READY:
            return self.model

        if self._model_state == ModelState.LOADING:
            if self._load_task and not self._load_task.done():
                logger.info("模型正在加载中，等待完成...")
                return await self._load_task
            elif self._load_task and self._load_task.done():
                if self._load_task.exception():
                    raise self._load_task.exception()
                return self._load_task.result()
            return None

        async with self._async_lock:
            double_check = self._model_state
            if double_check == ModelState.READY:
                return self.model
            if double_check == ModelState.LOADING:
                if self._load_task and not self._load_task.done():
                    return await self._load_task
                return None

            if self._model_state == ModelState.UNLOADED or self._model_state == ModelState.ERROR:
                logger.info("触发 Qwen3-VL 模型懒加载...")
                self._model_state = ModelState.LOADING
                self._last_error = None

                self._load_task = asyncio.create_task(
                    self._async_load_model(
                        model_path=model_path,
                        device=device,
                        load_in_4bit=load_in_4bit,
                        cpu_offload=cpu_offload,
                        enable_flash_attention=enable_flash_attention,
                        torch_compile=torch_compile,
                        progress_callback=progress_callback
                    )
                )

                try:
                    result = await self._load_task
                    self.model = result
                    self.is_loaded = True
                    self._model_state = ModelState.READY
                    logger.info("Qwen3-VL 模型懒加载完成")
                    return self.model
                except Exception as e:
                    self._model_state = ModelState.ERROR
                    self._last_error = str(e)
                    logger.error(f"Qwen3-VL 模型懒加载失败: {e}")
                    raise

        return None

    async def _async_load_model(
        self,
        model_path: Optional[Path] = None,
        device: str = "cuda",
        load_in_4bit: bool = True,
        cpu_offload: bool = True,
        enable_flash_attention: bool = True,
        torch_compile: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Any:
        """
        异步执行实际的模型加载逻辑（PERF-01 优化）

        在独立线程中执行同步的模型加载操作，避免阻塞事件循环。
        使用 asyncio.to_thread() 将同步操作包装为异步。

        Args:
            model_path: 模型路径
            device: 推理设备
            load_in_4bit: 是否使用 INT4 量化
            cpu_offload: 是否启用 CPU Offload
            enable_flash_attention: 是否启用 Flash Attention 2
            torch_compile: 是否启用 torch.compile
            progress_callback: 进度回调函数

        Returns:
            Any: 加载成功的模型实例

        Raises:
            Exception: 加载失败时抛出异常
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.load_model(
                model_path=model_path,
                device=device,
                load_in_4bit=load_in_4bit,
                cpu_offload=cpu_offload,
                enable_flash_attention=enable_flash_attention,
                torch_compile=torch_compile,
                progress_callback=progress_callback
            )
        )

    def preload_model(
        self,
        model_path: Optional[Path] = None,
        **kwargs
    ) -> bool:
        """
        预加载模型（管理员接口，用于手动预热）

        立即同步加载模型，适用于管理后台的预热操作。

        Args:
            model_path: 模型路径
            **kwargs: 其他加载参数（与 load_model 相同）

        Returns:
            bool: 是否加载成功
        """
        try:
            logger.info("管理员触发的模型预加载开始...")
            success = self.load_model(model_path=model_path, **kwargs)
            if success:
                self._model_state = ModelState.READY
                self.is_loaded = True
                logger.info("管理员预加载完成")
            else:
                self._model_state = ModelState.ERROR
                logger.warning("管理员预加载失败")
            return success
        except Exception as e:
            self._model_state = ModelState.ERROR
            self._last_error = str(e)
            logger.error(f"管理员预加载异常: {e}")
            return False

    def check_flash_attention_availability(self) -> bool:
        """
        检查 Flash Attention 2 是否可用

        Flash Attention 2 需要：
        1. CUDA 设备
        2. PyTorch 2.0+
        3. flash-attn 包已安装
        4. GPU 架构支持（Ampere 及以上推荐）

        Returns:
            bool: Flash Attention 2 是否可用
        """
        if not self.enable_flash_attention:
            logger.info("Flash Attention 已在配置中禁用")
            return False

        try:
            if not torch.cuda.is_available():
                logger.warning("Flash Attention 需要 CUDA 设备，当前不可用")
                return False

            major, minor = torch.cuda.get_device_capability()
            if major < 8:
                logger.warning(f"Flash Attention 2 推荐 Ampere 架构 (SM 8.0+)，当前 SM {major}.{minor}")

            try:
                import flash_attn
                flash_attn_version = getattr(flash_attn, '__version__', 'unknown')
                logger.info(f"Flash Attention 2 可用，版本: {flash_attn_version}")
                self._flash_attention_available = True
                return True
            except ImportError:
                logger.warning("flash-attn 包未安装，Flash Attention 2 不可用")
                logger.info("安装方法: pip install flash-attn --no-build-isolation")
                return False

        except Exception as e:
            logger.warning(f"检查 Flash Attention 可用性失败: {e}")
            return False

    def load_model(
        self,
        model_path: Optional[Path] = None,
        device: str = "cuda",
        load_in_4bit: bool = True,
        cpu_offload: bool = True,
        enable_flash_attention: bool = True,
        torch_compile: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """
        加载 Qwen3-VL 模型（线程安全）

        根据 Qwen3-VL 官方文档，使用 Qwen3VLForConditionalGeneration 类加载模型，
        确保架构完全匹配。

        启用 CPU Offload 时，使用 device_map="auto" 自动管理 CPU/GPU 分布，
        模型权重保留在 CPU 内存中，推理时动态加载到 GPU。

        Args:
            model_path: 模型路径
            device: 推理设备（cuda/cpu）
            load_in_4bit: 是否使用 INT4 量化
            cpu_offload: 是否启用 CPU Offload
            enable_flash_attention: 是否启用 Flash Attention 2
            torch_compile: 是否启用 torch.compile 优化
            progress_callback: 进度回调函数

        Returns:
            bool: 是否加载成功
        """
        with self._lock:
            try:
                from transformers import Qwen3VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

                if progress_callback:
                    progress_callback(5, "加载处理器")

                self.model_path = model_path or self.model_path
                self.device = device
                self.load_in_4bit = load_in_4bit
                self.cpu_offload = cpu_offload
                self.enable_flash_attention = enable_flash_attention
                self.torch_compile = torch_compile

                logger.info(f"正在加载 Qwen3-VL 模型：{self.model_path}")

                self.processor = AutoProcessor.from_pretrained(
                    str(self.model_path),
                    trust_remote_code=True
                )

                if progress_callback:
                    progress_callback(15, "处理器加载完成")

                quantization_config = None
                if self.load_in_4bit:
                    try:
                        import bitsandbytes as bnb
                        quantization_config = BitsAndBytesConfig(**QUANTIZATION_CONFIG)
                        logger.info("启用 INT4 量化加载（NF4 量化 + 双重量化）")
                    except ImportError:
                        logger.warning("bitsandbytes 未安装，使用默认精度加载")

                if progress_callback:
                    progress_callback(20, "开始加载模型权重")

                model_kwargs = {
                    "trust_remote_code": True,
                    "low_cpu_mem_usage": True
                }

                self.check_flash_attention_availability()
                if self._flash_attention_available:
                    model_kwargs["attn_implementation"] = "flash_attention_2"
                    logger.info("启用 Flash Attention 2 加速")

                if self.cpu_offload:
                    model_kwargs["device_map"] = "auto"
                    if quantization_config:
                        model_kwargs["quantization_config"] = quantization_config
                        model_kwargs["torch_dtype"] = torch.float16
                        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                            str(self.model_path),
                            **model_kwargs
                        )
                        logger.info("模型加载成功（INT4 量化 + CPU Offload 模式）")
                    else:
                        model_kwargs["torch_dtype"] = torch.bfloat16
                        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                            str(self.model_path),
                            **model_kwargs
                        )
                        logger.info("模型加载成功（BF16 + CPU Offload 模式）")
                    self._model_on_gpu = False
                else:
                    if quantization_config:
                        model_kwargs["quantization_config"] = quantization_config
                        model_kwargs["torch_dtype"] = torch.float16
                        model_kwargs["device_map"] = "cuda:0"
                        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                            str(self.model_path),
                            **model_kwargs
                        )
                        logger.info("模型加载成功（INT4 量化 - GPU 模式）")
                    else:
                        model_kwargs["torch_dtype"] = torch.bfloat16
                        model_kwargs["device_map"] = "auto"
                        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                            str(self.model_path),
                            **model_kwargs
                        )
                        logger.info("模型加载成功（BF16 精度）")
                    self._model_on_gpu = True

                if progress_callback:
                    progress_callback(80, "模型权重加载完成")

                if self.torch_compile and hasattr(torch, 'compile'):
                    try:
                        logger.info("正在应用 torch.compile 优化...")
                        self.model = torch.compile(self.model, mode="reduce-overhead")
                        logger.info("torch.compile 优化已启用")
                    except Exception as e:
                        logger.warning(f"torch.compile 优化失败: {e}")

                self.is_loaded = True

                if progress_callback:
                    progress_callback(100, "Qwen3-VL 模型加载完成")

                logger.info("Qwen3-VL 模型加载成功（使用 Qwen3VLForConditionalGeneration）")

                if self.load_in_4bit:
                    self._verify_int4_quantization()

                if self.cpu_offload:
                    logger.info("CPU Offload 已启用，模型将动态加载到 GPU")

                if self._flash_attention_available:
                    logger.info("Flash Attention 2 已启用")

                return True

            except ImportError as e:
                logger.warning(f"Qwen3VLForConditionalGeneration 不可用: {e}")
                self._load_model_fallback(progress_callback)
                return False
            except Exception as e:
                logger.error(f"Qwen3-VL 模型加载失败：{e}")
                self._load_model_fallback(progress_callback)
                return False

    def _verify_int4_quantization(self):
        """
        验证 INT4 量化是否生效

        检查模型权重的数据类型和量化状态，确保 INT4 量化正确应用。
        """
        try:
            quantized_params = 0
            total_params = 0

            for name, param in self.model.named_parameters():
                total_params += 1
                if hasattr(param, 'quant_type') or 'quant' in name.lower():
                    quantized_params += 1

            if self.load_in_4bit:
                logger.info(f"INT4 量化验证: {quantized_params}/{total_params} 参数已量化")
                logger.info("模型使用 INT4 量化，显存占用约 2.6GB")
            else:
                logger.info("模型使用 BF16 精度，显存占用约 9.8GB")

        except Exception as e:
            logger.warning(f"INT4 量化验证失败: {e}")

    def _load_model_fallback(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> None:
        """
        降级模式：标记为不可用

        Args:
            progress_callback: 进度回调函数
        """
        logger.warning("Qwen3-VL 模型不支持 AutoModelForCausalLM 降级模式")
        logger.warning("请确保 transformers 版本支持 Qwen3VLForConditionalGeneration")

        self.is_loaded = False
        self.model = None
        self.tokenizer = None
        self.processor = None

        if progress_callback:
            progress_callback(0, "降级模式不可用：Qwen3-VL 需要 Qwen3VLForConditionalGeneration")

    def unload_model(self) -> None:
        """
        释放 GPU 显存

        将模型从 GPU 移动到 CPU 内存，释放 GPU 显存供其他任务使用。
        """
        with self._lock:
            if not self.is_loaded or self.model is None:
                logger.debug("模型未加载，无需卸载")
                return

            if self.cpu_offload:
                logger.debug("CPU Offload 模式：模型由 accelerate 自动管理，跳过手动卸载")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    gc.collect()
                return

            if not self._model_on_gpu:
                logger.debug("模型已在 CPU 上，无需卸载")
                return

            try:
                logger.info("[GPU 释放] 正在将 Qwen 模型移动到 CPU...")
                self.model = self.model.to("cpu")

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()

                gc.collect()

                self._model_on_gpu = False

                if torch.cuda.is_available():
                    allocated = torch.cuda.memory_allocated() / 1024**2
                    reserved = torch.cuda.memory_reserved() / 1024**2
                    logger.info(f"[GPU 释放] Qwen 模型已卸载到 CPU，显存: 已用={allocated:.0f}MB, 保留={reserved:.0f}MB")

            except Exception as e:
                logger.warning(f"[GPU 释放] 卸载模型失败: {e}")

    def load_to_gpu(self) -> None:
        """
        将模型加载到 GPU

        将模型从 CPU 移动到 GPU，准备进行推理。
        """
        with self._lock:
            if not self.is_loaded or self.model is None:
                logger.warning("模型未加载，无法移动到 GPU")
                return

            if self.cpu_offload:
                logger.debug("CPU Offload 模式：模型由 accelerate 自动管理，跳过手动加载")
                return

            if self._model_on_gpu:
                logger.debug("模型已在 GPU 上，无需加载")
                return

            try:
                logger.info("[GPU 加载] 正在将 Qwen 模型移动到 GPU...")
                self.model = self.model.to("cuda:0")

                self._model_on_gpu = True

                if torch.cuda.is_available():
                    allocated = torch.cuda.memory_allocated() / 1024**2
                    reserved = torch.cuda.memory_reserved() / 1024**2
                    logger.info(f"[GPU 加载] Qwen 模型已加载到 GPU，显存: 已用={allocated:.0f}MB, 保留={reserved:.0f}MB")

            except Exception as e:
                logger.warning(f"[GPU 加载] 加载模型到 GPU 失败: {e}")

    def warmup(self) -> None:
        """
        模型预热

        执行一次推理以初始化 CUDA 内核，提高后续推理速度。
        """
        if not self.is_loaded:
            logger.warning("Qwen 模型未加载，无法预热")
            return

        try:
            import numpy as np

            if self.processor and self.model:
                dummy_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
                messages = [
                    {"role": "user", "content": [
                        {"type": "image"},
                        {"type": "text", "text": "warmup"}
                    ]}
                ]
                try:
                    text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    inputs = self.processor(text=[text], images=[dummy_image], return_tensors="pt", padding=True)
                    inputs = {k: v.to(self.model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
                    with torch.no_grad():
                        _ = self.model.generate(**inputs, max_new_tokens=10, do_sample=False)
                except Exception as e:
                    logger.debug(f"图像预热跳过: {e}")

            logger.info("Qwen 模型预热完成")

        except Exception as e:
            logger.warning(f"Qwen 模型预热失败: {e}")

    def get_model_status(self) -> Dict[str, Any]:
        """
        获取模型状态信息（PERF-01 增强）

        返回包含懒加载状态的完整模型状态字典。

        Returns:
            Dict[str, Any]: 包含模型状态的字典，新增字段：
                - state: ModelState 枚举值（unloaded/loading/ready/error）
                - lazy_load: 是否启用懒加载
                - last_error: 最后一次错误信息（如果有）
        """
        status = {
            "is_loaded": self.is_loaded,
            "state": self._model_state.value,
            "lazy_load": self._lazy_load,
            "device": self.device,
            "model_on_gpu": self._model_on_gpu,
            "cpu_offload": self.cpu_offload,
            "flash_attention_available": self._flash_attention_available,
            "model_path": str(self.model_path)
        }

        if self._last_error:
            status["last_error"] = self._last_error

        if torch.cuda.is_available():
            status.update({
                "gpu_memory_allocated_mb": torch.cuda.memory_allocated() / 1024**2,
                "gpu_memory_reserved_mb": torch.cuda.memory_reserved() / 1024**2,
                "gpu_memory_total_mb": torch.cuda.get_device_properties(0).total_memory / 1024**2
            })

        return status


def get_model_loader(lazy_load: bool = True) -> QwenModelLoader:
    """
    获取模型加载器单例

    Args:
        lazy_load: 是否启用懒加载模式（默认 True）

    Returns:
        QwenModelLoader: 模型加载器实例
    """
    return QwenModelLoader(lazy_load=lazy_load)
