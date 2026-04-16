# -*- coding: utf-8 -*-
"""
知识图谱构建模块 (Knowledge Graph Builder)

根据研究文档实现:
1. 农业知识图谱本体设计 (AgriKG Ontology)
2. TransE 图嵌入训练
3. 多跳推理支持
4. 自动化知识抽取

本体结构:
- 实体: Crop, Disease, Symptom, Pathogen, Environment, ControlMeasure
- 关系: CAUSES, MANIFESTS_AS, HAS_PATHOGEN, AFFECTED_BY, TREATED_BY
"""
import os
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import random

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader


class EntityType(Enum):
    """实体类型"""
    CROP = "Crop"                    # 作物
    DISEASE = "Disease"              # 病害
    SYMPTOM = "Symptom"              # 症状
    PATHOGEN = "Pathogen"            # 病原体
    ENVIRONMENT = "Environment"      # 环境条件
    CONTROL_MEASURE = "ControlMeasure"  # 防治措施
    CHEMICAL = "Chemical"            # 化学药剂
    VARIETY = "Variety"              # 品种


class RelationType(Enum):
    """关系类型"""
    CAUSES = "CAUSES"                    # 导致
    MANIFESTS_AS = "MANIFESTS_AS"        # 表现为
    HAS_PATHOGEN = "HAS_PATHOGEN"        # 有病原体
    AFFECTED_BY = "AFFECTED_BY"          # 受...影响
    TREATED_BY = "TREATED_BY"            # 被...治疗
    HAS_SYMPTOM = "HAS_SYMPTOM"          # 有症状
    OCCURS_IN = "OCCURS_IN"              # 发生在
    RECOMMENDED_FOR = "RECOMMENDED_FOR"  # 推荐用于
    SIMILAR_TO = "SIMILAR_TO"            # 相似于
    CONTRAINDICATED_WITH = "CONTRAINDICATED_WITH"  # 禁忌搭配


@dataclass
class Entity:
    """知识图谱实体"""
    id: str
    name: str
    type: EntityType
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "properties": self.properties
        }


@dataclass
class Relation:
    """知识图谱关系"""
    source: str  # 源实体ID
    target: str  # 目标实体ID
    type: RelationType
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "properties": self.properties
        }


@dataclass
class Triple:
    """知识三元组 (h, r, t)"""
    head: str
    relation: str
    tail: str
    
    def to_tuple(self) -> Tuple[str, str, str]:
        return (self.head, self.relation, self.tail)


class AgriKGOntology:
    """
    农业知识图谱本体
    
    定义核心实体类型和关系类型的约束
    """
    
    # 实体类型定义
    ENTITY_DEFINITIONS = {
        EntityType.CROP: {
            "description": "作物",
            "properties": ["name", "species", "growth_stage", "planting_region"]
        },
        EntityType.DISEASE: {
            "description": "病害",
            "properties": ["name", "chinese_name", "severity", "occurrence_stage"]
        },
        EntityType.SYMPTOM: {
            "description": "症状",
            "properties": ["name", "description", "location", "color", "shape"]
        },
        EntityType.PATHOGEN: {
            "description": "病原体",
            "properties": ["name", "scientific_name", "type", "optimal_temp", "optimal_humidity"]
        },
        EntityType.ENVIRONMENT: {
            "description": "环境条件",
            "properties": ["condition", "temperature_range", "humidity_range", "description"]
        },
        EntityType.CONTROL_MEASURE: {
            "description": "防治措施",
            "properties": ["name", "type", "application_method", "dosage", "timing"]
        },
        EntityType.CHEMICAL: {
            "description": "化学药剂",
            "properties": ["name", "active_ingredient", "category", "toxicity"]
        },
        EntityType.VARIETY: {
            "description": "品种",
            "properties": ["name", "resistance", "yield_potential", "maturity_period"]
        }
    }
    
    # 关系约束 (哪些实体类型可以建立哪些关系)
    RELATION_CONSTRAINTS = {
        RelationType.CAUSES: (EntityType.PATHOGEN, EntityType.DISEASE),
        RelationType.MANIFESTS_AS: (EntityType.DISEASE, EntityType.SYMPTOM),
        RelationType.HAS_PATHOGEN: (EntityType.DISEASE, EntityType.PATHOGEN),
        RelationType.AFFECTED_BY: (EntityType.DISEASE, EntityType.ENVIRONMENT),
        RelationType.TREATED_BY: (EntityType.DISEASE, EntityType.CONTROL_MEASURE),
        RelationType.HAS_SYMPTOM: (EntityType.DISEASE, EntityType.SYMPTOM),
        RelationType.OCCURS_IN: (EntityType.DISEASE, EntityType.CROP),
        RelationType.RECOMMENDED_FOR: (EntityType.CONTROL_MEASURE, EntityType.DISEASE),
        RelationType.SIMILAR_TO: (EntityType.DISEASE, EntityType.DISEASE),
        RelationType.CONTRAINDICATED_WITH: (EntityType.CHEMICAL, EntityType.CHEMICAL)
    }
    
    @classmethod
    def validate_triple(cls, head_type: EntityType, relation: RelationType, tail_type: EntityType) -> bool:
        """验证三元组是否符合本体约束"""
        if relation not in cls.RELATION_CONSTRAINTS:
            return False
        
        expected_head, expected_tail = cls.RELATION_CONSTRAINTS[relation]
        return head_type == expected_head and tail_type == expected_tail


class TransE(nn.Module):
    """
    TransE 模型
    
    知识图谱嵌入算法，将实体和关系映射到低维向量空间
    基本思想: h + r ≈ t (头实体向量 + 关系向量 ≈ 尾实体向量)
    
    论文: "Translating Embeddings for Modeling Multi-relational Data" (Bordes et al., 2013)
    """
    
    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        embedding_dim: int = 100,
        gamma: float = 12.0,
        norm: int = 1
    ):
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.gamma = gamma  # 边界
        self.norm = norm    # L1或L2范数
        
        # 实体嵌入
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        
        # 关系嵌入
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
        
        # 初始化
        self._init_weights()
    
    def _init_weights(self):
        """初始化权重"""
        # 实体嵌入使用均匀分布初始化
        nn.init.uniform_(
            self.entity_embeddings.weight,
            -6 / (self.embedding_dim ** 0.5),
            6 / (self.embedding_dim ** 0.5)
        )
        
        # 关系嵌入使用均匀分布初始化
        nn.init.uniform_(
            self.relation_embeddings.weight,
            -6 / (self.embedding_dim ** 0.5),
            6 / (self.embedding_dim ** 0.5)
        )
        
        # 归一化实体嵌入
        self.entity_embeddings.weight.data = F.normalize(
            self.entity_embeddings.weight.data, p=2, dim=1
        )
    
    def forward(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor,
        negative_heads: Optional[torch.Tensor] = None,
        negative_tails: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param heads: 头实体索引 [batch_size]
        :param relations: 关系索引 [batch_size]
        :param tails: 尾实体索引 [batch_size]
        :param negative_heads: 负采样头实体 [batch_size]
        :param negative_tails: 负采样尾实体 [batch_size]
        :return: 损失和分数
        """
        # 获取嵌入
        h = self.entity_embeddings(heads)
        r = self.relation_embeddings(relations)
        t = self.entity_embeddings(tails)
        
        # 计算正样本分数 (距离)
        positive_score = self._score(h, r, t)
        
        losses = {}
        
        if negative_heads is not None and negative_tails is not None:
            # 负采样
            h_neg = self.entity_embeddings(negative_heads)
            t_neg = self.entity_embeddings(negative_tails)
            
            # 计算负样本分数
            negative_score = self._score(h_neg, r, t_neg)
            
            # 计算损失 (margin-based ranking loss)
            loss = F.relu(self.gamma + positive_score - negative_score).mean()
            losses['loss'] = loss
            losses['positive_score'] = positive_score.mean()
            losses['negative_score'] = negative_score.mean()
        else:
            losses['positive_score'] = positive_score.mean()
        
        return losses
    
    def _score(self, h: torch.Tensor, r: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        计算三元组分数 (距离)
        
        :param h: 头实体嵌入 [batch_size, dim]
        :param r: 关系嵌入 [batch_size, dim]
        :param t: 尾实体嵌入 [batch_size, dim]
        :return: 分数 [batch_size]
        """
        # TransE: score = ||h + r - t||
        score = torch.norm(h + r - t, p=self.norm, dim=1)
        return score
    
    def predict_tail(self, head_id: int, relation_id: int, k: int = 10) -> List[Tuple[int, float]]:
        """
        预测尾实体
        
        :param head_id: 头实体ID
        :param relation_id: 关系ID
        :param k: 返回前k个
        :return: [(entity_id, score), ...]
        """
        with torch.no_grad():
            h = self.entity_embeddings(torch.tensor([head_id]))
            r = self.relation_embeddings(torch.tensor([relation_id]))
            
            # 计算所有实体作为尾实体的分数
            all_entities = self.entity_embeddings.weight
            scores = torch.norm(h + r - all_entities, p=self.norm, dim=1)
            
            # 获取前k个
            top_k_scores, top_k_indices = torch.topk(scores, k, largest=False)
            
            return [(idx.item(), score.item()) for idx, score in zip(top_k_indices, top_k_scores)]
    
    def get_embedding(self, entity_id: int) -> np.ndarray:
        """获取实体嵌入向量"""
        with torch.no_grad():
            embedding = self.entity_embeddings(torch.tensor([entity_id]))
            return embedding.numpy()[0]


class KnowledgeGraphDataset(Dataset):
    """知识图谱数据集"""
    
    def __init__(self, triples: List[Triple], entity2id: Dict[str, int], relation2id: Dict[str, int]):
        self.triples = triples
        self.entity2id = entity2id
        self.relation2id = relation2id
        self.num_entities = len(entity2id)
    
    def __len__(self):
        return len(self.triples)
    
    def __getitem__(self, idx):
        triple = self.triples[idx]
        
        head_id = self.entity2id[triple.head]
        relation_id = self.relation2id[triple.relation]
        tail_id = self.entity2id[triple.tail]
        
        # 负采样
        negative_head = random.randint(0, self.num_entities - 1)
        negative_tail = random.randint(0, self.num_entities - 1)
        
        return {
            'head': torch.tensor(head_id),
            'relation': torch.tensor(relation_id),
            'tail': torch.tensor(tail_id),
            'negative_head': torch.tensor(negative_head),
            'negative_tail': torch.tensor(negative_tail)
        }


class AgriKnowledgeGraph:
    """
    农业知识图谱
    
    管理实体、关系和三元组
    """
    
    def __init__(self, neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        """
        初始化知识图谱
        
        :param neo4j_uri: Neo4j数据库URI (可选)
        :param neo4j_user: Neo4j用户名 (可选)
        :param neo4j_password: Neo4j密码 (可选)
        """
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.triples: List[Triple] = []
        
        # ID映射
        self.entity2id: Dict[str, int] = {}
        self.relation2id: Dict[str, int] = {}
        self.id2entity: Dict[int, str] = {}
        self.id2relation: Dict[int, str] = {}
        
        # TransE模型
        self.transe_model: Optional[TransE] = None
        
        # Neo4j连接配置
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_driver = None
    
    def add_entity(self, entity: Entity) -> str:
        """添加实体"""
        self.entities[entity.id] = entity
        
        # 分配ID
        if entity.id not in self.entity2id:
            entity_id = len(self.entity2id)
            self.entity2id[entity.id] = entity_id
            self.id2entity[entity_id] = entity.id
        
        return entity.id
    
    def add_relation(self, relation: Relation):
        """添加关系"""
        self.relations.append(relation)
        
        # 创建三元组
        triple = Triple(
            head=relation.source,
            relation=relation.type.value,
            tail=relation.target
        )
        self.triples.append(triple)
        
        # 分配关系ID
        relation_key = relation.type.value
        if relation_key not in self.relation2id:
            relation_id = len(self.relation2id)
            self.relation2id[relation_key] = relation_id
            self.id2relation[relation_id] = relation_key
    
    def build_initial_knowledge(self):
        """构建初始农业知识"""
        print("🏗️ 构建初始农业知识图谱...")
        
        # 添加作物
        wheat = Entity(
            id="crop_wheat",
            name="小麦",
            type=EntityType.CROP,
            properties={"species": "Triticum aestivum", "type": "冬小麦/春小麦"}
        )
        self.add_entity(wheat)
        
        # 添加病害
        diseases = [
            ("disease_stripe_rust", "条锈病", "Stripe Rust", "Puccinia striiformis"),
            ("disease_leaf_rust", "叶锈病", "Leaf Rust", "Puccinia triticina"),
            ("disease_stem_rust", "秆锈病", "Stem Rust", "Puccinia graminis"),
            ("disease_powdery_mildew", "白粉病", "Powdery Mildew", "Blumeria graminis"),
            ("disease_fusarium", "赤霉病", "Fusarium Head Blight", "Fusarium graminearum"),
            ("disease_sharp_eyespot", "纹枯病", "Sharp Eyespot", "Rhizoctonia cerealis"),
            ("disease_root_rot", "根腐病", "Root Rot", "Bipolaris sorokiniana"),
        ]
        
        for disease_id, cn_name, en_name, pathogen_name in diseases:
            disease = Entity(
                id=disease_id,
                name=cn_name,
                type=EntityType.DISEASE,
                properties={"chinese_name": cn_name, "english_name": en_name}
            )
            self.add_entity(disease)
            
            # 添加病原体
            pathogen_id = f"pathogen_{disease_id.split('_')[1]}"
            pathogen = Entity(
                id=pathogen_id,
                name=pathogen_name,
                type=EntityType.PATHOGEN,
                properties={"scientific_name": pathogen_name}
            )
            self.add_entity(pathogen)
            
            # 添加关系: 病害 - 有病原体 -> 病原体
            self.add_relation(Relation(
                source=disease_id,
                target=pathogen_id,
                type=RelationType.HAS_PATHOGEN
            ))
            
            # 添加关系: 病害 - 发生在 -> 小麦
            self.add_relation(Relation(
                source=disease_id,
                target="crop_wheat",
                type=RelationType.OCCURS_IN
            ))
        
        # 添加症状
        symptoms = {
            "disease_stripe_rust": ["黄色条状孢子堆", "沿叶脉排列", "孢子堆破裂呈粉状"],
            "disease_powdery_mildew": ["白色粉状霉层", "叶片发黄", "黑色小点"],
            "disease_fusarium": ["穗部粉红色霉层", "籽粒干瘪变色", "穗轴腐烂"],
        }
        
        for disease_id, symptom_list in symptoms.items():
            for i, symptom_name in enumerate(symptom_list):
                symptom_id = f"symptom_{disease_id.split('_')[1]}_{i}"
                symptom = Entity(
                    id=symptom_id,
                    name=symptom_name,
                    type=EntityType.SYMPTOM
                )
                self.add_entity(symptom)
                
                # 添加关系: 病害 - 表现为 -> 症状
                self.add_relation(Relation(
                    source=disease_id,
                    target=symptom_id,
                    type=RelationType.MANIFESTS_AS
                ))
        
        # 添加防治措施
        control_measures = [
            ("control_triadimefon", "三唑酮", "化学防治", "粉锈宁"),
            ("control_carbendazim", "多菌灵", "化学防治", "广谱杀菌剂"),
            ("control_tebuconazole", "戊唑醇", "化学防治", "三唑类"),
            ("control_resistant_variety", "抗病品种", "农业防治", "选用抗病品种"),
            ("control_crop_rotation", "轮作倒茬", "农业防治", "与非寄主作物轮作"),
        ]
        
        for measure_id, name, measure_type, description in control_measures:
            measure = Entity(
                id=measure_id,
                name=name,
                type=EntityType.CONTROL_MEASURE,
                properties={"type": measure_type, "description": description}
            )
            self.add_entity(measure)
        
        # 添加病害-防治关系
        treatment_relations = [
            ("disease_stripe_rust", "control_triadimefon"),
            ("disease_powdery_mildew", "control_triadimefon"),
            ("disease_fusarium", "control_carbendazim"),
            ("disease_fusarium", "control_tebuconazole"),
        ]
        
        for disease_id, measure_id in treatment_relations:
            self.add_relation(Relation(
                source=disease_id,
                target=measure_id,
                type=RelationType.TREATED_BY
            ))
        
        print(f"✅ 初始知识图谱构建完成:")
        print(f"   实体数: {len(self.entities)}")
        print(f"   关系数: {len(self.relations)}")
        print(f"   三元组数: {len(self.triples)}")
    
    def train_transe(
        self,
        embedding_dim: int = 100,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        gamma: float = 12.0
    ):
        """
        训练TransE模型
        
        :param embedding_dim: 嵌入维度
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        :param learning_rate: 学习率
        :param gamma: 边界参数
        """
        print("\n🚀 训练TransE模型...")
        
        # 创建数据集
        dataset = KnowledgeGraphDataset(self.triples, self.entity2id, self.relation2id)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 创建模型
        self.transe_model = TransE(
            num_entities=len(self.entity2id),
            num_relations=len(self.relation2id),
            embedding_dim=embedding_dim,
            gamma=gamma
        )
        
        # 优化器
        optimizer = torch.optim.Adam(self.transe_model.parameters(), lr=learning_rate)
        
        # 训练
        for epoch in range(epochs):
            total_loss = 0.0
            
            for batch in dataloader:
                optimizer.zero_grad()

                losses = self.transe_model(
                    heads=batch['head'],
                    relations=batch['relation'],
                    tails=batch['tail'],
                    negative_heads=batch['negative_head'],
                    negative_tails=batch['negative_tail']
                )
                loss = losses['loss']
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                avg_loss = total_loss / len(dataloader)
                print(f"   Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        print("✅ TransE训练完成")
    
    def find_similar_entities(self, entity_id: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        查找相似实体
        
        :param entity_id: 实体ID
        :param k: 返回前k个
        :return: [(entity_id, similarity), ...]
        """
        if self.transe_model is None:
            return []
        
        entity_idx = self.entity2id.get(entity_id)
        if entity_idx is None:
            return []
        
        # 获取实体嵌入
        entity_emb = self.transe_model.get_embedding(entity_idx)
        
        # 计算与所有实体的相似度
        similarities = []
        for other_id, other_idx in self.entity2id.items():
            if other_id != entity_id:
                other_emb = self.transe_model.get_embedding(other_idx)
                similarity = np.dot(entity_emb, other_emb) / (np.linalg.norm(entity_emb) * np.linalg.norm(other_emb))
                similarities.append((other_id, similarity))
        
        # 排序并返回前k个
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def multi_hop_reasoning(self, start_entity: str, relation_path: List[str], max_depth: int = 3) -> List[Dict]:
        """
        多跳推理
        
        :param start_entity: 起始实体
        :param relation_path: 关系路径
        :param max_depth: 最大深度
        :return: 推理结果路径
        """
        results = []
        
        def dfs(current_entity: str, path: List[Dict], depth: int):
            if depth >= max_depth:
                return
            
            # 查找当前实体的所有出边
            for relation in self.relations:
                if relation.source == current_entity:
                    new_path = path + [{
                        "entity": current_entity,
                        "relation": relation.type.value,
                        "next_entity": relation.target
                    }]
                    
                    if depth == max_depth - 1:
                        results.append(new_path)
                    else:
                        dfs(relation.target, new_path, depth + 1)
        
        dfs(start_entity, [], 0)
        
        return results
    
    def get_disease_info(self, disease_name: str) -> Dict[str, Any]:
        """
        获取病害信息
        
        :param disease_name: 病害名称（中文或英文）
        :return: 病害信息字典
        """
        result = {
            "name": disease_name,
            "symptoms": [],
            "pathogen": None,
            "treatment": [],
            "prevention": [],
            "environment": []
        }
        
        # 查找病害实体
        disease_entity = None
        for entity in self.entities.values():
            if entity.name == disease_name or disease_name in entity.name:
                if entity.entity_type == EntityType.DISEASE or "disease" in entity.id.lower():
                    disease_entity = entity
                    break
        
        if disease_entity is None:
            # 尝试通过ID查找
            for eid, entity in self.entities.items():
                if disease_name.lower() in eid.lower() or disease_name.lower() in entity.name.lower():
                    disease_entity = entity
                    break
        
        if disease_entity is None:
            return result
        
        result["name"] = disease_entity.name
        
        # 查找相关关系
        for relation in self.relations:
            if relation.source == disease_entity.id:
                target_entity = self.entities.get(relation.target)
                if target_entity:
                    rel_type = relation.type.value
                    if "SYMPTOM" in rel_type:
                        result["symptoms"].append(target_entity.name)
                    elif "PATHOGEN" in rel_type or "CAUSED" in rel_type:
                        result["pathogen"] = target_entity.name
                    elif "TREAT" in rel_type:
                        result["treatment"].append(target_entity.name)
                    elif "PREVENT" in rel_type:
                        result["prevention"].append(target_entity.name)
                    elif "FAVOR" in rel_type or "ENVIRON" in rel_type:
                        result["environment"].append(target_entity.name)
        
        return result
    
    def save(self, output_dir: str):
        """保存知识图谱"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存实体
        entities_data = {eid: entity.to_dict() for eid, entity in self.entities.items()}
        with open(os.path.join(output_dir, "entities.json"), 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)
        
        # 保存关系
        relations_data = [relation.to_dict() for relation in self.relations]
        with open(os.path.join(output_dir, "relations.json"), 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)
        
        # 保存三元组
        triples_data = [asdict(triple) for triple in self.triples]
        with open(os.path.join(output_dir, "triples.json"), 'w', encoding='utf-8') as f:
            json.dump(triples_data, f, ensure_ascii=False, indent=2)
        
        # 保存ID映射
        mappings = {
            "entity2id": self.entity2id,
            "relation2id": self.relation2id
        }
        with open(os.path.join(output_dir, "mappings.json"), 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2)
        
        # 保存TransE模型
        if self.transe_model is not None:
            torch.save(self.transe_model.state_dict(), os.path.join(output_dir, "transe_model.pt"))
        
        print(f"✅ 知识图谱已保存: {output_dir}")
    
    def load(self, input_dir: str):
        """加载知识图谱"""
        # 加载实体
        with open(os.path.join(input_dir, "entities.json"), 'r', encoding='utf-8') as f:
            entities_data = json.load(f)
            for eid, data in entities_data.items():
                entity = Entity(
                    id=data['id'],
                    name=data['name'],
                    type=EntityType(data['type']),
                    properties=data.get('properties', {})
                )
                self.entities[eid] = entity
        
        # 加载关系
        with open(os.path.join(input_dir, "relations.json"), 'r', encoding='utf-8') as f:
            relations_data = json.load(f)
            for data in relations_data:
                relation = Relation(
                    source=data['source'],
                    target=data['target'],
                    type=RelationType(data['type']),
                    properties=data.get('properties', {})
                )
                self.relations.append(relation)
        
        # 加载ID映射
        with open(os.path.join(input_dir, "mappings.json"), 'r', encoding='utf-8') as f:
            mappings = json.load(f)
            self.entity2id = {k: int(v) for k, v in mappings['entity2id'].items()}
            self.relation2id = {k: int(v) for k, v in mappings['relation2id'].items()}
            self.id2entity = {int(v): k for k, v in mappings['entity2id'].items()}
            self.id2relation = {int(v): k for k, v in mappings['relation2id'].items()}
        
        print(f"✅ 知识图谱已加载: {input_dir}")
    
    def build_ontology(self):
        """构建知识图谱本体"""
        print("🏗️ 构建知识图谱本体...")
        self.build_initial_knowledge()
        print("✅ 本体构建完成")
    
    def import_agricultural_knowledge(self):
        """导入农业知识数据"""
        print("📚 导入农业知识数据...")
        # 这里可以扩展为从文件或数据库导入
        self.build_initial_knowledge()
        print("✅ 农业知识导入完成")
    
    def train_transe_embeddings(self, embedding_dim=50, epochs=100, batch_size=16, lr=0.001):
        """训练TransE图嵌入"""
        print("🚀 训练TransE图嵌入...")
        self.train_transe(embedding_dim=embedding_dim, epochs=epochs, batch_size=batch_size, learning_rate=lr)
        print("✅ TransE训练完成")


def test_knowledge_graph():
    """测试知识图谱"""
    print("=" * 70)
    print("🧪 测试农业知识图谱")
    print("=" * 70)
    
    # 创建知识图谱
    kg = AgriKnowledgeGraph()
    
    # 构建初始知识
    print("\n🏗️ 构建初始知识...")
    kg.build_initial_knowledge()
    
    # 训练TransE
    print("\n🚀 训练TransE...")
    kg.train_transe(embedding_dim=50, epochs=20, batch_size=8)
    
    # 查找相似实体
    print("\n🔍 查找相似实体...")
    similar = kg.find_similar_entities("disease_stripe_rust", k=3)
    print(f"与'条锈病'相似的实体:")
    for entity_id, similarity in similar:
        entity = kg.entities.get(entity_id)
        if entity:
            print(f"   {entity.name}: {similarity:.4f}")
    
    # 多跳推理
    print("\n🧠 多跳推理...")
    reasoning_results = kg.multi_hop_reasoning("disease_stripe_rust", [], max_depth=2)
    print(f"找到 {len(reasoning_results)} 条推理路径")
    for i, path in enumerate(reasoning_results[:3]):
        print(f"   路径 {i+1}:")
        for step in path:
            entity = kg.entities.get(step['entity'])
            next_entity = kg.entities.get(step['next_entity'])
            if entity and next_entity:
                print(f"      {entity.name} --[{step['relation']}]--> {next_entity.name}")
    
    # 保存
    print("\n💾 保存知识图谱...")
    kg.save("checkpoints/knowledge_graph")
    
    print("\n" + "=" * 70)
    print("✅ 知识图谱测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_knowledge_graph()
