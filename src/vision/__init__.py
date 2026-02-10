# -*- coding: utf-8 -*-
"""
视觉感知模块

基于改进YOLOv8的精准视觉检测，包含SerpensGate-YOLOv8架构：
- DySnakeConv (动态蛇形卷积)
- SPPELAN (多尺度特征聚合)
- STA (超级令牌注意力)
"""

from pathlib import Path

# 模型默认路径
DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "yolov8_wheat.pt"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "EnhancedVisionAgent":
        try:
            from .enhanced_vision_engine import EnhancedVisionAgent
            return EnhancedVisionAgent
        except ImportError as e:
            print(f"⚠️ EnhancedVisionAgent 导入失败: {e}")
            from .vision_engine import VisionAgent
            return VisionAgent
    elif name == "VisionAgent":
        from .vision_engine import VisionAgent
        return VisionAgent
    elif name == "DySnakeConv":
        from .dy_snake_conv import DySnakeConv
        return DySnakeConv
    elif name == "SPPELAN":
        from .sppelan_module import SPPELAN
        return SPPELAN
    elif name == "STAModule":
        from .sta_module import STAModule
        return STAModule
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_MODEL_PATH",
    # 增强版视觉智能体
    "EnhancedVisionAgent",
    # 基础视觉智能体
    "VisionAgent",
    # 核心组件
    "DySnakeConv",
    "SPPELAN",
    "STAModule"
]
