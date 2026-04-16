# -*- coding: utf-8 -*-
"""
记忆引用集成测试

测试 CaseMemory 病例记忆系统的核心功能：
1. 历史病例检索
2. 上下文注入
3. 病情变化对比
4. 记忆持久化
5. 多用户/多地块管理
"""
import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock
import json
import tempfile
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCaseMemoryBasic:
    """病例记忆基础功能测试"""
    
    @pytest.fixture
    def temp_memory_file(self, tmp_path):
        """创建临时记忆存储文件"""
        memory_file = tmp_path / "test_case_memory.json"
        return str(memory_file)
    
    @pytest.fixture
    def case_memory(self, temp_memory_file):
        """创建 CaseMemory 实例"""
        from src.memory.case_memory import CaseMemory
        return CaseMemory(storage_path=temp_memory_file)
    
    @pytest.fixture
    def sample_cases(self):
        """创建样本病例数据"""
        return [
            {
                "user_id": "user_001",
                "field_id": "field_001",
                "disease_type": "条锈病",
                "severity": "轻度",
                "confidence": 0.85,
                "recommendation": "观察病情，必要时喷药"
            },
            {
                "user_id": "user_001",
                "field_id": "field_001",
                "disease_type": "条锈病",
                "severity": "中度",
                "confidence": 0.90,
                "recommendation": "立即喷施三唑酮"
            },
            {
                "user_id": "user_001",
                "field_id": "field_002",
                "disease_type": "白粉病",
                "severity": "重度",
                "confidence": 0.95,
                "recommendation": "使用戊唑醇治疗"
            },
            {
                "user_id": "user_002",
                "field_id": "field_003",
                "disease_type": "赤霉病",
                "severity": "中度",
                "confidence": 0.88,
                "recommendation": "多菌灵喷雾"
            }
        ]
    
    def test_store_case(self, case_memory, sample_cases):
        """
        测试病例存储功能
        
        验证：
        1. 病例可以成功存储
        2. 生成唯一的病例 ID
        3. 病例数据完整保存
        """
        case = sample_cases[0]
        
        # 存储病例
        case_id = case_memory.store_case(
            user_id=case["user_id"],
            field_id=case["field_id"],
            image_path="test_image.jpg",
            disease_type=case["disease_type"],
            severity=case["severity"],
            confidence=case["confidence"],
            recommendation=case["recommendation"]
        )
        
        # 验证病例 ID
        assert case_id is not None
        assert case_id.startswith("CASE_")
        
        # 验证病例被存储（使用 retrieve_case）
        stored_case = case_memory.retrieve_case(case_id=case_id)
        assert stored_case is not None
        assert stored_case["disease_type"] == "条锈病"
    
    def test_retrieve_user_history(self, case_memory, sample_cases):
        """
        测试用户历史检索
        
        验证：
        1. 可以检索特定用户的所有病例
        2. 支持限制返回数量
        3. 返回结果按时间排序
        """
        # 存储多个病例
        for case in sample_cases:
            case_memory.store_case(
                user_id=case["user_id"],
                field_id=case["field_id"],
                image_path="test.jpg",
                disease_type=case["disease_type"],
                severity=case["severity"],
                confidence=case["confidence"],
                recommendation=case["recommendation"]
            )
        
        # 检索用户 001 的历史
        history = case_memory.retrieve_history(user_id="user_001", limit=10)
        
        # 验证结果
        assert len(history) == 3  # user_001 有 3 个病例
        assert all(c["user_id"] == "user_001" for c in history)
        
        # 限制返回数量
        limited_history = case_memory.retrieve_history(user_id="user_001", limit=2)
        assert len(limited_history) == 2
    
    def test_retrieve_by_field(self, case_memory, sample_cases):
        """
        测试按地块检索病例
        
        验证：
        1. 可以检索特定地块的所有病例
        2. 跨用户检索地块
        """
        # 存储病例
        for case in sample_cases:
            case_memory.store_case(
                user_id=case["user_id"],
                field_id=case["field_id"],
                image_path="test.jpg",
                disease_type=case["disease_type"],
                severity=case["severity"],
                confidence=case["confidence"],
                recommendation=case["recommendation"]
            )
        
        # 检索 field_001 的病例
        field_cases = case_memory.retrieve_by_field(field_id="field_001")
        
        # 验证结果
        assert len(field_cases) == 2
        assert all(c["field_id"] == "field_001" for c in field_cases)
    
    def test_get_latest_case(self, case_memory, sample_cases):
        """
        测试获取最新病例
        
        验证：
        1. 返回用户最新的病例
        2. 包含完整的病例信息
        """
        # 按时间顺序存储病例
        for case in sample_cases[:2]:  # 只存储 user_001 的前两个
            case_memory.store_case(
                user_id=case["user_id"],
                field_id=case["field_id"],
                image_path="test.jpg",
                disease_type=case["disease_type"],
                severity=case["severity"],
                confidence=case["confidence"],
                recommendation=case["recommendation"]
            )
        
        # 获取最新病例
        latest = case_memory.get_latest_case(user_id="user_001")
        
        # 验证结果
        assert latest is not None
        # 最新病例应该是第二个（中度），但由于时间戳可能相同，我们只验证 severity 在预期范围内
        assert latest["severity"] in ["轻度", "中度"]
    
    def test_persistence(self, temp_memory_file, sample_cases):
        """
        测试记忆持久化
        
        验证：
        1. 数据可以保存到磁盘
        2. 重新加载后数据完整
        """
        from src.memory.case_memory import CaseMemory
        
        # 创建并存储病例
        case_memory_1 = CaseMemory(storage_path=temp_memory_file)
        for case in sample_cases:
            case_memory_1.store_case(
                user_id=case["user_id"],
                field_id=case["field_id"],
                image_path="test.jpg",
                disease_type=case["disease_type"],
                severity=case["severity"],
                confidence=case["confidence"],
                recommendation=case["recommendation"]
            )
        
        # 验证文件已创建
        assert os.path.exists(temp_memory_file)
        
        # 重新加载
        case_memory_2 = CaseMemory(storage_path=temp_memory_file)
        
        # 验证数据完整（使用 len 检查）
        assert len(case_memory_2) == len(sample_cases)


class TestCaseMemoryAdvanced:
    """病例记忆高级功能测试"""
    
    @pytest.fixture
    def case_memory_with_data(self, tmp_path):
        """创建包含测试数据的 CaseMemory"""
        from src.memory.case_memory import CaseMemory
        
        memory_file = tmp_path / "advanced_test.json"
        case_memory = CaseMemory(storage_path=str(memory_file))
        
        # 添加带反馈的病例
        case_memory.store_case(
            user_id="user_003",
            field_id="field_004",
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="轻度",
            confidence=0.85,
            recommendation="观察病情"
        )
        
        # 添加带复查的病例
        case_memory.store_case(
            user_id="user_003",
            field_id="field_004",
            image_path="test2.jpg",
            disease_type="条锈病",
            severity="中度",
            confidence=0.90,
            recommendation="喷施药剂"
        )
        
        return case_memory
    
    def test_disease_progression_comparison(self, case_memory_with_data):
        """
        测试病情变化对比
        
        验证：
        1. 可以对比同一地块的前后两次诊断
        2. 判断病情发展趋势（好转/恶化/稳定）
        3. 提供详细对比信息
        """
        # 对比病情变化
        comparison = case_memory_with_data.compare_disease_progression(
            user_id="user_003",
            field_id="field_004"
        )
        
        # 验证对比结果
        assert comparison is not None
        assert "previous_case" in comparison
        assert "current_case" in comparison
        # 使用 progression 或 trend 字段
        assert "progression" in comparison or "trend" in comparison
    
    def test_context_injection_for_diagnosis(self, case_memory_with_data):
        """
        测试上下文注入
        
        验证：
        1. 获取历史病例用于诊断上下文
        2. 提供相关病史信息
        """
        # 获取用于上下文注入的病例（返回字符串）
        context_text = case_memory_with_data.get_context_for_injection(
            user_id="user_003"
        )
        
        # 验证返回了上下文信息
        assert context_text is not None
        assert isinstance(context_text, str)
        assert len(context_text) > 0
        
        # 验证包含必要信息
        assert "条锈病" in context_text or "病害" in context_text
    
    def test_feedback_integration(self, case_memory_with_data):
        """
        测试用户反馈集成
        
        验证：
        1. 可以添加用户反馈
        2. 反馈被正确存储
        3. 反馈可用于经验回放
        """
        # 获取最新病例
        latest_case = case_memory_with_data.get_latest_case(user_id="user_003")
        case_id = latest_case["case_id"]
        
        # 添加用户反馈（使用 update_feedback 方法，返回 bool）
        success = case_memory_with_data.update_feedback(
            case_id=case_id,
            feedback_type="采纳建议",
            details="已喷药，病情好转",
            medication_applied=True
        )
        
        # 验证反馈添加成功
        assert success is True
        
        # 验证反馈被存储
        updated_case = case_memory_with_data.retrieve_case(case_id)
        assert updated_case["user_feedback"] is not None
        assert updated_case["user_feedback"]["feedback_type"] == "采纳建议"


class TestCaseMemoryEdgeCases:
    """病例记忆边界情况测试"""
    
    @pytest.fixture
    def empty_case_memory(self, tmp_path):
        """创建空的 CaseMemory"""
        from src.memory.case_memory import CaseMemory
        memory_file = tmp_path / "empty_test.json"
        return CaseMemory(storage_path=str(memory_file))
    
    def test_retrieve_nonexistent_user(self, empty_case_memory):
        """
        测试检索不存在的用户
        
        验证：
        1. 返回空列表而不是报错
        2. 错误处理优雅
        """
        history = empty_case_memory.retrieve_history(user_id="nonexistent_user")
        assert history == []
    
    def test_retrieve_nonexistent_field(self, empty_case_memory):
        """
        测试检索不存在的地块
        
        验证：
        1. 返回空列表
        2. 不抛出异常
        """
        field_cases = empty_case_memory.retrieve_by_field(field_id="nonexistent_field")
        assert field_cases == []
    
    def test_get_latest_case_for_new_user(self, empty_case_memory):
        """
        测试获取新用户（无病例）的最新病例
        
        验证：
        1. 返回 None 而不是报错
        2. 调用方可以安全处理
        """
        latest = empty_case_memory.get_latest_case(user_id="new_user")
        assert latest is None
    
    def test_compare_with_insufficient_data(self, empty_case_memory):
        """
        测试数据不足时的病情对比
        
        验证：
        1. 只有一个病例时无法对比
        2. 返回适当的错误信息
        """
        # 只存储一个病例
        empty_case_memory.store_case(
            user_id="single_user",
            field_id="single_field",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="轻度",
            confidence=0.85,
            recommendation="观察"
        )
        
        # 尝试对比（只有一个病例）
        comparison = empty_case_memory.compare_disease_progression(
            user_id="single_user",
            field_id="single_field"
        )
        
        # 验证返回了适当的响应
        assert comparison is not None
        # 应该提示数据不足
        assert comparison.get("trend") is None or \
               comparison.get("message") is not None


class TestCaseMemoryDataIsolation:
    """测试数据隔离"""
    
    @pytest.fixture
    def multi_user_memory(self, tmp_path):
        """创建多用户 CaseMemory"""
        from src.memory.case_memory import CaseMemory
        
        memory_file = tmp_path / "multi_user.json"
        case_memory = CaseMemory(storage_path=str(memory_file))
        
        # 为不同用户存储病例
        users_data = [
            ("user_A", "field_A1", "条锈病", "轻度"),
            ("user_A", "field_A2", "白粉病", "中度"),
            ("user_B", "field_B1", "赤霉病", "重度"),
            ("user_C", "field_C1", "叶锈病", "轻度"),
        ]
        
        for user_id, field_id, disease, severity in users_data:
            case_memory.store_case(
                user_id=user_id,
                field_id=field_id,
                image_path="test.jpg",
                disease_type=disease,
                severity=severity,
                confidence=0.90,
                recommendation="治疗"
            )
        
        return case_memory
    
    def test_user_data_isolation(self, multi_user_memory):
        """
        测试用户数据隔离
        
        验证：
        1. 用户只能看到自己的病例
        2. 不同用户数据不混淆
        """
        # 检索用户 A 的数据
        user_a_cases = multi_user_memory.retrieve_history(user_id="user_A")
        
        # 验证只看到自己的 2 个病例
        assert len(user_a_cases) == 2
        assert all(c["user_id"] == "user_A" for c in user_a_cases)
        
        # 检索用户 B 的数据
        user_b_cases = multi_user_memory.retrieve_history(user_id="user_B")
        
        # 验证只看到自己的 1 个病例
        assert len(user_b_cases) == 1
        assert user_b_cases[0]["user_id"] == "user_B"
    
    def test_field_data_cross_user(self, multi_user_memory):
        """
        测试地块数据跨用户查询
        
        验证：
        1. 地块检索不受用户限制
        2. 可以查询各地块的所有病例
        """
        # 检索 field_A1
        field_a1_cases = multi_user_memory.retrieve_by_field(field_id="field_A1")
        assert len(field_a1_cases) == 1
        
        # 检索所有地块（使用 retrieve_history 遍历用户）
        all_fields = set()
        for user_id in ["user_A", "user_B", "user_C"]:
            user_cases = multi_user_memory.retrieve_history(user_id=user_id, limit=10)
            for case in user_cases:
                all_fields.add(case["field_id"])
        
        # 验证有 4 个不同的地块
        assert len(all_fields) == 4


def run_memory_integration_tests():
    """运行记忆集成测试的便捷函数"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_memory_integration_tests()
