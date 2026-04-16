"""
KAD-Former 知识引导注意力模块
Knowledge-Aided Deep fusion Transformer

实现基于知识图谱的注意力引导机制，用于多模态特征融合
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


class KnowledgeGuidedAttention(nn.Module):
    """
    知识引导注意力模块 (Knowledge-Guided Attention, KGA)
    
    利用农业知识图谱中的先验知识动态引导视觉注意力权重分配
    """
    
    def __init__(
        self,
        vision_dim: int = 512,
        knowledge_dim: int = 256,
        num_heads: int = 8,
        hidden_dim: int = 256,
        dropout: float = 0.1
    ):
        """
        初始化 KGA 模块
        
        参数:
            vision_dim: 视觉特征维度
            knowledge_dim: 知识嵌入维度
            num_heads: 注意力头数
            hidden_dim: 隐藏层维度
            dropout: Dropout 比率
        """
        super().__init__()
        self.vision_dim = vision_dim
        self.knowledge_dim = knowledge_dim
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim
        self.scale = hidden_dim ** -0.5
        
        # 视觉特征投影
        self.vision_proj = nn.Linear(vision_dim, hidden_dim)
        
        # 知识特征投影
        self.knowledge_proj = nn.Linear(knowledge_dim, hidden_dim)
        
        # 注意力输出投影
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, vision_dim),
            nn.LayerNorm(vision_dim),
            nn.Dropout(dropout)
        )
        
        # 门控机制（修复维度）
        self.gate = nn.Sequential(
            nn.Linear(vision_dim + hidden_dim, hidden_dim),
            nn.Sigmoid()
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        vision_features: torch.Tensor,
        knowledge_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        参数:
            vision_features: 视觉特征 [batch_size, seq_len, vision_dim]
            knowledge_embeddings: 知识嵌入 [batch_size, num_entities, knowledge_dim]
            attention_mask: 注意力掩码（可选）
            
        返回:
            增强后的视觉特征 [batch_size, seq_len, vision_dim]
        """
        batch_size, seq_len, _ = vision_features.shape
        num_entities = knowledge_embeddings.shape[1]
        
        # 特征投影
        vision_proj = self.vision_proj(vision_features)  # [B, S, H]
        knowledge_proj = self.knowledge_proj(knowledge_embeddings)  # [B, N, H]
        
        # 计算知识引导注意力
        # A_KG = Softmax(Q_V * K_K^T / sqrt(d_k))
        attention_scores = torch.matmul(vision_proj, knowledge_proj.transpose(-2, -1))  # [B, S, N]
        attention_scores = attention_scores * self.scale
        
        # 应用注意力掩码
        if attention_mask is not None:
            attention_scores = attention_scores.masked_fill(attention_mask == 0, -1e9)
        
        attention_weights = F.softmax(attention_scores, dim=-1)  # [B, S, N]
        attention_weights = self.dropout(attention_weights)
        
        # 知识特征加权求和
        knowledge_context = torch.matmul(attention_weights, knowledge_proj)  # [B, S, H]
        
        # 门控融合机制
        gate_input = torch.cat([vision_features, knowledge_context], dim=-1)
        gate = self.gate(gate_input)  # [B, S, H]
        
        # 投影知识上下文到视觉维度
        knowledge_output = self.output_proj(knowledge_context)  # [B, S, vision_dim]
        
        # 门控融合：F_V' = F_V + gate * F_K
        enhanced_features = vision_features + gate * knowledge_output
        
        return enhanced_features


class KADFormer(nn.Module):
    """
    KAD-Former 层：知识引导的 Transformer 层
    
    在标准 Transformer 基础上集成知识引导注意力
    """
    
    def __init__(
        self,
        vision_dim: int = 512,
        knowledge_dim: int = 256,
        num_heads: int = 8,
        hidden_dim: int = 2048,
        dropout: float = 0.1
    ):
        """
        初始化 KAD-Former 层
        
        参数:
            vision_dim: 视觉特征维度
            knowledge_dim: 知识嵌入维度
            num_heads: 注意力头数
            hidden_dim: FFN 隐藏层维度
            dropout: Dropout 比率
        """
        super().__init__()
        
        # 知识引导注意力
        self.kga = KnowledgeGuidedAttention(
            vision_dim=vision_dim,
            knowledge_dim=knowledge_dim,
            num_heads=num_heads,
            hidden_dim=vision_dim,
            dropout=dropout
        )
        
        # 标准自注意力（用于对比和融合）
        self.self_attention = nn.MultiheadAttention(
            embed_dim=vision_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
            bias=True
        )
        
        # 层归一化
        self.norm1 = nn.LayerNorm(vision_dim)
        self.norm2 = nn.LayerNorm(vision_dim)
        self.norm3 = nn.LayerNorm(vision_dim)
        
        # 前馈网络
        self.ffn = nn.Sequential(
            nn.Linear(vision_dim, min(hidden_dim, vision_dim * 2)),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(min(hidden_dim, vision_dim * 2), vision_dim),
            nn.Dropout(dropout)
        )
        
        # 融合权重（可学习）
        self.fusion_weight = nn.Parameter(torch.tensor(0.5))
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        vision_features: torch.Tensor,
        knowledge_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        参数:
            vision_features: 视觉特征 [batch_size, seq_len, vision_dim]
            knowledge_embeddings: 知识嵌入 [batch_size, num_entities, knowledge_dim]
            attention_mask: 注意力掩码
            
        返回:
            输出特征 [batch_size, seq_len, vision_dim]
        """
        # 残差连接 1：知识引导注意力
        kga_output = self.kga(vision_features, knowledge_embeddings, attention_mask)
        kga_output = self.norm1(kga_output)
        
        # 残差连接 2：标准自注意力
        self_attn_output, _ = self.self_attention(
            vision_features, vision_features, vision_features,
            key_padding_mask=None if attention_mask is None else (1 - attention_mask).bool()
        )
        self_attn_output = self.norm2(self_attn_output)
        
        # 自适应融合
        # fused = (1 - w) * KGA + w * SelfAttention
        fused = (1 - self.fusion_weight) * kga_output + self.fusion_weight * self_attn_output
        fused = vision_features + self.dropout(fused)
        
        # 残差连接 3：前馈网络
        ffn_output = self.ffn(fused)
        output = fused + self.dropout(ffn_output)
        output = self.norm3(output)
        
        return output


class DeepStackKADFormer(nn.Module):
    """
    DeepStack KAD-Former：多层特征注入
    
    通过残差路径将视觉编码器不同层级特征注入到 KAD-Former
    """
    
    def __init__(
        self,
        num_layers: int = 4,
        vision_dim: int = 512,
        knowledge_dim: int = 256,
        num_heads: int = 8,
        hidden_dim: int = 2048,
        dropout: float = 0.1
    ):
        """
        初始化 DeepStack KAD-Former
        
        参数:
            num_layers: KAD-Former 层数
            vision_dim: 视觉特征维度
            knowledge_dim: 知识嵌入维度
            num_heads: 注意力头数
            hidden_dim: FFN 隐藏层维度
            dropout: Dropout 比率
        """
        super().__init__()
        self.num_layers = num_layers
        
        # 堆叠多层 KAD-Former
        self.layers = nn.ModuleList([
            KADFormer(
                vision_dim=vision_dim,
                knowledge_dim=knowledge_dim,
                num_heads=num_heads,
                hidden_dim=hidden_dim,
                dropout=dropout
            )
            for _ in range(num_layers)
        ])
        
        # 层级特征注入（DeepStack）
        # 用于注入 ViT 不同层级的特征
        # 注意：假设 ViT 特征维度与 vision_dim 相同
        self.vit_feature_injectors = nn.ModuleList([
            nn.Identity()  # 如果维度相同，直接恒等映射
            for _ in range(num_layers)
        ])
        
        self.final_norm = nn.LayerNorm(vision_dim)
    
    def forward(
        self,
        vision_features: torch.Tensor,
        knowledge_embeddings: torch.Tensor,
        vit_features: Optional[list] = None,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        参数:
            vision_features: 初始视觉特征
            knowledge_embeddings: 知识嵌入
            vit_features: ViT 各层级特征列表（用于 DeepStack 注入）
            attention_mask: 注意力掩码
            
        返回:
            最终输出特征
        """
        output = vision_features
        
        for i, layer in enumerate(self.layers):
            # DeepStack 特征注入
            if vit_features is not None and i < len(vit_features):
                vit_feat = self.vit_feature_injectors[i](vit_features[i])
                output = output + vit_feat  # 残差注入
            
            # KAD-Former 层处理
            output = layer(output, knowledge_embeddings, attention_mask)
        
        output = self.final_norm(output)
        return output


# 示例用法
if __name__ == "__main__":
    # 配置参数
    batch_size = 2
    seq_len = 64
    num_entities = 10
    vision_dim = 512
    knowledge_dim = 256
    
    # 创建模拟数据
    vision_features = torch.randn(batch_size, seq_len, vision_dim)
    knowledge_embeddings = torch.randn(batch_size, num_entities, knowledge_dim)
    
    # 测试 KGA 模块
    kga = KnowledgeGuidedAttention(
        vision_dim=vision_dim,
        knowledge_dim=knowledge_dim,
        num_heads=8
    )
    enhanced = kga(vision_features, knowledge_embeddings)
    print(f"KGA 输出形状：{enhanced.shape}")
    
    # 测试 KAD-Former 层
    kad_layer = KADFormer(
        vision_dim=vision_dim,
        knowledge_dim=knowledge_dim,
        num_heads=8
    )
    output = kad_layer(vision_features, knowledge_embeddings)
    print(f"KAD-Former 输出形状：{output.shape}")
    
    # 测试 DeepStack KAD-Former
    deepstack = DeepStackKADFormer(
        num_layers=4,
        vision_dim=vision_dim,
        knowledge_dim=knowledge_dim,
        num_heads=8
    )
    
    # 模拟 ViT 多层特征
    vit_features = [torch.randn(batch_size, seq_len, vision_dim) for _ in range(4)]
    
    output = deepstack(vision_features, knowledge_embeddings, vit_features)
    print(f"DeepStack KAD-Former 输出形状：{output.shape}")
    
    print("\nKAD-Former 模块测试通过！")
