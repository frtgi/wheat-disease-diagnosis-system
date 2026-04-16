# -*- coding: utf-8 -*-
"""
图像预处理优化模块
提供高效的图像预处理管道，支持 JPEG 直接解码和批量处理
"""
import io
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Union, List

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from PIL import Image
    IMAGE_LIBS_AVAILABLE = True
except ImportError:
    IMAGE_LIBS_AVAILABLE = False
    logger.warning("PIL 或 numpy 不可用，图像预处理功能受限")


class ImagePreprocessor:
    """高效图像预处理器"""

    @staticmethod
    def load_image_jpeg_fast(file_path: str) -> Optional[np.ndarray]:
        """
        快速加载 JPEG 图像
        
        使用 PIL 的快速路径解码 JPEG，
        避免 RGB 转换开销（如可能）。
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            numpy 数组格式的图像，失败返回 None
        """
        if not IMAGE_LIBS_AVAILABLE:
            logger.error("图像处理库不可用")
            return None

        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"图像文件不存在: {file_path}")
                return None
            
            start_time = time.time()
            
            with Image.open(path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                image_array = np.array(img, dtype=np.uint8)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"快速 JPEG 加载完成: {file_path}, 耗时 {elapsed_ms:.2f}ms, 尺寸 {image_array.shape}")
            
            return image_array
            
        except Exception as e:
            logger.error(f"快速加载 JPEG 图像失败 ({file_path}): {e}")
            return None

    @staticmethod
    def load_image_from_bytes(image_data: bytes) -> Optional[np.ndarray]:
        """
        从字节数据快速加载图像
        
        Args:
            image_data: 图像二进制数据
            
        Returns:
            numpy 数组格式的图像，失败返回 None
        """
        if not IMAGE_LIBS_AVAILABLE:
            logger.error("图像处理库不可用")
            return None

        try:
            start_time = time.time()
            
            with Image.open(io.BytesIO(image_data)) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                image_array = np.array(img, dtype=np.uint8)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"从字节加载图像完成, 耗时 {elapsed_ms:.2f}ms, 尺寸 {image_array.shape}")
            
            return image_array
            
        except Exception as e:
            logger.error(f"从字节数据加载图像失败: {e}")
            return None

    @staticmethod
    def resize_with_padding(
        image: np.ndarray,
        target_size: Tuple[int, int] = (640, 640),
        padding_color: int = 114
    ) -> np.ndarray:
        """
        带填充的等比缩放
        
        保持图像比例缩放到目标尺寸，
        不足部分用指定颜色填充。
        
        Args:
            image: 输入图像 (H, W, C)
            target_size: 目标尺寸 (宽, 高)
            padding_color: 填充颜色
            
        Returns:
            处理后的图像 (target_h, target_w, C)
        """
        if not IMAGE_LIBS_AVAILABLE:
            raise RuntimeError("numpy 不可用，无法执行图像缩放")

        try:
            start_time = time.time()
            
            target_w, target_h = target_size
            h, w = image.shape[:2]
            
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            pil_image = Image.fromarray(image)
            resized = pil_image.resize((new_w, new_h), Image.Resampling.BILINEAR)
            resized_array = np.array(resized, dtype=np.uint8)
            
            padded = np.full((target_h, target_w, 3), padding_color, dtype=np.uint8)
            
            pad_top = (target_h - new_h) // 2
            pad_left = (target_w - new_w) // 2
            
            padded[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = resized_array
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"等比缩放完成: {w}x{h} -> {target_w}x{target_h}, 耗时 {elapsed_ms:.2f}ms")
            
            return padded
            
        except Exception as e:
            logger.error(f"等比缩放失败: {e}")
            raise

    @staticmethod
    def batch_preprocess(
        images: List[Union[str, np.ndarray, bytes]],
        target_size: Tuple[int, int] = (640, 640),
        normalize: bool = True
    ) -> np.ndarray:
        """
        批量预处理图像列表
        
        将多张图像统一处理为模型输入格式。
        
        Args:
            images: 图像路径、数组或字节数据列表
            target_size: 目标尺寸
            normalize: 是否归一化到 [0, 1]
            
        Returns:
            批量处理的 numpy 数组 (N, H, W, C)
        """
        if not IMAGE_LIBS_AVAILABLE:
            raise RuntimeError("图像处理库不可用")

        start_time = time.time()
        processed_images = []

        for i, img_input in enumerate(images):
            try:
                if isinstance(img_input, str):
                    img_array = ImagePreprocessor.load_image_jpeg_fast(img_input)
                elif isinstance(img_input, bytes):
                    img_array = ImagePreprocessor.load_image_from_bytes(img_input)
                elif isinstance(img_input, np.ndarray):
                    img_array = img_input
                else:
                    logger.warning(f"不支持的输入类型 [{i}]: {type(img_input)}")
                    continue
                
                if img_array is not None:
                    processed = ImagePreprocessor.resize_with_padding(
                        img_array, target_size=target_size
                    )
                    processed_images.append(processed)
                    
            except Exception as e:
                logger.error(f"批量预处理第 {i} 张图像失败: {e}")
                continue

        if not processed_images:
            logger.warning("批量预处理结果为空")
            return np.array([])

        batch_array = np.stack(processed_images, axis=0)

        if normalize:
            batch_array = batch_array.astype(np.float32) / 255.0

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"批量预处理完成: 输入 {len(images)} 张, "
            f"成功 {len(processed_images)} 张, "
            f"输出形状 {batch_array.shape}, "
            f"耗时 {elapsed_ms:.2f}ms"
        )

        return batch_array


def preprocess_image_for_yolo(
    image: Union[Image.Image, np.ndarray],
    target_size: Tuple[int, int] = (640, 640)
) -> Image.Image:
    """
    为 YOLO 模型预处理的便捷函数
    
    将 PIL 图像或 numpy 数组转换为 YOLO 所需的格式
    
    Args:
        image: PIL 图像或 numpy 数组
        target_size: 目标尺寸（YOLO 默认 640x640）
        
    Returns:
        处理后的 PIL 图像
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    
    original_size = image.size
    target_w, target_h = target_size
    
    ratio = min(target_w / original_size[0], target_h / original_size[1])
    new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
    
    image = image.resize(new_size, Image.Resampling.BILINEAR)
    
    new_image = Image.new("RGB", target_size, (114, 114, 114))
    paste_x = (target_w - new_size[0]) // 2
    paste_y = (target_h - new_size[1]) // 2
    new_image.paste(image, (paste_x, paste_y))
    
    return new_image
