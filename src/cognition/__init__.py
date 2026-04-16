# -*- coding: utf-8 -*-
"""
认知模块 - 基于多模态大模型的语义理解

包含多模态模型组件：
- QwenEngine (Qwen3-VL-2B-Instruct 模型引擎 - 默认推荐，约2GB显存优化，原生多模态)
- PromptTemplate (提示词模板)
- CognitionEngine (认知引擎)

支持的模型：
- Qwen/Qwen3-VL-2B-Instruct (默认推荐，约2GB显存优化，原生多模态)
"""

from pathlib import Path
from typing import Any

# 模型默认路径
DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "agri_llava"

# Qwen3-VL-2B-Instruct 模型配置 (默认推荐，约2GB显存优化，原生多模态)
QWEN_VL_2B_MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "QwenEngine":
        from .qwen_engine import QwenEngine
        return QwenEngine
    elif name == "QwenConfig":
        from .qwen_engine import QwenConfig
        return QwenConfig
    elif name == "create_qwen_engine":
        from .qwen_engine import create_qwen_engine
        return create_qwen_engine
    elif name == "CognitionEngine":
        try:
            from .cognition_engine import CognitionEngine
            return CognitionEngine
        except ImportError as e:
            print(f"[警告] CognitionEngine 导入失败: {e}")
            return None
    elif name == "PromptTemplate":
        from .prompt_templates import PromptTemplate
        return PromptTemplate
    elif name == "SystemPrompts":
        from .prompt_templates import SystemPrompts
        return SystemPrompts
    elif name == "DetectionResult":
        try:
            from .prompt_templates import DetectionResult
            return DetectionResult
        except ImportError:
            return Any
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_MODEL_PATH",
    "QWEN_VL_2B_MODEL_ID",
    # Qwen3-VL-2B-Instruct 核心组件 (默认推荐，约2GB显存优化，原生多模态)
    "QwenEngine",
    "QwenConfig",
    "create_qwen_engine",
    # 认知引擎
    "CognitionEngine",
    # 提示词相关
    "PromptTemplate",
    "SystemPrompts",
    "DetectionResult"
]
