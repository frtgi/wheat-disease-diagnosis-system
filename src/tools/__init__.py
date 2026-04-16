# -*- coding: utf-8 -*-
"""
工具执行层模块 - Tools Layer
IWDDA Agent 工具执行层，提供 6 类核心工具供规划层调用

模块结构:
1. BaseTool - 工具基类，定义工具接口规范
2. ToolManager - 工具管理器，统一管理和调度所有工具
3. DiagnosisTool - 图像诊断工具，执行病害识别
4. KnowledgeRetrievalTool - 知识检索工具，查询农业知识库
5. TreatmentTool - 防治方案生成工具，生成用药建议
6. CaseRecordTool - 病例记录工具，保存诊断案例
7. FollowupTool - 复查计划工具，创建复查任务
8. HistoryComparisonTool - 历史对比工具，对比前后病情变化

使用示例:
    from src.tools import ToolManager
    
    # 初始化工具管理器
    manager = ToolManager()
    
    # 注册工具
    manager.register_tool("diagnosis", DiagnosisTool())
    
    # 调用工具
    result = manager.execute_tool("diagnosis", image_path="test.jpg")
"""

from .base_tool import BaseTool
from .tool_manager import ToolManager
from .diagnosis_tool import DiagnosisTool
from .knowledge_retrieval_tool import KnowledgeRetrievalTool
from .treatment_tool import TreatmentTool
from .case_record_tool import CaseRecordTool
from .followup_tool import FollowupTool
from .history_comparison_tool import HistoryComparisonTool

__all__ = [
    "BaseTool",
    "ToolManager",
    "DiagnosisTool",
    "KnowledgeRetrievalTool",
    "TreatmentTool",
    "CaseRecordTool",
    "FollowupTool",
    "HistoryComparisonTool"
]
