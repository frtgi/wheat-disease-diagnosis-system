# -*- coding: utf-8 -*-
"""
反馈记忆层单元测试
测试 CaseMemory 和 FeedbackHandler 的核心功能
"""
import pytest
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.case_memory import CaseMemory
from src.memory.feedback_handler import FeedbackHandler, FeedbackType, StrategyAdjustmentType


class TestCaseMemory:
    """CaseMemory 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前的设置"""
        self.storage_path = tmp_path / "test_case_memories.json"
        self.case_memory = CaseMemory(storage_path=str(self.storage_path))
    
    def test_case_memory_initialization(self):
        """测试病例记忆初始化"""
        # Arrange & Act
        case_memory = CaseMemory()
        
        # Assert
        assert case_memory is not None
        assert len(case_memory) == 0
    
    def test_store_case_success(self):
        """测试成功存储病例"""
        # Arrange
        user_id = "test_user_001"
        image_path = "data/images/test.jpg"
        disease_type = "条锈病"
        severity = "中度"
        recommendation = "使用三唑酮可湿性粉剂喷雾"
        
        # Act
        case_id = self.case_memory.store_case(
            user_id=user_id,
            image_path=image_path,
            disease_type=disease_type,
            severity=severity,
            recommendation=recommendation
        )
        
        # Assert
        assert case_id is not None
        assert case_id.startswith("CASE_")
        assert len(self.case_memory) == 1
    
    def test_retrieve_case_success(self):
        """测试检索病例"""
        # Arrange
        case_id = self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="测试推荐"
        )
        
        # Act
        retrieved = self.case_memory.retrieve_case(case_id)
        
        # Assert
        assert retrieved is not None
        assert retrieved["case_id"] == case_id
        assert retrieved["disease_type"] == "条锈病"
    
    def test_retrieve_case_not_found(self):
        """测试检索不存在的病例"""
        # Act
        result = self.case_memory.retrieve_case("NON_EXISTENT_CASE")
        
        # Assert
        assert result is None
    
    def test_retrieve_history(self):
        """测试检索用户历史病例"""
        # Arrange
        user_id = "test_user_001"
        self.case_memory.store_case(
            user_id=user_id,
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        self.case_memory.store_case(
            user_id=user_id,
            image_path="test2.jpg",
            disease_type="叶锈病",
            severity="轻度",
            recommendation="推荐 2"
        )
        
        # Act
        history = self.case_memory.retrieve_history(user_id=user_id, limit=5)
        
        # Assert
        assert len(history) == 2
        # 验证按时间倒序
        assert history[0]["upload_timestamp"] >= history[1]["upload_timestamp"]
    
    def test_retrieve_by_field(self):
        """测试按地块检索病例"""
        # Arrange
        field_id = "test_field_001"
        self.case_memory.store_case(
            user_id="user1",
            field_id=field_id,
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        self.case_memory.store_case(
            user_id="user2",
            field_id=field_id,
            image_path="test2.jpg",
            disease_type="条锈病",
            severity="轻度",
            recommendation="推荐 2"
        )
        
        # Act
        field_cases = self.case_memory.retrieve_by_field(field_id=field_id)
        
        # Assert
        assert len(field_cases) == 2
    
    def test_get_latest_case(self):
        """测试获取最新病例"""
        # Arrange
        user_id = "test_user_001"
        self.case_memory.store_case(
            user_id=user_id,
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        import time
        time.sleep(0.1)
        self.case_memory.store_case(
            user_id=user_id,
            image_path="test2.jpg",
            disease_type="叶锈病",
            severity="轻度",
            recommendation="推荐 2"
        )
        
        # Act
        latest = self.case_memory.get_latest_case(user_id=user_id)
        
        # Assert
        assert latest is not None
        assert latest["disease_type"] == "叶锈病"
    
    def test_update_feedback(self):
        """测试更新用户反馈"""
        # Arrange
        case_id = self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        
        # Act
        success = self.case_memory.update_feedback(
            case_id=case_id,
            feedback_type="采纳建议",
            details="施药后病情好转",
            medication_applied=True,
            medication_name="三唑酮"
        )
        
        # Assert
        assert success is True
        case = self.case_memory.retrieve_case(case_id)
        assert case["user_feedback"] is not None
        assert case["user_feedback"]["medication_applied"] is True
    
    def test_update_followup_result(self):
        """测试更新复查结果"""
        # Arrange
        case_id = self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        
        # Act
        success = self.case_memory.update_followup_result(
            case_id=case_id,
            disease_status="缓解",
            improvement=True
        )
        
        # Assert
        assert success is True
        case = self.case_memory.retrieve_case(case_id)
        assert case["followup_result"] is not None
        assert case["followup_result"]["improvement"] is True
    
    def test_compare_disease_progression(self):
        """测试病情变化对比"""
        # Arrange
        user_id = "test_user_001"
        field_id = "test_field_001"
        
        self.case_memory.store_case(
            user_id=user_id,
            field_id=field_id,
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        import time
        time.sleep(0.1)
        self.case_memory.store_case(
            user_id=user_id,
            field_id=field_id,
            image_path="test2.jpg",
            disease_type="条锈病",
            severity="轻度",
            recommendation="推荐 2"
        )
        
        # Act
        comparison = self.case_memory.compare_disease_progression(
            user_id=user_id,
            field_id=field_id
        )
        
        # Assert
        assert comparison["has_comparison"] is True
        assert comparison["progression"] == "改善"
    
    def test_compare_insufficient_cases(self):
        """测试病例数量不足时的对比"""
        # Arrange
        user_id = "test_user_001"
        self.case_memory.store_case(
            user_id=user_id,
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        
        # Act
        comparison = self.case_memory.compare_disease_progression(user_id=user_id)
        
        # Assert
        assert comparison["has_comparison"] is False
    
    def test_get_context_for_injection(self):
        """测试获取上下文注入信息"""
        # Arrange
        user_id = "test_user_001"
        self.case_memory.store_case(
            user_id=user_id,
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐使用三唑酮"
        )
        
        # Act
        context = self.case_memory.get_context_for_injection(user_id=user_id)
        
        # Assert
        assert context is not None
        assert "条锈病" in context
    
    def test_delete_case(self):
        """测试删除病例"""
        # Arrange
        case_id = self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        
        # Act
        success = self.case_memory.delete_case(case_id)
        
        # Assert
        assert success is True
        assert len(self.case_memory) == 0
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # Arrange
        self.case_memory.store_case(
            user_id="user1",
            image_path="test1.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐 1"
        )
        self.case_memory.store_case(
            user_id="user2",
            image_path="test2.jpg",
            disease_type="叶锈病",
            severity="轻度",
            recommendation="推荐 2"
        )
        
        # Act
        stats = self.case_memory.get_statistics()
        
        # Assert
        assert stats["total_cases"] == 2
        assert stats["unique_users"] == 2
        assert "disease_distribution" in stats
    
    def test_clear_all(self):
        """测试清空所有病例"""
        # Arrange
        self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        
        # Act
        success = self.case_memory.clear_all()
        
        # Assert
        assert success is True
        assert len(self.case_memory) == 0
    
    def test_export_to_json(self, tmp_path):
        """测试导出到 JSON"""
        # Arrange
        self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        output_path = tmp_path / "export.json"
        
        # Act
        success = self.case_memory.export_to_json(str(output_path))
        
        # Assert
        assert success is True
        assert output_path.exists()


class TestFeedbackHandler:
    """FeedbackHandler 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前的设置"""
        self.case_memory = CaseMemory(storage_path=str(tmp_path / "test_memories.json"))
        self.feedback_handler = FeedbackHandler(case_memory=self.case_memory)
    
    def test_feedback_handler_initialization(self):
        """测试反馈处理器初始化"""
        # Arrange & Act
        handler = FeedbackHandler()
        
        # Assert
        assert handler is not None
        assert len(handler._feedback_history) == 0
    
    def test_parse_feedback_adopted(self):
        """测试解析采纳建议反馈"""
        # Arrange
        feedback_text = "采纳了建议，病情好转"
        
        # Act
        result = self.feedback_handler.parse_feedback(feedback_text)
        
        # Assert
        assert result["parsed_type"] == FeedbackType.ADOPTED.value
    
    def test_parse_feedback_medication_effective(self):
        """测试解析施药有效反馈"""
        # Arrange
        feedback_text = "施药后病情明显好转，效果很好"
        
        # Act
        result = self.feedback_handler.parse_feedback(feedback_text)
        
        # Assert
        assert result["parsed_type"] == FeedbackType.MEDICATION_EFFECTIVE.value
    
    def test_parse_feedback_disease_worsened(self):
        """测试解析病情恶化反馈"""
        # Arrange
        feedback_text = "病情加重了，扩散很严重"
        
        # Act
        result = self.feedback_handler.parse_feedback(feedback_text)
        
        # Assert
        assert result["parsed_type"] == FeedbackType.DISEASE_WORSENED.value
    
    def test_process_feedback_success(self):
        """测试处理反馈成功"""
        # Arrange
        case_id = self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        
        # Act
        result = self.feedback_handler.process_feedback(
            case_id=case_id,
            feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
            details="施药后病情好转",
            medication_name="三唑酮"
        )
        
        # Assert
        assert result["success"] is True
        assert len(result["adjustments_applied"]) > 0
    
    def test_get_strategy_adjustments(self):
        """测试获取策略调整建议"""
        # Act
        suggestions = self.feedback_handler.get_strategy_adjustments(disease_type="条锈病")
        
        # Assert
        assert "current_confidence" in suggestions
        assert "recommended_medications" in suggestions
    
    def test_apply_strategy_adjustment(self):
        """测试应用策略调整"""
        # Act
        success = self.feedback_handler.apply_strategy_adjustment(
            disease_type="条锈病",
            adjustment_type="confidence",
            adjustment_value=0.05,
            reason="测试调整"
        )
        
        # Assert
        assert success is True
    
    def test_get_adjusted_recommendation(self):
        """测试获取调整后的推荐方案"""
        # Act
        recommendation = self.feedback_handler.get_adjusted_recommendation(
            disease_type="条锈病",
            severity="中度"
        )
        
        # Assert
        assert "recommendation_text" in recommendation
        assert "confidence" in recommendation
    
    def test_get_feedback_statistics(self):
        """测试获取反馈统计"""
        # Arrange
        case_id = self.case_memory.store_case(
            user_id="test_user",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="推荐"
        )
        self.feedback_handler.process_feedback(
            case_id=case_id,
            feedback_type=FeedbackType.ADOPTED.value,
            details="测试反馈"
        )
        
        # Act
        stats = self.feedback_handler.get_feedback_statistics()
        
        # Assert
        assert stats["total_feedback"] == 1


def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
