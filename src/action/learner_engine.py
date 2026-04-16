# -*- coding: utf-8 -*-
"""
主动学习引擎模块

实现用户反馈收集、困难样本挖掘和增量学习功能
支持经验回放和知识蒸馏

文档参考：
- 7.1 增量学习与灾难性遗忘
- 7.1.1 经验回放
- 7.1.2 参数隔离与LoRA适配器
- 7.2 人机协同反馈闭环
"""
import os
import shutil
import datetime
import json
import random
from typing import Dict, Any, Optional, List, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image


class IncrementalLearningStrategy(Enum):
    """增量学习策略"""
    EXPERIENCE_REPLAY = "experience_replay"
    ICARL = "icarl"
    LWF = "lwf"
    EWC = "ewc"


@dataclass
class TrainingConfig:
    """训练配置"""
    learning_rate: float = 1e-4
    batch_size: int = 8
    epochs: int = 5
    weight_decay: float = 1e-5
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    rehearsal_ratio: float = 0.3
    confidence_threshold: float = 0.3
    distillation_temperature: float = 2.0
    distillation_alpha: float = 0.5


class FeedbackDataset(Dataset):
    """
    反馈数据集
    
    用于加载用户反馈的图像样本
    """
    
    def __init__(
        self,
        samples: List[Tuple[str, str, float]],
        label_to_idx: Dict[str, int],
        transform: Optional[transforms.Compose] = None,
        image_size: int = 224
    ):
        """
        初始化反馈数据集
        
        :param samples: 样本列表 [(image_path, label, confidence), ...]
        :param label_to_idx: 标签到索引的映射
        :param transform: 图像变换
        :param image_size: 图像大小
        """
        self.samples = samples
        self.label_to_idx = label_to_idx
        self.image_size = image_size
        
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        else:
            self.transform = transform
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, float]:
        image_path, label, confidence = self.samples[idx]
        
        try:
            image = Image.open(image_path).convert('RGB')
            image = self.transform(image)
        except Exception as e:
            print(f"⚠️ 加载图像失败 {image_path}: {e}")
            image = torch.zeros(3, self.image_size, self.image_size)
        
        label_idx = self.label_to_idx.get(label, 0)
        return image, label_idx, confidence


class ActiveLearner:
    """
    主动学习引擎
    
    功能:
    1. 收集用户反馈样本
    2. 困难样本挖掘 (Hard Sample Mining)
    3. 增量学习支持 (iCaRL, LwF, EWC)
    4. 经验回放管理
    5. 知识蒸馏
    
    文档参考:
    - 7.1 增量学习与灾难性遗忘
    - 7.2 人机协同反馈闭环
    """
    
    def __init__(
        self, 
        data_root: str = "datasets/feedback_data",
        replay_buffer_dir: str = "data/experience_replay",
        buffer_capacity: int = 1000,
        config: Optional[TrainingConfig] = None,
        device: str = 'cpu'
    ):
        """
        初始化主动学习引擎
        
        :param data_root: 反馈数据存储根目录
        :param replay_buffer_dir: 经验回放缓冲区目录
        :param buffer_capacity: 缓冲区容量
        :param config: 训练配置
        :param device: 计算设备
        """
        self.data_root = data_root
        self.replay_buffer_dir = replay_buffer_dir
        self.buffer_capacity = buffer_capacity
        self.config = config or TrainingConfig()
        self.device = device
        
        # 创建目录
        if not os.path.exists(self.data_root):
            os.makedirs(self.data_root)
        if not os.path.exists(self.replay_buffer_dir):
            os.makedirs(self.replay_buffer_dir)
        
        # 模型引用
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.criterion: Optional[nn.Module] = None
        
        # 旧模型用于知识蒸馏
        self.old_model: Optional[nn.Module] = None
        
        # 标签映射
        self.label_to_idx: Dict[str, int] = {}
        self.idx_to_label: Dict[int, str] = {}
        
        # 学习统计
        self.learning_stats = {
            "total_samples": 0,
            "hard_samples": 0,
            "incremental_steps": 0,
            "last_training_time": None,
            "training_history": []
        }
        
        # 经验回放缓冲区
        self.replay_buffer: List[Tuple[str, str, float]] = []
        
        # EWC参数存储
        self.ewc_params: Dict[str, torch.Tensor] = {}
        
        # 加载已有统计
        self._load_stats()
        
        print(f"🎓 [ActiveLearner] 主动学习引擎已就绪")
        print(f"   存储路径: {self.data_root}")
        print(f"   缓冲区容量: {self.buffer_capacity}")
        print(f"   排练比例: {self.config.rehearsal_ratio}")
    
    def collect_feedback(
        self, 
        image_path: str, 
        system_diagnosis: str, 
        confidence: float = 1.0,
        user_correction: Optional[str] = None, 
        comments: str = ""
    ) -> Dict[str, Any]:
        """
        收集用户反馈，构建困难样本库 (Hard Sample Mining)
        
        文档参考: 7.2 人机协同反馈闭环
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断结果
        :param confidence: 置信度
        :param user_correction: 用户修正结果
        :param comments: 用户评论
        :return: 收集结果
        """
        # 确定最终标签
        final_label = user_correction if user_correction else system_diagnosis
        
        # 更新标签映射
        if final_label not in self.label_to_idx:
            new_idx = len(self.label_to_idx)
            self.label_to_idx[final_label] = new_idx
            self.idx_to_label[new_idx] = final_label
        
        # 判断是否为困难样本
        is_hard_sample = confidence < self.config.confidence_threshold
        
        # 创建对应类别的文件夹
        save_dir = os.path.join(self.data_root, final_label)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 生成带时间戳的文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        
        # 标记：如果是修正过的或低置信度，加前缀
        if user_correction:
            prefix = f"err_{system_diagnosis}_corr_"
        elif is_hard_sample:
            prefix = "hard_"
        else:
            prefix = "confirmed_"
        
        new_filename = f"{timestamp}_{prefix}{final_label}{ext}"
        save_path = os.path.join(save_dir, new_filename)
        
        # 复制图片
        try:
            shutil.copy2(image_path, save_path)
            
            # 记录日志
            log_path = os.path.join(save_dir, "feedback_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                record = f"[{timestamp}] Image: {new_filename} | System: {system_diagnosis} | Final: {final_label} | Confidence: {confidence:.2f} | Comment: {comments}\n"
                f.write(record)
            
            # 更新统计
            self.learning_stats["total_samples"] += 1
            if is_hard_sample:
                self.learning_stats["hard_samples"] += 1
            
            # 添加到经验回放缓冲区
            self._add_to_replay_buffer(save_path, final_label, confidence)
            
            # 保存统计
            self._save_stats()
            
            print(f"💾 [主动学习] 样本已入库: {final_label}")
            print(f"   路径: {save_path}")
            print(f"   置信度: {confidence:.2f}")
            print(f"   困难样本: {'是' if is_hard_sample else '否'}")
            
            return {
                "success": True,
                "save_path": save_path,
                "final_label": final_label,
                "is_hard_sample": is_hard_sample,
                "message": f"样本已保存到 {save_path}"
            }
            
        except Exception as e:
            print(f"❌ 保存反馈数据失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"保存失败: {e}"
            }
    
    def set_model(
        self, 
        model: nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        criterion: Optional[nn.Module] = None
    ):
        """
        设置要训练的模型
        
        :param model: PyTorch模型
        :param optimizer: 优化器（可选，默认使用AdamW）
        :param criterion: 损失函数（可选，默认使用CrossEntropyLoss）
        """
        self.model = model.to(self.device)
        
        if optimizer is None:
            self.optimizer = torch.optim.AdamW(
                model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        else:
            self.optimizer = optimizer
        
        if criterion is None:
            self.criterion = nn.CrossEntropyLoss()
        else:
            self.criterion = criterion
        
        print(f"🔧 [主动学习] 模型已设置: {type(model).__name__}")
    
    def incremental_train_step(
        self,
        new_samples: List[Tuple[str, str, float]],
        strategy: IncrementalLearningStrategy = IncrementalLearningStrategy.EXPERIENCE_REPLAY,
        epochs: Optional[int] = None,
        callbacks: Optional[List[Callable]] = None
    ) -> Dict[str, Any]:
        """
        执行增量学习步骤
        
        文档参考: 7.1 增量学习与灾难性遗忘
        
        :param new_samples: 新样本列表 [(image_path, label, confidence), ...]
        :param strategy: 增量学习策略
        :param epochs: 训练轮数
        :param callbacks: 回调函数列表
        :return: 训练统计
        """
        if self.model is None:
            print("⚠️ [主动学习] 未设置模型，无法执行增量学习")
            return {"success": False, "error": "Model not set"}
        
        epochs = epochs or self.config.epochs
        
        print(f"\n🎓 [主动学习] 开始增量学习")
        print(f"   策略: {strategy.value}")
        print(f"   新样本数: {len(new_samples)}")
        print(f"   训练轮数: {epochs}")
        
        # 更新标签映射
        for _, label, _ in new_samples:
            if label not in self.label_to_idx:
                new_idx = len(self.label_to_idx)
                self.label_to_idx[label] = new_idx
                self.idx_to_label[new_idx] = label
        
        # 根据策略准备训练数据
        if strategy == IncrementalLearningStrategy.EXPERIENCE_REPLAY:
            all_samples = self._prepare_experience_replay(new_samples)
        elif strategy == IncrementalLearningStrategy.LWF:
            all_samples = self._prepare_lwf(new_samples)
        elif strategy == IncrementalLearningStrategy.EWC:
            all_samples = self._prepare_ewc(new_samples)
        else:
            all_samples = new_samples
        
        # 创建数据集和数据加载器
        dataset = FeedbackDataset(all_samples, self.label_to_idx)
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0,
            pin_memory=True
        )
        
        # 训练统计
        training_stats = {
            "success": True,
            "strategy": strategy.value,
            "total_samples": len(all_samples),
            "new_samples": len(new_samples),
            "rehearsal_samples": len(all_samples) - len(new_samples),
            "epochs": epochs,
            "batch_size": self.config.batch_size,
            "loss_history": [],
            "accuracy_history": [],
            "final_loss": 0.0,
            "final_accuracy": 0.0
        }
        
        # 训练循环
        try:
            self.model.train()
            
            global_step = 0
            total_loss = 0.0
            total_correct = 0
            total_samples = 0
            
            for epoch in range(epochs):
                epoch_loss = 0.0
                epoch_correct = 0
                epoch_samples = 0
                
                for batch_idx, (images, labels, confidences) in enumerate(dataloader):
                    images = images.to(self.device)
                    labels = labels.to(self.device)
                    
                    # 前向传播
                    self.optimizer.zero_grad()
                    outputs = self.model(images)
                    
                    # 计算损失
                    if isinstance(outputs, tuple):
                        logits = outputs[0]
                    else:
                        logits = outputs
                    
                    # 分类损失
                    cls_loss = self.criterion(logits, labels)
                    
                    # 根据策略添加额外损失
                    total_batch_loss = cls_loss
                    
                    if strategy == IncrementalLearningStrategy.LWF and self.old_model is not None:
                        distill_loss = self._compute_distillation_loss(images, logits)
                        total_batch_loss = (1 - self.config.distillation_alpha) * cls_loss + \
                                          self.config.distillation_alpha * distill_loss
                    
                    elif strategy == IncrementalLearningStrategy.EWC and self.ewc_params:
                        ewc_loss = self._compute_ewc_loss()
                        total_batch_loss = cls_loss + 0.1 * ewc_loss
                    
                    # 反向传播
                    total_batch_loss.backward()
                    
                    # 梯度裁剪
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.max_grad_norm
                    )
                    
                    self.optimizer.step()
                    
                    # 统计
                    batch_loss = total_batch_loss.item()
                    epoch_loss += batch_loss
                    total_loss += batch_loss
                    
                    _, predicted = torch.max(logits, 1)
                    correct = (predicted == labels).sum().item()
                    epoch_correct += correct
                    total_correct += correct
                    epoch_samples += labels.size(0)
                    total_samples += labels.size(0)
                    
                    global_step += 1
                    
                    # 回调
                    if callbacks:
                        for callback in callbacks:
                            callback(epoch, batch_idx, batch_loss, correct / labels.size(0))
                
                # Epoch统计
                avg_epoch_loss = epoch_loss / len(dataloader)
                epoch_accuracy = epoch_correct / epoch_samples if epoch_samples > 0 else 0
                
                training_stats["loss_history"].append(avg_epoch_loss)
                training_stats["accuracy_history"].append(epoch_accuracy)
                
                print(f"   Epoch {epoch+1}/{epochs}, Loss: {avg_epoch_loss:.4f}, Acc: {epoch_accuracy:.4f}")
            
            # 最终统计
            training_stats["final_loss"] = total_loss / (epochs * len(dataloader))
            training_stats["final_accuracy"] = total_correct / total_samples if total_samples > 0 else 0
            
            # 更新学习统计
            self.learning_stats["incremental_steps"] += 1
            self.learning_stats["last_training_time"] = datetime.datetime.now().isoformat()
            self.learning_stats["training_history"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "strategy": strategy.value,
                "samples": len(all_samples),
                "epochs": epochs,
                "final_loss": training_stats["final_loss"],
                "final_accuracy": training_stats["final_accuracy"]
            })
            self._save_stats()
            
            # 保存旧模型用于知识蒸馏
            if strategy in [IncrementalLearningStrategy.LWF, IncrementalLearningStrategy.EWC]:
                self.old_model = type(self.model)(**self.model.config) if hasattr(self.model, 'config') else None
                if self.old_model:
                    self.old_model.load_state_dict(self.model.state_dict())
                    self.old_model.eval()
            
            print(f"✅ [主动学习] 增量学习完成")
            print(f"   平均损失: {training_stats['final_loss']:.4f}")
            print(f"   准确率: {training_stats['final_accuracy']:.4f}")
            
        except Exception as e:
            training_stats["success"] = False
            training_stats["error"] = str(e)
            print(f"❌ [主动学习] 增量学习失败: {e}")
            import traceback
            traceback.print_exc()
        
        return training_stats
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        获取学习统计信息
        
        :return: 统计信息字典
        """
        stats = self.learning_stats.copy()
        stats["buffer_size"] = len(self.replay_buffer)
        stats["buffer_capacity"] = self.buffer_capacity
        stats["data_root"] = self.data_root
        stats["num_classes"] = len(self.label_to_idx)
        stats["classes"] = list(self.label_to_idx.keys())
        return stats
    
    def get_uncertain_samples(
        self,
        threshold: Optional[float] = None
    ) -> List[Tuple[str, str, float]]:
        """
        获取不确定性样本（低置信度样本）
        
        文档参考: 7.2 人机协同反馈闭环 - 不确定性预警
        
        :param threshold: 置信度阈值
        :return: 不确定性样本列表
        """
        threshold = threshold or self.config.confidence_threshold
        uncertain_samples = [
            (path, label, conf) 
            for path, label, conf in self.replay_buffer 
            if conf < threshold
        ]
        return uncertain_samples
    
    def _prepare_experience_replay(
        self, 
        new_samples: List[Tuple[str, str, float]]
    ) -> List[Tuple[str, str, float]]:
        """
        准备经验回放训练数据
        
        :param new_samples: 新样本
        :return: 混合后的训练数据
        """
        num_rehearsal = int(len(new_samples) * self.config.rehearsal_ratio)
        rehearsal_samples = self._get_rehearsal_samples(num_rehearsal)
        return new_samples + rehearsal_samples
    
    def _prepare_lwf(
        self, 
        new_samples: List[Tuple[str, str, float]]
    ) -> List[Tuple[str, str, float]]:
        """
        准备LwF (Learning without Forgetting) 训练数据
        
        :param new_samples: 新样本
        :return: 训练数据
        """
        return self._prepare_experience_replay(new_samples)
    
    def _prepare_ewc(
        self, 
        new_samples: List[Tuple[str, str, float]]
    ) -> List[Tuple[str, str, float]]:
        """
        准备EWC (Elastic Weight Consolidation) 训练数据
        
        :param new_samples: 新样本
        :return: 训练数据
        """
        # 计算Fisher信息矩阵（如果还没有）
        if not self.ewc_params and self.model is not None:
            self._compute_fisher_information()
        
        return self._prepare_experience_replay(new_samples)
    
    def _compute_distillation_loss(
        self, 
        images: torch.Tensor, 
        new_logits: torch.Tensor
    ) -> torch.Tensor:
        """
        计算知识蒸馏损失
        
        :param images: 输入图像
        :param new_logits: 新模型输出
        :return: 蒸馏损失
        """
        if self.old_model is None:
            return torch.tensor(0.0, device=self.device)
        
        with torch.no_grad():
            old_outputs = self.old_model(images)
            if isinstance(old_outputs, tuple):
                old_logits = old_outputs[0]
            else:
                old_logits = old_outputs
        
        # KL散度损失
        T = self.config.distillation_temperature
        loss = F.kl_div(
            F.log_softmax(new_logits / T, dim=1),
            F.softmax(old_logits / T, dim=1),
            reduction='batchmean'
        ) * (T * T)
        
        return loss
    
    def _compute_fisher_information(self):
        """
        计算Fisher信息矩阵用于EWC
        """
        if not self.replay_buffer:
            return
        
        print("📊 [EWC] 计算Fisher信息矩阵...")
        
        self.model.eval()
        fisher = {n: torch.zeros_like(p) for n, p in self.model.named_parameters()}
        
        # 使用回放缓冲区中的样本
        samples = self._get_rehearsal_samples(min(100, len(self.replay_buffer)))
        dataset = FeedbackDataset(samples, self.label_to_idx)
        dataloader = DataLoader(dataset, batch_size=self.config.batch_size, shuffle=False)
        
        for images, labels, _ in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)
            
            self.model.zero_grad()
            outputs = self.model(images)
            if isinstance(outputs, tuple):
                outputs = outputs[0]
            
            log_probs = F.log_softmax(outputs, dim=1)
            probs = F.softmax(outputs, dim=1)
            
            for i in range(len(labels)):
                label = labels[i]
                log_prob = log_probs[i, label]
                prob = probs[i, label]
                log_prob.backward(retain_graph=True)
                
                for n, p in self.model.named_parameters():
                    if p.grad is not None:
                        fisher[n] += prob.item() * p.grad.data ** 2
        
        # 归一化
        for n in fisher:
            fisher[n] /= len(dataset)
        
        self.ewc_params = fisher
        print("✅ [EWC] Fisher信息矩阵计算完成")
    
    def _compute_ewc_loss(self) -> torch.Tensor:
        """
        计算EWC正则化损失
        
        :return: EWC损失
        """
        if not self.ewc_params:
            return torch.tensor(0.0, device=self.device)
        
        loss = torch.tensor(0.0, device=self.device)
        for n, p in self.model.named_parameters():
            if n in self.ewc_params:
                loss += (self.ewc_params[n] * (p - p.data) ** 2).sum()
        
        return loss
    
    def _add_to_replay_buffer(self, image_path: str, label: str, confidence: float):
        """
        添加样本到经验回放缓冲区
        
        :param image_path: 图像路径
        :param label: 标签
        :param confidence: 置信度
        """
        self.replay_buffer.append((image_path, label, confidence))
        
        # 如果超出容量，移除置信度最高的样本（保留困难样本）
        if len(self.replay_buffer) > self.buffer_capacity:
            # 按置信度排序，移除高置信度样本
            self.replay_buffer.sort(key=lambda x: x[2], reverse=True)
            self.replay_buffer.pop(0)
    
    def _get_rehearsal_samples(self, num_samples: int) -> List[Tuple[str, str, float]]:
        """
        从经验回放缓冲区获取排练样本
        
        :param num_samples: 需要的样本数
        :return: 样本列表
        """
        if not self.replay_buffer:
            return []
        
        # 优先选择低置信度样本（困难样本）
        sorted_buffer = sorted(self.replay_buffer, key=lambda x: x[2])
        num_samples = min(num_samples, len(sorted_buffer))
        return sorted_buffer[:num_samples]
    
    def _save_stats(self):
        """保存学习统计到文件"""
        stats_path = os.path.join(self.data_root, "learning_stats.json")
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.learning_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存学习统计失败: {e}")
    
    def _load_stats(self):
        """从文件加载学习统计"""
        stats_path = os.path.join(self.data_root, "learning_stats.json")
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r', encoding='utf-8') as f:
                    loaded_stats = json.load(f)
                    self.learning_stats.update(loaded_stats)
            except Exception as e:
                print(f"⚠️ 加载学习统计失败: {e}")
        
        # 加载标签映射
        label_path = os.path.join(self.data_root, "label_mapping.json")
        if os.path.exists(label_path):
            try:
                with open(label_path, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                    self.label_to_idx = mapping.get("label_to_idx", {})
                    self.idx_to_label = {int(k): v for k, v in mapping.get("idx_to_label", {}).items()}
            except Exception as e:
                print(f"⚠️ 加载标签映射失败: {e}")
    
    def save_label_mapping(self):
        """保存标签映射"""
        label_path = os.path.join(self.data_root, "label_mapping.json")
        try:
            with open(label_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "label_to_idx": self.label_to_idx,
                    "idx_to_label": self.idx_to_label
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存标签映射失败: {e}")


# 别名，保持向后兼容
EnhancedActiveLearner = ActiveLearner
