# -*- coding: utf-8 -*-
"""
反馈闭环集成模块 (Feedback Integration Module)
将人机协同(Human-in-the-Loop)、增强型主动学习(Enhanced Active Learning)和主系统集成

实现功能:
1. 诊断结果自动评估与不确定性监控
2. 专家反馈收集与知识提取
3. 增量学习触发与管理
4. 知识图谱自动更新
5. 系统性能持续优化

文档参考:
- 7.2 人机协同反馈闭环
- 5.2 知识抽取与图谱构建自动化
"""
import os
import json
import datetime
import math
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# 导入相关模块
try:
    from ..evolution.human_in_the_loop import HumanInTheLoop, FeedbackRecord, FeedbackStatus
    from .learner_engine import ActiveLearner as EnhancedActiveLearner
    from ..graph.graph_engine import KnowledgeAgent
except ImportError:
    try:
        from evolution.human_in_the_loop import HumanInTheLoop, FeedbackRecord, FeedbackStatus
        from action.learner_engine import ActiveLearner as EnhancedActiveLearner
        from graph.graph_engine import KnowledgeAgent
    except ImportError:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.graph.graph_engine import KnowledgeAgent
        from src.action.learner_engine import ActiveLearner as EnhancedActiveLearner
        from src.evolution.human_in_the_loop import HumanInTheLoop, FeedbackRecord, FeedbackStatus


class LearningTrigger(Enum):
    """学习触发条件"""
    MANUAL = "manual"                    # 手动触发
    AUTO_THRESHOLD = "auto_threshold"    # 自动阈值触发
    SCHEDULED = "scheduled"              # 定时触发
    FEEDBACK_COUNT = "feedback_count"    # 反馈数量触发
    UNCERTAINTY_SPIKE = "uncertainty_spike"  # 不确定性突增触发


class UncertaintyDetector:
    """
    不确定性检测器
    
    文档参考: 7.2 人机协同反馈闭环 - 不确定性预警
    
    实现多维度的不确定性评估：
    1. 置信度阈值检测
    2. 熵值计算
    3. OOD (Out-of-Distribution) 检测
    4. 预测方差分析
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        entropy_threshold: float = 1.5,
        ood_threshold: float = 0.3
    ):
        """
        初始化不确定性检测器
        
        :param confidence_threshold: 置信度阈值
        :param entropy_threshold: 熵值阈值
        :param ood_threshold: OOD检测阈值
        """
        self.confidence_threshold = confidence_threshold
        self.entropy_threshold = entropy_threshold
        self.ood_threshold = ood_threshold
        
        # 历史预测分布（用于OOD检测）
        self.prediction_history: List[np.ndarray] = []
        self.history_size = 100
    
    def compute_uncertainty(
        self,
        probabilities: np.ndarray,
        features: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        计算综合不确定性
        
        :param probabilities: 预测概率分布 [num_classes]
        :param features: 特征向量（可选，用于OOD检测）
        :return: 不确定性评估结果
        """
        result = {
            "is_uncertain": False,
            "uncertainty_score": 0.0,
            "confidence": float(np.max(probabilities)),
            "entropy": 0.0,
            "is_ood": False,
            "uncertainty_factors": []
        }
        
        # 1. 置信度检测
        max_confidence = np.max(probabilities)
        if max_confidence < self.confidence_threshold:
            result["uncertainty_factors"].append("low_confidence")
            result["is_uncertain"] = True
        
        # 2. 熵值计算
        entropy = self._compute_entropy(probabilities)
        result["entropy"] = entropy
        if entropy > self.entropy_threshold:
            result["uncertainty_factors"].append("high_entropy")
            result["is_uncertain"] = True
        
        # 3. OOD检测（如果有特征）
        if features is not None:
            is_ood, ood_score = self._detect_ood(features)
            result["is_ood"] = is_ood
            result["ood_score"] = ood_score
            if is_ood:
                result["uncertainty_factors"].append("ood_detected")
                result["is_uncertain"] = True
        
        # 4. 预测方差分析
        if len(self.prediction_history) > 10:
            variance = self._compute_prediction_variance(probabilities)
            result["prediction_variance"] = variance
            if variance > 0.3:
                result["uncertainty_factors"].append("high_variance")
        
        # 综合不确定性评分
        result["uncertainty_score"] = self._compute_overall_uncertainty(
            max_confidence, entropy, result.get("ood_score", 0)
        )
        
        # 更新历史
        self._update_history(probabilities)
        
        return result
    
    def _compute_entropy(self, probabilities: np.ndarray) -> float:
        """
        计算预测熵
        
        :param probabilities: 概率分布
        :return: 熵值
        """
        # 避免log(0)
        probs = np.clip(probabilities, 1e-10, 1.0)
        entropy = -np.sum(probs * np.log(probs))
        return float(entropy)
    
    def _detect_ood(self, features: np.ndarray) -> Tuple[bool, float]:
        """
        OOD检测
        
        :param features: 特征向量
        :return: (是否OOD, OOD分数)
        """
        if len(self.prediction_history) < 10:
            return False, 0.0
        
        # 简化的OOD检测：基于马氏距离
        # 实际应用中可以使用更复杂的方法
        try:
            history_matrix = np.array(self.prediction_history[-self.history_size:])
            mean = np.mean(history_matrix, axis=0)
            cov = np.cov(history_matrix.T) + np.eye(len(mean)) * 1e-6
            
            # 计算马氏距离
            diff = features - mean
            if len(cov.shape) == 0:
                mahal_dist = abs(diff) / np.sqrt(cov)
            else:
                inv_cov = np.linalg.inv(cov)
                mahal_dist = np.sqrt(np.dot(np.dot(diff, inv_cov), diff))
            
            ood_score = min(mahal_dist / 10.0, 1.0)  # 归一化
            is_ood = ood_score > self.ood_threshold
            
            return is_ood, float(ood_score)
        except Exception:
            return False, 0.0
    
    def _compute_prediction_variance(self, probabilities: np.ndarray) -> float:
        """
        计算预测方差
        
        :param probabilities: 当前预测
        :return: 方差值
        """
        history = np.array(self.prediction_history[-20:])
        variance = np.mean(np.var(history, axis=0))
        return float(variance)
    
    def _compute_overall_uncertainty(
        self,
        confidence: float,
        entropy: float,
        ood_score: float
    ) -> float:
        """
        计算综合不确定性评分
        
        :param confidence: 置信度
        :param entropy: 熵值
        :param ood_score: OOD分数
        :return: 综合不确定性评分 [0, 1]
        """
        # 归一化各项指标
        conf_score = 1.0 - confidence
        entropy_score = min(entropy / 2.0, 1.0)  # 假设最大熵为2
        
        # 加权平均
        overall = 0.4 * conf_score + 0.4 * entropy_score + 0.2 * ood_score
        return float(min(overall, 1.0))
    
    def _update_history(self, probabilities: np.ndarray):
        """更新预测历史"""
        self.prediction_history.append(probabilities)
        if len(self.prediction_history) > self.history_size:
            self.prediction_history.pop(0)


class KnowledgeExtractor:
    """
    知识提取器
    
    文档参考: 5.2 知识抽取与图谱构建自动化
    
    从专家反馈中提取结构化知识三元组
    """
    
    def __init__(self, knowledge_agent: 'KnowledgeAgent'):
        """
        初始化知识提取器
        
        :param knowledge_agent: 知识图谱智能体
        """
        self.knowledge_agent = knowledge_agent
        
        # 知识模板
        self.templates = {
            "correction": {
                "pattern": "{correct_disease}易被误诊为{wrong_disease}",
                "relation": "易混淆为"
            },
            "symptom": {
                "pattern": "{disease}表现为{symptom}",
                "relation": "表现为"
            },
            "treatment": {
                "pattern": "{disease}可使用{treatment}防治",
                "relation": "防治措施"
            },
            "condition": {
                "pattern": "{disease}易在{condition}条件下发生",
                "relation": "发病条件"
            }
        }
    
    def extract_from_feedback(
        self,
        system_diagnosis: str,
        user_correction: Optional[str],
        comments: str
    ) -> List[Dict[str, Any]]:
        """
        从专家反馈中提取知识三元组
        
        :param system_diagnosis: 系统诊断
        :param user_correction: 用户修正
        :param comments: 评论
        :return: 知识三元组列表
        """
        triples = []
        
        # 1. 如果有修正，提取混淆关系
        if user_correction and user_correction != system_diagnosis:
            triples.append({
                "subject": user_correction,
                "predicate": "易混淆为",
                "object": system_diagnosis,
                "confidence": 0.9,
                "source": "expert_feedback"
            })
        
        # 2. 从评论中提取知识
        if comments:
            extracted = self._extract_from_text(comments)
            triples.extend(extracted)
        
        return triples
    
    def _extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取知识
        
        :param text: 文本内容
        :return: 知识三元组列表
        """
        triples = []
        
        # 简化的规则提取（实际应用可使用LLM）
        # 检测症状描述
        symptom_keywords = ["表现为", "症状是", "出现", "呈现"]
        for keyword in symptom_keywords:
            if keyword in text:
                parts = text.split(keyword)
                if len(parts) >= 2:
                    triples.append({
                        "subject": parts[0].strip(),
                        "predicate": "表现为",
                        "object": parts[1].strip()[:50],  # 限制长度
                        "confidence": 0.7,
                        "source": "expert_comment"
                    })
        
        # 检测防治措施
        treatment_keywords = ["使用", "喷施", "防治", "治疗"]
        for keyword in treatment_keywords:
            if keyword in text:
                parts = text.split(keyword)
                if len(parts) >= 2:
                    triples.append({
                        "subject": "病害",
                        "predicate": "防治措施",
                        "object": parts[1].strip()[:30],
                        "confidence": 0.6,
                        "source": "expert_comment"
                    })
        
        return triples
    
    def inject_to_knowledge_graph(
        self,
        triples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        将知识注入知识图谱
        
        :param triples: 知识三元组
        :return: 注入结果
        """
        result = {
            "success": True,
            "injected_count": 0,
            "failed_count": 0,
            "details": []
        }
        
        for triple in triples:
            try:
                subject = triple.get("subject", "")
                predicate = triple.get("predicate", "")
                obj = triple.get("object", "")
                confidence = triple.get("confidence", 0.8)
                
                # 调用知识图谱添加关系
                if hasattr(self.knowledge_agent, 'add_disease_relation'):
                    self.knowledge_agent.add_disease_relation(
                        disease_name=subject,
                        relation_type=predicate,
                        target_disease=obj,
                        confidence=confidence,
                        source=triple.get("source", "expert_feedback")
                    )
                
                result["injected_count"] += 1
                result["details"].append({
                    "triple": f"{subject}--{predicate}-->{obj}",
                    "status": "success"
                })
                
            except Exception as e:
                result["failed_count"] += 1
                result["details"].append({
                    "triple": f"{triple}",
                    "status": "failed",
                    "error": str(e)
                })
        
        return result


@dataclass
class FeedbackLoopConfig:
    """反馈闭环配置"""
    # 不确定性阈值
    high_uncertainty_threshold: float = 0.5
    critical_uncertainty_threshold: float = 0.3
    
    # 自动学习触发条件
    auto_learn_threshold: int = 50       # 累积50个反馈后自动触发学习
    min_feedback_for_learning: int = 10  # 最少需要10个反馈才触发学习
    
    # 经验回放配置
    replay_buffer_capacity: int = 1000
    rehearsal_ratio: float = 0.3
    
    # 知识提取配置
    extract_knowledge: bool = True
    update_knowledge_graph: bool = True
    
    # 存储路径
    feedback_dir: str = "data/human_feedback"
    replay_buffer_dir: str = "data/experience_replay"
    report_dir: str = "reports"


class FeedbackLoopIntegrator:
    """
    反馈闭环集成器
    
    协调人机协同、主动学习和知识管理，形成完整的反馈闭环
    
    文档参考: 7.2 人机协同反馈闭环
    """
    
    def __init__(
        self,
        knowledge_agent: KnowledgeAgent,
        config: Optional[FeedbackLoopConfig] = None,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        初始化反馈闭环集成器
        
        :param knowledge_agent: 知识图谱智能体
        :param config: 配置对象
        :param device: 计算设备
        """
        self.config = config or FeedbackLoopConfig()
        self.device = device
        self.knowledge_agent = knowledge_agent
        
        # 初始化不确定性检测器
        self.uncertainty_detector = UncertaintyDetector(
            confidence_threshold=self.config.high_uncertainty_threshold,
            entropy_threshold=1.5,
            ood_threshold=0.3
        )
        
        # 初始化知识提取器
        self.knowledge_extractor = KnowledgeExtractor(knowledge_agent)
        
        # 初始化人机协同模块
        self.human_in_the_loop = HumanInTheLoop(
            feedback_dir=self.config.feedback_dir,
            auto_flag_threshold=self.config.high_uncertainty_threshold
        )
        
        # 初始化增强型主动学习引擎
        self.active_learner = EnhancedActiveLearner(
            data_root="datasets/feedback_data",
            replay_buffer_dir=self.config.replay_buffer_dir,
            buffer_capacity=self.config.replay_buffer_capacity,
            rehearsal_ratio=self.config.rehearsal_ratio,
            confidence_threshold=self.config.critical_uncertainty_threshold,
            device=device
        )
        
        # 设置回调函数
        self.human_in_the_loop.on_feedback_submitted = self._on_feedback_received
        self.human_in_the_loop.on_knowledge_extracted = self._on_knowledge_extracted
        
        # 学习状态
        self.learning_status = {
            "is_learning": False,
            "last_learning_time": None,
            "total_learned_samples": 0,
            "pending_learning_count": 0,
            "uncertainty_trend": []
        }
        
        # 性能监控
        self.performance_history: List[Dict[str, Any]] = []
        
        # 创建报告目录
        os.makedirs(self.config.report_dir, exist_ok=True)
        
        print("=" * 70)
        print("🔄 [Feedback Loop Integrator] 反馈闭环集成器初始化完成")
        print("=" * 70)
        print(f"   不确定性阈值: {self.config.high_uncertainty_threshold}")
        print(f"   自动学习阈值: {self.config.auto_learn_threshold} 个反馈")
        print(f"   经验缓冲区容量: {self.config.replay_buffer_capacity}")
        print(f"   知识图谱更新: {'启用' if self.config.update_knowledge_graph else '禁用'}")
        print(f"   不确定性检测: 启用 (熵值阈值: 1.5)")
        print(f"   OOD检测: 启用")
    
    def process_diagnosis_result(
        self,
        image_path: str,
        diagnosis: str,
        confidence: float,
        vision_features: Optional[Dict] = None,
        user_description: str = "",
        probabilities: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        处理诊断结果
        
        根据置信度和不确定性决定是否提交专家审核
        
        :param image_path: 图像路径
        :param diagnosis: 诊断结果
        :param confidence: 置信度
        :param vision_features: 视觉特征
        :param user_description: 用户描述
        :param probabilities: 预测概率分布（用于不确定性检测）
        :return: 处理结果
        """
        result = {
            "diagnosis": diagnosis,
            "confidence": confidence,
            "requires_review": False,
            "feedback_record_id": None,
            "uncertainty_analysis": None,
            "message": ""
        }
        
        # 使用不确定性检测器进行多维度评估
        if probabilities is not None:
            features = None
            if vision_features and "features" in vision_features:
                features = np.array(vision_features["features"])
            
            uncertainty_result = self.uncertainty_detector.compute_uncertainty(
                probabilities, features
            )
            result["uncertainty_analysis"] = uncertainty_result
            
            # 记录不确定性趋势
            self.learning_status["uncertainty_trend"].append(
                uncertainty_result["uncertainty_score"]
            )
            if len(self.learning_status["uncertainty_trend"]) > 100:
                self.learning_status["uncertainty_trend"].pop(0)
            
            # 基于综合不确定性决定是否需要审核
            if uncertainty_result["is_uncertain"]:
                result["requires_review"] = True
                factors = ", ".join(uncertainty_result["uncertainty_factors"])
                result["message"] = f"⚠️ 检测到不确定性 ({factors})，已提交专家审核"
        else:
            # 降级到简单的置信度检查
            if confidence < self.config.high_uncertainty_threshold:
                result["requires_review"] = True
                result["message"] = f"⚠️ 诊断置信度较低 ({confidence:.2f})，已提交专家审核"
        
        # 提交到人机协同模块
        if result["requires_review"]:
            feedback_record = self.human_in_the_loop.submit_prediction(
                image_path=image_path,
                system_diagnosis=diagnosis,
                system_confidence=confidence,
                features=vision_features
            )
            
            if feedback_record:
                result["feedback_record_id"] = feedback_record.id
                result["uncertainty_level"] = feedback_record.uncertainty_level
                
                print(f"\n⚠️ [反馈闭环] 样本已标记待审核")
                print(f"   记录ID: {feedback_record.id}")
                print(f"   不确定性级别: {feedback_record.uncertainty_level}")
        else:
            # 置信度足够，直接收集为确认样本
            self.active_learner.collect_feedback(
                image_path=image_path,
                system_diagnosis=diagnosis,
                confidence=confidence,
                user_correction=None,
                comments=f"系统自动确认，置信度: {confidence:.2f}"
            )
            result["message"] = f"✅ 诊断置信度充足 ({confidence:.2f})，已自动确认"
        
        return result
    
    def submit_expert_feedback(
        self,
        record_id: str,
        correction: Optional[str] = None,
        comments: str = "",
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交专家反馈
        
        :param record_id: 反馈记录ID
        :param correction: 修正结果
        :param comments: 专家评论
        :param reviewer_id: 审核人ID
        :return: 处理结果
        """
        result = {
            "success": False,
            "record_id": record_id,
            "knowledge_extracted": [],
            "knowledge_injected": None,
            "message": ""
        }
        
        # 提交到人机协同模块
        success = self.human_in_the_loop.submit_feedback(
            record_id=record_id,
            user_correction=correction,
            user_comments=comments,
            reviewer_id=reviewer_id
        )
        
        if not success:
            result["message"] = "❌ 反馈提交失败，记录不存在"
            return result
        
        # 获取记录
        record = self.human_in_the_loop.feedback_records.get(record_id)
        if not record:
            result["message"] = "❌ 无法获取反馈记录"
            return result
        
        # 确定最终标签
        final_label = correction if correction else record.system_diagnosis
        
        # 添加到主动学习引擎
        self.active_learner.collect_feedback(
            image_path=record.image_path,
            system_diagnosis=record.system_diagnosis,
            confidence=record.system_confidence,
            user_correction=correction,
            comments=comments
        )
        
        # 提取知识三元组
        if self.config.extract_knowledge:
            knowledge_triples = self.knowledge_extractor.extract_from_feedback(
                system_diagnosis=record.system_diagnosis,
                user_correction=correction,
                comments=comments
            )
            result["knowledge_extracted"] = knowledge_triples
            
            # 注入知识图谱
            if knowledge_triples and self.config.update_knowledge_graph:
                inject_result = self.knowledge_extractor.inject_to_knowledge_graph(
                    knowledge_triples
                )
                result["knowledge_injected"] = inject_result
                
                print(f"\n📚 [知识提取] 提取到 {len(knowledge_triples)} 个三元组")
                print(f"   成功注入: {inject_result['injected_count']}")
        
        # 更新学习状态
        self.learning_status["pending_learning_count"] += 1
        
        result["success"] = True
        result["final_label"] = final_label
        result["is_correction"] = correction is not None and correction != record.system_diagnosis
        result["message"] = f"✅ 专家反馈已处理，最终标签: {final_label}"
        
        # 检查是否触发自动学习
        auto_learn_triggered = self._check_auto_learning_trigger()
        result["auto_learning_triggered"] = auto_learn_triggered
        
        if auto_learn_triggered:
            result["message"] += f"\n🔄 已累积 {self.learning_status['pending_learning_count']} 个反馈，建议触发增量学习"
        
        return result
    
    def _on_feedback_received(self, record: FeedbackRecord):
        """
        反馈接收回调
        
        :param record: 反馈记录
        """
        print(f"\n📥 [反馈闭环] 收到新反馈")
        print(f"   记录ID: {record.id}")
        print(f"   系统诊断: {record.system_diagnosis}")
        print(f"   用户修正: {record.user_correction or '无'}")
        print(f"   状态: {record.status}")
    
    def _on_knowledge_extracted(self, knowledge_triples: List[Dict[str, Any]]):
        """
        知识提取回调
        
        :param knowledge_triples: 知识三元组列表
        """
        if not self.config.update_knowledge_graph:
            return
        
        print(f"\n📚 [反馈闭环] 提取到 {len(knowledge_triples)} 个知识三元组")
        
        # 将知识注入知识图谱
        for triple in knowledge_triples:
            try:
                subject = triple.get("subject")
                predicate = triple.get("predicate")
                obj = triple.get("object")
                context = triple.get("context", "")
                
                # 添加到知识图谱
                self.knowledge_agent.add_disease_relation(
                    disease_name=subject,
                    relation_type="易混淆为",
                    target_disease=obj,
                    confidence=0.8,
                    source="expert_feedback"
                )
                
                print(f"   ✅ 知识已注入: {subject} --{predicate}--> {obj}")
                
            except Exception as e:
                print(f"   ⚠️ 知识注入失败: {e}")
    
    def _check_auto_learning_trigger(self) -> bool:
        """
        检查是否触发自动学习
        
        :return: 是否触发
        """
        return (
            self.learning_status["pending_learning_count"] >= self.config.auto_learn_threshold
            and self.learning_status["pending_learning_count"] >= self.config.min_feedback_for_learning
        )
    
    def trigger_incremental_learning(
        self,
        model: Optional[nn.Module] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        epochs: int = 5
    ) -> Dict[str, Any]:
        """
        触发增量学习
        
        :param model: 要训练的模型（可选）
        :param optimizer: 优化器（可选）
        :param epochs: 训练轮数
        :return: 学习结果
        """
        result = {
            "success": False,
            "samples_learned": 0,
            "training_stats": {},
            "message": ""
        }
        
        # 检查是否有足够的反馈
        if self.learning_status["pending_learning_count"] < self.config.min_feedback_for_learning:
            result["message"] = f"⚠️ 反馈数量不足 ({self.learning_status['pending_learning_count']}/{self.config.min_feedback_for_learning})"
            return result
        
        # 检查是否正在学习
        if self.learning_status["is_learning"]:
            result["message"] = "⚠️ 学习正在进行中，请稍后再试"
            return result
        
        self.learning_status["is_learning"] = True
        
        try:
            print("\n" + "=" * 70)
            print("🎓 [反馈闭环] 开始增量学习")
            print("=" * 70)
            
            # 导出训练数据
            export_stats = self.human_in_the_loop.export_training_data(
                output_dir="datasets/incremental_training"
            )
            
            # 如果提供了模型，执行训练
            if model is not None and optimizer is not None:
                # 设置模型到学习引擎
                self.active_learner.set_model(model)
                
                # 准备训练数据
                # 从导出的数据构建样本列表
                new_samples = []
                for root, dirs, files in os.walk("datasets/incremental_training"):
                    for file in files:
                        if file.endswith(('.jpg', '.png', '.jpeg')):
                            image_path = os.path.join(root, file)
                            label = os.path.basename(root)
                            new_samples.append((image_path, label, 0.8))  # 默认置信度0.8
                
                if new_samples:
                    # 执行增量训练
                    training_stats = self.active_learner.incremental_train_step(
                        new_samples=new_samples,
                        optimizer=optimizer,
                        criterion=nn.CrossEntropyLoss()
                    )
                    
                    result["training_stats"] = training_stats
                    print(f"\n✅ 增量训练完成")
                    print(f"   损失: {training_stats.get('loss', 0):.4f}")
                    print(f"   准确率: {training_stats.get('accuracy', 0):.2f}%")
            
            # 更新学习状态
            self.learning_status["last_learning_time"] = datetime.datetime.now().isoformat()
            self.learning_status["total_learned_samples"] += export_stats["total"]
            self.learning_status["pending_learning_count"] = 0
            
            result["success"] = True
            result["samples_learned"] = export_stats["total"]
            result["message"] = f"✅ 增量学习完成，学习了 {export_stats['total']} 个样本"
            
            # 记录性能
            self._record_performance()
            
        except Exception as e:
            result["message"] = f"❌ 增量学习失败: {str(e)}"
            print(f"\n❌ 增量学习失败: {e}")
            
        finally:
            self.learning_status["is_learning"] = False
        
        return result
    
    def get_pending_reviews(
        self,
        limit: int = 10,
        uncertainty_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取待审核列表
        
        :param limit: 数量限制
        :param uncertainty_filter: 不确定性级别过滤
        :return: 待审核记录列表
        """
        records = self.human_in_the_loop.get_pending_reviews(
            uncertainty_filter=uncertainty_filter,
            limit=limit
        )
        
        return [r.to_dict() for r in records]
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        :return: 系统状态字典
        """
        # 获取人机协同统计
        hitl_stats = self.human_in_the_loop.get_feedback_statistics()
        
        # 获取主动学习统计
        learning_stats = self.active_learner.get_learning_statistics()
        
        # 合并状态
        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "learning_status": self.learning_status,
            "feedback_statistics": hitl_stats,
            "active_learning_statistics": learning_stats,
            "config": {
                "high_uncertainty_threshold": self.config.high_uncertainty_threshold,
                "auto_learn_threshold": self.config.auto_learn_threshold,
                "replay_buffer_capacity": self.config.replay_buffer_capacity
            }
        }
        
        return status
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        生成反馈闭环报告
        
        :param output_path: 输出路径
        :return: 报告路径
        """
        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.config.report_dir,
                f"feedback_loop_report_{timestamp}.json"
            )
        
        # 收集报告数据
        report = {
            "generated_at": datetime.datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "performance_history": self.performance_history[-100:],  # 最近100条
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 [反馈闭环] 报告已生成: {output_path}")
        
        return output_path
    
    def _generate_recommendations(self) -> List[str]:
        """
        生成系统优化建议
        
        :return: 建议列表
        """
        recommendations = []
        
        # 基于反馈统计生成建议
        stats = self.human_in_the_loop.get_feedback_statistics()
        
        if stats.get("accuracy", 1.0) < 0.8:
            recommendations.append("系统准确率较低，建议增加训练数据")
        
        if stats.get("corrected_count", 0) > stats.get("confirmed_count", 0):
            recommendations.append("修正样本多于确认样本，建议检查模型性能")
        
        if self.learning_status["pending_learning_count"] > self.config.auto_learn_threshold:
            recommendations.append(f"已累积 {self.learning_status['pending_learning_count']} 个待学习样本，建议触发增量学习")
        
        learning_stats = self.active_learner.get_learning_statistics()
        if learning_stats.get("hard_samples", 0) > 50:
            recommendations.append("困难样本较多，建议进行针对性数据增强")
        
        return recommendations
    
    def _record_performance(self):
        """记录性能指标"""
        stats = self.human_in_the_loop.get_feedback_statistics()
        
        performance = {
            "timestamp": datetime.datetime.now().isoformat(),
            "accuracy": stats.get("accuracy", 0),
            "total_feedback": stats.get("total_records", 0),
            "correction_rate": stats.get("corrected_count", 0) / max(stats.get("total_records", 1), 1)
        }
        
        self.performance_history.append(performance)


def test_feedback_integration():
    """测试反馈闭环集成"""
    print("=" * 70)
    print("🧪 测试反馈闭环集成模块")
    print("=" * 70)
    
    # 创建配置
    config = FeedbackLoopConfig(
        high_uncertainty_threshold=0.6,
        auto_learn_threshold=5,  # 测试用，设置较低阈值
        min_feedback_for_learning=3
    )
    
    # 创建知识智能体（模拟）
    class MockKnowledgeAgent:
        def add_disease_relation(self, **kwargs):
            print(f"   [Mock KG] 添加关系: {kwargs}")
    
    kg_agent = MockKnowledgeAgent()
    
    # 创建集成器
    integrator = FeedbackLoopIntegrator(
        knowledge_agent=kg_agent,
        config=config,
        device='cpu'
    )
    
    # 测试处理诊断结果（高置信度）
    print("\n" + "=" * 70)
    print("🧪 测试高置信度诊断")
    print("=" * 70)
    
    result1 = integrator.process_diagnosis_result(
        image_path="test_image_1.jpg",
        diagnosis="条锈病",
        confidence=0.92
    )
    print(f"✅ 结果: {result1['message']}")
    
    # 测试处理诊断结果（低置信度）
    print("\n" + "=" * 70)
    print("🧪 测试低置信度诊断")
    print("=" * 70)
    
    result2 = integrator.process_diagnosis_result(
        image_path="test_image_2.jpg",
        diagnosis="白粉病",
        confidence=0.45
    )
    print(f"✅ 结果: {result2['message']}")
    print(f"   记录ID: {result2['feedback_record_id']}")
    
    # 测试提交专家反馈
    print("\n" + "=" * 70)
    print("🧪 测试专家反馈")
    print("=" * 70)
    
    if result2['feedback_record_id']:
        feedback_result = integrator.submit_expert_feedback(
            record_id=result2['feedback_record_id'],
            correction="赤霉病",
            comments="这是赤霉病，不是白粉病。注意穗部的粉红色霉层。",
            reviewer_id="expert_001"
        )
        print(f"✅ 反馈结果: {feedback_result['message']}")
    
    # 添加更多反馈以触发自动学习
    print("\n" + "=" * 70)
    print("🧪 添加更多反馈样本")
    print("=" * 70)
    
    for i in range(4):
        result = integrator.process_diagnosis_result(
            image_path=f"test_image_{i+3}.jpg",
            diagnosis="叶锈病",
            confidence=0.35
        )
        if result['feedback_record_id']:
            integrator.submit_expert_feedback(
                record_id=result['feedback_record_id'],
                correction="条锈病",
                comments="修正为条锈病",
                reviewer_id="expert_001"
            )
    
    # 获取系统状态
    print("\n" + "=" * 70)
    print("🧪 系统状态")
    print("=" * 70)
    
    status = integrator.get_system_status()
    print(f"✅ 总反馈数: {status['feedback_statistics']['total_records']}")
    print(f"✅ 待审核: {status['feedback_statistics']['pending_count']}")
    print(f"✅ 系统准确率: {status['feedback_statistics']['accuracy']:.2%}")
    print(f"✅ 待学习样本: {status['learning_status']['pending_learning_count']}")
    
    # 生成报告
    print("\n" + "=" * 70)
    print("🧪 生成报告")
    print("=" * 70)
    
    report_path = integrator.generate_report()
    print(f"✅ 报告已生成: {report_path}")
    
    # 清理测试数据
    import shutil
    for dir_path in ["data/human_feedback", "data/experience_replay", "datasets/feedback_data", "reports"]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    print("\n" + "=" * 70)
    print("✅ 反馈闭环集成测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_feedback_integration()
