# -*- coding: utf-8 -*-
"""
工具执行层单元测试
测试所有工具类的核心功能
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.base_tool import BaseTool
from src.tools.diagnosis_tool import DiagnosisTool
from src.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool
from src.tools.treatment_tool import TreatmentTool
from src.tools.case_record_tool import CaseRecordTool
from src.tools.followup_tool import FollowupTool
from src.tools.history_comparison_tool import HistoryComparisonTool


class TestBaseTool:
    """BaseTool 测试类"""
    
    def test_base_tool_initialization(self):
        """测试基类初始化"""
        # Arrange & Act
        tool = BaseTool(name="TestTool", description="测试工具")
        
        # Assert
        assert tool.name == "TestTool"
        assert tool.description == "测试工具"
        assert tool.version == "1.0.0"
        assert tool.is_available is True
    
    def test_base_tool_metadata(self):
        """测试基类元数据"""
        # Arrange
        tool = BaseTool(name="TestTool", description="测试工具")
        
        # Act
        metadata = tool.get_metadata()
        
        # Assert
        assert "name" in metadata
        assert "description" in metadata
        assert "version" in metadata
        assert "created_at" in metadata
        assert "is_available" in metadata
    
    def test_base_tool_validate_params(self):
        """测试基类参数验证"""
        # Arrange
        tool = BaseTool()
        
        # Act
        result = tool.validate_params(param1="value1", param2="value2")
        
        # Assert
        assert result is True  # 基类默认返回 True
    
    def test_base_tool_initialize(self):
        """测试基类初始化方法"""
        # Arrange
        tool = BaseTool()
        
        # Act
        result = tool.initialize()
        
        # Assert
        assert result is True
    
    def test_base_tool_cleanup(self):
        """测试基类清理方法"""
        # Arrange
        tool = BaseTool()
        
        # Act & Assert (不应该抛出异常)
        tool.cleanup()
    
    def test_base_tool_str(self):
        """测试基类字符串表示"""
        # Arrange
        tool = BaseTool(name="TestTool", description="测试工具")
        
        # Act
        result = str(tool)
        
        # Assert
        assert "TestTool" in result
        assert "测试工具" in result


class TestDiagnosisTool:
    """DiagnosisTool 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.tool = DiagnosisTool()
    
    def test_diagnosis_tool_initialization(self):
        """测试诊断工具初始化"""
        # Arrange & Act
        tool = DiagnosisTool()
        
        # Assert
        assert tool is not None
        assert tool.get_name() == "DiagnosisTool"
    
    def test_diagnosis_tool_execute_success(self):
        """测试诊断工具成功执行"""
        # Arrange
        image_path = "test_image.jpg"
        disease_type = "条锈病"
        
        # Act
        result = self.tool.execute(
            image_path=image_path,
            disease_type=disease_type
        )
        
        # Assert
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["disease_type"] == disease_type
    
    def test_diagnosis_tool_execute_missing_params(self):
        """测试诊断工具缺少参数"""
        # Act
        result = self.tool.execute()
        
        # Assert
        assert result["success"] is False
        assert "error" in result
    
    def test_diagnosis_tool_validate_params(self):
        """测试诊断工具参数验证"""
        # Arrange
        valid_params = {"image_path": "test.jpg", "disease_type": "条锈病"}
        invalid_params = {}
        
        # Act
        valid_result = self.tool.validate_params(**valid_params)
        invalid_result = self.tool.validate_params(**invalid_params)
        
        # Assert
        assert valid_result is True
        assert invalid_result is False


class TestKnowledgeRetrievalTool:
    """KnowledgeRetrievalTool 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.tool = KnowledgeRetrievalTool()
    
    def test_knowledge_tool_initialization(self):
        """测试知识检索工具初始化"""
        # Arrange & Act
        tool = KnowledgeRetrievalTool()
        
        # Assert
        assert tool is not None
        assert tool.get_name() == "KnowledgeRetrievalTool"
    
    def test_knowledge_tool_execute_success(self):
        """测试知识检索成功"""
        # Arrange
        disease_type = "条锈病"
        
        # Act
        result = self.tool.execute(disease_type=disease_type)
        
        # Assert
        assert result["success"] is True
        assert "knowledge" in result["data"]
    
    def test_knowledge_tool_unknown_disease(self):
        """测试未知病害检索"""
        # Arrange
        disease_type = "未知病害"
        
        # Act
        result = self.tool.execute(disease_type=disease_type)
        
        # Assert
        assert result["success"] is False
        assert "error" in result


class TestTreatmentTool:
    """TreatmentTool 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.tool = TreatmentTool()
    
    def test_treatment_tool_initialization(self):
        """测试防治工具初始化"""
        # Arrange & Act
        tool = TreatmentTool()
        
        # Assert
        assert tool is not None
    
    def test_treatment_tool_execute_success(self):
        """测试防治工具成功执行"""
        # Arrange
        disease_type = "条锈病"
        severity = "中度"
        
        # Act
        result = self.tool.execute(
            disease_type=disease_type,
            severity=severity
        )
        
        # Assert
        assert result["success"] is True
        assert "treatment_plan" in result["data"]


class TestCaseRecordTool:
    """CaseRecordTool 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前的设置"""
        self.storage_path = tmp_path / "test_cases.json"
        self.tool = CaseRecordTool(storage_path=str(self.storage_path))
    
    def test_case_record_tool_initialization(self):
        """测试病例记录工具初始化"""
        # Arrange & Act
        tool = CaseRecordTool()
        
        # Assert
        assert tool is not None
    
    def test_case_record_tool_execute(self):
        """测试病例记录执行"""
        # Arrange
        case_data = {
            "user_id": "test_user",
            "disease_type": "条锈病",
            "severity": "中度"
        }
        
        # Act
        result = self.tool.execute(**case_data)
        
        # Assert
        assert result["success"] is True
        assert "case_id" in result["data"]


class TestFollowupTool:
    """FollowupTool 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.tool = FollowupTool()
    
    def test_followup_tool_initialization(self):
        """测试复查工具初始化"""
        # Arrange & Act
        tool = FollowupTool()
        
        # Assert
        assert tool is not None
    
    def test_followup_tool_execute(self):
        """测试复查工具执行"""
        # Arrange
        case_id = "CASE_001"
        
        # Act
        result = self.tool.execute(case_id=case_id)
        
        # Assert
        assert result["success"] is True


class TestHistoryComparisonTool:
    """HistoryComparisonTool 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.tool = HistoryComparisonTool()
    
    def test_history_comparison_tool_initialization(self):
        """测试历史对比工具初始化"""
        # Arrange & Act
        tool = HistoryComparisonTool()
        
        # Assert
        assert tool is not None
    
    def test_history_comparison_tool_execute(self):
        """测试历史对比执行"""
        # Arrange
        user_id = "test_user"
        
        # Act
        result = self.tool.execute(user_id=user_id)
        
        # Assert
        assert result["success"] is True


def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
