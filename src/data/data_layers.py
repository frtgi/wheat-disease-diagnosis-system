# -*- coding: utf-8 -*-
"""
L1/L2/L3数据分层架构模块

基于文档第2.1节：数据分层管理架构

分层结构：
- L1层（原始数据层）：存储原始图像、标注等原始数据
- L2层（特征层）：存储提取的特征向量、中间表示
- L3层（语义层）：存储语义理解结果、知识关联

作者: IWDDA团队
"""
import os
import json
import hashlib
import torch
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pickle
import threading
from collections import defaultdict


class DataLayer(Enum):
    """数据层级枚举"""
    L1_RAW = "L1"           # 原始数据层
    L2_FEATURE = "L2"       # 特征层
    L3_SEMANTIC = "L3"      # 语义层


class DataType(Enum):
    """数据类型枚举"""
    IMAGE = "image"
    ANNOTATION = "annotation"
    FEATURE = "feature"
    EMBEDDING = "embedding"
    DETECTION = "detection"
    DIAGNOSIS = "diagnosis"
    KNOWLEDGE = "knowledge"


@dataclass
class DataMetadata:
    """数据元信息"""
    data_id: str
    layer: str
    data_type: str
    source: str
    timestamp: str
    checksum: Optional[str] = None
    parent_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataMetadata':
        """从字典创建"""
        return cls(**data)


@dataclass
class L1RawData:
    """
    L1层：原始数据
    
    存储原始图像、标注等未经处理的数据
    
    参考文档2.1节：
    L1层作为数据基础，保持数据的原始性和完整性
    """
    data_id: str
    image_path: Optional[str] = None
    image_data: Optional[np.ndarray] = None
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Optional[DataMetadata] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = DataMetadata(
                data_id=self.data_id,
                layer=DataLayer.L1_RAW.value,
                data_type=DataType.IMAGE.value,
                source="unknown",
                timestamp=datetime.now().isoformat()
            )
    
    def compute_checksum(self) -> str:
        """计算数据校验和"""
        if self.image_data is not None:
            return hashlib.md5(self.image_data.tobytes()).hexdigest()
        elif self.image_path:
            with open(self.image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不含图像数据）"""
        return {
            'data_id': self.data_id,
            'image_path': self.image_path,
            'annotations': self.annotations,
            'metadata': self.metadata.to_dict() if self.metadata else None
        }


@dataclass
class L2FeatureData:
    """
    L2层：特征数据
    
    存储从L1层提取的特征向量、中间表示
    
    参考文档2.1节：
    L2层存储视觉特征、多模态特征等中间表示
    支持特征索引和快速检索
    """
    data_id: str
    parent_id: str                          # 对应的L1层数据ID
    visual_features: Optional[np.ndarray] = None    # 视觉特征
    text_features: Optional[np.ndarray] = None      # 文本特征
    fusion_features: Optional[np.ndarray] = None    # 融合特征
    feature_dim: int = 0
    metadata: Optional[DataMetadata] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = DataMetadata(
                data_id=self.data_id,
                layer=DataLayer.L2_FEATURE.value,
                data_type=DataType.FEATURE.value,
                source=self.parent_id,
                timestamp=datetime.now().isoformat(),
                parent_ids=[self.parent_id]
            )
    
    def get_feature_vector(self, feature_type: str = 'fusion') -> Optional[np.ndarray]:
        """
        获取特征向量
        
        Args:
            feature_type: 特征类型 ('visual', 'text', 'fusion')
        
        Returns:
            特征向量
        """
        if feature_type == 'visual':
            return self.visual_features
        elif feature_type == 'text':
            return self.text_features
        elif feature_type == 'fusion':
            return self.fusion_features
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不含特征数组）"""
        return {
            'data_id': self.data_id,
            'parent_id': self.parent_id,
            'feature_dim': self.feature_dim,
            'metadata': self.metadata.to_dict() if self.metadata else None
        }


@dataclass
class L3SemanticData:
    """
    L3层：语义数据
    
    存储语义理解结果、知识关联
    
    参考文档2.1节：
    L3层存储高级语义信息，包括病害诊断结果、
    知识图谱关联、推理结论等
    """
    data_id: str
    parent_id: str                          # 对应的L2层数据ID
    diagnosis_result: Optional[Dict[str, Any]] = None   # 诊断结果
    disease_name: Optional[str] = None
    confidence: float = 0.0
    knowledge_entities: List[str] = field(default_factory=list)  # 关联的知识实体
    reasoning_path: List[str] = field(default_factory=list)      # 推理路径
    treatment_suggestion: Optional[str] = None
    metadata: Optional[DataMetadata] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = DataMetadata(
                data_id=self.data_id,
                layer=DataLayer.L3_SEMANTIC.value,
                data_type=DataType.DIAGNOSIS.value,
                source=self.parent_id,
                timestamp=datetime.now().isoformat(),
                parent_ids=[self.parent_id]
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data_id': self.data_id,
            'parent_id': self.parent_id,
            'diagnosis_result': self.diagnosis_result,
            'disease_name': self.disease_name,
            'confidence': self.confidence,
            'knowledge_entities': self.knowledge_entities,
            'reasoning_path': self.reasoning_path,
            'treatment_suggestion': self.treatment_suggestion,
            'metadata': self.metadata.to_dict() if self.metadata else None
        }


class DataLayerManager:
    """
    数据分层管理器
    
    统一管理L1/L2/L3三层数据的存储、检索和关联
    
    参考文档2.1节：
    实现数据的分层管理和跨层关联
    """
    
    def __init__(self, storage_root: str = "./data_layers"):
        """
        初始化数据分层管理器
        
        Args:
            storage_root: 存储根目录
        """
        self.storage_root = Path(storage_root)
        self.l1_path = self.storage_root / "L1_raw"
        self.l2_path = self.storage_root / "L2_feature"
        self.l3_path = self.storage_root / "L3_semantic"
        
        # 创建目录
        self.l1_path.mkdir(parents=True, exist_ok=True)
        self.l2_path.mkdir(parents=True, exist_ok=True)
        self.l3_path.mkdir(parents=True, exist_ok=True)
        
        # 内存索引
        self.l1_index: Dict[str, L1RawData] = {}
        self.l2_index: Dict[str, L2FeatureData] = {}
        self.l3_index: Dict[str, L3SemanticData] = {}
        
        # 层级关联索引
        self.l1_to_l2: Dict[str, List[str]] = defaultdict(list)  # L1 -> L2
        self.l2_to_l3: Dict[str, List[str]] = defaultdict(list)  # L2 -> L3
        self.l3_to_l1: Dict[str, str] = {}  # L3 -> L1 (通过L2)
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 加载已有数据
        self._load_existing_data()
    
    def _load_existing_data(self):
        """加载已有数据"""
        # 加载L1层元数据
        l1_meta_path = self.l1_path / "metadata.json"
        if l1_meta_path.exists():
            with open(l1_meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    metadata = DataMetadata.from_dict(item)
                    self.l1_index[metadata.data_id] = L1RawData(
                        data_id=metadata.data_id,
                        metadata=metadata
                    )
        
        # 加载L2层元数据
        l2_meta_path = self.l2_path / "metadata.json"
        if l2_meta_path.exists():
            with open(l2_meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    metadata = DataMetadata.from_dict(item)
                    self.l2_index[metadata.data_id] = L2FeatureData(
                        data_id=metadata.data_id,
                        parent_id=metadata.parent_ids[0] if metadata.parent_ids else "",
                        metadata=metadata
                    )
        
        # 加载L3层元数据
        l3_meta_path = self.l3_path / "metadata.json"
        if l3_meta_path.exists():
            with open(l3_meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    metadata = DataMetadata.from_dict(item)
                    self.l3_index[metadata.data_id] = L3SemanticData(
                        data_id=metadata.data_id,
                        parent_id=metadata.parent_ids[0] if metadata.parent_ids else "",
                        metadata=metadata
                    )
    
    def _save_metadata(self):
        """保存元数据"""
        with self._lock:
            # 保存L1元数据
            l1_meta = [d.metadata.to_dict() for d in self.l1_index.values()]
            with open(self.l1_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(l1_meta, f, ensure_ascii=False, indent=2)
            
            # 保存L2元数据
            l2_meta = [d.metadata.to_dict() for d in self.l2_index.values()]
            with open(self.l2_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(l2_meta, f, ensure_ascii=False, indent=2)
            
            # 保存L3元数据
            l3_meta = [d.metadata.to_dict() for d in self.l3_index.values()]
            with open(self.l3_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(l3_meta, f, ensure_ascii=False, indent=2)
    
    def store_l1_data(self, data: L1RawData) -> str:
        """
        存储L1层原始数据
        
        Args:
            data: L1层数据
        
        Returns:
            数据ID
        """
        with self._lock:
            # 保存图像数据
            if data.image_data is not None:
                image_path = self.l1_path / f"{data.data_id}.npy"
                np.save(image_path, data.image_data)
                data.image_path = str(image_path)
            
            # 保存标注
            if data.annotations:
                anno_path = self.l1_path / f"{data.data_id}_annotations.json"
                with open(anno_path, 'w', encoding='utf-8') as f:
                    json.dump(data.annotations, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.l1_index[data.data_id] = data
            
            # 保存元数据
            self._save_metadata()
        
        return data.data_id
    
    def store_l2_data(self, data: L2FeatureData) -> str:
        """
        存储L2层特征数据
        
        Args:
            data: L2层数据
        
        Returns:
            数据ID
        """
        with self._lock:
            # 保存特征向量
            feature_path = self.l2_path / f"{data.data_id}.npz"
            np.savez(
                feature_path,
                visual=data.visual_features,
                text=data.text_features,
                fusion=data.fusion_features
            )
            
            # 更新索引
            self.l2_index[data.data_id] = data
            
            # 更新层级关联
            self.l1_to_l2[data.parent_id].append(data.data_id)
            
            # 更新父数据的children_ids
            if data.parent_id in self.l1_index:
                self.l1_index[data.parent_id].metadata.children_ids.append(data.data_id)
            
            # 保存元数据
            self._save_metadata()
        
        return data.data_id
    
    def store_l3_data(self, data: L3SemanticData) -> str:
        """
        存储L3层语义数据
        
        Args:
            data: L3层数据
        
        Returns:
            数据ID
        """
        with self._lock:
            # 保存语义数据
            semantic_path = self.l3_path / f"{data.data_id}.json"
            with open(semantic_path, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.l3_index[data.data_id] = data
            
            # 更新层级关联
            self.l2_to_l3[data.parent_id].append(data.data_id)
            
            # 追溯到L1层
            if data.parent_id in self.l2_index:
                l2_data = self.l2_index[data.parent_id]
                self.l3_to_l1[data.data_id] = l2_data.parent_id
            
            # 更新父数据的children_ids
            if data.parent_id in self.l2_index:
                self.l2_index[data.parent_id].metadata.children_ids.append(data.data_id)
            
            # 保存元数据
            self._save_metadata()
        
        return data.data_id
    
    def get_l1_data(self, data_id: str, load_image: bool = False) -> Optional[L1RawData]:
        """
        获取L1层数据
        
        Args:
            data_id: 数据ID
            load_image: 是否加载图像数据
        
        Returns:
            L1层数据
        """
        if data_id not in self.l1_index:
            return None
        
        data = self.l1_index[data_id]
        
        if load_image and data.image_path:
            data.image_data = np.load(data.image_path)
        
        return data
    
    def get_l2_data(self, data_id: str, load_features: bool = False) -> Optional[L2FeatureData]:
        """
        获取L2层数据
        
        Args:
            data_id: 数据ID
            load_features: 是否加载特征向量
        
        Returns:
            L2层数据
        """
        if data_id not in self.l2_index:
            return None
        
        data = self.l2_index[data_id]
        
        if load_features:
            feature_path = self.l2_path / f"{data_id}.npz"
            if feature_path.exists():
                features = np.load(feature_path)
                data.visual_features = features.get('visual')
                data.text_features = features.get('text')
                data.fusion_features = features.get('fusion')
        
        return data
    
    def get_l3_data(self, data_id: str) -> Optional[L3SemanticData]:
        """
        获取L3层数据
        
        Args:
            data_id: 数据ID
        
        Returns:
            L3层数据
        """
        return self.l3_index.get(data_id)
    
    def get_data_lineage(self, data_id: str) -> Dict[str, Any]:
        """
        获取数据血缘关系
        
        Args:
            data_id: 数据ID
        
        Returns:
            血缘关系信息
        """
        lineage = {
            'data_id': data_id,
            'layer': None,
            'parents': [],
            'children': []
        }
        
        # 检查L1层
        if data_id in self.l1_index:
            data = self.l1_index[data_id]
            lineage['layer'] = 'L1'
            lineage['children'] = self.l1_to_l2.get(data_id, [])
        
        # 检查L2层
        elif data_id in self.l2_index:
            data = self.l2_index[data_id]
            lineage['layer'] = 'L2'
            lineage['parents'] = [data.parent_id]
            lineage['children'] = self.l2_to_l3.get(data_id, [])
        
        # 检查L3层
        elif data_id in self.l3_index:
            data = self.l3_index[data_id]
            lineage['layer'] = 'L3'
            lineage['parents'] = [data.parent_id]
            l1_id = self.l3_to_l1.get(data_id)
            if l1_id:
                lineage['root_parent'] = l1_id
        
        return lineage
    
    def get_full_pipeline_data(self, l1_data_id: str) -> Dict[str, Any]:
        """
        获取完整流水线数据
        
        从L1层数据ID获取关联的所有L2和L3数据
        
        Args:
            l1_data_id: L1层数据ID
        
        Returns:
            完整流水线数据
        """
        result = {
            'l1': None,
            'l2': [],
            'l3': []
        }
        
        # 获取L1数据
        result['l1'] = self.get_l1_data(l1_data_id)
        
        # 获取关联的L2数据
        l2_ids = self.l1_to_l2.get(l1_data_id, [])
        for l2_id in l2_ids:
            l2_data = self.get_l2_data(l2_id)
            if l2_data:
                result['l2'].append(l2_data)
            
            # 获取关联的L3数据
            l3_ids = self.l2_to_l3.get(l2_id, [])
            for l3_id in l3_ids:
                l3_data = self.get_l3_data(l3_id)
                if l3_data:
                    result['l3'].append(l3_data)
        
        return result
    
    def query_by_layer(
        self,
        layer: DataLayer,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        按层级查询数据
        
        Args:
            layer: 数据层级
            filters: 过滤条件
        
        Returns:
            符合条件的数据ID列表
        """
        if layer == DataLayer.L1_RAW:
            index = self.l1_index
        elif layer == DataLayer.L2_FEATURE:
            index = self.l2_index
        elif layer == DataLayer.L3_SEMANTIC:
            index = self.l3_index
        else:
            return []
        
        if not filters:
            return list(index.keys())
        
        results = []
        for data_id, data in index.items():
            match = True
            for key, value in filters.items():
                if hasattr(data, key):
                    if getattr(data, key) != value:
                        match = False
                        break
                elif data.metadata and hasattr(data.metadata, key):
                    if getattr(data.metadata, key) != value:
                        match = False
                        break
            
            if match:
                results.append(data_id)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            统计信息
        """
        return {
            'L1_raw': {
                'count': len(self.l1_index),
                'data_types': self._count_data_types(self.l1_index)
            },
            'L2_feature': {
                'count': len(self.l2_index),
                'data_types': self._count_data_types(self.l2_index)
            },
            'L3_semantic': {
                'count': len(self.l3_index),
                'data_types': self._count_data_types(self.l3_index)
            },
            'linkages': {
                'l1_to_l2': sum(len(v) for v in self.l1_to_l2.values()),
                'l2_to_l3': sum(len(v) for v in self.l2_to_l3.values())
            }
        }
    
    def _count_data_types(self, index: Dict) -> Dict[str, int]:
        """统计数据类型分布"""
        type_counts = defaultdict(int)
        for data in index.values():
            if data.metadata:
                type_counts[data.metadata.data_type] += 1
        return dict(type_counts)
    
    def clear_layer(self, layer: DataLayer):
        """
        清空指定层级数据
        
        Args:
            layer: 数据层级
        """
        with self._lock:
            if layer == DataLayer.L1_RAW:
                self.l1_index.clear()
                self.l1_to_l2.clear()
                # 删除文件
                for f in self.l1_path.glob("*"):
                    f.unlink()
            
            elif layer == DataLayer.L2_FEATURE:
                self.l2_index.clear()
                self.l2_to_l3.clear()
                for k in list(self.l1_to_l2.keys()):
                    self.l1_to_l2[k] = []
                for f in self.l2_path.glob("*"):
                    f.unlink()
            
            elif layer == DataLayer.L3_SEMANTIC:
                self.l3_index.clear()
                self.l3_to_l1.clear()
                for k in list(self.l2_to_l3.keys()):
                    self.l2_to_l3[k] = []
                for f in self.l3_path.glob("*"):
                    f.unlink()
            
            self._save_metadata()


class DataLayerPipeline:
    """
    数据分层流水线
    
    实现L1->L2->L3的数据处理流水线
    
    参考文档2.1节：
    数据在各层之间流转，支持增量处理和血缘追踪
    """
    
    def __init__(self, manager: DataLayerManager):
        """
        初始化流水线
        
        Args:
            manager: 数据分层管理器
        """
        self.manager = manager
        
        # 处理器注册表
        self.l1_processors: List[callable] = []
        self.l2_processors: List[callable] = []
    
    def register_l1_processor(self, processor: callable):
        """
        注册L1层处理器
        
        Args:
            processor: 处理函数，接收L1数据，返回L2数据
        """
        self.l1_processors.append(processor)
    
    def register_l2_processor(self, processor: callable):
        """
        注册L2层处理器
        
        Args:
            processor: 处理函数，接收L2数据，返回L3数据
        """
        self.l2_processors.append(processor)
    
    def process_l1_to_l2(self, l1_data_id: str) -> List[str]:
        """
        处理L1数据生成L2数据
        
        Args:
            l1_data_id: L1层数据ID
        
        Returns:
            生成的L2层数据ID列表
        """
        l1_data = self.manager.get_l1_data(l1_data_id, load_image=True)
        if l1_data is None:
            return []
        
        l2_ids = []
        for processor in self.l1_processors:
            l2_data = processor(l1_data)
            if l2_data:
                if isinstance(l2_data, list):
                    for d in l2_data:
                        l2_ids.append(self.manager.store_l2_data(d))
                else:
                    l2_ids.append(self.manager.store_l2_data(l2_data))
        
        return l2_ids
    
    def process_l2_to_l3(self, l2_data_id: str) -> List[str]:
        """
        处理L2数据生成L3数据
        
        Args:
            l2_data_id: L2层数据ID
        
        Returns:
            生成的L3层数据ID列表
        """
        l2_data = self.manager.get_l2_data(l2_data_id, load_features=True)
        if l2_data is None:
            return []
        
        l3_ids = []
        for processor in self.l2_processors:
            l3_data = processor(l2_data)
            if l3_data:
                if isinstance(l3_data, list):
                    for d in l3_data:
                        l3_ids.append(self.manager.store_l3_data(d))
                else:
                    l3_ids.append(self.manager.store_l3_data(l3_data))
        
        return l3_ids
    
    def process_full_pipeline(self, l1_data_id: str) -> Dict[str, Any]:
        """
        执行完整流水线处理
        
        Args:
            l1_data_id: L1层数据ID
        
        Returns:
            处理结果
        """
        result = {
            'l1_id': l1_data_id,
            'l2_ids': [],
            'l3_ids': []
        }
        
        # L1 -> L2
        l2_ids = self.process_l1_to_l2(l1_data_id)
        result['l2_ids'] = l2_ids
        
        # L2 -> L3
        for l2_id in l2_ids:
            l3_ids = self.process_l2_to_l3(l2_id)
            result['l3_ids'].extend(l3_ids)
        
        return result


def demo_data_layers():
    """演示数据分层架构"""
    print("=" * 70)
    print("📊 L1/L2/L3数据分层架构演示")
    print("=" * 70)
    
    # 创建管理器
    manager = DataLayerManager("./demo_data_layers")
    
    print("\n📦 创建L1层原始数据...")
    # 创建L1数据
    l1_data = L1RawData(
        data_id="wheat_001",
        image_data=np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
        annotations=[
            {"label": "条锈病", "bbox": [10, 20, 100, 150], "confidence": 0.95}
        ]
    )
    l1_data.metadata.source = "field_collection"
    l1_data.metadata.tags = ["条锈病", "叶片", "田间"]
    
    l1_id = manager.store_l1_data(l1_data)
    print(f"   L1数据已存储: {l1_id}")
    
    print("\n📦 创建L2层特征数据...")
    # 创建L2数据
    l2_data = L2FeatureData(
        data_id="wheat_001_feat",
        parent_id=l1_id,
        visual_features=np.random.randn(512).astype(np.float32),
        text_features=np.random.randn(512).astype(np.float32),
        fusion_features=np.random.randn(512).astype(np.float32),
        feature_dim=512
    )
    
    l2_id = manager.store_l2_data(l2_data)
    print(f"   L2数据已存储: {l2_id}")
    
    print("\n📦 创建L3层语义数据...")
    # 创建L3数据
    l3_data = L3SemanticData(
        data_id="wheat_001_diag",
        parent_id=l2_id,
        disease_name="条锈病",
        confidence=0.92,
        diagnosis_result={
            "disease": "条锈病",
            "severity": "中度",
            "affected_area": "15%"
        },
        knowledge_entities=["条锈病", "条形柄锈菌", "三唑酮"],
        reasoning_path=["视觉特征匹配", "知识图谱推理"],
        treatment_suggestion="建议使用三唑酮或戊唑醇进行防治"
    )
    
    l3_id = manager.store_l3_data(l3_data)
    print(f"   L3数据已存储: {l3_id}")
    
    print("\n📊 数据统计:")
    stats = manager.get_statistics()
    for layer, info in stats.items():
        print(f"   {layer}: {info}")
    
    print("\n🔍 数据血缘查询:")
    lineage = manager.get_data_lineage(l3_id)
    print(f"   L3数据 {l3_id} 的血缘:")
    print(f"   - 层级: {lineage['layer']}")
    print(f"   - 父数据: {lineage['parents']}")
    print(f"   - 根父数据(L1): {lineage.get('root_parent', 'N/A')}")
    
    print("\n🔍 完整流水线数据查询:")
    pipeline_data = manager.get_full_pipeline_data(l1_id)
    print(f"   L1数据: {pipeline_data['l1'].data_id if pipeline_data['l1'] else 'N/A'}")
    print(f"   L2数据: {[d.data_id for d in pipeline_data['l2']]}")
    print(f"   L3数据: {[d.data_id for d in pipeline_data['l3']]}")
    
    print("\n" + "=" * 70)
    print("✅ 数据分层架构演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_data_layers()
