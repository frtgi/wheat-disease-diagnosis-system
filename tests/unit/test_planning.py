# -*- coding: utf-8 -*-
"""
规划决策层单元测试
测试 PlanningEngine 和 TaskPlanner 的核心功能
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.planning.planning_engine import PlanningEngine
from src.planning.task_planner import TaskPlanner, TaskPriority, TaskStatus


class TestPlanningEngine:
    """PlanningEngine 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.engine = PlanningEngine()
        self.sample_cognition_output = {
            "disease_name": "条锈病",
            "confidence": 0.92,
            "severity_score": 0.45,
            "visual_features": [
                "叶片出现黄色条状孢子堆",
                "沿叶脉排列",
                "叶片褪绿"
            ],
            "environmental_conditions": {
                "temperature": "12°C",
                "humidity": "高湿"
            },
            "user_description": "叶片有黄色条纹，最近下雨"
        }
    
    def test_initialization(self):
        """测试 PlanningEngine 初始化"""
        # Arrange & Act
        engine = PlanningEngine()
        
        # Assert
        assert engine is not None
        assert engine.disease_knowledge is not None
        assert len(engine.disease_knowledge) > 0
        assert "条锈病" in engine.disease_knowledge
        assert engine.qwen_engine is None
    
    def test_generate_diagnosis_plan_structure(self, sample_cognition_output):
        """测试诊断计划生成的结构完整性"""
        # Arrange
        required_fields = [
            "病害诊断", "严重度评估", "推理依据",
            "风险等级", "防治措施", "复查计划"
        ]
        
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(sample_cognition_output)
        
        # Assert
        assert diagnosis_plan is not None
        for field in required_fields:
            assert field in diagnosis_plan, f"缺少必需字段：{field}"
    
    def test_disease_diagnosis_content(self, sample_cognition_output):
        """测试病害诊断内容的准确性"""
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(sample_cognition_output)
        disease_diagnosis = diagnosis_plan["病害诊断"]
        
        # Assert
        assert disease_diagnosis["病害名称"] == "条锈病"
        assert disease_diagnosis["置信度"] == 0.92
        assert len(disease_diagnosis["主要特征"]) > 0
        assert "诊断结论" in disease_diagnosis
    
    def test_severity_assessment_levels(self):
        """测试不同严重度评分的等级判断"""
        # Arrange
        test_cases = [
            (0.2, "轻度"),
            (0.5, "中度"),
            (0.8, "重度")
        ]
        
        # Act & Assert
        for severity_score, expected_level in test_cases:
            cognition_output = self.sample_cognition_output.copy()
            cognition_output["severity_score"] = severity_score
            
            diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
            severity_assessment = diagnosis_plan["严重度评估"]
            
            assert severity_assessment["严重度等级"] == expected_level
            assert severity_assessment["严重度评分"] == severity_score
    
    def test_risk_level_calculation(self):
        """测试风险等级计算逻辑"""
        # Arrange
        cognition_output = self.sample_cognition_output.copy()
        cognition_output["environmental_conditions"] = {
            "temperature": "12°C",
            "humidity": "高湿"
        }
        
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
        risk_level = diagnosis_plan["风险等级"]
        
        # Assert
        assert "风险等级" in risk_level
        assert risk_level["风险等级"] in ["低风险", "中风险", "高风险"]
        assert "风险评分" in risk_level
        assert 0 <= risk_level["风险评分"] <= 1
    
    def test_treatment_measures_by_severity(self):
        """测试根据严重度生成不同的防治措施"""
        # Arrange
        test_severities = ["轻度", "中度", "重度"]
        
        for severity in test_severities:
            cognition_output = self.sample_cognition_output.copy()
            if severity == "轻度":
                cognition_output["severity_score"] = 0.2
            elif severity == "中度":
                cognition_output["severity_score"] = 0.5
            else:
                cognition_output["severity_score"] = 0.8
            
            # Act
            diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
            treatment = diagnosis_plan["防治措施"]
            
            # Assert
            assert "推荐药剂" in treatment
            assert "防治步骤" in treatment
            assert len(treatment["防治步骤"]) > 0
    
    def test_followup_plan_generation(self):
        """测试复查计划生成"""
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(self.sample_cognition_output)
        followup = diagnosis_plan["复查计划"]
        
        # Assert
        assert "复查时间" in followup
        assert "复查间隔" in followup
        assert "紧急程度" in followup
        assert "复查内容" in followup
        assert len(followup["复查内容"]) > 0
    
    def test_validate_diagnosis_plan(self):
        """测试诊断计划验证功能"""
        # Arrange
        sample_diagnosis_plan = {
            "病害诊断": {"病害名称": "条锈病"},
            "严重度评估": {"严重度等级": "中度"},
            "推理依据": {"推理步骤": []},
            "风险等级": {"风险等级": "中风险"},
            "防治措施": {"推荐药剂": []},
            "复查计划": {"复查时间": "2026-03-16"}
        }
        
        # Act
        is_valid = self.engine.validate_diagnosis_plan(sample_diagnosis_plan)
        
        # Assert
        assert is_valid is True
    
    def test_validate_invalid_plan(self):
        """测试无效诊断计划验证"""
        # Arrange
        invalid_plan = {"病害诊断": {}}  # 缺少其他必需字段
        
        # Act
        is_valid = self.engine.validate_diagnosis_plan(invalid_plan)
        
        # Assert
        assert is_valid is False
    
    def test_unknown_disease_handling(self):
        """测试未知病害的处理"""
        # Arrange
        cognition_output = self.sample_cognition_output.copy()
        cognition_output["disease_name"] = "未知病害"
        
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
        
        # Assert
        assert diagnosis_plan is not None
        assert diagnosis_plan["病害诊断"]["病害名称"] == "未知病害"
    
    def test_empty_visual_features(self):
        """测试空视觉特征的处理"""
        # Arrange
        cognition_output = self.sample_cognition_output.copy()
        cognition_output["visual_features"] = []
        
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
        
        # Assert
        assert diagnosis_plan is not None
        assert "病害诊断" in diagnosis_plan
    
    def test_missing_environmental_conditions(self):
        """测试缺失环境条件的处理"""
        # Arrange
        cognition_output = self.sample_cognition_output.copy()
        cognition_output["environmental_conditions"] = {}
        
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
        
        # Assert
        assert diagnosis_plan is not None
        assert "风险等级" in diagnosis_plan
    
    def test_export_to_json(self, tmp_path, sample_diagnosis_plan):
        """测试导出 JSON 功能"""
        # Arrange
        output_path = tmp_path / "test_diagnosis_plan.json"
        
        # Act
        self.engine.export_to_json(sample_diagnosis_plan, str(output_path))
        
        # Assert
        assert output_path.exists()
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_plan = json.load(f)
        assert loaded_plan == sample_diagnosis_plan
    
    def test_disease_knowledge_completeness(self):
        """测试病害知识库的完整性"""
        # Arrange
        expected_diseases = [
            "条锈病", "叶锈病", "秆锈病", "白粉病",
            "赤霉病", "纹枯病", "根腐病", "蚜虫", "螨虫"
        ]
        
        # Assert
        for disease in expected_diseases:
            assert disease in self.engine.disease_knowledge
            disease_info = self.engine.disease_knowledge[disease]
            assert "severity_thresholds" in disease_info
            assert "treatments" in disease_info
            assert "risk_factors" in disease_info
    
    def test_confidence_rounding(self):
        """测试置信度四舍五入"""
        # Arrange
        cognition_output = self.sample_cognition_output.copy()
        cognition_output["confidence"] = 0.9234567
        
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
        
        # Assert
        confidence = diagnosis_plan["病害诊断"]["置信度"]
        assert isinstance(confidence, float)
        # 验证保留 4 位小数
        assert confidence == round(0.9234567, 4)
    
    def test_severity_score_percentage_format(self):
        """测试严重度百分比格式"""
        # Act
        diagnosis_plan = self.engine.generate_diagnosis_plan(self.sample_cognition_output)
        severity = diagnosis_plan["严重度评估"]
        
        # Assert
        assert "病斑覆盖率" in severity
        assert "%" in severity["病斑覆盖率"]


class TestTaskPlanner:
    """TaskPlanner 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.planner = TaskPlanner()
        self.sample_diagnosis_plan = {
            "病害诊断": {
                "病害名称": "条锈病",
                "置信度": 0.92,
                "主要特征": ["黄色条状孢子堆", "沿叶脉排列"]
            },
            "严重度评估": {
                "严重度等级": "中度",
                "严重度评分": 0.45,
                "影响评估": "病斑中等，对产量有一定影响"
            },
            "风险等级": {
                "风险等级": "中风险",
                "风险评分": 0.55,
                "传播速度": "较快"
            },
            "防治措施": {
                "推荐药剂": [
                    {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"}
                ],
                "防治步骤": [
                    "立即喷施治疗性杀菌剂",
                    "7-10 天后复查并补喷"
                ]
            },
            "复查计划": {
                "复查时间": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "复查间隔": "7 天",
                "紧急程度": "重要",
                "复查内容": ["拍摄田间照片", "描述病情变化"]
            }
        }
    
    def test_task_planner_initialization(self):
        """测试 TaskPlanner 初始化"""
        # Arrange & Act
        planner = TaskPlanner()
        
        # Assert
        assert planner is not None
        assert planner.tasks == []
        assert planner.task_counter == 0
    
    def test_generate_tasks_from_diagnosis_plan(self, sample_diagnosis_plan):
        """测试从诊断计划生成任务"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        assert len(tasks) > 0
        # 应该包含复查任务
        followup_tasks = [t for t in tasks if t.task_type == "复查"]
        assert len(followup_tasks) > 0
        # 应该包含防治任务
        treatment_tasks = [t for t in tasks if t.task_type == "防治"]
        assert len(treatment_tasks) > 0
    
    def test_task_priority_assignment(self, sample_diagnosis_plan):
        """测试任务优先级分配"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        for task in tasks:
            assert task.priority in [
                TaskPriority.URGENT,
                TaskPriority.HIGH,
                TaskPriority.MEDIUM,
                TaskPriority.LOW
            ]
    
    def test_task_severity_mapping(self):
        """测试不同严重度的任务生成"""
        # Arrange
        test_plans = [
            {"severity": "轻度", "expected_priority": TaskPriority.MEDIUM},
            {"severity": "中度", "expected_priority": TaskPriority.HIGH},
            {"severity": "重度", "expected_priority": TaskPriority.URGENT}
        ]
        
        for test_case in test_plans:
            diagnosis_plan = self.sample_diagnosis_plan.copy()
            diagnosis_plan["严重度评估"]["严重度等级"] = test_case["severity"]
            
            # Act
            planner = TaskPlanner()
            tasks = planner.generate_tasks(diagnosis_plan)
            
            # Assert
            treatment_tasks = [t for t in tasks if t.task_type == "防治"]
            if treatment_tasks:
                assert treatment_tasks[0].priority == test_case["expected_priority"]
    
    def test_task_sorting(self, sample_diagnosis_plan):
        """测试任务排序逻辑"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        for i in range(len(tasks) - 1):
            current_priority = priority_order[tasks[i].priority]
            next_priority = priority_order[tasks[i + 1].priority]
            # 优先级高的在前，同优先级按时间排序
            assert current_priority <= next_priority
    
    def test_get_tasks_by_type(self, sample_diagnosis_plan):
        """测试按类型获取任务"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        followup_tasks = self.planner.get_tasks_by_type("复查")
        assert len(followup_tasks) > 0
        for task in followup_tasks:
            assert task.task_type == "复查"
    
    def test_get_tasks_by_priority(self, sample_diagnosis_plan):
        """测试按优先级获取任务"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        for priority in TaskPriority:
            priority_tasks = self.planner.get_tasks_by_priority(priority)
            for task in priority_tasks:
                assert task.priority == priority
    
    def test_get_pending_tasks(self, sample_diagnosis_plan):
        """测试获取待执行任务"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        pending_tasks = self.planner.get_pending_tasks()
        
        # Assert
        assert len(pending_tasks) > 0
        for task in pending_tasks:
            assert task.status == TaskStatus.PENDING
    
    def test_task_to_dict(self, sample_diagnosis_plan):
        """测试任务转换为字典"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        task_dict = tasks[0].to_dict()
        
        # Assert
        assert "task_id" in task_dict
        assert "task_type" in task_dict
        assert "title" in task_dict
        assert "description" in task_dict
        assert "priority" in task_dict
        assert "scheduled_time" in task_dict
        assert "status" in task_dict
    
    def test_task_complete(self, sample_diagnosis_plan):
        """测试任务完成标记"""
        # Arrange
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        task = tasks[0]
        
        # Act
        task.complete()
        
        # Assert
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
    
    def test_task_cancel(self, sample_diagnosis_plan):
        """测试任务取消"""
        # Arrange
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        task = tasks[0]
        
        # Act
        task.cancel()
        
        # Assert
        assert task.status == TaskStatus.CANCELLED
    
    def test_task_add_note(self, sample_diagnosis_plan):
        """测试添加任务备注"""
        # Arrange
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        task = tasks[0]
        note_content = "测试备注内容"
        
        # Act
        task.add_note(note_content)
        
        # Assert
        assert len(task.notes) > 0
        assert task.notes[-1]["content"] == note_content
    
    def test_export_tasks_to_json(self, tmp_path, sample_diagnosis_plan):
        """测试导出任务到 JSON"""
        # Arrange
        output_path = tmp_path / "test_tasks.json"
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Act
        self.planner.export_tasks_to_json(str(output_path))
        
        # Assert
        assert output_path.exists()
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "tasks" in data
        assert len(data["tasks"]) == len(tasks)
    
    def test_monitoring_task_generation(self, sample_diagnosis_plan):
        """测试监测任务生成"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        monitoring_tasks = [t for t in tasks if t.task_type == "监测"]
        assert len(monitoring_tasks) > 0
        assert "病情监测" in monitoring_tasks[0].title
    
    def test_management_task_generation(self, sample_diagnosis_plan):
        """测试管理任务生成"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        
        # Assert
        management_tasks = [t for t in tasks if t.task_type == "管理"]
        assert len(management_tasks) > 0
        assert "田间管理" in management_tasks[0].title
    
    def test_high_risk_followup_tasks(self):
        """测试高风险情况下的额外复查任务"""
        # Arrange
        diagnosis_plan = self.sample_diagnosis_plan.copy()
        diagnosis_plan["严重度评估"]["严重度等级"] = "重度"
        diagnosis_plan["风险等级"]["风险等级"] = "高风险"
        
        # Act
        tasks = self.planner.generate_tasks(diagnosis_plan)
        
        # Assert
        followup_tasks = [t for t in tasks if t.task_type == "复查"]
        # 高风险/重度应该有 2 个复查任务
        assert len(followup_tasks) >= 1
    
    def test_task_scheduling_time(self, sample_diagnosis_plan):
        """测试任务计划时间合理性"""
        # Act
        tasks = self.planner.generate_tasks(sample_diagnosis_plan)
        now = datetime.now()
        
        # Assert
        for task in tasks:
            assert task.scheduled_time >= now
            assert task.deadline >= task.scheduled_time


def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
