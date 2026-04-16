# -*- coding: utf-8 -*-
"""
任务规划器 - Task Planner
IWDDA Agent 规划决策层组件，负责将诊断计划分解为可执行任务

功能特性:
1. 接收 PlanningEngine 生成的诊断计划
2. 分解防治步骤为具体可执行任务
3. 生成复查任务并设置提醒
4. 支持任务优先级排序和调度
5. 集成 Qwen3-VL-4B-Instruct 进行任务优化

输出任务类型:
- 复查任务：定期田间检查和拍照
- 防治任务：喷药、施肥、清除病株等
- 监测任务：环境参数监测、病情发展跟踪
- 管理任务：田间管理改善、通风降湿等
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TaskPriority(Enum):
    """
    任务优先级枚举
    """
    URGENT = "紧急"  # 需要立即执行
    HIGH = "重要"    # 24 小时内执行
    MEDIUM = "常规"  # 3 天内执行
    LOW = "观察"     # 7 天内执行


class TaskStatus(Enum):
    """
    任务状态枚举
    """
    PENDING = "待执行"
    IN_PROGRESS = "执行中"
    COMPLETED = "已完成"
    OVERDUE = "已逾期"
    CANCELLED = "已取消"


class Task:
    """
    任务类
    表示单个可执行任务
    """
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        title: str,
        description: str,
        priority: TaskPriority,
        scheduled_time: datetime,
        deadline: Optional[datetime] = None
    ):
        """
        初始化任务
        
        :param task_id: 任务唯一标识
        :param task_type: 任务类型（复查/防治/监测/管理）
        :param title: 任务标题
        :param description: 任务描述
        :param priority: 任务优先级
        :param scheduled_time: 计划执行时间
        :param deadline: 任务截止时间（可选）
        """
        self.task_id = task_id
        self.task_type = task_type
        self.title = title
        self.description = description
        self.priority = priority
        self.scheduled_time = scheduled_time
        self.deadline = deadline if deadline else scheduled_time
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.completed_at = None
        self.notes = []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将任务转换为字典
        
        :return: 任务字典
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "scheduled_time": self.scheduled_time.strftime("%Y-%m-%d %H:%M"),
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M") if self.deadline else None,
            "status": self.status.value,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": self.completed_at.strftime("%Y-%m-%d %H:%M:%S") if self.completed_at else None,
            "notes": self.notes
        }
    
    def add_note(self, note: str) -> None:
        """
        添加任务备注
        
        :param note: 备注内容
        """
        self.notes.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": note
        })
    
    def complete(self) -> None:
        """
        标记任务为已完成
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def cancel(self) -> None:
        """
        取消任务
        """
        self.status = TaskStatus.CANCELLED


class TaskPlanner:
    """
    任务规划器类
    
    负责将诊断计划分解为可执行任务：
    - 复查任务生成
    - 防治步骤分解
    - 任务优先级排序
    - 任务调度管理
    
    输入：PlanningEngine 生成的诊断计划
    输出：任务列表（包含复查任务、防治任务等）
    """
    
    def __init__(self):
        """
        初始化任务规划器
        """
        self.tasks: List[Task] = []
        self.task_counter = 0
    
    def generate_tasks(
        self,
        diagnosis_plan: Dict[str, Any],
        user_info: Optional[Dict[str, Any]] = None
    ) -> List[Task]:
        """
        根据诊断计划生成任务列表
        
        :param diagnosis_plan: 诊断计划（来自 PlanningEngine）
        :param user_info: 用户信息（可选，包含地块信息、联系方式等）
        :return: 任务列表
        """
        self.tasks = []
        self.task_counter = 0
        
        # 从诊断计划提取信息
        disease_diagnosis = diagnosis_plan.get("病害诊断", {})
        severity_assessment = diagnosis_plan.get("严重度评估", {})
        risk_level = diagnosis_plan.get("风险等级", {})
        treatment_measures = diagnosis_plan.get("防治措施", {})
        followup_plan = diagnosis_plan.get("复查计划", {})
        
        disease_name = disease_diagnosis.get("病害名称", "未知病害")
        severity_level = severity_assessment.get("严重度等级", "中度")
        risk = risk_level.get("风险等级", "中风险")
        
        # 1. 生成复查任务
        followup_tasks = self._generate_followup_tasks(
            disease_name, followup_plan, severity_level, risk
        )
        self.tasks.extend(followup_tasks)
        
        # 2. 生成防治任务
        treatment_tasks = self._generate_treatment_tasks(
            disease_name, treatment_measures, severity_level
        )
        self.tasks.extend(treatment_tasks)
        
        # 3. 生成监测任务
        monitoring_tasks = self._generate_monitoring_tasks(
            disease_name, risk_level, severity_assessment
        )
        self.tasks.extend(monitoring_tasks)
        
        # 4. 生成管理任务
        management_tasks = self._generate_management_tasks(
            disease_name, treatment_measures
        )
        self.tasks.extend(management_tasks)
        
        # 按优先级和时间排序
        self._sort_tasks()
        
        return self.tasks
    
    def _generate_followup_tasks(
        self,
        disease_name: str,
        followup_plan: Dict[str, Any],
        severity_level: str,
        risk: str
    ) -> List[Task]:
        """
        生成复查任务
        
        :param disease_name: 病害名称
        :param followup_plan: 复查计划
        :param severity_level: 严重度等级
        :param risk: 风险等级
        :return: 复查任务列表
        """
        tasks = []
        
        followup_time = followup_plan.get("复查时间", datetime.now().strftime("%Y-%m-%d"))
        followup_interval = followup_plan.get("复查间隔", "7 天")
        urgency = followup_plan.get("紧急程度", "常规")
        followup_content = followup_plan.get("复查内容", [])
        
        # 映射紧急程度到优先级
        priority_map = {
            "紧急": TaskPriority.URGENT,
            "重要": TaskPriority.HIGH,
            "常规": TaskPriority.MEDIUM
        }
        priority = priority_map.get(urgency, TaskPriority.MEDIUM)
        
        # 解析复查时间
        try:
            scheduled_time = datetime.strptime(followup_time, "%Y-%m-%d")
        except ValueError:
            scheduled_time = datetime.now() + timedelta(days=7)
        
        # 创建复查任务
        task_id = f"FOLLOWUP_{self._generate_task_id()}"
        title = f"{disease_name}复查 - {severity_level}{risk}"
        
        description_parts = [
            f"病害：{disease_name}",
            f"严重度：{severity_level}",
            f"风险：{risk}",
            f"复查间隔：{followup_interval}",
            "",
            "复查内容：",
        ]
        for item in followup_content:
            description_parts.append(f"- {item}")
        
        description = "\n".join(description_parts)
        
        task = Task(
            task_id=task_id,
            task_type="复查",
            title=title,
            description=description,
            priority=priority,
            scheduled_time=scheduled_time,
            deadline=scheduled_time + timedelta(days=1)
        )
        
        task.add_note(f"复查任务生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        tasks.append(task)
        
        # 如果是重度或高风险，添加额外复查任务
        if severity_level == "重度" or risk == "高风险":
            second_check_time = scheduled_time + timedelta(days=3)
            task_id_2 = f"FOLLOWUP_{self._generate_task_id()}"
            task_2 = Task(
                task_id=task_id_2,
                task_type="复查",
                title=f"{disease_name}二次复查",
                description=f"首次复查后 3 天进行二次复查，评估防治效果",
                priority=TaskPriority.HIGH,
                scheduled_time=second_check_time,
                deadline=second_check_time + timedelta(days=1)
            )
            tasks.append(task_2)
        
        return tasks
    
    def _generate_treatment_tasks(
        self,
        disease_name: str,
        treatment_measures: Dict[str, Any],
        severity_level: str
    ) -> List[Task]:
        """
        生成防治任务
        
        :param disease_name: 病害名称
        :param treatment_measures: 防治措施
        :param severity_level: 严重度等级
        :return: 防治任务列表
        """
        tasks = []
        
        recommended_agents = treatment_measures.get("推荐药剂", [])
        treatment_steps = treatment_measures.get("防治步骤", [])
        application_timing = treatment_measures.get("施药时机", "晴朗无风天气")
        
        # 根据严重度确定防治任务优先级
        if severity_level == "重度":
            priority = TaskPriority.URGENT
            delay_days = 0
        elif severity_level == "中度":
            priority = TaskPriority.HIGH
            delay_days = 1
        else:
            priority = TaskPriority.MEDIUM
            delay_days = 2
        
        scheduled_time = datetime.now() + timedelta(days=delay_days)
        
        # 创建首次防治任务
        task_id = f"TREATMENT_{self._generate_task_id()}"
        title = f"{disease_name}首次防治"
        
        description_parts = [
            f"病害：{disease_name}",
            f"严重度：{severity_level}",
            "",
            "推荐药剂：",
        ]
        
        for i, agent in enumerate(recommended_agents[:3], 1):
            if isinstance(agent, dict):
                name = agent.get("name", "未知药剂")
                concentration = agent.get("concentration", "")
                dosage = agent.get("dosage", "")
                description_parts.append(f"{i}. {name} ({concentration}) - {dosage}")
            else:
                description_parts.append(f"{i}. {agent}")
        
        description_parts.extend([
            "",
            "防治步骤：",
        ])
        for step in treatment_steps[:5]:
            description_parts.append(f"- {step}")
        
        description_parts.extend([
            "",
            f"施药时机：{application_timing}",
            "注意事项：",
            "- 交替使用不同作用机理的药剂",
            "- 注意个人防护",
            "- 遵守安全间隔期"
        ])
        
        description = "\n".join(description_parts)
        
        task = Task(
            task_id=task_id,
            task_type="防治",
            title=title,
            description=description,
            priority=priority,
            scheduled_time=scheduled_time,
            deadline=scheduled_time + timedelta(days=2)
        )
        
        task.add_note(f"防治任务生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        tasks.append(task)
        
        # 如果需要多次防治，生成第二次防治任务
        if severity_level in ["中度", "重度"]:
            second_treatment_time = scheduled_time + timedelta(days=7)
            task_id_2 = f"TREATMENT_{self._generate_task_id()}"
            task_2 = Task(
                task_id=task_id_2,
                task_type="防治",
                title=f"{disease_name}第二次防治",
                description=f"首次防治后 7 天进行第二次防治，巩固防治效果",
                priority=TaskPriority.MEDIUM,
                scheduled_time=second_treatment_time,
                deadline=second_treatment_time + timedelta(days=2)
            )
            tasks.append(task_2)
        
        return tasks
    
    def _generate_monitoring_tasks(
        self,
        disease_name: str,
        risk_level: Dict[str, Any],
        severity_assessment: Dict[str, Any]
    ) -> List[Task]:
        """
        生成监测任务
        
        :param disease_name: 病害名称
        :param risk_level: 风险等级
        :param severity_assessment: 严重度评估
        :return: 监测任务列表
        """
        tasks = []
        
        risk = risk_level.get("风险等级", "中风险")
        risk_score = risk_level.get("风险评分", 0.5)
        spread_rate = risk_level.get("传播速度", "中等")
        
        # 根据风险等级确定监测频率
        if risk == "高风险":
            interval_days = 2
            priority = TaskPriority.HIGH
        elif risk == "中风险":
            interval_days = 5
            priority = TaskPriority.MEDIUM
        else:
            interval_days = 7
            priority = TaskPriority.LOW
        
        scheduled_time = datetime.now() + timedelta(days=1)
        
        task_id = f"MONITOR_{self._generate_task_id()}"
        title = f"{disease_name}病情监测"
        
        description = "\n".join([
            f"病害：{disease_name}",
            f"风险等级：{risk}",
            f"风险评分：{risk_score:.2f}",
            f"传播速度：{spread_rate}",
            "",
            "监测内容：",
            "- 记录田间温度、湿度",
            "- 观察病斑扩展情况",
            "- 统计新发病植株数量",
            "- 拍照记录病情变化",
            "",
            f"监测频率：每{interval_days}天一次"
        ])
        
        task = Task(
            task_id=task_id,
            task_type="监测",
            title=title,
            description=description,
            priority=priority,
            scheduled_time=scheduled_time,
            deadline=scheduled_time + timedelta(days=interval_days)
        )
        
        task.add_note(f"监测任务生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        tasks.append(task)
        
        return tasks
    
    def _generate_management_tasks(
        self,
        disease_name: str,
        treatment_measures: Dict[str, Any]
    ) -> List[Task]:
        """
        生成管理任务
        
        :param disease_name: 病害名称
        :param treatment_measures: 防治措施
        :return: 管理任务列表
        """
        tasks = []
        
        notes = treatment_measures.get("注意事项", [])
        
        # 通用田间管理任务
        scheduled_time = datetime.now() + timedelta(days=3)
        
        task_id = f"MANAGE_{self._generate_task_id()}"
        title = f"{disease_name}田间管理"
        
        description = "\n".join([
            f"病害：{disease_name}",
            "",
            "管理措施：",
            "- 改善田间通风透光条件",
            "- 合理密植，避免过度拥挤",
            "- 清除田间杂草和病残体",
            "- 合理施肥，避免过量施氮",
            "- 及时排水，降低田间湿度",
            "",
            "长期管理：",
            "- 轮作倒茬",
            "- 选用抗病品种",
            "- 深耕灭茬"
        ])
        
        task = Task(
            task_id=task_id,
            task_type="管理",
            title=title,
            description=description,
            priority=TaskPriority.LOW,
            scheduled_time=scheduled_time,
            deadline=scheduled_time + timedelta(days=7)
        )
        
        task.add_note(f"管理任务生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        tasks.append(task)
        
        return tasks
    
    def _generate_task_id(self) -> str:
        """
        生成任务 ID
        
        :return: 任务 ID 字符串
        """
        self.task_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{timestamp}_{self.task_counter:03d}"
    
    def _sort_tasks(self) -> None:
        """
        对任务进行排序
        优先级：紧急 > 重要 > 常规 > 观察
        时间：计划时间早的在前
        """
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        self.tasks.sort(
            key=lambda t: (priority_order[t.priority], t.scheduled_time)
        )
    
    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """
        按类型获取任务
        
        :param task_type: 任务类型（复查/防治/监测/管理）
        :return: 任务列表
        """
        return [t for t in self.tasks if t.task_type == task_type]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """
        按优先级获取任务
        
        :param priority: 任务优先级
        :return: 任务列表
        """
        return [t for t in self.tasks if t.priority == priority]
    
    def get_pending_tasks(self) -> List[Task]:
        """
        获取待执行任务
        
        :return: 待执行任务列表
        """
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]
    
    def export_tasks_to_json(self, file_path: str) -> None:
        """
        将任务列表导出为 JSON 文件
        
        :param file_path: 输出文件路径
        """
        tasks_data = {
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_tasks": len(self.tasks),
            "tasks": [task.to_dict() for task in self.tasks]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        print(f"[TaskPlanner] 任务列表已导出至：{file_path}")
    
    def print_task_summary(self) -> None:
        """
        打印任务摘要
        """
        print("\n" + "=" * 60)
        print("📋 任务规划摘要")
        print("=" * 60)
        
        print(f"\n总任务数：{len(self.tasks)}")
        
        # 按类型统计
        type_count = {}
        for task in self.tasks:
            task_type = task.task_type
            type_count[task_type] = type_count.get(task_type, 0) + 1
        
        print("\n按类型统计：")
        for task_type, count in type_count.items():
            print(f"  - {task_type}任务：{count}个")
        
        # 按优先级统计
        priority_count = {}
        for task in self.tasks:
            priority = task.priority.value
            priority_count[priority] = priority_count.get(priority, 0) + 1
        
        print("\n按优先级统计：")
        for priority, count in priority_count.items():
            print(f"  - {priority}: {count}个")
        
        # 列出前 5 个紧急任务
        urgent_tasks = [t for t in self.tasks if t.priority in [TaskPriority.URGENT, TaskPriority.HIGH]]
        if urgent_tasks:
            print("\n紧急/重要任务：")
            for task in urgent_tasks[:5]:
                print(f"  [{task.task_type}] {task.title} - {task.scheduled_time.strftime('%Y-%m-%d')}")
        
        print("=" * 60)


def test_task_planner():
    """测试任务规划器"""
    print("=" * 60)
    print("🧪 测试 TaskPlanner")
    print("=" * 60)
    
    planner = TaskPlanner()
    
    # 模拟诊断计划
    diagnosis_plan = {
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
            ]
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
    
    print("\n1️⃣ 生成任务列表")
    tasks = planner.generate_tasks(diagnosis_plan)
    
    print("\n2️⃣ 打印任务摘要")
    planner.print_task_summary()
    
    print("\n3️⃣ 任务详情:")
    for i, task in enumerate(tasks[:5], 1):
        print(f"\n任务{i}:")
        print(f"  ID: {task.task_id}")
        print(f"  类型：{task.task_type}")
        print(f"  标题：{task.title}")
        print(f"  优先级：{task.priority.value}")
        print(f"  计划时间：{task.scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  状态：{task.status.value}")
    
    print("\n4️⃣ 导出任务列表")
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "exports",
                               f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    planner.export_tasks_to_json(output_path)
    
    print("\n" + "=" * 60)
    print("✅ TaskPlanner 测试通过！")
    print("=" * 60)
    
    return tasks


if __name__ == "__main__":
    test_task_planner()
