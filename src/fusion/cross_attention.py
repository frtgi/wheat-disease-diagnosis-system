"""
跨模态特征对齐模块 - Cross-Modal Attention
实现基于研究文档的跨模态特征对齐机制
"""
import torch
import torch.nn as nn


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


def create_cross_attention_model():
    """
    创建跨模态注意力模型
    """
    model = CrossModalAttention(
        text_dim=768,
        vision_dim=256,
        num_heads=8
    )
    
    print("✅ 跨模态特征对齐模块已创建")
    print(f"   文本维度: {model.text_dim}")
    print(f"   视觉维度: {model.vision_dim}")
    print(f"   注意力头数: {model.num_heads}")
    
    return model


if __name__ == "__main__":
    print("=" * 60)
    print("🧠 [Cross-Modal Attention] 创建跨模态特征对齐模块")
    print("=" * 60)
    
    model = create_cross_attention_model()
    
    print("\n" + "=" * 60)
