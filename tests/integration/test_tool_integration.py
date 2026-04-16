# -*- coding: utf-8 -*-
"""
工具调用集成测试

测试 ToolManager 工具管理器的核心功能：
1. 工具注册与注销
2. 工具调用与结果返回
3. 批量工具执行
4. 错误处理机制
5. 与规划层的集成
"""
import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock
import json
import tempfile

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestToolManagerBasic:
    """工具管理器基础功能测试"""
    
    @pytest.fixture
    def tool_manager(self):
        """创建 ToolManager 实例"""
        from src.tools.tool_manager import ToolManager
        return ToolManager()
    
    @pytest.fixture
    def mock_tools(self):
        """创建模拟工具"""
        from src.tools.base_tool import BaseTool
        
        # 模拟知识检索工具
        class MockKnowledgeTool(BaseTool):
            def __init__(self):
                super().__init__(name="knowledge_retrieval", description="知识检索工具")
            
            def get_name(self):
                return "knowledge_retrieval"
            
            def get_description(self):
                return "检索病害相关知识"
            
            def execute(self, **kwargs):
                disease_name = kwargs.get("disease_name", "")
                return {
                    "success": True,
                    "disease": disease_name,
                    "symptoms": ["症状 1", "症状 2"],
                    "causes": ["原因 1"],
                    "treatments": ["治疗方案 1"]
                }
        
        # 模拟防治工具
        class MockTreatmentTool(BaseTool):
            def __init__(self):
                super().__init__(name="treatment", description="防治方案生成工具")
            
            def get_name(self):
                return "treatment"
            
            def get_description(self):
                return "生成防治方案"
            
            def execute(self, **kwargs):
                disease = kwargs.get("disease_name", "")
                severity = kwargs.get("severity_level", "")
                return {
                    "success": True,
                    "treatment_plan": {
                        "disease": disease,
                        "severity": severity,
                        "recommendations": ["喷施药剂", "农业防治"]
                    }
                }
        
        # 模拟病例记录工具
        class MockCaseRecordTool(BaseTool):
            def __init__(self):
                super().__init__(name="case_record", description="病例记录工具")
            
            def get_name(self):
                return "case_record"
            
            def get_description(self):
                return "记录诊断病例"
            
            def execute(self, **kwargs):
                diagnosis_plan = kwargs.get("diagnosis_plan", {})
                return {
                    "success": True,
                    "case_id": "CASE_TEST_001",
                    "stored": True
                }
        
        return {
            "knowledge": MockKnowledgeTool(),
            "treatment": MockTreatmentTool(),
            "case_record": MockCaseRecordTool()
        }
    
    def test_tool_registration(self, tool_manager, mock_tools):
        """
        测试工具注册功能
        
        验证：
        1. 工具可以成功注册
        2. 注册后可以在工具列表中查到
        3. 重复注册会被覆盖
        """
        # 注册知识检索工具
        success = tool_manager.register_tool("knowledge", mock_tools["knowledge"])
        assert success is True
        assert "knowledge" in tool_manager.get_tool_names()
        
        # 注册防治工具
        success = tool_manager.register_tool("treatment", mock_tools["treatment"])
        assert success is True
        assert "treatment" in tool_manager.get_tool_names()
        
        # 验证工具数量
        assert len(tool_manager.get_tool_names()) == 2
        
        # 获取所有工具元数据
        metadata_list = tool_manager.get_all_tool_metadata()
        assert len(metadata_list) == 2
    
    def test_tool_unregistration(self, tool_manager, mock_tools):
        """
        测试工具注销功能
        
        验证：
        1. 工具可以成功注销
        2. 注销后不在工具列表中
        3. 注销不存在的工具返回 False
        """
        # 先注册
        tool_manager.register_tool("knowledge", mock_tools["knowledge"])
        assert "knowledge" in tool_manager.get_tool_names()
        
        # 注销工具
        success = tool_manager.unregister_tool("knowledge")
        assert success is True
        assert "knowledge" not in tool_manager.get_tool_names()
        
        # 注销不存在的工具
        success = tool_manager.unregister_tool("non_existent_tool")
        assert success is False
    
    def test_single_tool_execution(self, tool_manager, mock_tools):
        """
        测试单个工具执行
        
        验证：
        1. 工具可以正确执行
        2. 返回结果包含必要字段
        3. 参数正确传递给工具
        """
        # 注册工具
        tool_manager.register_tool("knowledge", mock_tools["knowledge"])
        
        # 执行工具
        result = tool_manager.execute_tool("knowledge", disease_name="条锈病")
        
        # 验证结果
        assert result["success"] is True
        assert result["disease"] == "条锈病"
        assert "symptoms" in result
        assert "treatments" in result
        assert "tool_name" in result
        assert "timestamp" in result
    
    def test_tool_execution_with_invalid_name(self, tool_manager):
        """
        测试执行不存在的工具
        
        验证：
        1. 执行不存在的工具返回错误
        2. 错误信息清晰明确
        """
        result = tool_manager.execute_tool("non_existent_tool")
        
        assert result["success"] is False
        assert "error" in result
        assert "不存在" in result["error"]
    
    def test_batch_tool_execution(self, tool_manager, mock_tools):
        """
        测试批量工具执行
        
        验证：
        1. 多个工具可以按顺序执行
        2. 返回结果列表
        3. 每个工具的结果独立
        """
        # 注册多个工具
        tool_manager.register_tool("knowledge", mock_tools["knowledge"])
        tool_manager.register_tool("treatment", mock_tools["treatment"])
        tool_manager.register_tool("case_record", mock_tools["case_record"])
        
        # 批量执行
        tool_calls = [
            {"tool_name": "knowledge", "params": {"disease_name": "条锈病"}},
            {"tool_name": "treatment", "params": {"disease_name": "条锈病", "severity_level": "中度"}},
            {"tool_name": "case_record", "params": {"diagnosis_plan": {"病害诊断": {"病害名称": "条锈病"}}}}
        ]
        
        results = tool_manager.execute_multiple(tool_calls)
        
        # 验证结果
        assert len(results) == 3
        assert all(r["success"] is True for r in results)
        assert results[0]["disease"] == "条锈病"
        assert results[1]["treatment_plan"]["severity"] == "中度"
        assert results[2]["case_id"] == "CASE_TEST_001"
    
    def test_execution_history(self, tool_manager, mock_tools):
        """
        测试执行历史记录
        
        验证：
        1. 执行历史被正确记录
        2. 可以获取历史记录
        3. 历史记录包含必要信息
        """
        # 注册并执行工具
        tool_manager.register_tool("knowledge", mock_tools["knowledge"])
        tool_manager.execute_tool("knowledge", disease_name="条锈病")
        tool_manager.execute_tool("knowledge", disease_name="白粉病")
        
        # 获取执行历史
        history = tool_manager.get_execution_history(limit=10)
        
        # 验证历史记录
        assert len(history) == 2
        assert history[0]["tool_name"] == "knowledge"
        assert history[0]["params"]["disease_name"] == "条锈病"
        assert history[1]["params"]["disease_name"] == "白粉病"
        
        # 清空历史
        tool_manager.clear_history()
        assert len(tool_manager.get_execution_history()) == 0
    
    def test_tool_status_tracking(self, tool_manager, mock_tools):
        """
        测试工具状态跟踪
        
        验证：
        1. 工具状态可以被查询
        2. 注册后状态为 True
        3. 注销后状态为 None 或 False
        """
        # 初始状态
        status = tool_manager.get_tool_status("knowledge")
        assert status is None
        
        # 注册后状态
        tool_manager.register_tool("knowledge", mock_tools["knowledge"])
        status = tool_manager.get_tool_status("knowledge")
        assert status is True
        
        # 注销后状态
        tool_manager.unregister_tool("knowledge")
        status = tool_manager.get_tool_status("knowledge")
        assert status is None


class TestToolIntegrationWithPlanning:
    """工具与规划层集成测试"""
    
    @pytest.fixture
    def integrated_system(self):
        """创建集成系统（规划层 + 工具层）"""
        from src.planning.planning_engine import PlanningEngine
        from src.tools.tool_manager import ToolManager
        from src.tools.base_tool import BaseTool
        
        # 创建规划引擎
        planning_engine = PlanningEngine()
        
        # 创建工具管理器
        tool_manager = ToolManager()
        
        # 创建模拟工具
        class MockKnowledgeTool(BaseTool):
            def __init__(self):
                super().__init__(name="knowledge_retrieval", description="知识检索")
            
            def get_name(self):
                return "knowledge_retrieval"
            
            def get_description(self):
                return "检索病害知识"
            
            def execute(self, **kwargs):
                return {
                    "success": True,
                    "knowledge": f"检索到{kwargs.get('disease_name')}的相关知识"
                }
        
        class MockTreatmentTool(BaseTool):
            def __init__(self):
                super().__init__(name="treatment", description="防治方案")
            
            def get_name(self):
                return "treatment"
            
            def get_description(self):
                return "生成防治方案"
            
            def execute(self, **kwargs):
                return {
                    "success": True,
                    "plan": f"为{kwargs.get('disease_name')}生成防治方案"
                }
        
        class MockFollowupTool(BaseTool):
            def __init__(self):
                super().__init__(name="followup", description="复查工具")
            
            def get_name(self):
                return "followup"
            
            def get_description(self):
                return "创建复查任务"
            
            def execute(self, **kwargs):
                return {
                    "success": True,
                    "followup_created": True
                }
        
        class MockCaseRecordTool(BaseTool):
            def __init__(self):
                super().__init__(name="case_record", description="病例记录")
            
            def get_name(self):
                return "case_record"
            
            def get_description(self):
                return "记录诊断病例"
            
            def execute(self, **kwargs):
                return {
                    "success": True,
                    "case_id": "CASE_AUTO_001"
                }
        
        # 注册工具
        tool_manager.register_tool("knowledge", MockKnowledgeTool())
        tool_manager.register_tool("treatment", MockTreatmentTool())
        tool_manager.register_tool("followup", MockFollowupTool())
        tool_manager.register_tool("case_record", MockCaseRecordTool())
        
        return {
            "planning": planning_engine,
            "tools": tool_manager
        }
    
    def test_execute_tools_from_diagnosis_plan(self, integrated_system):
        """
        测试根据诊断计划自动执行工具
        
        验证：
        1. 规划层生成诊断计划
        2. 工具层根据计划自动调用相应工具
        3. 返回所有工具的执行结果
        """
        planning_engine = integrated_system["planning"]
        tool_manager = integrated_system["tools"]
        
        # 创建认知输出
        cognition_output = {
            "disease_name": "条锈病",
            "confidence": 0.92,
            "severity_score": 0.65,
            "visual_features": ["黄色条状病斑"],
            "environmental_conditions": {
                "temperature": "15°C",
                "humidity": "高湿"
            }
        }
        
        # 生成诊断计划
        diagnosis_plan = planning_engine.generate_diagnosis_plan(cognition_output)
        
        # 验证计划结构完整
        assert "病害诊断" in diagnosis_plan
        assert "防治措施" in diagnosis_plan
        assert "复查计划" in diagnosis_plan
        
        # 根据计划执行工具
        tool_results = tool_manager.execute_from_plan(diagnosis_plan)
        
        # 验证工具执行结果
        assert isinstance(tool_results, list)
        assert len(tool_results) > 0
        
        # 验证至少执行了知识检索和病例记录
        tool_names = [r.get("tool_name") for r in tool_results]
        assert "knowledge" in tool_names or "case_record" in tool_names
    
    def test_tool_error_handling_in_plan_execution(self, integrated_system):
        """
        测试计划执行中的工具错误处理
        
        验证：
        1. 某个工具失败不影响其他工具执行
        2. 错误信息被正确记录
        """
        tool_manager = integrated_system["tools"]
        
        # 创建一个会失败的诊断计划
        invalid_plan = {
            "病害诊断": {"病害名称": ""},  # 空病害名称
            "防治措施": {},
            "复查计划": {}
        }
        
        # 执行工具（应该能处理空值）
        results = tool_manager.execute_from_plan(invalid_plan)
        
        # 验证返回了结果列表
        assert isinstance(results, list)


class TestToolErrorScenarios:
    """工具错误场景测试"""
    
    @pytest.fixture
    def tool_manager_with_failing_tool(self):
        """创建包含失败工具的 ToolManager"""
        from src.tools.tool_manager import ToolManager
        from src.tools.base_tool import BaseTool
        
        tool_manager = ToolManager()
        
        # 正常工具
        class NormalTool(BaseTool):
            def __init__(self):
                super().__init__(name="normal_tool", description="正常工具")
            
            def get_name(self):
                return "normal_tool"
            
            def get_description(self):
                return "一个正常的工具"
            
            def execute(self, **kwargs):
                return {"success": True, "message": "执行成功"}
        
        # 总是失败的工具
        class FailingTool(BaseTool):
            def __init__(self):
                super().__init__(name="failing_tool", description="失败工具")
            
            def get_name(self):
                return "failing_tool"
            
            def get_description(self):
                return "总是失败的工具"
            
            def execute(self, **kwargs):
                raise Exception("模拟工具执行失败")
        
        # 参数验证失败的工具
        class StrictTool(BaseTool):
            def __init__(self):
                super().__init__(name="strict_tool", description="严格工具")
            
            def get_name(self):
                return "strict_tool"
            
            def get_description(self):
                return "需要特定参数的工具"
            
            def validate_params(self, **kwargs):
                # 要求必须有 required_param
                return "required_param" in kwargs
            
            def execute(self, **kwargs):
                return {"success": True}
        
        tool_manager.register_tool("normal", NormalTool())
        tool_manager.register_tool("failing", FailingTool())
        tool_manager.register_tool("strict", StrictTool())
        
        return tool_manager
    
    def test_tool_exception_handling(self, tool_manager_with_failing_tool):
        """
        测试工具异常处理
        
        验证：
        1. 工具抛出异常时返回标准错误格式
        2. 异常信息被正确捕获
        """
        result = tool_manager_with_failing_tool.execute_tool("failing")
        
        assert result["success"] is False
        assert "error" in result
        assert "模拟工具执行失败" in result["error"]
    
    def test_tool_param_validation(self, tool_manager_with_failing_tool):
        """
        测试工具参数验证
        
        验证：
        1. 参数验证失败返回错误
        2. 参数验证通过则正常执行
        """
        # 缺少必需参数
        result = tool_manager_with_failing_tool.execute_tool("strict")
        assert result["success"] is False
        
        # 提供必需参数
        result = tool_manager_with_failing_tool.execute_tool("strict", required_param="value")
        assert result["success"] is True


def run_tool_integration_tests():
    """运行工具集成测试的便捷函数"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_tool_integration_tests()
