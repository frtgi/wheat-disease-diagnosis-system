# -*- coding: utf-8 -*-
"""
部署优化模块

包含TensorRT导出、ONNX转换和模型优化功能
支持云边协同部署
"""

from pathlib import Path
from typing import Any

# 默认模型路径
DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "ONNXExporter":
        try:
            from .tensorrt_exporter import ONNXExporter
            return ONNXExporter
        except ImportError as e:
            print(f"⚠️ ONNXExporter 导入失败: {e}")
            return None
    elif name == "TensorRTBuilder":
        try:
            from .tensorrt_exporter import TensorRTBuilder
            return TensorRTBuilder
        except ImportError:
            return None
    elif name == "TensorRTInference":
        try:
            from .tensorrt_exporter import TensorRTInference
            return TensorRTInference
        except ImportError:
            return None
    elif name == "ModelOptimizer":
        try:
            from .tensorrt_exporter import ModelOptimizer
            return ModelOptimizer
        except ImportError:
            return None
    elif name == "TensorRTConfig":
        try:
            from .tensorrt_exporter import TensorRTConfig
            return TensorRTConfig
        except ImportError:
            return Any
    elif name == "PrecisionMode":
        try:
            from .tensorrt_exporter import PrecisionMode
            return PrecisionMode
        except ImportError:
            from enum import Enum
            class PrecisionMode(Enum):
                FP32 = "fp32"
                FP16 = "fp16"
                INT8 = "int8"
            return PrecisionMode
    elif name == "EdgeOptimizer":
        try:
            from .edge_optimizer import EdgeOptimizer
            return EdgeOptimizer
        except ImportError as e:
            print(f"⚠️ EdgeOptimizer 导入失败: {e}")
            return None
    elif name == "EdgeConfig":
        try:
            from .edge_optimizer import EdgeConfig
            return EdgeConfig
        except ImportError:
            return Any
    elif name == "QuantizationMode":
        try:
            from .edge_optimizer import QuantizationMode
            return QuantizationMode
        except ImportError:
            from enum import Enum
            class QuantizationMode(Enum):
                FP32 = "fp32"
                FP16 = "fp16"
                INT8 = "int8"
                DYNAMIC = "dynamic"
            return QuantizationMode
    elif name == "ModelQuantizer":
        try:
            from .edge_optimizer import ModelQuantizer
            return ModelQuantizer
        except ImportError:
            return None
    elif name == "TensorRTConverter":
        try:
            from .edge_optimizer import TensorRTConverter
            return TensorRTConverter
        except ImportError:
            return None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_MODEL_DIR",
    # TensorRT相关
    "ONNXExporter",
    "TensorRTBuilder",
    "TensorRTInference",
    "ModelOptimizer",
    "TensorRTConfig",
    "PrecisionMode",
    # 边缘端优化
    "EdgeOptimizer",
    "EdgeConfig",
    "QuantizationMode",
    "ModelQuantizer",
    "TensorRTConverter"
]
