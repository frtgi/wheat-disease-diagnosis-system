# -*- coding: utf-8 -*-
"""
GNN多跳推理模块

根据文档第5章：知识图谱构建与推理机制
实现基于图神经网络的多跳推理能力

功能：
1. GCN（图卷积网络）实现
2. GAT（图注意力网络）实现
3. 多跳消息传递
4. 基于GNN的知识图谱推理
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class GraphData:
    """图数据结构"""
    num_nodes: int
    num_edges: int
    node_features: torch.Tensor
    edge_index: torch.Tensor
    edge_type: Optional[torch.Tensor] = None
    node_names: Optional[List[str]] = None


class GCNLayer(nn.Module):
    """
    图卷积网络层 (Graph Convolutional Network Layer)
    
    数学公式：
    H^{(l+1)} = σ(D^{-1/2} A D^{-1/2} H^{(l)} W^{(l)})
    
    其中：
    - A: 邻接矩阵
    - D: 度矩阵
    - H: 节点特征
    - W: 可学习权重
    """
    
    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        """
        初始化GCN层
        
        Args:
            in_features: 输入特征维度
            out_features: 输出特征维度
            bias: 是否使用偏置
        """
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter('bias', None)
        
        self.reset_parameters()
    
    def reset_parameters(self):
        """重置参数"""
        nn.init.xavier_uniform_(self.weight)
        if self.bias is not None:
            nn.init.zeros_(self.bias)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 节点特征 [num_nodes, in_features]
            edge_index: 边索引 [2, num_edges]
        
        Returns:
            更新后的节点特征 [num_nodes, out_features]
        """
        # 线性变换
        support = torch.mm(x, self.weight)
        
        # 计算归一化邻接矩阵
        num_nodes = x.size(0)
        
        # 构建邻接矩阵
        adj = torch.zeros(num_nodes, num_nodes, device=x.device)
        adj[edge_index[0], edge_index[1]] = 1
        
        # 添加自环
        adj = adj + torch.eye(num_nodes, device=x.device)
        
        # 计算度矩阵
        degree = adj.sum(dim=1, keepdim=True)
        degree_inv_sqrt = torch.pow(degree, -0.5)
        degree_inv_sqrt[torch.isinf(degree_inv_sqrt)] = 0
        
        # 归一化
        adj_normalized = degree_inv_sqrt * adj * degree_inv_sqrt.t()
        
        # 消息传递
        output = torch.mm(adj_normalized, support)
        
        if self.bias is not None:
            output = output + self.bias
        
        return output


class GATLayer(nn.Module):
    """
    图注意力网络层 (Graph Attention Network Layer)
    
    使用注意力机制聚合邻居信息：
    α_{ij} = softmax(LeakyReLU(a^T [Wh_i || Wh_j]))
    
    其中：
    - W: 线性变换权重
    - a: 注意力向量
    - ||: 拼接操作
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        num_heads: int = 8,
        concat: bool = True,
        dropout: float = 0.1,
        leaky_relu_slope: float = 0.2
    ):
        """
        初始化GAT层
        
        Args:
            in_features: 输入特征维度
            out_features: 输出特征维度
            num_heads: 注意力头数
            concat: 是否拼接多头输出
            dropout: Dropout概率
            leaky_relu_slope: LeakyReLU斜率
        """
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        self.num_heads = num_heads
        self.concat = concat
        self.dropout = dropout
        
        # 线性变换
        self.W = nn.Parameter(torch.FloatTensor(num_heads, in_features, out_features))
        
        # 注意力参数
        self.a_src = nn.Parameter(torch.FloatTensor(num_heads, out_features, 1))
        self.a_dst = nn.Parameter(torch.FloatTensor(num_heads, out_features, 1))
        
        self.leaky_relu = nn.LeakyReLU(leaky_relu_slope)
        self.dropout_layer = nn.Dropout(dropout)
        
        self.reset_parameters()
    
    def reset_parameters(self):
        """重置参数"""
        nn.init.xavier_uniform_(self.W)
        nn.init.xavier_uniform_(self.a_src)
        nn.init.xavier_uniform_(self.a_dst)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 节点特征 [num_nodes, in_features]
            edge_index: 边索引 [2, num_edges]
        
        Returns:
            更新后的节点特征
        """
        num_nodes = x.size(0)
        
        # 线性变换 [num_heads, num_nodes, out_features]
        h = torch.einsum('ni,hio->hno', x, self.W)
        
        # 计算注意力分数
        attn_src = torch.einsum('hno,hoi->hni', h, self.a_src).squeeze(-1)
        attn_dst = torch.einsum('hno,hoi->hni', h, self.a_dst).squeeze(-1)
        
        # 边的注意力分数
        edge_attn = attn_src[:, edge_index[0]] + attn_dst[:, edge_index[1]]
        edge_attn = self.leaky_relu(edge_attn)
        
        # Softmax归一化（按目标节点）
        edge_attn = self._sparse_softmax(edge_attn, edge_index[1], num_nodes)
        edge_attn = self.dropout_layer(edge_attn)
        
        # 消息传递
        out = self._aggregate(h, edge_index, edge_attn, num_nodes)
        
        # 多头处理
        if self.concat:
            out = out.permute(1, 0, 2).contiguous().view(num_nodes, -1)
        else:
            out = out.mean(dim=0)
        
        return out
    
    def _sparse_softmax(
        self,
        edge_attn: torch.Tensor,
        target_nodes: torch.Tensor,
        num_nodes: int
    ) -> torch.Tensor:
        """稀疏Softmax"""
        # 对每个目标节点的入边进行softmax
        max_attn = torch.zeros(self.num_heads, num_nodes, device=edge_attn.device)
        max_attn.scatter_reduce_(
            1,
            target_nodes.unsqueeze(0).expand(self.num_heads, -1),
            edge_attn,
            reduce='amax',
            include_self=False
        )
        
        edge_attn = edge_attn - max_attn[:, target_nodes]
        edge_attn = torch.exp(edge_attn)
        
        sum_attn = torch.zeros(self.num_heads, num_nodes, device=edge_attn.device)
        sum_attn.scatter_add_(1, target_nodes.unsqueeze(0).expand(self.num_heads, -1), edge_attn)
        
        edge_attn = edge_attn / (sum_attn[:, target_nodes] + 1e-8)
        
        return edge_attn
    
    def _aggregate(
        self,
        h: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attn: torch.Tensor,
        num_nodes: int
    ) -> torch.Tensor:
        """聚合邻居信息"""
        # 加权求和
        src_features = h[:, edge_index[0]]
        weighted_features = src_features * edge_attn.unsqueeze(-1)
        
        out = torch.zeros(self.num_heads, num_nodes, self.out_features, device=h.device)
        out.scatter_add_(
            1,
            edge_index[1].unsqueeze(0).unsqueeze(-1).expand(
                self.num_heads, -1, self.out_features
            ),
            weighted_features
        )
        
        return out


class MultiHopGNN(nn.Module):
    """
    多跳图神经网络
    
    支持多跳推理的知识图谱推理模型
    """
    
    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        embedding_dim: int = 128,
        num_layers: int = 2,
        gnn_type: str = 'gcn',
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        """
        初始化多跳GNN
        
        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            embedding_dim: 嵌入维度
            num_layers: GNN层数
            gnn_type: GNN类型 ('gcn' 或 'gat')
            num_heads: 注意力头数（仅GAT）
            dropout: Dropout概率
        """
        super().__init__()
        
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.gnn_type = gnn_type
        
        # 实体嵌入
        self.entity_embedding = nn.Embedding(num_entities, embedding_dim)
        
        # 关系嵌入
        self.relation_embedding = nn.Embedding(num_relations, embedding_dim)
        
        # GNN层
        self.gnn_layers = nn.ModuleList()
        for i in range(num_layers):
            if gnn_type == 'gcn':
                self.gnn_layers.append(GCNLayer(embedding_dim, embedding_dim))
            else:  # gat
                self.gnn_layers.append(GATLayer(
                    embedding_dim,
                    embedding_dim // num_heads,
                    num_heads=num_heads,
                    concat=True,
                    dropout=dropout
                ))
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(embedding_dim)
        
        self.reset_parameters()
    
    def reset_parameters(self):
        """重置参数"""
        nn.init.xavier_uniform_(self.entity_embedding.weight)
        nn.init.xavier_uniform_(self.relation_embedding.weight)
    
    def forward(
        self,
        entity_ids: torch.Tensor,
        edge_index: torch.Tensor,
        edge_type: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        Args:
            entity_ids: 实体ID [batch_size]
            edge_index: 边索引 [2, num_edges]
            edge_type: 边类型 [num_edges]
        
        Returns:
            实体嵌入 [batch_size, embedding_dim]
        """
        # 获取所有实体嵌入
        x = self.entity_embedding.weight
        
        # 多层GNN
        for i, gnn_layer in enumerate(self.gnn_layers):
            x = gnn_layer(x, edge_index)
            x = F.relu(x)
            x = self.dropout(x)
            x = self.layer_norm(x)
        
        # 获取目标实体嵌入
        entity_embeds = x[entity_ids]
        
        return entity_embeds
    
    def multi_hop_reasoning(
        self,
        query_entity: int,
        relation: int,
        num_hops: int = 2,
        edge_index: torch.Tensor = None,
        edge_type: torch.Tensor = None
    ) -> torch.Tensor:
        """
        多跳推理
        
        Args:
            query_entity: 查询实体ID
            relation: 关系ID
            num_hops: 跳数
            edge_index: 边索引
            edge_type: 边类型
        
        Returns:
            候选实体得分
        """
        # 获取实体嵌入
        entity_embeds = self.entity_embedding.weight
        
        # 获取关系嵌入
        rel_embed = self.relation_embedding(torch.tensor([relation]))
        
        # 多跳消息传递
        for hop in range(num_hops):
            for gnn_layer in self.gnn_layers:
                entity_embeds = gnn_layer(entity_embeds, edge_index)
                entity_embeds = F.relu(entity_embeds)
        
        # 查询实体嵌入
        query_embed = entity_embeds[query_entity]
        
        # 计算候选实体得分
        # TransE风格：h + r ≈ t
        target_embed = query_embed + rel_embed.squeeze(0)
        
        # 计算与所有实体的相似度
        scores = torch.mm(target_embed.unsqueeze(0), entity_embeds.t()).squeeze(0)
        
        return scores


class KnowledgeGraphReasoner:
    """
    知识图谱推理器
    
    整合GNN进行知识图谱推理
    支持基于环境因素的多跳推理
    """
    
    def __init__(
        self,
        entities: List[str],
        relations: List[str],
        triples: List[Tuple[str, str, str]],
        embedding_dim: int = 128,
        num_layers: int = 2,
        gnn_type: str = 'gcn'
    ):
        """
        初始化推理器
        
        Args:
            entities: 实体列表
            relations: 关系列表
            triples: 三元组列表
            embedding_dim: 嵌入维度
            num_layers: GNN层数
            gnn_type: GNN类型
        """
        self.entities = entities
        self.relations = relations
        self.triples = triples
        
        # 构建索引
        self.entity2id = {e: i for i, e in enumerate(entities)}
        self.id2entity = {i: e for i, e in enumerate(entities)}
        self.relation2id = {r: i for i, r in enumerate(relations)}
        self.id2relation = {i: r for i, r in enumerate(relations)}
        
        # 构建图数据
        self.edge_index, self.edge_type = self._build_graph()
        
        # 构建邻接表用于快速查询
        self.adjacency_list = self._build_adjacency_list()
        
        # 初始化GNN模型
        self.model = MultiHopGNN(
            num_entities=len(entities),
            num_relations=len(relations),
            embedding_dim=embedding_dim,
            num_layers=num_layers,
            gnn_type=gnn_type
        )
    
    def _build_graph(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """构建图数据"""
        src_nodes = []
        dst_nodes = []
        edge_types = []
        
        for h, r, t in self.triples:
            if h in self.entity2id and t in self.entity2id and r in self.relation2id:
                src_nodes.append(self.entity2id[h])
                dst_nodes.append(self.entity2id[t])
                edge_types.append(self.relation2id[r])
        
        edge_index = torch.tensor([src_nodes, dst_nodes], dtype=torch.long)
        edge_type = torch.tensor(edge_types, dtype=torch.long)
        
        return edge_index, edge_type
    
    def _build_adjacency_list(self) -> Dict[str, Dict[str, Set[str]]]:
        """
        构建邻接表用于快速查询
        
        :return: 邻接表 {实体: {关系: {目标实体集合}}}
        """
        adj_list = {}
        
        for h, r, t in self.triples:
            if h not in adj_list:
                adj_list[h] = {}
            if r not in adj_list[h]:
                adj_list[h][r] = set()
            adj_list[h][r].add(t)
        
        return adj_list
    
    def query(
        self,
        entity_name: str,
        relation_name: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        查询推理
        
        Args:
            entity_name: 实体名称
            relation_name: 关系名称
            top_k: 返回top-k结果
        
        Returns:
            候选实体列表 [(实体名, 得分)]
        """
        if entity_name not in self.entity2id:
            return []
        
        if relation_name not in self.relation2id:
            return []
        
        entity_id = self.entity2id[entity_name]
        relation_id = self.relation2id[relation_name]
        
        # 多跳推理
        scores = self.model.multi_hop_reasoning(
            query_entity=entity_id,
            relation=relation_id,
            num_hops=2,
            edge_index=self.edge_index,
            edge_type=self.edge_type
        )
        
        # 获取top-k
        top_scores, top_indices = torch.topk(scores, min(top_k, len(self.entities)))
        
        results = []
        for idx, score in zip(top_indices.tolist(), top_scores.tolist()):
            results.append((self.id2entity[idx], score))
        
        return results
    
    def find_similar_entities(
        self,
        entity_name: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        查找相似实体
        
        Args:
            entity_name: 实体名称
            top_k: 返回top-k结果
        
        Returns:
            相似实体列表
        """
        if entity_name not in self.entity2id:
            return []
        
        entity_id = self.entity2id[entity_name]
        
        # 获取实体嵌入
        entity_ids = torch.tensor([entity_id])
        entity_embeds = self.model(entity_ids, self.edge_index, self.edge_type)
        
        # 计算与所有实体的相似度
        all_embeds = self.model.entity_embedding.weight
        similarities = F.cosine_similarity(entity_embeds.unsqueeze(1), all_embeds.unsqueeze(0))
        
        # 获取top-k（排除自身）
        similarities[entity_id] = -float('inf')
        top_scores, top_indices = torch.topk(similarities.squeeze(0), top_k)
        
        results = []
        for idx, score in zip(top_indices.tolist(), top_scores.tolist()):
            results.append((self.id2entity[idx], score))
        
        return results
    
    def multi_hop_reasoning_with_environment(
        self,
        symptom: str,
        environment_factors: Dict[str, float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于环境因素的多跳推理
        
        根据文档5.3.2多跳推理场景：
        - Hop 1: 从症状推断可能的病害
        - Hop 2: 结合环境因素筛选最可能的病害
        
        :param symptom: 症状描述
        :param environment_factors: 环境因素字典 {因素名: 权重}
        :param top_k: 返回top-k结果
        :return: 推理结果列表
        """
        results = []
        
        # Hop 1: 从症状推断可能的病害
        possible_diseases = self._get_diseases_by_symptom(symptom)
        
        if not possible_diseases:
            return results
        
        # Hop 2: 结合环境因素计算综合得分
        disease_scores = []
        
        for disease in possible_diseases:
            # 基础得分（来自GNN嵌入相似度）
            base_score = self._get_base_score(symptom, disease)
            
            # 环境因素得分
            env_score = self._calculate_environment_score(disease, environment_factors)
            
            # 综合得分
            total_score = base_score * 0.4 + env_score * 0.6
            
            # 获取病害的环境偏好
            env_preferences = self._get_disease_environment_preferences(disease)
            
            disease_scores.append({
                "disease": disease,
                "score": total_score,
                "base_score": base_score,
                "environment_score": env_score,
                "environment_preferences": env_preferences,
                "reasoning_path": self._build_reasoning_path(symptom, disease, environment_factors)
            })
        
        # 按得分排序
        disease_scores.sort(key=lambda x: x["score"], reverse=True)
        
        return disease_scores[:top_k]
    
    def _get_diseases_by_symptom(self, symptom: str) -> List[str]:
        """
        根据症状获取可能的病害
        
        :param symptom: 症状描述
        :return: 可能的病害列表
        """
        diseases = set()
        
        # 遍历邻接表查找相关病害
        for entity, relations in self.adjacency_list.items():
            # 检查是否是症状实体
            if "HAS_SYMPTOM" in relations:
                symptoms = relations["HAS_SYMPTOM"]
                for s in symptoms:
                    if symptom.lower() in s.lower() or s.lower() in symptom.lower():
                        diseases.add(entity)
            
            # 反向检查：病害-症状关系
            if symptom in self.adjacency_list:
                if "MANIFESTS_AS" in self.adjacency_list.get(symptom, {}):
                    diseases.update(self.adjacency_list[symptom]["MANIFESTS_AS"])
        
        return list(diseases)
    
    def _get_base_score(self, symptom: str, disease: str) -> float:
        """
        计算症状与病害的基础关联得分
        
        :param symptom: 症状
        :param disease: 病害
        :return: 基础得分
        """
        if symptom not in self.entity2id or disease not in self.entity2id:
            return 0.5
        
        symptom_id = self.entity2id[symptom]
        disease_id = self.entity2id[disease]
        
        # 使用GNN嵌入计算相似度
        with torch.no_grad():
            symptom_embed = self.model.entity_embedding.weight[symptom_id]
            disease_embed = self.model.entity_embedding.weight[disease_id]
            
            similarity = F.cosine_similarity(
                symptom_embed.unsqueeze(0),
                disease_embed.unsqueeze(0)
            ).item()
            
            # 归一化到0-1
            score = (similarity + 1) / 2
        
        return score
    
    def _calculate_environment_score(
        self,
        disease: str,
        environment_factors: Dict[str, float]
    ) -> float:
        """
        计算病害与环境因素的匹配得分
        
        :param disease: 病害名称
        :param environment_factors: 环境因素字典
        :return: 环境匹配得分
        """
        if not environment_factors:
            return 0.5
        
        # 获取病害的环境偏好
        preferences = self._get_disease_environment_preferences(disease)
        
        if not preferences:
            return 0.5
        
        # 计算匹配得分
        matched_score = 0.0
        total_weight = 0.0
        
        for factor, weight in environment_factors.items():
            total_weight += abs(weight)
            
            # 检查病害是否偏好此环境因素
            for pref in preferences:
                if factor.lower() in pref.lower() or pref.lower() in factor.lower():
                    matched_score += weight
        
        if total_weight == 0:
            return 0.5
        
        # 归一化得分
        normalized_score = (matched_score / total_weight + 1) / 2
        
        return normalized_score
    
    def _get_disease_environment_preferences(self, disease: str) -> List[str]:
        """
        获取病害的环境偏好
        
        :param disease: 病害名称
        :return: 环境偏好列表
        """
        preferences = []
        
        if disease in self.adjacency_list:
            # 检查OCCURS_IN关系
            if "OCCURS_IN" in self.adjacency_list[disease]:
                preferences.extend(self.adjacency_list[disease]["OCCURS_IN"])
            
            # 检查FAVORED_BY关系
            if "FAVORED_BY" in self.adjacency_list[disease]:
                preferences.extend(self.adjacency_list[disease]["FAVORED_BY"])
        
        return list(set(preferences))
    
    def _build_reasoning_path(
        self,
        symptom: str,
        disease: str,
        environment_factors: Dict[str, float]
    ) -> List[str]:
        """
        构建推理路径说明
        
        :param symptom: 症状
        :param disease: 病害
        :param environment_factors: 环境因素
        :return: 推理路径列表
        """
        path = []
        
        # Hop 1: 症状到病害
        path.append(f"Hop 1: 症状 '{symptom}' 与病害 '{disease}' 相关联")
        
        # Hop 2: 环境因素
        env_prefs = self._get_disease_environment_preferences(disease)
        if env_prefs and environment_factors:
            env_match = []
            for factor in environment_factors:
                for pref in env_prefs:
                    if factor.lower() in pref.lower() or pref.lower() in factor.lower():
                        env_match.append(f"'{disease}'偏好'{pref}'，与当前环境'{factor}'匹配")
            
            if env_match:
                path.append(f"Hop 2: 环境因素分析 - {'; '.join(env_match)}")
        
        return path
    
    def diagnose_with_context(
        self,
        symptom: str,
        environment_context: Dict[str, Any],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        结合上下文的诊断推理
        
        :param symptom: 症状描述
        :param environment_context: 环境上下文（温度、湿度、天气等）
        :param top_k: 返回top-k结果
        :return: 诊断结果字典
        """
        # 提取环境因素权重
        env_factors = self._extract_environment_weights(environment_context)
        
        # 多跳推理
        reasoning_results = self.multi_hop_reasoning_with_environment(
            symptom, env_factors, top_k
        )
        
        # 构建诊断报告
        diagnosis = {
            "symptom": symptom,
            "environment_context": environment_context,
            "possible_diseases": reasoning_results,
            "confidence": reasoning_results[0]["score"] if reasoning_results else 0.0,
            "reasoning_summary": self._generate_reasoning_summary(reasoning_results)
        }
        
        return diagnosis
    
    def _extract_environment_weights(
        self,
        environment_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        从环境上下文提取权重
        
        :param environment_context: 环境上下文
        :return: 环境因素权重字典
        """
        weights = {}
        
        # 温度因素
        temp = environment_context.get("temperature")
        if temp is not None:
            if temp < 15:
                weights["低温"] = 1.0
            elif temp > 25:
                weights["高温"] = 1.0
        
        # 湿度因素
        humidity = environment_context.get("humidity")
        if humidity is not None:
            if humidity > 80:
                weights["高湿"] = 1.0
            elif humidity < 40:
                weights["干旱"] = 0.5
        
        # 天气因素
        weather = environment_context.get("weather", "").lower()
        if "雨" in weather or "阴" in weather:
            weights["连阴雨"] = 1.0
        if "晴" in weather:
            weights["晴朗"] = 0.5
        
        # 直接指定的因素
        if "factors" in environment_context:
            for factor, weight in environment_context["factors"].items():
                weights[factor] = weight
        
        return weights
    
    def _generate_reasoning_summary(
        self,
        reasoning_results: List[Dict[str, Any]]
    ) -> str:
        """
        生成推理摘要
        
        :param reasoning_results: 推理结果列表
        :return: 摘要文本
        """
        if not reasoning_results:
            return "无法确定诊断结果，请提供更多信息。"
        
        top_result = reasoning_results[0]
        disease = top_result["disease"]
        score = top_result["score"]
        
        summary_parts = [f"根据症状分析和环境因素推理，最可能的诊断是【{disease}】，置信度{score:.1%}。"]
        
        if top_result.get("reasoning_path"):
            summary_parts.append("推理路径：")
            for step in top_result["reasoning_path"]:
                summary_parts.append(f"  - {step}")
        
        if len(reasoning_results) > 1:
            other_diseases = [r["disease"] for r in reasoning_results[1:]]
            summary_parts.append(f"其他可能的病害：{', '.join(other_diseases)}。")
        
        return "\n".join(summary_parts)


def demo_gnn_reasoning():
    """演示GNN推理"""
    print("=" * 70)
    print("📊 GNN多跳推理演示")
    print("=" * 70)
    
    # 示例知识图谱
    entities = [
        "条锈病", "叶锈病", "白粉病", "赤霉病",
        "条形柄锈菌", "禾谷镰刀菌", "禾本科布氏白粉菌",
        "三唑酮", "戊唑醇", "多菌灵",
        "高湿", "低温", "连阴雨"
    ]
    
    relations = [
        "HAS_PATHOGEN", "TREATED_BY", "OCCURS_IN",
        "CAUSES", "MANIFESTS_AS"
    ]
    
    triples = [
        ("条锈病", "HAS_PATHOGEN", "条形柄锈菌"),
        ("赤霉病", "HAS_PATHOGEN", "禾谷镰刀菌"),
        ("白粉病", "HAS_PATHOGEN", "禾本科布氏白粉菌"),
        ("条锈病", "TREATED_BY", "三唑酮"),
        ("条锈病", "TREATED_BY", "戊唑醇"),
        ("赤霉病", "TREATED_BY", "多菌灵"),
        ("赤霉病", "TREATED_BY", "戊唑醇"),
        ("条锈病", "OCCURS_IN", "高湿"),
        ("条锈病", "OCCURS_IN", "低温"),
        ("赤霉病", "OCCURS_IN", "连阴雨"),
        ("条形柄锈菌", "CAUSES", "条锈病"),
        ("禾谷镰刀菌", "CAUSES", "赤霉病"),
    ]
    
    # 创建推理器
    reasoner = KnowledgeGraphReasoner(
        entities=entities,
        relations=relations,
        triples=triples,
        embedding_dim=64,
        num_layers=2,
        gnn_type='gcn'
    )
    
    print(f"\n📊 知识图谱统计:")
    print(f"   实体数: {len(entities)}")
    print(f"   关系数: {len(relations)}")
    print(f"   三元组数: {len(triples)}")
    
    # 多跳推理示例
    print("\n🔍 多跳推理示例:")
    
    # 查询：条锈病应该用什么药治疗？
    results = reasoner.query("条锈病", "TREATED_BY", top_k=3)
    print(f"\n查询: 条锈病 --[TREATED_BY]--> ?")
    for entity, score in results:
        print(f"   候选: {entity} (得分: {score:.4f})")
    
    # 查询：赤霉病的病原菌是什么？
    results = reasoner.query("赤霉病", "HAS_PATHOGEN", top_k=3)
    print(f"\n查询: 赤霉病 --[HAS_PATHOGEN]--> ?")
    for entity, score in results:
        print(f"   候选: {entity} (得分: {score:.4f})")
    
    # 查找相似实体
    print("\n🔍 相似实体查询:")
    similar = reasoner.find_similar_entities("条锈病", top_k=3)
    print(f"\n与'条锈病'相似的实体:")
    for entity, score in similar:
        print(f"   {entity} (相似度: {score:.4f})")
    
    print("\n" + "=" * 70)
    print("✅ GNN多跳推理演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_gnn_reasoning()
