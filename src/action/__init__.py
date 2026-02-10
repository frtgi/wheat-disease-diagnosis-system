# -*- coding: utf-8 -*-
"""
动作执行模块

包含学习、进化、人机协同等功能
"""

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "ActiveLearner":
        from .learner_engine import ActiveLearner
        return ActiveLearner
    elif name == "EnhancedActiveLearner":
        try:
            from .enhanced_learner_engine import EnhancedActiveLearner
            return EnhancedActiveLearner
        except ImportError as e:
            print(f"⚠️ EnhancedActiveLearner 导入失败: {e}")
            from .learner_engine import ActiveLearner
            return ActiveLearner
    elif name == "HumanInTheLoop":
        from .human_in_the_loop import HumanInTheLoop
        return HumanInTheLoop
    elif name == "FeedbackLoopIntegrator":
        from .feedback_integration import FeedbackLoopIntegrator
        return FeedbackLoopIntegrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ActiveLearner",
    "EnhancedActiveLearner",
    "HumanInTheLoop",
    "FeedbackLoopIntegrator"
]
