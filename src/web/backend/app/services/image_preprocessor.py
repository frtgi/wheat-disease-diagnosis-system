"""
优化的图像预处理服务
实现 GPU 加速、预处理流水线并行化、高效图像格式

功能特性：
1. GPU 加速预处理（如果可用）
2. 预处理流水线并行化
3. 支持多种图像格式（包括 WebP）
4. 自适应图像尺寸调整
5. 批处理预处理
6. 图像增强（可选）
"""
import io
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import queue

try:
    import torch
    import torchvision.transforms as T
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PreprocessConfig:
    """
    预处理配置数据类
    
    Attributes:
        target_size: 目标尺寸 (width, height)
        keep_aspect_ratio: 是否保持宽高比
        padding_color: 填充颜色 (R, G, B)
        color_mode: 颜色模式 'RGB' 或 'BGR'
        normalize_mean: 归一化均值
        normalize_std: 归一化标准差
        enable_augmentation: 是否启用图像增强
        enable_gpu: 是否启用 GPU 加速
        batch_size: 批处理大小
    """
    target_size: Tuple[int, int] = (640, 640)
    keep_aspect_ratio: bool = True
    padding_color: Tuple[int, int, int] = (114, 114, 114)
    color_mode: str = "RGB"
    normalize_mean: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    normalize_std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
    enable_augmentation: bool = False
    enable_gpu: bool = True
    batch_size: int = 8


@dataclass
class PreprocessResult:
    """
    预处理结果数据类
    
    Attributes:
        tensor: 预处理后的张量
        original_size: 原始尺寸 (width, height)
        processed_size: 处理后尺寸 (width, height)
        scale_factor: 缩放因子
        padding: 填充信息 (left, top, right, bottom)
        processing_time_ms: 处理时间（毫秒）
        format: 图像格式
    """
    tensor: Optional["torch.Tensor"] = None
    original_size: Tuple[int, int] = (0, 0)
    processed_size: Tuple[int, int] = (0, 0)
    scale_factor: float = 1.0
    padding: Tuple[int, int, int, int] = (0, 0, 0, 0)
    processing_time_ms: float = 0.0
    format: str = "unknown"


class GPUPreprocessor:
    """
    GPU 加速图像预处理器
    
    使用 PyTorch 和 CUDA 加速图像预处理操作
    """
    
    def __init__(self, config: PreprocessConfig):
        """
        初始化 GPU 预处理器
        
        Args:
            config: 预处理配置
        """
        self.config = config
        self._device = None
        self._transforms = None
        self._initialized = False
        
        if TORCH_AVAILABLE and config.enable_gpu:
            self._init_gpu()
    
    def _init_gpu(self) -> None:
        """初始化 GPU 相关资源"""
        try:
            if torch.cuda.is_available():
                self._device = torch.device("cuda:0")
                
                self._transforms = T.Compose([
                    T.Resize(
                        self.config.target_size,
                        interpolation=T.InterpolationMode.BILINEAR,
                        antialias=True
                    ),
                    T.ConvertImageDtype(torch.float32),
                    T.Normalize(
                        mean=list(self.config.normalize_mean),
                        std=list(self.config.normalize_std)
                    )
                ])
                
                self._initialized = True
                logger.info(f"GPU 预处理器已初始化: device={self._device}")
            else:
                logger.warning("CUDA 不可用，将使用 CPU 预处理")
                self._device = torch.device("cpu")
        except Exception as e:
            logger.warning(f"GPU 初始化失败: {e}，将使用 CPU 预处理")
            self._device = torch.device("cpu") if TORCH_AVAILABLE else None
    
    def preprocess(
        self,
        image: Union["Image.Image", np.ndarray, torch.Tensor]
    ) -> PreprocessResult:
        """
        预处理单张图像
        
        Args:
            image: 输入图像（PIL Image、NumPy 数组或 PyTorch 张量）
            
        Returns:
            PreprocessResult: 预处理结果
        """
        start_time = time.time()
        
        if not TORCH_AVAILABLE:
            return self._cpu_fallback(image)
        
        try:
            if isinstance(image, Image.Image):
                original_size = image.size
                image_array = np.array(image)
                if image_array.ndim == 2:
                    image_array = np.stack([image_array] * 3, axis=-1)
                elif image_array.shape[2] == 4:
                    image_array = image_array[:, :, :3]
                
                tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)
                
            elif isinstance(image, np.ndarray):
                original_size = (image.shape[1], image.shape[0])
                if image.ndim == 2:
                    image = np.stack([image] * 3, axis=-1)
                elif image.shape[2] == 4:
                    image = image[:, :, :3]
                
                tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0)
                
            elif isinstance(image, torch.Tensor):
                if image.dim() == 3:
                    tensor = image.unsqueeze(0)
                else:
                    tensor = image
                _, _, h, w = tensor.shape
                original_size = (w, h)
            else:
                raise ValueError(f"不支持的图像类型: {type(image)}")
            
            if self.config.keep_aspect_ratio:
                tensor, scale, padding = self._resize_with_padding(tensor)
            else:
                tensor = self._resize_direct(tensor)
                scale = 1.0
                padding = (0, 0, 0, 0)
            
            if self._device is not None:
                tensor = tensor.to(self._device)
            
            if self._transforms is not None:
                tensor = self._transforms(tensor.float())
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return PreprocessResult(
                tensor=tensor,
                original_size=original_size,
                processed_size=self.config.target_size,
                scale_factor=scale,
                padding=padding,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            logger.error(f"GPU 预处理失败: {e}")
            return self._cpu_fallback(image)
    
    def _resize_with_padding(
        self,
        tensor: torch.Tensor
    ) -> Tuple[torch.Tensor, float, Tuple[int, int, int, int]]:
        """
        保持宽高比缩放并填充
        
        Args:
            tensor: 输入张量 [B, C, H, W]
            
        Returns:
            Tuple: (缩放后的张量, 缩放因子, 填充信息)
        """
        _, _, h, w = tensor.shape
        target_w, target_h = self.config.target_size
        
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = torch.nn.functional.interpolate(
            tensor.float(),
            size=(new_h, new_w),
            mode="bilinear",
            align_corners=False
        )
        
        pad_w = target_w - new_w
        pad_h = target_h - new_h
        pad_left = pad_w // 2
        pad_right = pad_w - pad_left
        pad_top = pad_h // 2
        pad_bottom = pad_h - pad_top
        
        padding = (pad_left, pad_top, pad_right, pad_bottom)
        
        padded = torch.nn.functional.pad(
            resized,
            (pad_left, pad_right, pad_top, pad_bottom),
            value=self.config.padding_color[0] / 255.0
        )
        
        return padded, scale, padding
    
    def _resize_direct(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        直接缩放到目标尺寸
        
        Args:
            tensor: 输入张量 [B, C, H, W]
            
        Returns:
            torch.Tensor: 缩放后的张量
        """
        return torch.nn.functional.interpolate(
            tensor.float(),
            size=self.config.target_size[::-1],
            mode="bilinear",
            align_corners=False
        )
    
    def _cpu_fallback(
        self,
        image: Union["Image.Image", np.ndarray]
    ) -> PreprocessResult:
        """
        CPU 降级处理
        
        Args:
            image: 输入图像
            
        Returns:
            PreprocessResult: 预处理结果
        """
        start_time = time.time()
        
        if PIL_AVAILABLE and isinstance(image, Image.Image):
            original_size = image.size
            if self.config.keep_aspect_ratio:
                image = self._resize_pil_with_padding(image)
            else:
                image = image.resize(self.config.target_size, Image.Resampling.BILINEAR)
            
            image_array = np.array(image).astype(np.float32) / 255.0
            image_array = (image_array - np.array(self.config.normalize_mean)) / np.array(self.config.normalize_std)
            
            if TORCH_AVAILABLE:
                tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)
            else:
                tensor = None
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return PreprocessResult(
                tensor=tensor,
                original_size=original_size,
                processed_size=self.config.target_size,
                processing_time_ms=processing_time_ms
            )
        
        return PreprocessResult()
    
    def _resize_pil_with_padding(self, image: "Image.Image") -> "Image.Image":
        """
        PIL 图像保持宽高比缩放并填充
        
        Args:
            image: PIL 图像
            
        Returns:
            Image.Image: 处理后的图像
        """
        target_w, target_h = self.config.target_size
        w, h = image.size
        
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)
        
        new_image = Image.new("RGB", self.config.target_size, self.config.padding_color)
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        new_image.paste(resized, (paste_x, paste_y))
        
        return new_image
    
    def preprocess_batch(
        self,
        images: List[Union["Image.Image", np.ndarray, torch.Tensor]]
    ) -> List[PreprocessResult]:
        """
        批量预处理图像
        
        Args:
            images: 图像列表
            
        Returns:
            List[PreprocessResult]: 预处理结果列表
        """
        results = []
        
        for i in range(0, len(images), self.config.batch_size):
            batch = images[i:i + self.config.batch_size]
            batch_results = [self.preprocess(img) for img in batch]
            results.extend(batch_results)
        
        return results
    
    def is_gpu_available(self) -> bool:
        """
        检查 GPU 是否可用
        
        Returns:
            bool: GPU 是否可用
        """
        return self._initialized and self._device is not None and self._device.type == "cuda"


class ImagePreprocessor:
    """
    图像预处理器主类
    
    整合 GPU/CPU 预处理、流水线并行化、高效格式支持
    """
    
    def __init__(
        self,
        config: Optional[PreprocessConfig] = None,
        enable_pipeline_parallel: bool = True,
        pipeline_workers: int = 2
    ):
        """
        初始化图像预处理器
        
        Args:
            config: 预处理配置
            enable_pipeline_parallel: 是否启用流水线并行化
            pipeline_workers: 流水线工作线程数
        """
        self.config = config or PreprocessConfig()
        self.enable_pipeline_parallel = enable_pipeline_parallel
        self.pipeline_workers = pipeline_workers
        
        self._gpu_preprocessor = GPUPreprocessor(self.config)
        
        self._executor: Optional[ThreadPoolExecutor] = None
        self._task_queue: Optional[queue.Queue] = None
        self._result_queue: Optional[queue.Queue] = None
        self._running = False
        
        if enable_pipeline_parallel:
            self._init_pipeline()
        
        self._stats = {
            "total_processed": 0,
            "total_time_ms": 0.0,
            "avg_time_ms": 0.0,
            "gpu_processed": 0,
            "cpu_processed": 0
        }
        
        logger.info(
            f"图像预处理器已初始化: "
            f"GPU={'可用' if self._gpu_preprocessor.is_gpu_available() else '不可用'}, "
            f"流水线并行={'启用' if enable_pipeline_parallel else '禁用'}"
        )
    
    def _init_pipeline(self) -> None:
        """初始化预处理流水线"""
        self._executor = ThreadPoolExecutor(max_workers=self.pipeline_workers)
        self._task_queue = queue.Queue(maxsize=100)
        self._result_queue = queue.Queue(maxsize=100)
        self._running = True
        
        for _ in range(self.pipeline_workers):
            self._executor.submit(self._pipeline_worker)
        
        logger.info(f"预处理流水线已启动: workers={self.pipeline_workers}")
    
    def _pipeline_worker(self) -> None:
        """流水线工作线程"""
        while self._running:
            try:
                task = self._task_queue.get(timeout=0.1)
                if task is None:
                    break
                
                task_id, image = task
                result = self._gpu_preprocessor.preprocess(image)
                self._result_queue.put((task_id, result))
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"流水线处理错误: {e}")
    
    def preprocess(
        self,
        image: Union["Image.Image", np.ndarray, torch.Tensor, bytes, str, Path]
    ) -> PreprocessResult:
        """
        预处理图像
        
        Args:
            image: 输入图像（支持多种格式）
            
        Returns:
            PreprocessResult: 预处理结果
        """
        start_time = time.time()
        
        try:
            loaded_image = self._load_image(image)
            
            result = self._gpu_preprocessor.preprocess(loaded_image)
            
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            return PreprocessResult()
    
    def _load_image(
        self,
        image: Union["Image.Image", np.ndarray, torch.Tensor, bytes, str, Path]
    ) -> Union["Image.Image", np.ndarray, torch.Tensor]:
        """
        加载图像
        
        Args:
            image: 输入图像（多种格式）
            
        Returns:
            加载后的图像
        """
        if isinstance(image, (str, Path)):
            return Image.open(image).convert("RGB")
        
        if isinstance(image, bytes):
            return Image.open(io.BytesIO(image)).convert("RGB")
        
        return image
    
    def _update_stats(self, result: PreprocessResult) -> None:
        """
        更新统计信息
        
        Args:
            result: 预处理结果
        """
        self._stats["total_processed"] += 1
        self._stats["total_time_ms"] += result.processing_time_ms
        self._stats["avg_time_ms"] = (
            self._stats["total_time_ms"] / self._stats["total_processed"]
        )
        
        if self._gpu_preprocessor.is_gpu_available():
            self._stats["gpu_processed"] += 1
        else:
            self._stats["cpu_processed"] += 1
    
    def preprocess_batch(
        self,
        images: List[Union["Image.Image", np.ndarray, torch.Tensor, bytes, str, Path]]
    ) -> List[PreprocessResult]:
        """
        批量预处理图像
        
        Args:
            images: 图像列表
            
        Returns:
            List[PreprocessResult]: 预处理结果列表
        """
        results = []
        
        for i in range(0, len(images), self.config.batch_size):
            batch = images[i:i + self.config.batch_size]
            
            if self.enable_pipeline_parallel and self._executor:
                batch_results = list(self._executor.map(self.preprocess, batch))
            else:
                batch_results = [self.preprocess(img) for img in batch]
            
            results.extend(batch_results)
        
        return results
    
    def preprocess_async(
        self,
        image: Union["Image.Image", np.ndarray, torch.Tensor, bytes, str, Path],
        callback: Optional[callable] = None
    ) -> str:
        """
        异步预处理图像
        
        Args:
            image: 输入图像
            callback: 回调函数
            
        Returns:
            str: 任务 ID
        """
        if not self.enable_pipeline_parallel or not self._task_queue:
            raise RuntimeError("流水线并行未启用")
        
        task_id = f"task_{int(time.time() * 1000)}_{id(image)}"
        self._task_queue.put((task_id, image))
        
        if callback:
            def check_result():
                while True:
                    try:
                        tid, result = self._result_queue.get(timeout=1.0)
                        if tid == task_id:
                            callback(result)
                            break
                    except queue.Empty:
                        continue
            
            threading.Thread(target=check_result, daemon=True).start()
        
        return task_id
    
    def get_result(self, task_id: str, timeout: float = 10.0) -> Optional[PreprocessResult]:
        """
        获取异步处理结果
        
        Args:
            task_id: 任务 ID
            timeout: 超时时间（秒）
            
        Returns:
            Optional[PreprocessResult]: 预处理结果
        """
        if not self._result_queue:
            return None
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                tid, result = self._result_queue.get(timeout=0.1)
                if tid == task_id:
                    return result
                self._result_queue.put((tid, result))
            except queue.Empty:
                continue
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            **self._stats,
            "gpu_available": self._gpu_preprocessor.is_gpu_available(),
            "pipeline_parallel": self.enable_pipeline_parallel
        }
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            stats["gpu_memory"] = {
                "allocated_mb": torch.cuda.memory_allocated() / 1024**2,
                "reserved_mb": torch.cuda.memory_reserved() / 1024**2
            }
        
        return stats
    
    def stop(self) -> None:
        """停止预处理器"""
        self._running = False
        
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        if self._task_queue:
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                except queue.Empty:
                    break
        
        if self._result_queue:
            while not self._result_queue.empty():
                try:
                    self._result_queue.get_nowait()
                except queue.Empty:
                    break
        
        logger.info("图像预处理器已停止")


class ImageFormatConverter:
    """
    图像格式转换器
    
    支持高效图像格式（如 WebP）
    """
    
    @staticmethod
    def to_webp(
        image: "Image.Image",
        quality: int = 85
    ) -> bytes:
        """
        转换为 WebP 格式
        
        Args:
            image: PIL 图像
            quality: 压缩质量（1-100）
            
        Returns:
            bytes: WebP 图像数据
        """
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=quality)
        return buffer.getvalue()
    
    @staticmethod
    def from_webp(data: bytes) -> "Image.Image":
        """
        从 WebP 格式加载
        
        Args:
            data: WebP 图像数据
            
        Returns:
            Image.Image: PIL 图像
        """
        return Image.open(io.BytesIO(data))
    
    @staticmethod
    def optimize_format(
        image: "Image.Image",
        max_size_kb: int = 500
    ) -> Tuple[bytes, str]:
        """
        自动选择最优格式
        
        Args:
            image: PIL 图像
            max_size_kb: 最大文件大小（KB）
            
        Returns:
            Tuple[bytes, str]: (图像数据, 格式名称)
        """
        best_format = "PNG"
        best_data = None
        best_size = float("inf")
        
        for fmt in ["WEBP", "PNG", "JPEG"]:
            buffer = io.BytesIO()
            
            if fmt == "WEBP":
                for quality in [95, 85, 75, 65]:
                    buffer = io.BytesIO()
                    image.save(buffer, format="WEBP", quality=quality)
                    size = len(buffer.getvalue())
                    if size < best_size and size <= max_size_kb * 1024:
                        best_size = size
                        best_data = buffer.getvalue()
                        best_format = "WEBP"
            elif fmt == "JPEG":
                if image.mode == "RGBA":
                    image = image.convert("RGB")
                for quality in [95, 85, 75, 65]:
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=quality)
                    size = len(buffer.getvalue())
                    if size < best_size and size <= max_size_kb * 1024:
                        best_size = size
                        best_data = buffer.getvalue()
                        best_format = "JPEG"
            else:
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                size = len(buffer.getvalue())
                if size < best_size and size <= max_size_kb * 1024:
                    best_size = size
                    best_data = buffer.getvalue()
                    best_format = "PNG"
        
        return best_data, best_format


_image_preprocessor: Optional[ImagePreprocessor] = None


def get_image_preprocessor() -> ImagePreprocessor:
    """
    获取图像预处理器单例
    
    Returns:
        ImagePreprocessor: 图像预处理器实例
    """
    global _image_preprocessor
    
    if _image_preprocessor is None:
        try:
            from app.core.ai_config import ai_config
            config = PreprocessConfig(
                target_size=ai_config.IMAGE_PREPROCESS_TARGET_SIZE,
                keep_aspect_ratio=ai_config.IMAGE_PREPROCESS_KEEP_ASPECT_RATIO,
                padding_color=ai_config.IMAGE_PREPROCESS_PADDING_COLOR,
                color_mode=ai_config.IMAGE_PREPROCESS_COLOR_MODE,
                normalize_mean=ai_config.IMAGE_PREPROCESS_NORMALIZE_MEAN,
                normalize_std=ai_config.IMAGE_PREPROCESS_NORMALIZE_STD,
                enable_augmentation=ai_config.IMAGE_PREPROCESS_ENABLE_AUGMENTATION,
                enable_gpu=ai_config.IMAGE_PREPROCESS_ENABLE_GPU,
                batch_size=ai_config.IMAGE_PREPROCESS_BATCH_SIZE
            )
            _image_preprocessor = ImagePreprocessor(
                config=config,
                enable_pipeline_parallel=ai_config.IMAGE_PREPROCESS_ENABLE_PIPELINE_PARALLEL,
                pipeline_workers=ai_config.IMAGE_PREPROCESS_PIPELINE_WORKERS
            )
        except Exception as e:
            logger.error(f"初始化图像预处理器失败: {e}")
            _image_preprocessor = ImagePreprocessor()
    
    return _image_preprocessor


def initialize_image_preprocessor(
    target_size: Tuple[int, int] = (640, 640),
    enable_gpu: bool = True,
    enable_pipeline_parallel: bool = True,
    pipeline_workers: int = 2
) -> ImagePreprocessor:
    """
    初始化图像预处理器
    
    Args:
        target_size: 目标尺寸
        enable_gpu: 是否启用 GPU 加速
        enable_pipeline_parallel: 是否启用流水线并行
        pipeline_workers: 流水线工作线程数
        
    Returns:
        ImagePreprocessor: 图像预处理器实例
    """
    global _image_preprocessor
    
    config = PreprocessConfig(
        target_size=target_size,
        enable_gpu=enable_gpu
    )
    
    _image_preprocessor = ImagePreprocessor(
        config=config,
        enable_pipeline_parallel=enable_pipeline_parallel,
        pipeline_workers=pipeline_workers
    )
    
    logger.info(
        f"图像预处理器已初始化: "
        f"target_size={target_size}, "
        f"enable_gpu={enable_gpu}"
    )
    
    return _image_preprocessor
