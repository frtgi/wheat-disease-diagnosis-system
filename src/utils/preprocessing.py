# -*- coding: utf-8 -*-
"""
统一图像预处理模块

整合了多种预处理实现，提供统一的接口：
- CPU 预处理（基于 OpenCV/NumPy）
- GPU 预处理（基于 PyTorch）
- 图像质量评估
- 数据增强

特性：
- 统一的 API 接口
- 自动选择最优后端
- 向后兼容现有代码
- 支持批处理和异步处理
"""
import os
import io
import time
import logging
from typing import Tuple, Optional, Dict, Any, List, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV 不可用，CPU 预处理功能受限")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL 不可用，图像加载功能受限")

try:
    import torch
    import torchvision.transforms as T
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch 不可用，GPU 预处理功能受限")


class BackendType(Enum):
    """预处理后端类型"""
    AUTO = "auto"
    CPU = "cpu"
    GPU = "gpu"


@dataclass
class PreprocessConfig:
    """
    预处理配置
    
    统一的配置类，支持 CPU 和 GPU 后端
    """
    target_size: Tuple[int, int] = (640, 640)
    normalize: bool = True
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
    preserve_aspect_ratio: bool = False
    pad_color: Tuple[int, int, int] = (114, 114, 114)
    min_size: int = 32
    max_size: int = 1280
    backend: BackendType = BackendType.AUTO
    enable_gpu: bool = True
    color_mode: str = "RGB"
    batch_size: int = 8


@dataclass
class PreprocessResult:
    """
    预处理结果
    
    包含处理后的图像和元数据
    """
    image: Any  # np.ndarray 或 torch.Tensor
    original_shape: Tuple[int, int, int]
    processed_shape: Tuple[int, int, int]
    scale_info: Dict[str, Any]
    processing_time_ms: float
    backend: str
    metadata: Dict[str, Any]


def preprocess_image(
    image: Union[str, Path, "Image.Image", np.ndarray, "torch.Tensor"],
    target_size: Tuple[int, int] = (640, 640),
    normalize: bool = True,
    preserve_aspect_ratio: bool = False,
    backend: BackendType = BackendType.AUTO,
    **kwargs
) -> PreprocessResult:
    """
    统一的图像预处理函数
    
    这是对外的主要接口，自动选择最优后端进行预处理。
    
    :param image: 输入图像（路径、PIL Image、NumPy 数组或 PyTorch 张量）
    :param target_size: 目标尺寸 (width, height)
    :param normalize: 是否归一化
    :param preserve_aspect_ratio: 是否保持宽高比
    :param backend: 后端类型（AUTO/CPU/GPU）
    :param kwargs: 其他参数
    :return: PreprocessResult 对象
    
    示例:
        >>> result = preprocess_image("image.jpg", target_size=(640, 640))
        >>> processed_image = result.image
    """
    config = PreprocessConfig(
        target_size=target_size,
        normalize=normalize,
        preserve_aspect_ratio=preserve_aspect_ratio,
        backend=backend,
        **kwargs
    )
    
    preprocessor = get_preprocessor(config)
    return preprocessor.preprocess(image)


class ImagePreprocessor:
    """
    统一的图像预处理器
    
    整合 CPU 和 GPU 预处理功能，提供统一的接口
    """
    
    def __init__(self, config: Optional[PreprocessConfig] = None):
        """
        初始化预处理器
        
        :param config: 预处理配置
        """
        self.config = config or PreprocessConfig()
        self._backend = self._select_backend()
        self._cpu_preprocessor = None
        self._gpu_preprocessor = None
        
        if self._backend in [BackendType.CPU, BackendType.AUTO]:
            self._init_cpu_preprocessor()
        
        if self._backend in [BackendType.GPU, BackendType.AUTO]:
            self._init_gpu_preprocessor()
        
        logger.info(f"图像预处理器已初始化: backend={self._backend.value}")
    
    def _select_backend(self) -> BackendType:
        """
        选择预处理后端
        
        :return: 后端类型
        """
        if self.config.backend != BackendType.AUTO:
            return self.config.backend
        
        if TORCH_AVAILABLE and self.config.enable_gpu and torch.cuda.is_available():
            return BackendType.GPU
        elif OPENCV_AVAILABLE:
            return BackendType.CPU
        elif TORCH_AVAILABLE:
            return BackendType.GPU
        else:
            raise RuntimeError("无可用的预处理后端")
    
    def _init_cpu_preprocessor(self):
        """初始化 CPU 预处理器"""
        if not OPENCV_AVAILABLE:
            return
        
        from ..vision.preprocessing import ImagePreprocessor as VisionPreprocessor
        from ..vision.preprocessing import PreprocessConfig as VisionConfig
        
        vision_config = VisionConfig(
            target_size=self.config.target_size,
            normalize=self.config.normalize,
            mean=self.config.mean,
            std=self.config.std,
            preserve_aspect_ratio=self.config.preserve_aspect_ratio,
            pad_color=self.config.pad_color,
            min_size=self.config.min_size,
            max_size=self.config.max_size
        )
        
        self._cpu_preprocessor = VisionPreprocessor(vision_config)
        logger.debug("CPU 预处理器已初始化")
    
    def _init_gpu_preprocessor(self):
        """初始化 GPU 预处理器"""
        if not TORCH_AVAILABLE:
            return
        
        try:
            from ..web.backend.app.services.image_preprocessor import (
                ImagePreprocessor as WebPreprocessor,
                PreprocessConfig as WebConfig
            )
            
            web_config = WebConfig(
                target_size=self.config.target_size,
                keep_aspect_ratio=self.config.preserve_aspect_ratio,
                padding_color=self.config.pad_color,
                color_mode=self.config.color_mode,
                normalize_mean=self.config.mean,
                normalize_std=self.config.std,
                enable_gpu=self.config.enable_gpu,
                batch_size=self.config.batch_size
            )
            
            self._gpu_preprocessor = WebPreprocessor(config=web_config)
            logger.debug("GPU 预处理器已初始化")
        except ImportError:
            logger.debug("GPU 预处理器模块不可用")
    
    def preprocess(
        self,
        image: Union[str, Path, "Image.Image", np.ndarray, "torch.Tensor"]
    ) -> PreprocessResult:
        """
        预处理图像
        
        :param image: 输入图像
        :return: 预处理结果
        """
        start_time = time.time()
        
        loaded_image = self._load_image(image)
        
        if self._backend == BackendType.GPU and self._gpu_preprocessor:
            result = self._gpu_preprocessor.preprocess(loaded_image)
            processing_time = (time.time() - start_time) * 1000
            
            return PreprocessResult(
                image=result.tensor if hasattr(result, 'tensor') else result.get('image'),
                original_shape=self._get_shape(loaded_image),
                processed_shape=self._get_shape(result.tensor if hasattr(result, 'tensor') else result.get('image')),
                scale_info=result.__dict__ if hasattr(result, '__dict__') else result,
                processing_time_ms=processing_time,
                backend="gpu",
                metadata={}
            )
        elif self._backend == BackendType.CPU and self._cpu_preprocessor:
            processed, metadata = self._cpu_preprocessor.preprocess(loaded_image)
            processing_time = (time.time() - start_time) * 1000
            
            return PreprocessResult(
                image=processed,
                original_shape=metadata.get("original_shape", self._get_shape(loaded_image)),
                processed_shape=metadata.get("processed_shape", self._get_shape(processed)),
                scale_info=metadata.get("scale_info", {}),
                processing_time_ms=processing_time,
                backend="cpu",
                metadata=metadata
            )
        else:
            raise RuntimeError("无可用的预处理器")
    
    def _load_image(
        self,
        image: Union[str, Path, "Image.Image", np.ndarray, "torch.Tensor"]
    ) -> Union["Image.Image", np.ndarray, "torch.Tensor"]:
        """
        加载图像
        
        :param image: 输入图像
        :return: 加载后的图像
        """
        if isinstance(image, (str, Path)):
            if not PIL_AVAILABLE:
                raise ImportError("PIL 不可用，无法加载图像文件")
            return Image.open(image).convert("RGB")
        
        if isinstance(image, bytes):
            if not PIL_AVAILABLE:
                raise ImportError("PIL 不可用，无法加载图像数据")
            return Image.open(io.BytesIO(image)).convert("RGB")
        
        return image
    
    def _get_shape(self, image: Any) -> Tuple[int, int, int]:
        """
        获取图像形状
        
        :param image: 图像对象
        :return: 形状元组
        """
        if isinstance(image, np.ndarray):
            return image.shape
        elif TORCH_AVAILABLE and isinstance(image, torch.Tensor):
            if image.dim() == 4:
                return tuple(image.shape[1:])
            elif image.dim() == 3:
                return tuple(image.shape)
            else:
                return (1, image.shape[-1], image.shape[-2])
        elif PIL_AVAILABLE and isinstance(image, Image.Image):
            return (image.size[1], image.size[0], 3)
        else:
            return (0, 0, 0)
    
    def preprocess_batch(
        self,
        images: List[Union[str, Path, "Image.Image", np.ndarray, "torch.Tensor"]]
    ) -> List[PreprocessResult]:
        """
        批量预处理图像
        
        :param images: 图像列表
        :return: 预处理结果列表
        """
        results = []
        
        for i in range(0, len(images), self.config.batch_size):
            batch = images[i:i + self.config.batch_size]
            
            if self._backend == BackendType.GPU and self._gpu_preprocessor:
                batch_results = self._gpu_preprocessor.preprocess_batch(batch)
                results.extend([
                    PreprocessResult(
                        image=r.tensor if hasattr(r, 'tensor') else r.get('image'),
                        original_shape=self._get_shape(img),
                        processed_shape=self._get_shape(r.tensor if hasattr(r, 'tensor') else r.get('image')),
                        scale_info=r.__dict__ if hasattr(r, '__dict__') else r,
                        processing_time_ms=r.processing_time_ms if hasattr(r, 'processing_time_ms') else 0,
                        backend="gpu",
                        metadata={}
                    )
                    for r, img in zip(batch_results, batch)
                ])
            else:
                batch_results = [self.preprocess(img) for img in batch]
                results.extend(batch_results)
        
        return results


_preprocessor_instance: Optional[ImagePreprocessor] = None


def get_preprocessor(config: Optional[PreprocessConfig] = None) -> ImagePreprocessor:
    """
    获取预处理器单例
    
    :param config: 预处理配置
    :return: ImagePreprocessor 实例
    """
    global _preprocessor_instance
    
    if _preprocessor_instance is None or config is not None:
        _preprocessor_instance = ImagePreprocessor(config)
    
    return _preprocessor_instance


def create_preprocessor(
    target_size: Tuple[int, int] = (640, 640),
    normalize: bool = True,
    preserve_aspect_ratio: bool = False,
    backend: BackendType = BackendType.AUTO,
    **kwargs
) -> ImagePreprocessor:
    """
    创建预处理器实例的工厂函数
    
    :param target_size: 目标尺寸
    :param normalize: 是否归一化
    :param preserve_aspect_ratio: 是否保持宽高比
    :param backend: 后端类型
    :param kwargs: 其他参数
    :return: ImagePreprocessor 实例
    """
    config = PreprocessConfig(
        target_size=target_size,
        normalize=normalize,
        preserve_aspect_ratio=preserve_aspect_ratio,
        backend=backend,
        **kwargs
    )
    
    return ImagePreprocessor(config)
