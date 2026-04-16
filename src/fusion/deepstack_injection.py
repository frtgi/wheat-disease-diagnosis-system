# -*- coding: utf-8 -*-
"""
DeepStack 多层特征注入模块 (DeepStack Multi-Layer Feature Injection)

实现 Qwen3-VL 视觉编码器的多层特征注入机制：
1. 浅层特征注入（纹理/边缘）：捕获病斑细微纹理（霉层、孢子堆）
2. 中层特征注入（部件/结构）：捕获病斑形状和分布特征
3. 高层特征注入（语义/物体）：捕获病害类别语义信息

技术特性:
- 多层级特征融合
- 自适应权重学习
- 残差连接
- 维度对齐投影
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import math


class LayerFeatureProjector(nn.Module):
    """
    单层特征投影器
    
    将特定层的视觉特征投影到目标维度
    """
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        """
        初始化层特征投影器
        
        :param input_dim: 输入特征维度
        :param output_dim: 输出特征维度
        :param num_heads: 注意力头数
        :param dropout: Dropout 比率
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # 特征投影
        self.proj = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        # 自注意力增强
        self.self_attn = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # 层归一化
        self.norm = nn.LayerNorm(output_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入特征 [batch, seq_len, input_dim]
        :return: 投影后的特征 [batch, seq_len, output_dim]
        """
        # 特征投影
        proj_feat = self.proj(x)
        
        # 自注意力增强
        attn_out, _ = self.self_attn(proj_feat, proj_feat, proj_feat)
        proj_feat = self.norm(proj_feat + attn_out)
        
        return proj_feat


class DeepStackFeatureInjection(nn.Module):
    """
    DeepStack 多层特征注入模块
    
    将 ViT 的浅层、中层、高层特征分别注入到 LLM 的不同层级中：
    - 浅层特征：纹理/边缘信息，增强病斑细微纹理感知
    - 中层特征：部件/结构信息，增强病斑形状识别
    - 高层特征：语义/物体信息，增强病害类别理解
    """
    
    def __init__(
        self,
        vision_dims: Dict[str, int] = None,
        llm_dim: int = 4096,
        num_heads: int = 8,
        dropout: float = 0.1,
        enable_layer_weights: bool = True
    ):
        """
        初始化 DeepStack 模块
        
        :param vision_dims: 各层视觉特征维度 {'low': dim, 'mid': dim, 'high': dim}
        :param llm_dim: LLM 隐藏层维度
        :param num_heads: 注意力头数
        :param dropout: Dropout 比率
        :param enable_layer_weights: 是否启用层级权重学习
        """
        super().__init__()
        
        # 默认维度配置（Qwen3-VL ViT 架构）
        if vision_dims is None:
            vision_dims = {
                'low': 1024,    # 浅层特征维度
                'mid': 1024,    # 中层特征维度
                'high': 1024    # 高层特征维度
            }
        
        self.vision_dims = vision_dims
        self.llm_dim = llm_dim
        self.enable_layer_weights = enable_layer_weights
        
        # 浅层特征投影器（纹理/边缘）
        self.low_layer_proj = LayerFeatureProjector(
            input_dim=vision_dims['low'],
            output_dim=llm_dim // 4,  # 注入到 LLM 浅层
            num_heads=num_heads,
            dropout=dropout
        )
        
        # 中层特征投影器（部件/结构）
        self.mid_layer_proj = LayerFeatureProjector(
            input_dim=vision_dims['mid'],
            output_dim=llm_dim // 2,  # 注入到 LLM 中层
            num_heads=num_heads,
            dropout=dropout
        )
        
        # 高层特征投影器（语义/物体）
        self.high_layer_proj = LayerFeatureProjector(
            input_dim=vision_dims['high'],
            output_dim=llm_dim,  # 注入到 LLM 高层
            num_heads=num_heads,
            dropout=dropout
        )
        
        # 维度对齐投影层（将低/中层特征扩展到 llm_dim）
        self.low_dim_proj = nn.Linear(llm_dim // 4, llm_dim)
        self.mid_dim_proj = nn.Linear(llm_dim // 2, llm_dim)
        
        # 层级权重学习
        if enable_layer_weights:
            self.layer_weights = nn.Parameter(
                torch.ones(3) / 3  # 初始权重均匀分布
            )
        
        # 跨层注意力融合
        self.cross_layer_attn = nn.MultiheadAttention(
            embed_dim=llm_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # 最终融合层
        self.fusion_layer = nn.Sequential(
            nn.Linear(llm_dim * 2, llm_dim),
            nn.LayerNorm(llm_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(llm_dim, llm_dim)
        )
        
        # 门控机制
        self.gate = nn.Sequential(
            nn.Linear(llm_dim * 2, llm_dim),
            nn.Sigmoid()
        )
        
        # 残差权重
        self.residual_weight = nn.Parameter(torch.tensor(0.5))
        
    def forward(
        self,
        low_features: torch.Tensor,
        mid_features: torch.Tensor,
        high_features: torch.Tensor,
        llm_hidden_states: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param low_features: 浅层视觉特征 [batch, seq_len, low_dim]
        :param mid_features: 中层视觉特征 [batch, seq_len, mid_dim]
        :param high_features: 高层视觉特征 [batch, seq_len, high_dim]
        :param llm_hidden_states: LLM 隐藏状态（可选）
        :return: 融合后的特征字典
        """
        batch_size = high_features.shape[0]
        seq_len = high_features.shape[1]
        
        # 投影各层特征
        low_proj = self.low_layer_proj(low_features)
        mid_proj = self.mid_layer_proj(mid_features)
        high_proj = self.high_layer_proj(high_features)
        
        # 维度对齐（使用线性投影扩展到 llm_dim）
        # low_proj: [batch, seq_len, llm_dim//4] -> [batch, seq_len, llm_dim]
        # mid_proj: [batch, seq_len, llm_dim//2] -> [batch, seq_len, llm_dim]
        low_expanded = self.low_dim_proj(low_proj)
        mid_expanded = self.mid_dim_proj(mid_proj)
        
        # 计算层级权重
        if self.enable_layer_weights:
            weights = F.softmax(self.layer_weights, dim=0)
            low_weight = weights[0]
            mid_weight = weights[1]
            high_weight = weights[2]
        else:
            low_weight = mid_weight = high_weight = 1.0 / 3
        
        # 加权融合
        weighted_low = low_expanded * low_weight
        weighted_mid = mid_expanded * mid_weight
        weighted_high = high_proj * high_weight
        
        # 跨层注意力融合 - 使用 cat 而不是 stack
        # 将三个特征沿序列维度拼接: [batch, seq_len*3, llm_dim]
        stacked_features = torch.cat([weighted_low, weighted_mid, weighted_high], dim=1)
        
        attn_out, attn_weights = self.cross_layer_attn(
            stacked_features, stacked_features, stacked_features
        )
        
        # 池化融合
        fused_visual = attn_out.mean(dim=1, keepdim=True)
        fused_visual = fused_visual.expand(-1, seq_len, -1)
        
        # 与 LLM 隐藏状态融合
        if llm_hidden_states is not None:
            concat_features = torch.cat([fused_visual, llm_hidden_states], dim=-1)
            
            # 门控融合
            gate = self.gate(concat_features)
            fused = self.fusion_layer(concat_features)
            
            # 残差连接
            residual_weight = torch.sigmoid(self.residual_weight)
            output = residual_weight * fused + (1 - residual_weight) * llm_hidden_states
            output = gate * output + (1 - gate) * fused_visual
        else:
            output = fused_visual
            gate = None
        
        return {
            'fused_features': output,
            'low_features': low_proj,
            'mid_features': mid_proj,
            'high_features': high_proj,
            'layer_weights': {
                'low': low_weight.item() if isinstance(low_weight, torch.Tensor) else low_weight,
                'mid': mid_weight.item() if isinstance(mid_weight, torch.Tensor) else mid_weight,
                'high': high_weight.item() if isinstance(high_weight, torch.Tensor) else high_weight
            },
            'attention_weights': attn_weights,
            'gate_values': gate
        }
    
    def get_injection_layers(self) -> List[Dict[str, Any]]:
        """
        获取注入层配置
        
        :return: 注入层配置列表
        """
        return [
            {
                'name': 'low_layer',
                'target_llm_layer': 4,   # 注入到 LLM 第 4 层
                'feature_type': 'texture_edge',
                'description': '浅层特征注入（纹理/边缘）'
            },
            {
                'name': 'mid_layer',
                'target_llm_layer': 16,  # 注入到 LLM 第 16 层
                'feature_type': 'structure',
                'description': '中层特征注入（部件/结构）'
            },
            {
                'name': 'high_layer',
                'target_llm_layer': 28,  # 注入到 LLM 第 28 层
                'feature_type': 'semantic',
                'description': '高层特征注入（语义/物体）'
            }
        ]


class DeepStackVisionEncoder(nn.Module):
    """
    DeepStack 视觉编码器包装器
    
    从视觉编码器中提取多层特征
    """
    
    def __init__(
        self,
        base_encoder: nn.Module,
        extraction_layers: List[int] = None,
        output_dim: int = 1024
    ):
        """
        初始化 DeepStack 视觉编码器
        
        :param base_encoder: 基础视觉编码器（如 ViT）
        :param extraction_layers: 特征提取层索引 [low_layer, mid_layer, high_layer]
        :param output_dim: 输出特征维度
        """
        super().__init__()
        
        self.base_encoder = base_encoder
        
        # 默认提取层（ViT-Base 的 4, 8, 12 层）
        if extraction_layers is None:
            extraction_layers = [4, 8, 12]
        
        self.extraction_layers = extraction_layers
        self.output_dim = output_dim
        
        # 特征缓存
        self.feature_cache = {}
        
        # 注册钩子
        self._register_hooks()
        
    def _register_hooks(self):
        """注册前向钩子以提取中间层特征"""
        
        def make_hook(layer_name):
            def hook(module, input, output):
                self.feature_cache[layer_name] = output
            return hook
        
        # 这里需要根据实际的视觉编码器结构注册钩子
        # 示例：假设 encoder.layers 是层列表
        if hasattr(self.base_encoder, 'layers'):
            for i, layer in enumerate(self.base_encoder.layers):
                if i in self.extraction_layers:
                    layer_idx = self.extraction_layers.index(i)
                    layer_name = ['low', 'mid', 'high'][layer_idx]
                    layer.register_forward_hook(make_hook(layer_name))
    
    def forward(self, images: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param images: 输入图像 [batch, channels, height, width]
        :return: 多层特征字典
        """
        # 清空缓存
        self.feature_cache = {}
        
        # 前向传播
        final_output = self.base_encoder(images)
        
        return {
            'low_features': self.feature_cache.get('low', final_output),
            'mid_features': self.feature_cache.get('mid', final_output),
            'high_features': self.feature_cache.get('high', final_output),
            'final_output': final_output
        }


def create_deepstack_injection(
    vision_dims: Dict[str, int] = None,
    llm_dim: int = 4096,
    num_heads: int = 8,
    dropout: float = 0.1
) -> DeepStackFeatureInjection:
    """
    创建 DeepStack 特征注入模块
    
    :param vision_dims: 各层视觉特征维度
    :param llm_dim: LLM 隐藏层维度
    :param num_heads: 注意力头数
    :param dropout: Dropout 比率
    :return: DeepStackFeatureInjection 实例
    """
    return DeepStackFeatureInjection(
        vision_dims=vision_dims,
        llm_dim=llm_dim,
        num_heads=num_heads,
        dropout=dropout
    )


def test_deepstack_injection():
    """测试 DeepStack 特征注入模块"""
    print("\n" + "=" * 60)
    print("DeepStack 多层特征注入模块测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 初始化 DeepStack 模块")
        deepstack = create_deepstack_injection(
            vision_dims={'low': 1024, 'mid': 1024, 'high': 1024},
            llm_dim=4096
        )
        print("[OK] DeepStack 模块初始化成功")
        
        print("\n[测试 2] 多层特征注入测试")
        batch_size = 2
        seq_len = 64
        
        low_features = torch.randn(batch_size, seq_len, 1024)
        mid_features = torch.randn(batch_size, seq_len, 1024)
        high_features = torch.randn(batch_size, seq_len, 1024)
        llm_hidden = torch.randn(batch_size, seq_len, 4096)
        
        result = deepstack(low_features, mid_features, high_features, llm_hidden)
        
        print(f"[OK] 特征注入成功")
        print(f"   融合特征维度：{result['fused_features'].shape}")
        print(f"   层级权重：{result['layer_weights']}")
        
        print("\n[测试 3] 无 LLM 隐藏状态测试")
        result_no_llm = deepstack(low_features, mid_features, high_features)
        print(f"[OK] 无 LLM 融合成功")
        print(f"   融合特征维度：{result_no_llm['fused_features'].shape}")
        
        print("\n[测试 4] 注入层配置")
        injection_layers = deepstack.get_injection_layers()
        for layer in injection_layers:
            print(f"   {layer['name']}: {layer['description']}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_deepstack_injection()
