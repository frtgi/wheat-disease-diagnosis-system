# -*- coding: utf-8 -*-
"""
数据增强引擎 (Data Augmentation Engine)
根据研究文档，实现农业图像专用的数据增强策略

支持:
1. 几何变换增强
2. 颜色空间增强
3. 噪声与模糊增强
4. 光照变化增强
5. 混合增强 (Mixup, CutMix, Mosaic)
6. 领域特定增强 (叶片遮挡、病害模拟等)
"""
import os
import random
import math
from typing import List, Tuple, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import torch
from torch.utils.data import Dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2


class AugmentationType(Enum):
    """增强类型枚举"""
    GEOMETRIC = "geometric"       # 几何变换
    COLOR = "color"               # 颜色变换
    NOISE = "noise"               # 噪声
    LIGHTING = "lighting"         # 光照
    MIX = "mix"                   # 混合增强
    DOMAIN = "domain"             # 领域特定


@dataclass
class AugmentationConfig:
    """数据增强配置"""
    # 几何变换
    rotation_range: Tuple[int, int] = (-15, 15)
    scale_range: Tuple[float, float] = (0.9, 1.1)
    flip_horizontal: bool = True
    flip_vertical: bool = False
    
    # 颜色变换
    brightness_range: Tuple[float, float] = (0.8, 1.2)
    contrast_range: Tuple[float, float] = (0.8, 1.2)
    saturation_range: Tuple[float, float] = (0.8, 1.2)
    hue_range: Tuple[float, float] = (-0.1, 0.1)
    
    # 噪声
    gaussian_noise_prob: float = 0.3
    gaussian_noise_var: Tuple[float, float] = (0.001, 0.01)
    
    # 模糊
    blur_prob: float = 0.2
    blur_limit: int = 3
    
    # 光照
    lighting_prob: float = 0.3
    lighting_intensity: Tuple[float, float] = (0.8, 1.2)
    
    # 混合增强
    mixup_prob: float = 0.0
    cutmix_prob: float = 0.0
    mosaic_prob: float = 0.0
    
    # 领域特定
    random_occlusion_prob: float = 0.1
    occlusion_size_range: Tuple[float, float] = (0.02, 0.1)
    
    # 通用
    apply_prob: float = 0.5
    num_augmentations: int = 1


class GeometricAugmentation:
    """几何变换增强"""
    
    @staticmethod
    def rotate(image: np.ndarray, angle: float, center: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        旋转图像
        
        :param image: 输入图像
        :param angle: 旋转角度
        :param center: 旋转中心
        :return: 旋转后的图像
        """
        h, w = image.shape[:2]
        if center is None:
            center = (w // 2, h // 2)
        
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_CONSTANT, 
                                  borderValue=(128, 128, 128))
        return rotated
    
    @staticmethod
    def scale(image: np.ndarray, scale_factor: float) -> np.ndarray:
        """
        缩放图像
        
        :param image: 输入图像
        :param scale_factor: 缩放因子
        :return: 缩放后的图像
        """
        h, w = image.shape[:2]
        new_h, new_w = int(h * scale_factor), int(w * scale_factor)
        
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # 如果放大，裁剪中心区域；如果缩小，填充
        if scale_factor > 1.0:
            # 裁剪中心
            start_h = (new_h - h) // 2
            start_w = (new_w - w) // 2
            result = resized[start_h:start_h+h, start_w:start_w+w]
        else:
            # 填充
            result = np.full_like(image, 128)
            start_h = (h - new_h) // 2
            start_w = (w - new_w) // 2
            result[start_h:start_h+new_h, start_w:start_w+new_w] = resized
        
        return result
    
    @staticmethod
    def flip(image: np.ndarray, horizontal: bool = True) -> np.ndarray:
        """
        翻转图像
        
        :param image: 输入图像
        :param horizontal: 是否水平翻转
        :return: 翻转后的图像
        """
        if horizontal:
            return cv2.flip(image, 1)
        else:
            return cv2.flip(image, 0)
    
    @staticmethod
    def random_crop(image: np.ndarray, crop_size: Tuple[int, int]) -> np.ndarray:
        """
        随机裁剪
        
        :param image: 输入图像
        :param crop_size: 裁剪尺寸 (h, w)
        :return: 裁剪后的图像
        """
        h, w = image.shape[:2]
        crop_h, crop_w = crop_size
        
        if crop_h > h or crop_w > w:
            # 如果裁剪尺寸大于图像，先调整大小
            scale = max(crop_h / h, crop_w / w) * 1.2
            new_h, new_w = int(h * scale), int(w * scale)
            image = cv2.resize(image, (new_w, new_h))
            h, w = new_h, new_w
        
        # 随机选择裁剪位置
        start_h = random.randint(0, h - crop_h)
        start_w = random.randint(0, w - crop_w)
        
        return image[start_h:start_h+crop_h, start_w:start_w+crop_w]


class ColorAugmentation:
    """颜色空间增强"""
    
    @staticmethod
    def adjust_brightness(image: np.ndarray, factor: float) -> np.ndarray:
        """
        调整亮度
        
        :param image: 输入图像
        :param factor: 亮度因子
        :return: 调整后的图像
        """
        pil_image = Image.fromarray(image)
        enhancer = ImageEnhance.Brightness(pil_image)
        result = enhancer.enhance(factor)
        return np.array(result)
    
    @staticmethod
    def adjust_contrast(image: np.ndarray, factor: float) -> np.ndarray:
        """
        调整对比度
        
        :param image: 输入图像
        :param factor: 对比度因子
        :return: 调整后的图像
        """
        pil_image = Image.fromarray(image)
        enhancer = ImageEnhance.Contrast(pil_image)
        result = enhancer.enhance(factor)
        return np.array(result)
    
    @staticmethod
    def adjust_saturation(image: np.ndarray, factor: float) -> np.ndarray:
        """
        调整饱和度
        
        :param image: 输入图像
        :param factor: 饱和度因子
        :return: 调整后的图像
        """
        pil_image = Image.fromarray(image)
        enhancer = ImageEnhance.Color(pil_image)
        result = enhancer.enhance(factor)
        return np.array(result)
    
    @staticmethod
    def adjust_hue(image: np.ndarray, factor: float) -> np.ndarray:
        """
        调整色调
        
        :param image: 输入图像
        :param factor: 色调偏移 (-0.5 to 0.5)
        :return: 调整后的图像
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 0] = (hsv[:, :, 0] + factor * 180) % 180
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        return result
    
    @staticmethod
    def random_gamma(image: np.ndarray, gamma_range: Tuple[float, float] = (0.8, 1.2)) -> np.ndarray:
        """
        随机Gamma校正
        
        :param image: 输入图像
        :param gamma_range: Gamma范围
        :return: 调整后的图像
        """
        gamma = random.uniform(*gamma_range)
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
        return cv2.LUT(image, table)


class NoiseAugmentation:
    """噪声增强"""
    
    @staticmethod
    def add_gaussian_noise(image: np.ndarray, var: float = 0.01) -> np.ndarray:
        """
        添加高斯噪声
        
        :param image: 输入图像
        :param var: 噪声方差
        :return: 添加噪声后的图像
        """
        row, col, ch = image.shape
        sigma = var ** 0.5
        gauss = np.random.normal(0, sigma, (row, col, ch))
        gauss = gauss.reshape(row, col, ch)
        noisy = image.astype(np.float32) + gauss * 255
        return np.clip(noisy, 0, 255).astype(np.uint8)
    
    @staticmethod
    def add_salt_pepper_noise(image: np.ndarray, amount: float = 0.004) -> np.ndarray:
        """
        添加椒盐噪声
        
        :param image: 输入图像
        :param amount: 噪声比例
        :return: 添加噪声后的图像
        """
        s_vs_p = 0.5
        out = np.copy(image)
        
        # 盐噪声
        num_salt = np.ceil(amount * image.size * s_vs_p)
        coords = [np.random.randint(0, i - 1, int(num_salt)) for i in image.shape]
        out[coords[0], coords[1], :] = 255
        
        # 椒噪声
        num_pepper = np.ceil(amount * image.size * (1. - s_vs_p))
        coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in image.shape]
        out[coords[0], coords[1], :] = 0
        
        return out
    
    @staticmethod
    def apply_blur(image: np.ndarray, blur_type: str = "gaussian", ksize: int = 3) -> np.ndarray:
        """
        应用模糊
        
        :param image: 输入图像
        :param blur_type: 模糊类型 (gaussian, median, average)
        :param ksize: 核大小
        :return: 模糊后的图像
        """
        if blur_type == "gaussian":
            return cv2.GaussianBlur(image, (ksize, ksize), 0)
        elif blur_type == "median":
            return cv2.medianBlur(image, ksize)
        elif blur_type == "average":
            return cv2.blur(image, (ksize, ksize))
        else:
            return image


class DomainAugmentation:
    """领域特定增强 - 针对农业病害图像"""
    
    @staticmethod
    def random_occlusion(image: np.ndarray, occlusion_ratio: float = 0.05) -> np.ndarray:
        """
        随机遮挡 - 模拟叶片遮挡
        
        :param image: 输入图像
        :param occlusion_ratio: 遮挡比例
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy()
        
        # 计算遮挡区域大小
        area = h * w
        occlusion_area = int(area * occlusion_ratio)
        
        # 随机选择遮挡形状
        shape_type = random.choice(['rectangle', 'ellipse'])
        
        if shape_type == 'rectangle':
            # 矩形遮挡
            occ_w = int(math.sqrt(occlusion_area * random.uniform(0.5, 2)))
            occ_h = int(occlusion_area / occ_w)
            
            x = random.randint(0, max(0, w - occ_w))
            y = random.randint(0, max(0, h - occ_h))
            
            # 填充随机颜色（模拟其他叶片）
            color = random.choice([(0, 100, 0), (34, 139, 34), (107, 142, 35)])
            cv2.rectangle(result, (x, y), (x + occ_w, y + occ_h), color, -1)
        
        else:
            # 椭圆遮挡
            occ_w = int(math.sqrt(occlusion_area * random.uniform(0.5, 2)))
            occ_h = int(occlusion_area / occ_w)
            
            x = random.randint(occ_w // 2, w - occ_w // 2)
            y = random.randint(occ_h // 2, h - occ_h // 2)
            
            color = random.choice([(0, 100, 0), (34, 139, 34), (107, 142, 35)])
            cv2.ellipse(result, (x, y), (occ_w // 2, occ_h // 2), 0, 0, 360, color, -1)
        
        return result
    
    @staticmethod
    def simulate_shadow(image: np.ndarray, num_shadows: int = 1) -> np.ndarray:
        """
        模拟阴影 - 模拟光照不均
        
        :param image: 输入图像
        :param num_shadows: 阴影数量
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy().astype(np.float32)
        
        for _ in range(num_shadows):
            # 创建阴影掩码
            mask = np.ones((h, w), dtype=np.float32)
            
            # 随机多边形阴影
            num_points = random.randint(3, 6)
            points = []
            for _ in range(num_points):
                x = random.randint(0, w)
                y = random.randint(0, h)
                points.append([x, y])
            
            points = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [points], 0.4)  # 阴影区域亮度降低
            
            # 应用阴影
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            mask = np.expand_dims(mask, axis=2)
            result = result * mask
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def simulate_rain(image: np.ndarray, intensity: float = 0.1) -> np.ndarray:
        """
        模拟雨滴 - 模拟雨天拍摄
        
        :param image: 输入图像
        :param intensity: 雨滴强度
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy()
        
        # 生成雨滴
        num_drops = int(intensity * h * w / 100)
        
        for _ in range(num_drops):
            x = random.randint(0, w)
            y = random.randint(0, h)
            length = random.randint(5, 20)
            
            # 绘制雨滴
            cv2.line(result, (x, y), (x, y + length), (200, 200, 200), 1)
        
        return result
    
    @staticmethod
    def color_constancy(image: np.ndarray, power: int = 6, gamma: float = 0.5) -> np.ndarray:
        """
        颜色恒常性 - 模拟不同光照条件下的颜色变化
        
        :param image: 输入图像
        :param power: 幂次
        :param gamma: Gamma值
        :return: 增强后的图像
        """
        img = image.astype(np.float32) / 255.0
        
        # 计算每个通道的均值
        mean_r = np.mean(img[:, :, 0] ** power) ** (1 / power)
        mean_g = np.mean(img[:, :, 1] ** power) ** (1 / power)
        mean_b = np.mean(img[:, :, 2] ** power) ** (1 / power)
        
        # 计算灰度世界假设
        mean_gray = (mean_r + mean_g + mean_b) / 3
        
        # 调整每个通道
        img[:, :, 0] = img[:, :, 0] * (mean_gray / mean_r) ** gamma
        img[:, :, 1] = img[:, :, 1] * (mean_gray / mean_g) ** gamma
        img[:, :, 2] = img[:, :, 2] * (mean_gray / mean_b) ** gamma
        
        return np.clip(img * 255, 0, 255).astype(np.uint8)


class MixAugmentation:
    """混合增强技术"""
    
    @staticmethod
    def mixup(image1: np.ndarray, image2: np.ndarray, alpha: float = 0.4) -> Tuple[np.ndarray, float]:
        """
        Mixup增强
        
        :param image1: 第一张图像
        :param image2: 第二张图像
        :param alpha: Beta分布参数
        :return: (混合后的图像, 混合比例)
        """
        lam = np.random.beta(alpha, alpha)
        mixed = lam * image1.astype(np.float32) + (1 - lam) * image2.astype(np.float32)
        return mixed.astype(np.uint8), lam
    
    @staticmethod
    def cutmix(image1: np.ndarray, image2: np.ndarray, alpha: float = 1.0) -> np.ndarray:
        """
        CutMix增强
        
        :param image1: 第一张图像（目标）
        :param image2: 第二张图像（源）
        :param alpha: Beta分布参数
        :return: 混合后的图像
        """
        h, w = image1.shape[:2]
        
        # 随机裁剪区域
        lam = np.random.beta(alpha, alpha)
        cut_ratio = np.sqrt(1 - lam)
        cut_w = int(w * cut_ratio)
        cut_h = int(h * cut_ratio)
        
        # 随机位置
        cx = np.random.randint(w)
        cy = np.random.randint(h)
        
        x1 = np.clip(cx - cut_w // 2, 0, w)
        y1 = np.clip(cy - cut_h // 2, 0, h)
        x2 = np.clip(cx + cut_w // 2, 0, w)
        y2 = np.clip(cy + cut_h // 2, 0, h)
        
        # 应用CutMix
        result = image1.copy()
        result[y1:y2, x1:x2] = image2[y1:y2, x1:x2]
        
        return result
    
    @staticmethod
    def mosaic(images: List[np.ndarray], size: Tuple[int, int] = (640, 640)) -> np.ndarray:
        """
        Mosaic增强 - 将4张图像拼接成1张
        
        :param images: 图像列表（至少4张）
        :param size: 输出尺寸
        :return: 拼接后的图像
        """
        if len(images) < 4:
            raise ValueError("Mosaic需要至少4张图像")
        
        h, w = size
        mosaic_img = np.full((h, w, 3), 114, dtype=np.uint8)
        
        # 随机中心点
        xc = int(random.uniform(h * 0.25, h * 0.75))
        yc = int(random.uniform(w * 0.25, w * 0.75))
        
        indices = random.sample(range(len(images)), 4)
        
        for i, idx in enumerate(indices):
            img = images[idx]
            img_h, img_w = img.shape[:2]
            
            # 计算放置位置
            if i == 0:  # 左上
                x1, y1, x2, y2 = max(xc - img_w, 0), max(yc - img_h, 0), xc, yc
            elif i == 1:  # 右上
                x1, y1, x2, y2 = xc, max(yc - img_h, 0), min(xc + img_w, w), yc
            elif i == 2:  # 左下
                x1, y1, x2, y2 = max(xc - img_w, 0), yc, xc, min(yc + img_h, h)
            else:  # 右下
                x1, y1, x2, y2 = xc, yc, min(xc + img_w, w), min(yc + img_h, h)
            
            # 调整图像大小以适应区域
            new_w, new_h = x2 - x1, y2 - y1
            resized = cv2.resize(img, (new_w, new_h))
            
            # 放置图像
            mosaic_img[y1:y2, x1:x2] = resized
        
        return mosaic_img


class AugmentationEngine:
    """
    数据增强引擎
    
    提供统一的接口进行各种数据增强操作
    """
    
    def __init__(self, config: Optional[AugmentationConfig] = None):
        """
        初始化增强引擎
        
        :param config: 增强配置
        """
        self.config = config or AugmentationConfig()
        
        # 初始化各类增强器
        self.geometric = GeometricAugmentation()
        self.color = ColorAugmentation()
        self.noise = NoiseAugmentation()
        self.domain = DomainAugmentation()
        self.mix = MixAugmentation()
        
        print("🎨 [Augmentation Engine] 数据增强引擎初始化完成")
    
    def augment(self, image: np.ndarray, aug_type: Optional[AugmentationType] = None) -> np.ndarray:
        """
        对图像进行增强
        
        :param image: 输入图像 (H, W, C)
        :param aug_type: 增强类型（None表示随机选择）
        :return: 增强后的图像
        """
        if aug_type is None:
            # 随机选择增强类型
            aug_type = random.choice(list(AugmentationType))
        
        result = image.copy()
        
        if aug_type == AugmentationType.GEOMETRIC:
            result = self._apply_geometric(result)
        elif aug_type == AugmentationType.COLOR:
            result = self._apply_color(result)
        elif aug_type == AugmentationType.NOISE:
            result = self._apply_noise(result)
        elif aug_type == AugmentationType.LIGHTING:
            result = self._apply_lighting(result)
        elif aug_type == AugmentationType.DOMAIN:
            result = self._apply_domain(result)
        
        return result
    
    def _apply_geometric(self, image: np.ndarray) -> np.ndarray:
        """应用几何变换"""
        result = image.copy()
        
        # 旋转
        if random.random() < self.config.apply_prob:
            angle = random.uniform(*self.config.rotation_range)
            result = self.geometric.rotate(result, angle)
        
        # 缩放
        if random.random() < self.config.apply_prob:
            scale = random.uniform(*self.config.scale_range)
            result = self.geometric.scale(result, scale)
        
        # 水平翻转
        if self.config.flip_horizontal and random.random() < 0.5:
            result = self.geometric.flip(result, horizontal=True)
        
        # 垂直翻转
        if self.config.flip_vertical and random.random() < 0.5:
            result = self.geometric.flip(result, horizontal=False)
        
        return result
    
    def _apply_color(self, image: np.ndarray) -> np.ndarray:
        """应用颜色变换"""
        result = image.copy()
        
        # 亮度
        if random.random() < self.config.apply_prob:
            factor = random.uniform(*self.config.brightness_range)
            result = self.color.adjust_brightness(result, factor)
        
        # 对比度
        if random.random() < self.config.apply_prob:
            factor = random.uniform(*self.config.contrast_range)
            result = self.color.adjust_contrast(result, factor)
        
        # 饱和度
        if random.random() < self.config.apply_prob:
            factor = random.uniform(*self.config.saturation_range)
            result = self.color.adjust_saturation(result, factor)
        
        # 色调
        if random.random() < self.config.apply_prob:
            factor = random.uniform(*self.config.hue_range)
            result = self.color.adjust_hue(result, factor)
        
        return result
    
    def _apply_noise(self, image: np.ndarray) -> np.ndarray:
        """应用噪声"""
        result = image.copy()
        
        # 高斯噪声
        if random.random() < self.config.gaussian_noise_prob:
            var = random.uniform(*self.config.gaussian_noise_var)
            result = self.noise.add_gaussian_noise(result, var)
        
        # 模糊
        if random.random() < self.config.blur_prob:
            ksize = random.choice([3, 5, 7])
            result = self.noise.apply_blur(result, blur_type="gaussian", ksize=ksize)
        
        return result
    
    def _apply_lighting(self, image: np.ndarray) -> np.ndarray:
        """应用光照变换"""
        result = image.copy()
        
        # Gamma校正
        result = self.color.random_gamma(result)
        
        # 阴影模拟
        if random.random() < self.config.lighting_prob:
            result = self.domain.simulate_shadow(result, num_shadows=random.randint(1, 2))
        
        return result
    
    def _apply_domain(self, image: np.ndarray) -> np.ndarray:
        """应用领域特定增强"""
        result = image.copy()
        
        # 随机遮挡
        if random.random() < self.config.random_occlusion_prob:
            ratio = random.uniform(*self.config.occlusion_size_range)
            result = self.domain.random_occlusion(result, occlusion_ratio=ratio)
        
        # 颜色恒常性
        if random.random() < self.config.apply_prob:
            result = self.domain.color_constancy(result)
        
        return result
    
    def augment_batch(
        self,
        images: List[np.ndarray],
        num_augmentations: int = 1
    ) -> List[np.ndarray]:
        """
        批量增强图像
        
        :param images: 图像列表
        :param num_augmentations: 每张图像增强数量
        :return: 增强后的图像列表
        """
        augmented = []
        
        for img in images:
            for _ in range(num_augmentations):
                aug_img = self.augment(img)
                augmented.append(aug_img)
        
        return augmented
    
    def get_albumentations_pipeline(self) -> A.Compose:
        """
        获取Albumentations增强管道
        
        :return: Albumentations Compose对象
        """
        transform = A.Compose([
            A.HorizontalFlip(p=0.5 if self.config.flip_horizontal else 0),
            A.VerticalFlip(p=0.5 if self.config.flip_vertical else 0),
            A.Rotate(limit=self.config.rotation_range, p=self.config.apply_prob),
            A.RandomScale(scale_limit=0.1, p=self.config.apply_prob),
            A.ColorJitter(
                brightness=self.config.brightness_range[1] - 1,
                contrast=self.config.contrast_range[1] - 1,
                saturation=self.config.saturation_range[1] - 1,
                hue=self.config.hue_range[1],
                p=self.config.apply_prob
            ),
            A.GaussNoise(var_limit=self.config.gaussian_noise_var, p=self.config.gaussian_noise_prob),
            A.Blur(blur_limit=self.config.blur_limit, p=self.config.blur_prob),
            A.RandomGamma(gamma_limit=(80, 120), p=self.config.apply_prob),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
        
        return transform


def test_augmentation_engine():
    """测试数据增强引擎"""
    print("=" * 70)
    print("🧪 测试数据增强引擎")
    print("=" * 70)
    
    # 创建增强引擎
    config = AugmentationConfig(
        rotation_range=(-30, 30),
        brightness_range=(0.7, 1.3),
        apply_prob=0.8
    )
    engine = AugmentationEngine(config)
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    
    # 测试几何增强
    print("\n" + "=" * 70)
    print("🧪 测试几何增强")
    print("=" * 70)
    
    aug_geom = engine.augment(test_image, AugmentationType.GEOMETRIC)
    print(f"✅ 几何增强: {test_image.shape} -> {aug_geom.shape}")
    
    # 测试颜色增强
    print("\n" + "=" * 70)
    print("🧪 测试颜色增强")
    print("=" * 70)
    
    aug_color = engine.augment(test_image, AugmentationType.COLOR)
    print(f"✅ 颜色增强: 输入均值 {test_image.mean():.2f} -> 输出均值 {aug_color.mean():.2f}")
    
    # 测试噪声增强
    print("\n" + "=" * 70)
    print("🧪 测试噪声增强")
    print("=" * 70)
    
    aug_noise = engine.augment(test_image, AugmentationType.NOISE)
    print(f"✅ 噪声增强: 输入标准差 {test_image.std():.2f} -> 输出标准差 {aug_noise.std():.2f}")
    
    # 测试领域增强
    print("\n" + "=" * 70)
    print("🧪 测试领域特定增强")
    print("=" * 70)
    
    aug_domain = engine.augment(test_image, AugmentationType.DOMAIN)
    print(f"✅ 领域增强完成")
    
    # 测试批量增强
    print("\n" + "=" * 70)
    print("🧪 测试批量增强")
    print("=" * 70)
    
    batch = [test_image.copy() for _ in range(5)]
    augmented_batch = engine.augment_batch(batch, num_augmentations=2)
    print(f"✅ 批量增强: {len(batch)} 张 -> {len(augmented_batch)} 张")
    
    # 测试Albumentations管道
    print("\n" + "=" * 70)
    print("🧪 测试Albumentations管道")
    print("=" * 70)
    
    pipeline = engine.get_albumentations_pipeline()
    transformed = pipeline(image=test_image)
    print(f"✅ Albumentations: 输入 {test_image.shape} -> 输出 {transformed['image'].shape}")
    
    print("\n" + "=" * 70)
    print("✅ 数据增强引擎测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_augmentation_engine()
