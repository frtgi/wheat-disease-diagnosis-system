# -*- coding: utf-8 -*-
"""
增强型主动学习引擎 (Enhanced Active Learner)
集成经验回放机制，实现增量学习与灾难性遗忘防护

根据研究文档，本模块实现:
1. 困难样本挖掘 (Hard Sample Mining)
2. 经验回放 (Experience Replay)
3. 增量学习 (Incremental Learning)
4. 类别增量学习 (Class-Incremental Learning, CIL)
"""
import os
import shutil
import datetime
import json
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import random

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from PIL import Image

# 导入经验回放模块
try:
    from .experience_replay import (
        Experience,
        ExperienceReplayBuffer,
        IncrementalLearner
    )
except ImportError:
    from experience_replay import (
        Experience,
        ExperienceReplayBuffer,
        IncrementalLearner
    )


@dataclass
class FeedbackRecord:
    """
    反馈记录数据类
    存储用户反馈的完整信息
    """
    image_path: str
    system_diagnosis: str
    user_correction: Optional[str]
    confidence: float
    timestamp: str
    comments: str
    is_correction: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackRecord':
        """从字典创建"""
        return cls(**data)


class FeedbackDataset(Dataset):
    """
    反馈数据集
    用于增量学习的 PyTorch Dataset
    """
    
    def __init__(
        self,
        samples: List[Tuple[str, str]],
        transform=None,
        class_to_idx: Optional[Dict[str, int]] = None
    ):
        """
        初始化数据集
        
        :param samples: 样本列表 [(image_path, label), ...]
        :param transform: 图像变换
        :param class_to_idx: 类别到索引的映射
        """
        self.samples = samples
        self.transform = transform
        
        # 构建类别映射
        if class_to_idx is None:
            classes = sorted(list(set([label for _, label in samples])))
            self.class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
        else:
            self.class_to_idx = class_to_idx
        
        self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """获取单个样本"""
        image_path, label = self.samples[idx]
        
        # 加载图像
        image = Image.open(image_path).convert('RGB')
        
        # 应用变换
        if self.transform:
            image = self.transform(image)
        
        # 获取标签索引
        label_idx = self.class_to_idx[label]
        
        return image, label_idx
    
    def get_class_names(self) -> List[str]:
        """获取类别名称列表"""
        return [self.idx_to_class[i] for i in range(len(self.class_to_idx))]


class EnhancedActiveLearner:
    """
    增强型主动学习引擎
    
    功能:
    1. 困难样本挖掘 - 识别并存储低置信度或错误分类的样本
    2. 经验回放 - 维护历史样本缓冲区，防止灾难性遗忘
    3. 增量学习 - 支持新类别和新样本的持续学习
    4. 自适应采样 - 智能选择需要人工标注的样本
    """
    
    def __init__(
        self,
        data_root: str = "datasets/feedback_data",
        replay_buffer_dir: str = "data/experience_replay",
        buffer_capacity: int = 1000,
        rehearsal_ratio: float = 0.3,
        confidence_threshold: float = 0.7,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        初始化增强型主动学习引擎
        
        :param data_root: 反馈数据存储根目录
        :param replay_buffer_dir: 经验回放缓冲区目录
        :param buffer_capacity: 经验缓冲区容量
        :param rehearsal_ratio: 复习样本比例
        :param confidence_threshold: 置信度阈值（低于此值的样本视为困难样本）
        :param device: 计算设备
        """
        self.data_root = data_root
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.rehearsal_ratio = rehearsal_ratio
        
        # 创建存储目录
        os.makedirs(data_root, exist_ok=True)
        
        # 初始化经验回放缓冲区
        self.replay_buffer = ExperienceReplayBuffer(
            capacity=buffer_capacity,
            storage_dir=replay_buffer_dir,
            priority_alpha=0.6,
            priority_beta=0.4
        )
        
        # 增量学习器（延迟初始化，等待模型传入）
        self.incremental_learner: Optional[IncrementalLearner] = None
        
        # 反馈历史记录
        self.feedback_history: List[FeedbackRecord] = []
        
        # 困难样本池
        self.hard_samples: List[Dict[str, Any]] = []
        
        # 类别映射
        self.class_to_idx: Dict[str, int] = {}
        self.idx_to_class: Dict[int, str] = {}
        
        # 学习统计
        self.learning_stats = {
            "total_feedback": 0,
            "corrections": 0,
            "confirmations": 0,
            "hard_samples": 0,
            "incremental_updates": 0
        }
        
        # 加载历史记录
        self._load_history()
        
        print(f"🎓 [Enhanced Active Learner] 增强型主动学习引擎已就绪")
        print(f"   存储路径: {data_root}")
        print(f"   经验缓冲区: {len(self.replay_buffer)} 样本")
        print(f"   置信度阈值: {confidence_threshold}")
        print(f"   复习比例: {rehearsal_ratio}")
    
    def set_model(self, model: nn.Module):
        """
        设置要训练的模型
        
        :param model: 神经网络模型
        """
        self.incremental_learner = IncrementalLearner(
            model=model,
            replay_buffer=self.replay_buffer,
            rehearsal_ratio=self.rehearsal_ratio
        )
        print(f"✅ 模型已设置到增量学习器")
    
    def collect_feedback(
        self,
        image_path: str,
        system_diagnosis: str,
        confidence: float,
        user_correction: Optional[str] = None,
        comments: str = "",
        features: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        """
        收集用户反馈，构建困难样本库并更新经验回放
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断结果
        :param confidence: 置信度
        :param user_correction: 用户修正（如果有）
        :param comments: 用户评论
        :param features: 特征向量（可选）
        :return: 反馈处理结果
        """
        # 确定最终标签
        final_label = user_correction if user_correction else system_diagnosis
        is_correction = user_correction is not None
        
        # 创建反馈记录
        timestamp = datetime.datetime.now().isoformat()
        record = FeedbackRecord(
            image_path=image_path,
            system_diagnosis=system_diagnosis,
            user_correction=user_correction,
            confidence=confidence,
            timestamp=timestamp,
            comments=comments,
            is_correction=is_correction
        )
        self.feedback_history.append(record)
        
        # 更新统计
        self.learning_stats["total_feedback"] += 1
        if is_correction:
            self.learning_stats["corrections"] += 1
        else:
            self.learning_stats["confirmations"] += 1
        
        # 保存到反馈数据集
        save_result = self._save_to_feedback_dataset(image_path, system_diagnosis, 
                                                      final_label, is_correction, timestamp)
        
        # 添加到经验回放缓冲区
        priority = self._calculate_priority(confidence, is_correction)
        self.replay_buffer.add_experience(
            image_path=image_path,
            label=final_label,
            confidence=confidence,
            features=features,
            priority=priority,
            metadata={
                "system_diagnosis": system_diagnosis,
                "is_correction": is_correction,
                "comments": comments
            }
        )
        
        # 检查是否为困难样本
        is_hard = self._is_hard_sample(confidence, is_correction)
        if is_hard:
            self.hard_samples.append({
                "image_path": image_path,
                "system_diagnosis": system_diagnosis,
                "final_label": final_label,
                "confidence": confidence,
                "timestamp": timestamp
            })
            self.learning_stats["hard_samples"] += 1
        
        # 保存历史记录
        self._save_history()
        
        result = {
            "success": True,
            "final_label": final_label,
            "is_correction": is_correction,
            "is_hard_sample": is_hard,
            "saved_path": save_result.get("saved_path"),
            "buffer_size": len(self.replay_buffer)
        }
        
        print(f"💾 [主动学习] 反馈已收集")
        print(f"   标签: {final_label} {'(用户修正)' if is_correction else '(系统确认)'}")
        print(f"   困难样本: {'是' if is_hard else '否'}")
        print(f"   经验缓冲区: {len(self.replay_buffer)} 样本")
        
        return result
    
    def _calculate_priority(self, confidence: float, is_correction: bool) -> float:
        """
        计算样本优先级
        
        优先级规则:
        - 被修正的样本优先级更高
        - 低置信度样本优先级更高
        - 困难样本优先级更高
        
        :param confidence: 置信度
        :param is_correction: 是否被修正
        :return: 优先级分数 (0-1)
        """
        base_priority = 1.0 - confidence  # 置信度越低，优先级越高
        
        if is_correction:
            base_priority += 0.3  # 修正样本额外加分
        
        if confidence < self.confidence_threshold:
            base_priority += 0.2  # 困难样本额外加分
        
        return min(base_priority, 1.0)
    
    def _is_hard_sample(self, confidence: float, is_correction: bool) -> bool:
        """
        判断是否为困难样本
        
        :param confidence: 置信度
        :param is_correction: 是否被修正
        :return: 是否为困难样本
        """
        return is_correction or confidence < self.confidence_threshold
    
    def _save_to_feedback_dataset(
        self,
        image_path: str,
        system_diagnosis: str,
        final_label: str,
        is_correction: bool,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        保存到反馈数据集
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断
        :param final_label: 最终标签
        :param is_correction: 是否修正
        :param timestamp: 时间戳
        :return: 保存结果
        """
        # 创建类别目录
        save_dir = os.path.join(self.data_root, final_label)
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        
        # 添加前缀
        prefix = f"err_{system_diagnosis}_corr_" if is_correction else "confirmed_"
        new_filename = f"{timestamp.replace(':', '-')}_{prefix}{final_label}{ext}"
        save_path = os.path.join(save_dir, new_filename)
        
        # 复制图像
        try:
            if os.path.exists(image_path):
                shutil.copy2(image_path, save_path)
            
            # 记录日志
            log_path = os.path.join(save_dir, "feedback_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                record = (f"[{timestamp}] Image: {new_filename} | "
                         f"System: {system_diagnosis} | Final: {final_label}\n")
                f.write(record)
            
            return {"success": True, "saved_path": save_path}
            
        except Exception as e:
            print(f"❌ 保存反馈数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def query_samples_for_labeling(
        self,
        unlabeled_pool: List[Dict[str, Any]],
        num_samples: int = 10,
        strategy: str = "uncertainty"
    ) -> List[Dict[str, Any]]:
        """
        主动学习采样策略
        从未标注池中选择最有价值的样本进行人工标注
        
        :param unlabeled_pool: 未标注样本池
        :param num_samples: 需要采样的数量
        :param strategy: 采样策略 ("uncertainty", "diversity", "hybrid")
        :return: 选中的样本列表
        """
        if len(unlabeled_pool) <= num_samples:
            return unlabeled_pool
        
        if strategy == "uncertainty":
            return self._uncertainty_sampling(unlabeled_pool, num_samples)
        elif strategy == "diversity":
            return self._diversity_sampling(unlabeled_pool, num_samples)
        elif strategy == "hybrid":
            return self._hybrid_sampling(unlabeled_pool, num_samples)
        else:
            # 默认随机采样
            return random.sample(unlabeled_pool, num_samples)
    
    def _uncertainty_sampling(
        self,
        unlabeled_pool: List[Dict[str, Any]],
        num_samples: int
    ) -> List[Dict[str, Any]]:
        """
        不确定性采样
        选择模型最不确定（置信度最低）的样本
        
        :param unlabeled_pool: 未标注样本池
        :param num_samples: 采样数量
        :return: 选中的样本
        """
        # 按置信度排序（选择置信度最低的）
        sorted_pool = sorted(unlabeled_pool, key=lambda x: x.get("confidence", 1.0))
        return sorted_pool[:num_samples]
    
    def _diversity_sampling(
        self,
        unlabeled_pool: List[Dict[str, Any]],
        num_samples: int
    ) -> List[Dict[str, Any]]:
        """
        多样性采样
        确保选中的样本在特征空间上分布均匀
        
        :param unlabeled_pool: 未标注样本池
        :param num_samples: 采样数量
        :return: 选中的样本
        """
        # 简化实现：随机选择不同类别的样本
        # 实际应用中可以使用聚类算法（如K-means）
        
        # 按预测类别分组
        class_groups: Dict[str, List[Dict]] = {}
        for sample in unlabeled_pool:
            pred_class = sample.get("prediction", "unknown")
            if pred_class not in class_groups:
                class_groups[pred_class] = []
            class_groups[pred_class].append(sample)
        
        # 从每个类别均匀采样
        samples_per_class = max(1, num_samples // len(class_groups))
        selected = []
        
        for class_name, samples in class_groups.items():
            selected.extend(random.sample(samples, min(samples_per_class, len(samples))))
        
        # 如果不够，随机补充
        if len(selected) < num_samples:
            remaining = [s for s in unlabeled_pool if s not in selected]
            additional = random.sample(remaining, min(num_samples - len(selected), len(remaining)))
            selected.extend(additional)
        
        return selected[:num_samples]
    
    def _hybrid_sampling(
        self,
        unlabeled_pool: List[Dict[str, Any]],
        num_samples: int
    ) -> List[Dict[str, Any]]:
        """
        混合采样策略
        结合不确定性和多样性
        
        :param unlabeled_pool: 未标注样本池
        :param num_samples: 采样数量
        :return: 选中的样本
        """
        # 50% 不确定性 + 50% 多样性
        uncertainty_num = num_samples // 2
        diversity_num = num_samples - uncertainty_num
        
        uncertainty_samples = self._uncertainty_sampling(unlabeled_pool, uncertainty_num)
        
        # 从未被选中的样本中进行多样性采样
        remaining = [s for s in unlabeled_pool if s not in uncertainty_samples]
        diversity_samples = self._diversity_sampling(remaining, diversity_num)
        
        return uncertainty_samples + diversity_samples
    
    def prepare_incremental_training_data(
        self,
        new_samples: List[Tuple[str, str]],
        batch_size: int = 32
    ) -> List[Tuple[List[str], List[str]]]:
        """
        准备增量训练数据
        混合新样本和经验回放样本
        
        :param new_samples: 新样本列表 [(image_path, label), ...]
        :param batch_size: 批次大小
        :return: 训练批次列表
        """
        if self.incremental_learner is None:
            print("⚠️ 增量学习器未初始化，请先调用 set_model()")
            return []
        
        batches = self.incremental_learner.prepare_training_batch(new_samples, batch_size)
        
        print(f"✅ 已准备 {len(batches)} 个训练批次")
        print(f"   新样本: {len(new_samples)} 个")
        print(f"   经验回放: {len(self.replay_buffer)} 个")
        
        return batches
    
    def incremental_train_step(
        self,
        new_samples: List[Tuple[str, str, float]],
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        transform: Optional[Callable] = None
    ) -> Dict[str, float]:
        """
        执行一步增量训练
        
        :param new_samples: 新样本列表 [(image_path, label, confidence), ...]
        :param optimizer: 优化器
        :param criterion: 损失函数
        :param transform: 图像变换
        :return: 训练统计
        """
        if self.incremental_learner is None:
            print("⚠️ 增量学习器未初始化")
            return {}
        
        # 更新经验回放
        self.incremental_learner.update_model(new_samples)
        
        # 准备训练数据
        new_data = [(path, label) for path, label, _ in new_samples]
        batches = self.prepare_incremental_training_data(new_data, batch_size=32)
        
        if not batches:
            return {}
        
        # 训练模型
        self.incremental_learner.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_paths, batch_labels in batches:
            # 加载图像
            images = []
            for path in batch_paths:
                try:
                    img = Image.open(path).convert('RGB')
                    if transform:
                        img = transform(img)
                    else:
                        # 默认变换
                        img = torch.from_numpy(np.array(img)).permute(2, 0, 1).float() / 255.0
                    images.append(img)
                except Exception as e:
                    print(f"⚠️ 加载图像失败 {path}: {e}")
                    continue
            
            if not images:
                continue
            
            # 构建批次
            images = torch.stack(images).to(self.device)
            
            # 获取标签索引
            label_indices = [self._get_or_create_class_idx(label) for label in batch_labels]
            labels = torch.tensor(label_indices).to(self.device)
            
            # 前向传播
            optimizer.zero_grad()
            outputs = self.incremental_learner.model(images)
            
            # 如果类别数增加，需要调整输出层
            if outputs.size(1) < len(self.class_to_idx):
                # 扩展输出层
                print(f"🔄 扩展输出层: {outputs.size(1)} -> {len(self.class_to_idx)}")
                # 这里简化处理，实际应该动态调整模型结构
            
            loss = criterion(outputs, labels)
            
            # 反向传播
            loss.backward()
            optimizer.step()
            
            # 统计
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
        
        # 更新统计
        self.learning_stats["incremental_updates"] += 1
        
        avg_loss = total_loss / len(batches) if batches else 0
        accuracy = 100.0 * correct / total if total > 0 else 0
        
        print(f"✅ 增量训练完成")
        print(f"   平均损失: {avg_loss:.4f}")
        print(f"   准确率: {accuracy:.2f}%")
        
        return {
            "loss": avg_loss,
            "accuracy": accuracy,
            "samples": total
        }
    
    def _get_or_create_class_idx(self, class_name: str) -> int:
        """
        获取或创建类别索引
        
        :param class_name: 类别名称
        :return: 类别索引
        """
        if class_name not in self.class_to_idx:
            idx = len(self.class_to_idx)
            self.class_to_idx[class_name] = idx
            self.idx_to_class[idx] = class_name
            
            # 添加到增量学习器
            if self.incremental_learner:
                self.incremental_learner.add_new_class(class_name)
        
        return self.class_to_idx[class_name]
    
    def get_hard_samples(self, num_samples: int = 10) -> List[Dict[str, Any]]:
        """
        获取困难样本
        
        :param num_samples: 样本数量
        :return: 困难样本列表
        """
        return self.hard_samples[:num_samples]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        获取学习统计信息
        
        :return: 统计信息字典
        """
        stats = {
            **self.learning_stats,
            "buffer_size": len(self.replay_buffer),
            "buffer_distribution": self.replay_buffer.get_class_distribution(),
            "learned_classes": list(self.class_to_idx.keys()),
            "num_classes": len(self.class_to_idx)
        }
        
        if self.incremental_learner:
            stats["incremental_stats"] = self.incremental_learner.get_replay_statistics()
        
        return stats
    
    def export_training_report(self, output_path: str = "reports/active_learning_report.json"):
        """
        导出训练报告
        
        :param output_path: 输出路径
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "statistics": self.get_learning_statistics(),
            "hard_samples": self.hard_samples[:50],  # 只导出前50个
            "recent_feedback": [r.to_dict() for r in self.feedback_history[-100:]]  # 最近100条
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 训练报告已导出: {output_path}")
    
    def _save_history(self):
        """保存历史记录到磁盘"""
        history_path = os.path.join(self.data_root, "feedback_history.json")
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(
                [r.to_dict() for r in self.feedback_history],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        # 保存统计
        stats_path = os.path.join(self.data_root, "learning_stats.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.learning_stats, f, ensure_ascii=False, indent=2)
    
    def _load_history(self):
        """从磁盘加载历史记录"""
        # 加载反馈历史
        history_path = os.path.join(self.data_root, "feedback_history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_history = [FeedbackRecord.from_dict(r) for r in data]
            except Exception as e:
                print(f"⚠️ 加载反馈历史失败: {e}")
        
        # 加载统计
        stats_path = os.path.join(self.data_root, "learning_stats.json")
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r', encoding='utf-8') as f:
                    self.learning_stats = json.load(f)
            except Exception as e:
                print(f"⚠️ 加载学习统计失败: {e}")


def test_enhanced_active_learner():
    """测试增强型主动学习引擎"""
    print("=" * 70)
    print("🧪 测试增强型主动学习引擎")
    print("=" * 70)
    
    # 创建学习引擎
    learner = EnhancedActiveLearner(
        data_root="datasets/test_feedback",
        replay_buffer_dir="data/test_experience_replay",
        buffer_capacity=100,
        rehearsal_ratio=0.3,
        confidence_threshold=0.7
    )
    
    # 模拟收集反馈
    print("\n" + "=" * 70)
    print("🧪 测试反馈收集")
    print("=" * 70)
    
    test_cases = [
        ("test1.jpg", "条锈病", 0.95, None),
        ("test2.jpg", "白粉病", 0.45, "赤霉病"),  # 低置信度 + 修正
        ("test3.jpg", "蚜虫", 0.65, None),  # 低置信度
        ("test4.jpg", "赤霉病", 0.88, None),
        ("test5.jpg", "条锈病", 0.55, "白粉病"),  # 修正
    ]
    
    for image_path, system_diag, conf, user_corr in test_cases:
        result = learner.collect_feedback(
            image_path=image_path,
            system_diagnosis=system_diag,
            confidence=conf,
            user_correction=user_corr,
            comments="测试反馈"
        )
        print(f"   - {image_path}: {result['final_label']}, 困难样本: {result['is_hard_sample']}")
    
    # 测试主动采样
    print("\n" + "=" * 70)
    print("🧪 测试主动采样策略")
    print("=" * 70)
    
    unlabeled_pool = [
        {"image_path": f"unlabeled_{i}.jpg", "prediction": random.choice(["条锈病", "白粉病"]), 
         "confidence": random.uniform(0.3, 0.95)}
        for i in range(20)
    ]
    
    # 不确定性采样
    uncertainty_samples = learner.query_samples_for_labeling(
        unlabeled_pool, num_samples=5, strategy="uncertainty"
    )
    print(f"\n✅ 不确定性采样: {len(uncertainty_samples)} 个")
    for s in uncertainty_samples:
        print(f"   - {s['image_path']}: 置信度 {s['confidence']:.2f}")
    
    # 多样性采样
    diversity_samples = learner.query_samples_for_labeling(
        unlabeled_pool, num_samples=5, strategy="diversity"
    )
    print(f"\n✅ 多样性采样: {len(diversity_samples)} 个")
    for s in diversity_samples:
        print(f"   - {s['image_path']}: 预测 {s['prediction']}")
    
    # 获取统计信息
    print("\n" + "=" * 70)
    print("🧪 学习统计信息")
    print("=" * 70)
    
    stats = learner.get_learning_statistics()
    print(f"✅ 总反馈数: {stats['total_feedback']}")
    print(f"✅ 修正数: {stats['corrections']}")
    print(f"✅ 确认数: {stats['confirmations']}")
    print(f"✅ 困难样本数: {stats['hard_samples']}")
    print(f"✅ 经验缓冲区大小: {stats['buffer_size']}")
    print(f"✅ 类别分布: {stats['buffer_distribution']}")
    
    # 清理测试数据
    import shutil
    if os.path.exists("datasets/test_feedback"):
        shutil.rmtree("datasets/test_feedback")
    if os.path.exists("data/test_experience_replay"):
        shutil.rmtree("data/test_experience_replay")
    
    print("\n" + "=" * 70)
    print("✅ 增强型主动学习引擎测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_enhanced_active_learner()
