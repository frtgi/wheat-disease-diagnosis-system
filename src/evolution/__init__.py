# -*- coding: utf-8 -*-
"""
自进化机制模块

包含 Experience Replay 和 Human-in-the-Loop Feedback
实现增量学习、经验回放和人机协同反馈闭环
"""

from pathlib import Path
from typing import Any

# 默认存储路径
DEFAULT_BUFFER_PATH = Path(__file__).parent.parent.parent / "data" / "experience_replay"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "ExperienceReplayBuffer":
        try:
            from .experience_replay import ExperienceReplayBuffer
            return ExperienceReplayBuffer
        except ImportError as e:
            print(f"⚠️ ExperienceReplayBuffer 导入失败: {e}")
            return None
    elif name == "ExperienceReplayDataset":
        try:
            from .experience_replay import ExperienceReplayDataset
            return ExperienceReplayDataset
        except ImportError:
            return Any
    elif name == "ExperienceReplayTrainer":
        try:
            from .experience_replay import ExperienceReplayTrainer
            return ExperienceReplayTrainer
        except ImportError:
            return Any
    elif name == "FeedbackType":
        try:
            from .human_feedback import FeedbackType
            return FeedbackType
        except ImportError:
            # 定义占位符
            from enum import Enum
            class FeedbackType(Enum):
                CORRECTION = "correction"
                CONFIRMATION = "confirmation"
                REJECTION = "rejection"
            return FeedbackType
    elif name == "HumanFeedbackCollector":
        try:
            from .human_feedback import HumanFeedbackCollector
            return HumanFeedbackCollector
        except ImportError:
            return None
    elif name == "FeedbackAnalyzer":
        try:
            from .human_feedback import FeedbackAnalyzer
            return FeedbackAnalyzer
        except ImportError:
            return None
    elif name == "FeedbackIntegration":
        try:
            from .human_feedback import FeedbackIntegration
            return FeedbackIntegration
        except ImportError:
            return None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_BUFFER_PATH",
    # Experience Replay
    "ExperienceReplayBuffer",
    "ExperienceReplayDataset",
    "ExperienceReplayTrainer",
    
    # Human Feedback
    "FeedbackType",
    "HumanFeedbackCollector",
    "FeedbackAnalyzer",
    "FeedbackIntegration"
]
