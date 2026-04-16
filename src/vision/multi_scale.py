# -*- coding: utf-8 -*-
"""
多尺度检测模块

提供多尺度检测功能：
- 多尺度推理
- 小目标检测增强
- 结果融合
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MultiScaleConfig:
    """多尺度检测配置"""
    scales: List[float] = None
    flip: bool = True
    merge_iou_threshold: float = 0.5
    min_confidence: float = 0.1
    
    def __post_init__(self):
        if self.scales is None:
            self.scales = [0.75, 1.0, 1.25]


class MultiScaleDetector:
    """
    多尺度检测器
    
    通过多尺度推理提高检测精度，特别是小目标检测
    """
    
    def __init__(self, config: Optional[MultiScaleConfig] = None):
        """
        初始化多尺度检测器
        
        :param config: 多尺度配置
        """
        self.config = config or MultiScaleConfig()
        print(f"🔍 [MultiScaleDetector] 初始化完成")
        print(f"   尺度: {self.config.scales}")
        print(f"   翻转增强: {self.config.flip}")
    
    def detect_multiscale(
        self,
        image: np.ndarray,
        detector_fn,
        original_size: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行多尺度检测
        
        :param image: 输入图像
        :param detector_fn: 检测函数
        :param original_size: 原始尺寸 (W, H)
        :return: 融合后的检测结果
        """
        if original_size is None:
            original_size = (image.shape[1], image.shape[0])
        
        all_detections = []
        
        for scale in self.config.scales:
            # 缩放图像
            scaled_image = self._scale_image(image, scale)
            
            # 检测
            detections = detector_fn(scaled_image)
            
            # 调整坐标到原始尺寸
            detections = self._rescale_detections(
                detections, scale, original_size
            )
            
            all_detections.extend(detections)
            
            # 翻转增强
            if self.config.flip:
                flipped_image = cv2.flip(scaled_image, 1)
                flipped_dets = detector_fn(flipped_image)
                flipped_dets = self._flip_detections(
                    flipped_dets, scaled_image.shape[1]
                )
                flipped_dets = self._rescale_detections(
                    flipped_dets, scale, original_size
                )
                all_detections.extend(flipped_dets)
        
        # 融合结果
        merged = self._merge_detections(all_detections)
        
        return merged
    
    def _scale_image(
        self,
        image: np.ndarray,
        scale: float
    ) -> np.ndarray:
        """缩放图像"""
        h, w = image.shape[:2]
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    def _rescale_detections(
        self,
        detections: List[Dict[str, Any]],
        scale: float,
        original_size: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """调整检测坐标到原始尺寸"""
        rescaled = []
        
        for det in detections:
            new_det = det.copy()
            
            if "bbox" in det:
                bbox = det["bbox"]
                new_det["bbox"] = [x / scale for x in bbox]
            
            rescaled.append(new_det)
        
        return rescaled
    
    def _flip_detections(
        self,
        detections: List[Dict[str, Any]],
        image_width: int
    ) -> List[Dict[str, Any]]:
        """翻转检测坐标"""
        flipped = []
        
        for det in detections:
            new_det = det.copy()
            
            if "bbox" in det:
                x1, y1, x2, y2 = det["bbox"]
                new_x1 = image_width - x2
                new_x2 = image_width - x1
                new_det["bbox"] = [new_x1, y1, new_x2, y2]
            
            flipped.append(new_det)
        
        return flipped
    
    def _merge_detections(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """融合检测结果 (NMS)"""
        if not detections:
            return []
        
        # 按置信度排序
        detections = sorted(
            detections,
            key=lambda x: x.get("confidence", 0),
            reverse=True
        )
        
        merged = []
        
        while detections:
            best = detections.pop(0)
            merged.append(best)
            
            # 过滤重叠的检测
            remaining = []
            for det in detections:
                if det.get("name") != best.get("name"):
                    remaining.append(det)
                    continue
                
                iou = self._compute_iou(
                    best.get("bbox", [0, 0, 0, 0]),
                    det.get("bbox", [0, 0, 0, 0])
                )
                
                if iou < self.config.merge_iou_threshold:
                    remaining.append(det)
            
            detections = remaining
        
        return merged
    
    def _compute_iou(
        self,
        box1: List[float],
        box2: List[float]
    ) -> float:
        """计算IoU"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / (union + 1e-8)


class SmallObjectEnhancer:
    """
    小目标检测增强器
    
    专门优化小目标检测
    """
    
    def __init__(
        self,
        min_object_size: int = 32,
        crop_size: int = 640,
        overlap: float = 0.25
    ):
        """
        初始化小目标增强器
        
        :param min_object_size: 最小目标尺寸
        :param crop_size: 裁剪尺寸
        :param overlap: 裁剪重叠比例
        """
        self.min_object_size = min_object_size
        self.crop_size = crop_size
        self.overlap = overlap
    
    def detect_with_crop(
        self,
        image: np.ndarray,
        detector_fn
    ) -> List[Dict[str, Any]]:
        """
        使用裁剪策略检测小目标
        
        :param image: 输入图像
        :param detector_fn: 检测函数
        :return: 检测结果
        """
        h, w = image.shape[:2]
        
        # 如果图像较小，直接检测
        if w <= self.crop_size and h <= self.crop_size:
            return detector_fn(image)
        
        # 计算裁剪位置
        stride = int(self.crop_size * (1 - self.overlap))
        crops = []
        
        for y in range(0, h - self.crop_size + 1, stride):
            for x in range(0, w - self.crop_size + 1, stride):
                crops.append((x, y, x + self.crop_size, y + self.crop_size))
        
        # 添加边缘裁剪
        if crops:
            last_x, last_y = crops[-1][2], crops[-1][3]
            if last_x < w:
                for y in range(0, h - self.crop_size + 1, stride):
                    crops.append((w - self.crop_size, y, w, y + self.crop_size))
            if last_y < h:
                for x in range(0, w - self.crop_size + 1, stride):
                    crops.append((x, h - self.crop_size, x + self.crop_size, h))
        
        # 检测每个裁剪区域
        all_detections = []
        
        for x1, y1, x2, y2 in crops:
            crop = image[y1:y2, x1:x2]
            detections = detector_fn(crop)
            
            # 调整坐标
            for det in detections:
                if "bbox" in det:
                    bbox = det["bbox"]
                    det["bbox"] = [
                        bbox[0] + x1,
                        bbox[1] + y1,
                        bbox[2] + x1,
                        bbox[3] + y1
                    ]
                all_detections.append(det)
        
        # 融合结果
        return self._merge_detections(all_detections)
    
    def _merge_detections(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """融合检测结果"""
        if not detections:
            return []
        
        # 简单的NMS
        detections = sorted(
            detections,
            key=lambda x: x.get("confidence", 0),
            reverse=True
        )
        
        merged = []
        for det in detections:
            is_duplicate = False
            for existing in merged:
                if det.get("name") == existing.get("name"):
                    iou = self._compute_iou(
                        det.get("bbox", [0, 0, 0, 0]),
                        existing.get("bbox", [0, 0, 0, 0])
                    )
                    if iou > 0.5:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                merged.append(det)
        
        return merged
    
    def _compute_iou(self, box1: List[float], box2: List[float]) -> float:
        """计算IoU"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / (union + 1e-8)


def create_multiscale_detector(
    scales: List[float] = None,
    flip: bool = True
) -> MultiScaleDetector:
    """
    工厂函数: 创建多尺度检测器
    
    :param scales: 尺度列表
    :param flip: 是否使用翻转增强
    :return: MultiScaleDetector实例
    """
    config = MultiScaleConfig(scales=scales, flip=flip)
    return MultiScaleDetector(config)


def create_small_object_enhancer(
    min_object_size: int = 32,
    crop_size: int = 640
) -> SmallObjectEnhancer:
    """
    工厂函数: 创建小目标增强器
    
    :param min_object_size: 最小目标尺寸
    :param crop_size: 裁剪尺寸
    :return: SmallObjectEnhancer实例
    """
    return SmallObjectEnhancer(min_object_size, crop_size)
