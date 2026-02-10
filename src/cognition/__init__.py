# -*- coding: utf-8 -*-
"""
认知模块 - 基于LLaVA的多模态语义理解

包含Agri-LLaVA架构组件：
- CLIPVisionEncoder (视觉编码器)
- ProjectionLayer (投影层)
- AgriLLaVA (多模态大模型)
- PromptTemplate (提示词模板)
"""

from pathlib import Path
from typing import Any

# 模型默认路径
DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "agri_llava"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "AgriLLaVA":
        from .llava_engine import AgriLLaVA
        return AgriLLaVA
    elif name == "CLIPVisionEncoder":
        from .llava_engine import CLIPVisionEncoder
        return CLIPVisionEncoder
    elif name == "ProjectionLayer":
        from .llava_engine import ProjectionLayer
        return ProjectionLayer
    elif name == "CognitionEngine":
        try:
            from .cognition_engine import CognitionEngine
            return CognitionEngine
        except ImportError as e:
            print(f"⚠️ CognitionEngine 导入失败: {e}")
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
            # 返回占位符类型
            return Any
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_MODEL_PATH",
    # 核心模型组件
    "AgriLLaVA",
    "CLIPVisionEncoder",
    "ProjectionLayer",
    "CognitionEngine",
    # 提示词相关
    "PromptTemplate",
    "SystemPrompts",
    "DetectionResult"
]
