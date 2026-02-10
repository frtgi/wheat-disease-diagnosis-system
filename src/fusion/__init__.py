# -*- coding: utf-8 -*-
"""
多模态融合模块

整合视觉和文本信息，进行综合分析和决策
包含增强版KAD-Former架构：
- 知识引导注意力 (KGA)
- 跨模态特征对齐
- GraphRAG检索增强生成
- 三流融合（视觉+文本+知识）
"""

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "EnhancedFusionAgent":
        try:
            from .enhanced_fusion_engine import EnhancedFusionAgent
            return EnhancedFusionAgent
        except ImportError as e:
            print(f"⚠️ EnhancedFusionAgent 导入失败: {e}")
            # 回退到基础版本
            from .fusion_engine import FusionAgent
            return FusionAgent
    elif name == "KnowledgeGuidedAttention":
        from .kga_module import KnowledgeGuidedAttention
        return KnowledgeGuidedAttention
    elif name == "CrossModalAttention":
        from .cross_attention import CrossModalAttention
        return CrossModalAttention
    elif name == "KADFusion":
        from .kga_module import KADFusion
        return KADFusion
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # 增强版融合引擎
    "EnhancedFusionAgent",
    # 基础模块
    "KnowledgeGuidedAttention",
    "CrossModalAttention",
    "KADFusion"
]
