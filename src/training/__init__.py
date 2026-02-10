# -*- coding: utf-8 -*-
"""
模型训练模块

包含YOLOv8微调、Agri-LLaVA训练、知识图谱嵌入训练等功能
"""

from pathlib import Path
from typing import Any

# 默认训练路径
DEFAULT_CHECKPOINT_DIR = Path(__file__).parent.parent.parent / "checkpoints"
DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "training"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "YOLOTrainer":
        try:
            from .yolo_trainer import YOLOTrainer
            return YOLOTrainer
        except ImportError as e:
            print(f"⚠️ YOLOTrainer 导入失败: {e}")
            return None
    elif name == "CIoULoss":
        try:
            from .yolo_trainer import CIoULoss
            return CIoULoss
        except ImportError:
            return None
    elif name == "LoRATrainer":
        try:
            from .lora_trainer import LoRATrainer
            return LoRATrainer
        except ImportError:
            return None
    elif name == "AgriLLaVATrainer":
        try:
            from .agri_llava_trainer import AgriLLaVATrainer
            return AgriLLaVATrainer
        except ImportError:
            return None
    elif name == "TrainingConfig":
        try:
            from .base_trainer import TrainingConfig
            return TrainingConfig
        except ImportError:
            return Any
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_CHECKPOINT_DIR",
    "DEFAULT_LOG_DIR",
    # YOLO训练
    "YOLOTrainer",
    "CIoULoss",
    # LoRA训练
    "LoRATrainer",
    # Agri-LLaVA训练
    "AgriLLaVATrainer",
    # 基础配置
    "TrainingConfig"
]
