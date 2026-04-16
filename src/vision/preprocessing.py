# -*- coding: utf-8 -*-
"""
图像预处理模块

提供图像预处理功能，包括：
- 图像归一化
- 尺寸自适应
- 数据增强
- 质量评估
"""
import os
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PreprocessConfig:
    """预处理配置"""
    target_size: Tuple[int, int] = (640, 640)
    normalize: bool = True
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
    preserve_aspect_ratio: bool = False
    pad_color: Tuple[int, int, int] = (114, 114, 114)
    min_size: int = 32
    max_size: int = 1280


class ImagePreprocessor:
    """
    图像预处理器
    
    提供完整的图像预处理管道
    """
    
    def __init__(self, config: Optional[PreprocessConfig] = None):
        """
        初始化预处理器
        
        :param config: 预处理配置
        """
        self.config = config or PreprocessConfig()
        print(f"🖼️ [ImagePreprocessor] 初始化完成")
        print(f"   目标尺寸: {self.config.target_size}")
    
    def preprocess(
        self,
        image: np.ndarray,
        return_tensor: bool = False
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        执行完整预处理
        
        :param image: 输入图像 (BGR格式)
        :param return_tensor: 是否返回tensor格式
        :return: (预处理后图像, 元数据)
        """
        metadata = {
            "original_shape": image.shape,
            "preprocess_steps": []
        }
        
        # 1. 颜色空间转换
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            metadata["preprocess_steps"].append("gray_to_bgr")
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            metadata["preprocess_steps"].append("bgra_to_bgr")
        
        # 2. 尺寸调整
        image, scale_info = self._resize_image(image)
        metadata["scale_info"] = scale_info
        metadata["preprocess_steps"].append("resize")
        
        # 3. 归一化
        if self.config.normalize:
            image = self._normalize(image)
            metadata["preprocess_steps"].append("normalize")
        
        # 4. 转换为tensor格式
        if return_tensor:
            image = self._to_tensor(image)
            metadata["preprocess_steps"].append("to_tensor")
        
        metadata["processed_shape"] = image.shape
        
        return image, metadata
    
    def _resize_image(
        self,
        image: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        调整图像尺寸
        
        :param image: 输入图像
        :return: (调整后图像, 缩放信息)
        """
        h, w = image.shape[:2]
        target_h, target_w = self.config.target_size
        
        scale_info = {
            "original_size": (w, h),
            "target_size": (target_w, target_h),
            "scale": 1.0,
            "pad": (0, 0, 0, 0)
        }
        
        if self.config.preserve_aspect_ratio:
            # 保持宽高比
            scale = min(target_w / w, target_h / h)
            scale = max(scale, self.config.min_size / max(w, h))
            scale = min(scale, self.config.max_size / max(w, h))
            
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # 填充
            pad_w = target_w - new_w
            pad_h = target_h - new_h
            pad_top = pad_h // 2
            pad_bottom = pad_h - pad_top
            pad_left = pad_w // 2
            pad_right = pad_w - pad_left
            
            image = cv2.copyMakeBorder(
                resized,
                pad_top, pad_bottom, pad_left, pad_right,
                cv2.BORDER_CONSTANT,
                value=self.config.pad_color
            )
            
            scale_info["scale"] = scale
            scale_info["pad"] = (pad_left, pad_top, pad_right, pad_bottom)
        else:
            # 直接缩放
            image = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
            scale_info["scale"] = (target_w / w, target_h / h)
        
        return image, scale_info
    
    def _normalize(self, image: np.ndarray) -> np.ndarray:
        """
        归一化图像
        
        :param image: 输入图像 (0-255)
        :return: 归一化图像
        """
        image = image.astype(np.float32) / 255.0
        mean = np.array(self.config.mean).reshape(1, 1, 3)
        std = np.array(self.config.std).reshape(1, 1, 3)
        image = (image - mean) / std
        return image
    
    def _to_tensor(self, image: np.ndarray) -> np.ndarray:
        """
        转换为tensor格式 (CHW)
        
        :param image: 输入图像 (HWC)
        :return: tensor格式 (CHW)
        """
        return np.transpose(image, (2, 0, 1))
    
    def preprocess_batch(
        self,
        images: list,
        return_tensors: bool = True
    ) -> Tuple[np.ndarray, list]:
        """
        批量预处理
        
        :param images: 图像列表
        :param return_tensors: 是否返回tensor格式
        :return: (批量图像, 元数据列表)
        """
        processed = []
        metadata_list = []
        
        for image in images:
            proc_image, metadata = self.preprocess(image, return_tensors)
            processed.append(proc_image)
            metadata_list.append(metadata)
        
        if return_tensors and len(processed) > 0:
            processed = np.stack(processed, axis=0)
        
        return processed, metadata_list


class ImageQualityAssessor:
    """
    图像质量评估器
    
    评估图像质量，检测模糊、曝光等问题
    """
    
    def __init__(self):
        """初始化质量评估器"""
        self.blur_threshold = 100.0
        self.brightness_range = (50, 200)
        self.contrast_min = 20.0
    
    def assess(self, image: np.ndarray) -> Dict[str, Any]:
        """
        评估图像质量
        
        :param image: 输入图像
        :return: 质量评估结果
        """
        result = {
            "is_valid": True,
            "warnings": [],
            "scores": {}
        }
        
        # 1. 模糊检测
        blur_score = self._check_blur(image)
        result["scores"]["blur"] = blur_score
        if blur_score < self.blur_threshold:
            result["warnings"].append(f"图像可能模糊 (Laplacian方差: {blur_score:.1f})")
        
        # 2. 亮度检测
        brightness = self._check_brightness(image)
        result["scores"]["brightness"] = brightness
        if brightness < self.brightness_range[0]:
            result["warnings"].append(f"图像过暗 (亮度: {brightness:.1f})")
        elif brightness > self.brightness_range[1]:
            result["warnings"].append(f"图像过亮 (亮度: {brightness:.1f})")
        
        # 3. 对比度检测
        contrast = self._check_contrast(image)
        result["scores"]["contrast"] = contrast
        if contrast < self.contrast_min:
            result["warnings"].append(f"图像对比度过低 (对比度: {contrast:.1f})")
        
        # 4. 尺寸检测
        h, w = image.shape[:2]
        result["scores"]["size"] = (w, h)
        if w < 224 or h < 224:
            result["warnings"].append(f"图像尺寸过小 ({w}x{h})")
        
        if len(result["warnings"]) > 0:
            result["is_valid"] = False
        
        return result
    
    def _check_blur(self, image: np.ndarray) -> float:
        """检测模糊程度"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def _check_brightness(self, image: np.ndarray) -> float:
        """检测亮度"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return np.mean(gray)
    
    def _check_contrast(self, image: np.ndarray) -> float:
        """检测对比度"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return gray.std()


class DataAugmenter:
    """
    数据增强器
    
    提供训练时的数据增强功能
    """
    
    def __init__(self, augment_prob: float = 0.5):
        """
        初始化增强器
        
        :param augment_prob: 增强概率
        """
        self.augment_prob = augment_prob
    
    def augment(self, image: np.ndarray) -> np.ndarray:
        """
        执行数据增强
        
        :param image: 输入图像
        :return: 增强后图像
        """
        if np.random.random() > self.augment_prob:
            return image
        
        # 随机选择增强方法
        augmentations = [
            self._random_flip,
            self._random_brightness,
            self._random_contrast,
            self._random_hue,
        ]
        
        aug = np.random.choice(augmentations)
        return aug(image)
    
    def _random_flip(self, image: np.ndarray) -> np.ndarray:
        """随机翻转"""
        if np.random.random() > 0.5:
            return cv2.flip(image, 1)
        return image
    
    def _random_brightness(self, image: np.ndarray) -> np.ndarray:
        """随机亮度"""
        factor = 1.0 + np.random.uniform(-0.2, 0.2)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def _random_contrast(self, image: np.ndarray) -> np.ndarray:
        """随机对比度"""
        factor = 1.0 + np.random.uniform(-0.2, 0.2)
        mean = image.mean()
        return np.clip((image - mean) * factor + mean, 0, 255).astype(np.uint8)
    
    def _random_hue(self, image: np.ndarray) -> np.ndarray:
        """随机色调"""
        shift = np.random.randint(-10, 10)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(int) + shift) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def create_preprocessor(
    target_size: Tuple[int, int] = (640, 640),
    normalize: bool = True,
    preserve_aspect_ratio: bool = False
) -> ImagePreprocessor:
    """
    工厂函数: 创建预处理器
    
    :param target_size: 目标尺寸
    :param normalize: 是否归一化
    :param preserve_aspect_ratio: 是否保持宽高比
    :return: ImagePreprocessor实例
    """
    config = PreprocessConfig(
        target_size=target_size,
        normalize=normalize,
        preserve_aspect_ratio=preserve_aspect_ratio
    )
    return ImagePreprocessor(config)
