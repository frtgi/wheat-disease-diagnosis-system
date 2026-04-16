# -*- coding: utf-8 -*-
"""
工具执行层单元测试 - Test Tools
测试所有工具类的功能和集成
"""

import os
import sys
import unittest
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.base_tool import BaseTool
from tools.tool_manager import ToolManager
from tools.diagnosis_tool import DiagnosisTool
from tools.knowledge_retrieval_tool import KnowledgeRetrievalTool
from tools.treatment_tool import TreatmentTool
from tools.case_record_tool import CaseRecordTool
from tools.followup_tool import FollowupTool
from tools.history_comparison_tool import HistoryComparisonTool


class ConcreteTestTool(BaseTool):
    """具体工具类用于测试"""
    
    def __init__(self):
        super().__init__(name="ConcreteTestTool", description="测试具体工具")
    
    def get_name(self):
        return "ConcreteTestTool"
    
    def get_description(self):
        return "测试具体工具"
    
    def execute(self, **kwargs):
        return {"success": True, "data": "test"}


class TestBaseTool(unittest.TestCase):
    """测试 BaseTool 基类"""
    
    def test_base_tool_initialization(self):
        """测试基类初始化"""
        tool = ConcreteTestTool()
        self.assertEqual(tool.name, "ConcreteTestTool")
        self.assertEqual(tool.description, "测试具体工具")
        self.assertIsNotNone(tool.version)
        self.assertTrue(tool.is_available)
    
    def test_base_tool_metadata(self):
        """测试基类元数据"""
        tool = ConcreteTestTool()
        metadata = tool.get_metadata()
        self.assertIn("name", metadata)
        self.assertIn("description", metadata)
        self.assertIn("version", metadata)
        self.assertIn("created_at", metadata)
        self.assertIn("is_available", metadata)


class TestDiagnosisTool(unittest.TestCase):
    """测试 DiagnosisTool"""
    
    def setUp(self):
        """设置测试环境"""
        self.tool = DiagnosisTool()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tool.get_name(), "DiagnosisTool")
        self.assertIsNotNone(self.tool.get_description())
    
    def test_validate_params_success(self):
        """测试参数验证成功"""
        # 创建临时测试文件
        test_file = "test_image.jpg"
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = self.tool.validate_params(image_path=test_file)
        self.assertTrue(result)
        
        # 清理
        os.remove(test_file)
    
    def test_validate_params_failure(self):
        """测试参数验证失败"""
        result = self.tool.validate_params()
        self.assertFalse(result)
        
        result = self.tool.validate_params(image_path="nonexistent.jpg")
        self.assertFalse(result)
    
    def test_execute_mock_diagnosis(self):
        """测试执行诊断（模拟）"""
        test_file = "test_yellow_rust.jpg"
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = self.tool.execute(image_path=test_file)
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertIn('disease_name', result['data'])
        self.assertIn('confidence', result['data'])
        
        # 清理
        os.remove(test_file)


class TestKnowledgeRetrievalTool(unittest.TestCase):
    """测试 KnowledgeRetrievalTool"""
    
    def setUp(self):
        """设置测试环境"""
        self.tool = KnowledgeRetrievalTool()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tool.get_name(), "KnowledgeRetrievalTool")
    
    def test_retrieve_knowledge(self):
        """测试知识检索"""
        result = self.tool.execute(disease_name="条锈病")
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        data = result['data']
        self.assertEqual(data['disease_name'], "条锈病")
        self.assertTrue(data['found'])
        self.assertIn('pathogen', data)
        self.assertIn('symptoms', data)
    
    def test_retrieve_treatments(self):
        """测试检索防治方案"""
        result = self.tool.execute(
            disease_name="蚜虫",
            query_type="treatment"
        )
        
        self.assertTrue(result['success'])
        data = result['data']
        self.assertIn('treatments', data)
        self.assertGreater(len(data['treatments']), 0)
    
    def test_get_all_diseases(self):
        """测试获取所有病害"""
        diseases = self.tool.get_all_diseases()
        self.assertIsInstance(diseases, list)
        self.assertGreater(len(diseases), 0)


class TestTreatmentTool(unittest.TestCase):
    """测试 TreatmentTool"""
    
    def setUp(self):
        """设置测试环境"""
        self.tool = TreatmentTool()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tool.get_name(), "TreatmentTool")
    
    def test_generate_treatment_plan(self):
        """测试生成防治方案"""
        result = self.tool.execute(
            disease_name="条锈病",
            severity_level="中度"
        )
        
        self.assertTrue(result['success'])
        data = result['data']
        self.assertEqual(data['disease_name'], "条锈病")
        self.assertIn('recommended_agents', data)
        self.assertIn('treatment_steps', data)
        self.assertIn('safety_interval', data)
    
    def test_generate_treatment_by_severity(self):
        """测试根据严重度生成防治方案"""
        # 轻度
        result_light = self.tool.execute(
            disease_name="条锈病",
            severity_level="轻度"
        )
        # 重度
        result_severe = self.tool.execute(
            disease_name="条锈病",
            severity_level="重度"
        )
        
        light_agents = len(result_light['data']['recommended_agents'])
        severe_agents = len(result_severe['data']['recommended_agents'])
        
        # 重度应该推荐更多药剂
        self.assertGreaterEqual(severe_agents, light_agents)


class TestCaseRecordTool(unittest.TestCase):
    """测试 CaseRecordTool"""
    
    def setUp(self):
        """设置测试环境"""
        self.tool = CaseRecordTool()
        self.tool.initialize()
        
        # 模拟诊断计划
        self.diagnosis_plan = {
            "病害诊断": {
                "病害名称": "条锈病",
                "置信度": 0.92,
                "主要特征": ["黄色条状孢子堆", "沿叶脉排列"],
                "病原体": "条形柄锈菌",
                "诊断结论": "综合判断为条锈病"
            },
            "严重度评估": {
                "严重度等级": "中度",
                "严重度评分": 0.45,
                "影响评估": "病斑中等，对产量有一定影响"
            },
            "防治措施": {
                "推荐药剂": [
                    {"name": "三唑酮", "concentration": "15% 可湿性粉剂"}
                ],
                "防治步骤": ["立即喷施治疗性杀菌剂"],
                "施药时机": "晴朗无风天气",
                "安全间隔期": "14 天"
            },
            "复查计划": {
                "复查时间": "2026-03-16",
                "复查间隔": "7 天",
                "紧急程度": "重要"
            }
        }
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tool.get_name(), "CaseRecordTool")
    
    def test_record_case(self):
        """测试记录病例"""
        result = self.tool.execute(
            diagnosis_plan=self.diagnosis_plan,
            image_path="test.jpg",
            user_info={"user_id": "test_user"}
        )
        
        self.assertTrue(result['success'])
        data = result['data']
        self.assertIn('case_id', data)
        self.assertIn('record_time', data)
        self.assertTrue(data['case_id'].startswith('CASE_'))
    
    def test_get_case_by_id(self):
        """测试获取病例"""
        # 先记录一个病例
        result = self.tool.execute(
            diagnosis_plan=self.diagnosis_plan,
            image_path="test.jpg"
        )
        
        case_id = result['data']['case_id']
        case = self.tool.get_case_by_id(case_id)
        
        self.assertIsNotNone(case)
        self.assertEqual(case['case_id'], case_id)


class TestFollowupTool(unittest.TestCase):
    """测试 FollowupTool"""
    
    def setUp(self):
        """设置测试环境"""
        self.tool = FollowupTool()
        self.tool.initialize()
        
        self.followup_plan = {
            "复查时间": "2026-03-16",
            "复查间隔": "7 天",
            "紧急程度": "重要",
            "复查内容": [
                "拍摄田间照片",
                "描述病情变化"
            ],
            "预期目标": "病情得到控制",
            "复查任务 ID": "FOLLOWUP_TEST_001"
        }
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tool.get_name(), "FollowupTool")
    
    def test_create_followup_task(self):
        """测试创建复查任务"""
        result = self.tool.execute(
            followup_plan=self.followup_plan,
            disease_name="条锈病",
            severity_level="中度",
            create_reminder=True
        )
        
        self.assertTrue(result['success'])
        data = result['data']
        self.assertIn('task_id', data)
        self.assertIn('scheduled_time', data)
        self.assertTrue(data['reminder_set'])
    
    def test_get_task_statistics(self):
        """测试获取任务统计"""
        # 创建任务
        self.tool.execute(
            followup_plan=self.followup_plan,
            disease_name="条锈病"
        )
        
        stats = self.tool.get_task_statistics()
        
        self.assertIn('total_tasks', stats)
        self.assertIn('pending_tasks', stats)
        self.assertIn('completed_tasks', stats)
        self.assertIn('completion_rate', stats)


class TestHistoryComparisonTool(unittest.TestCase):
    """测试 HistoryComparisonTool"""
    
    def setUp(self):
        """设置测试环境"""
        self.tool = HistoryComparisonTool()
        self.tool.initialize()
        
        # 模拟历史病例
        self.previous_case = {
            "case_id": "CASE_PREV_001",
            "record_time": "2026-03-02T10:00:00",
            "diagnosis_info": {
                "disease_name": "条锈病",
                "confidence": 0.88
            },
            "severity_info": {
                "severity_level": "中度",
                "severity_score": 0.55
            }
        }
        
        # 模拟当前病例
        self.current_case = {
            "case_id": "CASE_CURR_001",
            "record_time": "2026-03-09T10:00:00",
            "diagnosis_info": {
                "disease_name": "条锈病",
                "confidence": 0.92
            },
            "severity_info": {
                "severity_level": "轻度",
                "severity_score": 0.25
            }
        }
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tool.get_name(), "HistoryComparisonTool")
    
    def test_compare_cases(self):
        """测试病例对比"""
        result = self.tool.execute(
            current_case=self.current_case,
            previous_case=self.previous_case
        )
        
        self.assertTrue(result['success'])
        data = result['data']
        self.assertIn('comparison_time', data)
        self.assertIn('disease_comparison', data)
        self.assertIn('severity_comparison', data)
        self.assertIn('progression_analysis', data)
        self.assertIn('treatment_effectiveness', data)
    
    def test_generate_report(self):
        """测试生成对比报告"""
        comparison_result = {
            "comparison_time": "2026-03-09T10:00:00",
            "time_interval": {"description": "间隔 7 天"},
            "disease_comparison": {
                "current_disease": "条锈病",
                "previous_disease": "条锈病"
            },
            "severity_comparison": {
                "current_level": "轻度",
                "previous_level": "中度",
                "level_trend": "减轻"
            },
            "progression_analysis": {
                "description": "病情明显好转"
            },
            "treatment_effectiveness": {
                "effectiveness": "有效",
                "effectiveness_score": 75
            },
            "recommendations": ["继续当前防治方案"]
        }
        
        report = self.tool.generate_comparison_report(comparison_result)
        
        self.assertIsInstance(report, str)
        self.assertIn("历史病情对比报告", report)
        self.assertIn("条锈病", report)


class TestToolManager(unittest.TestCase):
    """测试 ToolManager"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = ToolManager()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.manager), 0)
        self.assertEqual(self.manager.get_tool_names(), [])
    
    def test_register_tool(self):
        """测试注册工具"""
        tool = DiagnosisTool()
        result = self.manager.register_tool("diagnosis", tool)
        
        self.assertTrue(result)
        self.assertEqual(len(self.manager), 1)
        self.assertIn("diagnosis", self.manager.get_tool_names())
    
    def test_unregister_tool(self):
        """测试注销工具"""
        tool = DiagnosisTool()
        self.manager.register_tool("diagnosis", tool)
        
        result = self.manager.unregister_tool("diagnosis")
        
        self.assertTrue(result)
        self.assertEqual(len(self.manager), 0)
    
    def test_execute_tool(self):
        """测试执行工具"""
        # 注册工具
        tool = KnowledgeRetrievalTool()
        self.manager.register_tool("knowledge", tool)
        
        # 执行工具
        result = self.manager.execute_tool(
            "knowledge",
            disease_name="条锈病"
        )
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertEqual(result['tool_name'], 'knowledge')
    
    def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具"""
        result = self.manager.execute_tool("nonexistent")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_execute_multiple(self):
        """测试批量执行工具"""
        # 注册工具
        self.manager.register_tool("knowledge", KnowledgeRetrievalTool())
        self.manager.register_tool("treatment", TreatmentTool())
        
        # 批量执行
        tool_calls = [
            {
                "tool_name": "knowledge",
                "params": {"disease_name": "条锈病"}
            },
            {
                "tool_name": "treatment",
                "params": {
                    "disease_name": "条锈病",
                    "severity_level": "中度"
                }
            }
        ]
        
        results = self.manager.execute_multiple(tool_calls)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]['success'])
        self.assertTrue(results[1]['success'])
    
    def test_execute_from_plan(self):
        """测试根据诊断计划执行工具"""
        # 注册所有工具
        self.manager.register_tool("knowledge", KnowledgeRetrievalTool())
        self.manager.register_tool("treatment", TreatmentTool())
        self.manager.register_tool("followup", FollowupTool())
        self.manager.register_tool("case_record", CaseRecordTool())
        
        # 模拟诊断计划
        diagnosis_plan = {
            "病害诊断": {
                "病害名称": "条锈病",
                "置信度": 0.92
            },
            "严重度评估": {
                "严重度等级": "中度",
                "严重度评分": 0.45
            },
            "防治措施": {
                "推荐药剂": [{"name": "三唑酮"}],
                "防治步骤": ["喷施药剂"]
            },
            "复查计划": {
                "复查时间": "2026-03-16",
                "复查间隔": "7 天"
            }
        }
        
        # 执行
        results = self.manager.execute_from_plan(diagnosis_plan)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    def test_get_execution_history(self):
        """测试获取执行历史"""
        # 注册并执行工具
        tool = KnowledgeRetrievalTool()
        self.manager.register_tool("knowledge", tool)
        self.manager.execute_tool("knowledge", disease_name="条锈病")
        
        history = self.manager.get_execution_history()
        
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertIn('tool_name', history[0])
        self.assertIn('timestamp', history[0])


class TestToolIntegration(unittest.TestCase):
    """测试工具集成"""
    
    def test_full_diagnosis_workflow(self):
        """测试完整诊断工作流"""
        # 初始化工具管理器
        manager = ToolManager()
        
        # 注册所有工具
        manager.register_tool("diagnosis", DiagnosisTool())
        manager.register_tool("knowledge", KnowledgeRetrievalTool())
        manager.register_tool("treatment", TreatmentTool())
        manager.register_tool("case_record", CaseRecordTool())
        manager.register_tool("followup", FollowupTool())
        
        print("\n" + "=" * 60)
        print("测试完整诊断工作流")
        print("=" * 60)
        
        # 创建临时测试图像
        test_image = "test_yellow_rust.jpg"
        with open(test_image, 'w') as f:
            f.write("test")
        
        # 创建临时测试图像
        test_image = "test_yellow_rust.jpg"
        with open(test_image, 'w') as f:
            f.write("test")
        
        try:
            # 1. 图像诊断
            print("\n1. 执行图像诊断...")
            diagnosis_result = manager.execute_tool(
                "diagnosis",
                image_path=test_image
            )
            self.assertTrue(diagnosis_result['success'])
            disease_name = diagnosis_result['data'].get('chinese_name', '条锈病')
            print(f"   诊断结果：{disease_name}")
            
            # 2. 知识检索
            print("\n2. 检索病害知识...")
            knowledge_result = manager.execute_tool(
                "knowledge",
                disease_name=disease_name
            )
            self.assertTrue(knowledge_result['success'])
            print(f"   找到病害信息：{knowledge_result['data']['disease_name']}")
            
            # 3. 生成防治方案
            print("\n3. 生成防治方案...")
            treatment_result = manager.execute_tool(
                "treatment",
                disease_name=disease_name,
                severity_level="中度"
            )
            self.assertTrue(treatment_result['success'])
            print(f"   推荐药剂数量：{len(treatment_result['data']['recommended_agents'])}")
            
            # 4. 记录病例
            print("\n4. 记录病例...")
            diagnosis_plan = {
                "病害诊断": {
                    "病害名称": disease_name,
                    "置信度": diagnosis_result['data']['confidence']
                },
                "严重度评估": {
                    "严重度等级": "中度",
                    "严重度评分": 0.45
                },
                "防治措施": treatment_result['data'],
                "复查计划": {
                    "复查时间": "2026-03-16",
                    "复查间隔": "7 天"
                }
            }
            case_result = manager.execute_tool(
                "case_record",
                diagnosis_plan=diagnosis_plan
            )
            self.assertTrue(case_result['success'])
            print(f"   病例 ID: {case_result['data']['case_id']}")
            
            # 5. 创建复查任务
            print("\n5. 创建复查任务...")
            followup_result = manager.execute_tool(
                "followup",
                followup_plan=diagnosis_plan['复查计划']
            )
            self.assertTrue(followup_result['success'])
            print(f"   任务 ID: {followup_result['data']['task_id']}")
            
            print("\n" + "=" * 60)
            print("✅ 完整诊断工作流测试通过！")
            print("=" * 60)
        
        finally:
            # 清理测试文件
            if os.path.exists(test_image):
                os.remove(test_image)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestBaseTool))
    suite.addTests(loader.loadTestsFromTestCase(TestDiagnosisTool))
    suite.addTests(loader.loadTestsFromTestCase(TestKnowledgeRetrievalTool))
    suite.addTests(loader.loadTestsFromTestCase(TestTreatmentTool))
    suite.addTests(loader.loadTestsFromTestCase(TestCaseRecordTool))
    suite.addTests(loader.loadTestsFromTestCase(TestFollowupTool))
    suite.addTests(loader.loadTestsFromTestCase(TestHistoryComparisonTool))
    suite.addTests(loader.loadTestsFromTestCase(TestToolManager))
    suite.addTests(loader.loadTestsFromTestCase(TestToolIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 工具执行层单元测试")
    print("=" * 60)
    
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
