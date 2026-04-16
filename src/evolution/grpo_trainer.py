# -*- coding: utf-8 -*-
"""
GRPO 强化学习训练器 (Group Relative Policy Optimization Trainer)
IWDDA Agent 自进化机制核心组件，基于组相对策略优化的强化学习框架

功能特性:
1. 诊断准确性奖励：与专家标注一致时给予高奖励
2. 推理逻辑性奖励：符合农业知识规则时给予奖励
3. 输出简洁度奖励：避免冗余输出
4. 策略优化：基于 GRPO 算法更新策略网络
5. 与 CaseMemory 和 FeedbackHandler 集成：从反馈中积累训练数据

GRPO 算法核心:
- 对每个状态采样多个动作（诊断结果）
- 计算组内相对优势（相对于组平均奖励）
- 使用 PPO 风格的 clipped surrogate loss 优化策略
- 引入 KL 散度惩罚防止策略偏离过大

使用示例:
    from src.evolution import GRPOTrainer
    from src.memory import CaseMemory, FeedbackHandler
    
    # 初始化
    case_memory = CaseMemory()
    feedback_handler = FeedbackHandler(case_memory=case_memory)
    trainer = GRPOTrainer(case_memory=case_memory, feedback_handler=feedback_handler)
    
    # 训练
    trainer.train(num_iterations=100, batch_size=32)
    
    # 评估
    performance = trainer.evaluate()
"""

import os
import sys
import json
import math
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import numpy as np

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
class GRPOConfig:
    """
    GRPO 训练配置类
    
    包含 GRPO 算法的所有超参数配置
    """
    # 模型架构
    hidden_size: int = 256
    num_layers: int = 3
    dropout_rate: float = 0.1
    
    # GRPO 算法参数
    num_samples_per_state: int = 5  # 每个状态采样的动作数
    clip_epsilon: float = 0.2  # PPO clip 参数
    kl_beta: float = 0.01  # KL 散度惩罚系数
    entropy_coef: float = 0.01  # 熵正则化系数
    
    # 训练参数
    learning_rate: float = 1e-4
    gamma: float = 0.99  # 折扣因子
    max_epochs: int = 100
    batch_size: int = 32
    
    # 奖励权重
    accuracy_weight: float = 1.0  # 诊断准确性奖励权重
    logic_weight: float = 0.5  # 推理逻辑性奖励权重
    conciseness_weight: float = 0.3  # 输出简洁度奖励权重
    
    # 设备
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class RewardNetwork(nn.Module):
    """
    奖励网络类
    
    用于计算综合奖励分数，包括：
    - 诊断准确性奖励
    - 推理逻辑性奖励
    - 输出简洁度奖励
    """
    
    def __init__(self, input_size: int, hidden_size: int = 128):
        """
        初始化奖励网络
        
        :param input_size: 输入特征维度
        :param hidden_size: 隐藏层维度
        """
        super(RewardNetwork, self).__init__()
        
        self.accuracy_head = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, 1)
        )
        
        self.logic_head = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, 1)
        )
        
        self.conciseness_head = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, 1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播计算各项奖励
        
        :param x: 输入特征张量 [batch_size, input_size]
        :return: (准确性奖励，逻辑性奖励，简洁度奖励) 三个张量
        """
        accuracy_reward = self.accuracy_head(x)
        logic_reward = self.logic_head(x)
        conciseness_reward = self.conciseness_head(x)
        
        return accuracy_reward, logic_reward, conciseness_reward


class PolicyNetwork(nn.Module):
    """
    策略网络类
    
    GRPO 算法的核心，用于生成诊断动作的概率分布
    """
    
    def __init__(
        self,
        input_size: int,
        output_size: int,
        hidden_size: int = 256,
        num_layers: int = 3,
        dropout_rate: float = 0.1
    ):
        """
        初始化策略网络
        
        :param input_size: 输入特征维度（图像特征 + 文本特征 + 上下文特征）
        :param output_size: 输出维度（病害类型数量）
        :param hidden_size: 隐藏层维度
        :param num_layers: 网络层数
        :param dropout_rate: Dropout 比率
        """
        super(PolicyNetwork, self).__init__()
        
        layers = []
        prev_size = input_size
        
        for i in range(num_layers):
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.LayerNorm(hidden_size),
                nn.Dropout(dropout_rate)
            ])
            prev_size = hidden_size
        
        self.feature_extractor = nn.Sequential(*layers)
        
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_size, output_size),
            nn.Softmax(dim=-1)
        )
        
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_size, 1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param x: 输入特征张量
        :return: (动作概率分布，状态价值)
        """
        features = self.feature_extractor(x)
        
        action_probs = self.actor_head(features)
        state_value = self.critic_head(features)
        
        return action_probs, state_value
    
    def get_action(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[int, torch.Tensor]:
        """
        根据状态采样动作
        
        :param state: 状态张量
        :param deterministic: 是否使用确定性策略（选择概率最大的动作）
        :return: (动作索引，动作概率)
        """
        action_probs, _ = self.forward(state)
        
        if deterministic:
            action = torch.argmax(action_probs, dim=-1)
            action_prob = torch.max(action_probs, dim=-1).values
        else:
            dist = Categorical(action_probs)
            action = dist.sample()
            action_prob = dist.log_prob(action)
        
        return action.item(), action_prob


class GRPOTrainer:
    """
    GRPO 训练器类
    
    实现 Group Relative Policy Optimization 强化学习算法，用于：
    1. 优化诊断策略
    2. 提高诊断准确性
    3. 改善推理逻辑性
    4. 优化输出质量
    
    核心流程:
    1. 从病例记忆和反馈中收集训练数据
    2. 对每个状态采样多个动作
    3. 计算综合奖励（准确性 + 逻辑性 + 简洁度）
    4. 计算组内相对优势
    5. 更新策略网络
    """
    
    def __init__(
        self,
        input_size: int = 512,
        num_disease_types: int = 15,
        config: Optional[GRPOConfig] = None,
        case_memory: Optional[Any] = None,
        feedback_handler: Optional[Any] = None,
        model_path: Optional[str] = None
    ):
        """
        初始化 GRPO 训练器
        
        :param input_size: 输入特征维度
        :param num_disease_types: 病害类型数量
        :param config: GRPO 配置
        :param case_memory: CaseMemory 实例
        :param feedback_handler: FeedbackHandler 实例
        :param model_path: 模型保存路径
        """
        self.config = config or GRPOConfig()
        self.case_memory = case_memory
        self.feedback_handler = feedback_handler
        self.model_path = model_path or "models/grpo"
        
        # 确保目录存在
        Path(self.model_path).mkdir(parents=True, exist_ok=True)
        
        # 初始化网络
        self.policy_network = PolicyNetwork(
            input_size=input_size,
            output_size=num_disease_types,
            hidden_size=self.config.hidden_size,
            num_layers=self.config.num_layers,
            dropout_rate=self.config.dropout_rate
        ).to(self.config.device)
        
        self.reward_network = RewardNetwork(
            input_size=input_size,
            hidden_size=128
        ).to(self.config.device)
        
        # 优化器
        self.policy_optimizer = torch.optim.Adam(
            self.policy_network.parameters(),
            lr=self.config.learning_rate
        )
        
        self.reward_optimizer = torch.optim.Adam(
            self.reward_network.parameters(),
            lr=self.config.learning_rate
        )
        
        # 训练历史
        self.training_history: List[Dict[str, float]] = []
        self.episode_rewards: List[float] = []
        
        # 农业知识规则（用于逻辑性奖励）
        self.agro_knowledge_rules = self._init_agro_knowledge_rules()
        
        # 加载已有模型
        self._load_model()
        
        print("=" * 60)
        print("🎯 [GRPOTrainer] GRPO 强化学习训练器初始化完成")
        print("=" * 60)
        print(f"   设备：{self.config.device}")
        print(f"   输入维度：{input_size}")
        print(f"   病害类型数：{num_disease_types}")
        print(f"   采样数/状态：{self.config.num_samples_per_state}")
        print(f"   学习率：{self.config.learning_rate}")
    
    def _init_agro_knowledge_rules(self) -> Dict[str, Any]:
        """
        初始化农业知识规则库
        
        用于推理逻辑性奖励的计算
        
        :return: 农业知识规则字典
        """
        return {
            "severity_consistency": {
                "description": "严重度与病斑面积一致性规则",
                "weight": 0.3,
                "rules": {
                    "轻度": {"min_area": 0, "max_area": 0.15},
                    "中度": {"min_area": 0.15, "max_area": 0.40},
                    "重度": {"min_area": 0.40, "max_area": 1.0}
                }
            },
            "disease_seasonality": {
                "description": "病害季节性规律",
                "weight": 0.3,
                "rules": {
                    "条锈病": {"peak_months": [3, 4, 5], "temperature_range": (10, 20)},
                    "叶锈病": {"peak_months": [4, 5, 6], "temperature_range": (15, 25)},
                    "白粉病": {"peak_months": [3, 4, 5, 9, 10], "temperature_range": (15, 22)},
                    "赤霉病": {"peak_months": [4, 5], "temperature_range": (20, 28), "humidity_required": True}
                }
            },
            "medication_effectiveness": {
                "description": "药剂有效性规则",
                "weight": 0.4,
                "rules": {
                    "条锈病": ["三唑酮", "烯唑醇", "戊唑醇"],
                    "叶锈病": ["三唑酮", "腈菌唑"],
                    "白粉病": ["多菌灵", "甲基硫菌灵"],
                    "赤霉病": ["多菌灵", "戊唑醇"]
                }
            }
        }
    
    def _prepare_state(self, case_data: Dict[str, Any]) -> torch.Tensor:
        """
        准备状态特征向量
        
        :param case_data: 病例数据
        :return: 状态张量 [1, input_size]
        """
        # 这里简化处理，实际应该从图像、文本等提取特征
        # 示例：拼接图像特征、文本特征、上下文特征
        
        # 图像特征（模拟）
        image_features = torch.randn(1, 256).to(self.config.device)
        
        # 文本特征（模拟）
        text_features = torch.randn(1, 128).to(self.config.device)
        
        # 上下文特征（模拟）
        context_features = torch.randn(1, 128).to(self.config.device)
        
        # 拼接特征
        state = torch.cat([image_features, text_features, context_features], dim=-1)
        
        return state
    
    def _calculate_accuracy_reward(
        self,
        predicted_disease: str,
        expert_label: str,
        confidence: float
    ) -> float:
        """
        计算诊断准确性奖励
        
        :param predicted_disease: 预测的病害类型
        :param expert_label: 专家标注的病害类型
        :param confidence: 预测置信度
        :return: 准确性奖励分数
        """
        if predicted_disease == expert_label:
            # 完全正确：基础奖励 + 置信度加成
            reward = 1.0 + 0.5 * confidence
        else:
            # 错误：负奖励
            reward = -0.5
        
        return reward * self.config.accuracy_weight
    
    def _calculate_logic_reward(
        self,
        diagnosis: Dict[str, Any],
        case_context: Dict[str, Any]
    ) -> float:
        """
        计算推理逻辑性奖励
        
        :param diagnosis: 诊断结果（包含病害类型、严重度、推荐方案等）
        :param case_context: 病例上下文（包含时间、地点、天气等）
        :return: 逻辑性奖励分数
        """
        logic_score = 0.0
        total_weight = 0.0
        
        # 规则 1: 严重度与病斑面积一致性
        severity_rule = self.agro_knowledge_rules["severity_consistency"]
        if "severity" in diagnosis and "lesion_area" in case_context:
            lesion_area = case_context["lesion_area"]
            severity = diagnosis["severity"]
            
            if severity in severity_rule["rules"]:
                area_range = severity_rule["rules"][severity]
                if area_range["min_area"] <= lesion_area < area_range["max_area"]:
                    logic_score += severity_rule["weight"]
                    total_weight += severity_rule["weight"]
        
        # 规则 2: 季节性规律
        seasonality_rule = self.agro_knowledge_rules["disease_seasonality"]
        if "disease_type" in diagnosis and "month" in case_context:
            disease = diagnosis["disease_type"]
            month = case_context["month"]
            
            if disease in seasonality_rule["rules"]:
                peak_months = seasonality_rule["rules"][disease]["peak_months"]
                if month in peak_months:
                    logic_score += seasonality_rule["weight"]
                total_weight += seasonality_rule["weight"]
        
        # 规则 3: 推荐方案有效性
        med_rule = self.agro_knowledge_rules["medication_effectiveness"]
        if "disease_type" in diagnosis and "recommendation" in diagnosis:
            disease = diagnosis["disease_type"]
            recommendation = diagnosis["recommendation"]
            
            if disease in med_rule["rules"]:
                effective_meds = med_rule["rules"][disease]
                if any(med in recommendation for med in effective_meds):
                    logic_score += med_rule["weight"]
                total_weight += med_rule["weight"]
        
        # 归一化
        if total_weight > 0:
            logic_score /= total_weight
        
        return logic_score * self.config.logic_weight
    
    def _calculate_conciseness_reward(
        self,
        output_text: str,
        max_length: int = 200
    ) -> float:
        """
        计算输出简洁度奖励
        
        :param output_text: 输出文本
        :param max_length: 最大推荐长度
        :return: 简洁度奖励分数
        """
        length = len(output_text)
        
        if length <= max_length:
            # 长度合适：奖励
            reward = 1.0
        else:
            # 过长：惩罚，超出越多惩罚越大
            excess_ratio = (length - max_length) / max_length
            reward = max(0.0, 1.0 - excess_ratio)
        
        # 检查冗余（简单检查重复短语）
        sentences = output_text.split('。')
        if len(sentences) > len(set(sentences)):
            # 有重复句子
            reward *= 0.8
        
        return reward * self.config.conciseness_weight
    
    def _calculate_total_reward(
        self,
        diagnosis: Dict[str, Any],
        expert_label: Optional[str] = None,
        case_context: Optional[Dict[str, Any]] = None,
        output_text: str = ""
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算综合奖励
        
        :param diagnosis: 诊断结果
        :param expert_label: 专家标注（可选）
        :param case_context: 病例上下文
        :param output_text: 输出文本
        :return: (总奖励，各项奖励明细)
        """
        rewards = {}
        
        # 准确性奖励
        if expert_label:
            accuracy_reward = self._calculate_accuracy_reward(
                diagnosis.get("disease_type", ""),
                expert_label,
                diagnosis.get("confidence", 0.5)
            )
            rewards["accuracy"] = accuracy_reward
        else:
            rewards["accuracy"] = 0.0
        
        # 逻辑性奖励
        if case_context:
            logic_reward = self._calculate_logic_reward(diagnosis, case_context)
            rewards["logic"] = logic_reward
        else:
            rewards["logic"] = 0.0
        
        # 简洁度奖励
        if output_text:
            conciseness_reward = self._calculate_conciseness_reward(output_text)
            rewards["conciseness"] = conciseness_reward
        else:
            rewards["conciseness"] = 0.0
        
        # 总奖励
        total_reward = sum(rewards.values())
        
        return total_reward, rewards
    
    def _sample_actions(
        self,
        state: torch.Tensor,
        num_samples: int
    ) -> List[Tuple[int, torch.Tensor]]:
        """
        对给定状态采样多个动作
        
        :param state: 状态张量
        :param num_samples: 采样数量
        :return: 动作列表 [(动作索引，动作概率), ...]
        """
        actions = []
        
        # 确保策略网络在正确的设备上
        self.policy_network.to(state.device)
        
        for _ in range(num_samples):
            action, action_prob = self.policy_network.get_action(state, deterministic=False)
            actions.append((action, action_prob))
        
        return actions
    
    def _compute_group_advantage(
        self,
        rewards: List[float]
    ) -> List[torch.Tensor]:
        """
        计算组内相对优势（Group Relative Advantage）
        
        GRPO 算法核心：计算每个动作相对于组平均奖励的优势
        
        :param rewards: 奖励列表
        :return: 优势值列表
        """
        rewards_tensor = torch.tensor(rewards, dtype=torch.float32)
        
        # 组平均奖励
        mean_reward = torch.mean(rewards_tensor)
        
        # 组标准差（用于归一化）
        std_reward = torch.std(rewards_tensor) + 1e-8
        
        # 相对优势 = (当前奖励 - 平均奖励) / 标准差
        advantages = (rewards_tensor - mean_reward) / std_reward
        
        return advantages.tolist()
    
    def _grpo_update(
        self,
        states: List[torch.Tensor],
        actions: List[int],
        old_action_probs: List[torch.Tensor],
        advantages: List[float]
    ) -> Dict[str, float]:
        """
        执行 GRPO 策略更新
        
        :param states: 状态列表
        :param actions: 动作列表
        :param old_action_probs: 旧策略下的动作概率
        :param advantages: 优势值列表
        :return: 训练指标字典
        """
        total_loss = 0.0
        total_clip_frac = 0.0
        total_kl_div = 0.0
        
        # 确保网络在正确的设备上
        device = states[0].device
        self.policy_network.to(device)
        
        # 批量更新
        for state, action, old_prob, adv in zip(
            states, actions, old_action_probs, advantages
        ):
            # 获取新策略下的动作概率（使用 clone 避免 in-place 操作）
            _, new_prob = self.policy_network.get_action(state, deterministic=False)
            
            # 计算比率 r = π_new(a|s) / π_old(a|s)
            ratio = torch.exp(new_prob.clone() - old_prob.clone())
            
            # Clipped surrogate loss
            adv_tensor = torch.tensor(adv, dtype=torch.float32).to(device)
            surr1 = ratio * adv_tensor
            surr2 = torch.clamp(
                ratio,
                1.0 - self.config.clip_epsilon,
                1.0 + self.config.clip_epsilon
            ) * adv_tensor
            
            policy_loss = -torch.min(surr1, surr2)
            
            # KL 散度惩罚（使用 clone 避免 in-place）
            kl_div = old_prob.clone() - new_prob.clone()
            
            # 总损失
            loss = policy_loss + self.config.kl_beta * kl_div
            
            # 反向传播
            self.policy_optimizer.zero_grad()
            loss.backward()
            self.policy_optimizer.step()
            
            # 统计
            total_loss += loss.item()
            total_clip_frac += torch.abs(ratio - 1.0).item()
            total_kl_div += kl_div.item()
        
        num_updates = len(states)
        
        return {
            "policy_loss": total_loss / num_updates,
            "clip_fraction": total_clip_frac / num_updates,
            "kl_divergence": total_kl_div / num_updates
        }
    
    def train(
        self,
        num_iterations: int = 100,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        训练 GRPO 模型
        
        :param num_iterations: 迭代次数
        :param batch_size: 批次大小（使用配置中的默认值）
        :return: 训练结果统计
        """
        if batch_size is None:
            batch_size = self.config.batch_size
        
        print("\n" + "=" * 60)
        print("🎯 [GRPOTrainer] 开始 GRPO 训练")
        print("=" * 60)
        print(f"   迭代次数：{num_iterations}")
        print(f"   批次大小：{batch_size}")
        print(f"   设备：{self.config.device}")
        
        self.policy_network.train()
        self.reward_network.train()
        
        # 模拟训练数据（实际应从 CaseMemory 和 FeedbackHandler 获取）
        training_data = self._prepare_training_data()
        
        if not training_data:
            print("⚠️ 无训练数据，跳过训练")
            return {"status": "skipped", "reason": "no_training_data"}
        
        for iteration in range(num_iterations):
            batch_rewards = []
            batch_metrics = []
            
            # 采样一个批次
            batch_indices = random.sample(
                range(len(training_data)),
                min(batch_size, len(training_data))
            )
            
            for idx in batch_indices:
                sample = training_data[idx]
                state = sample["state"]
                expert_label = sample.get("expert_label")
                context = sample.get("context")
                
                # 采样多个动作
                actions = self._sample_actions(
                    state,
                    self.config.num_samples_per_state
                )
                
                # 计算每个动作的奖励
                rewards = []
                for action, action_prob in actions:
                    diagnosis = self._action_to_diagnosis(action)
                    total_reward, reward_details = self._calculate_total_reward(
                        diagnosis,
                        expert_label,
                        context
                    )
                    rewards.append(total_reward)
                
                # 计算组内相对优势
                advantages = self._compute_group_advantage(rewards)
                
                # GRPO 更新
                states_list = [state] * self.config.num_samples_per_state
                actions_list = [a[0] for a in actions]
                old_probs = [a[1] for a in actions]
                
                metrics = self._grpo_update(
                    states_list,
                    actions_list,
                    old_probs,
                    advantages
                )
                
                batch_rewards.append(max(rewards))
                batch_metrics.append(metrics)
            
            # 计算平均奖励
            avg_reward = sum(batch_rewards) / len(batch_rewards)
            self.episode_rewards.append(avg_reward)
            
            # 记录训练历史
            avg_metrics = {
                key: sum(m[key] for m in batch_metrics) / len(batch_metrics)
                for key in batch_metrics[0].keys()
            }
            
            history_record = {
                "iteration": iteration + 1,
                "avg_reward": avg_reward,
                **avg_metrics,
                "timestamp": datetime.now().isoformat()
            }
            self.training_history.append(history_record)
            
            # 打印进度
            if (iteration + 1) % 10 == 0:
                print(f"   Iteration {iteration + 1}/{num_iterations} - "
                      f"奖励：{avg_reward:.4f}, "
                      f"损失：{avg_metrics['policy_loss']:.4f}, "
                      f"KL: {avg_metrics['kl_divergence']:.4f}")
        
        # 保存模型
        self._save_model()
        
        print("\n" + "=" * 60)
        print("✅ [GRPOTrainer] GRPO 训练完成")
        print("=" * 60)
        print(f"   最终平均奖励：{self.episode_rewards[-1]:.4f}")
        print(f"   训练轮次：{len(self.training_history)}")
        
        return {
            "status": "completed",
            "final_reward": self.episode_rewards[-1],
            "num_iterations": num_iterations,
            "training_history": self.training_history
        }
    
    def _prepare_training_data(self) -> List[Dict[str, Any]]:
        """
        准备训练数据
        
        从 CaseMemory 和 FeedbackHandler 中积累诊断案例
        
        :return: 训练数据列表
        """
        training_data = []
        
        if self.case_memory is None:
            print("⚠️ 未提供 CaseMemory，使用模拟数据")
            # 生成模拟数据
            for i in range(50):
                disease_type = random.choice(["条锈病", "叶锈病", "白粉病", "赤霉病"])
                training_data.append({
                    "state": self._prepare_state({
                        "disease_type": disease_type,
                        "severity": random.choice(["轻度", "中度", "重度"])
                    }),
                    "expert_label": disease_type,
                    "context": {
                        "month": random.randint(1, 12),
                        "lesion_area": random.uniform(0, 1)
                    }
                })
            return training_data
        
        # 从 CaseMemory 获取真实数据
        all_cases = list(self.case_memory._cases.values())
        
        for case in all_cases:
            # 只使用有反馈的高质量案例
            if case.get("user_feedback") or case.get("followup_result"):
                expert_label = case.get("disease_type")
                
                training_data.append({
                    "state": self._prepare_state(case),
                    "expert_label": expert_label,
                    "context": {
                        "month": int(case.get("upload_timestamp", "2026-01-01").split("-")[1]),
                        "lesion_area": 0.3,  # 实际应从图像分析获取
                        "severity": case.get("severity")
                    }
                })
        
        print(f"✓ 准备训练数据：{len(training_data)} 个样本")
        return training_data
    
    def _action_to_diagnosis(self, action: int) -> Dict[str, Any]:
        """
        将动作索引转换为诊断结果
        
        :param action: 动作索引（对应病害类型）
        :return: 诊断结果字典
        """
        disease_types = [
            "条锈病", "叶锈病", "秆锈病", "白粉病", "赤霉病",
            "纹枯病", "全蚀病", "黄矮病", "丛矮病", "蚜虫",
            "红蜘蛛", "麦蜘蛛", "粘虫", "麦蚜", "其他"
        ]
        
        disease_type = disease_types[action % len(disease_types)]
        
        return {
            "disease_type": disease_type,
            "severity": random.choice(["轻度", "中度", "重度"]),
            "confidence": random.uniform(0.7, 0.95),
            "recommendation": f"使用针对性药剂防治{disease_type}"
        }
    
    def evaluate(self) -> Dict[str, Any]:
        """
        评估模型性能
        
        :return: 评估结果字典
        """
        print("\n" + "=" * 60)
        print("📊 [GRPOTrainer] 模型评估")
        print("=" * 60)
        
        self.policy_network.eval()
        
        # 准备测试数据
        test_data = self._prepare_training_data()
        
        if not test_data:
            return {"status": "skipped", "reason": "no_test_data"}
        
        correct_predictions = 0
        total_rewards = []
        
        with torch.no_grad():
            for sample in test_data:
                state = sample["state"]
                expert_label = sample.get("expert_label")
                
                # 获取预测
                action, _ = self.policy_network.get_action(state, deterministic=True)
                diagnosis = self._action_to_diagnosis(action)
                
                # 计算奖励
                total_reward, _ = self._calculate_total_reward(
                    diagnosis,
                    expert_label,
                    sample.get("context")
                )
                total_rewards.append(total_reward)
                
                # 检查准确性
                if diagnosis["disease_type"] == expert_label:
                    correct_predictions += 1
        
        accuracy = correct_predictions / len(test_data)
        avg_reward = sum(total_rewards) / len(total_rewards)
        
        print(f"   测试样本数：{len(test_data)}")
        print(f"   准确率：{accuracy:.4f}")
        print(f"   平均奖励：{avg_reward:.4f}")
        
        return {
            "status": "completed",
            "accuracy": accuracy,
            "avg_reward": avg_reward,
            "num_samples": len(test_data)
        }
    
    def _save_model(self) -> bool:
        """
        保存模型
        
        :return: 保存是否成功
        """
        try:
            # 保存策略网络
            policy_path = os.path.join(self.model_path, "policy_network.pt")
            torch.save({
                "model_state_dict": self.policy_network.state_dict(),
                "optimizer_state_dict": self.policy_optimizer.state_dict(),
                "training_history": self.training_history,
                "episode_rewards": self.episode_rewards,
                "config": self.config
            }, policy_path)
            
            # 保存奖励网络
            reward_path = os.path.join(self.model_path, "reward_network.pt")
            torch.save({
                "model_state_dict": self.reward_network.state_dict(),
                "optimizer_state_dict": self.reward_optimizer.state_dict()
            }, reward_path)
            
            # 保存训练历史
            history_path = os.path.join(self.model_path, "training_history.json")
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "training_history": self.training_history,
                    "episode_rewards": self.episode_rewards
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 模型已保存至：{self.model_path}")
            return True
        
        except Exception as e:
            print(f"✗ 模型保存失败：{e}")
            return False
    
    def _load_model(self) -> bool:
        """
        加载模型
        
        :return: 加载是否成功
        """
        policy_path = os.path.join(self.model_path, "policy_network.pt")
        
        if not os.path.exists(policy_path):
            print("ℹ️ 未找到已有模型，将使用随机初始化")
            return False
        
        try:
            # 加载策略网络
            checkpoint = torch.load(policy_path, map_location=self.config.device)
            self.policy_network.load_state_dict(checkpoint["model_state_dict"])
            self.policy_optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            self.training_history = checkpoint.get("training_history", [])
            self.episode_rewards = checkpoint.get("episode_rewards", [])
            
            # 加载奖励网络
            reward_path = os.path.join(self.model_path, "reward_network.pt")
            if os.path.exists(reward_path):
                reward_checkpoint = torch.load(reward_path, map_location=self.config.device)
                self.reward_network.load_state_dict(reward_checkpoint["model_state_dict"])
            
            print(f"✓ 模型已加载：{self.model_path}")
            return True
        
        except Exception as e:
            print(f"✗ 模型加载失败：{e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取训练统计信息
        
        :return: 统计字典
        """
        if not self.training_history:
            return {
                "status": "no_training",
                "message": "尚未进行训练"
            }
        
        return {
            "total_iterations": len(self.training_history),
            "final_reward": self.episode_rewards[-1] if self.episode_rewards else 0,
            "avg_reward": sum(self.episode_rewards) / len(self.episode_rewards) if self.episode_rewards else 0,
            "best_reward": max(self.episode_rewards) if self.episode_rewards else 0,
            "model_path": self.model_path,
            "device": self.config.device
        }


def test_grpo_trainer():
    """测试 GRPO 训练器"""
    print("=" * 60)
    print("🧪 测试 GRPOTrainer")
    print("=" * 60)
    
    # 初始化训练器
    config = GRPOConfig(
        hidden_size=128,
        num_layers=2,
        num_samples_per_state=3,
        learning_rate=1e-3,
        max_epochs=10
    )
    
    trainer = GRPOTrainer(
        input_size=512,
        num_disease_types=15,
        config=config
    )
    
    print("\n1️⃣ 初始状态")
    stats = trainer.get_statistics()
    print(f"   状态：{stats.get('status', 'unknown')}")
    
    print("\n2️⃣ 开始训练")
    train_result = trainer.train(num_iterations=20, batch_size=16)
    print(f"   训练状态：{train_result.get('status')}")
    print(f"   最终奖励：{train_result.get('final_reward', 0):.4f}")
    
    print("\n3️⃣ 模型评估")
    eval_result = trainer.evaluate()
    print(f"   评估状态：{eval_result.get('status')}")
    print(f"   准确率：{eval_result.get('accuracy', 0):.4f}")
    print(f"   平均奖励：{eval_result.get('avg_reward', 0):.4f}")
    
    print("\n4️⃣ 训练统计")
    stats = trainer.get_statistics()
    print(f"   总迭代次数：{stats.get('total_iterations', 0)}")
    print(f"   最终奖励：{stats.get('final_reward', 0):.4f}")
    print(f"   平均奖励：{stats.get('avg_reward', 0):.4f}")
    print(f"   最佳奖励：{stats.get('best_reward', 0):.4f}")
    
    print("\n" + "=" * 60)
    print("✅ GRPOTrainer 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_grpo_trainer()
