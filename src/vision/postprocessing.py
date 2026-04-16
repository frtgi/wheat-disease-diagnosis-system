# -*- coding: utf-8 -*-
"""
后处理模块

提供检测结果后处理功能：
- NMS优化 (Soft-NMS, 类别感知NMS)
- 边界框精炼
- 置信度校准
- 结果过滤
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PostprocessConfig:
    """后处理配置"""
    iou_threshold: float = 0.45
    conf_threshold: float = 0.25
    max_detections: int = 100
    use_soft_nms: bool = False
    sigma: float = 0.5
    min_box_size: int = 10


class NMSProcessor:
    """
    NMS处理器
    
    提供多种NMS变体实现
    """
    
    def __init__(self, config: Optional[PostprocessConfig] = None):
        """
        初始化NMS处理器
        
        :param config: 后处理配置
        """
        self.config = config or PostprocessConfig()
    
    def nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        classes: Optional[np.ndarray] = None
    ) -> List[int]:
        """
        标准NMS
        
        :param boxes: 边界框 (N, 4) [x1, y1, x2, y2]
        :param scores: 置信度 (N,)
        :param classes: 类别 (N,)
        :return: 保留的索引列表
        """
        if len(boxes) == 0:
            return []
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if len(keep) >= self.config.max_detections:
                break
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            
            inds = np.where(iou <= self.config.iou_threshold)[0]
            order = order[inds + 1]
        
        return keep
    
    def soft_nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        classes: Optional[np.ndarray] = None
    ) -> Tuple[List[int], np.ndarray]:
        """
        Soft-NMS
        
        :param boxes: 边界框 (N, 4)
        :param scores: 置信度 (N,)
        :param classes: 类别 (N,)
        :return: (保留索引, 调整后的置信度)
        """
        if len(boxes) == 0:
            return [], np.array([])
        
        boxes = boxes.astype(np.float64)
        scores = scores.astype(np.float64)
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        
        keep = []
        new_scores = scores.copy()
        
        for _ in range(len(boxes)):
            max_idx = np.argmax(new_scores)
            max_score = new_scores[max_idx]
            
            if max_score < self.config.conf_threshold:
                break
            
            keep.append(max_idx)
            
            if len(keep) >= self.config.max_detections:
                break
            
            xx1 = np.maximum(x1[max_idx], x1)
            yy1 = np.maximum(y1[max_idx], y1)
            xx2 = np.minimum(x2[max_idx], x2)
            yy2 = np.minimum(y2[max_idx], y2)
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            iou = inter / (areas[max_idx] + areas - inter)
            
            weight = np.exp(-(iou ** 2) / self.config.sigma)
            new_scores = new_scores * weight
            new_scores[max_idx] = 0
        
        return keep, scores[keep] * np.exp(-np.array([0] + [0.1] * (len(keep) - 1)))
    
    def class_aware_nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        classes: np.ndarray
    ) -> List[int]:
        """
        类别感知NMS
        
        :param boxes: 边界框 (N, 4)
        :param scores: 置信度 (N,)
        :param classes: 类别 (N,)
        :return: 保留的索引列表
        """
        if len(boxes) == 0:
            return []
        
        unique_classes = np.unique(classes)
        all_keep = []
        
        for cls in unique_classes:
            cls_mask = classes == cls
            cls_boxes = boxes[cls_mask]
            cls_scores = scores[cls_mask]
            
            cls_keep = self.nms(cls_boxes, cls_scores)
            
            original_indices = np.where(cls_mask)[0]
            all_keep.extend(original_indices[cls_keep].tolist())
        
        return all_keep


class BoxRefiner:
    """
    边界框精炼器
    
    优化检测边界框
    """
    
    def __init__(self):
        """初始化边界框精炼器"""
        pass
    
    def refine_boxes(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        精炼边界框
        
        :param boxes: 边界框 (N, 4)
        :param scores: 置信度 (N,)
        :param image_shape: 图像尺寸 (H, W)
        :return: 精炼后的边界框
        """
        if len(boxes) == 0:
            return boxes
        
        refined = boxes.copy().astype(np.float64)
        h, w = image_shape
        
        refined[:, 0] = np.clip(refined[:, 0], 0, w - 1)
        refined[:, 1] = np.clip(refined[:, 1], 0, h - 1)
        refined[:, 2] = np.clip(refined[:, 2], 0, w - 1)
        refined[:, 3] = np.clip(refined[:, 3], 0, h - 1)
        
        refined[:, 2] = np.maximum(refined[:, 2], refined[:, 0] + 1)
        refined[:, 3] = np.maximum(refined[:, 3], refined[:, 1] + 1)
        
        return refined.astype(np.int32)
    
    def expand_boxes(
        self,
        boxes: np.ndarray,
        scale: float = 1.1
    ) -> np.ndarray:
        """
        扩展边界框
        
        :param boxes: 边界框 (N, 4)
        :param scale: 扩展比例
        :return: 扩展后的边界框
        """
        if len(boxes) == 0:
            return boxes
        
        expanded = boxes.copy().astype(np.float64)
        
        cx = (expanded[:, 0] + expanded[:, 2]) / 2
        cy = (expanded[:, 1] + expanded[:, 3]) / 2
        w = expanded[:, 2] - expanded[:, 0]
        h = expanded[:, 3] - expanded[:, 1]
        
        new_w = w * scale
        new_h = h * scale
        
        expanded[:, 0] = cx - new_w / 2
        expanded[:, 1] = cy - new_h / 2
        expanded[:, 2] = cx + new_w / 2
        expanded[:, 3] = cy + new_h / 2
        
        return expanded.astype(np.int32)


class ConfidenceCalibrator:
    """
    置信度校准器
    
    校准检测置信度
    """
    
    def __init__(self, temperature: float = 1.0):
        """
        初始化置信度校准器
        
        :param temperature: 温度参数
        """
        self.temperature = temperature
    
    def calibrate(
        self,
        scores: np.ndarray,
        method: str = "temperature"
    ) -> np.ndarray:
        """
        校准置信度
        
        :param scores: 原始置信度
        :param method: 校准方法
        :return: 校准后的置信度
        """
        if method == "temperature":
            return self._temperature_scaling(scores)
        elif method == "sigmoid":
            return self._sigmoid_scaling(scores)
        else:
            return scores
    
    def _temperature_scaling(self, scores: np.ndarray) -> np.ndarray:
        """温度缩放"""
        return 1.0 / (1.0 + np.exp(-np.log(scores / (1 - scores + 1e-8)) / self.temperature))
    
    def _sigmoid_scaling(self, scores: np.ndarray) -> np.ndarray:
        """Sigmoid缩放"""
        return 1.0 / (1.0 + np.exp(-scores * 5))


class DetectionPostprocessor:
    """
    检测结果后处理器
    
    整合所有后处理功能
    """
    
    def __init__(self, config: Optional[PostprocessConfig] = None):
        """
        初始化后处理器
        
        :param config: 后处理配置
        """
        self.config = config or PostprocessConfig()
        self.nms_processor = NMSProcessor(self.config)
        self.box_refiner = BoxRefiner()
        self.conf_calibrator = ConfidenceCalibrator()
    
    def process(
        self,
        detections: List[Dict[str, Any]],
        image_shape: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """
        执行完整后处理
        
        :param detections: 原始检测结果
        :param image_shape: 图像尺寸
        :return: 后处理后的检测结果
        """
        if not detections:
            return []
        
        boxes = np.array([d.get("bbox", [0, 0, 0, 0]) for d in detections])
        scores = np.array([d.get("confidence", 0) for d in detections])
        classes = np.array([d.get("class_id", 0) for d in detections])
        
        boxes = self.box_refiner.refine_boxes(boxes, scores, image_shape)
        
        scores = self.conf_calibrator.calibrate(scores)
        
        if self.config.use_soft_nms:
            keep, new_scores = self.nms_processor.soft_nms(boxes, scores, classes)
        else:
            keep = self.nms_processor.class_aware_nms(boxes, scores, classes)
            new_scores = scores[keep]
        
        results = []
        for i, idx in enumerate(keep):
            det = detections[idx].copy()
            det["bbox"] = boxes[idx].tolist()
            det["confidence"] = float(new_scores[i])
            
            box_area = (boxes[idx, 2] - boxes[idx, 0]) * (boxes[idx, 3] - boxes[idx, 1])
            if box_area < self.config.min_box_size ** 2:
                continue
            
            results.append(det)
        
        return results[:self.config.max_detections]


def create_postprocessor(
    iou_threshold: float = 0.45,
    conf_threshold: float = 0.25,
    use_soft_nms: bool = False
) -> DetectionPostprocessor:
    """
    工厂函数: 创建后处理器
    
    :param iou_threshold: IoU阈值
    :param conf_threshold: 置信度阈值
    :param use_soft_nms: 是否使用Soft-NMS
    :return: DetectionPostprocessor实例
    """
    config = PostprocessConfig(
        iou_threshold=iou_threshold,
        conf_threshold=conf_threshold,
        use_soft_nms=use_soft_nms
    )
    return DetectionPostprocessor(config)
