# -*- coding: utf-8 -*-
"""
KAD-Former 知识引导注意力模块 (Knowledge-Aided Deep fusion Transformer)
实现知识图谱引导的视觉注意力机制，"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class KnowledgeGuidedAttention(nn.Module):
    """
    知识引导注意力模块 (Knowledge-Guided Attention, KGA)
    
    通过知识图谱先验知识引导视觉注意力聚焦于病斑区域
    
    公式: A_KG = Softmax(Q_V * K_K^T / sqrt(d_k))
    """
    
    def __init__(
        self,
        visual_dim: int = 768,
        knowledge_dim: int = 256,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        """
        初始化 KGA 模块
        
        Args:
            visual_dim: 视觉特征维度
            knowledge_dim: 知识嵌入维度
            num_heads: 注意力头数
            dropout: Dropout 比例
        """
        super().__init__()
        self.visual_dim = visual_dim
        self.knowledge_dim = knowledge_dim
        self.num_heads = num_heads
        
        self.head_dim = visual_dim // num_heads
        
        self.q_proj = nn.Linear(visual_dim, visual_dim)
        self.k_proj = nn.Linear(knowledge_dim, visual_dim)
        
        self.out_proj = nn.Linear(visual_dim, visual_dim)
        
        self.dropout = nn.Dropout(dropout)
        
        self.scale = self.head_dim ** -0.5
    
    def forward(
        self,
        visual_features: torch.Tensor,
        knowledge_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        Args:
            visual_features: 视觉特征 [B, N, visual_dim]
            knowledge_embeddings: 知识嵌入 [B, M, knowledge_dim]
            attention_mask: 注意力掩码 [B, N]
            
        Returns:
            融合后的特征 [B, N, visual_dim]
        """
        B, N, _ = visual_features.shape
        M = knowledge_embeddings.size(1)
        
        Q = self.q_proj(visual_features)
        K = self.k_proj(knowledge_embeddings)
        
        Q = Q.view(B, self.num_heads, N, self.head_dim).transpose(1, 2)
        K = K.view(B, self.num_heads, M, self.head_dim).transpose(1, 2)
        
        attention_scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        
        if attention_mask is not None:
            attention_scores = attention_scores.masked_fill(attention_mask == 0, float('-inf'))
        
        attention_weights = F.softmax(attention_scores, dim=-1)
        
        knowledge_attention = torch.matmul(attention_weights, K.transpose(1, 2))
        
        knowledge_attention = knowledge_attention.transpose(1, 2).contiguous()
        knowledge_attention = knowledge_attention.view(B, N, self.visual_dim)
        
        output = self.out_proj(visual_features + knowledge_attention)
        output = self.dropout(output)
        
        return output


class GatedFusionLayer(nn.Module):
    """
    门控融合层 (Gated Fusion Layer)
    
    通过门控机制融合视觉特征和知识特征
    """
    
    def __init__(
        self,
        visual_dim: int = 768,
        knowledge_dim: int = 256,
        hidden_dim: int = 512
    ):
        """
        初始化门控融合层
        
        Args:
            visual_dim: 视觉特征维度
            knowledge_dim: 知识特征维度
            hidden_dim: 隐藏层维度
        """
        super().__init__()
        
        self.visual_proj = nn.Linear(visual_dim, hidden_dim)
        self.knowledge_proj = nn.Linear(knowledge_dim, hidden_dim)
        
        self.gate_visual = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Sigmoid()
        )
        self.gate_knowledge = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Sigmoid()
        )
        
        self.output_proj = nn.Linear(hidden_dim, visual_dim)
        
        self.layer_norm = nn.LayerNorm(visual_dim)
    
    def forward(
        self,
        visual_features: torch.Tensor,
        knowledge_features: torch.Tensor
    ) -> torch.Tensor:
        """
        前向传播
        
        Args:
            visual_features: 视觉特征 [B, N, visual_dim]
            knowledge_features: 知识特征 [B, M, knowledge_dim]
            
        Returns:
            融合特征 [B, N, visual_dim]
        """
        visual_proj = self.visual_proj(visual_features)
        knowledge_proj = self.knowledge_proj(knowledge_features)
        
        if knowledge_proj.dim(1) < visual_proj.dim(1):
            knowledge_proj = F.interpolate(
                knowledge_proj, 
                size=visual_proj.shape[1], 
                mode='linear'
            )
        elif knowledge_proj.dim(1) > visual_proj.dim(1):
                knowledge_proj = knowledge_proj[:, :visual_proj.shape[1], :]
        
        gate_v = self.gate_visual(visual_proj)
        gate_k = self.gate_knowledge(knowledge_proj)
        
        fused = gate_v * visual_proj + gate_k * knowledge_proj
        
        output = self.output_proj(fused)
        output = self.layer_norm(output)
        
        return output


class KADFormer(nn.Module):
    """
    KAD-Former: 知识引导的深层多模态融合 Transformer
    
    整合 KGA 和门控融合机制，    实现视觉特征、语义特征和知识特征的深度融合
    """
    
    def __init__(
        self,
        visual_dim: int = 768,
        text_dim: int = 2560,
        knowledge_dim: int = 256,
        hidden_dim: int = 512,
        num_heads: int = 8,
        num_layers: int = 4,
        dropout: float = 0.1
    ):
        """
        初始化 KAD-Former
        
        Args:
            visual_dim: 视觉特征维度
            text_dim: 文本特征维度
            knowledge_dim: 知识嵌入维度
            hidden_dim: 隐藏层维度
            num_heads: 注意力头数
            num_layers: 层数
            dropout: Dropout 比例
        """
        super().__init__()
        
        self.visual_dim = visual_dim
        self.text_dim = text_dim
        self.knowledge_dim = knowledge_dim
        
        self.visual_adapter = nn.Linear(visual_dim, hidden_dim)
        self.text_adapter = nn.Linear(text_dim, hidden_dim)
        self.knowledge_adapter = nn.Linear(knowledge_dim, hidden_dim)
        
        self.layers = nn.ModuleList([
            KADFormerLayer(hidden_dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        self.output_proj = nn.Linear(hidden_dim, visual_dim)
        
    def forward(
        self,
        visual_features: torch.Tensor,
        text_features: torch.Tensor,
        knowledge_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        Args:
            visual_features: 视觉特征 [B, N_v, visual_dim]
            text_features: 文本特征 [B, N_t, text_dim]
            knowledge_embeddings: 知识嵌入 [B, N_k, knowledge_dim]
            attention_mask: 注意力掩码 [B, N_v]
            
        Returns:
            融合特征 [B, N_v, visual_dim]
        """
        visual_hidden = self.visual_adapter(visual_features)
        text_hidden = self.text_adapter(text_features)
        knowledge_hidden = self.knowledge_adapter(knowledge_embeddings)
        
        hidden = visual_hidden
        
        for layer in self.layers:
            hidden = layer(hidden, text_hidden, knowledge_hidden, attention_mask)
        
        output = self.output_proj(hidden)
        
        return output


class KADFormerLayer(nn.Module):
    """
    KAD-Former 单层
    """
    
    def __init__(
        self,
        hidden_dim: int = 512,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        """
        初始化 KAD-Former 层
        """
        super().__init__()
        
        self.kga = KnowledgeGuidedAttention(
            visual_dim=hidden_dim,
            knowledge_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout
        )
        
        self.gated_fusion = GatedFusionLayer(
            visual_dim=hidden_dim,
            knowledge_dim=hidden_dim,
            hidden_dim=hidden_dim
        )
        
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout)
        )
        
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        
    def forward(
        self,
        visual_features: torch.Tensor,
        text_features: torch.Tensor,
        knowledge_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        """
        attended = self.kga(visual_features, knowledge_features, attention_mask)
        visual_features = visual_features + attended
        visual_features = self.norm1(visual_features)
        
        fused = self.gated_fusion(visual_features, knowledge_features)
        visual_features = visual_features + fused
        visual_features = self.norm2(visual_features)
        
        ffn_output = self.ffn(visual_features)
        visual_features = visual_features + ffn_output
        
        return visual_features


def create_kad_former(
    visual_dim: int = 768,
    text_dim: int = 2560,
    knowledge_dim: int = 256,
    hidden_dim: int = 512,
    num_heads: int = 8,
    num_layers: int = 4,
    dropout: float = 0.1
) -> KADFormer:
    """
    创建 KAD-Former 模型
    
    Args:
        visual_dim: 视觉特征维度
        text_dim: 文本特征维度
        knowledge_dim: 知识嵌入维度
        hidden_dim: 隐藏层维度
        num_heads: 注意力头数
        num_layers: 层数
        dropout: Dropout 比例
        
    Returns:
        KADFormer: KAD-Former 模型
    """
    return KADFormer(
        visual_dim=visual_dim,
        text_dim=text_dim,
        knowledge_dim=knowledge_dim,
        hidden_dim=hidden_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        dropout=dropout
    )
