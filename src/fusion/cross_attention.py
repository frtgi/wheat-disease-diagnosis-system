# -*- coding: utf-8 -*-
"""
跨模态特征对齐模块 - Cross-Modal Attention with SE Mechanism

实现基于研究文档的跨模态特征对齐机制：
1. Cross-Modal Attention: 文本特征作为 Query 查询视觉特征
2. SE (Squeeze-and-Excitation): 动态加权关键特征
3. 多头注意力机制
4. 残差连接和层归一化

技术特性:
- 动态特征加权
- 背景噪声抑制
- 关键文本特征与图像区域关联
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import math


class SEBlock(nn.Module):
    """
    Squeeze-and-Excitation Block (SE 模块)
    
    通过全局池化和全连接层学习通道权重，
    动态调整特征通道的重要性
    """
    
    def __init__(
        self,
        channels: int,
        reduction_ratio: int = 16,
        use_bias: bool = True
    ):
        """
        初始化 SE 模块
        
        :param channels: 输入通道数
        :param reduction_ratio: 压缩比率
        :param use_bias: 是否使用偏置
        """
        super().__init__()
        
        self.channels = channels
        self.reduction_ratio = reduction_ratio
        
        # Squeeze: 全局平均池化
        self.squeeze = nn.AdaptiveAvgPool1d(1)
        
        # Excitation: 两个全连接层
        reduced_channels = max(channels // reduction_ratio, 8)
        self.excitation = nn.Sequential(
            nn.Linear(channels, reduced_channels, bias=use_bias),
            nn.ReLU(inplace=True),
            nn.Linear(reduced_channels, channels, bias=use_bias),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入特征 [batch, seq_len, channels] 或 [batch, channels, seq_len]
        :return: 加权后的特征
        """
        # 处理不同输入格式
        if x.dim() == 3:
            if x.shape[1] != self.channels:
                # [batch, seq_len, channels] -> [batch, channels, seq_len]
                x = x.transpose(1, 2)
                squeeze_out = self.squeeze(x).squeeze(-1)
                scale = self.excitation(squeeze_out)
                scale = scale.unsqueeze(-1)
                out = x * scale
                return out.transpose(1, 2)  # 恢复原始形状
            else:
                # [batch, channels, seq_len]
                squeeze_out = self.squeeze(x).squeeze(-1)
                scale = self.excitation(squeeze_out)
                scale = scale.unsqueeze(-1)
                return x * scale
        else:
            raise ValueError(f"SE Block 期望 3D 输入，但得到 {x.dim()}D")


class CrossModalAttention(nn.Module):
    """
    跨模态特征对齐 - Cross-Modal Attention
    
    文本特征作为 Query 去"查询"视觉特征，
    实现文本-视觉特征的对齐
    """
    
    def __init__(
        self,
        text_dim: int,
        vision_dim: int,
        num_heads: int = 8,
        hidden_dim: int = None,
        dropout: float = 0.1
    ):
        """
        初始化跨模态注意力模块
        
        :param text_dim: 文本特征维度
        :param vision_dim: 视觉特征维度
        :param num_heads: 注意力头数
        :param hidden_dim: 隐藏层维度
        :param dropout: Dropout 比率
        """
        super().__init__()
        
        self.text_dim = text_dim
        self.vision_dim = vision_dim
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim or min(text_dim, vision_dim)
        self.head_dim = self.hidden_dim // num_heads
        
        # 文本特征的 Query 投影
        self.text_q_proj = nn.Linear(text_dim, self.hidden_dim)
        
        # 视觉特征的 Key, Value 投影
        self.vision_k_proj = nn.Linear(vision_dim, self.hidden_dim)
        self.vision_v_proj = nn.Linear(vision_dim, self.hidden_dim)
        
        # 输出投影
        self.out_proj = nn.Linear(self.hidden_dim, text_dim)
        
        # 层归一化
        self.norm = nn.LayerNorm(text_dim)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self,
        text_features: torch.Tensor,
        vision_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param text_features: 文本特征 [batch, text_seq_len, text_dim]
        :param vision_features: 视觉特征 [batch, vision_seq_len, vision_dim]
        :param attention_mask: 注意力掩码（可选）
        :return: 对齐后的特征和注意力权重
        """
        batch_size = text_features.shape[0]
        
        # 处理 2D 输入
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
        scores = torch.matmul(Q_t, K_v.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # 应用注意力掩码
        if attention_mask is not None:
            scores = scores + attention_mask
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 应用注意力到视觉 Value
        attended_vision = torch.matmul(attn_weights, V_v)
        attended_vision = attended_vision.transpose(1, 2).contiguous()
        attended_vision = attended_vision.view(batch_size, -1, self.hidden_dim)
        
        # 输出投影
        output = self.out_proj(attended_vision)
        output = self.norm(output)
        
        return output, attn_weights


class SEEnhancedCrossModalAttention(nn.Module):
    """
    SE 增强的跨模态注意力模块
    
    结合 Cross-Modal Attention 和 SE 机制：
    1. 使用 SE 模块动态加权关键文本特征
    2. 使用 Cross-Modal Attention 关联文本和图像区域
    3. 抑制背景噪声干扰
    """
    
    def __init__(
        self,
        text_dim: int,
        vision_dim: int,
        num_heads: int = 8,
        hidden_dim: int = None,
        dropout: float = 0.1,
        se_reduction_ratio: int = 16
    ):
        """
        初始化 SE 增强的跨模态注意力模块
        
        :param text_dim: 文本特征维度
        :param vision_dim: 视觉特征维度
        :param num_heads: 注意力头数
        :param hidden_dim: 隐藏层维度
        :param dropout: Dropout 比率
        :param se_reduction_ratio: SE 模块压缩比率
        """
        super().__init__()
        
        self.text_dim = text_dim
        self.vision_dim = vision_dim
        self.hidden_dim = hidden_dim or min(text_dim, vision_dim)
        
        # 文本特征 SE 模块
        self.text_se = SEBlock(
            channels=text_dim,
            reduction_ratio=se_reduction_ratio
        )
        
        # 视觉特征 SE 模块
        self.vision_se = SEBlock(
            channels=vision_dim,
            reduction_ratio=se_reduction_ratio
        )
        
        # 跨模态注意力
        self.cross_attn = CrossModalAttention(
            text_dim=text_dim,
            vision_dim=vision_dim,
            num_heads=num_heads,
            hidden_dim=self.hidden_dim,
            dropout=dropout
        )
        
        # 融合层
        self.fusion = nn.Sequential(
            nn.Linear(text_dim * 2, text_dim),
            nn.LayerNorm(text_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        # 门控机制
        self.gate = nn.Sequential(
            nn.Linear(text_dim * 2, text_dim),
            nn.Sigmoid()
        )
        
        # 残差权重
        self.residual_weight = nn.Parameter(torch.tensor(0.5))
        
    def forward(
        self,
        text_features: torch.Tensor,
        vision_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param text_features: 文本特征 [batch, text_seq_len, text_dim]
        :param vision_features: 视觉特征 [batch, vision_seq_len, vision_dim]
        :param attention_mask: 注意力掩码（可选）
        :return: 包含融合特征和注意力权重的字典
        """
        # SE 加权
        text_weighted = self.text_se(text_features)
        vision_weighted = self.vision_se(vision_features)
        
        # 跨模态注意力
        cross_out, cross_attn_weights = self.cross_attn(
            text_weighted, vision_weighted, attention_mask
        )
        
        # 融合
        concat_features = torch.cat([text_weighted, cross_out], dim=-1)
        
        # 门控融合
        gate = self.gate(concat_features)
        fused = self.fusion(concat_features)
        
        # 残差连接
        residual_weight = torch.sigmoid(self.residual_weight)
        output = residual_weight * fused + (1 - residual_weight) * text_weighted
        output = gate * output + (1 - gate) * cross_out
        
        return {
            'fused_features': output,
            'text_weighted': text_weighted,
            'vision_weighted': vision_weighted,
            'cross_attention_weights': cross_attn_weights,
            'gate_values': gate
        }


class MultiScaleCrossModalAttention(nn.Module):
    """
    多尺度跨模态注意力模块
    
    在不同尺度上应用跨模态注意力：
    - 局部尺度：捕获细节特征
    - 全局尺度：捕获语义特征
    """
    
    def __init__(
        self,
        text_dim: int,
        vision_dim: int,
        num_heads: int = 8,
        hidden_dim: int = None,
        dropout: float = 0.1,
        num_scales: int = 3
    ):
        """
        初始化多尺度跨模态注意力模块
        
        :param text_dim: 文本特征维度
        :param vision_dim: 视觉特征维度
        :param num_heads: 注意力头数
        :param hidden_dim: 隐藏层维度
        :param dropout: Dropout 比率
        :param num_scales: 尺度数量
        """
        super().__init__()
        
        self.num_scales = num_scales
        
        # 多尺度 SE 增强跨模态注意力
        self.scale_modules = nn.ModuleList([
            SEEnhancedCrossModalAttention(
                text_dim=text_dim,
                vision_dim=vision_dim,
                num_heads=num_heads,
                hidden_dim=hidden_dim,
                dropout=dropout
            )
            for _ in range(num_scales)
        ])
        
        # 尺度权重学习
        self.scale_weights = nn.Parameter(torch.ones(num_scales) / num_scales)
        
        # 最终融合层
        self.final_fusion = nn.Sequential(
            nn.Linear(text_dim * num_scales, text_dim),
            nn.LayerNorm(text_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
    def forward(
        self,
        text_features: torch.Tensor,
        vision_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param text_features: 文本特征
        :param vision_features: 视觉特征
        :param attention_mask: 注意力掩码
        :return: 多尺度融合结果
        """
        # 计算尺度权重
        weights = F.softmax(self.scale_weights, dim=0)
        
        # 多尺度处理
        scale_outputs = []
        all_attn_weights = []
        
        for i, scale_module in enumerate(self.scale_modules):
            # 对视觉特征进行不同尺度的池化
            if i == 0:
                # 局部尺度：保持原始分辨率
                vision_scaled = vision_features
            else:
                # 其他尺度：下采样
                scale_factor = 2 ** i
                vision_scaled = F.avg_pool1d(
                    vision_features.transpose(1, 2),
                    kernel_size=scale_factor,
                    stride=scale_factor
                ).transpose(1, 2)
            
            result = scale_module(text_features, vision_scaled, attention_mask)
            scale_outputs.append(result['fused_features'] * weights[i])
            all_attn_weights.append(result['cross_attention_weights'])
        
        # 拼接并融合
        concat_features = torch.cat(scale_outputs, dim=-1)
        final_output = self.final_fusion(concat_features)
        
        return {
            'fused_features': final_output,
            'scale_outputs': scale_outputs,
            'scale_weights': weights.tolist(),
            'attention_weights': all_attn_weights
        }


def create_cross_attention_model(
    text_dim: int = 768,
    vision_dim: int = 512,
    num_heads: int = 8,
    use_se: bool = True
) -> nn.Module:
    """
    创建跨模态注意力模型
    
    :param text_dim: 文本特征维度
    :param vision_dim: 视觉特征维度
    :param num_heads: 注意力头数
    :param use_se: 是否使用 SE 增强
    :return: 跨模态注意力模型
    """
    if use_se:
        model = SEEnhancedCrossModalAttention(
            text_dim=text_dim,
            vision_dim=vision_dim,
            num_heads=num_heads
        )
        print("✅ SE 增强跨模态注意力模块已创建")
    else:
        model = CrossModalAttention(
            text_dim=text_dim,
            vision_dim=vision_dim,
            num_heads=num_heads
        )
        print("✅ 基础跨模态注意力模块已创建")
    
    print(f"   文本维度: {text_dim}")
    print(f"   视觉维度: {vision_dim}")
    print(f"   注意力头数: {num_heads}")
    
    return model


def test_cross_attention():
    """测试跨模态注意力模块"""
    print("\n" + "=" * 60)
    print("跨模态注意力模块测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 基础跨模态注意力")
        base_model = create_cross_attention_model(use_se=False)
        
        batch_size = 2
        text_seq_len = 32
        vision_seq_len = 64
        
        text_features = torch.randn(batch_size, text_seq_len, 768)
        vision_features = torch.randn(batch_size, vision_seq_len, 512)
        
        output, attn_weights = base_model(text_features, vision_features)
        print(f"[OK] 输出维度: {output.shape}")
        print(f"[OK] 注意力权重维度: {attn_weights.shape}")
        
        print("\n[测试 2] SE 增强跨模态注意力")
        se_model = create_cross_attention_model(use_se=True)
        
        result = se_model(text_features, vision_features)
        print(f"[OK] 融合特征维度: {result['fused_features'].shape}")
        print(f"[OK] 文本加权特征维度: {result['text_weighted'].shape}")
        print(f"[OK] 视觉加权特征维度: {result['vision_weighted'].shape}")
        
        print("\n[测试 3] 多尺度跨模态注意力")
        multi_scale_model = MultiScaleCrossModalAttention(
            text_dim=768,
            vision_dim=512,
            num_heads=8,
            num_scales=3
        )
        
        ms_result = multi_scale_model(text_features, vision_features)
        print(f"[OK] 多尺度融合特征维度: {ms_result['fused_features'].shape}")
        print(f"[OK] 尺度权重: {ms_result['scale_weights']}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_cross_attention()
