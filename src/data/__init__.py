# -*- coding: utf-8 -*-
"""
数据工程模块

包含数据增强、数据集构建和数据预处理功能
支持多模态数据底座构建 (L1/L2/L3三层体系)
"""

from pathlib import Path
from typing import Any

# 默认数据路径
DEFAULT_DATA_ROOT = Path(__file__).parent.parent.parent / "datasets"

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "AugmentationEngine":
        try:
            from .augmentation_engine import AugmentationEngine
            return AugmentationEngine
        except ImportError as e:
            print(f"⚠️ AugmentationEngine 导入失败: {e}")
            return None
    elif name == "AugmentationConfig":
        try:
            from .augmentation_engine import AugmentationConfig
            return AugmentationConfig
        except ImportError:
            return Any
    elif name == "GeometricAugmentation":
        try:
            from .augmentation_engine import GeometricAugmentation
            return GeometricAugmentation
        except ImportError:
            return None
    elif name == "ColorAugmentation":
        try:
            from .augmentation_engine import ColorAugmentation
            return ColorAugmentation
        except ImportError:
            return None
    elif name == "DomainAugmentation":
        try:
            from .augmentation_engine import DomainAugmentation
            return DomainAugmentation
        except ImportError:
            return None
    elif name == "MultimodalDatasetBuilder":
        try:
            from .dataset_builder import MultimodalDatasetBuilder
            return MultimodalDatasetBuilder
        except ImportError as e:
            print(f"⚠️ MultimodalDatasetBuilder 导入失败: {e}")
            return None
    elif name == "DataLevel":
        try:
            from .dataset_builder import DataLevel
            return DataLevel
        except ImportError:
            from enum import Enum
            class DataLevel(Enum):
                L1_PERCEPTION = "L1"
                L2_QUANTIFICATION = "L2"
                L3_COGNITION = "L3"
            return DataLevel
    elif name == "L1Sample":
        try:
            from .dataset_builder import L1Sample
            return L1Sample
        except ImportError:
            return Any
    elif name == "L2Sample":
        try:
            from .dataset_builder import L2Sample
            return L2Sample
        except ImportError:
            return Any
    elif name == "L3Sample":
        try:
            from .dataset_builder import L3Sample
            return L3Sample
        except ImportError:
            return Any
    elif name == "DataLayerManager":
        try:
            from .data_layers import DataLayerManager
            return DataLayerManager
        except ImportError as e:
            print(f"⚠️ DataLayerManager 导入失败: {e}")
            return None
    elif name == "L1RawData":
        try:
            from .data_layers import L1RawData
            return L1RawData
        except ImportError:
            return Any
    elif name == "L2FeatureData":
        try:
            from .data_layers import L2FeatureData
            return L2FeatureData
        except ImportError:
            return Any
    elif name == "L3SemanticData":
        try:
            from .data_layers import L3SemanticData
            return L3SemanticData
        except ImportError:
            return Any
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_DATA_ROOT",
    # 数据增强
    "AugmentationEngine",
    "AugmentationConfig",
    "GeometricAugmentation",
    "ColorAugmentation",
    "DomainAugmentation",
    # 数据集构建
    "MultimodalDatasetBuilder",
    "DataLevel",
    "L1Sample",
    "L2Sample",
    "L3Sample",
    # 数据分层架构
    "DataLayerManager",
    "L1RawData",
    "L2FeatureData",
    "L3SemanticData"
]
