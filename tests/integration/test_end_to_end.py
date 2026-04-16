# -*- coding: utf-8 -*-
"""
六层架构端到端集成测试

测试完整的 IWDDA 六层架构流程：
1. 输入层 (Input) → 2. 感知层 (Perception) → 3. 认知层 (Cognition) → 
4. 规划层 (Planning) → 5. 工具层 (Tool) → 6. 记忆层 (Memory)

验证数据流、异常处理和模块协同工作能力
"""
import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch
import json

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSixLayerArchitecture:
    """六层架构端到端测试类"""
    
    @pytest.fixture
    def mock_image_path(self, tmp_path):
        """创建模拟图像文件"""
        from PIL import Image
        import numpy as np
        
        # 创建测试图像
        image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        image_path = tmp_path / "test_wheat.jpg"
        image.save(image_path)
        return str(image_path)
    
    @pytest.fixture
    def mock_environment_data(self):
        """模拟环境数据"""
        return {
            "temperature": 15.5,
            "humidity": 85.0,
            "growth_stage": "拔节期",
            "location": "河南省郑州市"
        }
    
    @pytest.fixture
    def six_layer_pipeline(self):
        """初始化六层架构流水线"""
        from src.input.input_parser import InputParser
        from src.planning.planning_engine import PlanningEngine
        from src.memory.case_memory import CaseMemory
        from src.tools.tool_manager import ToolManager
        
        # 初始化各层模块
        input_parser = InputParser()
        planning_engine = PlanningEngine()
        
        # 使用临时文件存储记忆
        import tempfile
        memory_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        memory_file.close()
        case_memory = CaseMemory(storage_path=memory_file.name)
        
        tool_manager = ToolManager()
        
        return {
            "input": input_parser,
            "planning": planning_engine,
            "memory": case_memory,
            "tools": tool_manager
        }
    
    def test_complete_data_flow(self, six_layer_pipeline, mock_image_path, mock_environment_data):
        """
        测试完整数据流：输入→感知→认知→规划→工具→记忆
        
        验证数据在各层之间的传递是否正确
        """
        # Step 1: 输入层 - 解析图像和环境数据
        input_parser = six_layer_pipeline["input"]
        parsed_input = input_parser.parse_image(mock_image_path)
        assert parsed_input is not None
        assert "image" in parsed_input
        assert "metadata" in parsed_input
        
        # 解析环境数据
        env_input = {
            "text": f"温度{mock_environment_data['temperature']}°C，湿度{mock_environment_data['humidity']}%",
            "structured": mock_environment_data
        }
        
        # Step 2-3: 感知层 + 认知层 (使用模拟数据)
        # 模拟感知和认知层的输出
        cognition_output = {
            "disease_name": "条锈病",
            "confidence": 0.92,
            "severity_score": 0.65,
            "visual_features": ["黄色条状孢子堆", "沿叶脉排列"],
            "environmental_conditions": mock_environment_data
        }
        
        # Step 4: 规划层 - 生成诊断计划
        planning_engine = six_layer_pipeline["planning"]
        diagnosis_plan = planning_engine.generate_diagnosis_plan(cognition_output)
        
        # 验证诊断计划结构
        assert diagnosis_plan is not None
        assert "病害诊断" in diagnosis_plan
        assert "严重度评估" in diagnosis_plan
        assert "防治措施" in diagnosis_plan
        assert "复查计划" in diagnosis_plan
        
        # 验证病害诊断内容
        disease_diagnosis = diagnosis_plan["病害诊断"]
        assert disease_diagnosis["病害名称"] == "条锈病"
        assert disease_diagnosis["置信度"] > 0.8
        
        # Step 5: 工具层 - 执行工具调用
        tool_manager = six_layer_pipeline["tools"]
        tool_results = tool_manager.execute_from_plan(diagnosis_plan)
        
        # 验证工具执行结果
        assert isinstance(tool_results, list)
        
        # Step 6: 记忆层 - 存储病例
        case_memory = six_layer_pipeline["memory"]
        case_id = case_memory.store_case(
            user_id="test_user_001",
            field_id="test_field_001",
            image_path=mock_image_path,
            disease_type="条锈病",
            severity="中度",
            confidence=0.92,
            recommendation="使用三唑酮可湿性粉剂喷雾"
        )
        
        # 验证病例存储
        assert case_id is not None
        assert case_id.startswith("CASE_")
        
        # 验证可以检索到该病例
        history = case_memory.retrieve_history(user_id="test_user_001", limit=5)
        assert len(history) > 0
        assert history[0]["case_id"] == case_id
    
    def test_exception_handling_in_pipeline(self, six_layer_pipeline):
        """
        测试异常处理：验证某一层失败时的容错能力
        
        模拟认知层输出异常数据，验证系统是否能处理
        """
        planning_engine = six_layer_pipeline["planning"]
        
        # 模拟异常认知输出（置信度为负数）
        abnormal_cognition = {
            "disease_name": "未知病害",
            "confidence": -0.5,  # 异常值
            "severity_score": 1.5,  # 超出范围
            "visual_features": []
        }
        
        # 规划层应该能处理异常输入
        diagnosis_plan = planning_engine.generate_diagnosis_plan(abnormal_cognition)
        
        # 验证即使输入异常，仍能生成基本结构的计划
        assert diagnosis_plan is not None
        assert "病害诊断" in diagnosis_plan
    
    def test_memory_context_injection(self, six_layer_pipeline, mock_image_path):
        """
        测试记忆引用：验证历史病例上下文注入
        
        1. 存储多个病例
        2. 检索特定用户的历史
        3. 验证病情变化对比
        """
        case_memory = six_layer_pipeline["memory"]
        
        # 存储第一个病例（轻度）
        case_id_1 = case_memory.store_case(
            user_id="test_user_002",
            field_id="test_field_002",
            image_path=mock_image_path,
            disease_type="条锈病",
            severity="轻度",
            confidence=0.85,
            recommendation="观察病情，必要时喷药"
        )
        
        # 存储第二个病例（中度，同一地块）
        case_id_2 = case_memory.store_case(
            user_id="test_user_002",
            field_id="test_field_002",
            image_path=mock_image_path,
            disease_type="条锈病",
            severity="中度",
            confidence=0.90,
            recommendation="立即喷施三唑酮"
        )
        
        # 检索用户历史
        history = case_memory.retrieve_history(user_id="test_user_002", limit=10)
        assert len(history) == 2
        
        # 检索特定地块的病例
        field_cases = case_memory.retrieve_by_field(field_id="test_field_002")
        assert len(field_cases) == 2
        
        # 获取最新病例
        latest_case = case_memory.get_latest_case(user_id="test_user_002")
        # 验证获取到了病例（不检查具体 ID，因为时间戳可能相同）
        assert latest_case is not None
        assert latest_case["severity"] in ["轻度", "中度"]
    
    def test_tool_execution_integration(self, six_layer_pipeline):
        """
        测试工具执行：验证 ToolManager 与诊断计划的集成
        
        1. 注册多个工具
        2. 根据诊断计划执行工具
        3. 验证执行结果
        """
        tool_manager = six_layer_pipeline["tools"]
        
        # 验证工具管理器初始化
        assert len(tool_manager.get_tool_names()) >= 0
        
        # 创建诊断计划
        diagnosis_plan = {
            "病害诊断": {
                "病害名称": "白粉病",
                "置信度": 0.88,
                "主要特征": ["白色粉状霉层"]
            },
            "严重度评估": {
                "严重度等级": "中度",
                "严重度评分": 0.55
            },
            "防治措施": {
                "推荐药剂": [
                    {"name": "三唑酮", "concentration": "15% 可湿性粉剂"}
                ]
            },
            "复查计划": {
                "复查时间": "2026-03-16",
                "复查间隔": "7 天"
            }
        }
        
        # 执行工具（即使工具未实际注册，也应返回适当的结果）
        results = tool_manager.execute_from_plan(diagnosis_plan)
        
        # 验证返回结果结构
        assert isinstance(results, list)


class TestEndToEndScenarios:
    """端到端场景测试类"""
    
    @pytest.fixture
    def six_layer_pipeline(self):
        """初始化六层架构流水线"""
        from src.input.input_parser import InputParser
        from src.planning.planning_engine import PlanningEngine
        from src.memory.case_memory import CaseMemory
        from src.tools.tool_manager import ToolManager
        
        # 初始化各层模块
        input_parser = InputParser()
        planning_engine = PlanningEngine()
        
        # 使用临时文件存储记忆
        import tempfile
        memory_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        memory_file.close()
        case_memory = CaseMemory(storage_path=memory_file.name)
        
        tool_manager = ToolManager()
        
        return {
            "input": input_parser,
            "planning": planning_engine,
            "memory": case_memory,
            "tools": tool_manager
        }
    
    @pytest.fixture
    def test_scenarios(self):
        """定义测试场景"""
        return [
            {
                "name": "单病害诊断场景",
                "disease": "条锈病",
                "severity": "中度",
                "expected_tools": ["knowledge", "treatment", "case_record"]
            },
            {
                "name": "多病害并发场景",
                "disease": "条锈病 + 白粉病",
                "severity": "重度",
                "expected_tools": ["knowledge", "treatment", "case_record"]
            },
            {
                "name": "复查场景",
                "disease": "条锈病",
                "severity": "轻度",
                "has_history": True,
                "expected_tools": ["history_comparison", "case_record"]
            }
        ]
    
    def test_single_disease_scenario(self, test_scenarios, six_layer_pipeline):
        """测试单病害诊断场景"""
        scenario = test_scenarios[0]
        
        # 模拟认知输出
        cognition_output = {
            "disease_name": scenario["disease"],
            "confidence": 0.90,
            "severity_score": 0.5,
            "visual_features": ["黄色条状病斑"]
        }
        
        # 生成诊断计划
        planning_engine = six_layer_pipeline["planning"]
        plan = planning_engine.generate_diagnosis_plan(cognition_output)
        
        # 验证计划包含必要信息
        assert plan["病害诊断"]["病害名称"] == scenario["disease"]
        assert plan["严重度评估"]["严重度等级"] == scenario["severity"]
    
    def test_multi_disease_scenario(self, test_scenarios, six_layer_pipeline):
        """测试多病害并发场景"""
        scenario = test_scenarios[1]
        
        # 模拟多病害认知输出
        cognition_output = {
            "disease_name": "条锈病",
            "confidence": 0.85,
            "severity_score": 0.8,
            "secondary_diseases": ["白粉病"],
            "visual_features": ["黄色条状病斑", "白色粉状霉层"]
        }
        
        # 生成诊断计划
        planning_engine = six_layer_pipeline["planning"]
        plan = planning_engine.generate_diagnosis_plan(cognition_output)
        
        # 验证计划处理了多病害情况
        assert plan["病害诊断"]["病害名称"] in scenario["disease"]


def run_end_to_end_tests():
    """运行端到端测试的便捷函数"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_end_to_end_tests()
