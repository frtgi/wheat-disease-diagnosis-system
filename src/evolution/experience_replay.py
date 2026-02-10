# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/src/evolution/experience_replay.py
"""
自进化机制 - Experience Replay
存储历史诊断样本，定期重放训练，避免灾难性遗忘
"""

import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Any
import random
from datetime import datetime

class ExperienceReplayBuffer:
    """
    经验回放缓冲区
    存储历史诊断样本，用于持续学习
    """
    
    def __init__(self, buffer_size=1000, save_path="data/experience_replay"):
        """
        初始化经验回放缓冲区
        :param buffer_size: 缓冲区最大容量
        :param save_path: 保存路径
        """
        self.buffer_size = buffer_size
        self.save_path = save_path
        self.buffer: List[Dict[str, Any]] = []
        
        # 创建保存目录
        os.makedirs(save_path, exist_ok=True)
        
        # 加载历史数据
        self._load_buffer()
        
        print(f"📦 [Experience Replay] 缓冲区初始化完成，当前样本数: {len(self.buffer)}")
    
    def _load_buffer(self):
        """
        从磁盘加载历史缓冲区数据
        """
        buffer_file = os.path.join(self.save_path, "experience_buffer.json")
        if os.path.exists(buffer_file):
            try:
                with open(buffer_file, 'r', encoding='utf-8') as f:
                    self.buffer = json.load(f)
                print(f"✅ [Experience Replay] 已加载 {len(self.buffer)} 条历史样本")
            except Exception as e:
                print(f"⚠️ [Experience Replay] 加载历史数据失败: {e}")
                self.buffer = []
    
    def _save_buffer(self):
        """
        保存缓冲区数据到磁盘
        """
        buffer_file = os.path.join(self.save_path, "experience_buffer.json")
        try:
            with open(buffer_file, 'w', encoding='utf-8') as f:
                json.dump(self.buffer, f, ensure_ascii=False, indent=2)
            print(f"💾 [Experience Replay] 已保存 {len(self.buffer)} 条样本到磁盘")
        except Exception as e:
            print(f"⚠️ [Experience Replay] 保存数据失败: {e}")
    
    def add_experience(self, image_path: str, user_text: str, 
                        vision_result: Dict, text_result: Dict, 
                        final_diagnosis: str, user_feedback: str = None):
        """
        添加新的诊断经验到缓冲区
        :param image_path: 图像路径
        :param user_text: 用户文本描述
        :param vision_result: 视觉诊断结果
        :param text_result: 文本诊断结果
        :param final_diagnosis: 最终诊断结果
        :param user_feedback: 用户反馈（可选）
        """
        experience = {
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "user_text": user_text,
            "vision_result": vision_result,
            "text_result": text_result,
            "final_diagnosis": final_diagnosis,
            "user_feedback": user_feedback,
            "priority": self._calculate_priority(vision_result, text_result, final_diagnosis)
        }
        
        # 如果缓冲区已满，移除优先级最低的样本
        if len(self.buffer) >= self.buffer_size:
            self.buffer.sort(key=lambda x: x['priority'], reverse=True)
            self.buffer.pop()
        
        self.buffer.append(experience)
        
        # 定期保存
        if len(self.buffer) % 10 == 0:
            self._save_buffer()
        
        print(f"➕ [Experience Replay] 已添加新样本，当前缓冲区大小: {len(self.buffer)}")
    
    def _calculate_priority(self, vision_result: Dict, text_result: Dict, 
                           final_diagnosis: str) -> float:
        """
        计算样本优先级
        优先级越高，越容易被保留和重放
        """
        priority = 0.5
        
        # 视觉和文本结果不一致的样本优先级更高
        if vision_result.get('label') != text_result.get('label'):
            priority += 0.3
        
        # 有用户反馈的样本优先级更高
        if vision_result.get('user_feedback'):
            priority += 0.2
        
        # 低置信度的样本优先级更高（需要更多训练）
        vision_conf = vision_result.get('conf', 0.0)
        text_conf = text_result.get('conf', 0.0)
        if vision_conf < 0.5 or text_conf < 0.5:
            priority += 0.2
        
        return min(priority, 1.0)
    
    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        从缓冲区采样一批样本
        :param batch_size: 批次大小
        :return: 采样结果
        """
        if len(self.buffer) == 0:
            return []
        
        # 根据优先级进行加权采样
        priorities = [exp['priority'] for exp in self.buffer]
        total_priority = sum(priorities)
        
        if total_priority == 0:
            # 如果所有优先级都为0，均匀采样
            return random.sample(self.buffer, min(batch_size, len(self.buffer)))
        
        # 加权采样
        probs = [p / total_priority for p in priorities]
        sampled_indices = random.choices(
            range(len(self.buffer)), 
            weights=probs, 
            k=min(batch_size, len(self.buffer))
        )
        
        return [self.buffer[i] for i in sampled_indices]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取缓冲区统计信息
        """
        if not self.buffer:
            return {"total": 0}
        
        diagnosis_counts = {}
        for exp in self.buffer:
            diagnosis = exp['final_diagnosis']
            diagnosis_counts[diagnosis] = diagnosis_counts.get(diagnosis, 0) + 1
        
        avg_priority = sum(exp['priority'] for exp in self.buffer) / len(self.buffer)
        
        return {
            "total": len(self.buffer),
            "diagnosis_distribution": diagnosis_counts,
            "avg_priority": avg_priority
        }


class ExperienceReplayDataset(Dataset):
    """
    经验回放数据集
    用于 PyTorch DataLoader
    """
    
    def __init__(self, experiences: List[Dict[str, Any]]):
        """
        初始化数据集
        :param experiences: 经验列表
        """
        self.experiences = experiences
    
    def __len__(self):
        return len(self.experiences)
    
    def __getitem__(self, idx):
        """
        获取单个样本
        """
        exp = self.experiences[idx]
        
        # 返回样本数据（实际使用时需要加载图像和文本）
        return {
            "image_path": exp['image_path'],
            "user_text": exp['user_text'],
            "vision_result": exp['vision_result'],
            "text_result": exp['text_result'],
            "final_diagnosis": exp['final_diagnosis'],
            "user_feedback": exp['user_feedback']
        }


class ExperienceReplayTrainer:
    """
    经验回放训练器
    使用历史样本进行持续学习
    """
    
    def __init__(self, model, replay_buffer: ExperienceReplayBuffer, 
                 learning_rate=0.001, device='cuda'):
        """
        初始化训练器
        :param model: 要训练的模型
        :param replay_buffer: 经验回放缓冲区
        :param learning_rate: 学习率
        :param device: 设备
        """
        self.model = model
        self.replay_buffer = replay_buffer
        self.device = device
        
        # 优化器
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        
        # 损失函数
        self.criterion = nn.CrossEntropyLoss()
        
        print("🎓 [Experience Replay Trainer] 训练器初始化完成")
    
    def replay_train(self, epochs=10, batch_size=16):
        """
        执行经验回放训练
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        """
        if len(self.replay_buffer.buffer) == 0:
            print("⚠️ [Experience Replay] 缓冲区为空，跳过训练")
            return
        
        print(f"🔄 [Experience Replay] 开始训练，缓冲区样本数: {len(self.replay_buffer.buffer)}")
        
        # 采样数据
        sampled_experiences = self.replay_buffer.sample(len(self.replay_buffer.buffer))
        
        # 创建数据集和数据加载器
        dataset = ExperienceReplayDataset(sampled_experiences)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 训练循环
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0.0
            num_batches = 0
            
            for batch in dataloader:
                # 这里需要根据实际模型实现前向传播和反向传播
                # 示例代码（需要根据实际模型调整）
                
                # 模拟损失计算
                loss = torch.tensor(0.1, requires_grad=True)
                
                # 反向传播
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
                num_batches += 1
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0
            print(f"📊 [Experience Replay] Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        print("✅ [Experience Replay] 训练完成")
    
    def save_checkpoint(self, path="models/experience_replay_checkpoint.pt"):
        """
        保存训练检查点
        """
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'buffer_size': len(self.replay_buffer.buffer)
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(checkpoint, path)
        print(f"💾 [Experience Replay] 检查点已保存: {path}")
    
    def load_checkpoint(self, path="models/experience_replay_checkpoint.pt"):
        """
        加载训练检查点
        """
        if os.path.exists(path):
            checkpoint = torch.load(path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            print(f"✅ [Experience Replay] 检查点已加载: {path}")
        else:
            print(f"⚠️ [Experience Replay] 检查点不存在: {path}")


# 使用示例
if __name__ == "__main__":
    # 创建经验回放缓冲区
    replay_buffer = ExperienceReplayBuffer(buffer_size=100)
    
    # 添加一些示例经验
    replay_buffer.add_experience(
        image_path="data/test/image1.jpg",
        user_text="叶片上有黄色条纹",
        vision_result={"label": "条锈病", "conf": 0.85},
        text_result={"label": "条锈病", "conf": 0.90},
        final_diagnosis="条锈病"
    )
    
    # 获取统计信息
    stats = replay_buffer.get_statistics()
    print(f"📊 统计信息: {stats}")
    
    # 采样数据
    sampled = replay_buffer.sample(batch_size=5)
    print(f"🎲 采样结果: {len(sampled)} 条样本")
