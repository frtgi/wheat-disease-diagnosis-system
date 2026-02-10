# -*- coding: utf-8 -*-
"""
超级令牌注意力模块 (Super Token Attention, STA)
根据研究文档，该模块用于捕捉全局依赖关系，将全局上下文信息注入到局部特征中
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class SuperTokenAttention(nn.Module):
    """
    超级令牌注意力 (Super Token Attention, STA)
    
    机制描述:
    STA将视觉特征图转化为一组视觉令牌（Visual Tokens），
    并聚合成一个能够代表全局语义的"超级令牌"。
    这个超级令牌与每一个局部令牌进行交互（Attention），
    从而将全局上下文信息注入到局部特征中。
    
    诊断意义:
    通过STA，模型能够"意识到"如果图像底部有严重的白粉病，
    那么上部叶片的轻微褪绿更有可能是白粉病的早期症状，
    而不是其他原因。这种全局推理能力对于提高复杂背景下的检测准确率至关重要。
    """
    
    def __init__(self, dim, num_heads=8, num_super_tokens=4, qkv_bias=False, attn_drop=0., proj_drop=0.):
        """
        初始化STA模块
        
        :param dim: 输入特征维度
        :param num_heads: 注意力头数
        :param num_super_tokens: 超级令牌数量
        :param qkv_bias: 是否使用偏置
        :param attn_drop: 注意力dropout率
        :param proj_drop: 投影dropout率
        """
        super(SuperTokenAttention, self).__init__()
        
        self.dim = dim
        self.num_heads = num_heads
        self.num_super_tokens = num_super_tokens
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5
        
        # 将特征图转换为视觉令牌
        self.token_embed = nn.Sequential(
            nn.Conv2d(dim, dim, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(dim),
            nn.ReLU(inplace=True),
            nn.Conv2d(dim, dim, kernel_size=1, bias=False)
        )
        
        # 超级令牌生成 - 使用可学习的聚类中心
        self.super_token_prototype = nn.Parameter(
            torch.randn(1, num_super_tokens, dim)
        )
        
        # Q, K, V 投影
        self.q_proj = nn.Linear(dim, dim, bias=qkv_bias)
        self.k_proj = nn.Linear(dim, dim, bias=qkv_bias)
        self.v_proj = nn.Linear(dim, dim, bias=qkv_bias)
        
        # 注意力dropout
        self.attn_drop = nn.Dropout(attn_drop)
        
        # 输出投影
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
        
        # 层归一化
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        
        # FFN
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(proj_drop),
            nn.Linear(dim * 4, dim),
            nn.Dropout(proj_drop)
        )
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化权重"""
        nn.init.trunc_normal_(self.super_token_prototype, std=0.02)
        
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm):
                nn.init.constant_(m.bias, 0)
                nn.init.constant_(m.weight, 1.0)
            elif isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
    
    def forward(self, x):
        """
        前向传播
        
        :param x: 输入特征图 [batch, channels, height, width]
        :return: 输出特征图 [batch, channels, height, width]
        """
        batch_size, C, H, W = x.shape
        
        # 保存残差
        residual = x
        
        # 1. 将特征图转换为视觉令牌 [batch, H*W, C]
        tokens = self.token_embed(x)
        tokens = tokens.flatten(2).transpose(1, 2)  # [B, H*W, C]
        tokens = self.norm1(tokens)
        
        # 2. 生成超级令牌
        # 扩展超级令牌原型到batch size
        super_tokens = self.super_token_prototype.expand(batch_size, -1, -1)  # [B, num_super, C]
        
        # 3. 局部令牌到超级令牌的注意力 (聚类)
        # 计算每个局部令牌与超级令牌的相似度
        q_super = self.q_proj(super_tokens)  # [B, num_super, C]
        k_local = self.k_proj(tokens)  # [B, H*W, C]
        v_local = self.v_proj(tokens)  # [B, H*W, C]
        
        # 重塑为多头注意力格式
        q_super = q_super.view(batch_size, self.num_super_tokens, self.num_heads, self.head_dim).transpose(1, 2)
        k_local = k_local.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        v_local = v_local.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力: 超级令牌查询局部令牌
        attn = (q_super @ k_local.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        
        # 聚合局部信息到超级令牌
        super_tokens_enhanced = (attn @ v_local).transpose(1, 2).reshape(batch_size, self.num_super_tokens, C)
        super_tokens_enhanced = self.proj(super_tokens_enhanced)
        super_tokens_enhanced = self.proj_drop(super_tokens_enhanced)
        
        # 4. 超级令牌到局部令牌的注意力 (广播全局信息)
        q_local = self.q_proj(tokens)  # [B, H*W, C]
        k_super = self.k_proj(super_tokens_enhanced)  # [B, num_super, C]
        v_super = self.v_proj(super_tokens_enhanced)  # [B, num_super, C]
        
        # 重塑为多头注意力格式
        q_local = q_local.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        k_super = k_super.view(batch_size, self.num_super_tokens, self.num_heads, self.head_dim).transpose(1, 2)
        v_super = v_super.view(batch_size, self.num_super_tokens, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力: 局部令牌查询超级令牌
        attn2 = (q_local @ k_super.transpose(-2, -1)) * self.scale
        attn2 = attn2.softmax(dim=-1)
        attn2 = self.attn_drop(attn2)
        
        # 广播全局信息到局部令牌
        tokens_enhanced = (attn2 @ v_super).transpose(1, 2).reshape(batch_size, H * W, C)
        tokens_enhanced = self.proj(tokens_enhanced)
        tokens_enhanced = self.proj_drop(tokens_enhanced)
        
        # 5. FFN
        tokens_enhanced = tokens_enhanced + self.ffn(self.norm2(tokens_enhanced))
        
        # 6. 重塑回特征图
        output = tokens_enhanced.transpose(1, 2).view(batch_size, C, H, W)
        
        # 残差连接
        output = output + residual
        
        return output


class STABlock(nn.Module):
    """
    STA 基础块，包含STA和卷积操作
    """
    
    def __init__(self, dim, num_heads=8, num_super_tokens=4, mlp_ratio=4., drop=0.):
        super(STABlock, self).__init__()
        
        self.norm1 = nn.BatchNorm2d(dim)
        self.sta = SuperTokenAttention(
            dim=dim,
            num_heads=num_heads,
            num_super_tokens=num_super_tokens,
            attn_drop=drop,
            proj_drop=drop
        )
        
        self.norm2 = nn.BatchNorm2d(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Conv2d(dim, mlp_hidden_dim, 1, bias=False),
            nn.BatchNorm2d(mlp_hidden_dim),
            nn.GELU(),
            nn.Dropout(drop),
            nn.Conv2d(mlp_hidden_dim, dim, 1, bias=False),
            nn.BatchNorm2d(dim),
            nn.Dropout(drop)
        )
    
    def forward(self, x):
        """
        前向传播
        """
        # STA分支
        x = x + self.sta(self.norm1(x))
        
        # MLP分支
        x = x + self.mlp(self.norm2(x))
        
        return x


class HierarchicalSTA(nn.Module):
    """
    分层超级令牌注意力
    在不同尺度上应用STA，捕捉多尺度的全局依赖
    """
    
    def __init__(self, in_channels, out_channels, num_scales=3):
        super(HierarchicalSTA, self).__init__()
        
        self.num_scales = num_scales
        
        # 计算每个上采样分支的输出通道数，确保总和等于out_channels
        base_channels = out_channels // num_scales
        remainder = out_channels - base_channels * num_scales
        
        self.up_channels = []
        for i in range(num_scales):
            # 最后一个分支承担余数
            ch = base_channels + (remainder if i == num_scales - 1 else 0)
            self.up_channels.append(ch)
        
        # 下采样路径
        self.down_samples = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(in_channels if i == 0 else out_channels, out_channels, 3, stride=2, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            ) for i in range(num_scales)
        ])
        
        # 每个尺度的STA
        self.sta_blocks = nn.ModuleList([
            STABlock(out_channels, num_heads=8, num_super_tokens=4)
            for _ in range(num_scales)
        ])
        
        # 上采样和融合
        self.up_samples = nn.ModuleList([
            nn.Sequential(
                nn.Upsample(scale_factor=2**i, mode='bilinear', align_corners=False),
                nn.Conv2d(out_channels, up_ch, 1, bias=False),
                nn.BatchNorm2d(up_ch)
            ) for i, up_ch in enumerate(self.up_channels)
        ])
        
        # 最终融合
        self.fusion = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        """
        前向传播
        """
        multi_scale_features = []
        
        current = x
        for down, sta, up in zip(self.down_samples, self.sta_blocks, self.up_samples):
            # 下采样
            current = down(current)
            # 应用STA
            current = sta(current)
            # 上采样到原始尺寸
            upsampled = up(current)
            multi_scale_features.append(upsampled)
        
        # 融合多尺度特征
        fused = torch.cat(multi_scale_features, dim=1)
        output = self.fusion(fused)
        
        return output


class GlobalContextModule(nn.Module):
    """
    全局上下文模块
    轻量级的全局信息聚合模块
    """
    
    def __init__(self, in_channels, reduction=16):
        super(GlobalContextModule, self).__init__()
        
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        
        self.mlp = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // reduction, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels // reduction, in_channels, 1, bias=False)
        )
        
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        """
        前向传播
        """
        # 全局平均池化分支
        avg_out = self.mlp(self.avg_pool(x))
        # 全局最大池化分支
        max_out = self.mlp(self.max_pool(x))
        
        # 融合
        out = self.sigmoid(avg_out + max_out)
        
        return x * out


def test_sta():
    """
    测试STA模块
    """
    print("=" * 60)
    print("🧪 测试 Super Token Attention (STA) 模块")
    print("=" * 60)
    
    # 创建测试输入
    batch_size = 2
    in_channels = 256
    height, width = 32, 32
    x = torch.randn(batch_size, in_channels, height, width)
    
    # 测试SuperTokenAttention
    print("\n" + "=" * 60)
    print("🧪 测试 SuperTokenAttention")
    print("=" * 60)
    
    sta = SuperTokenAttention(dim=in_channels, num_heads=8, num_super_tokens=4)
    output = sta(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in sta.parameters()):,}")
    
    # 测试STABlock
    print("\n" + "=" * 60)
    print("🧪 测试 STABlock")
    print("=" * 60)
    
    sta_block = STABlock(in_channels, num_heads=8, num_super_tokens=4)
    output2 = sta_block(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output2.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in sta_block.parameters()):,}")
    
    # 测试HierarchicalSTA
    print("\n" + "=" * 60)
    print("🧪 测试 HierarchicalSTA")
    print("=" * 60)
    
    hier_sta = HierarchicalSTA(in_channels, 256, num_scales=3)
    output3 = hier_sta(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output3.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in hier_sta.parameters()):,}")
    
    # 测试GlobalContextModule
    print("\n" + "=" * 60)
    print("🧪 测试 GlobalContextModule")
    print("=" * 60)
    
    gcm = GlobalContextModule(in_channels)
    output4 = gcm(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output4.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in gcm.parameters()):,}")
    
    print("\n" + "=" * 60)
    print("✅ STA 模块测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_sta()
