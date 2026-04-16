# -*- coding: utf-8 -*-
"""
动作执行模块

包含学习、进化、人机协同等功能

文档参考:
- 7.1 增量学习与灾难性遗忘
- 7.2 人机协同反馈闭环
"""

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "ActiveLearner":
        from .learner_engine import ActiveLearner
        return ActiveLearner
    elif name == "EnhancedActiveLearner":
        from .learner_engine import ActiveLearner
        return ActiveLearner
    elif name == "HumanInTheLoop":
        from ..evolution.human_in_the_loop import HumanInTheLoop
        return HumanInTheLoop
    elif name == "FeedbackLoopIntegrator":
        from .feedback_integration import FeedbackLoopIntegrator
        return FeedbackLoopIntegrator
    elif name == "IncrementalLearningStrategy":
        from .learner_engine import IncrementalLearningStrategy
        return IncrementalLearningStrategy
    elif name == "TrainingConfig":
        from .learner_engine import TrainingConfig
        return TrainingConfig
    elif name == "FeedbackDataset":
        from .learner_engine import FeedbackDataset
        return FeedbackDataset
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # 主动学习
    "ActiveLearner",
    "EnhancedActiveLearner",
    "IncrementalLearningStrategy",
    "TrainingConfig",
    "FeedbackDataset",
    
    # 人机协同
    "HumanInTheLoop",
    "FeedbackLoopIntegrator"
]
