# -*- coding: utf-8 -*-
"""
记忆层模块单元测试
测试 CaseMemory 和 FeedbackHandler 的所有核心功能

测试覆盖:
1. CaseMemory 存储和检索功能
2. CaseMemory 持久化功能
3. CaseMemory 病情变化对比
4. CaseMemory 上下文注入
5. FeedbackHandler 反馈处理
6. FeedbackHandler 策略调整
7. 记忆引用机制
8. 集成测试

运行测试:
    python tests/test_memory.py
    
或使用 pytest:
    pytest tests/test_memory.py -v
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.case_memory import CaseMemory
from src.memory.feedback_handler import FeedbackHandler, FeedbackType, StrategyAdjustmentType


class TestCaseMemory(unittest.TestCase):
    """CaseMemory 单元测试类"""
    
    def setUp(self):
        """测试前准备：创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        self.test_storage_path = os.path.join(self.test_dir, "test_cases.json")
        self.case_memory = CaseMemory(storage_path=self.test_storage_path)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试初始化功能"""
        print("\n[测试] 初始化功能")
        
        # 验证存储路径
        self.assertEqual(self.case_memory.storage_path, self.test_storage_path)
        
        # 验证初始状态
        self.assertEqual(len(self.case_memory), 0)
        self.assertIsInstance(self.case_memory._cases, dict)
        self.assertIsInstance(self.case_memory._user_index, dict)
        self.assertIsInstance(self.case_memory._field_index, dict)
        
        print("✓ 初始化功能测试通过")
    
    def test_store_case(self):
        """测试病例存储功能"""
        print("\n[测试] 病例存储功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test_001.jpg",
            disease_type="条锈病",
            severity="中度",
            confidence=0.87,
            recommendation="使用三唑酮可湿性粉剂喷雾"
        )
        
        # 验证病例 ID 格式
        self.assertTrue(case_id.startswith("CASE_"))
        
        # 验证病例数量
        self.assertEqual(len(self.case_memory), 1)
        
        # 验证病例数据
        case = self.case_memory.retrieve_case(case_id)
        self.assertIsNotNone(case)
        self.assertEqual(case["user_id"], "test_user_001")
        self.assertEqual(case["field_id"], "test_field_001")
        self.assertEqual(case["disease_type"], "条锈病")
        self.assertEqual(case["severity"], "中度")
        self.assertEqual(case["confidence"], 0.87)
        
        # 验证索引
        self.assertIn("test_user_001", self.case_memory._user_index)
        self.assertIn("test_field_001", self.case_memory._field_index)
        
        print("✓ 病例存储功能测试通过")
    
    def test_retrieve_case(self):
        """测试病例检索功能"""
        print("\n[测试] 病例检索功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试推荐"
        )
        
        # 检索存在的病例
        case = self.case_memory.retrieve_case(case_id)
        self.assertIsNotNone(case)
        self.assertEqual(case["case_id"], case_id)
        
        # 检索不存在的病例
        non_existent = self.case_memory.retrieve_case("NON_EXISTENT_ID")
        self.assertIsNone(non_existent)
        
        print("✓ 病例检索功能测试通过")
    
    def test_retrieve_history(self):
        """测试历史病例检索功能"""
        print("\n[测试] 历史病例检索功能")
        
        # 存储多个病例
        import time
        case_ids = []
        for i in range(5):
            case_id = self.case_memory.store_case(
                user_id="test_user_001",
                field_id="test_field_001",
                image_path=f"data/images/test_{i:03d}.jpg",
                disease_type="条锈病",
                severity="中度",
                recommendation=f"推荐方案{i}"
            )
            case_ids.append(case_id)
            time.sleep(0.1)  # 确保时间戳不同
        
        # 检索全部历史
        history = self.case_memory.retrieve_history(user_id="test_user_001")
        self.assertEqual(len(history), 5)
        
        # 按数量限制检索
        limited = self.case_memory.retrieve_history(user_id="test_user_001", limit=3)
        self.assertEqual(len(limited), 3)
        
        # 验证时间倒序（最新的在前）
        self.assertEqual(limited[0]["case_id"], case_ids[-1])
        
        # 测试空用户
        empty = self.case_memory.retrieve_history(user_id="non_existent_user")
        self.assertEqual(len(empty), 0)
        
        print("✓ 历史病例检索功能测试通过")
    
    def test_retrieve_by_field(self):
        """测试按地块检索功能"""
        print("\n[测试] 按地块检索功能")
        
        # 存储同一地块的多个病例
        for i in range(3):
            self.case_memory.store_case(
                user_id="test_user_001",
                field_id="test_field_001",
                image_path=f"data/images/field1_{i}.jpg",
                disease_type="条锈病",
                severity="中度",
                recommendation=f"推荐{i}"
            )
        
        # 存储不同地块的病例
        self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_002",
            image_path="data/images/field2_0.jpg",
            disease_type="叶锈病",
            severity="轻度",
            recommendation="不同推荐"
        )
        
        # 检索特定地块
        field1_cases = self.case_memory.retrieve_by_field(field_id="test_field_001")
        self.assertEqual(len(field1_cases), 3)
        
        field2_cases = self.case_memory.retrieve_by_field(field_id="test_field_002")
        self.assertEqual(len(field2_cases), 1)
        self.assertEqual(field2_cases[0]["disease_type"], "叶锈病")
        
        print("✓ 按地块检索功能测试通过")
    
    def test_get_latest_case(self):
        """测试获取最新病例功能"""
        print("\n[测试] 获取最新病例功能")
        
        # 存储两个病例
        import time
        case_id_1 = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test_1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        time.sleep(0.1)
        
        case_id_2 = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test_2.jpg",
            disease_type="条锈病",
            severity="轻度",
            recommendation="推荐 2"
        )
        
        # 获取最新病例
        latest = self.case_memory.get_latest_case(user_id="test_user_001")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["case_id"], case_id_2)
        
        print("✓ 获取最新病例功能测试通过")
    
    def test_update_feedback(self):
        """测试更新用户反馈功能"""
        print("\n[测试] 更新用户反馈功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试推荐"
        )
        
        # 更新反馈
        success = self.case_memory.update_feedback(
            case_id=case_id,
            feedback_type="采纳建议",
            details="施药后病情好转",
            medication_applied=True,
            medication_name="三唑酮可湿性粉剂"
        )
        
        self.assertTrue(success)
        
        # 验证反馈数据
        case = self.case_memory.retrieve_case(case_id)
        self.assertIsNotNone(case["user_feedback"])
        self.assertEqual(case["user_feedback"]["feedback_type"], "采纳建议")
        self.assertEqual(case["user_feedback"]["medication_applied"], True)
        self.assertEqual(case["user_feedback"]["medication_name"], "三唑酮可湿性粉剂")
        
        # 测试更新不存在的病例
        failed = self.case_memory.update_feedback(
            case_id="NON_EXISTENT",
            feedback_type="测试",
            details="测试"
        )
        self.assertFalse(failed)
        
        print("✓ 更新用户反馈功能测试通过")
    
    def test_update_followup_result(self):
        """测试更新复查结果功能"""
        print("\n[测试] 更新复查结果功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试推荐"
        )
        
        # 更新复查结果
        success = self.case_memory.update_followup_result(
            case_id=case_id,
            disease_status="缓解",
            new_image_path="data/images/test_followup.jpg",
            new_disease_type="条锈病",
            new_severity="轻度",
            improvement=True
        )
        
        self.assertTrue(success)
        
        # 验证复查数据
        case = self.case_memory.retrieve_case(case_id)
        self.assertIsNotNone(case["followup_result"])
        self.assertEqual(case["followup_result"]["disease_status"], "缓解")
        self.assertEqual(case["followup_result"]["improvement"], True)
        self.assertEqual(case["followup_result"]["new_severity"], "轻度")
        
        print("✓ 更新复查结果功能测试通过")
    
    def test_compare_disease_progression(self):
        """测试病情变化对比功能"""
        print("\n[测试] 病情变化对比功能")
        
        # 存储两个病例（模拟病情改善）
        import time
        self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test_1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        time.sleep(0.1)
        
        self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test_2.jpg",
            disease_type="条锈病",
            severity="轻度",  # 改善
            recommendation="推荐 2"
        )
        
        # 对比病情
        comparison = self.case_memory.compare_disease_progression(
            user_id="test_user_001",
            field_id="test_field_001"
        )
        
        self.assertTrue(comparison["has_comparison"])
        self.assertEqual(comparison["progression"], "改善")
        self.assertIn("降至", comparison["severity_change"])
        self.assertTrue("summary" in comparison)
        
        # 测试病例不足
        single_case_memory = CaseMemory(storage_path=os.path.join(self.test_dir, "single.json"))
        single_case_memory.store_case(
            user_id="test_user_002",
            field_id="test_field_002",
            image_path="data/images/single.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        
        single_comparison = single_case_memory.compare_disease_progression(
            user_id="test_user_002"
        )
        self.assertFalse(single_comparison["has_comparison"])
        
        print("✓ 病情变化对比功能测试通过")
    
    def test_get_context_for_injection(self):
        """测试上下文注入功能"""
        print("\n[测试] 上下文注入功能")
        
        # 存储病例并添加反馈
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="使用三唑酮可湿性粉剂喷雾"
        )
        
        # 添加反馈
        self.case_memory.update_feedback(
            case_id=case_id,
            feedback_type="采纳建议",
            details="施药后好转",
            medication_applied=True,
            medication_name="三唑酮"
        )
        
        # 获取上下文
        context = self.case_memory.get_context_for_injection(
            user_id="test_user_001",
            field_id="test_field_001"
        )
        
        self.assertIsNotNone(context)
        self.assertIn("【历史病例记忆】", context)
        self.assertIn("条锈病", context)
        self.assertIn("三唑酮", context)
        
        # 测试无病例情况
        empty_context = self.case_memory.get_context_for_injection(
            user_id="non_existent_user"
        )
        self.assertIsNone(empty_context)
        
        print("✓ 上下文注入功能测试通过")
    
    def test_persistence(self):
        """测试持久化功能"""
        print("\n[测试] 持久化功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试推荐"
        )
        
        # 验证文件存在
        self.assertTrue(os.path.exists(self.test_storage_path))
        
        # 创建新的 CaseMemory 实例（从磁盘加载）
        new_case_memory = CaseMemory(storage_path=self.test_storage_path)
        
        # 验证数据已加载
        self.assertEqual(len(new_case_memory), 1)
        loaded_case = new_case_memory.retrieve_case(case_id)
        self.assertIsNotNone(loaded_case)
        self.assertEqual(loaded_case["disease_type"], "条锈病")
        
        print("✓ 持久化功能测试通过")
    
    def test_get_statistics(self):
        """测试统计信息功能"""
        print("\n[测试] 统计信息功能")
        
        # 存储多个病例
        for i in range(3):
            self.case_memory.store_case(
                user_id=f"user_{i % 2}",  # 2 个用户
                field_id=f"field_{i}",
                image_path=f"data/images/test_{i}.jpg",
                disease_type="条锈病" if i % 2 == 0 else "叶锈病",
                severity="中度",
                recommendation=f"推荐{i}"
            )
        
        # 获取统计
        stats = self.case_memory.get_statistics()
        
        self.assertEqual(stats["total_cases"], 3)
        self.assertEqual(stats["unique_users"], 2)
        self.assertEqual(stats["unique_fields"], 3)
        self.assertIn("disease_distribution", stats)
        self.assertIn("severity_distribution", stats)
        
        print("✓ 统计信息功能测试通过")
    
    def test_delete_case(self):
        """测试删除病例功能"""
        print("\n[测试] 删除病例功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试"
        )
        
        # 删除病例
        success = self.case_memory.delete_case(case_id)
        self.assertTrue(success)
        self.assertEqual(len(self.case_memory), 0)
        
        # 删除不存在的病例
        failed = self.case_memory.delete_case("NON_EXISTENT")
        self.assertFalse(failed)
        
        print("✓ 删除病例功能测试通过")
    
    def test_clear_all(self):
        """测试清空所有数据功能"""
        print("\n[测试] 清空所有数据功能")
        
        # 存储多个病例
        for i in range(5):
            self.case_memory.store_case(
                user_id=f"user_{i}",
                field_id=f"field_{i}",
                image_path=f"data/images/test_{i}.jpg",
                disease_type="条锈病",
                severity="中度",
                recommendation=f"推荐{i}"
            )
        
        # 清空
        success = self.case_memory.clear_all()
        self.assertTrue(success)
        self.assertEqual(len(self.case_memory), 0)
        
        # 验证持久化
        new_memory = CaseMemory(storage_path=self.test_storage_path)
        self.assertEqual(len(new_memory), 0)
        
        print("✓ 清空所有数据功能测试通过")


class TestFeedbackHandler(unittest.TestCase):
    """FeedbackHandler 单元测试类"""
    
    def setUp(self):
        """测试前准备：创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        self.test_storage_path = os.path.join(self.test_dir, "test_feedback.json")
        self.case_memory = CaseMemory(storage_path=self.test_storage_path)
        self.feedback_handler = FeedbackHandler(case_memory=self.case_memory)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试初始化功能"""
        print("\n[测试] FeedbackHandler 初始化")
        
        self.assertIsNotNone(self.feedback_handler._feedback_to_strategy_map)
        self.assertIsNotNone(self.feedback_handler._disease_strategies)
        self.assertEqual(len(self.feedback_handler._feedback_history), 0)
        
        print("✓ FeedbackHandler 初始化测试通过")
    
    def test_parse_feedback(self):
        """测试反馈解析功能"""
        print("\n[测试] 反馈解析功能")
        
        test_cases = [
            ("采纳了建议，病情好转", FeedbackType.ADOPTED.value),
            ("施药后有效，病斑减少", FeedbackType.MEDICATION_EFFECTIVE.value),
            ("施药后没效果", FeedbackType.MEDICATION_INEFFECTIVE.value),
            ("病情加重了，更严重", FeedbackType.DISEASE_WORSENED.value),
            ("病情自然缓解", FeedbackType.DISEASE_IMPROVED.value),
            ("需要专家复核", FeedbackType.NEEDS_MANUAL_REVIEW.value)
        ]
        
        for text, expected_type in test_cases:
            parsed = self.feedback_handler.parse_feedback(text)
            self.assertEqual(parsed["parsed_type"], expected_type, 
                           f"解析失败：'{text}' 应该解析为 '{expected_type}'")
            self.assertGreater(parsed["confidence"], 0.5)
        
        print("✓ 反馈解析功能测试通过")
    
    def test_process_feedback(self):
        """测试反馈处理功能"""
        print("\n[测试] 反馈处理功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="使用三唑酮"
        )
        
        # 处理反馈（施药有效）
        result = self.feedback_handler.process_feedback(
            case_id=case_id,
            feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
            details="使用三唑酮后病斑明显减少",
            medication_name="三唑酮",
            medication_applied=True,
            disease_status="改善"
        )
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["case_id"], case_id)
        self.assertGreater(len(result["adjustments_applied"]), 0)
        
        # 验证病例已更新
        case = self.case_memory.retrieve_case(case_id)
        self.assertIsNotNone(case["user_feedback"])
        self.assertIsNotNone(case["followup_result"])
        self.assertEqual(case["followup_result"]["disease_status"], "改善")
        
        print("✓ 反馈处理功能测试通过")
    
    def test_strategy_adjustments(self):
        """测试策略调整功能"""
        print("\n[测试] 策略调整功能")
        
        # 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试"
        )
        
        # 处理多个反馈
        for i in range(3):
            self.feedback_handler.process_feedback(
                case_id=case_id,
                feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
                details=f"测试反馈{i}",
                medication_name="三唑酮"
            )
        
        # 获取策略调整建议
        suggestions = self.feedback_handler.get_strategy_adjustments(disease_type="条锈病")
        
        self.assertIn("current_confidence", suggestions)
        self.assertIn("recommendation_priority", suggestions)
        self.assertGreater(suggestions["confidence_adjustment"], 0)
        
        print("✓ 策略调整功能测试通过")
    
    def test_apply_strategy_adjustment(self):
        """测试手动应用策略调整功能"""
        print("\n[测试] 手动应用策略调整")
        
        # 应用置信度调整
        success = self.feedback_handler.apply_strategy_adjustment(
            disease_type="条锈病",
            adjustment_type="confidence",
            adjustment_value=0.05,
            reason="测试调整"
        )
        self.assertTrue(success)
        
        # 验证调整
        strategy = self.feedback_handler._disease_strategies["条锈病"]
        self.assertEqual(strategy["confidence_adjustment"], 0.05)
        
        # 应用优先级调整
        success = self.feedback_handler.apply_strategy_adjustment(
            disease_type="条锈病",
            adjustment_type="priority",
            adjustment_value=-0.1,
            reason="测试"
        )
        self.assertTrue(success)
        self.assertEqual(strategy["recommendation_priority"], 0.9)
        
        print("✓ 手动应用策略调整测试通过")
    
    def test_get_adjusted_recommendation(self):
        """测试获取调整后的推荐方案功能"""
        print("\n[测试] 获取调整后的推荐方案")
        
        # 获取推荐
        recommendation = self.feedback_handler.get_adjusted_recommendation(
            disease_type="条锈病",
            severity="中度"
        )
        
        self.assertIn("disease_type", recommendation)
        self.assertIn("recommendation_text", recommendation)
        self.assertIn("recommended_medications", recommendation)
        self.assertGreater(len(recommendation["recommended_medications"]), 0)
        
        # 测试未知病害
        unknown = self.feedback_handler.get_adjusted_recommendation(
            disease_type="未知病害",
            severity="中度"
        )
        self.assertIn("error", unknown)
        
        print("✓ 获取调整后的推荐方案测试通过")
    
    def test_feedback_statistics(self):
        """测试反馈统计功能"""
        print("\n[测试] 反馈统计功能")
        
        # 添加反馈
        case_id = self.case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path="data/images/test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试"
        )
        
        for i in range(5):
            self.feedback_handler.process_feedback(
                case_id=case_id,
                feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
                details=f"测试{i}"
            )
        
        # 获取统计
        stats = self.feedback_handler.get_feedback_statistics()
        
        self.assertEqual(stats["total_feedback"], 5)
        self.assertIn("type_distribution", stats)
        
        print("✓ 反馈统计功能测试通过")


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.test_dir, "integration_test.json")
        self.case_memory = CaseMemory(storage_path=self.memory_path)
        self.feedback_handler = FeedbackHandler(case_memory=self.case_memory)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        print("\n[集成测试] 完整工作流程")
        
        # 1. 存储初始病例
        case_id_1 = self.case_memory.store_case(
            user_id="integration_user",
            field_id="integration_field",
            image_path="data/images/integration_1.jpg",
            disease_type="条锈病",
            severity="中度",
            confidence=0.85,
            recommendation="使用三唑酮可湿性粉剂喷雾"
        )
        
        # 2. 获取上下文注入信息（第一个病例也会有上下文）
        context_before = self.case_memory.get_context_for_injection(
            user_id="integration_user",
            field_id="integration_field"
        )
        self.assertIsNotNone(context_before)
        self.assertIn("条锈病", context_before)
        
        import time
        time.sleep(0.1)
        
        # 3. 存储复查病例
        case_id_2 = self.case_memory.store_case(
            user_id="integration_user",
            field_id="integration_field",
            image_path="data/images/integration_2.jpg",
            disease_type="条锈病",
            severity="轻度",  # 改善
            confidence=0.90,
            recommendation="继续观察"
        )
        
        # 4. 处理用户反馈
        feedback_result = self.feedback_handler.process_feedback(
            case_id=case_id_1,
            feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
            details="施药后病情明显好转",
            medication_name="三唑酮",
            medication_applied=True,
            disease_status="改善"
        )
        self.assertTrue(feedback_result["success"])
        
        # 5. 获取上下文注入信息（现在应该有内容）
        context_after = self.case_memory.get_context_for_injection(
            user_id="integration_user",
            field_id="integration_field"
        )
        self.assertIsNotNone(context_after)
        self.assertIn("条锈病", context_after)
        
        # 6. 对比病情变化
        comparison = self.case_memory.compare_disease_progression(
            user_id="integration_user",
            field_id="integration_field"
        )
        self.assertTrue(comparison["has_comparison"])
        self.assertEqual(comparison["progression"], "改善")
        
        # 7. 获取策略调整建议
        suggestions = self.feedback_handler.get_strategy_adjustments(disease_type="条锈病")
        self.assertGreater(suggestions["confidence_adjustment"], 0)
        
        # 8. 获取调整后的推荐
        recommendation = self.feedback_handler.get_adjusted_recommendation(
            disease_type="条锈病",
            severity="轻度"
        )
        self.assertIn("recommendation_text", recommendation)
        
        # 9. 验证持久化
        new_memory = CaseMemory(storage_path=self.memory_path)
        self.assertEqual(len(new_memory), 2)
        
        print("✓ 完整工作流程测试通过")
    
    def test_memory_reference_mechanism(self):
        """测试记忆引用机制"""
        print("\n[集成测试] 记忆引用机制")
        
        # 存储多个病例
        import time
        for i in range(3):
            self.case_memory.store_case(
                user_id="ref_user",
                field_id="ref_field",
                image_path=f"data/images/ref_{i}.jpg",
                disease_type="条锈病",
                severity="中度",
                recommendation=f"推荐方案{i}"
            )
            time.sleep(0.1)
        
        # 再次诊断时检索历史
        latest = self.case_memory.get_latest_case(
            user_id="ref_user",
            field_id="ref_field"
        )
        
        self.assertIsNotNone(latest)
        self.assertEqual(latest["disease_type"], "条锈病")
        
        # 获取历史病例数量
        history = self.case_memory.retrieve_history(
            user_id="ref_user",
            limit=10
        )
        self.assertEqual(len(history), 3)
        
        print("✓ 记忆引用机制测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("🧪 开始运行记忆层模块单元测试")
    print("=" * 80)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestCaseMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print(f"测试结果：{result.testsRun} 个测试，{len(result.failures)} 个失败，{len(result.errors)} 个错误")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
