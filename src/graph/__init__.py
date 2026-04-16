# -*- coding: utf-8 -*-
"""
知识图谱模块

基于 Neo4j 的知识图谱，存储农业领域知识和病虫害关系
包含GraphRAG检索增强生成功能
"""

from pathlib import Path
from typing import Any

# Neo4j 默认连接配置
# 注意：生产环境应使用环境变量 NEO4J_PASSWORD
import os
NEO4J_CONFIG = {
    "uri": os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.environ.get("NEO4J_USER", "neo4j"),
    "password": os.environ.get("NEO4J_PASSWORD", "123456789s")
}

# 延迟导入，避免循环导入问题
def __getattr__(name):
    if name == "KnowledgeAgent":
        try:
            from .graph_engine import KnowledgeAgent
            return KnowledgeAgent
        except ImportError as e:
            print(f"⚠️ KnowledgeAgent 导入失败: {e}")
            return None
    elif name == "GraphRAGEngine":
        try:
            from .graphrag_engine import GraphRAGEngine
            return GraphRAGEngine
        except ImportError as e:
            print(f"⚠️ GraphRAGEngine 导入失败: {e}")
            return None
    elif name == "Neo4jConnection":
        try:
            from .graph_engine import Neo4jConnection
            return Neo4jConnection
        except ImportError:
            return Any
    elif name == "AgriKnowledgeGraph":
        try:
            from .knowledge_graph_builder import AgriKnowledgeGraph
            return AgriKnowledgeGraph
        except ImportError as e:
            print(f"⚠️ AgriKnowledgeGraph 导入失败: {e}")
            return None
    elif name == "TransE":
        try:
            from .knowledge_graph_builder import TransE
            return TransE
        except ImportError:
            return None
    elif name == "EntityType":
        try:
            from .knowledge_graph_builder import EntityType
            return EntityType
        except ImportError:
            from enum import Enum
            class EntityType(Enum):
                CROP = "Crop"
                DISEASE = "Disease"
                SYMPTOM = "Symptom"
                PATHOGEN = "Pathogen"
                ENVIRONMENT = "Environment"
                CONTROL_MEASURE = "ControlMeasure"
                CHEMICAL = "Chemical"
                VARIETY = "Variety"
            return EntityType
    elif name == "RelationType":
        try:
            from .knowledge_graph_builder import RelationType
            return RelationType
        except ImportError:
            from enum import Enum
            class RelationType(Enum):
                CAUSES = "CAUSES"
                MANIFESTS_AS = "MANIFESTS_AS"
                HAS_PATHOGEN = "HAS_PATHOGEN"
                TREATED_BY = "TREATED_BY"
            return RelationType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "NEO4J_CONFIG",
    # 核心组件
    "KnowledgeAgent",
    "GraphRAGEngine",
    "Neo4jConnection",
    # 知识图谱构建
    "AgriKnowledgeGraph",
    "TransE",
    "EntityType",
    "RelationType"
]
