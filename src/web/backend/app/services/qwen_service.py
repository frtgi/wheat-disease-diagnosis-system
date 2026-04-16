"""
Qwen3-VL 多模态诊断服务（门面类）
作为统一入口，组合配置、加载、预处理、推理和后处理模块
保持原有 API 接口不变，确保向后兼容

PERF-01 优化：支持懒加载模式
- 服务启动时不加载模型（默认）
- 首次诊断请求时按需加载
- 支持异步加载和状态查询
"""
import logging
import asyncio
import warnings
from functools import wraps
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from PIL import Image

from .qwen.qwen_config import (
    MODEL_NAME,
    MODEL_PATH,
    INFERENCE_PARAMS,
    PROMPT_TEMPLATES
)
from .qwen.qwen_loader import QwenModelLoader, get_model_loader, ModelState
from .qwen.qwen_preprocessor import QwenPreprocessor, get_preprocessor
from .qwen.qwen_inferencer import QwenInferencer, get_inferencer
from .qwen.qwen_postprocessor import QwenPostprocessor, get_postprocessor

logger = logging.getLogger(__name__)


def deprecated(replacement: str) -> Callable:
    """
    标记已弃用的方法，调用时发出 DeprecationWarning

    Args:
        replacement: 推荐替代的方法名

    Returns:
        装饰器函数，包装原方法并在调用时发出警告
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} 已弃用，请使用 {replacement} 替代",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class QwenService:
    """
    Qwen3-VL 多模态诊断服务（门面类）

    采用 Facade 设计模式，将复杂的子系统（配置、加载、预处理、推理、后处理）
    封装为统一的接口，简化外部调用。

    保持与原始 qwen_service.py 完全兼容的公共接口。

    集成特性：
    - 原生 Early Fusion 多模态架构
    - KAD-Former 知识引导注意力
    - DeepStack 多层视觉特征注入
    - Graph-RAG 上下文增强
    - Thinking 推理链模式
    - 动态加载/卸载（CPU Offload）优化显存使用
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: str = "cuda",
        load_in_4bit: bool = False,
        enable_kad_former: bool = True,
        enable_graph_rag: bool = True,
        auto_load: bool = True,
        cpu_offload: bool = True,
        max_new_tokens: int = 768,
        temperature_diagnosis: float = 0.2,
        temperature_thinking: float = 0.5,
        top_p: float = 0.9,
        do_sample: bool = False,
        repetition_penalty: float = 1.1,
        max_tokens_thinking: int = 1024,
        max_tokens_normal: int = 512,
        enable_flash_attention: bool = True,
        kv_cache_quantization: bool = False,
        kv_cache_quantization_bits: int = 8,
        kv_cache_quantization_group_size: int = 64,
        torch_compile: bool = False,
        torch_compile_mode: str = "reduce-overhead",
        torch_compile_fullgraph: bool = False,
        torch_compile_dynamic: bool = True,
        lazy_load: bool = True
    ) -> None:
        """
        初始化 Qwen3-VL 服务

        Args:
            model_path: 模型路径
            device: 推理设备（cuda/cpu）
            load_in_4bit: 是否使用 INT4 量化
            enable_kad_former: 是否启用 KAD-Former
            enable_graph_rag: 是否启用 Graph-RAG
            auto_load: 是否自动加载模型（非懒加载模式下生效）
            cpu_offload: 是否启用 CPU Offload
            max_new_tokens: 最大生成 token 数
            temperature_diagnosis: 诊断任务温度
            temperature_thinking: Thinking 模式温度
            top_p: 核采样参数
            do_sample: 是否采样
            repetition_penalty: 重复惩罚
            max_tokens_thinking: Thinking 模式最大生成长度
            max_tokens_normal: 普通模式最大生成长度
            enable_flash_attention: 是否启用 Flash Attention 2
            kv_cache_quantization: 是否启用 KV Cache 量化
            kv_cache_quantization_bits: KV Cache 量化位数
            kv_cache_quantization_group_size: KV Cache 量化组大小
            torch_compile: 是否启用 torch.compile
            torch_compile_mode: torch.compile 编译模式
            torch_compile_fullgraph: 是否编译完整计算图
            torch_compile_dynamic: 是否支持动态形状输入
            lazy_load: 是否启用懒加载模式（PERF-01，默认 True）
                     - True: 服务启动时不加载模型，首次诊断时按需加载
                     - False: 初始化时立即加载模型（保持原有行为）
        """
        self.model_path = model_path or MODEL_PATH
        self.device = device
        self.load_in_4bit = load_in_4bit
        self.enable_kad_former = enable_kad_former
        self.enable_graph_rag = enable_graph_rag
        self.cpu_offload = cpu_offload

        # PERF-01：懒加载配置
        self._lazy_load = lazy_load

        self.max_new_tokens = max_new_tokens
        self.temperature_diagnosis = temperature_diagnosis
        self.temperature_thinking = temperature_thinking
        self.top_p = top_p
        self.do_sample = do_sample
        self.repetition_penalty = repetition_penalty
        self.max_tokens_thinking = max_tokens_thinking
        self.max_tokens_normal = max_tokens_normal

        self.enable_flash_attention = enable_flash_attention
        self.kv_cache_quantization = kv_cache_quantization
        self.kv_cache_quantization_bits = kv_cache_quantization_bits
        self.kv_cache_quantization_group_size = kv_cache_quantization_group_size
        self.torch_compile = torch_compile
        self.torch_compile_mode = torch_compile_mode
        self.torch_compile_fullgraph = torch_compile_fullgraph
        self.torch_compile_dynamic = torch_compile_dynamic

        # PERF-01：使用懒加载配置初始化 loader
        self.loader = get_model_loader(lazy_load=lazy_load)
        self.preprocessor = get_preprocessor()
        self.inferencer = get_inferencer(
            max_new_tokens=max_new_tokens,
            temperature_diagnosis=temperature_diagnosis,
            temperature_thinking=temperature_thinking,
            top_p=top_p,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
            max_tokens_thinking=max_tokens_thinking,
            max_tokens_normal=max_tokens_normal,
            kv_cache_quantization=kv_cache_quantization,
            kv_cache_quantization_bits=kv_cache_quantization_bits,
            kv_cache_quantization_group_size=kv_cache_quantization_group_size
        )
        self.postprocessor = get_postprocessor()

        self.kad_former: Optional[Any] = None
        self.fusion_engine: Optional[Any] = None
        self.graphrag_engine: Optional[Any] = None

        self._initialize_modules()

        # PERF-01：仅在非懒加载模式下自动加载
        if auto_load and not lazy_load:
            logger.info("非懒加载模式，立即加载模型...")
            self._load_model()
        elif lazy_load:
            logger.info("懒加载模式已启用，模型将在首次诊断请求时按需加载")

    def _initialize_modules(self) -> None:
        """
        初始化 KAD-Former 和 Graph-RAG 模块
        """
        try:
            if self.enable_kad_former:
                try:
                    from ....fusion import create_fusion_engine
                    self.fusion_engine = create_fusion_engine()
                    logger.info("KAD-Former 融合引擎初始化成功")
                except ImportError:
                    logger.debug("KAD-Former 融合模块未安装，跳过")
                    self.enable_kad_former = False

            if self.enable_graph_rag:
                try:
                    from .graphrag_service import get_graphrag_service
                    self.graphrag_engine = get_graphrag_service()
                    logger.info("Graph-RAG 引擎初始化成功 (graphrag_service)")
                except ImportError as e:
                    logger.debug(f"Graph-RAG 引擎未安装，将使用基础模式: {e}")
                    self.enable_graph_rag = False

        except Exception as e:
            logger.warning(f"模块初始化失败：{e}，将使用基础模式")
            self.enable_kad_former = False
            self.enable_graph_rag = False

    def _load_model(self, progress_callback: Optional[Callable] = None) -> None:
        """
        加载模型（委托给 loader 模块）

        Args:
            progress_callback: 进度回调函数
        """
        success = self.loader.load_model(
            model_path=self.model_path,
            device=self.device,
            load_in_4bit=self.load_in_4bit,
            cpu_offload=self.cpu_offload,
            enable_flash_attention=self.enable_flash_attention,
            torch_compile=self.torch_compile,
            progress_callback=progress_callback
        )

        if success:
            self.loader.warmup()

    @property
    def is_loaded(self) -> bool:
        """获取模型是否已加载"""
        return self.loader.is_loaded

    @property
    def model_state(self) -> ModelState:
        """获取当前模型状态（PERF-01）"""
        return self.loader.get_state()

    @property
    def is_lazy_load(self) -> bool:
        """是否启用懒加载模式（PERF-01）"""
        return self._lazy_load

    async def ensure_loaded(self, progress_callback: Optional[Callable] = None) -> None:
        """
        确保模型已加载（PERF-01 懒加载核心方法）

        如果启用懒加载且模型未加载，则触发异步加载。
        此方法应该在诊断请求开始时调用。

        Args:
            progress_callback: 进度回调函数

        Raises:
            Exception: 模型加载失败时抛出异常
        """
        if not self._lazy_load:
            if not self.is_loaded:
                self._load_model(progress_callback=progress_callback)
            return

        state = self.loader.get_state()
        if state == ModelState.READY:
            return

        logger.info("懒加载：触发 Qwen3-VL 模型加载...")
        await self.loader.ensure_loaded(
            model_path=self.model_path,
            device=self.device,
            load_in_4bit=self.load_in_4bit,
            cpu_offload=self.cpu_offload,
            enable_flash_attention=self.enable_flash_attention,
            torch_compile=self.torch_compile,
            progress_callback=progress_callback
        )

        if self.loader.get_state() == ModelState.READY:
            logger.info("懒加载：Qwen3-VL 模型就绪")
            self.loader.warmup()

    async def diagnose_async(
        self,
        image: Optional[Image.Image] = None,
        symptoms: str = "",
        enable_thinking: bool = True,
        use_graph_rag: bool = True,
        disease_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        异步多模态诊断（PERF-01 增强）

        自动处理懒加载逻辑：
        - 如果模型未加载，先触发加载
        - 如果正在加载，等待完成
        - 加载完成后执行诊断

        Args:
            image: 病害图像（可选）
            symptoms: 症状描述文本
            enable_thinking: 是否启用 Thinking 推理链模式
            use_graph_rag: 是否使用 Graph-RAG 上下文增强
            disease_context: 疾病上下文（用于 Graph-RAG 检索）

        Returns:
            Dict[str, Any]: 诊断结果字典
        """
        await self.ensure_loaded()
        return await asyncio.to_thread(
            self.diagnose,
            image=image,
            symptoms=symptoms,
            enable_thinking=enable_thinking,
            use_graph_rag=use_graph_rag,
            disease_context=disease_context
        )

    @property
    def model(self) -> Any:
        """获取模型实例"""
        return self.loader.model

    @property
    def processor(self) -> Any:
        """获取处理器实例"""
        return self.loader.processor

    @property
    def tokenizer(self) -> Any:
        """获取 tokenizer 实例"""
        return self.loader.tokenizer

    @deprecated("diagnose_async")
    def diagnose(
        self,
        image: Optional[Image.Image] = None,
        symptoms: str = "",
        enable_thinking: bool = True,
        use_graph_rag: bool = True,
        disease_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ⚠️ 已弃用：请使用 diagnose_async() 替代

        多模态诊断（同步兼容层）

        此方法为向后兼容保留的同步接口，推荐使用 diagnose_async() 以获得
        原生异步性能（自动处理懒加载和模型状态管理）。

        Args:
            image: 病害图像（可选）
            symptoms: 症状描述文本
            enable_thinking: 是否启用 Thinking 推理链模式
            use_graph_rag: 是否使用 Graph-RAG 上下文增强
            disease_context: 疾病上下文（用于 Graph-RAG 检索）

        Returns:
            Dict[str, Any]: 诊断结果字典
        """
        if not self.is_loaded:
            return {
                "success": False,
                "error": "模型未加载",
                "diagnosis": None
            }

        from app.services.vram_manager import get_vram_manager
        vram_mgr = get_vram_manager()

        gpu_status_before = self.loader.get_model_status()
        if gpu_status_before.get("gpu_memory_allocated_mb"):
            logger.info(f"[Qwen 推理] 推理前显存: 已用={gpu_status_before['gpu_memory_allocated_mb']:.0f}MB")

        vram_mgr.check_and_warn()

        try:
            if self.cpu_offload:
                self.loader.load_to_gpu()

            graphrag_context = ""
            knowledge_links = []
            if self.enable_graph_rag and use_graph_rag and self.graphrag_engine and disease_context:
                try:
                    knowledge_context = self.graphrag_engine.retrieve_disease_knowledge(disease_context)
                    if knowledge_context and knowledge_context.triples:
                        graphrag_context = f"\n{knowledge_context.tokens}\n"
                        knowledge_links = [t.tail for t in knowledge_context.triples]
                        logger.info(f"Graph-RAG 检索到知识：{len(knowledge_context.triples)} 个三元组")
                except Exception as e:
                    logger.warning(f"Graph-RAG 检索失败：{e}")

            system_prompt = self.preprocessor.build_system_prompt(enable_thinking)

            image = self.preprocessor.preprocess_image(image)

            if image and symptoms:
                query = self.preprocessor.build_multimodal_query(symptoms, graphrag_context, enable_thinking)
                messages = self.preprocessor.format_chat_template(image, system_prompt, query, has_image=True)
            elif image:
                query = self.preprocessor.build_image_query(graphrag_context, enable_thinking)
                messages = self.preprocessor.format_chat_template(image, system_prompt, query, has_image=True)
            else:
                query = self.preprocessor.build_text_query(symptoms, graphrag_context, enable_thinking)
                messages = self.preprocessor.format_chat_template(None, system_prompt, query, has_image=False)

            if self.loader.processor is not None:
                response = self.inferencer.infer_single(
                    model=self.loader.model,
                    processor=self.loader.processor,
                    image=image,
                    messages=messages,
                    enable_thinking=enable_thinking
                )
            else:
                response = ""

            diagnosis = self.postprocessor.parse_response(response, enable_thinking)

            result = {
                "success": True,
                "diagnosis": diagnosis,
                "raw_response": response,
                "model": MODEL_NAME,
                "knowledge_links": knowledge_links,
                "features": {
                    "thinking_mode": enable_thinking,
                    "graph_rag": self.enable_graph_rag and use_graph_rag,
                    "kad_former": self.enable_kad_former,
                    "int4_quantization": self.load_in_4bit,
                    "cpu_offload": self.cpu_offload,
                    "flash_attention": self.loader._flash_attention_available,
                    "kv_cache_quantization": self.kv_cache_quantization,
                    "torch_compile": self.torch_compile
                }
            }

            if enable_thinking:
                reasoning_chain = self.postprocessor.extract_reasoning_chain(response)
                if reasoning_chain:
                    result["reasoning_chain"] = reasoning_chain

            return result

        except Exception as e:
            logger.error(f"Qwen3-VL 诊断失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "diagnosis": None
            }
        finally:
            if self.cpu_offload:
                self.loader.unload_model()
                gpu_status_after = self.loader.get_model_status()
                if gpu_status_after.get("gpu_memory_allocated_mb"):
                    logger.info(f"[Qwen 推理] 推理后显存: 已用={gpu_status_after['gpu_memory_allocated_mb']:.0f}MB")
            vram_mgr.cleanup(aggressive=False)

    def unload_from_gpu(self) -> None:
        """
        释放 GPU 显存（委托给 loader 模块）
        """
        self.loader.unload_model()

    def load_to_gpu(self) -> None:
        """
        将模型加载到 GPU（委托给 loader 模块）
        """
        self.loader.load_to_gpu()

    def get_gpu_memory_status(self) -> Dict[str, float]:
        """
        获取 GPU 显存状态

        Returns:
            Dict[str, float]: 显存状态信息
        """
        status = self.loader.get_model_status()
        return {
            "available": status.get("gpu_memory_total_mb", 0) > 0,
            "allocated_mb": status.get("gpu_memory_allocated_mb", 0),
            "reserved_mb": status.get("gpu_memory_reserved_mb", 0),
            "total_mb": status.get("gpu_memory_total_mb", 0)
        }

    def get_load_progress(self) -> int:
        """
        获取加载进度

        Returns:
            int: 加载进度百分比
        """
        return 100 if self.is_loaded else 0

    def _warmup(self) -> None:
        """
        模型预热（委托给 loader 模块）
        """
        self.loader.warmup()

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息（PERF-01 增强）

        Returns:
            Dict[str, Any]: 模型详细信息，新增懒加载相关字段
        """
        info = {
            "model_type": MODEL_NAME,
            "model_path": str(self.model_path),
            "is_loaded": self.is_loaded,
            "device": self.device,
            "capabilities": ["text-generation", "image-analysis", "multimodal"],
            # PERF-01：懒加载状态
            "lazy_load": self._lazy_load,
            "model_state": self.loader.get_state().value,
            "features": {
                "int4_quantization": self.load_in_4bit,
                "kad_former": self.enable_kad_former,
                "graph_rag": self.enable_graph_rag,
                "thinking_mode": True,
                "early_fusion": True,
                "deepstack": True,
                "flash_attention": self.loader._flash_attention_available,
                "kv_cache_quantization": self.kv_cache_quantization,
                "torch_compile": self.torch_compile
            }
        }

        if self.load_in_4bit:
            info["estimated_vram"] = "~2.6GB (INT4)"
        else:
            info["estimated_vram"] = "~9.8GB (BF16)"

        return info


# 全局服务实例
_qwen_service: Optional[QwenService] = None


def get_qwen_service(lazy_load: bool = True) -> QwenService:
    """
    获取 Qwen3-VL 服务单例（PERF-01 增强）

    从 ai_config 加载推理参数配置，确保参数统一管理。
    支持懒加载模式配置。

    Args:
        lazy_load: 是否启用懒加载模式（默认 True）
                 - True: 服务启动时不加载模型（推荐，启动时间 ~10s）
                 - False: 启动时立即加载模型（启动时间 ~98s）

    Returns:
        QwenService 实例
    """
    global _qwen_service
    if _qwen_service is None:
        try:
            from app.core.ai_config import ai_config
            _qwen_service = QwenService(
                model_path=ai_config.QWEN_MODEL_PATH,
                device=ai_config.QWEN_DEVICE,
                load_in_4bit=ai_config.QWEN_LOAD_IN_4BIT,
                enable_kad_former=ai_config.ENABLE_KAD_FORMER,
                enable_graph_rag=ai_config.ENABLE_GRAPH_RAG,
                max_new_tokens=ai_config.QWEN_MAX_NEW_TOKENS,
                temperature_diagnosis=ai_config.QWEN_TEMPERATURE_DIAGNOSIS,
                temperature_thinking=ai_config.QWEN_TEMPERATURE_THINKING,
                top_p=ai_config.QWEN_TOP_P,
                do_sample=ai_config.QWEN_DO_SAMPLE,
                repetition_penalty=ai_config.QWEN_REPETITION_PENALTY,
                max_tokens_thinking=ai_config.QWEN_MAX_TOKENS_THINKING,
                max_tokens_normal=ai_config.QWEN_MAX_TOKENS_NORMAL,
                enable_flash_attention=ai_config.ENABLE_FLASH_ATTENTION,
                kv_cache_quantization=ai_config.KV_CACHE_QUANTIZATION,
                kv_cache_quantization_bits=ai_config.KV_CACHE_QUANTIZATION_BITS,
                kv_cache_quantization_group_size=ai_config.KV_CACHE_QUANTIZATION_GROUP_SIZE,
                torch_compile=ai_config.TORCH_COMPILE_ENABLE,
                torch_compile_mode=ai_config.TORCH_COMPILE_MODE,
                torch_compile_fullgraph=ai_config.TORCH_COMPILE_FULLGRAPH,
                torch_compile_dynamic=ai_config.TORCH_COMPILE_DYNAMIC,
                lazy_load=lazy_load  # PERF-01：传递懒加载配置
            )
        except Exception as e:
            logger.error(f"初始化 Qwen 服务失败：{e}")
            from app.core.ai_config import AIConfig
            ai_config = AIConfig()
            _qwen_service = QwenService(
                model_path=ai_config.QWEN_MODEL_PATH,
                device=ai_config.QWEN_DEVICE,
                load_in_4bit=ai_config.QWEN_LOAD_IN_4BIT,
                enable_kad_former=ai_config.ENABLE_KAD_FORMER,
                enable_graph_rag=ai_config.ENABLE_GRAPH_RAG,
                max_new_tokens=ai_config.QWEN_MAX_NEW_TOKENS,
                temperature_diagnosis=ai_config.QWEN_TEMPERATURE_DIAGNOSIS,
                temperature_thinking=ai_config.QWEN_TEMPERATURE_THINKING,
                top_p=ai_config.QWEN_TOP_P,
                do_sample=ai_config.QWEN_DO_SAMPLE,
                repetition_penalty=ai_config.QWEN_REPETITION_PENALTY,
                max_tokens_thinking=ai_config.QWEN_MAX_TOKENS_THINKING,
                max_tokens_normal=ai_config.QWEN_MAX_TOKENS_NORMAL,
                enable_flash_attention=ai_config.ENABLE_FLASH_ATTENTION,
                kv_cache_quantization=ai_config.KV_CACHE_QUANTIZATION,
                kv_cache_quantization_bits=ai_config.KV_CACHE_QUANTIZATION_BITS,
                kv_cache_quantization_group_size=ai_config.KV_CACHE_QUANTIZATION_GROUP_SIZE,
                torch_compile=ai_config.TORCH_COMPILE_ENABLE,
                lazy_load=lazy_load  # PERF-01：传递懒加载配置
            )
    return _qwen_service
