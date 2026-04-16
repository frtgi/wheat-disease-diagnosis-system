# -*- coding: utf-8 -*-
"""
规划决策层 - Planning Layer
IWDDA Agent 架构的核心组件，负责诊断计划生成和任务规划

包含模块:
- PlanningEngine: 诊断计划生成器，输出固定 6 部分结构
- TaskPlanner: 任务规划器，将诊断计划分解为可执行任务

固定输出结构:
1. 病害诊断 - 判断病害类型
2. 严重度评估 - 轻度/中度/重度
3. 推理依据 - 图像特征 + 环境条件 + 知识库规则
4. 风险等级 - 评估传播风险
5. 防治措施 - 推荐药剂 + 用药浓度 + 防治步骤
6. 复查计划 - 自动生成复查任务
"""

from src.planning.planning_engine import PlanningEngine
from src.planning.task_planner import TaskPlanner

__all__ = ["PlanningEngine", "TaskPlanner"]
