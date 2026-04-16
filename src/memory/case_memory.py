# -*- coding: utf-8 -*-
"""
病例记忆系统 - Case Memory
IWDDA Agent 反馈记忆层核心组件，负责病例记忆的存储、检索和持久化

功能特性:
1. 记忆存储结构：存储用户信息、上传时间、病害类型、严重度、推荐方案、用户反馈、复查结果
2. 记忆检索接口：支持按用户 ID、地块 ID、时间范围等多种方式检索
3. 持久化存储：使用 JSON 文件存储，支持自动加载和保存
4. 记忆引用机制：再次诊断时检索历史病例，提供上下文注入
5. 病情变化对比：对比前后两次诊断结果，判断病情发展趋势

数据结构:
{
    "case_id": "CASE_20260309_001",
    "user_id": "user_001",
    "field_id": "field_001",
    "upload_timestamp": "2026-03-09T10:30:00",
    "image_path": "data/images/field_001_20260309.jpg",
    "disease_type": "条锈病",
    "severity": "中度",
    "confidence": 0.87,
    "recommendation": "使用三唑酮可湿性粉剂喷雾，7 天一次，连续 2-3 次",
    "risk_level": "中风险",
    "reasoning": "图像显示叶片出现黄色条状病斑，符合条锈病特征",
    "user_feedback": {
        "feedback_type": "采纳建议",
        "feedback_timestamp": "2026-03-10T09:00:00",
        "details": "已施药，病情有所好转",
        "medication_applied": true,
        "medication_name": "三唑酮可湿性粉剂"
    },
    "followup_result": {
        "followup_timestamp": "2026-03-16T10:00:00",
        "disease_status": "缓解",
        "new_image_path": "data/images/field_001_20260316.jpg",
        "new_disease_type": "条锈病",
        "new_severity": "轻度",
        "improvement": true
    }
}

使用示例:
    from src.memory import CaseMemory
    
    # 初始化病例记忆系统
    case_memory = CaseMemory(storage_path="data/case_memories.json")
    
    # 存储新病例
    case_id = case_memory.store_case(
        user_id="user_001",
        field_id="field_001",
        image_path="data/images/test.jpg",
        disease_type="条锈病",
        severity="中度",
        recommendation="使用三唑酮可湿性粉剂喷雾"
    )
    
    # 检索用户历史病例
    history = case_memory.retrieve_history(user_id="user_001", limit=5)
    
    # 检索特定地块的病例
    field_cases = case_memory.retrieve_by_field(field_id="field_001")
    
    # 获取最新病例用于上下文注入
    latest_case = case_memory.get_latest_case(user_id="user_001")
    
    # 对比病情变化
    comparison = case_memory.compare_disease_progression(
        user_id="user_001",
        field_id="field_001"
    )
"""

import os
import sys
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class CaseMemory:
    """
    病例记忆系统类
    
    负责管理所有病例记忆的存储、检索和持久化：
    - 存储新的诊断病例
    - 检索历史病例记录
    - 持久化到 JSON 文件
    - 支持多种检索方式（用户 ID、地块 ID、时间范围等）
    - 病情变化对比分析
    """
    
    def __init__(self, storage_path: str = "data/case_memories.json"):
        """
        初始化病例记忆系统
        
        :param storage_path: JSON 存储文件路径
        """
        self.storage_path = storage_path
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._user_index: Dict[str, List[str]] = {}  # user_id -> [case_id]
        self._field_index: Dict[str, List[str]] = {}  # field_id -> [case_id]
        
        # 确保存储目录存在
        storage_dir = os.path.dirname(storage_path)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
            print(f"[CaseMemory] 创建存储目录：{storage_dir}")
        
        # 加载已有数据
        self._load_from_disk()
        
        print(f"[CaseMemory] 病例记忆系统初始化完成，已加载 {len(self._cases)} 个病例")
    
    def _generate_case_id(self) -> str:
        """
        生成唯一的病例 ID
        
        :return: 病例 ID 字符串，格式为 CASE_YYYYMMDD_XXXX
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:4].upper()
        return f"CASE_{timestamp}_{unique_id}"
    
    def _load_from_disk(self) -> bool:
        """
        从磁盘加载病例数据
        
        :return: 加载是否成功
        """
        if not os.path.exists(self.storage_path):
            print(f"[CaseMemory] 存储文件不存在，创建新文件：{self.storage_path}")
            return True
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cases = data.get("cases", {})
            self._user_index = data.get("user_index", {})
            self._field_index = data.get("field_index", {})
            
            print(f"[CaseMemory] 成功加载 {len(self._cases)} 个病例")
            return True
        
        except Exception as e:
            print(f"[CaseMemory] 加载数据时发生错误：{e}")
            return False
    
    def _save_to_disk(self) -> bool:
        """
        保存病例数据到磁盘
        
        :return: 保存是否成功
        """
        try:
            data = {
                "cases": self._cases,
                "user_index": self._user_index,
                "field_index": self._field_index,
                "last_updated": datetime.now().isoformat(),
                "total_cases": len(self._cases)
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[CaseMemory] 成功保存 {len(self._cases)} 个病例到 {self.storage_path}")
            return True
        
        except Exception as e:
            print(f"[CaseMemory] 保存数据时发生错误：{e}")
            return False
    
    def store_case(
        self,
        user_id: str,
        image_path: str,
        disease_type: str,
        severity: str,
        recommendation: str,
        field_id: Optional[str] = None,
        confidence: Optional[float] = None,
        risk_level: Optional[str] = None,
        reasoning: Optional[str] = None,
        symptoms: Optional[str] = None,
        growth_stage: Optional[str] = None,
        weather: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        存储新的诊断病例
        
        :param user_id: 用户 ID
        :param image_path: 上传的图像路径
        :param disease_type: 病害类型（如"条锈病"、"叶锈病"等）
        :param severity: 严重度等级（轻度/中度/重度）
        :param recommendation: 推荐防治方案
        :param field_id: 地块 ID（可选，用于同一地块多次诊断）
        :param confidence: 诊断置信度（0-1 之间）
        :param risk_level: 风险等级（低风险/中风险/高风险）
        :param reasoning: 诊断推理依据
        :param symptoms: 症状描述
        :param growth_stage: 生长阶段
        :param weather: 天气情况
        :param kwargs: 其他扩展字段
        :return: 病例 ID
        """
        case_id = self._generate_case_id()
        
        case_data = {
            "case_id": case_id,
            "user_id": user_id,
            "field_id": field_id or f"field_{user_id}_default",
            "upload_timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "disease_type": disease_type,
            "severity": severity,
            "confidence": confidence,
            "recommendation": recommendation,
            "risk_level": risk_level,
            "reasoning": reasoning,
            "symptoms": symptoms,
            "growth_stage": growth_stage,
            "weather": weather,
            "user_feedback": None,
            "followup_result": None,
            "metadata": kwargs
        }
        
        # 存储病例
        self._cases[case_id] = case_data
        
        # 更新用户索引
        if user_id not in self._user_index:
            self._user_index[user_id] = []
        self._user_index[user_id].append(case_id)
        
        # 更新地块索引
        field_id = case_data["field_id"]
        if field_id not in self._field_index:
            self._field_index[field_id] = []
        self._field_index[field_id].append(case_id)
        
        # 保存到磁盘
        self._save_to_disk()
        
        print(f"[CaseMemory] 新病例存储成功：{case_id} (用户：{user_id}, 病害：{disease_type})")
        return case_id
    
    def retrieve_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        检索单个病例
        
        :param case_id: 病例 ID
        :return: 病例数据字典，不存在则返回 None
        """
        case = self._cases.get(case_id)
        if case:
            print(f"[CaseMemory] 检索到病例：{case_id}")
        else:
            print(f"[CaseMemory] 未找到病例：{case_id}")
        return case
    
    def retrieve_history(
        self,
        user_id: str,
        limit: int = 10,
        disease_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索用户的历史病例
        
        :param user_id: 用户 ID
        :param limit: 返回数量限制（默认 10 条，按时间倒序）
        :param disease_type: 病害类型过滤（可选）
        :return: 病例列表
        """
        case_ids = self._user_index.get(user_id, [])
        
        if not case_ids:
            print(f"[CaseMemory] 用户 {user_id} 无历史病例")
            return []
        
        # 按时间倒序排序（新的在前）
        sorted_cases = sorted(
            [self._cases[cid] for cid in case_ids if cid in self._cases],
            key=lambda x: x.get("upload_timestamp", ""),
            reverse=True
        )
        
        # 过滤病害类型
        if disease_type:
            sorted_cases = [c for c in sorted_cases if c.get("disease_type") == disease_type]
        
        # 限制数量
        result = sorted_cases[:limit]
        
        print(f"[CaseMemory] 检索到用户 {user_id} 的 {len(result)} 条历史病例")
        return result
    
    def retrieve_by_field(
        self,
        field_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        检索特定地块的历史病例
        
        :param field_id: 地块 ID
        :param limit: 返回数量限制
        :return: 病例列表
        """
        case_ids = self._field_index.get(field_id, [])
        
        if not case_ids:
            print(f"[CaseMemory] 地块 {field_id} 无历史病例")
            return []
        
        # 按时间倒序排序
        sorted_cases = sorted(
            [self._cases[cid] for cid in case_ids if cid in self._cases],
            key=lambda x: x.get("upload_timestamp", ""),
            reverse=True
        )
        
        result = sorted_cases[:limit]
        
        print(f"[CaseMemory] 检索到地块 {field_id} 的 {len(result)} 条历史病例")
        return result
    
    def get_latest_case(self, user_id: str, field_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取用户最新的一个病例（用于上下文注入）
        
        :param user_id: 用户 ID
        :param field_id: 地块 ID（可选，指定则获取该地块的最新病例）
        :return: 最新病例数据，无病例则返回 None
        """
        if field_id:
            cases = self.retrieve_by_field(field_id, limit=1)
        else:
            cases = self.retrieve_history(user_id, limit=1)
        
        if cases:
            latest = cases[0]
            print(f"[CaseMemory] 获取最新病例：{latest['case_id']}")
            return latest
        
        print(f"[CaseMemory] 未找到最新病例")
        return None
    
    def update_feedback(
        self,
        case_id: str,
        feedback_type: str,
        details: str,
        medication_applied: bool = False,
        medication_name: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        更新病例的用户反馈信息
        
        :param case_id: 病例 ID
        :param feedback_type: 反馈类型（采纳建议/未采纳/部分采纳）
        :param details: 反馈详细信息
        :param medication_applied: 是否已施药
        :param medication_name: 施药名称
        :param kwargs: 其他扩展字段
        :return: 更新是否成功
        """
        if case_id not in self._cases:
            print(f"[CaseMemory] 更新失败：病例 {case_id} 不存在")
            return False
        
        case = self._cases[case_id]
        case["user_feedback"] = {
            "feedback_type": feedback_type,
            "feedback_timestamp": datetime.now().isoformat(),
            "details": details,
            "medication_applied": medication_applied,
            "medication_name": medication_name,
            **kwargs
        }
        
        self._save_to_disk()
        
        print(f"[CaseMemory] 病例 {case_id} 反馈信息更新成功")
        return True
    
    def update_followup_result(
        self,
        case_id: str,
        disease_status: str,
        new_image_path: Optional[str] = None,
        new_disease_type: Optional[str] = None,
        new_severity: Optional[str] = None,
        improvement: bool = False,
        **kwargs
    ) -> bool:
        """
        更新病例的复查结果
        
        :param case_id: 病例 ID
        :param disease_status: 病情状态（缓解/稳定/恶化）
        :param new_image_path: 复查时上传的新图像路径
        :param new_disease_type: 复查时的病害类型
        :param new_severity: 复查时的严重度
        :param improvement: 是否有所改善
        :param kwargs: 其他扩展字段
        :return: 更新是否成功
        """
        if case_id not in self._cases:
            print(f"[CaseMemory] 更新失败：病例 {case_id} 不存在")
            return False
        
        case = self._cases[case_id]
        case["followup_result"] = {
            "followup_timestamp": datetime.now().isoformat(),
            "disease_status": disease_status,
            "new_image_path": new_image_path,
            "new_disease_type": new_disease_type,
            "new_severity": new_severity,
            "improvement": improvement,
            **kwargs
        }
        
        self._save_to_disk()
        
        print(f"[CaseMemory] 病例 {case_id} 复查结果更新成功")
        return True
    
    def compare_disease_progression(
        self,
        user_id: str,
        field_id: Optional[str] = None,
        disease_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        对比病情变化趋势（对比前后两次诊断结果）
        
        :param user_id: 用户 ID
        :param field_id: 地块 ID（可选）
        :param disease_type: 病害类型（可选）
        :return: 病情对比结果字典，包含：
            - has_comparison: 是否有可对比的病例
            - previous_case: 上次病例
            - current_case: 当前病例
            - progression: 发展趋势（改善/稳定/恶化）
            - severity_change: 严重度变化
            - time_span_days: 时间间隔（天）
        """
        # 获取最新两个病例
        if field_id:
            cases = self.retrieve_by_field(field_id, limit=2)
        else:
            cases = self.retrieve_history(user_id, disease_type=disease_type, limit=2)
        
        if len(cases) < 2:
            print(f"[CaseMemory] 无法对比：病例数量不足 2 个")
            return {
                "has_comparison": False,
                "message": "病例数量不足，需要至少 2 个病例才能进行对比"
            }
        
        current = cases[0]  # 最新的
        previous = cases[1]  # 上一次的
        
        # 计算时间间隔
        try:
            current_time = datetime.fromisoformat(current["upload_timestamp"])
            previous_time = datetime.fromisoformat(previous["upload_timestamp"])
            time_span = (current_time - previous_time).days
        except:
            time_span = 0
        
        # 分析严重度变化
        severity_order = {"轻度": 1, "中度": 2, "重度": 3}
        prev_severity = severity_order.get(previous.get("severity"), 0)
        curr_severity = severity_order.get(current.get("severity"), 0)
        
        if curr_severity < prev_severity:
            progression = "改善"
            severity_change = f"从{previous.get('severity')}降至{current.get('severity')}"
        elif curr_severity > prev_severity:
            progression = "恶化"
            severity_change = f"从{previous.get('severity')}升至{current.get('severity')}"
        else:
            progression = "稳定"
            severity_change = f"保持{current.get('severity')}"
        
        # 判断是否有复查反馈
        has_followup = previous.get("followup_result") is not None
        
        comparison_result = {
            "has_comparison": True,
            "previous_case": {
                "case_id": previous["case_id"],
                "timestamp": previous["upload_timestamp"],
                "disease_type": previous.get("disease_type"),
                "severity": previous.get("severity"),
                "recommendation": previous.get("recommendation")
            },
            "current_case": {
                "case_id": current["case_id"],
                "timestamp": current["upload_timestamp"],
                "disease_type": current.get("disease_type"),
                "severity": current.get("severity"),
                "recommendation": current.get("recommendation")
            },
            "progression": progression,
            "severity_change": severity_change,
            "time_span_days": time_span,
            "has_followup_feedback": has_followup,
            "summary": f"该地块上次诊断为{previous.get('disease_type')} {previous.get('severity')}，"
                      f"本次诊断为{current.get('disease_type')} {current.get('severity')}，"
                      f"病情发展趋势：{progression}"
        }
        
        print(f"[CaseMemory] 病情对比完成：{progression} - {severity_change}")
        return comparison_result
    
    def get_context_for_injection(
        self,
        user_id: str,
        field_id: Optional[str] = None
    ) -> Optional[str]:
        """
        获取用于上下文注入的记忆信息（将历史记忆作为上下文注入到认知层）
        
        :param user_id: 用户 ID
        :param field_id: 地块 ID（可选）
        :return: 格式化的上下文字符串，用于注入到认知层 prompt
        """
        latest = self.get_latest_case(user_id, field_id)
        
        if not latest:
            return None
        
        # 构建上下文信息
        context_parts = []
        
        # 基本信息
        context_parts.append(f"用户曾于 {latest['upload_timestamp']} 上传过田间图像")
        
        # 诊断历史
        disease_info = f"当时诊断为{latest.get('disease_type', '未知病害')}"
        if latest.get('severity'):
            disease_info += f"，严重度为{latest.get('severity')}"
        context_parts.append(disease_info)
        
        # 推荐方案
        if latest.get('recommendation'):
            context_parts.append(f"推荐防治方案：{latest['recommendation']}")
        
        # 用户反馈
        feedback = latest.get('user_feedback')
        if feedback:
            feedback_type = feedback.get('feedback_type', '未知')
            details = feedback.get('details', '')
            context_parts.append(f"用户反馈：{feedback_type} - {details}")
            
            if feedback.get('medication_applied'):
                med_name = feedback.get('medication_name', '某种药剂')
                context_parts.append(f"用户已施用{med_name}")
        
        # 复查结果
        followup = latest.get('followup_result')
        if followup:
            status = followup.get('disease_status', '未知')
            improvement = followup.get('improvement', False)
            context_parts.append(f"复查结果：病情{status}，{'有所改善' if improvement else '未见明显改善'}")
        
        # 病情对比
        comparison = self.compare_disease_progression(user_id, field_id)
        if comparison and comparison.get('has_comparison'):
            context_parts.append(f"病情发展趋势：{comparison.get('summary', '')}")
        
        context_text = "【历史病例记忆】\n" + "\n".join(context_parts)
        
        print(f"[CaseMemory] 生成上下文注入信息，长度：{len(context_text)} 字符")
        return context_text
    
    def delete_case(self, case_id: str) -> bool:
        """
        删除指定病例
        
        :param case_id: 病例 ID
        :return: 删除是否成功
        """
        if case_id not in self._cases:
            print(f"[CaseMemory] 删除失败：病例 {case_id} 不存在")
            return False
        
        case = self._cases[case_id]
        user_id = case.get("user_id")
        field_id = case.get("field_id")
        
        # 从索引中移除
        if user_id and user_id in self._user_index:
            if case_id in self._user_index[user_id]:
                self._user_index[user_id].remove(case_id)
        
        if field_id and field_id in self._field_index:
            if case_id in self._field_index[field_id]:
                self._field_index[field_id].remove(case_id)
        
        # 删除病例
        del self._cases[case_id]
        
        # 保存到磁盘
        self._save_to_disk()
        
        print(f"[CaseMemory] 病例 {case_id} 删除成功")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取病例统计信息
        
        :return: 统计信息字典
        """
        total_cases = len(self._cases)
        
        if total_cases == 0:
            return {
                "total_cases": 0,
                "message": "暂无病例数据"
            }
        
        # 病害类型分布
        disease_distribution = {}
        severity_distribution = {}
        feedback_count = 0
        followup_count = 0
        
        for case in self._cases.values():
            # 病害类型
            disease = case.get("disease_type", "未知")
            disease_distribution[disease] = disease_distribution.get(disease, 0) + 1
            
            # 严重度
            severity = case.get("severity", "未知")
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
            
            # 反馈和复查统计
            if case.get("user_feedback"):
                feedback_count += 1
            if case.get("followup_result"):
                followup_count += 1
        
        stats = {
            "total_cases": total_cases,
            "unique_users": len(self._user_index),
            "unique_fields": len(self._field_index),
            "disease_distribution": disease_distribution,
            "severity_distribution": severity_distribution,
            "feedback_rate": feedback_count / total_cases if total_cases > 0 else 0,
            "followup_rate": followup_count / total_cases if total_cases > 0 else 0,
            "storage_path": self.storage_path
        }
        
        print(f"[CaseMemory] 统计信息：共 {total_cases} 个病例，{stats['unique_users']} 个用户")
        return stats
    
    def clear_all(self) -> bool:
        """
        清空所有病例数据
        
        :return: 清空是否成功
        """
        self._cases.clear()
        self._user_index.clear()
        self._field_index.clear()
        
        self._save_to_disk()
        
        print(f"[CaseMemory] 所有病例数据已清空")
        return True
    
    def export_to_json(self, output_path: str) -> bool:
        """
        导出病例数据到指定 JSON 文件
        
        :param output_path: 输出文件路径
        :return: 导出是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(list(self._cases.values()), f, ensure_ascii=False, indent=2)
            
            print(f"[CaseMemory] 数据已导出至：{output_path}")
            return True
        
        except Exception as e:
            print(f"[CaseMemory] 导出失败：{e}")
            return False
    
    def __len__(self) -> int:
        """
        获取病例总数
        
        :return: 病例数量
        """
        return len(self._cases)
    
    def __contains__(self, case_id: str) -> bool:
        """
        检查病例是否存在
        
        :param case_id: 病例 ID
        :return: 是否存在
        """
        return case_id in self._cases
    
    def __str__(self) -> str:
        """
        病例记忆系统的字符串表示
        
        :return: 描述字符串
        """
        return f"CaseMemory(病例数：{len(self)}, 存储路径：{self.storage_path})"


def test_case_memory():
    """测试病例记忆系统"""
    print("=" * 60)
    print("🧪 测试 CaseMemory")
    print("=" * 60)
    
    # 初始化（使用临时测试文件）
    test_path = "data/test_case_memories.json"
    case_memory = CaseMemory(storage_path=test_path)
    
    print(f"\n1️⃣ 初始状态：病例数 = {len(case_memory)}")
    
    print("\n2️⃣ 存储新病例")
    case_id_1 = case_memory.store_case(
        user_id="test_user_001",
        field_id="test_field_001",
        image_path="data/images/test_001.jpg",
        disease_type="条锈病",
        severity="中度",
        confidence=0.87,
        risk_level="中风险",
        recommendation="使用三唑酮可湿性粉剂喷雾，7 天一次",
        reasoning="图像显示叶片出现黄色条状病斑"
    )
    print(f"   病例 1 ID: {case_id_1}")
    
    # 模拟时间延迟
    import time
    time.sleep(1)
    
    case_id_2 = case_memory.store_case(
        user_id="test_user_001",
        field_id="test_field_001",
        image_path="data/images/test_002.jpg",
        disease_type="条锈病",
        severity="轻度",
        confidence=0.92,
        risk_level="低风险",
        recommendation="继续观察，必要时施药",
        reasoning="病斑有所减少，病情缓解"
    )
    print(f"   病例 2 ID: {case_id_2}")
    
    print(f"\n3️⃣ 当前病例总数：{len(case_memory)}")
    
    print("\n4️⃣ 检索用户历史病例")
    history = case_memory.retrieve_history(user_id="test_user_001", limit=5)
    print(f"   检索到 {len(history)} 条历史记录")
    for i, case in enumerate(history, 1):
        print(f"   - 病例{i}: {case['disease_type']} {case['severity']} ({case['upload_timestamp']})")
    
    print("\n5️⃣ 获取最新病例")
    latest = case_memory.get_latest_case(user_id="test_user_001")
    if latest:
        print(f"   最新病例：{latest['case_id']} - {latest['disease_type']} {latest['severity']}")
    
    print("\n6️⃣ 更新用户反馈")
    success = case_memory.update_feedback(
        case_id=case_id_1,
        feedback_type="采纳建议",
        details="施药后病情有所好转",
        medication_applied=True,
        medication_name="三唑酮可湿性粉剂"
    )
    print(f"   反馈更新：{'成功' if success else '失败'}")
    
    print("\n7️⃣ 更新复查结果")
    success = case_memory.update_followup_result(
        case_id=case_id_1,
        disease_status="缓解",
        new_image_path="data/images/test_followup.jpg",
        new_disease_type="条锈病",
        new_severity="轻度",
        improvement=True
    )
    print(f"   复查更新：{'成功' if success else '失败'}")
    
    print("\n8️⃣ 病情变化对比")
    comparison = case_memory.compare_disease_progression(
        user_id="test_user_001",
        field_id="test_field_001"
    )
    if comparison.get("has_comparison"):
        print(f"   发展趋势：{comparison['progression']}")
        print(f"   严重度变化：{comparison['severity_change']}")
        print(f"   时间间隔：{comparison['time_span_days']} 天")
        print(f"   对比摘要：{comparison['summary']}")
    
    print("\n9️⃣ 上下文注入信息")
    context = case_memory.get_context_for_injection(
        user_id="test_user_001",
        field_id="test_field_001"
    )
    if context:
        print(f"   上下文信息:\n{context}")
    
    print("\n🔟 统计信息")
    stats = case_memory.get_statistics()
    print(f"   总病例数：{stats['total_cases']}")
    print(f"   用户数：{stats['unique_users']}")
    print(f"   地块数：{stats['unique_fields']}")
    print(f"   反馈率：{stats['feedback_rate']:.2%}")
    print(f"   复查率：{stats['followup_rate']:.2%}")
    
    print("\n" + "=" * 60)
    print("✅ CaseMemory 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_case_memory()
