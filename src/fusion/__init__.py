"""
多模态融合模块
提供 KAD-Former、融合引擎等组件
"""
from .kad_former import (
    KnowledgeGuidedAttention,
    KADFormer,
    DeepStackKADFormer
)

from .fusion_engine import (
    MultimodalFusionEngine,
    FUSION_CONFIG,
    create_fusion_engine
)

__all__ = [
    # KAD-Former 组件
    "KnowledgeGuidedAttention",
    "KADFormer",
    "DeepStackKADFormer",
    
    # 融合引擎
    "MultimodalFusionEngine",
    "FUSION_CONFIG",
    "create_fusion_engine"
]
