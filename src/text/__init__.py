# -*- coding: utf-8 -*-
"""
文本理解模块

基于 LLM/BERT 的自然语言处理，用于理解农户描述、生成诊断建议
包含：
- 多模态语义理解
- 交互式对话
- 诊断报告生成
"""

from pathlib import Path
from typing import Any

# 模型默认路径
DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "llm_weights.bin"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "LanguageAgent":
        from .text_engine import LanguageAgent
        return LanguageAgent
    elif name == "EnhancedLanguageAgent":
        # 直接使用 LanguageAgent 作为增强版
        from .text_engine import LanguageAgent
        return LanguageAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_MODEL_PATH",
    # 文本智能体
    "LanguageAgent",
    "EnhancedLanguageAgent"
]
