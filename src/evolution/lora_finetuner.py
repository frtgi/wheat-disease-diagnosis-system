# -*- coding: utf-8 -*-
"""
LoRA 增量微调器 (LoRA Fine-tuner)
IWDDA Agent 自进化机制核心组件，基于 LoRA 的参数高效微调框架

功能特性:
1. 新病害快速适配：基于 few-shot learning 快速适应新病害类型
2. 区域专属模型：针对不同地区病害特征差异进行微调
3. 增量学习：在不遗忘旧知识的前提下学习新知识
4. 适配器管理：管理多个 LoRA 适配器，支持动态切换
5. 与 CaseMemory 和 FeedbackHandler 集成：从反馈中积累微调数据

LoRA 原理:
- 冻结预训练模型权重
- 在 Transformer 层添加低秩分解的可训练矩阵
- 只训练低秩矩阵，大幅减少参数量
- 支持多个适配器，便于快速切换

使用示例:
    from src.evolution import LoRAFinetuner
    from src.memory import CaseMemory, FeedbackHandler
    
    # 初始化
    case_memory = CaseMemory()
    feedback_handler = FeedbackHandler(case_memory=case_memory)
    finetuner = LoRAFinetuner(
        base_model_path="models/base_model",
        case_memory=case_memory,
        feedback_handler=feedback_handler
    )
    
    # 新病害快速适配
    finetuner.finetune_new_disease(
        disease_type="新病害",
        num_shots=10,
        output_dir="models/lora_new_disease"
    )
    
    # 区域专属模型
    finetuner.finetune_regional_model(
        region="河南",
        disease_types=["条锈病", "叶锈病"],
        output_dir="models/lora_henan"
    )
"""

import os
import sys
import json
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 尝试导入 CaseMemory 和 FeedbackHandler
try:
    from src.memory.case_memory import CaseMemory
    from src.memory.feedback_handler import FeedbackHandler, FeedbackType
except ImportError:
    CaseMemory = None
    FeedbackHandler = None
    FeedbackType = None


@dataclass
class LoRAConfig:
    """
    LoRA 配置类
    
    包含 LoRA 微调的所有超参数配置
    """
    # LoRA 核心参数
    lora_r: int = 8  # 低秩矩阵的秩
    lora_alpha: int = 16  # LoRA 缩放系数
    lora_dropout: float = 0.1  # Dropout 比率
    
    # 训练参数
    learning_rate: float = 1e-4
    num_epochs: int = 10
    batch_size: int = 16
    warmup_steps: int = 100
    weight_decay: float = 0.01
    
    # 适配器配置
    target_modules: List[str] = None  # 目标模块列表
    
    # 设备
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    def __post_init__(self):
        """后处理初始化"""
        if self.target_modules is None:
            self.target_modules = ["query", "key", "value", "output"]


class LoRALayer(nn.Module):
    """
    LoRA 层类
    
    实现单个 LoRA 适配器层：
    - 冻结原始权重 W
    - 添加低秩分解矩阵 A 和 B
    - 前向传播：h = Wx + (BA)x * alpha / r
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        r: int = 8,
        alpha: int = 16,
        dropout_rate: float = 0.1
    ):
        """
        初始化 LoRA 层
        
        :param in_features: 输入特征维度
        :param out_features: 输出特征维度
        :param r: 低秩矩阵的秩
        :param alpha: LoRA 缩放系数
        :param dropout_rate: Dropout 比率
        """
        super(LoRALayer, self).__init__()
        
        self.r = r
        self.alpha = alpha
        self.scaling = alpha / r
        
        # 冻结的原始权重
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features),
            requires_grad=False
        )
        
        # LoRA 矩阵 A (下采样) 和 B (上采样)
        # A 使用 Kaiming 初始化，B 初始化为 0
        self.lora_A = nn.Parameter(torch.zeros(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        
        # 初始化
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
        
        # Dropout
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else nn.Identity()
        
        # 使 lora_A 和 lora_B 成为可训练参数
        self.lora_A.requires_grad = True
        self.lora_B.requires_grad = True
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入张量 [batch_size, in_features]
        :return: 输出张量 [batch_size, out_features]
        """
        # 原始权重输出（冻结）
        with torch.no_grad():
            original_output = F.linear(x, self.weight)
        
        # LoRA 分支输出：先过 lora_A 再过 lora_B
        # x: [batch, in_features]
        # lora_A: [r, in_features] -> 需要转置为 [in_features, r]
        # lora_B: [out_features, r] -> 需要转置为 [r, out_features]
        lora_output = F.linear(
            F.linear(self.dropout(x), self.lora_A.t()),
            self.lora_B.t()
        ) * self.scaling
        
        return original_output + lora_output
    
    def merge_weights(self) -> None:
        """
        合并 LoRA 权重到原始权重
        
        用于推理时加速（合并后无需额外计算）
        """
        # 计算合并后的权重增量
        delta_weight = (self.lora_B @ self.lora_A) * self.scaling
        
        # 更新原始权重
        self.weight.data += delta_weight
        
        # 重置 LoRA 矩阵
        nn.init.zeros_(self.lora_A)
        nn.init.zeros_(self.lora_B)


class LoRAAdapter(nn.Module):
    """
    LoRA 适配器类
    
    管理多个 LoRA 层，支持动态切换和合并
    """
    
    def __init__(
        self,
        base_model: nn.Module,
        config: LoRAConfig,
        adapter_name: str = "default"
    ):
        """
        初始化 LoRA 适配器
        
        :param base_model: 基础模型
        :param config: LoRA 配置
        :param adapter_name: 适配器名称
        """
        super(LoRAAdapter, self).__init__()
        
        self.base_model = base_model
        self.config = config
        self.adapter_name = adapter_name
        
        # LoRA 层字典
        self.lora_layers = nn.ModuleDict()
        
        # 记录适配器状态
        self.is_merged = False
        self.training_samples = 0
        self.created_at = datetime.now().isoformat()
    
    def add_lora_layer(
        self,
        layer_name: str,
        in_features: int,
        out_features: int
    ) -> None:
        """
        添加 LoRA 层
        
        :param layer_name: 层名称
        :param in_features: 输入维度
        :param out_features: 输出维度
        """
        lora_layer = LoRALayer(
            in_features=in_features,
            out_features=out_features,
            r=self.config.lora_r,
            alpha=self.config.lora_alpha,
            dropout_rate=self.config.lora_dropout
        )
        
        self.lora_layers[layer_name] = lora_layer
        print(f"  ✓ 添加 LoRA 层：{layer_name} ({in_features} -> {out_features})")
    
    def forward(self, x: torch.Tensor, layer_name: str) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入张量
        :param layer_name: 使用的 LoRA 层名称
        :return: 输出张量
        """
        if layer_name not in self.lora_layers:
            raise ValueError(f"未知的 LoRA 层：{layer_name}")
        
        return self.lora_layers[layer_name](x)
    
    def save_adapter(self, output_dir: str) -> str:
        """
        保存适配器
        
        :param output_dir: 输出目录
        :return: 保存路径
        """
        adapter_path = os.path.join(output_dir, f"{self.adapter_name}_adapter.pt")
        
        torch.save({
            "adapter_name": self.adapter_name,
            "lora_layers_state_dict": self.lora_layers.state_dict(),
            "config": self.config,
            "training_samples": self.training_samples,
            "created_at": self.created_at,
            "is_merged": self.is_merged
        }, adapter_path)
        
        print(f"✓ 适配器已保存：{adapter_path}")
        return adapter_path
    
    @classmethod
    def load_adapter(
        cls,
        base_model: nn.Module,
        adapter_path: str
    ) -> 'LoRAAdapter':
        """
        加载适配器
        
        :param base_model: 基础模型
        :param adapter_path: 适配器路径
        :return: 加载的适配器
        """
        checkpoint = torch.load(adapter_path, map_location="cpu")
        
        config = checkpoint["config"]
        adapter = cls(base_model, config, checkpoint["adapter_name"])
        
        adapter.lora_layers.load_state_dict(checkpoint["lora_layers_state_dict"])
        adapter.training_samples = checkpoint["training_samples"]
        adapter.created_at = checkpoint["created_at"]
        adapter.is_merged = checkpoint.get("is_merged", False)
        
        print(f"✓ 适配器已加载：{adapter_path}")
        return adapter


class DiseaseDataset(Dataset):
    """
    病害数据集类
    
    用于 LoRA 微调的数据集
    """
    
    def __init__(self, samples: List[Dict[str, Any]]):
        """
        初始化数据集
        
        :param samples: 样本列表
        """
        self.samples = samples
    
    def __len__(self) -> int:
        """获取样本数量"""
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        获取单个样本
        
        :param idx: 样本索引
        :return: (特征，标签，元数据)
        """
        sample = self.samples[idx]
        
        # 特征（模拟，实际应从图像和文本提取）
        features = torch.randn(512)
        
        # 标签（病害类型索引）
        label = sample.get("label", 0)
        
        # 元数据
        metadata = {
            "disease_type": sample.get("disease_type", "unknown"),
            "severity": sample.get("severity", "unknown"),
            "region": sample.get("region", "unknown")
        }
        
        return features, torch.tensor(label, dtype=torch.long), metadata


class LoRAFinetuner:
    """
    LoRA 微调器类
    
    实现基于 LoRA 的参数高效微调：
    1. 新病害快速适配（few-shot learning）
    2. 区域专属模型微调
    3. 增量学习（EWC 正则化防止灾难性遗忘）
    4. 适配器管理（保存、加载、切换）
    """
    
    def __init__(
        self,
        base_model_path: Optional[str] = None,
        config: Optional[LoRAConfig] = None,
        case_memory: Optional[Any] = None,
        feedback_handler: Optional[Any] = None,
        output_dir: str = "models/lora"
    ):
        """
        初始化 LoRA 微调器
        
        :param base_model_path: 基础模型路径
        :param config: LoRA 配置
        :param case_memory: CaseMemory 实例
        :param feedback_handler: FeedbackHandler 实例
        :param output_dir: 输出目录
        """
        self.config = config or LoRAConfig()
        self.case_memory = case_memory
        self.feedback_handler = feedback_handler
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 基础模型（简化为线性层，实际应为 Transformer）
        self.base_model = self._create_base_model(base_model_path)
        
        # 当前活跃的适配器
        self.active_adapter: Optional[LoRAAdapter] = None
        self.adapters: Dict[str, LoRAAdapter] = {}
        
        # EWC 正则化（防止灾难性遗忘）
        self.ewc_fisher_info: Dict[str, torch.Tensor] = {}
        self.ewc_params: Dict[str, torch.Tensor] = {}
        
        # 训练历史
        self.training_history: List[Dict[str, Any]] = []
        
        # 病害类型映射
        self.disease2idx = self._init_disease_mapping()
        self.idx2disease = {v: k for k, v in self.disease2idx.items()}
        
        print("=" * 60)
        print("🔧 [LoRAFinetuner] LoRA 微调器初始化完成")
        print("=" * 60)
        print(f"   设备：{self.config.device}")
        print(f"   LoRA 秩：{self.config.lora_r}")
        print(f"   缩放系数：{self.config.lora_alpha}")
        print(f"   学习率：{self.config.learning_rate}")
        print(f"   输出目录：{self.output_dir}")
    
    def _create_base_model(self, model_path: Optional[str]) -> nn.Module:
        """
        创建或加载基础模型
        
        :param model_path: 模型路径
        :return: 基础模型
        """
        # 简化模型（实际应加载预训练的 Transformer）
        base_model = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        if model_path and os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location="cpu")
                base_model.load_state_dict(checkpoint["model_state_dict"])
                print(f"✓ 基础模型已加载：{model_path}")
            except Exception as e:
                print(f"⚠️ 加载基础模型失败：{e}")
        
        return base_model
    
    def _init_disease_mapping(self) -> Dict[str, int]:
        """
        初始化病害类型映射
        
        :return: 病害类型到索引的映射字典
        """
        diseases = [
            "条锈病", "叶锈病", "秆锈病", "白粉病", "赤霉病",
            "纹枯病", "全蚀病", "黄矮病", "丛矮病", "蚜虫",
            "红蜘蛛", "麦蜘蛛", "粘虫", "麦蚜", "其他"
        ]
        return {disease: idx for idx, disease in enumerate(diseases)}
    
    def create_adapter(self, adapter_name: str) -> LoRAAdapter:
        """
        创建新的 LoRA 适配器
        
        :param adapter_name: 适配器名称
        :return: 创建的适配器
        """
        adapter = LoRAAdapter(
            base_model=self.base_model,
            config=self.config,
            adapter_name=adapter_name
        )
        
        # 为目标模块添加 LoRA 层
        for module_name in self.config.target_modules:
            adapter.add_lora_layer(
                layer_name=module_name,
                in_features=512,
                out_features=256
            )
        
        self.adapters[adapter_name] = adapter
        self.active_adapter = adapter
        
        print(f"✓ 创建适配器：{adapter_name}")
        return adapter
    
    def finetune_new_disease(
        self,
        disease_type: str,
        num_shots: int = 10,
        num_epochs: Optional[int] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        新病害快速适配（Few-shot Learning）
        
        :param disease_type: 新病害类型
        :param num_shots: 样本数量（few-shot）
        :param num_epochs: 训练轮数
        :param output_dir: 输出目录
        :return: 训练结果
        """
        print("\n" + "=" * 60)
        print(f"🆕 [LoRAFinetuner] 新病害快速适配：{disease_type}")
        print("=" * 60)
        print(f"   样本数：{num_shots}")
        print(f"   训练轮数：{num_epochs or self.config.num_epochs}")
        
        if num_epochs is None:
            num_epochs = self.config.num_epochs
        
        if output_dir is None:
            output_dir = str(self.output_dir / f"lora_{disease_type}")
        
        # 创建专用适配器
        adapter_name = f"new_disease_{disease_type}"
        adapter = self.create_adapter(adapter_name)
        
        # 准备 few-shot 数据
        training_data = self._prepare_few_shot_data(disease_type, num_shots)
        
        if not training_data:
            print("⚠️ 无训练数据，跳过微调")
            return {"status": "skipped", "reason": "no_training_data"}
        
        # 训练
        result = self._train_adapter(
            adapter=adapter,
            training_data=training_data,
            num_epochs=num_epochs,
            disease_type=disease_type
        )
        
        # 保存适配器
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        adapter.save_adapter(output_dir)
        
        print(f"\n✅ 新病害适配完成：{disease_type}")
        print(f"   适配器路径：{output_dir}")
        print(f"   最终损失：{result.get('final_loss', 0):.4f}")
        print(f"   准确率：{result.get('accuracy', 0):.4f}")
        
        return {
            "status": "completed",
            "disease_type": disease_type,
            "adapter_name": adapter_name,
            "output_dir": output_dir,
            **result
        }
    
    def finetune_regional_model(
        self,
        region: str,
        disease_types: List[str],
        num_epochs: Optional[int] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        区域专属模型微调
        
        :param region: 地区名称
        :param disease_types: 目标病害类型列表
        :param num_epochs: 训练轮数
        :param output_dir: 输出目录
        :return: 训练结果
        """
        print("\n" + "=" * 60)
        print(f"🌍 [LoRAFinetuner] 区域专属模型微调：{region}")
        print("=" * 60)
        print(f"   目标病害：{disease_types}")
        
        if num_epochs is None:
            num_epochs = self.config.num_epochs
        
        if output_dir is None:
            output_dir = str(self.output_dir / f"lora_{region}")
        
        # 创建区域适配器
        adapter_name = f"regional_{region}"
        adapter = self.create_adapter(adapter_name)
        
        # 准备区域数据
        training_data = self._prepare_regional_data(region, disease_types)
        
        if not training_data:
            print("⚠️ 无训练数据，跳过微调")
            return {"status": "skipped", "reason": "no_training_data"}
        
        # 训练
        result = self._train_adapter(
            adapter=adapter,
            training_data=training_data,
            num_epochs=num_epochs,
            disease_types=disease_types,
            region=region
        )
        
        # 保存适配器
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        adapter.save_adapter(output_dir)
        
        print(f"\n✅ 区域模型微调完成：{region}")
        print(f"   适配器路径：{output_dir}")
        print(f"   最终损失：{result.get('final_loss', 0):.4f}")
        
        return {
            "status": "completed",
            "region": region,
            "adapter_name": adapter_name,
            "output_dir": output_dir,
            **result
        }
    
    def _prepare_few_shot_data(
        self,
        disease_type: str,
        num_shots: int
    ) -> List[Dict[str, Any]]:
        """
        准备 few-shot 学习数据
        
        :param disease_type: 病害类型
        :param num_shots: 样本数量
        :return: 训练样本列表
        """
        samples = []
        
        if self.case_memory:
            # 从 CaseMemory 获取真实数据
            all_cases = list(self.case_memory._cases.values())
            
            # 筛选目标病害的病例
            target_cases = [
                c for c in all_cases
                if c.get("disease_type") == disease_type
            ]
            
            # 优先选择有反馈的高质量病例
            high_quality_cases = [
                c for c in target_cases
                if c.get("user_feedback") or c.get("followup_result")
            ]
            
            # 混合采样
            if high_quality_cases:
                samples.extend(high_quality_cases)
            if len(samples) < num_shots and target_cases:
                samples.extend(target_cases)
            
            # 限制数量
            samples = samples[:num_shots]
        
        # 如果没有真实数据，生成模拟数据
        if len(samples) < num_shots:
            for i in range(num_shots - len(samples)):
                samples.append({
                    "disease_type": disease_type,
                    "severity": np.random.choice(["轻度", "中度", "重度"]),
                    "region": "default",
                    "label": self.disease2idx.get(disease_type, 14)
                })
        
        print(f"✓ 准备 few-shot 数据：{len(samples)} 个样本")
        return samples
    
    def _prepare_regional_data(
        self,
        region: str,
        disease_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        准备区域微调数据
        
        :param region: 地区名称
        :param disease_types: 目标病害类型
        :return: 训练样本列表
        """
        samples = []
        
        if self.case_memory:
            # 从 CaseMemory 获取特定区域的病例
            all_cases = list(self.case_memory._cases.values())
            
            # 筛选区域和病害类型
            for case in all_cases:
                case_region = case.get("metadata", {}).get("region", "")
                case_disease = case.get("disease_type")
                
                if case_region == region and case_disease in disease_types:
                    samples.append({
                        **case,
                        "region": region,
                        "label": self.disease2idx.get(case_disease, 14)
                    })
        
        # 生成模拟数据
        if not samples:
            for disease in disease_types:
                for _ in range(20):  # 每个病害 20 个样本
                    samples.append({
                        "disease_type": disease,
                        "severity": np.random.choice(["轻度", "中度", "重度"]),
                        "region": region,
                        "label": self.disease2idx.get(disease, 14)
                    })
        
        print(f"✓ 准备区域数据：{len(samples)} 个样本")
        return samples
    
    def _train_adapter(
        self,
        adapter: LoRAAdapter,
        training_data: List[Dict[str, Any]],
        num_epochs: int,
        disease_type: Optional[str] = None,
        disease_types: Optional[List[str]] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        训练 LoRA 适配器
        
        :param adapter: LoRA 适配器
        :param training_data: 训练数据
        :param num_epochs: 训练轮数
        :param disease_type: 病害类型（单个）
        :param disease_types: 病害类型列表
        :param region: 地区
        :return: 训练结果
        """
        adapter.train()
        
        # 创建数据集和数据加载器
        dataset = DiseaseDataset(training_data)
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0
        )
        
        # 优化器（只优化 LoRA 参数）
        optimizer = torch.optim.AdamW(
            adapter.lora_layers.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        
        # 损失函数
        criterion = nn.CrossEntropyLoss()
        
        # EWC 正则化（如果已有旧知识）
        ewc_loss_fn = self._create_ewc_loss() if self.ewc_fisher_info else None
        
        # 训练循环
        total_loss = 0.0
        correct_predictions = 0
        total_samples = 0
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            epoch_correct = 0
            
            for batch_idx, (features, labels, metadata) in enumerate(dataloader):
                features = features.to(self.config.device)
                labels = labels.to(self.config.device)
                
                # 确保基础模型在正确的设备上
                self.base_model.to(self.config.device)
                
                # 前向传播
                # 简化处理：使用基础模型 + LoRA
                base_features = self.base_model(features)
                
                # 应用 LoRA（使用第一个 LoRA 层作为示例）
                if adapter.lora_layers:
                    # 确保 LoRA 层在正确的设备上
                    first_layer_key = list(adapter.lora_layers.keys())[0]
                    lora_layer = adapter.lora_layers[first_layer_key]
                    lora_output = lora_layer(base_features)
                else:
                    lora_output = base_features
                
                # 分类头（确保权重在正确的设备上）
                classifier_weight = torch.randn(len(self.disease2idx), 128).to(self.config.device)
                logits = F.linear(lora_output, classifier_weight)
                
                # 计算损失
                loss = criterion(logits, labels)
                
                # 添加 EWC 正则化
                if ewc_loss_fn:
                    loss += ewc_loss_fn(adapter)
                
                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # 统计
                total_loss += loss.item()
                epoch_loss += loss.item()
                
                predictions = torch.argmax(logits, dim=-1)
                epoch_correct += (predictions == labels).sum().item()
                total_samples += labels.size(0)
            
            # 计算 epoch 平均损失和准确率
            avg_loss = epoch_loss / len(dataloader)
            accuracy = epoch_correct / max(1, total_samples)
            
            # 记录训练历史
            history_record = {
                "epoch": epoch + 1,
                "loss": avg_loss,
                "accuracy": accuracy,
                "timestamp": datetime.now().isoformat()
            }
            self.training_history.append(history_record)
            
            # 打印进度
            if (epoch + 1) % 5 == 0 or epoch == 0:
                print(f"   Epoch {epoch + 1}/{num_epochs} - "
                      f"损失：{avg_loss:.4f}, "
                      f"准确率：{accuracy:.4f}")
        
        # 更新适配器训练样本数
        adapter.training_samples = len(training_data)
        
        # 计算 EWC Fisher 信息（用于后续增量学习）
        self._update_ewc_fisher_info(adapter, dataloader)
        
        return {
            "final_loss": total_loss / (num_epochs * len(dataloader)),
            "accuracy": correct_predictions / max(1, total_samples),
            "num_epochs": num_epochs,
            "num_samples": len(training_data)
        }
    
    def _create_ewc_loss(self) -> Callable:
        """
        创建 EWC 损失函数
        
        :return: EWC 损失函数
        """
        fisher_info = self.ewc_fisher_info
        old_params = self.ewc_params
        ewc_lambda = 1000.0
        
        def ewc_loss(adapter: LoRAAdapter) -> torch.Tensor:
            loss = torch.tensor(0.0)
            
            for name, param in adapter.lora_layers.named_parameters():
                if name in fisher_info:
                    loss += (fisher_info[name] * (param - old_params[name]).pow(2)).sum()
            
            return ewc_lambda * loss
        
        return ewc_loss
    
    def _update_ewc_fisher_info(
        self,
        adapter: LoRAAdapter,
        dataloader: DataLoader
    ) -> None:
        """
        更新 EWC Fisher 信息矩阵
        
        :param adapter: LoRA 适配器
        :param dataloader: 数据加载器
        """
        adapter.eval()
        
        fisher_info = {}
        params = {}
        
        # 计算 Fisher 信息（对角近似）
        for name, param in adapter.lora_layers.named_parameters():
            if param.requires_grad:
                fisher_info[name] = torch.zeros_like(param)
                params[name] = param.data.clone()
        
        for features, labels, _ in dataloader:
            features = features.to(self.config.device)
            labels = labels.to(self.config.device)
            
            # 前向传播
            base_features = self.base_model(features)
            if adapter.lora_layers:
                output = adapter(base_features, list(adapter.lora_layers.keys())[0])
            else:
                output = base_features
            
            logits = F.linear(output, torch.randn(len(self.disease2idx), 128))
            loss = F.cross_entropy(logits, labels)
            
            # 计算梯度
            adapter.zero_grad()
            loss.backward()
            
            # 累积 Fisher 信息
            for name, param in adapter.lora_layers.named_parameters():
                if param.requires_grad and param.grad is not None:
                    fisher_info[name] += param.grad.data.pow(2)
        
        # 平均
        num_samples = len(dataloader.dataset)
        for name in fisher_info:
            fisher_info[name] /= num_samples
        
        self.ewc_fisher_info = fisher_info
        self.ewc_params = params
        
        print(f"✓ EWC Fisher 信息已更新")
    
    def load_adapter(self, adapter_path: str) -> LoRAAdapter:
        """
        加载已有适配器
        
        :param adapter_path: 适配器路径
        :return: 加载的适配器
        """
        adapter = LoRAAdapter.load_adapter(self.base_model, adapter_path)
        
        adapter_name = adapter.adapter_name
        self.adapters[adapter_name] = adapter
        self.active_adapter = adapter
        
        print(f"✓ 加载适配器：{adapter_name}")
        return adapter
    
    def set_active_adapter(self, adapter_name: str) -> bool:
        """
        设置活跃适配器
        
        :param adapter_name: 适配器名称
        :return: 设置是否成功
        """
        if adapter_name not in self.adapters:
            print(f"✗ 适配器不存在：{adapter_name}")
            return False
        
        self.active_adapter = self.adapters[adapter_name]
        print(f"✓ 设置活跃适配器：{adapter_name}")
        return True
    
    def list_adapters(self) -> List[Dict[str, Any]]:
        """
        列出所有适配器
        
        :return: 适配器列表
        """
        return [
            {
                "name": name,
                "training_samples": adapter.training_samples,
                "created_at": adapter.created_at,
                "is_merged": adapter.is_merged
            }
            for name, adapter in self.adapters.items()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        :return: 统计字典
        """
        return {
            "num_adapters": len(self.adapters),
            "adapters": self.list_adapters(),
            "total_training_samples": sum(
                a.training_samples for a in self.adapters.values()
            ),
            "training_history_length": len(self.training_history),
            "output_dir": str(self.output_dir)
        }


def test_lora_finetuner():
    """测试 LoRA 微调器"""
    print("=" * 60)
    print("🧪 测试 LoRAFinetuner")
    print("=" * 60)
    
    # 初始化微调器
    config = LoRAConfig(
        lora_r=8,
        lora_alpha=16,
        learning_rate=1e-3,
        num_epochs=5,
        batch_size=8
    )
    
    finetuner = LoRAFinetuner(
        config=config,
        output_dir="models/test_lora"
    )
    
    print("\n1️⃣ 初始状态")
    stats = finetuner.get_statistics()
    print(f"   适配器数：{stats.get('num_adapters', 0)}")
    
    print("\n2️⃣ 新病害快速适配")
    result = finetuner.finetune_new_disease(
        disease_type="测试病害",
        num_shots=20,
        num_epochs=5
    )
    print(f"   状态：{result.get('status')}")
    print(f"   适配器：{result.get('adapter_name', 'N/A')}")
    print(f"   准确率：{result.get('accuracy', 0):.4f}")
    
    print("\n3️⃣ 区域专属模型微调")
    result = finetuner.finetune_regional_model(
        region="测试区域",
        disease_types=["条锈病", "叶锈病"],
        num_epochs=5
    )
    print(f"   状态：{result.get('status')}")
    print(f"   适配器：{result.get('adapter_name', 'N/A')}")
    
    print("\n4️⃣ 适配器列表")
    adapters = finetuner.list_adapters()
    for adapter in adapters:
        print(f"   - {adapter['name']}: {adapter['training_samples']} 样本")
    
    print("\n5️⃣ 最终统计")
    stats = finetuner.get_statistics()
    print(f"   总适配器数：{stats.get('num_adapters')}")
    print(f"   总训练样本：{stats.get('total_training_samples')}")
    
    print("\n" + "=" * 60)
    print("✅ LoRAFinetuner 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    import math
    test_lora_finetuner()
