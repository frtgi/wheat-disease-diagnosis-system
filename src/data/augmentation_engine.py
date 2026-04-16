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


class GenerativeSynthesis:
    """
    生成式合成 - 根据文档2.2节
    对于样本稀缺的病害，利用生成模型合成逼真图像
    """
    
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        """
        初始化生成式合成器
        
        :param device: 计算设备
        """
        self.device = device
        self.diffusion_model = None
        self._model_loaded = False
    
    def _load_model(self):
        """延迟加载扩散模型"""
        if self._model_loaded:
            return
        
        try:
            from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
            import torch
            
            model_id = "stabilityai/stable-diffusion-2-1-base"
            
            print(f"🎨 [GenerativeSynthesis] 正在加载Stable Diffusion模型...")
            print(f"   设备: {self.device}")
            
            scheduler = EulerDiscreteScheduler.from_pretrained(model_id, subfolder="scheduler")
            self.diffusion_model = StableDiffusionPipeline.from_pretrained(
                model_id,
                scheduler=scheduler,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32
            )
            self.diffusion_model = self.diffusion_model.to(self.device)
            
            self._model_loaded = True
            print("✅ [GenerativeSynthesis] Stable Diffusion模型加载完成")
            
        except ImportError as e:
            print(f"⚠️ [GenerativeSynthesis] diffusers库未安装: {e}")
            print("   请运行: pip install diffusers transformers accelerate")
        except Exception as e:
            print(f"⚠️ [GenerativeSynthesis] 模型加载失败: {e}")
    
    def generate_disease_image(
        self,
        disease_name: str,
        symptom_description: str,
        num_images: int = 1,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        生成病害图像
        
        根据文档2.2节：输入提示词"小麦叶片上覆盖白色粉状霉层，伴有黑色小点"，
        生成逼真的白粉病晚期图像
        
        :param disease_name: 病害名称
        :param symptom_description: 症状描述
        :param num_images: 生成数量
        :param num_inference_steps: 推理步数
        :param guidance_scale: 引导比例
        :param seed: 随机种子
        :return: 生成的图像列表
        """
        self._load_model()
        
        if self.diffusion_model is None:
            print("⚠️ 扩散模型未加载，返回空白图像")
            return [np.zeros((512, 512, 3), dtype=np.uint8) for _ in range(num_images)]
        
        # 构建提示词
        prompt = f"wheat leaf with {disease_name}, {symptom_description}, "
        prompt += "agricultural photography, detailed texture, natural lighting"
        
        negative_prompt = "blurry, low quality, distorted, artificial, cartoon"
        
        # 设置随机种子
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        images = []
        for i in range(num_images):
            with torch.no_grad():
                output = self.diffusion_model(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                )
            
            # 转换为numpy数组
            pil_image = output.images[0]
            np_image = np.array(pil_image)
            images.append(np_image)
            
            if seed is not None:
                seed += 1
                generator = torch.Generator(device=self.device).manual_seed(seed)
        
        return images
    
    def generate_synthetic_dataset(
        self,
        disease_info: Dict[str, str],
        num_samples: int = 100,
        output_dir: Optional[str] = None
    ) -> List[np.ndarray]:
        """
        生成合成数据集
        
        :param disease_info: 病害信息字典 {name: description}
        :param num_samples: 每种病害生成数量
        :param output_dir: 输出目录
        :return: 生成的图像列表
        """
        all_images = []
        
        for disease_name, description in disease_info.items():
            print(f"\n🎨 生成 {disease_name} 样本...")
            
            images = self.generate_disease_image(
                disease_name=disease_name,
                symptom_description=description,
                num_images=num_samples
            )
            
            if output_dir:
                disease_dir = os.path.join(output_dir, disease_name)
                os.makedirs(disease_dir, exist_ok=True)
                
                for i, img in enumerate(images):
                    img_path = os.path.join(disease_dir, f"synthetic_{i:04d}.jpg")
                    cv2.imwrite(img_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            
            all_images.extend(images)
        
        return all_images


class AdvancedMosaicAugmentation:
    """
    高级Mosaic增强 - 根据文档2.2节
    针对条锈病和叶锈病病斑细小的特点，优化Mosaic增强策略
    """
    
    @staticmethod
    def mosaic_with_small_objects(
        images: List[np.ndarray],
        bboxes_list: Optional[List[List[np.ndarray]]] = None,
        size: Tuple[int, int] = (640, 640),
        min_object_size: int = 10
    ) -> Tuple[np.ndarray, Optional[List[np.ndarray]]]:
        """
        带小目标保护的Mosaic增强
        
        :param images: 图像列表（至少4张）
        :param bboxes_list: 边界框列表（可选）
        :param size: 输出尺寸
        :param min_object_size: 最小目标尺寸
        :return: (增强后的图像, 调整后的边界框)
        """
        if len(images) < 4:
            raise ValueError("Mosaic需要至少4张图像")
        
        h, w = size
        mosaic_img = np.full((h, w, 3), 114, dtype=np.uint8)
        mosaic_bboxes = []
        
        # 随机中心点（偏向中心以保护小目标）
        xc = int(random.uniform(h * 0.35, h * 0.65))
        yc = int(random.uniform(w * 0.35, w * 0.65))
        
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
            
            # 调整图像大小
            new_w, new_h = x2 - x1, y2 - y1
            scale_x = new_w / img_w
            scale_y = new_h / img_h
            
            resized = cv2.resize(img, (new_w, new_h))
            mosaic_img[y1:y2, x1:x2] = resized
            
            # 调整边界框
            if bboxes_list and idx < len(bboxes_list):
                for bbox in bboxes_list[idx]:
                    # bbox格式: [x1, y1, x2, y2] 或 [cx, cy, w, h]
                    if len(bbox) >= 4:
                        # 假设是xyxy格式
                        new_bbox = bbox.copy()
                        new_bbox[0] = int(bbox[0] * scale_x) + x1
                        new_bbox[1] = int(bbox[1] * scale_y) + y1
                        new_bbox[2] = int(bbox[2] * scale_x) + x1
                        new_bbox[3] = int(bbox[3] * scale_y) + y1
                        
                        # 检查目标是否足够大
                        bbox_w = new_bbox[2] - new_bbox[0]
                        bbox_h = new_bbox[3] - new_bbox[1]
                        
                        if bbox_w >= min_object_size and bbox_h >= min_object_size:
                            mosaic_bboxes.append(new_bbox)
        
        return mosaic_img, mosaic_bboxes if mosaic_bboxes else None
    
    @staticmethod
    def mosaic_9(images: List[np.ndarray], size: Tuple[int, int] = (640, 640)) -> np.ndarray:
        """
        9宫格Mosaic增强 - 更密集的混合
        
        :param images: 图像列表（至少9张）
        :param size: 输出尺寸
        :return: 拼接后的图像
        """
        if len(images) < 9:
            # 如果不足9张，复用部分图像
            while len(images) < 9:
                images.append(images[len(images) % len(images[:4])])
        
        h, w = size
        cell_h, cell_w = h // 3, w // 3
        mosaic_img = np.full((h, w, 3), 114, dtype=np.uint8)
        
        indices = random.sample(range(len(images)), min(9, len(images)))
        
        for i, idx in enumerate(indices):
            row = i // 3
            col = i % 3
            
            img = images[idx]
            resized = cv2.resize(img, (cell_w, cell_h))
            
            y1, y2 = row * cell_h, (row + 1) * cell_h
            x1, x2 = col * cell_w, (col + 1) * cell_w
            
            mosaic_img[y1:y2, x1:x2] = resized
        
        return mosaic_img


class HighlightSimulation:
    """
    高光模拟增强 - 根据文档2.2节
    针对早晨露水可能导致病斑反光的问题，引入高光模拟增强
    """
    
    @staticmethod
    def add_specular_highlight(
        image: np.ndarray,
        num_highlights: int = 3,
        intensity_range: Tuple[float, float] = (0.3, 0.7),
        size_range: Tuple[int, int] = (5, 20)
    ) -> np.ndarray:
        """
        添加镜面高光 - 模拟露水反光
        
        :param image: 输入图像
        :param num_highlights: 高光数量
        :param intensity_range: 强度范围
        :param size_range: 大小范围
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy().astype(np.float32)
        
        for _ in range(num_highlights):
            # 随机位置
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            
            # 随机大小
            size = random.randint(*size_range)
            
            # 随机强度
            intensity = random.uniform(*intensity_range)
            
            # 创建高光掩码
            mask = np.zeros((h, w), dtype=np.float32)
            cv2.circle(mask, (x, y), size, intensity, -1)
            
            # 高斯模糊使高光更自然
            mask = cv2.GaussianBlur(mask, (size * 2 + 1, size * 2 + 1), 0)
            
            # 应用高光
            mask = np.expand_dims(mask, axis=2)
            result = result + mask * 255
            result = np.clip(result, 0, 255)
        
        return result.astype(np.uint8)
    
    @staticmethod
    def add_dew_drops(
        image: np.ndarray,
        num_drops: int = 20,
        drop_size_range: Tuple[int, int] = (2, 6)
    ) -> np.ndarray:
        """
        添加露水滴 - 模拟清晨露水
        
        :param image: 输入图像
        :param num_drops: 露水滴数量
        :param drop_size_range: 水滴大小范围
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy()
        
        for _ in range(num_drops):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            size = random.randint(*drop_size_range)
            
            # 创建水滴效果（半透明高光）
            overlay = result.copy()
            cv2.circle(overlay, (x, y), size, (220, 230, 240), -1)
            
            # 添加高光边缘
            cv2.circle(overlay, (x - size // 3, y - size // 3), size // 2, (255, 255, 255), -1)
            
            # 混合
            alpha = 0.3
            result = cv2.addWeighted(overlay, alpha, result, 1 - alpha, 0)
        
        return result
    
    @staticmethod
    def simulate_morning_dew(image: np.ndarray, intensity: float = 0.5) -> np.ndarray:
        """
        模拟早晨露水效果 - 综合效果
        
        :param image: 输入图像
        :param intensity: 效果强度
        :return: 增强后的图像
        """
        result = image.copy()
        
        # 添加露水滴
        num_drops = int(20 * intensity)
        result = HighlightSimulation.add_dew_drops(result, num_drops=num_drops)
        
        # 添加高光
        num_highlights = int(3 * intensity)
        result = HighlightSimulation.add_specular_highlight(result, num_highlights=num_highlights)
        
        # 轻微增加整体亮度（模拟清晨光线）
        result = cv2.convertScaleAbs(result, alpha=1.0 + 0.1 * intensity, beta=5)
        
        return result


class ElongatedLesionAugmentation:
    """
    细长病斑增强 - 根据文档2.2节
    针对条锈病等细长病斑的形态学增强
    """
    
    @staticmethod
    def generate_elongated_lesion(
        image_shape: Tuple[int, int],
        length_range: Tuple[int, int] = (20, 100),
        width_range: Tuple[int, int] = (2, 8),
        color: Tuple[int, int, int] = (255, 200, 0),
        blur_sigma: float = 1.0
    ) -> np.ndarray:
        """
        生成细长病斑形状
        
        :param image_shape: 图像形状 (H, W)
        :param length_range: 长度范围
        :param width_range: 宽度范围
        :param color: 病斑颜色 (B, G, R)
        :param blur_sigma: 模糊程度
        :return: 病斑掩码
        """
        h, w = image_shape
        mask = np.zeros((h, w, 3), dtype=np.uint8)
        
        # 随机位置
        cx = random.randint(0, w)
        cy = random.randint(0, h)
        
        # 随机尺寸
        length = random.randint(*length_range)
        width = random.randint(*width_range)
        
        # 随机角度
        angle = random.uniform(0, 180)
        
        # 绘制椭圆
        cv2.ellipse(mask, (cx, cy), (length // 2, width // 2), angle, 0, 360, color, -1)
        
        # 添加模糊
        if blur_sigma > 0:
            mask = cv2.GaussianBlur(mask, (0, 0), blur_sigma)
        
        return mask
    
    @staticmethod
    def add_stripe_rust_symptom(
        image: np.ndarray,
        num_stripes: int = 5,
        intensity: float = 0.7
    ) -> np.ndarray:
        """
        添加条锈病条纹症状
        
        :param image: 输入图像
        :param num_stripes: 条纹数量
        :param intensity: 叠加强度
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy().astype(np.float32)
        
        for _ in range(num_stripes):
            # 生成条纹
            stripe = ElongatedLesionAugmentation.generate_elongated_lesion(
                (h, w),
                length_range=(30, 80),
                width_range=(2, 5),
                color=(0, 200, 255),  # 黄色条纹
                blur_sigma=0.5
            )
            
            # 叠加
            alpha = random.uniform(0.3, intensity)
            result = result * (1 - alpha) + stripe.astype(np.float32) * alpha
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def add_powdery_mildew_symptom(
        image: np.ndarray,
        num_spots: int = 10,
        intensity: float = 0.6
    ) -> np.ndarray:
        """
        添加白粉病症状
        
        :param image: 输入图像
        :param num_spots: 病斑数量
        :param intensity: 叠加强度
        :return: 增强后的图像
        """
        h, w = image.shape[:2]
        result = image.copy().astype(np.float32)
        
        for _ in range(num_spots):
            # 随机位置
            cx = random.randint(0, w)
            cy = random.randint(0, h)
            
            # 随机大小
            size = random.randint(10, 40)
            
            # 白色霉层
            color = (240, 240, 240)
            
            # 绘制不规则形状
            overlay = np.zeros_like(result)
            num_points = random.randint(5, 8)
            points = []
            for _ in range(num_points):
                angle = random.uniform(0, 2 * np.pi)
                r = random.uniform(size * 0.5, size)
                px = int(cx + r * np.cos(angle))
                py = int(cy + r * np.sin(angle))
                points.append([px, py])
            
            points = np.array(points, dtype=np.int32)
            cv2.fillPoly(overlay, [points], color)
            
            # 模糊
            overlay = cv2.GaussianBlur(overlay, (0, 0), 2)
            
            # 叠加
            alpha = random.uniform(0.2, intensity)
            mask = (overlay.sum(axis=2) > 0).astype(np.float32)
            mask = np.expand_dims(mask, axis=2)
            result = result * (1 - mask * alpha) + overlay * alpha
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def morphological_enhancement(
        image: np.ndarray,
        operation: str = "dilate",
        kernel_size: int = 3,
        iterations: int = 1
    ) -> np.ndarray:
        """
        形态学增强
        
        :param image: 输入图像
        :param operation: 操作类型 (dilate, erode, open, close)
        :param kernel_size: 核大小
        :param iterations: 迭代次数
        :return: 增强后的图像
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        if operation == "dilate":
            return cv2.dilate(image, kernel, iterations=iterations)
        elif operation == "erode":
            return cv2.erode(image, kernel, iterations=iterations)
        elif operation == "open":
            return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=iterations)
        elif operation == "close":
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        else:
            return image
    
    @staticmethod
    def enhance_lesion_contrast(
        image: np.ndarray,
        lesion_color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]] = None
    ) -> np.ndarray:
        """
        增强病斑对比度
        
        :param image: 输入图像
        :param lesion_color_range: 病斑颜色范围 (lower, upper)
        :return: 增强后的图像
        """
        if lesion_color_range is None:
            # 默认黄色病斑范围
            lower = np.array([0, 150, 150])
            upper = np.array([50, 255, 255])
        else:
            lower = np.array(lesion_color_range[0])
            upper = np.array(lesion_color_range[1])
        
        # 转换到HSV空间
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # 创建病斑掩码
        mask = cv2.inRange(hsv, lower, upper)
        
        # 增强病斑区域
        result = image.copy()
        lesion_pixels = mask > 0
        
        # 增加饱和度和亮度
        hsv[:, :, 1][lesion_pixels] = np.clip(hsv[:, :, 1][lesion_pixels] * 1.2, 0, 255)
        hsv[:, :, 2][lesion_pixels] = np.clip(hsv[:, :, 2][lesion_pixels] * 1.1, 0, 255)
        
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        return result


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
    根据文档2.2节实现农业图像专用增强策略
    """
    
    def __init__(self, config: Optional[AugmentationConfig] = None, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        """
        初始化增强引擎
        
        :param config: 增强配置
        :param device: 计算设备（用于生成式合成）
        """
        self.config = config or AugmentationConfig()
        self.device = device
        
        # 初始化各类增强器
        self.geometric = GeometricAugmentation()
        self.color = ColorAugmentation()
        self.noise = NoiseAugmentation()
        self.domain = DomainAugmentation()
        self.mix = MixAugmentation()
        
        # 高级增强器
        self.advanced_mosaic = AdvancedMosaicAugmentation()
        self.highlight = HighlightSimulation()
        self.generative = GenerativeSynthesis(device=device)
        self.elongated_lesion = ElongatedLesionAugmentation()
        
        print("🎨 [Augmentation Engine] 数据增强引擎初始化完成")
        print("   集成: 几何变换、颜色变换、噪声、领域特定、高级Mosaic、高光模拟、生成式合成、细长病斑增强")
    
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
    
    def apply_advanced_mosaic(
        self,
        images: List[np.ndarray],
        bboxes_list: Optional[List[List[np.ndarray]]] = None,
        size: Tuple[int, int] = (640, 640),
        protect_small_objects: bool = True
    ) -> Tuple[np.ndarray, Optional[List[np.ndarray]]]:
        """
        应用高级Mosaic增强 - 根据文档2.2节
        针对条锈病和叶锈病病斑细小的特点优化
        
        :param images: 图像列表
        :param bboxes_list: 边界框列表
        :param size: 输出尺寸
        :param protect_small_objects: 是否保护小目标
        :return: (增强图像, 边界框)
        """
        if protect_small_objects and bboxes_list:
            return self.advanced_mosaic.mosaic_with_small_objects(
                images, bboxes_list, size
            )
        else:
            return self.mix.mosaic(images, size), None
    
    def apply_morning_dew_simulation(
        self,
        image: np.ndarray,
        intensity: float = 0.5
    ) -> np.ndarray:
        """
        应用早晨露水模拟 - 根据文档2.2节
        针对早晨露水可能导致病斑反光的问题
        
        :param image: 输入图像
        :param intensity: 效果强度 (0-1)
        :return: 增强后的图像
        """
        return self.highlight.simulate_morning_dew(image, intensity)
    
    def apply_highlight_augmentation(
        self,
        image: np.ndarray,
        num_highlights: int = 3
    ) -> np.ndarray:
        """
        应用高光增强 - 提高模型对反光的鲁棒性
        
        :param image: 输入图像
        :param num_highlights: 高光数量
        :return: 增强后的图像
        """
        return self.highlight.add_specular_highlight(image, num_highlights)
    
    def apply_elongated_lesion_augmentation(
        self,
        image: np.ndarray,
        disease_type: str = "stripe_rust",
        num_lesions: int = 5,
        intensity: float = 0.7
    ) -> np.ndarray:
        """
        应用细长病斑增强 - 根据文档2.2节
        针对条锈病等细长病斑的形态学增强
        
        :param image: 输入图像
        :param disease_type: 病害类型 (stripe_rust, powdery_mildew)
        :param num_lesions: 病斑数量
        :param intensity: 叠加强度
        :return: 增强后的图像
        """
        if disease_type == "stripe_rust":
            return self.elongated_lesion.add_stripe_rust_symptom(
                image, num_stripes=num_lesions, intensity=intensity
            )
        elif disease_type == "powdery_mildew":
            return self.elongated_lesion.add_powdery_mildew_symptom(
                image, num_spots=num_lesions, intensity=intensity
            )
        else:
            return image
    
    def apply_morphological_enhancement(
        self,
        image: np.ndarray,
        operation: str = "dilate",
        kernel_size: int = 3,
        iterations: int = 1
    ) -> np.ndarray:
        """
        应用形态学增强
        
        :param image: 输入图像
        :param operation: 操作类型 (dilate, erode, open, close)
        :param kernel_size: 核大小
        :param iterations: 迭代次数
        :return: 增强后的图像
        """
        return self.elongated_lesion.morphological_enhancement(
            image, operation, kernel_size, iterations
        )
    
    def apply_lesion_contrast_enhancement(
        self,
        image: np.ndarray,
        lesion_color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]] = None
    ) -> np.ndarray:
        """
        应用病斑对比度增强
        
        :param image: 输入图像
        :param lesion_color_range: 病斑颜色范围
        :return: 增强后的图像
        """
        return self.elongated_lesion.enhance_lesion_contrast(image, lesion_color_range)
    
    def generate_synthetic_samples(
        self,
        disease_name: str,
        symptom_description: str,
        num_samples: int = 10,
        output_dir: Optional[str] = None
    ) -> List[np.ndarray]:
        """
        生成合成样本 - 根据文档2.2节
        对于样本稀缺的病害，利用生成模型合成逼真图像
        
        :param disease_name: 病害名称
        :param symptom_description: 症状描述
        :param num_samples: 生成数量
        :param output_dir: 输出目录
        :return: 生成的图像列表
        """
        return self.generative.generate_disease_image(
            disease_name=disease_name,
            symptom_description=symptom_description,
            num_images=num_samples
        )
    
    def create_training_pipeline(
        self,
        include_mosaic: bool = True,
        include_mixup: bool = True,
        include_highlight: bool = True,
        target_size: Tuple[int, int] = (640, 640)
    ) -> A.Compose:
        """
        创建训练用增强管道 - 根据文档2.2节
        
        :param include_mosaic: 是否包含Mosaic增强
        :param include_mixup: 是否包含Mixup增强
        :param include_highlight: 是否包含高光模拟
        :param target_size: 目标尺寸
        :return: Albumentations增强管道
        """
        transforms = [
            # 几何变换
            A.HorizontalFlip(p=0.5 if self.config.flip_horizontal else 0),
            A.VerticalFlip(p=0.5 if self.config.flip_vertical else 0),
            A.Rotate(limit=self.config.rotation_range, p=self.config.apply_prob),
            A.RandomScale(scale_limit=0.1, p=self.config.apply_prob),
            
            # 颜色变换 - 模拟不同天气和时间段
            A.ColorJitter(
                brightness=self.config.brightness_range[1] - 1,
                contrast=self.config.contrast_range[1] - 1,
                saturation=self.config.saturation_range[1] - 1,
                hue=self.config.hue_range[1],
                p=self.config.apply_prob
            ),
            
            # 噪声和模糊
            A.GaussNoise(var_limit=self.config.gaussian_noise_var, p=self.config.gaussian_noise_prob),
            A.Blur(blur_limit=self.config.blur_limit, p=self.config.blur_prob),
            
            # 光照变化
            A.RandomGamma(gamma_limit=(80, 120), p=self.config.apply_prob),
            A.RandomBrightnessContrast(p=self.config.apply_prob),
            
            # 归一化和转换为张量
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ]
        
        return A.Compose(transforms)
    
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
