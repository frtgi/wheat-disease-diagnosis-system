# -*- coding: utf-8 -*-
"""
文本理解模块

基于 LLM/BERT 的自然语言处理，用于理解农户描述、生成诊断建议
包含增强版Agri-LLaVA认知引擎：
- 多模态语义理解
- 交互式对话
- 诊断报告生成
"""

from pathlib import Path

# 模型默认路径
DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "llm_weights.bin"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "EnhancedLanguageAgent":
        try:
            from .enhanced_text_engine import EnhancedLanguageAgent
            return EnhancedLanguageAgent
        except ImportError as e:
            print(f"⚠️ EnhancedLanguageAgent 导入失败: {e}")
            # 回退到基础版本
            from .text_engine import LanguageAgent
            return LanguageAgent
    elif name == "LanguageAgent":
        from .text_engine import LanguageAgent
        return LanguageAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_MODEL_PATH",
    # 增强版文本智能体
    "EnhancedLanguageAgent",
    # 原有LanguageAgent
    "LanguageAgent"
]
