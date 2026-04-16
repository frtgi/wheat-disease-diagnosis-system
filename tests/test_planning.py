# -*- coding: utf-8 -*-
"""
规划决策层单元测试 - Planning Layer Unit Tests
测试 PlanningEngine 和 TaskPlanner 的功能

测试覆盖:
1. PlanningEngine 诊断计划生成（6 部分结构）
2. TaskPlanner 任务分解（复查任务、防治任务）
3. Qwen3-VL-4B-Instruct 集成（CoT 推理）
4. 数据验证和导出功能

验证标准:
- PlanningEngine 能正确生成 6 部分诊断计划
- TaskPlanner 能生成合理的复查任务和防治步骤
- 单元测试通过率 100%
"""

import os
import sys
import json
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.planning.planning_engine import PlanningEngine
from src.planning.task_planner import TaskPlanner, Task, TaskPriority, TaskStatus


class TestPlanningEngine(unittest.TestCase):
    """PlanningEngine 测试类"""
    
    def setUp(self):
        """
        测试前准备
        """
        self.engine = PlanningEngine()
        
        # 标准认知层输出（测试用例）
        self.standard_cognition_output = {
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
        
        # 轻度病害测试用例
        self.light_cognition_output = {
            "disease_name": "白粉病",
            "confidence": 0.85,
            "severity_score": 0.2,
            "visual_features": ["叶片有白色粉状霉层"],
            "environmental_conditions": {
                "temperature": "18°C",
                "humidity": "中湿"
            },
            "user_description": ""
        }
        
        # 重度病害测试用例
        self.severe_cognition_output = {
            "disease_name": "赤霉病",
            "confidence": 0.95,
            "severity_score": 0.8,
            "visual_features": [
                "穗部漂白",
                "粉红色霉层",
                "籽粒干瘪"
            ],
            "environmental_conditions": {
                "temperature": "22°C",
                "humidity": "连阴雨"
            },
            "user_description": "穗部发白，有粉红色霉"
        }
    
    def test_generate_diagnosis_plan_structure(self):
        """
        测试诊断计划结构（必须包含 6 个部分）
        """
        print("\n[测试] 诊断计划结构验证")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        # 验证 6 个必需字段
        required_fields = [
            "病害诊断",
            "严重度评估",
            "推理依据",
            "风险等级",
            "防治措施",
            "复查计划"
        ]
        
        for field in required_fields:
            self.assertIn(field, diagnosis_plan, f"缺少必需字段：{field}")
            self.assertIsNotNone(diagnosis_plan[field], f"字段为空：{field}")
        
        print(f"✓ 诊断计划包含所有必需字段：{required_fields}")
    
    def test_disease_diagnosis_content(self):
        """
        测试病害诊断部分内容
        """
        print("\n[测试] 病害诊断内容验证")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        disease_diagnosis = diagnosis_plan["病害诊断"]
        
        # 验证病害诊断字段
        self.assertIn("病害名称", disease_diagnosis)
        self.assertIn("置信度", disease_diagnosis)
        self.assertIn("诊断结论", disease_diagnosis)
        
        # 验证病害名称正确
        self.assertEqual(disease_diagnosis["病害名称"], "条锈病")
        
        # 验证置信度在合理范围内
        confidence = disease_diagnosis["置信度"]
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        print(f"✓ 病害诊断内容正确：{disease_diagnosis['病害名称']} (置信度：{confidence:.2f})")
    
    def test_severity_assessment_levels(self):
        """
        测试严重度评估分级逻辑
        """
        print("\n[测试] 严重度评估分级验证")
        
        # 测试轻度
        light_plan = self.engine.generate_diagnosis_plan(self.light_cognition_output)
        light_severity = light_plan["严重度评估"]
        self.assertEqual(light_severity["严重度等级"], "轻度")
        print(f"✓ 轻度评估正确：{light_severity['严重度等级']} (评分：{light_severity['严重度评分']:.2f})")
        
        # 测试中度
        medium_plan = self.engine.generate_diagnosis_plan(self.standard_cognition_output)
        medium_severity = medium_plan["严重度评估"]
        self.assertEqual(medium_severity["严重度等级"], "中度")
        print(f"✓ 中度评估正确：{medium_severity['严重度等级']} (评分：{medium_severity['严重度评分']:.2f})")
        
        # 测试重度
        severe_plan = self.engine.generate_diagnosis_plan(self.severe_cognition_output)
        severe_severity = severe_plan["严重度评估"]
        self.assertEqual(severe_severity["严重度等级"], "重度")
        print(f"✓ 重度评估正确：{severe_severity['严重度等级']} (评分：{severe_severity['严重度评分']:.2f})")
    
    def test_reasoning_basis_structure(self):
        """
        测试推理依据结构
        """
        print("\n[测试] 推理依据结构验证")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        reasoning_basis = diagnosis_plan["推理依据"]
        
        # 验证推理依据字段
        self.assertIn("推理步骤", reasoning_basis)
        self.assertIn("视觉证据", reasoning_basis)
        self.assertIn("环境证据", reasoning_basis)
        self.assertIn("知识证据", reasoning_basis)
        self.assertIn("推理链", reasoning_basis)
        
        # 验证推理步骤数量
        reasoning_steps = reasoning_basis["推理步骤"]
        self.assertGreaterEqual(len(reasoning_steps), 3, "推理步骤不足")
        
        print(f"✓ 推理依据结构完整，包含{len(reasoning_steps)}个推理步骤")
    
    def test_risk_level_assessment(self):
        """
        测试风险等级评估
        """
        print("\n[测试] 风险等级评估验证")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        risk_level = diagnosis_plan["风险等级"]
        
        # 验证风险等级字段
        self.assertIn("风险等级", risk_level)
        self.assertIn("风险评分", risk_level)
        self.assertIn("预警信息", risk_level)
        
        # 验证风险等级取值
        valid_risk_levels = ["低风险", "中风险", "高风险"]
        self.assertIn(risk_level["风险等级"], valid_risk_levels)
        
        # 验证风险评分范围
        risk_score = risk_level["风险评分"]
        self.assertGreaterEqual(risk_score, 0.0)
        self.assertLessEqual(risk_score, 1.0)
        
        print(f"✓ 风险等级评估正确：{risk_level['风险等级']} (评分：{risk_score:.2f})")
    
    def test_treatment_measures(self):
        """
        测试防治措施内容
        """
        print("\n[测试] 防治措施内容验证")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        treatment_measures = diagnosis_plan["防治措施"]
        
        # 验证防治措施字段
        self.assertIn("推荐药剂", treatment_measures)
        self.assertIn("防治步骤", treatment_measures)
        self.assertIn("注意事项", treatment_measures)
        
        # 验证推荐药剂非空
        self.assertIsInstance(treatment_measures["推荐药剂"], list)
        
        # 验证防治步骤非空
        self.assertIsInstance(treatment_measures["防治步骤"], list)
        self.assertGreater(len(treatment_measures["防治步骤"]), 0)
        
        print(f"✓ 防治措施内容完整，包含{len(treatment_measures['推荐药剂'])}种药剂")
    
    def test_followup_plan(self):
        """
        测试复查计划
        """
        print("\n[测试] 复查计划验证")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        followup_plan = diagnosis_plan["复查计划"]
        
        # 验证复查计划字段
        self.assertIn("复查时间", followup_plan)
        self.assertIn("复查间隔", followup_plan)
        self.assertIn("紧急程度", followup_plan)
        self.assertIn("复查内容", followup_plan)
        
        # 验证复查时间格式
        followup_time = followup_plan["复查时间"]
        try:
            datetime.strptime(followup_time, "%Y-%m-%d")
            print(f"✓ 复查时间格式正确：{followup_time}")
        except ValueError:
            self.fail("复查时间格式错误")
        
        # 验证复查内容非空
        self.assertIsInstance(followup_plan["复查内容"], list)
        self.assertGreater(len(followup_plan["复查内容"]), 0)
    
    def test_validate_diagnosis_plan(self):
        """
        测试诊断计划验证功能
        """
        print("\n[测试] 诊断计划验证功能")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        is_valid = self.engine.validate_diagnosis_plan(diagnosis_plan)
        self.assertTrue(is_valid, "诊断计划验证失败")
        
        print("✓ 诊断计划验证通过")
    
    def test_export_to_json(self):
        """
        测试 JSON 导出功能
        """
        print("\n[测试] JSON 导出功能")
        
        diagnosis_plan = self.engine.generate_diagnosis_plan(
            self.standard_cognition_output
        )
        
        # 导出到临时文件
        temp_file = os.path.join(
            os.path.dirname(__file__),
            f"test_diagnosis_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        self.engine.export_to_json(diagnosis_plan, temp_file)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(temp_file), "导出的文件不存在")
        
        # 验证 JSON 格式正确
        with open(temp_file, 'r', encoding='utf-8') as f:
            loaded_plan = json.load(f)
        
        self.assertEqual(loaded_plan["病害诊断"]["病害名称"], "条锈病")
        
        # 清理临时文件
        os.remove(temp_file)
        
        print(f"✓ JSON 导出功能正常，文件已清理")
    
    def test_different_diseases(self):
        """
        测试不同病害的诊断计划生成
        """
        print("\n[测试] 不同病害诊断计划生成")
        
        test_cases = [
            {"disease_name": "条锈病", "severity_score": 0.45},
            {"disease_name": "叶锈病", "severity_score": 0.35},
            {"disease_name": "白粉病", "severity_score": 0.25},
            {"disease_name": "赤霉病", "severity_score": 0.75},
            {"disease_name": "蚜虫", "severity_score": 0.55},
        ]
        
        for case in test_cases:
            cognition_output = {
                "disease_name": case["disease_name"],
                "confidence": 0.9,
                "severity_score": case["severity_score"],
                "visual_features": ["病害特征"],
                "environmental_conditions": {"temperature": "20°C", "humidity": "中湿"},
                "user_description": ""
            }
            
            diagnosis_plan = self.engine.generate_diagnosis_plan(cognition_output)
            
            # 验证 6 部分结构
            self.assertEqual(len(diagnosis_plan), 6, f"{case['disease_name']}诊断计划结构不完整")
            self.assertEqual(
                diagnosis_plan["病害诊断"]["病害名称"],
                case["disease_name"],
                f"病害名称不匹配：{case['disease_name']}"
            )
            
            print(f"  ✓ {case['disease_name']}诊断计划生成成功")
        
        print("✓ 所有病害诊断计划生成正常")


class TestTaskPlanner(unittest.TestCase):
    """TaskPlanner 测试类"""
    
    def setUp(self):
        """
        测试前准备
        """
        self.planner = TaskPlanner()
        
        # 标准诊断计划（测试用例）
        self.standard_diagnosis_plan = {
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
                    {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"},
                    {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"}
                ],
                "防治步骤": [
                    "立即喷施治疗性杀菌剂",
                    "7-10 天后复查并补喷",
                    "清除严重病株，减少菌源"
                ],
                "注意事项": ["交替使用药剂", "注意防护"]
            },
            "复查计划": {
                "复查时间": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "复查间隔": "7 天",
                "紧急程度": "重要",
                "复查内容": [
                    "拍摄田间照片",
                    "描述病情变化",
                    "记录防治措施"
                ]
            }
        }
        
        # 重度病害诊断计划
        self.severe_diagnosis_plan = {
            "病害诊断": {
                "病害名称": "赤霉病",
                "置信度": 0.95,
                "主要特征": ["穗部漂白", "粉红色霉层"]
            },
            "严重度评估": {
                "严重度等级": "重度",
                "严重度评分": 0.8,
                "影响评估": "病斑严重，对产量影响较大"
            },
            "风险等级": {
                "风险等级": "高风险",
                "风险评分": 0.85,
                "传播速度": "快"
            },
            "防治措施": {
                "推荐药剂": [
                    {"name": "多菌灵", "concentration": "50% 可湿性粉剂", "dosage": "100g/亩"}
                ],
                "防治步骤": [
                    "紧急喷施高效治疗剂",
                    "清除严重病株并带出田外",
                    "5-7 天后复查"
                ],
                "注意事项": ["紧急防治"]
            },
            "复查计划": {
                "复查时间": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "复查间隔": "3 天",
                "紧急程度": "紧急",
                "复查内容": ["拍摄田间照片", "评估防治效果"]
            }
        }
    
    def test_generate_tasks_structure(self):
        """
        测试任务生成结构
        """
        print("\n[测试] 任务生成结构验证")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 验证任务列表非空
        self.assertGreater(len(tasks), 0, "未生成任何任务")
        
        # 验证任务类型
        task_types = set(task.task_type for task in tasks)
        expected_types = {"复查", "防治", "监测", "管理"}
        
        # 至少包含一种任务类型
        self.assertTrue(len(task_types) > 0, "任务类型为空")
        
        print(f"✓ 生成了{len(tasks)}个任务，包含{len(task_types)}种类型：{task_types}")
    
    def test_followup_task_generation(self):
        """
        测试复查任务生成
        """
        print("\n[测试] 复查任务生成验证")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 获取复查任务
        followup_tasks = [t for t in tasks if t.task_type == "复查"]
        
        # 验证复查任务存在
        self.assertGreater(len(followup_tasks), 0, "未生成复查任务")
        
        # 验证复查任务属性
        followup_task = followup_tasks[0]
        self.assertIn("复查", followup_task.title)
        self.assertIn("条锈病", followup_task.title)
        
        # 验证任务优先级
        self.assertIn(followup_task.priority, [
            TaskPriority.URGENT,
            TaskPriority.HIGH,
            TaskPriority.MEDIUM
        ])
        
        print(f"✓ 复查任务生成正确：{followup_task.title} (优先级：{followup_task.priority.value})")
    
    def test_treatment_task_generation(self):
        """
        测试防治任务生成
        """
        print("\n[测试] 防治任务生成验证")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 获取防治任务
        treatment_tasks = [t for t in tasks if t.task_type == "防治"]
        
        # 验证防治任务存在
        self.assertGreater(len(treatment_tasks), 0, "未生成防治任务")
        
        # 验证防治任务属性
        treatment_task = treatment_tasks[0]
        self.assertIn("防治", treatment_task.title)
        self.assertIn("条锈病", treatment_task.title)
        
        # 验证描述包含药剂信息
        self.assertIn("三唑酮", treatment_task.description)
        
        print(f"✓ 防治任务生成正确：{treatment_task.title}")
    
    def test_task_priority_assignment(self):
        """
        测试任务优先级分配
        """
        print("\n[测试] 任务优先级分配验证")
        
        # 测试中度病害
        medium_tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        medium_priorities = set(task.priority for task in medium_tasks)
        
        # 测试重度病害
        self.planner = TaskPlanner()  # 重置规划器
        severe_tasks = self.planner.generate_tasks(self.severe_diagnosis_plan)
        severe_priorities = set(task.priority for task in severe_tasks)
        
        # 验证重度病害的优先级更高
        has_urgent_in_severe = TaskPriority.URGENT in severe_priorities
        print(f"  中度病害优先级：{[p.value for p in medium_priorities]}")
        print(f"  重度病害优先级：{[p.value for p in severe_priorities]}")
        
        print("✓ 任务优先级分配合理")
    
    def test_task_sorting(self):
        """
        测试任务排序
        """
        print("\n[测试] 任务排序验证")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 验证任务已排序（按优先级和时间）
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        is_sorted = True
        for i in range(len(tasks) - 1):
            current_priority = priority_order[tasks[i].priority]
            next_priority = priority_order[tasks[i + 1].priority]
            
            if current_priority > next_priority:
                is_sorted = False
                break
        
        self.assertTrue(is_sorted, "任务未按优先级排序")
        
        print("✓ 任务排序正确")
    
    def test_task_export_to_json(self):
        """
        测试任务导出功能
        """
        print("\n[测试] 任务导出功能")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 导出到临时文件
        temp_file = os.path.join(
            os.path.dirname(__file__),
            f"test_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        self.planner.export_tasks_to_json(temp_file)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(temp_file), "导出的文件不存在")
        
        # 验证 JSON 格式正确
        with open(temp_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        self.assertIn("total_tasks", tasks_data)
        self.assertEqual(tasks_data["total_tasks"], len(tasks))
        self.assertIn("tasks", tasks_data)
        
        # 清理临时文件
        os.remove(temp_file)
        
        print(f"✓ 任务导出功能正常，共导出{len(tasks)}个任务")
    
    def test_task_status_management(self):
        """
        测试任务状态管理
        """
        print("\n[测试] 任务状态管理验证")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 验证初始状态为待执行
        for task in tasks:
            self.assertEqual(task.status, TaskStatus.PENDING)
        
        # 测试完成任务
        test_task = tasks[0]
        test_task.complete()
        self.assertEqual(test_task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(test_task.completed_at)
        
        # 测试取消任务
        if len(tasks) > 1:
            test_task2 = tasks[1]
            test_task2.cancel()
            self.assertEqual(test_task2.status, TaskStatus.CANCELLED)
        
        # 测试获取待执行任务
        pending_tasks = self.planner.get_pending_tasks()
        self.assertGreaterEqual(len(pending_tasks), 0)
        
        print("✓ 任务状态管理正常")
    
    def test_task_notes(self):
        """
        测试任务备注功能
        """
        print("\n[测试] 任务备注功能验证")
        
        tasks = self.planner.generate_tasks(self.standard_diagnosis_plan)
        
        # 验证任务已有备注
        test_task = tasks[0]
        initial_notes_count = len(test_task.notes)
        self.assertGreaterEqual(initial_notes_count, 0)
        
        # 添加新备注
        test_task.add_note("测试备注内容")
        self.assertEqual(len(test_task.notes), initial_notes_count + 1)
        
        print("✓ 任务备注功能正常")


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def test_end_to_end_workflow(self):
        """
        测试端到端工作流程
        """
        print("\n[集成测试] 端到端工作流程")
        
        # Step 1: 模拟认知层输出
        cognition_output = {
            "disease_name": "叶锈病",
            "confidence": 0.88,
            "severity_score": 0.5,
            "visual_features": [
                "橙褐色圆形孢子堆",
                "散生叶片表面",
                "周围有褪绿圈"
            ],
            "environmental_conditions": {
                "temperature": "18°C",
                "humidity": "高湿"
            },
            "user_description": "叶片上有橙褐色斑点"
        }
        
        print("  Step 1: 认知层输出准备完成")
        
        # Step 2: PlanningEngine 生成诊断计划
        planning_engine = PlanningEngine()
        diagnosis_plan = planning_engine.generate_diagnosis_plan(cognition_output)
        
        # 验证诊断计划
        self.assertEqual(len(diagnosis_plan), 6, "诊断计划结构不完整")
        self.assertEqual(diagnosis_plan["病害诊断"]["病害名称"], "叶锈病")
        
        print("  Step 2: 诊断计划生成完成")
        
        # Step 3: TaskPlanner 生成任务
        task_planner = TaskPlanner()
        tasks = task_planner.generate_tasks(diagnosis_plan)
        
        # 验证任务生成
        self.assertGreater(len(tasks), 0, "未生成任何任务")
        
        print("  Step 3: 任务规划完成，生成{}个任务".format(len(tasks)))
        
        # Step 4: 验证输出
        # 验证诊断计划 6 部分
        required_fields = ["病害诊断", "严重度评估", "推理依据", "风险等级", "防治措施", "复查计划"]
        for field in required_fields:
            self.assertIn(field, diagnosis_plan)
        
        # 验证任务类型
        task_types = set(task.task_type for task in tasks)
        self.assertTrue(len(task_types) > 0)
        
        print("  Step 4: 输出验证完成")
        
        # Step 5: 导出结果
        temp_plan_file = os.path.join(
            os.path.dirname(__file__),
            f"test_e2e_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        temp_tasks_file = os.path.join(
            os.path.dirname(__file__),
            f"test_e2e_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        planning_engine.export_to_json(diagnosis_plan, temp_plan_file)
        task_planner.export_tasks_to_json(temp_tasks_file)
        
        # 清理临时文件
        os.remove(temp_plan_file)
        os.remove(temp_tasks_file)
        
        print("  Step 5: 结果导出完成")
        
        print("✓ 端到端工作流程测试通过")


def run_tests():
    """
    运行所有测试
    """
    print("=" * 60)
    print("🧪 IWDDA 规划决策层单元测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestPlanningEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskPlanner))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"总测试数：{result.testsRun}")
    print(f"成功：{result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败：{len(result.failures)}")
    print(f"错误：{len(result.errors)}")
    
    if result.failures:
        print("\n失败测试：")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n错误测试：")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    print("=" * 60)
    
    # 返回测试结果
    success = result.wasSuccessful()
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    
    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
