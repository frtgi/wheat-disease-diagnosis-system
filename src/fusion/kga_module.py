"""
KAD-Fusion 核心模块
实现基于研究文档的知识引导注意力（KGA）和跨模态特征对齐
"""
import torch
import torch.nn as nn


class KnowledgeGuidedAttention(nn.Module):
    """
    知识引导注意力（KGA）- Knowledge-Guided Attention
    根据研究文档，KGA 利用知识图谱中的先验知识来"校准"视觉模型的注意力焦点
    """
    def __init__(self, vision_dim, knowledge_dim, num_heads=8, hidden_dim=None):
        super(KnowledgeGuidedAttention, self).__init__()
        self.vision_dim = vision_dim
        self.knowledge_dim = knowledge_dim
        self.num_heads = num_heads
        # 使用统一的隐藏维度
        self.hidden_dim = hidden_dim or min(vision_dim, knowledge_dim)
        self.head_dim = self.hidden_dim // num_heads
        
        # 视觉特征的 Query 投影 (映射到hidden_dim)
        self.vision_q_proj = nn.Linear(vision_dim, self.hidden_dim)
        
        # 知识特征的 Key, Value 投影 (映射到hidden_dim)
        self.knowledge_k_proj = nn.Linear(knowledge_dim, self.hidden_dim)
        self.knowledge_v_proj = nn.Linear(knowledge_dim, self.hidden_dim)
        
        # 输出投影 (映射回vision_dim)
        self.out_proj = nn.Linear(self.hidden_dim, vision_dim)
        self.norm = nn.LayerNorm(vision_dim)
    
    def forward(self, vision_features, knowledge_embeddings):
        """
        vision_features: [batch, seq_len, vision_dim]
        knowledge_embeddings: [batch, num_knowledge, knowledge_dim]
        """
        batch_size = vision_features.shape[0]
        
        # 生成视觉 Query
        Q_v = self.vision_q_proj(vision_features)
        Q_v = Q_v.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 生成知识 Key, Value
        K_k = self.knowledge_k_proj(knowledge_embeddings)
        K_k = K_k.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V_k = self.knowledge_v_proj(knowledge_embeddings)
        V_k = V_k.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算知识引导的注意力图
        scores = torch.matmul(Q_v, K_k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = torch.softmax(scores, dim=-1)
        
        # 应用注意力到知识 Value
        attended_knowledge = torch.matmul(attn_weights, V_k)
        attended_knowledge = attended_knowledge.transpose(1, 2).contiguous()
        attended_knowledge = attended_knowledge.view(batch_size, -1, self.hidden_dim)
        
        # 输出投影
        attended_knowledge = self.out_proj(attended_knowledge)
        
        # 残差连接
        enhanced_vision = vision_features + attended_knowledge
        enhanced_vision = self.norm(enhanced_vision)
        
        return enhanced_vision


class CrossModalAttention(nn.Module):
    """
    跨模态特征对齐 - Cross-Modal Attention
    文本特征作为 Query 去"查询"视觉特征
    """
    def __init__(self, text_dim, vision_dim, num_heads=8, hidden_dim=None):
        super(CrossModalAttention, self).__init__()
        self.text_dim = text_dim
        self.vision_dim = vision_dim
        self.num_heads = num_heads
        # 使用统一的隐藏维度
        self.hidden_dim = hidden_dim or min(text_dim, vision_dim)
        self.head_dim = self.hidden_dim // num_heads
        
        # 文本特征的 Query 投影 (映射到hidden_dim)
        self.text_q_proj = nn.Linear(text_dim, self.hidden_dim)
        
        # 视觉特征的 Key, Value 投影 (映射到hidden_dim)
        self.vision_k_proj = nn.Linear(vision_dim, self.hidden_dim)
        self.vision_v_proj = nn.Linear(vision_dim, self.hidden_dim)
        
        # 输出投影 (映射回text_dim)
        self.out_proj = nn.Linear(self.hidden_dim, text_dim)
        self.norm = nn.LayerNorm(text_dim)
    
    def forward(self, text_features, vision_features):
        """
        text_features: [batch, seq_len, text_dim] 或 [batch, text_dim]
        vision_features: [batch, seq_len, vision_dim]
        """
        batch_size = text_features.shape[0]
        
        # 如果text_features是2D，扩展为3D
        if text_features.dim() == 2:
            text_features = text_features.unsqueeze(1)
        
        # 生成文本 Query
        Q_t = self.text_q_proj(text_features)
        Q_t = Q_t.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 生成视觉 Key, Value
        K_v = self.vision_k_proj(vision_features)
        K_v = K_v.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V_v = self.vision_v_proj(vision_features)
        V_v = V_v.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算跨模态注意力
        scores = torch.matmul(Q_t, K_v.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = torch.softmax(scores, dim=-1)
        
        # 应用注意力到视觉 Value
        attended_vision = torch.matmul(attn_weights, V_v)
        attended_vision = attended_vision.transpose(1, 2).contiguous()
        attended_vision = attended_vision.view(batch_size, -1, self.hidden_dim)
        
        # 输出投影
        output = self.out_proj(attended_vision)
        output = self.norm(output)
        
        return output


class KADFusion(nn.Module):
    """
    KAD-Fusion: Knowledge-Aware Diffusion Transformer
    融合视觉、文本和知识特征
    """
    def __init__(self, vision_dim=512, text_dim=768, knowledge_dim=256, num_heads=8):
        super(KADFusion, self).__init__()
        
        # 知识引导注意力
        self.kga = KnowledgeGuidedAttention(vision_dim, knowledge_dim, num_heads)
        
        # 跨模态注意力 - 输出维度为text_dim
        self.cross_attention = CrossModalAttention(text_dim, vision_dim, num_heads)
        
        # 将text_dim映射到vision_dim的投影层
        self.text_to_vision_proj = nn.Linear(text_dim, vision_dim)
        
        # 特征融合层
        self.fusion_layers = nn.Sequential(
            nn.Linear(vision_dim, vision_dim * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(vision_dim * 2, vision_dim),
            nn.GELU(),
            nn.Dropout(0.1)
        )
        
        # 最终输出层
        self.output_layer = nn.Sequential(
            nn.Linear(vision_dim, vision_dim),
            nn.LayerNorm(vision_dim)
        )
    
    def forward(self, vision_features, text_features, knowledge_embeddings):
        """
        vision_features: [batch, seq_len, vision_dim]
        text_features: [batch, text_dim]
        knowledge_embeddings: [batch, num_knowledge, knowledge_dim]
        """
        # 步骤 1: 知识引导注意力增强视觉特征
        enhanced_vision = self.kga(vision_features, knowledge_embeddings)
        
        # 步骤 2: 跨模态特征对齐
        # 扩展text_features以匹配vision_features的seq_len维度
        text_features_expanded = text_features.unsqueeze(1).expand(-1, enhanced_vision.size(1), -1)
        fused_features = self.cross_attention(text_features_expanded, enhanced_vision)
        
        # 步骤 3: 将融合特征从text_dim映射到vision_dim
        fused_features = self.text_to_vision_proj(fused_features)
        
        # 步骤 4: 特征融合
        output = self.fusion_layers(fused_features)
        
        # 步骤 5: 最终输出
        output = self.output_layer(output)
        
        return output


def create_kad_fusion_model():
    """
    创建 KAD-Fusion 模型
    """
    model = KADFusion(
        vision_dim=512,
        text_dim=768,
        knowledge_dim=256,
        num_heads=8
    )
    
    print("✅ KAD-Fusion 模型已创建")
    print(f"   视觉维度: {model.kga.vision_dim}")
    print(f"   文本维度: {model.cross_attention.text_dim}")
    print(f"   知识维度: {model.kga.knowledge_dim}")
    print(f"   注意力头数: {model.kga.num_heads}")
    
    return model


if __name__ == "__main__":
    print("=" * 60)
    print("🧠 [KAD-Fusion] 创建知识引导注意力模块")
    print("=" * 60)
    
    model = create_kad_fusion_model()
    
    print("\n" + "=" * 60)
    print("✅ KAD-Fusion 核心模块实现完成！")
    print("\n" + "=" * 60)
