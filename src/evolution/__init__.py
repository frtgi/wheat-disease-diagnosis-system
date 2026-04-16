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
    elif name == "HumanInTheLoop":
        try:
            from .human_in_the_loop import HumanInTheLoop
            return HumanInTheLoop
        except ImportError as e:
            print(f"⚠️ HumanInTheLoop 导入失败: {e}")
            return None
    elif name == "FeedbackRecord":
        try:
            from .human_in_the_loop import FeedbackRecord
            return FeedbackRecord
        except ImportError:
            return Any
    elif name == "FeedbackStatus":
        try:
            from .human_in_the_loop import FeedbackStatus
            return FeedbackStatus
        except ImportError:
            from enum import Enum
            class FeedbackStatus(Enum):
                PENDING = "pending"
                REVIEWED = "reviewed"
                CONFIRMED = "confirmed"
                CORRECTED = "corrected"
                DISCARDED = "discarded"
                PROCESSED = "processed"
            return FeedbackStatus
    elif name == "IncrementalLearner":
        try:
            from .incremental_learning import IncrementalLearner
            return IncrementalLearner
        except ImportError as e:
            print(f"⚠️ IncrementalLearner 导入失败: {e}")
            return None
    elif name == "iCaRL":
        try:
            from .incremental_learning import iCaRL
            return iCaRL
        except ImportError:
            return Any
    elif name == "LwF":
        try:
            from .incremental_learning import LwF
            return LwF
        except ImportError:
            return Any
    elif name == "EWC":
        try:
            from .incremental_learning import EWC
            return EWC
        except ImportError:
            return Any
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_BUFFER_PATH",
    # Experience Replay
    "ExperienceReplayBuffer",
    "ExperienceReplayDataset",
    "ExperienceReplayTrainer",
    
    # Human-in-the-Loop
    "HumanInTheLoop",
    "FeedbackRecord",
    "FeedbackStatus",
    
    # Incremental Learning
    "IncrementalLearner",
    "iCaRL",
    "LwF",
    "EWC"
]
