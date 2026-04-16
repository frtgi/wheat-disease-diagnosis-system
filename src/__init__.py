# -*- coding: utf-8 -*-
"""
WheatAgent 核心代码库

基于多模态特征融合的小麦病害诊断智能体 (IWDDA)
包含感知-认知-行动闭环的完整架构
"""

__version__ = "0.2.0"
__author__ = "WheatAgent Team"

# 延迟导入所有子模块，避免循环导入
def __getattr__(name):
    if name == "vision":
        from . import vision
        return vision
    elif name == "text":
        from . import text
        return text
    elif name == "cognition":
        from . import cognition
        return cognition
    elif name == "fusion":
        from . import fusion
        return fusion
    elif name == "graph":
        from . import graph
        return graph
    elif name == "action":
        from . import action
        return action
    elif name == "evolution":
        from . import evolution
        return evolution
    elif name == "data":
        from . import data
        return data
    elif name == "deploy":
        from . import deploy
        return deploy
    elif name == "evaluation":
        from . import evaluation
        return evaluation
    elif name == "planning":
        from . import planning
        return planning
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "__version__",
    "__author__",
    # 子模块
    "vision",
    "text", 
    "cognition",
    "fusion",
    "graph",
    "action",
    "evolution",
    "data",
    "deploy",
    "evaluation",
    "planning"
]
