# -*- coding: utf-8 -*-
"""
反馈处理机制 - Feedback Handler
IWDDA Agent 反馈记忆层核心组件，负责处理用户反馈并调整诊断策略

功能特性:
1. 用户反馈解析：解析用户反馈类型（采纳建议、施药情况、病情变化）
2. 反馈→策略调整映射：根据反馈调整诊断策略和推荐方案
3. 反馈分类处理：区分不同类型的反馈并采取相应措施
4. 策略调整规则：基于反馈自动调整诊断置信度、推荐方案等
5. 与 CaseMemory 集成：将反馈结果存储到病例记忆中

反馈类型:
- 采纳建议：用户采纳了推荐的防治方案
- 未采纳：用户未采纳推荐方案
- 部分采纳：用户部分采纳了推荐方案
- 施药有效：施药后病情好转
- 施药无效：施药后病情无改善
- 病情恶化：病情加重
- 病情缓解：病情自然好转
- 需要人工复核：系统无法处理，需要人工介入

策略调整:
- 提高/降低诊断置信度
- 调整推荐方案优先级
- 标记需要人工复核的案例
- 生成新的防治建议

使用示例:
    from src.memory import FeedbackHandler, CaseMemory
    
    # 初始化
    case_memory = CaseMemory()
    feedback_handler = FeedbackHandler(case_memory=case_memory)
    
    # 处理用户反馈
    result = feedback_handler.process_feedback(
        case_id="CASE_20260309_001",
        feedback_type="施药有效",
        details="使用三唑酮后，病斑明显减少",
        medication_name="三唑酮可湿性粉剂"
    )
    
    # 获取策略调整建议
    adjustments = feedback_handler.get_strategy_adjustments(
        disease_type="条锈病",
        feedback_history=[...]
    )
    
    # 调整诊断策略
    feedback_handler.apply_strategy_adjustment(
        disease_type="条锈病",
        adjustment_type="提高置信度",
        adjustment_value=0.05
    )
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 尝试导入 CaseMemory，如果失败则使用 None
try:
    from .case_memory import CaseMemory
except ImportError:
    CaseMemory = None


class FeedbackType(Enum):
    """反馈类型枚举"""
    ADOPTED = "采纳建议"
    NOT_ADOPTED = "未采纳"
    PARTIALLY_ADOPTED = "部分采纳"
    MEDICATION_EFFECTIVE = "施药有效"
    MEDICATION_INEFFECTIVE = "施药无效"
    DISEASE_WORSENED = "病情恶化"
    DISEASE_IMPROVED = "病情缓解"
    NEEDS_MANUAL_REVIEW = "需要人工复核"


class StrategyAdjustmentType(Enum):
    """策略调整类型枚举"""
    CONFIDENCE_UP = "提高置信度"
    CONFIDENCE_DOWN = "降低置信度"
    PRIORITY_UP = "提高优先级"
    PRIORITY_DOWN = "降低优先级"
    ADD_MANUAL_REVIEW = "添加人工复核标记"
    UPDATE_RECOMMENDATION = "更新推荐方案"
    NO_ADJUSTMENT = "无需调整"


class FeedbackHandler:
    """
    反馈处理器类
    
    负责处理用户反馈并调整诊断策略：
    - 解析用户反馈
    - 映射反馈到策略调整
    - 更新病例记忆
    - 生成策略调整建议
    - 与 CaseMemory 集成
    """
    
    def __init__(self, case_memory: Optional[Any] = None, config_path: Optional[str] = None):
        """
        初始化反馈处理器
        
        :param case_memory: CaseMemory 实例（可选）
        :param config_path: 配置文件路径（可选）
        """
        self.case_memory = case_memory
        self.config_path = config_path
        
        # 反馈处理统计
        self._feedback_history: List[Dict[str, Any]] = []
        self._strategy_adjustments: Dict[str, Dict[str, Any]] = {}
        
        # 反馈→策略调整映射规则
        self._feedback_to_strategy_map = self._init_feedback_strategy_map()
        
        # 病害策略配置
        self._disease_strategies = self._init_disease_strategies()
        
        # 加载配置（如果提供）
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        
        print(f"[FeedbackHandler] 反馈处理器初始化完成")
    
    def _init_feedback_strategy_map(self) -> Dict[str, Dict[str, Any]]:
        """
        初始化反馈到策略调整的映射规则
        
        :return: 映射规则字典
        """
        return {
            FeedbackType.ADOPTED.value: {
                "description": "用户采纳了推荐方案",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.CONFIDENCE_UP.value,
                        "value": 0.02,
                        "reason": "用户采纳表明诊断可能准确"
                    }
                ],
                "auto_apply": True
            },
            FeedbackType.NOT_ADOPTED.value: {
                "description": "用户未采纳推荐方案",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.CONFIDENCE_DOWN.value,
                        "value": 0.05,
                        "reason": "用户未采纳，诊断可能需要调整"
                    }
                ],
                "auto_apply": False,
                "requires_review": True
            },
            FeedbackType.PARTIALLY_ADOPTED.value: {
                "description": "用户部分采纳推荐方案",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.UPDATE_RECOMMENDATION.value,
                        "reason": "需要根据用户反馈优化推荐方案"
                    }
                ],
                "auto_apply": False
            },
            FeedbackType.MEDICATION_EFFECTIVE.value: {
                "description": "施药后病情好转",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.CONFIDENCE_UP.value,
                        "value": 0.05,
                        "reason": "施药有效验证了诊断准确性"
                    },
                    {
                        "type": StrategyAdjustmentType.PRIORITY_UP.value,
                        "value": 0.1,
                        "reason": "该药剂对该病害有效，提高推荐优先级"
                    }
                ],
                "auto_apply": True
            },
            FeedbackType.MEDICATION_INEFFECTIVE.value: {
                "description": "施药后病情无改善",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.CONFIDENCE_DOWN.value,
                        "value": 0.1,
                        "reason": "施药无效，诊断可能不准确或药剂不对症"
                    },
                    {
                        "type": StrategyAdjustmentType.PRIORITY_DOWN.value,
                        "value": 0.15,
                        "reason": "该药剂效果不佳，降低推荐优先级"
                    },
                    {
                        "type": StrategyAdjustmentType.UPDATE_RECOMMENDATION.value,
                        "reason": "需要更新推荐方案"
                    }
                ],
                "auto_apply": False,
                "requires_review": True
            },
            FeedbackType.DISEASE_WORSENED.value: {
                "description": "病情恶化",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.CONFIDENCE_DOWN.value,
                        "value": 0.08,
                        "reason": "病情恶化表明诊断或推荐可能不当"
                    },
                    {
                        "type": StrategyAdjustmentType.ADD_MANUAL_REVIEW.value,
                        "reason": "病情恶化需要人工复核"
                    }
                ],
                "auto_apply": False,
                "requires_review": True,
                "urgent": True
            },
            FeedbackType.DISEASE_IMPROVED.value: {
                "description": "病情缓解",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.CONFIDENCE_UP.value,
                        "value": 0.03,
                        "reason": "病情自然好转，诊断可能准确"
                    }
                ],
                "auto_apply": True
            },
            FeedbackType.NEEDS_MANUAL_REVIEW.value: {
                "description": "需要人工复核",
                "adjustments": [
                    {
                        "type": StrategyAdjustmentType.ADD_MANUAL_REVIEW.value,
                        "reason": "系统无法处理，需要人工介入"
                    }
                ],
                "auto_apply": False,
                "requires_review": True,
                "urgent": True
            }
        }
    
    def _init_disease_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        初始化病害诊断策略配置
        
        :return: 病害策略字典
        """
        return {
            "条锈病": {
                "base_confidence": 0.8,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "三唑酮可湿性粉剂", "priority": 1.0, "effectiveness": 0.85},
                    {"name": "烯唑醇可湿性粉剂", "priority": 0.9, "effectiveness": 0.82},
                    {"name": "戊唑醇乳油", "priority": 0.8, "effectiveness": 0.80}
                ],
                "manual_review_count": 0
            },
            "叶锈病": {
                "base_confidence": 0.75,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "三唑酮可湿性粉剂", "priority": 1.0, "effectiveness": 0.80},
                    {"name": "腈菌唑乳油", "priority": 0.9, "effectiveness": 0.78}
                ],
                "manual_review_count": 0
            },
            "秆锈病": {
                "base_confidence": 0.75,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "烯唑醇可湿性粉剂", "priority": 1.0, "effectiveness": 0.83}
                ],
                "manual_review_count": 0
            },
            "白粉病": {
                "base_confidence": 0.85,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "多菌灵可湿性粉剂", "priority": 1.0, "effectiveness": 0.88},
                    {"name": "甲基硫菌灵可湿性粉剂", "priority": 0.9, "effectiveness": 0.85}
                ],
                "manual_review_count": 0
            },
            "赤霉病": {
                "base_confidence": 0.80,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "多菌灵可湿性粉剂", "priority": 1.0, "effectiveness": 0.82},
                    {"name": "戊唑醇乳油", "priority": 0.9, "effectiveness": 0.80}
                ],
                "manual_review_count": 0
            },
            "纹枯病": {
                "base_confidence": 0.78,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "井冈霉素水剂", "priority": 1.0, "effectiveness": 0.85}
                ],
                "manual_review_count": 0
            },
            "全蚀病": {
                "base_confidence": 0.72,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "硅噻菌胺悬浮剂", "priority": 1.0, "effectiveness": 0.75}
                ],
                "manual_review_count": 0
            },
            "黄矮病": {
                "base_confidence": 0.70,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "吡虫啉可湿性粉剂", "priority": 1.0, "effectiveness": 0.78}
                ],
                "manual_review_count": 0
            },
            "丛矮病": {
                "base_confidence": 0.68,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "盐酸吗啉胍可湿性粉剂", "priority": 1.0, "effectiveness": 0.72}
                ],
                "manual_review_count": 0
            },
            "蚜虫": {
                "base_confidence": 0.88,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "吡虫啉可湿性粉剂", "priority": 1.0, "effectiveness": 0.90},
                    {"name": "啶虫脒乳油", "priority": 0.9, "effectiveness": 0.88}
                ],
                "manual_review_count": 0
            },
            "红蜘蛛": {
                "base_confidence": 0.85,
                "confidence_adjustment": 0.0,
                "recommendation_priority": 1.0,
                "recommended_medications": [
                    {"name": "阿维菌素乳油", "priority": 1.0, "effectiveness": 0.88},
                    {"name": "哒螨灵可湿性粉剂", "priority": 0.9, "effectiveness": 0.85}
                ],
                "manual_review_count": 0
            }
        }
    
    def _load_config(self, config_path: str) -> bool:
        """
        加载配置文件
        
        :param config_path: 配置文件路径
        :return: 加载是否成功
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新病害策略
            if "disease_strategies" in config:
                self._disease_strategies.update(config["disease_strategies"])
            
            # 更新反馈映射
            if "feedback_strategy_map" in config:
                self._feedback_to_strategy_map.update(config["feedback_strategy_map"])
            
            print(f"[FeedbackHandler] 成功加载配置文件：{config_path}")
            return True
        
        except Exception as e:
            print(f"[FeedbackHandler] 加载配置文件失败：{e}")
            return False
    
    def _save_config(self, config_path: str) -> bool:
        """
        保存配置文件
        
        :param config_path: 配置文件路径
        :return: 保存是否成功
        """
        try:
            config = {
                "disease_strategies": self._disease_strategies,
                "feedback_strategy_map": self._feedback_to_strategy_map,
                "last_updated": datetime.now().isoformat()
            }
            
            # 确保目录存在
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"[FeedbackHandler] 配置文件已保存：{config_path}")
            return True
        
        except Exception as e:
            print(f"[FeedbackHandler] 保存配置文件失败：{e}")
            return False
    
    def parse_feedback(
        self,
        feedback_text: str,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解析用户反馈文本（从自然语言中提取反馈信息）
        
        :param feedback_text: 用户反馈文本
        :param case_id: 病例 ID（可选）
        :return: 解析后的反馈信息字典
        """
        result = {
            "case_id": case_id,
            "feedback_text": feedback_text,
            "parsed_type": None,
            "confidence": 0.0,
            "medication_info": None,
            "disease_status": None,
            "details": feedback_text
        }
        
        # 关键词匹配（简化版本，可扩展为 NLP 模型）
        feedback_lower = feedback_text.lower()
        
        # 检测反馈类型
        if any(kw in feedback_text for kw in ["采纳", "采用", "使用", "按照"]):
            result["parsed_type"] = FeedbackType.ADOPTED.value
            result["confidence"] = 0.8
        
        if any(kw in feedback_text for kw in ["未采纳", "没用", "没采用"]):
            result["parsed_type"] = FeedbackType.NOT_ADOPTED.value
            result["confidence"] = 0.8
        
        if any(kw in feedback_text for kw in ["部分采纳", "用了一部分"]):
            result["parsed_type"] = FeedbackType.PARTIALLY_ADOPTED.value
            result["confidence"] = 0.75
        
        if any(kw in feedback_text for kw in ["好转", "改善", "有效", "减轻", "减少"]):
            result["disease_status"] = "改善"
            if any(kw in feedback_text for kw in ["药", "施药", "喷洒"]):
                result["parsed_type"] = FeedbackType.MEDICATION_EFFECTIVE.value
                result["confidence"] = 0.85
        
        if any(kw in feedback_text for kw in ["无效", "没效果", "没好转", "没变化"]):
            result["disease_status"] = "无变化"
            if any(kw in feedback_text for kw in ["药", "施药", "喷洒"]):
                result["parsed_type"] = FeedbackType.MEDICATION_INEFFECTIVE.value
                result["confidence"] = 0.85
        
        if any(kw in feedback_text for kw in ["恶化", "加重", "更严重", "扩散"]):
            result["parsed_type"] = FeedbackType.DISEASE_WORSENED.value
            result["disease_status"] = "恶化"
            result["confidence"] = 0.9
        
        if any(kw in feedback_text for kw in ["缓解", "自然好转"]):
            result["parsed_type"] = FeedbackType.DISEASE_IMPROVED.value
            result["disease_status"] = "缓解"
            result["confidence"] = 0.75
        
        if any(kw in feedback_text for kw in ["人工", "专家", "复核", "复查"]):
            result["parsed_type"] = FeedbackType.NEEDS_MANUAL_REVIEW.value
            result["confidence"] = 0.95
        
        # 提取药剂信息
        medication_keywords = ["三唑酮", "烯唑醇", "戊唑醇", "多菌灵", "吡虫啉", "阿维菌素"]
        for med in medication_keywords:
            if med in feedback_text:
                result["medication_info"] = {"name": med}
                break
        
        # 如果未匹配到类型，使用默认
        if not result["parsed_type"]:
            result["parsed_type"] = FeedbackType.ADOPTED.value
            result["confidence"] = 0.5
        
        print(f"[FeedbackHandler] 反馈解析完成：{result['parsed_type']} (置信度：{result['confidence']:.2f})")
        return result
    
    def process_feedback(
        self,
        case_id: str,
        feedback_type: str,
        details: str = "",
        medication_name: Optional[str] = None,
        medication_applied: bool = False,
        disease_status: Optional[str] = None,
        auto_apply_adjustment: bool = True
    ) -> Dict[str, Any]:
        """
        处理用户反馈（核心方法）
        
        :param case_id: 病例 ID
        :param feedback_type: 反馈类型（采纳建议/施药有效/病情恶化等）
        :param details: 反馈详细信息
        :param medication_name: 施药名称
        :param medication_applied: 是否已施药
        :param disease_status: 病情状态（改善/恶化/稳定）
        :param auto_apply_adjustment: 是否自动应用策略调整
        :return: 处理结果字典
        """
        result = {
            "success": False,
            "case_id": case_id,
            "feedback_type": feedback_type,
            "adjustments_applied": [],
            "requires_manual_review": False,
            "message": ""
        }
        
        # 1. 更新病例记忆（如果提供了 CaseMemory）
        if self.case_memory and case_id:
            # 确定反馈类型和病情状态
            if disease_status is None:
                if feedback_type in [FeedbackType.MEDICATION_EFFECTIVE.value, FeedbackType.DISEASE_IMPROVED.value]:
                    disease_status = "改善"
                elif feedback_type == FeedbackType.DISEASE_WORSENED.value:
                    disease_status = "恶化"
                else:
                    disease_status = "稳定"
            
            improvement = (disease_status == "改善")
            
            # 更新复查结果
            self.case_memory.update_followup_result(
                case_id=case_id,
                disease_status=disease_status,
                improvement=improvement
            )
            
            # 更新用户反馈
            self.case_memory.update_feedback(
                case_id=case_id,
                feedback_type=feedback_type,
                details=details,
                medication_applied=medication_applied,
                medication_name=medication_name
            )
        
        # 2. 获取策略调整规则
        strategy_rules = self._feedback_to_strategy_map.get(feedback_type, {})
        adjustments = strategy_rules.get("adjustments", [])
        requires_review = strategy_rules.get("requires_review", False)
        
        # 3. 应用策略调整
        if auto_apply_adjustment and strategy_rules.get("auto_apply", False):
            for adjustment in adjustments:
                adj_type = adjustment.get("type")
                adj_value = adjustment.get("value", 0.0)
                adj_reason = adjustment.get("reason", "")
                
                # 执行调整
                if adj_type == StrategyAdjustmentType.CONFIDENCE_UP.value:
                    self._apply_confidence_adjustment(case_id, adj_value)
                elif adj_type == StrategyAdjustmentType.CONFIDENCE_DOWN.value:
                    self._apply_confidence_adjustment(case_id, -adj_value)
                elif adj_type == StrategyAdjustmentType.PRIORITY_UP.value:
                    self._apply_priority_adjustment(case_id, adj_value)
                elif adj_type == StrategyAdjustmentType.PRIORITY_DOWN.value:
                    self._apply_priority_adjustment(case_id, -adj_value)
                
                result["adjustments_applied"].append({
                    "type": adj_type,
                    "value": adj_value,
                    "reason": adj_reason
                })
        
        # 4. 标记需要人工复核
        if requires_review:
            result["requires_manual_review"] = True
            self._mark_for_manual_review(case_id)
        
        # 5. 记录反馈历史
        self._feedback_history.append({
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "feedback_type": feedback_type,
            "details": details,
            "medication_name": medication_name,
            "adjustments_applied": result["adjustments_applied"],
            "requires_review": requires_review
        })
        
        result["success"] = True
        result["message"] = f"反馈处理完成，应用了 {len(result['adjustments_applied'])} 项策略调整"
        
        if requires_review:
            result["message"] += "，需要人工复核"
        
        print(f"[FeedbackHandler] 反馈处理完成：{case_id} - {feedback_type}")
        return result
    
    def _apply_confidence_adjustment(self, case_id: str, adjustment: float) -> None:
        """
        应用置信度调整
        
        :param case_id: 病例 ID
        :param adjustment: 调整值（正数=提高，负数=降低）
        """
        # 从病例获取病害类型
        if self.case_memory and case_id in self.case_memory:
            case = self.case_memory.retrieve_case(case_id)
            if case:
                disease_type = case.get("disease_type")
                if disease_type and disease_type in self._disease_strategies:
                    strategy = self._disease_strategies[disease_type]
                    strategy["confidence_adjustment"] += adjustment
                    
                    # 限制调整范围
                    strategy["confidence_adjustment"] = max(-0.3, min(0.3, strategy["confidence_adjustment"]))
                    
                    print(f"[FeedbackHandler] 置信度调整：{disease_type} {adjustment:+.3f}")
    
    def _apply_priority_adjustment(self, case_id: str, adjustment: float) -> None:
        """
        应用推荐优先级调整
        
        :param case_id: 病例 ID
        :param adjustment: 调整值（正数=提高，负数=降低）
        """
        # 从病例获取病害类型和药剂信息
        if self.case_memory and case_id in self.case_memory:
            case = self.case_memory.retrieve_case(case_id)
            if case:
                disease_type = case.get("disease_type")
                if disease_type and disease_type in self._disease_strategies:
                    strategy = self._disease_strategies[disease_type]
                    strategy["recommendation_priority"] += adjustment
                    
                    # 限制调整范围
                    strategy["recommendation_priority"] = max(0.5, min(1.5, strategy["recommendation_priority"]))
                    
                    print(f"[FeedbackHandler] 优先级调整：{disease_type} {adjustment:+.3f}")
    
    def _mark_for_manual_review(self, case_id: str) -> None:
        """
        标记病例需要人工复核
        
        :param case_id: 病例 ID
        """
        if self.case_memory and case_id in self.case_memory:
            case = self.case_memory.retrieve_case(case_id)
            if case:
                disease_type = case.get("disease_type")
                if disease_type and disease_type in self._disease_strategies:
                    self._disease_strategies[disease_type]["manual_review_count"] += 1
                    print(f"[FeedbackHandler] 标记人工复核：{case_id}")
    
    def get_strategy_adjustments(
        self,
        disease_type: str,
        feedback_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        获取病害的策略调整建议
        
        :param disease_type: 病害类型
        :param feedback_history: 反馈历史记录（可选）
        :return: 策略调整建议字典
        """
        if disease_type not in self._disease_strategies:
            return {
                "error": f"未知病害类型：{disease_type}",
                "suggestion": "建议添加该病害的策略配置"
            }
        
        strategy = self._disease_strategies[disease_type]
        
        # 计算当前置信度
        current_confidence = strategy["base_confidence"] + strategy["confidence_adjustment"]
        current_confidence = max(0.0, min(1.0, current_confidence))
        
        # 计算当前优先级
        current_priority = strategy["recommendation_priority"]
        
        # 生成调整建议
        suggestions = []
        
        if strategy["confidence_adjustment"] < -0.1:
            suggestions.append({
                "type": "警告",
                "message": "该病害诊断置信度持续下降，建议检查诊断模型"
            })
        
        if strategy["manual_review_count"] > 5:
            suggestions.append({
                "type": "建议",
                "message": f"该病害已有{strategy['manual_review_count']}次需要人工复核，建议优化诊断规则"
            })
        
        if current_confidence < 0.6:
            suggestions.append({
                "type": "警告",
                "message": "诊断置信度低于阈值，建议重新训练模型或调整特征提取"
            })
        
        return {
            "disease_type": disease_type,
            "current_confidence": current_confidence,
            "confidence_adjustment": strategy["confidence_adjustment"],
            "recommendation_priority": current_priority,
            "manual_review_count": strategy["manual_review_count"],
            "recommended_medications": strategy["recommended_medications"],
            "suggestions": suggestions
        }
    
    def apply_strategy_adjustment(
        self,
        disease_type: str,
        adjustment_type: str,
        adjustment_value: float,
        reason: str = ""
    ) -> bool:
        """
        手动应用策略调整
        
        :param disease_type: 病害类型
        :param adjustment_type: 调整类型
        :param adjustment_value: 调整值
        :param reason: 调整原因
        :return: 调整是否成功
        """
        if disease_type not in self._disease_strategies:
            print(f"[FeedbackHandler] 调整失败：未知病害类型 {disease_type}")
            return False
        
        strategy = self._disease_strategies[disease_type]
        
        if adjustment_type == "confidence":
            strategy["confidence_adjustment"] += adjustment_value
            strategy["confidence_adjustment"] = max(-0.3, min(0.3, strategy["confidence_adjustment"]))
        
        elif adjustment_type == "priority":
            strategy["recommendation_priority"] += adjustment_value
            strategy["recommendation_priority"] = max(0.5, min(1.5, strategy["recommendation_priority"]))
        
        elif adjustment_type == "medication_priority":
            # 调整特定药剂的优先级
            medication_name = reason  # 这里 reason 用作药剂名
            for med in strategy["recommended_medications"]:
                if med["name"] == medication_name:
                    med["priority"] += adjustment_value
                    med["priority"] = max(0.1, min(2.0, med["priority"]))
                    break
        
        # 记录调整
        self._strategy_adjustments[disease_type] = {
            "timestamp": datetime.now().isoformat(),
            "type": adjustment_type,
            "value": adjustment_value,
            "reason": reason
        }
        
        print(f"[FeedbackHandler] 策略调整应用成功：{disease_type} - {adjustment_type} {adjustment_value:+.3f}")
        return True
    
    def get_adjusted_recommendation(
        self,
        disease_type: str,
        severity: str
    ) -> Dict[str, Any]:
        """
        获取调整后的推荐方案
        
        :param disease_type: 病害类型
        :param severity: 严重度
        :return: 推荐方案字典
        """
        if disease_type not in self._disease_strategies:
            return {
                "error": f"未知病害类型：{disease_type}",
                "recommendation": "请咨询农业专家"
            }
        
        strategy = self._disease_strategies[disease_type]
        
        # 获取调整后的置信度
        current_confidence = strategy["base_confidence"] + strategy["confidence_adjustment"]
        current_confidence = max(0.0, min(1.0, current_confidence))
        
        # 获取调整后的优先级
        current_priority = strategy["recommendation_priority"]
        
        # 排序药剂（按优先级）
        medications = sorted(
            strategy["recommended_medications"],
            key=lambda x: x.get("priority", 0),
            reverse=True
        )
        
        # 生成推荐方案
        recommendation_text = self._generate_recommendation_text(
            disease_type=disease_type,
            severity=severity,
            medications=medications,
            confidence=current_confidence
        )
        
        return {
            "disease_type": disease_type,
            "severity": severity,
            "confidence": current_confidence,
            "priority": current_priority,
            "recommended_medications": medications,
            "recommendation_text": recommendation_text,
            "manual_review_needed": strategy["manual_review_count"] > 3
        }
    
    def _generate_recommendation_text(
        self,
        disease_type: str,
        severity: str,
        medications: List[Dict[str, Any]],
        confidence: float
    ) -> str:
        """
        生成推荐方案文本
        
        :param disease_type: 病害类型
        :param severity: 严重度
        :param medications: 推荐药剂列表
        :param confidence: 诊断置信度
        :return: 推荐方案文本
        """
        # 基础模板
        templates = {
            "轻度": "建议使用{medication}进行防治，注意观察病情变化。",
            "中度": "建议及时使用{medication}进行喷雾防治，7 天一次，连续 2-3 次。",
            "重度": "病情严重，建议立即使用{medication}进行防治，并考虑增加防治频次。如条件允许，请咨询当地农业专家。"
        }
        
        # 获取最佳药剂
        best_med = medications[0]["name"] if medications else "广谱杀菌剂"
        
        # 生成文本
        template = templates.get(severity, templates["中度"])
        recommendation = template.format(medication=best_med)
        
        # 添加置信度提示
        if confidence < 0.6:
            recommendation += " 注意：诊断置信度较低，建议结合田间实际情况综合判断。"
        
        return recommendation
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        获取反馈统计信息
        
        :return: 统计信息字典
        """
        if not self._feedback_history:
            return {
                "total_feedback": 0,
                "message": "暂无反馈数据"
            }
        
        # 反馈类型分布
        type_distribution = {}
        review_count = 0
        
        for feedback in self._feedback_history:
            fb_type = feedback.get("feedback_type", "未知")
            type_distribution[fb_type] = type_distribution.get(fb_type, 0) + 1
            
            if feedback.get("requires_review"):
                review_count += 1
        
        return {
            "total_feedback": len(self._feedback_history),
            "type_distribution": type_distribution,
            "manual_review_count": review_count,
            "review_rate": review_count / len(self._feedback_history) if self._feedback_history else 0
        }
    
    def export_feedback_history(self, output_path: str) -> bool:
        """
        导出反馈历史到 JSON 文件
        
        :param output_path: 输出文件路径
        :return: 导出是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self._feedback_history, f, ensure_ascii=False, indent=2)
            
            print(f"[FeedbackHandler] 反馈历史已导出至：{output_path}")
            return True
        
        except Exception as e:
            print(f"[FeedbackHandler] 导出失败：{e}")
            return False
    
    def save_strategies(self, config_path: str) -> bool:
        """
        保存策略配置到文件
        
        :param config_path: 配置文件路径
        :return: 保存是否成功
        """
        return self._save_config(config_path)
    
    def __str__(self) -> str:
        """
        反馈处理器的字符串表示
        
        :return: 描述字符串
        """
        return f"FeedbackHandler(反馈数：{len(self._feedback_history)}, 病害策略：{len(self._disease_strategies)}个)"


def test_feedback_handler():
    """测试反馈处理器"""
    print("=" * 60)
    print("🧪 测试 FeedbackHandler")
    print("=" * 60)
    
    # 导入 CaseMemory
    from .case_memory import CaseMemory
    
    # 初始化
    test_memory_path = "data/test_feedback_memories.json"
    case_memory = CaseMemory(storage_path=test_memory_path)
    feedback_handler = FeedbackHandler(case_memory=case_memory)
    
    print(f"\n1️⃣ 初始状态：{feedback_handler}")
    
    print("\n2️⃣ 存储测试病例")
    case_id_1 = case_memory.store_case(
        user_id="test_user_002",
        field_id="test_field_002",
        image_path="data/images/test_fb_001.jpg",
        disease_type="条锈病",
        severity="中度",
        recommendation="使用三唑酮可湿性粉剂喷雾"
    )
    print(f"   病例 ID: {case_id_1}")
    
    print("\n3️⃣ 处理用户反馈（施药有效）")
    result = feedback_handler.process_feedback(
        case_id=case_id_1,
        feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
        details="使用三唑酮后，病斑明显减少",
        medication_name="三唑酮可湿性粉剂",
        medication_applied=True,
        disease_status="改善"
    )
    print(f"   处理结果：{result['message']}")
    print(f"   策略调整：{len(result['adjustments_applied'])} 项")
    for adj in result['adjustments_applied']:
        print(f"     - {adj['type']}: {adj['reason']}")
    
    print("\n4️⃣ 获取策略调整建议")
    suggestions = feedback_handler.get_strategy_adjustments(disease_type="条锈病")
    print(f"   当前置信度：{suggestions.get('current_confidence', 0):.3f}")
    print(f"   推荐优先级：{suggestions.get('recommendation_priority', 0):.3f}")
    if suggestions.get('suggestions'):
        print(f"   建议:")
        for sug in suggestions['suggestions']:
            print(f"     - {sug['type']}: {sug['message']}")
    
    print("\n5️⃣ 获取调整后的推荐方案")
    recommendation = feedback_handler.get_adjusted_recommendation(
        disease_type="条锈病",
        severity="中度"
    )
    print(f"   推荐置信度：{recommendation.get('confidence', 0):.3f}")
    print(f"   推荐药剂：{recommendation.get('recommended_medications', [{}])[0].get('name', 'N/A')}")
    print(f"   推荐方案：{recommendation.get('recommendation_text', '')}")
    
    print("\n6️⃣ 手动应用策略调整")
    success = feedback_handler.apply_strategy_adjustment(
        disease_type="条锈病",
        adjustment_type="confidence",
        adjustment_value=0.05,
        reason="测试调整"
    )
    print(f"   调整结果：{'成功' if success else '失败'}")
    
    print("\n7️⃣ 反馈统计信息")
    stats = feedback_handler.get_feedback_statistics()
    print(f"   总反馈数：{stats.get('total_feedback', 0)}")
    print(f"   类型分布：{stats.get('type_distribution', {})}")
    print(f"   需要复核：{stats.get('manual_review_count', 0)}")
    
    print("\n8️⃣ 测试反馈解析")
    test_texts = [
        "采纳了建议，施药后病情好转",
        "施药后没有效果，病情加重了",
        "部分采纳，用了一种药",
        "需要专家复核"
    ]
    for text in test_texts:
        parsed = feedback_handler.parse_feedback(text)
        print(f"   原文：{text}")
        print(f"   解析：{parsed['parsed_type']} (置信度：{parsed['confidence']:.2f})")
    
    print("\n" + "=" * 60)
    print("✅ FeedbackHandler 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_feedback_handler()
