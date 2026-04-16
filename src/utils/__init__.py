# -*- coding: utf-8 -*-
"""
工具模块

包含日志管理、错误处理、配置管理、性能监控、推理缓存等通用工具
"""

from pathlib import Path
from typing import Any

DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
DEFAULT_REPORT_DIR = Path(__file__).parent.parent.parent / "logs" / "performance"

def __getattr__(name):
    if name == "Logger":
        try:
            from .logger import Logger
            return Logger
        except ImportError as e:
            print(f"⚠️ Logger 导入失败: {e}")
            return None
    elif name == "LogLevel":
        try:
            from .logger import LogLevel
            return LogLevel
        except ImportError:
            from enum import IntEnum
            class LogLevel(IntEnum):
                DEBUG = 10
                INFO = 20
                WARNING = 30
                ERROR = 40
                CRITICAL = 50
            return LogLevel
    elif name == "ErrorHandler":
        try:
            from .error_handler import ErrorHandler
            return ErrorHandler
        except ImportError:
            return None
    elif name == "ConfigManager":
        try:
            from .config_manager import ConfigManager
            return ConfigManager
        except ImportError:
            return None
    elif name == "PerformanceMonitor":
        try:
            from .performance_monitor import PerformanceMonitor
            return PerformanceMonitor
        except ImportError as e:
            print(f"⚠️ PerformanceMonitor 导入失败: {e}")
            return None
    elif name == "MetricType":
        try:
            from .performance_monitor import MetricType
            return MetricType
        except ImportError:
            return None
    elif name == "timed":
        try:
            from .performance_monitor import timed
            return timed
        except ImportError:
            return None
    elif name == "get_global_monitor":
        try:
            from .performance_monitor import get_global_monitor
            return get_global_monitor
        except ImportError:
            return None
    elif name == "InferenceCache":
        try:
            from .inference_cache import InferenceCache
            return InferenceCache
        except ImportError as e:
            print(f"⚠️ InferenceCache 导入失败: {e}")
            return None
    elif name == "CacheEntry":
        try:
            from .inference_cache import CacheEntry
            return CacheEntry
        except ImportError:
            return None
    elif name == "ImageHasher":
        try:
            from .inference_cache import ImageHasher
            return ImageHasher
        except ImportError:
            return None
    elif name == "create_inference_cache":
        try:
            from .inference_cache import create_inference_cache
            return create_inference_cache
        except ImportError:
            return None
    elif name == "get_global_cache":
        try:
            from .inference_cache import get_global_cache
            return get_global_cache
        except ImportError:
            return None
    elif name == "ImagePreprocessor":
        try:
            from .preprocessing import ImagePreprocessor
            return ImagePreprocessor
        except ImportError as e:
            print(f"⚠️ ImagePreprocessor 导入失败: {e}")
            return None
    elif name == "PreprocessConfig":
        try:
            from .preprocessing import PreprocessConfig
            return PreprocessConfig
        except ImportError:
            return None
    elif name == "PreprocessResult":
        try:
            from .preprocessing import PreprocessResult
            return PreprocessResult
        except ImportError:
            return None
    elif name == "BackendType":
        try:
            from .preprocessing import BackendType
            return BackendType
        except ImportError:
            return None
    elif name == "preprocess_image":
        try:
            from .preprocessing import preprocess_image
            return preprocess_image
        except ImportError:
            return None
    elif name == "get_preprocessor":
        try:
            from .preprocessing import get_preprocessor
            return get_preprocessor
        except ImportError:
            return None
    elif name == "create_preprocessor":
        try:
            from .preprocessing import create_preprocessor
            return create_preprocessor
        except ImportError:
            return None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_LOG_DIR",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_REPORT_DIR",
    "Logger",
    "LogLevel",
    "ErrorHandler",
    "ConfigManager",
    "PerformanceMonitor",
    "MetricType",
    "timed",
    "get_global_monitor",
    "InferenceCache",
    "CacheEntry",
    "ImageHasher",
    "create_inference_cache",
    "get_global_cache",
    "ImagePreprocessor",
    "PreprocessConfig",
    "PreprocessResult",
    "BackendType",
    "preprocess_image",
    "get_preprocessor",
    "create_preprocessor"
]
