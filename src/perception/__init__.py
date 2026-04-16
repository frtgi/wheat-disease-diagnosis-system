# -*- coding: utf-8 -*-
"""
感知诊断层 (Perception Layer)

IWDDA Agent Phase 10: 感知诊断层优化
实现 YOLOv8 和 Qwen3-VL 双引擎特征融合

模块组成:
1. YOLOv8 引擎：ROI 定位、病斑特征提取、小目标检测
2. Qwen3-VL 视觉引擎：图像理解、候选生成、视觉 - 文本对齐
3. 融合引擎：双引擎特征融合、gating mechanism、联合特征输出

技术特性:
- 注意力机制提升 ROI 定位精度
- 多尺度特征提取优化病斑识别
- Early Fusion 策略实现深度融合
- Gating Mechanism 学习融合权重
- mAP 提升目标：>5%
"""

from .yolo_engine import YOLOEngine
from .qwen_vl_engine import QwenVLEngine
from .fusion_engine import DualEngineFusion

__all__ = [
    'YOLOEngine',
    'QwenVLEngine',
    'DualEngineFusion'
]

__version__ = '1.0.0'
__author__ = 'IWDDA Team'
