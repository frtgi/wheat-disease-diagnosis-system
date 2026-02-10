# -*- coding: utf-8 -*-
"""
工具模块

包含日志管理、错误处理、配置管理等通用工具
"""

from pathlib import Path
from typing import Any

# 默认工具路径
DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

# 延迟导入，避免循环导入问题
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_LOG_DIR",
    "DEFAULT_CONFIG_DIR",
    # 日志相关
    "Logger",
    "LogLevel",
    # 错误处理
    "ErrorHandler",
    # 配置管理
    "ConfigManager"
]
