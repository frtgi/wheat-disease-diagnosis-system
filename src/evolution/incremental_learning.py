# -*- coding: utf-8 -*-
"""
类增量学习算法实现

根据文档第7章：自进化机制 - 增量学习与反馈闭环
实现防止灾难性遗忘的类增量学习算法

算法：
1. iCaRL (Incremental Classifier and Representation Learning)
2. LwF (Learning without Forgetting)
3. EWC (Elastic Weight Consolidation)
4. 知识蒸馏损失
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from collections import defaultdict
import copy


@dataclass
class IncrementalConfig:
    """增量学习配置"""
    num_classes: int = 10
    embedding_dim: int = 512
    memory_size: int = 2000
    temperature: float = 2.0
    ewc_lambda: float = 1000.0
    lwf_alpha: float = 1.0
    distillation_alpha: float = 1.0


class ExemplarMemory:
    """
    样本记忆库
    
    存储每个类别的代表性样本，用于增量学习时的复习
    """
    
    def __init__(self, memory_size: int = 2000):
        """
        初始化样本记忆库
        
        Args:
            memory_size: 总记忆容量
        """
        self.memory_size = memory_size
        self.exemplars: Dict[int, List[torch.Tensor]] = defaultdict(list)
        self.class_means: Dict[int, torch.Tensor] = {}
    
    def update_exemplars(
        self,
        features: torch.Tensor,
        labels: torch.Tensor,
        class_ids: List[int]
    ):
        """
        更新样本记忆
        
        Args:
            features: 特征向量 [N, D]
            labels: 标签 [N]
            class_ids: 新增类别列表
        """
        num_classes = len(self.exemplars) + len(class_ids)
        per_class = self.memory_size // num_classes
        
        # 压缩旧类别的样本
        for cls in self.exemplars:
            if len(self.exemplars[cls]) > per_class:
                self.exemplars[cls] = self.exemplars[cls][:per_class]
        
        # 为新类别选择样本
        for cls in class_ids:
            mask = labels == cls
            cls_features = features[mask]
            
            if len(cls_features) > 0:
                # 计算类均值
                class_mean = cls_features.mean(dim=0)
                self.class_means[cls] = class_mean
                
                # 选择最接近类均值的样本
                distances = torch.norm(cls_features - class_mean.unsqueeze(0), dim=1)
                _, indices = torch.sort(distances)
                
                selected = indices[:per_class]
                self.exemplars[cls] = [cls_features[i] for i in selected]
    
    def get_all_exemplars(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        获取所有记忆样本
        
        Returns:
            features: 特征向量
            labels: 标签
        """
        features = []
        labels = []
        
        for cls, exemplars in self.exemplars.items():
            features.extend(exemplars)
            labels.extend([cls] * len(exemplars))
        
        if features:
            features = torch.stack(features)
            labels = torch.tensor(labels)
        
        return features, labels
    
    def get_class_mean(self, class_id: int) -> Optional[torch.Tensor]:
        """获取类均值"""
        return self.class_means.get(class_id)


class iCaRL(nn.Module):
    """
    iCaRL: Incremental Classifier and Representation Learning
    
    核心思想：
    1. 使用样本记忆库存储代表性样本
    2. 使用知识蒸馏损失保持旧知识
    3. 使用最近类均值分类器
    
    论文: iCaRL: Incremental Classifier and Representation Learning
    """
    
    def __init__(self, config: IncrementalConfig):
        """
        初始化iCaRL
        
        Args:
            config: 增量学习配置
        """
        super().__init__()
        
        self.config = config
        self.num_classes = config.num_classes
        self.embedding_dim = config.embedding_dim
        
        # 特征提取器
        self.feature_extractor = nn.Sequential(
            nn.Linear(config.embedding_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        
        # 分类器
        self.classifier = nn.Linear(256, config.num_classes)
        
        # 样本记忆库
        self.exemplar_memory = ExemplarMemory(config.memory_size)
        
        # 已学习的类别
        self.learned_classes: List[int] = []
        
        # 旧模型（用于蒸馏）
        self.old_model = None
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入特征
        
        Returns:
            分类 logits
        """
        features = self.feature_extractor(x)
        logits = self.classifier(features)
        return logits
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """提取特征"""
        return self.feature_extractor(x)
    
    def compute_loss(
        self,
        features: torch.Tensor,
        labels: torch.Tensor,
        new_classes: List[int]
    ) -> Tuple[torch.Tensor, Dict]:
        """
        计算iCaRL损失
        
        Args:
            features: 输入特征
            labels: 标签
            new_classes: 新增类别
        
        Returns:
            总损失和损失字典
        """
        # 分类损失
        logits = self.forward(features)
        classification_loss = F.cross_entropy(logits, labels)
        
        # 知识蒸馏损失
        distillation_loss = torch.tensor(0.0)
        if self.old_model is not None and len(self.learned_classes) > 0:
            with torch.no_grad():
                old_logits = self.old_model(features)
            
            # 只对旧类别计算蒸馏损失
            old_classes_mask = [i for i in range(logits.size(1)) if i not in new_classes]
            if old_classes_mask:
                distillation_loss = self._distillation_loss(
                    logits[:, old_classes_mask],
                    old_logits[:, old_classes_mask]
                )
        
        # 总损失
        total_loss = (
            classification_loss +
            self.config.distillation_alpha * distillation_loss
        )
        
        loss_dict = {
            'classification_loss': classification_loss.item(),
            'distillation_loss': distillation_loss.item() if isinstance(distillation_loss, torch.Tensor) else distillation_loss,
            'total_loss': total_loss.item()
        }
        
        return total_loss, loss_dict
    
    def _distillation_loss(
        self,
        new_logits: torch.Tensor,
        old_logits: torch.Tensor
    ) -> torch.Tensor:
        """
        计算知识蒸馏损失
        
        Args:
            new_logits: 新模型输出
            old_logits: 旧模型输出
        
        Returns:
            蒸馏损失
        """
        T = self.config.temperature
        
        new_log_probs = F.log_softmax(new_logits / T, dim=1)
        old_probs = F.softmax(old_logits / T, dim=1)
        
        loss = F.kl_div(new_log_probs, old_probs, reduction='batchmean')
        
        return loss * (T ** 2)
    
    def before_incremental_learning(self, new_classes: List[int]):
        """
        增量学习前的准备工作
        
        Args:
            new_classes: 新增类别
        """
        # 保存旧模型
        self.old_model = copy.deepcopy(self)
        self.old_model.eval()
        
        # 更新已学习类别
        self.learned_classes.extend(new_classes)
    
    def after_incremental_learning(
        self,
        features: torch.Tensor,
        labels: torch.Tensor,
        new_classes: List[int]
    ):
        """
        增量学习后的更新工作
        
        Args:
            features: 特征向量
            labels: 标签
            new_classes: 新增类别
        """
        # 更新样本记忆库
        extracted_features = self.extract_features(features)
        self.exemplar_memory.update_exemplars(extracted_features.detach(), labels, new_classes)
    
    def classify_with_exemplars(self, x: torch.Tensor) -> torch.Tensor:
        """
        使用样本记忆库进行分类
        
        Args:
            x: 输入特征
        
        Returns:
            预测类别
        """
        features = self.extract_features(x)
        
        # 计算与每个类均值的距离
        predictions = []
        for i in range(len(features)):
            min_dist = float('inf')
            pred_class = -1
            
            for cls, mean in self.exemplar_memory.class_means.items():
                dist = torch.norm(features[i] - mean)
                if dist < min_dist:
                    min_dist = dist
                    pred_class = cls
            
            predictions.append(pred_class)
        
        return torch.tensor(predictions)


class LwF(nn.Module):
    """
    LwF: Learning without Forgetting
    
    核心思想：
    1. 不使用样本记忆库
    2. 使用知识蒸馏保持旧任务的输出分布
    3. 新任务学习时约束旧任务输出的变化
    
    论文: Learning without Forgetting
    """
    
    def __init__(self, config: IncrementalConfig):
        """
        初始化LwF
        
        Args:
            config: 增量学习配置
        """
        super().__init__()
        
        self.config = config
        self.temperature = config.temperature
        self.alpha = config.lwf_alpha
        
        # 共享特征提取器
        self.shared_features = nn.Sequential(
            nn.Linear(config.embedding_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        
        # 旧任务分类器
        self.old_classifier = None
        
        # 新任务分类器
        self.new_classifier = nn.Linear(256, config.num_classes)
        
        # 已学习类别数
        self.old_num_classes = 0
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        features = self.shared_features(x)
        return self.new_classifier(features)
    
    def compute_loss(
        self,
        features: torch.Tensor,
        labels: torch.Tensor,
        new_classes: List[int]
    ) -> Tuple[torch.Tensor, Dict]:
        """
        计算LwF损失
        
        Args:
            features: 输入特征
            labels: 标签
            new_classes: 新增类别
        
        Returns:
            总损失和损失字典
        """
        # 新任务损失
        new_logits = self.forward(features)
        new_loss = F.cross_entropy(new_logits, labels)
        
        # 旧任务蒸馏损失
        old_loss = torch.tensor(0.0)
        if self.old_classifier is not None:
            with torch.no_grad():
                old_logits = self.old_classifier(self.shared_features(features))
            
            current_old_logits = new_logits[:, :self.old_num_classes]
            old_loss = self._distillation_loss(current_old_logits, old_logits)
        
        # 总损失
        total_loss = new_loss + self.alpha * old_loss
        
        loss_dict = {
            'new_task_loss': new_loss.item(),
            'old_task_distillation_loss': old_loss.item() if isinstance(old_loss, torch.Tensor) else old_loss,
            'total_loss': total_loss.item()
        }
        
        return total_loss, loss_dict
    
    def _distillation_loss(
        self,
        new_logits: torch.Tensor,
        old_logits: torch.Tensor
    ) -> torch.Tensor:
        """计算蒸馏损失"""
        T = self.temperature
        
        new_log_probs = F.log_softmax(new_logits / T, dim=1)
        old_probs = F.softmax(old_logits / T, dim=1)
        
        return F.kl_div(new_log_probs, old_probs, reduction='batchmean') * (T ** 2)
    
    def before_incremental_learning(self, new_num_classes: int):
        """
        增量学习前保存旧分类器
        
        Args:
            new_num_classes: 新的总类别数
        """
        # 保存旧分类器
        self.old_classifier = copy.deepcopy(self.new_classifier)
        self.old_classifier.eval()
        
        # 更新分类器
        self.old_num_classes = self.new_classifier.out_features
        self.new_classifier = nn.Linear(256, new_num_classes)


class EWC:
    """
    EWC: Elastic Weight Consolidation
    
    核心思想：
    1. 计算参数对旧任务的重要性（Fisher信息矩阵）
    2. 约束重要参数的变化
    3. 二次惩罚项
    
    论文: Overcoming catastrophic forgetting in neural networks
    """
    
    def __init__(self, model: nn.Module, config: IncrementalConfig):
        """
        初始化EWC
        
        Args:
            model: 神经网络模型
            config: 增量学习配置
        """
        self.model = model
        self.config = config
        self.lambda_ewc = config.ewc_lambda
        
        # Fisher信息矩阵
        self.fisher_info: Dict[str, torch.Tensor] = {}
        
        # 最优参数
        self.optimal_params: Dict[str, torch.Tensor] = {}
    
    def compute_fisher_info(
        self,
        dataloader,
        criterion,
        device: str = 'cpu'
    ):
        """
        计算Fisher信息矩阵
        
        Args:
            dataloader: 数据加载器
            criterion: 损失函数
            device: 设备
        """
        self.model.eval()
        
        # 初始化Fisher信息
        for name, param in self.model.named_parameters():
            self.fisher_info[name] = torch.zeros_like(param)
        
        # 计算Fisher信息
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)
            
            self.model.zero_grad()
            
            output = self.model(data)
            loss = criterion(output, target)
            loss.backward()
            
            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    self.fisher_info[name] += param.grad.data.pow(2)
        
        # 归一化
        for name in self.fisher_info:
            self.fisher_info[name] /= len(dataloader)
        
        # 保存最优参数
        for name, param in self.model.named_parameters():
            self.optimal_params[name] = param.data.clone()
    
    def ewc_loss(self) -> torch.Tensor:
        """
        计算EWC正则化损失
        
        Returns:
            EWC损失
        """
        loss = 0.0
        
        for name, param in self.model.named_parameters():
            if name in self.fisher_info:
                fisher = self.fisher_info[name]
                optimal = self.optimal_params[name]
                
                loss += (fisher * (param - optimal).pow(2)).sum()
        
        return self.lambda_ewc * loss
    
    def compute_total_loss(
        self,
        criterion,
        output: torch.Tensor,
        target: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict]:
        """
        计算总损失（任务损失 + EWC损失）
        
        Args:
            criterion: 任务损失函数
            output: 模型输出
            target: 目标
        
        Returns:
            总损失和损失字典
        """
        task_loss = criterion(output, target)
        ewc_loss = self.ewc_loss()
        
        total_loss = task_loss + ewc_loss
        
        loss_dict = {
            'task_loss': task_loss.item(),
            'ewc_loss': ewc_loss.item(),
            'total_loss': total_loss.item()
        }
        
        return total_loss, loss_dict


class IncrementalLearner:
    """
    增量学习管理器
    
    整合多种增量学习算法
    """
    
    def __init__(
        self,
        model: nn.Module,
        config: IncrementalConfig,
        method: str = 'icarl'
    ):
        """
        初始化增量学习管理器
        
        Args:
            model: 基础模型
            config: 配置
            method: 方法 ('icarl', 'lwf', 'ewc')
        """
        self.config = config
        self.method = method
        
        if method == 'icarl':
            self.learner = iCaRL(config)
        elif method == 'lwf':
            self.learner = LwF(config)
        elif method == 'ewc':
            self.learner = EWC(model, config)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def learn_new_classes(
        self,
        features: torch.Tensor,
        labels: torch.Tensor,
        new_classes: List[int]
    ) -> Dict:
        """
        学习新类别
        
        Args:
            features: 特征向量
            labels: 标签
            new_classes: 新类别列表
        
        Returns:
            训练结果
        """
        if self.method == 'icarl':
            self.learner.before_incremental_learning(new_classes)
            loss, loss_dict = self.learner.compute_loss(features, labels, new_classes)
            self.learner.after_incremental_learning(features, labels, new_classes)
        elif self.method == 'lwf':
            new_num_classes = max(new_classes) + 1
            self.learner.before_incremental_learning(new_num_classes)
            loss, loss_dict = self.learner.compute_loss(features, labels, new_classes)
        else:
            loss_dict = {'message': 'EWC requires separate training loop'}
        
        return loss_dict


def demo_incremental_learning():
    """演示增量学习"""
    print("=" * 70)
    print("📊 类增量学习算法演示")
    print("=" * 70)
    
    # 配置
    config = IncrementalConfig(
        num_classes=10,
        embedding_dim=512,
        memory_size=200
    )
    
    # 模拟数据
    torch.manual_seed(42)
    
    # 初始类别 (0-4)
    initial_features = torch.randn(100, 512)
    initial_labels = torch.randint(0, 5, (100,))
    
    # 新类别 (5-9)
    new_features = torch.randn(50, 512)
    new_labels = torch.randint(5, 10, (50,))
    
    print("\n📊 iCaRL 演示:")
    print("-" * 50)
    
    icarl = iCaRL(config)
    
    # 初始训练
    print("初始训练 (类别 0-4)...")
    loss, loss_dict = icarl.compute_loss(initial_features, initial_labels, list(range(5)))
    print(f"损失: {loss_dict}")
    
    # 增量学习
    print("\n增量学习 (类别 5-9)...")
    icarl.before_incremental_learning(list(range(5, 10)))
    loss, loss_dict = icarl.compute_loss(new_features, new_labels, list(range(5, 10)))
    print(f"损失: {loss_dict}")
    
    print("\n📊 LwF 演示:")
    print("-" * 50)
    
    lwf = LwF(config)
    
    # 初始训练
    print("初始训练 (类别 0-4)...")
    loss, loss_dict = lwf.compute_loss(initial_features, initial_labels, list(range(5)))
    print(f"损失: {loss_dict}")
    
    # 增量学习
    print("\n增量学习 (类别 5-9)...")
    lwf.before_incremental_learning(10)
    loss, loss_dict = lwf.compute_loss(new_features, new_labels, list(range(5, 10)))
    print(f"损失: {loss_dict}")
    
    print("\n📊 EWC 演示:")
    print("-" * 50)
    
    # 创建简单模型
    model = nn.Sequential(
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Linear(256, 10)
    )
    
    ewc = EWC(model, config)
    
    print("EWC需要在外部训练循环中计算Fisher信息矩阵")
    print(f"EWC Lambda: {ewc.lambda_ewc}")
    
    print("\n" + "=" * 70)
    print("✅ 类增量学习算法演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_incremental_learning()
