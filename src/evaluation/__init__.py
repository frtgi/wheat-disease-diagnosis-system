# -*- coding: utf-8 -*-
"""
性能评估模块

包含模型性能评估、鲁棒性测试和基准测试功能
支持多维度评估体系
"""

from pathlib import Path
from typing import Any

# 默认报告路径
DEFAULT_REPORT_DIR = Path(__file__).parent.parent.parent / "reports"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "PerformanceEvaluator":
        try:
            from .evaluation_framework import PerformanceEvaluator
            return PerformanceEvaluator
        except ImportError as e:
            print(f"⚠️ PerformanceEvaluator 导入失败: {e}")
            return None
    elif name == "BenchmarkSuite":
        try:
            from .evaluation_framework import BenchmarkSuite
            return BenchmarkSuite
        except ImportError:
            return None
    elif name == "DetectionMetrics":
        try:
            from .evaluation_framework import DetectionMetrics
            return DetectionMetrics
        except ImportError:
            return Any
    elif name == "EfficiencyMetrics":
        try:
            from .evaluation_framework import EfficiencyMetrics
            return EfficiencyMetrics
        except ImportError:
            return Any
    elif name == "RobustnessMetrics":
        try:
            from .evaluation_framework import RobustnessMetrics
            return RobustnessMetrics
        except ImportError:
            return Any
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_REPORT_DIR",
    # 评估框架
    "PerformanceEvaluator",
    "BenchmarkSuite",
    # 评估指标
    "DetectionMetrics",
    "EfficiencyMetrics",
    "RobustnessMetrics"
]
