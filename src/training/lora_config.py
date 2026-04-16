# -*- coding: utf-8 -*-
"""
全组件 LoRA 微调配置模块 (Full-Component LoRA Fine-tuning)

实现同时对 Visual Encoder、Adapter 和 Language Model 进行 LoRA 微调：
1. 视觉编码器 LoRA 配置
2. 适配器 LoRA 配置
3. 语言模型 LoRA 配置
4. 统一的微调管理

技术特性:
- 多组件 LoRA 配置
- 参数高效微调
- 梯度检查点
- 混合精度训练
"""
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import json


@dataclass
class LoRAConfig:
    """
    LoRA 配置参数
    
    定义单个组件的 LoRA 配置
    """
    r: int = 8                          # LoRA 秩
    lora_alpha: int = 16                # LoRA 缩放系数
    lora_dropout: float = 0.05          # LoRA Dropout
    target_modules: List[str] = field(default_factory=list)  # 目标模块
    bias: str = "none"                  # 偏置处理方式
    fan_in_fan_out: bool = False        # 是否使用 fan_in_fan_out
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'r': self.r,
            'lora_alpha': self.lora_alpha,
            'lora_dropout': self.lora_dropout,
            'target_modules': self.target_modules,
            'bias': self.bias,
            'fan_in_fan_out': self.fan_in_fan_out
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoRAConfig':
        """从字典创建"""
        return cls(
            r=data.get('r', 8),
            lora_alpha=data.get('lora_alpha', 16),
            lora_dropout=data.get('lora_dropout', 0.05),
            target_modules=data.get('target_modules', []),
            bias=data.get('bias', 'none'),
            fan_in_fan_out=data.get('fan_in_fan_out', False)
        )


@dataclass
class VisionEncoderLoRAConfig(LoRAConfig):
    """
    视觉编码器 LoRA 配置
    
    针对 ViT 视觉编码器的特定配置
    """
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "qkv", "proj", "fc1", "fc2"
    ])
    bias: str = "none"
    
    # 视觉编码器特有配置
    attention_layers: List[int] = field(default_factory=list)  # 应用 LoRA 的注意力层
    mlp_layers: List[int] = field(default_factory=list)        # 应用 LoRA 的 MLP 层
    freeze_patch_embed: bool = True                            # 是否冻结 patch embedding


@dataclass
class AdapterLoRAConfig(LoRAConfig):
    """
    适配器 LoRA 配置
    
    针对视觉-语言适配器的特定配置
    """
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "visual_proj", "text_proj", "cross_attn"
    ])
    bias: str = "none"
    
    # 适配器特有配置
    adapter_type: str = "linear"   # 适配器类型
    adapter_dim: int = 512         # 适配器维度


@dataclass
class LanguageModelLoRAConfig(LoRAConfig):
    """
    语言模型 LoRA 配置
    
    针对 LLM 的特定配置
    """
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    bias: str = "none"
    
    # 语言模型特有配置
    attention_layers: List[int] = field(default_factory=list)  # 应用 LoRA 的注意力层
    mlp_layers: List[int] = field(default_factory=list)        # 应用 LoRA 的 MLP 层
    freeze_embed_tokens: bool = True                            # 是否冻结 token embedding
    freeze_lm_head: bool = True                                 # 是否冻结 LM head


@dataclass
class FullComponentLoRAConfig:
    """
    全组件 LoRA 微调配置
    
    整合视觉编码器、适配器和语言模型的 LoRA 配置
    """
    vision_config: VisionEncoderLoRAConfig = field(default_factory=VisionEncoderLoRAConfig)
    adapter_config: AdapterLoRAConfig = field(default_factory=AdapterLoRAConfig)
    language_config: LanguageModelLoRAConfig = field(default_factory=LanguageModelLoRAConfig)
    
    # 全局配置
    enable_vision_lora: bool = True
    enable_adapter_lora: bool = True
    enable_language_lora: bool = True
    
    # 训练配置
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_grad_norm: float = 1.0
    
    # 优化配置
    gradient_checkpointing: bool = True
    use_reentrant: bool = False
    optim: str = "adamw_torch"
    
    # 精度配置
    bf16: bool = True
    fp16: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'vision_config': self.vision_config.to_dict(),
            'adapter_config': self.adapter_config.to_dict(),
            'language_config': self.language_config.to_dict(),
            'enable_vision_lora': self.enable_vision_lora,
            'enable_adapter_lora': self.enable_adapter_lora,
            'enable_language_lora': self.enable_language_lora,
            'learning_rate': self.learning_rate,
            'weight_decay': self.weight_decay,
            'warmup_ratio': self.warmup_ratio,
            'num_train_epochs': self.num_train_epochs,
            'per_device_train_batch_size': self.per_device_train_batch_size,
            'gradient_accumulation_steps': self.gradient_accumulation_steps,
            'max_grad_norm': self.max_grad_norm,
            'gradient_checkpointing': self.gradient_checkpointing,
            'use_reentrant': self.use_reentrant,
            'optim': self.optim,
            'bf16': self.bf16,
            'fp16': self.fp16
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FullComponentLoRAConfig':
        """从字典创建"""
        return cls(
            vision_config=VisionEncoderLoRAConfig.from_dict(data.get('vision_config', {})),
            adapter_config=AdapterLoRAConfig.from_dict(data.get('adapter_config', {})),
            language_config=LanguageModelLoRAConfig.from_dict(data.get('language_config', {})),
            enable_vision_lora=data.get('enable_vision_lora', True),
            enable_adapter_lora=data.get('enable_adapter_lora', True),
            enable_language_lora=data.get('enable_language_lora', True),
            learning_rate=data.get('learning_rate', 1e-4),
            weight_decay=data.get('weight_decay', 0.01),
            warmup_ratio=data.get('warmup_ratio', 0.1),
            num_train_epochs=data.get('num_train_epochs', 3),
            per_device_train_batch_size=data.get('per_device_train_batch_size', 4),
            gradient_accumulation_steps=data.get('gradient_accumulation_steps', 4),
            max_grad_norm=data.get('max_grad_norm', 1.0),
            gradient_checkpointing=data.get('gradient_checkpointing', True),
            use_reentrant=data.get('use_reentrant', False),
            optim=data.get('optim', 'adamw_torch'),
            bf16=data.get('bf16', True),
            fp16=data.get('fp16', False)
        )


class LoRAModule(nn.Module):
    """
    LoRA 模块
    
    实现低秩适应 (Low-Rank Adaptation)
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        fan_in_fan_out: bool = False
    ):
        """
        初始化 LoRA 模块
        
        :param in_features: 输入特征维度
        :param out_features: 输出特征维度
        :param r: LoRA 秩
        :param lora_alpha: LoRA 缩放系数
        :param lora_dropout: Dropout 比率
        :param fan_in_fan_out: 是否使用 fan_in_fan_out
        """
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        self.r = r
        self.lora_alpha = lora_alpha
        self.scaling = lora_alpha / r
        self.fan_in_fan_out = fan_in_fan_out
        
        # LoRA A 矩阵 (降维)
        self.lora_A = nn.Parameter(torch.zeros(r, in_features))
        
        # LoRA B 矩阵 (升维)
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        
        # Dropout
        self.lora_dropout = nn.Dropout(p=lora_dropout) if lora_dropout > 0 else nn.Identity()
        
        # 初始化
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入张量
        :return: LoRA 输出
        """
        result = self.lora_dropout(x) @ self.lora_A.T @ self.lora_B.T
        return result * self.scaling


class LoRALinear(nn.Module):
    """
    带 LoRA 的线性层
    
    将原始线性层与 LoRA 模块结合
    """
    
    def __init__(
        self,
        original_linear: nn.Linear,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05
    ):
        """
        初始化带 LoRA 的线性层
        
        :param original_linear: 原始线性层
        :param r: LoRA 秩
        :param lora_alpha: LoRA 缩放系数
        :param lora_dropout: Dropout 比率
        """
        super().__init__()
        
        self.original_linear = original_linear
        self.original_linear.weight.requires_grad = False
        
        if self.original_linear.bias is not None:
            self.original_linear.bias.requires_grad = False
        
        self.lora = LoRAModule(
            in_features=original_linear.in_features,
            out_features=original_linear.out_features,
            r=r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入张量
        :return: 输出张量
        """
        return self.original_linear(x) + self.lora(x)


def apply_lora_to_module(
    module: nn.Module,
    target_modules: List[str],
    r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05
) -> nn.Module:
    """
    将 LoRA 应用到模块的指定子模块
    
    :param module: 目标模块
    :param target_modules: 目标子模块名称列表
    :param r: LoRA 秩
    :param lora_alpha: LoRA 缩放系数
    :param lora_dropout: Dropout 比率
    :return: 修改后的模块
    """
    for name, submodule in module.named_modules():
        # 检查是否是目标模块
        for target in target_modules:
            if target in name and isinstance(submodule, nn.Linear):
                # 获取父模块和属性名
                parts = name.rsplit('.', 1)
                if len(parts) == 2:
                    parent_name, attr_name = parts
                    parent = module.get_submodule(parent_name)
                else:
                    parent = module
                    attr_name = name
                
                # 替换为 LoRA 线性层
                lora_linear = LoRALinear(
                    submodule,
                    r=r,
                    lora_alpha=lora_alpha,
                    lora_dropout=lora_dropout
                )
                setattr(parent, attr_name, lora_linear)
                
    return module


def get_lora_parameters(model: nn.Module) -> List[nn.Parameter]:
    """
    获取模型中所有 LoRA 参数
    
    :param model: 模型
    :return: LoRA 参数列表
    """
    lora_params = []
    for name, param in model.named_parameters():
        if 'lora_' in name:
            lora_params.append(param)
    return lora_params


def count_lora_parameters(model: nn.Module) -> Dict[str, int]:
    """
    统计 LoRA 参数数量
    
    :param model: 模型
    :return: 参数统计字典
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    lora_params = sum(p.numel() for p in get_lora_parameters(model))
    
    return {
        'total_params': total_params,
        'trainable_params': trainable_params,
        'lora_params': lora_params,
        'trainable_ratio': trainable_params / total_params if total_params > 0 else 0,
        'lora_ratio': lora_params / total_params if total_params > 0 else 0
    }


def create_qwen3vl_lora_config(
    vision_r: int = 8,
    adapter_r: int = 8,
    language_r: int = 16,
    learning_rate: float = 1e-4
) -> FullComponentLoRAConfig:
    """
    创建 Qwen3-VL 的 LoRA 配置
    
    :param vision_r: 视觉编码器 LoRA 秩
    :param adapter_r: 适配器 LoRA 秩
    :param language_r: 语言模型 LoRA 秩
    :param learning_rate: 学习率
    :return: 完整 LoRA 配置
    """
    vision_config = VisionEncoderLoRAConfig(
        r=vision_r,
        lora_alpha=vision_r * 2,
        target_modules=["qkv", "proj", "fc1", "fc2"],
        attention_layers=list(range(12)),  # 所有注意力层
        mlp_layers=list(range(12)),        # 所有 MLP 层
        freeze_patch_embed=True
    )
    
    adapter_config = AdapterLoRAConfig(
        r=adapter_r,
        lora_alpha=adapter_r * 2,
        target_modules=["visual_proj", "text_proj", "cross_attn"],
        adapter_type="linear",
        adapter_dim=512
    )
    
    language_config = LanguageModelLoRAConfig(
        r=language_r,
        lora_alpha=language_r * 2,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        attention_layers=list(range(32)),  # Qwen3-VL-4B 有 32 层
        mlp_layers=list(range(32)),
        freeze_embed_tokens=True,
        freeze_lm_head=True
    )
    
    return FullComponentLoRAConfig(
        vision_config=vision_config,
        adapter_config=adapter_config,
        language_config=language_config,
        learning_rate=learning_rate
    )


def test_lora_config():
    """测试 LoRA 配置模块"""
    import math
    print("\n" + "=" * 60)
    print("全组件 LoRA 微调配置测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 创建 Qwen3-VL LoRA 配置")
        config = create_qwen3vl_lora_config()
        print(f"[OK] 视觉编码器 LoRA 秩: {config.vision_config.r}")
        print(f"[OK] 适配器 LoRA 秩: {config.adapter_config.r}")
        print(f"[OK] 语言模型 LoRA 秩: {config.language_config.r}")
        print(f"[OK] 学习率: {config.learning_rate}")
        
        print("\n[测试 2] 配置序列化")
        config_dict = config.to_dict()
        restored_config = FullComponentLoRAConfig.from_dict(config_dict)
        print(f"[OK] 序列化和反序列化成功")
        
        print("\n[测试 3] LoRA 模块测试")
        lora_module = LoRAModule(
            in_features=768,
            out_features=768,
            r=8,
            lora_alpha=16
        )
        
        x = torch.randn(2, 10, 768)
        output = lora_module(x)
        print(f"[OK] LoRA 输出维度: {output.shape}")
        
        print("\n[测试 4] LoRA 线性层测试")
        original_linear = nn.Linear(768, 768)
        lora_linear = LoRALinear(original_linear, r=8, lora_alpha=16)
        
        output = lora_linear(x)
        print(f"[OK] LoRA 线性层输出维度: {output.shape}")
        
        print("\n[测试 5] 参数统计")
        param_stats = count_lora_parameters(lora_linear)
        print(f"[OK] 总参数: {param_stats['total_params']}")
        print(f"[OK] 可训练参数: {param_stats['trainable_params']}")
        print(f"[OK] LoRA 参数: {param_stats['lora_params']}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


# 导入 math 模块
import math


if __name__ == "__main__":
    test_lora_config()
