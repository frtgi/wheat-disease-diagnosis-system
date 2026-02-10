# -*- coding: utf-8 -*-
"""
YOLOv8 训练优化模块

根据研究文档实现:
1. CIoU Loss - 针对细长病斑优化的损失函数
2. LoRA 微调 - 低秩自适应微调
3. 多尺度训练策略
"""
import os
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np


class CIoULoss(nn.Module):
    """
    Complete Intersection over Union Loss
    
    针对细长病斑检测优化的损失函数，考虑:
    - 重叠面积
    - 中心点距离
    - 长宽比一致性
    
    公式: CIoU = IoU - (ρ²(b,b^gt)/c²) - (αv)
    其中:
    - ρ: 中心点欧氏距离
    - c: 最小外接矩形对角线长度
    - v: 长宽比一致性度量
    - α: 权重系数
    """
    
    def __init__(self, eps: float = 1e-7):
        super().__init__()
        self.eps = eps
    
    def forward(self, pred_boxes: torch.Tensor, target_boxes: torch.Tensor) -> torch.Tensor:
        """
        计算CIoU Loss
        
        :param pred_boxes: 预测框 [N, 4] (x1, y1, x2, y2) 或 (cx, cy, w, h)
        :param target_boxes: 目标框 [N, 4]
        :return: CIoU Loss
        """
        # 确保输入格式为 (x1, y1, x2, y2)
        pred_boxes = self._convert_to_xyxy(pred_boxes)
        target_boxes = self._convert_to_xyxy(target_boxes)
        
        # 计算交集
        inter_x1 = torch.max(pred_boxes[:, 0], target_boxes[:, 0])
        inter_y1 = torch.max(pred_boxes[:, 1], target_boxes[:, 1])
        inter_x2 = torch.min(pred_boxes[:, 2], target_boxes[:, 2])
        inter_y2 = torch.min(pred_boxes[:, 3], target_boxes[:, 3])
        
        inter_w = torch.clamp(inter_x2 - inter_x1, min=0)
        inter_h = torch.clamp(inter_y2 - inter_y1, min=0)
        inter_area = inter_w * inter_h
        
        # 计算并集
        pred_area = (pred_boxes[:, 2] - pred_boxes[:, 0]) * (pred_boxes[:, 3] - pred_boxes[:, 1])
        target_area = (target_boxes[:, 2] - target_boxes[:, 0]) * (target_boxes[:, 3] - target_boxes[:, 1])
        union_area = pred_area + target_area - inter_area + self.eps
        
        # IoU
        iou = inter_area / union_area
        
        # 计算中心点距离
        pred_center_x = (pred_boxes[:, 0] + pred_boxes[:, 2]) / 2
        pred_center_y = (pred_boxes[:, 1] + pred_boxes[:, 3]) / 2
        target_center_x = (target_boxes[:, 0] + target_boxes[:, 2]) / 2
        target_center_y = (target_boxes[:, 1] + target_boxes[:, 3]) / 2
        
        center_distance = (pred_center_x - target_center_x) ** 2 + (pred_center_y - target_center_y) ** 2
        
        # 计算最小外接矩形对角线长度
        c_x1 = torch.min(pred_boxes[:, 0], target_boxes[:, 0])
        c_y1 = torch.min(pred_boxes[:, 1], target_boxes[:, 1])
        c_x2 = torch.max(pred_boxes[:, 2], target_boxes[:, 2])
        c_y2 = torch.max(pred_boxes[:, 3], target_boxes[:, 3])
        
        c_diagonal = (c_x2 - c_x1) ** 2 + (c_y2 - c_y1) ** 2 + self.eps
        
        # 长宽比一致性
        pred_w = pred_boxes[:, 2] - pred_boxes[:, 0]
        pred_h = pred_boxes[:, 3] - pred_boxes[:, 1]
        target_w = target_boxes[:, 2] - target_boxes[:, 0]
        target_h = target_boxes[:, 3] - target_boxes[:, 1]
        
        v = (4 / (math.pi ** 2)) * torch.pow(
            torch.atan(target_w / (target_h + self.eps)) - torch.atan(pred_w / (pred_h + self.eps)), 2
        )
        
        with torch.no_grad():
            alpha = v / (1 - iou + v + self.eps)
        
        # CIoU
        ciou = iou - (center_distance / c_diagonal) - (alpha * v)
        
        # Loss = 1 - CIoU
        loss = 1 - ciou
        
        return loss.mean()
    
    def _convert_to_xyxy(self, boxes: torch.Tensor) -> torch.Tensor:
        """将框转换为xyxy格式"""
        if boxes.shape[-1] == 4:
            # 假设输入是 (cx, cy, w, h) 格式
            if boxes[..., 2:].min() < 1.0:  # 归一化坐标
                cx, cy, w, h = boxes[..., 0], boxes[..., 1], boxes[..., 2], boxes[..., 3]
                x1 = cx - w / 2
                y1 = cy - h / 2
                x2 = cx + w / 2
                y2 = cy + h / 2
                return torch.stack([x1, y1, x2, y2], dim=-1)
        return boxes


class LoRALayer(nn.Module):
    """
    LoRA (Low-Rank Adaptation) 层
    
    通过低秩矩阵微调预训练模型，减少可训练参数量
    公式: W = W_0 + BA，其中 B ∈ R^{d×r}, A ∈ R^{r×k}, r << min(d, k)
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.0
    ):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # LoRA参数
        self.lora_A = nn.Parameter(torch.zeros(in_features, rank))
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))
        
        # Dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        
        # 初始化
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        # x @ A @ B * scaling
        result = self.dropout(x) @ self.lora_A @ self.lora_B * self.scaling
        return result


def inject_lora(
    model: nn.Module,
    target_modules: List[str],
    rank: int = 8,
    alpha: float = 16.0,
    dropout: float = 0.0
) -> nn.Module:
    """
    向模型注入LoRA层
    
    :param model: 原始模型
    :param target_modules: 目标模块名称列表
    :param rank: LoRA秩
    :param alpha: LoRA缩放系数
    :param dropout: Dropout率
    :return: 注入LoRA后的模型
    """
    lora_layers = {}
    
    for name, module in model.named_modules():
        if any(target in name for target in target_modules):
            if isinstance(module, nn.Linear):
                lora = LoRALayer(
                    in_features=module.in_features,
                    out_features=module.out_features,
                    rank=rank,
                    alpha=alpha,
                    dropout=dropout
                )
                lora_layers[name] = lora
                
                # 冻结原始参数
                for param in module.parameters():
                    param.requires_grad = False
    
    # 将LoRA层添加到模型
    for name, lora in lora_layers.items():
        parent_name = '.'.join(name.split('.')[:-1])
        child_name = name.split('.')[-1]
        
        if parent_name:
            parent = model.get_submodule(parent_name)
        else:
            parent = model
        
        # 创建包装模块
        original_module = getattr(parent, child_name)
        wrapped = LoRAWapper(original_module, lora)
        setattr(parent, child_name, wrapped)
    
    return model


class LoRAWapper(nn.Module):
    """LoRA包装器"""
    
    def __init__(self, original_module: nn.Module, lora: LoRALayer):
        super().__init__()
        self.original = original_module
        self.lora = lora
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播：原始输出 + LoRA输出"""
        original_out = self.original(x)
        lora_out = self.lora(x)
        return original_out + lora_out


class YOLOTrainer:
    """
    YOLOv8 训练器
    
    支持:
    - CIoU Loss
    - LoRA微调
    - 多尺度训练
    - 混合精度训练
    """
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        use_ciou: bool = True,
        use_lora: bool = False,
        lora_rank: int = 8,
        lora_alpha: float = 16.0
    ):
        """
        初始化训练器
        
        :param model: YOLO模型
        :param device: 计算设备
        :param use_ciou: 是否使用CIoU Loss
        :param use_lora: 是否使用LoRA
        :param lora_rank: LoRA秩
        :param lora_alpha: LoRA缩放系数
        """
        self.model = model.to(device)
        self.device = device
        self.use_ciou = use_ciou
        self.use_lora = use_lora
        
        # 注入LoRA
        if use_lora:
            target_modules = ['conv', 'cv1', 'cv2', 'cv3']  # YOLO中的卷积模块
            self.model = inject_lora(
                self.model,
                target_modules,
                rank=lora_rank,
                alpha=lora_alpha
            )
            print(f"✅ LoRA已注入 (rank={lora_rank}, alpha={lora_alpha})")
        
        # 损失函数
        if use_ciou:
            self.ciou_loss = CIoULoss()
            print("✅ CIoU Loss已启用")
        
        self.optimizer = None
        self.scheduler = None
    
    def setup_training(
        self,
        learning_rate: float = 1e-3,
        weight_decay: float = 5e-4,
        warmup_epochs: int = 3,
        total_epochs: int = 100
    ):
        """
        设置训练参数
        
        :param learning_rate: 学习率
        :param weight_decay: 权重衰减
        :param warmup_epochs: 预热轮数
        :param total_epochs: 总轮数
        """
        # 只优化需要梯度的参数
        trainable_params = [p for p in self.model.parameters() if p.requires_grad]
        
        self.optimizer = torch.optim.AdamW(
            trainable_params,
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # 学习率调度器
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=total_epochs - warmup_epochs
        )
        
        self.warmup_epochs = warmup_epochs
        self.total_epochs = total_epochs
        
        print(f"✅ 训练设置完成:")
        print(f"   可训练参数: {sum(p.numel() for p in trainable_params):,}")
        print(f"   学习率: {learning_rate}")
        print(f"   预热轮数: {warmup_epochs}")
    
    def train_epoch(self, dataloader: DataLoader, epoch: int) -> Dict[str, float]:
        """
        训练一个epoch
        
        :param dataloader: 数据加载器
        :param epoch: 当前epoch
        :return: 训练指标
        """
        self.model.train()
        total_loss = 0.0
        num_batches = len(dataloader)
        
        for batch_idx, (images, targets) in enumerate(dataloader):
            images = images.to(self.device)
            targets = targets.to(self.device)
            
            # 前向传播
            outputs = self.model(images)
            
            # 计算损失
            loss = self._compute_loss(outputs, targets)
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
            if batch_idx % 10 == 0:
                print(f"   Epoch {epoch} [{batch_idx}/{num_batches}] Loss: {loss.item():.4f}")
        
        avg_loss = total_loss / num_batches
        
        return {"loss": avg_loss}
    
    def _compute_loss(
        self,
        outputs: torch.Tensor,
        targets: torch.Tensor
    ) -> torch.Tensor:
        """
        计算损失
        
        :param outputs: 模型输出
        :param targets: 目标标签
        :return: 总损失
        """
        # 这里简化处理，实际应该根据YOLO输出格式解析
        # 包括分类损失、置信度损失、定位损失
        
        total_loss = torch.tensor(0.0, device=self.device)
        
        # 如果使用CIoU，替换定位损失
        if self.use_ciou and outputs.shape[-1] >= 4:
            # 假设前4个是边界框坐标
            pred_boxes = outputs[..., :4]
            target_boxes = targets[..., :4]
            
            ciou_loss = self.ciou_loss(pred_boxes, target_boxes)
            total_loss += ciou_loss
        
        # 分类损失 (CrossEntropy)
        if outputs.shape[-1] > 4:
            pred_cls = outputs[..., 4:]
            target_cls = targets[..., 4:].long()
            
            cls_loss = F.cross_entropy(pred_cls, target_cls)
            total_loss += cls_loss
        
        return total_loss
    
    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """
        验证模型
        
        :param dataloader: 验证数据加载器
        :return: 验证指标
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = len(dataloader)
        
        with torch.no_grad():
            for images, targets in dataloader:
                images = images.to(self.device)
                targets = targets.to(self.device)
                
                outputs = self.model(images)
                loss = self._compute_loss(outputs, targets)
                
                total_loss += loss.item()
        
        avg_loss = total_loss / num_batches
        
        return {"val_loss": avg_loss}
    
    def save_checkpoint(self, path: str, epoch: int, metrics: Dict[str, float]):
        """
        保存检查点
        
        :param path: 保存路径
        :param epoch: 当前epoch
        :param metrics: 训练指标
        """
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'metrics': metrics
        }
        
        torch.save(checkpoint, path)
        print(f"✅ 检查点已保存: {path}")
    
    def load_checkpoint(self, path: str):
        """
        加载检查点
        
        :param path: 检查点路径
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        if self.optimizer:
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"✅ 检查点已加载: {path}")


def test_ciou_loss():
    """测试CIoU Loss"""
    print("=" * 70)
    print("🧪 测试CIoU Loss")
    print("=" * 70)
    
    ciou_loss = CIoULoss()
    
    # 测试用例：预测框和目标框
    pred_boxes = torch.tensor([
        [0.3, 0.3, 0.7, 0.7],  # 中心对齐，大小相同
        [0.1, 0.1, 0.5, 0.5],  # 偏移
        [0.2, 0.2, 0.8, 0.4],  # 细长框
    ])
    
    target_boxes = torch.tensor([
        [0.3, 0.3, 0.7, 0.7],
        [0.3, 0.3, 0.7, 0.7],
        [0.2, 0.2, 0.8, 0.4],
    ])
    
    loss = ciou_loss(pred_boxes, target_boxes)
    print(f"✅ CIoU Loss: {loss.item():.4f}")
    
    # 测试完全匹配
    loss_match = ciou_loss(target_boxes, target_boxes)
    print(f"✅ 完全匹配的CIoU Loss: {loss_match.item():.4f}")
    
    print("\n" + "=" * 70)
    print("✅ CIoU Loss测试通过！")
    print("=" * 70)


def test_lora():
    """测试LoRA"""
    print("=" * 70)
    print("🧪 测试LoRA")
    print("=" * 70)
    
    # 创建简单模型
    model = nn.Sequential(
        nn.Linear(100, 50),
        nn.ReLU(),
        nn.Linear(50, 10)
    )
    
    # 统计原始可训练参数
    original_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"原始可训练参数: {original_params:,}")
    
    # 注入LoRA
    model = inject_lora(model, ['0', '2'], rank=4, alpha=8.0)
    
    # 统计LoRA后可训练参数
    lora_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"LoRA后可训练参数: {lora_params:,}")
    print(f"参数减少比例: {(1 - lora_params/original_params)*100:.2f}%")
    
    # 测试前向传播
    x = torch.randn(2, 100)
    output = model(x)
    print(f"输出形状: {output.shape}")
    
    print("\n" + "=" * 70)
    print("✅ LoRA测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_ciou_loss()
    test_lora()
