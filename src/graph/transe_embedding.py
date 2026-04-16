# -*- coding: utf-8 -*-
"""
TransE知识图谱嵌入模块

基于文档第5.3节：知识图谱嵌入与推理
TransE (Translating Embeddings) 是一种经典的知识图谱嵌入方法

核心思想：h + r ≈ t
- 头实体嵌入 + 关系嵌入 ≈ 尾实体嵌入

作者: IWDDA团队
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import random


@dataclass
class Triple:
    """知识三元组数据结构"""
    head: str
    relation: str
    tail: str
    
    def __iter__(self):
        return iter([self.head, self.relation, self.tail])


class TransE(nn.Module):
    """
    TransE知识图谱嵌入模型
    
    参考文档5.3节：
    TransE将实体和关系映射到低维向量空间，
    通过平移操作建模关系：h + r ≈ t
    
    损失函数：
    L = Σ max(0, d(h+r, t) - d(h'+r, t') + γ)
    
    其中：
    - d(·,·): 距离函数（L1或L2）
    - γ: 边界超参数
    - (h', r, t'): 负采样三元组
    
    优势：
    1. 计算效率高
    2. 适合一对一关系建模
    3. 可解释性强
    """
    
    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        embedding_dim: int = 128,
        margin: float = 1.0,
        norm: str = 'l2',
        normalize: bool = True
    ):
        """
        初始化TransE模型
        
        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            embedding_dim: 嵌入维度
            margin: 边界超参数γ
            norm: 距离度量，'l1'或'l2'
            normalize: 是否对嵌入进行归一化
        """
        super().__init__()
        
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        self.margin = margin
        self.norm_order = 1 if norm == 'l1' else 2
        self.normalize = normalize
        
        # 实体嵌入矩阵 [num_entities, embedding_dim]
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        
        # 关系嵌入矩阵 [num_relations, embedding_dim]
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
        
        # 初始化参数
        self._init_embeddings()
    
    def _init_embeddings(self):
        """初始化嵌入参数"""
        # 使用Xavier均匀初始化
        bound = 6.0 / np.sqrt(self.embedding_dim)
        
        nn.init.uniform_(self.entity_embeddings.weight, -bound, bound)
        nn.init.uniform_(self.relation_embeddings.weight, -bound, bound)
        
        # 归一化
        if self.normalize:
            with torch.no_grad():
                self.entity_embeddings.weight.data = F.normalize(
                    self.entity_embeddings.weight.data, p=2, dim=1
                )
                self.relation_embeddings.weight.data = F.normalize(
                    self.relation_embeddings.weight.data, p=2, dim=1
                )
    
    def forward(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor
    ) -> torch.Tensor:
        """
        计算三元组得分
        
        Args:
            heads: 头实体索引 [batch_size]
            relations: 关系索引 [batch_size]
            tails: 尾实体索引 [batch_size]
        
        Returns:
            三元组得分 [batch_size]，得分越低表示越可能正确
        """
        # 获取嵌入
        h_embed = self.entity_embeddings(heads)  # [batch, dim]
        r_embed = self.relation_embeddings(relations)  # [batch, dim]
        t_embed = self.entity_embeddings(tails)  # [batch, dim]
        
        # 计算距离: ||h + r - t||
        score = torch.norm(h_embed + r_embed - t_embed, p=self.norm_order, dim=1)
        
        return score
    
    def compute_loss(
        self,
        positive_triples: Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
        negative_triples: Tuple[torch.Tensor, torch.Tensor, torch.Tensor]
    ) -> torch.Tensor:
        """
        计算边界排序损失
        
        Args:
            positive_triples: 正样本三元组 (h, r, t)
            negative_triples: 负样本三元组 (h', r, t')
        
        Returns:
            损失值
        """
        pos_heads, pos_relations, pos_tails = positive_triples
        neg_heads, neg_relations, neg_tails = negative_triples
        
        # 计算正样本得分
        pos_scores = self.forward(pos_heads, pos_relations, pos_tails)
        
        # 计算负样本得分
        neg_scores = self.forward(neg_heads, neg_relations, neg_tails)
        
        # 边界排序损失: max(0, pos_score - neg_score + margin)
        loss = F.relu(pos_scores - neg_scores + self.margin)
        
        return loss.mean()
    
    def predict_tail(
        self,
        head: Union[int, str],
        relation: Union[int, str],
        entity2id: Optional[Dict[str, int]] = None,
        relation2id: Optional[Dict[str, int]] = None,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        预测尾实体
        
        给定头实体和关系，预测最可能的尾实体
        
        Args:
            head: 头实体索引或名称
            relation: 关系索引或名称
            entity2id: 实体名称到ID的映射
            relation2id: 关系名称到ID的映射
            top_k: 返回top-k结果
        
        Returns:
            候选尾实体列表 [(实体ID, 得分)]
        """
        self.eval()
        
        with torch.no_grad():
            # 转换ID
            if isinstance(head, str):
                head = entity2id.get(head, -1)
            if isinstance(relation, str):
                relation = relation2id.get(relation, -1)
            
            if head < 0 or relation < 0:
                return []
            
            # 获取嵌入
            h_embed = self.entity_embeddings(torch.tensor([head]))
            r_embed = self.relation_embeddings(torch.tensor([relation]))
            
            # 计算目标向量: h + r
            target = h_embed + r_embed
            
            # 计算与所有实体的距离
            all_entity_embeds = self.entity_embeddings.weight
            distances = torch.norm(
                target.unsqueeze(1) - all_entity_embeds.unsqueeze(0),
                p=self.norm_order,
                dim=2
            ).squeeze(0)
            
            # 排序获取top-k（距离越小越好）
            top_scores, top_indices = torch.topk(distances, k=top_k, largest=False)
            
            results = []
            for idx, score in zip(top_indices.tolist(), top_scores.tolist()):
                results.append((idx, score))
            
            return results
    
    def predict_head(
        self,
        relation: Union[int, str],
        tail: Union[int, str],
        entity2id: Optional[Dict[str, int]] = None,
        relation2id: Optional[Dict[str, int]] = None,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        预测头实体
        
        给定关系和尾实体，预测最可能的头实体
        
        Args:
            relation: 关系索引或名称
            tail: 尾实体索引或名称
            entity2id: 实体名称到ID的映射
            relation2id: 关系名称到ID的映射
            top_k: 返回top-k结果
        
        Returns:
            候选头实体列表 [(实体ID, 得分)]
        """
        self.eval()
        
        with torch.no_grad():
            # 转换ID
            if isinstance(tail, str):
                tail = entity2id.get(tail, -1)
            if isinstance(relation, str):
                relation = relation2id.get(relation, -1)
            
            if tail < 0 or relation < 0:
                return []
            
            # 获取嵌入
            r_embed = self.relation_embeddings(torch.tensor([relation]))
            t_embed = self.entity_embeddings(torch.tensor([tail]))
            
            # 计算目标向量: t - r
            target = t_embed - r_embed
            
            # 计算与所有实体的距离
            all_entity_embeds = self.entity_embeddings.weight
            distances = torch.norm(
                target.unsqueeze(1) - all_entity_embeds.unsqueeze(0),
                p=self.norm_order,
                dim=2
            ).squeeze(0)
            
            # 排序获取top-k
            top_scores, top_indices = torch.topk(distances, k=top_k, largest=False)
            
            results = []
            for idx, score in zip(top_indices.tolist(), top_scores.tolist()):
                results.append((idx, score))
            
            return results
    
    def get_entity_embedding(self, entity_id: int) -> torch.Tensor:
        """
        获取实体嵌入向量
        
        Args:
            entity_id: 实体ID
        
        Returns:
            实体嵌入向量 [embedding_dim]
        """
        return self.entity_embeddings(torch.tensor([entity_id])).squeeze(0)
    
    def get_relation_embedding(self, relation_id: int) -> torch.Tensor:
        """
        获取关系嵌入向量
        
        Args:
            relation_id: 关系ID
        
        Returns:
            关系嵌入向量 [embedding_dim]
        """
        return self.relation_embeddings(torch.tensor([relation_id])).squeeze(0)


class TransETrainer:
    """
    TransE模型训练器
    
    实现负采样和训练循环
    """
    
    def __init__(
        self,
        model: TransE,
        learning_rate: float = 0.001,
        weight_decay: float = 0.0001,
        num_negatives: int = 10
    ):
        """
        初始化训练器
        
        Args:
            model: TransE模型
            learning_rate: 学习率
            weight_decay: 权重衰减
            num_negatives: 每个正样本对应的负样本数
        """
        self.model = model
        self.num_negatives = num_negatives
        
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
    
    def generate_negative_samples(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        生成负样本
        
        随机替换头实体或尾实体
        
        Args:
            heads: 正样本头实体
            relations: 正样本关系
            tails: 正样本尾实体
        
        Returns:
            负样本三元组
        """
        batch_size = heads.size(0)
        
        # 复制正样本
        neg_heads = heads.clone()
        neg_relations = relations.clone()
        neg_tails = tails.clone()
        
        # 随机选择替换头实体还是尾实体
        mask = torch.rand(batch_size) < 0.5
        
        # 替换头实体
        num_to_replace_head = mask.sum().item()
        if num_to_replace_head > 0:
            random_heads = torch.randint(
                0, self.model.num_entities, (num_to_replace_head,)
            )
            neg_heads[mask] = random_heads
        
        # 替换尾实体
        num_to_replace_tail = (~mask).sum().item()
        if num_to_replace_tail > 0:
            random_tails = torch.randint(
                0, self.model.num_entities, (num_to_replace_tail,)
            )
            neg_tails[~mask] = random_tails
        
        return neg_heads, neg_relations, neg_tails
    
    def train_step(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor
    ) -> float:
        """
        单步训练
        
        Args:
            heads: 头实体索引
            relations: 关系索引
            tails: 尾实体索引
        
        Returns:
            损失值
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        # 生成负样本
        neg_heads, neg_relations, neg_tails = self.generate_negative_samples(
            heads, relations, tails
        )
        
        # 计算损失
        loss = self.model.compute_loss(
            (heads, relations, tails),
            (neg_heads, neg_relations, neg_tails)
        )
        
        # 反向传播
        loss.backward()
        self.optimizer.step()
        
        # 归一化嵌入
        if self.model.normalize:
            with torch.no_grad():
                self.model.entity_embeddings.weight.data = F.normalize(
                    self.model.entity_embeddings.weight.data, p=2, dim=1
                )
        
        return loss.item()


class TransR(nn.Module):
    """
    TransR知识图谱嵌入模型
    
    TransR在TransE基础上引入关系特定的投影空间
    
    参考文档5.3节扩展：
    TransR通过关系投影矩阵，将实体映射到关系特定的空间
    
    公式：h_r = h * M_r, t_r = t * M_r
    得分：||h_r + r - t_r||
    """
    
    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        entity_dim: int = 128,
        relation_dim: int = 64,
        margin: float = 1.0,
        norm: str = 'l2'
    ):
        """
        初始化TransR模型
        
        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            entity_dim: 实体嵌入维度
            relation_dim: 关系嵌入维度
            margin: 边界超参数
            norm: 距离度量
        """
        super().__init__()
        
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.entity_dim = entity_dim
        self.relation_dim = relation_dim
        self.margin = margin
        self.norm_order = 1 if norm == 'l1' else 2
        
        # 实体嵌入
        self.entity_embeddings = nn.Embedding(num_entities, entity_dim)
        
        # 关系嵌入
        self.relation_embeddings = nn.Embedding(num_relations, relation_dim)
        
        # 关系投影矩阵 [num_relations, entity_dim, relation_dim]
        self.projection_matrices = nn.Parameter(
            torch.FloatTensor(num_relations, entity_dim, relation_dim)
        )
        
        self._init_embeddings()
    
    def _init_embeddings(self):
        """初始化嵌入参数"""
        nn.init.xavier_uniform_(self.entity_embeddings.weight)
        nn.init.xavier_uniform_(self.relation_embeddings.weight)
        nn.init.xavier_uniform_(self.projection_matrices)
    
    def _project(
        self,
        entity_embed: torch.Tensor,
        relation_id: torch.Tensor
    ) -> torch.Tensor:
        """
        将实体投影到关系空间
        
        Args:
            entity_embed: 实体嵌入 [batch, entity_dim]
            relation_id: 关系ID [batch]
        
        Returns:
            投影后的实体嵌入 [batch, relation_dim]
        """
        # 获取投影矩阵 [batch, entity_dim, relation_dim]
        proj_matrix = self.projection_matrices[relation_id]
        
        # 投影: [batch, entity_dim] @ [batch, entity_dim, relation_dim]
        projected = torch.bmm(entity_embed.unsqueeze(1), proj_matrix).squeeze(1)
        
        return projected
    
    def forward(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor
    ) -> torch.Tensor:
        """
        计算三元组得分
        
        Args:
            heads: 头实体索引
            relations: 关系索引
            tails: 尾实体索引
        
        Returns:
            三元组得分
        """
        # 获取嵌入
        h_embed = self.entity_embeddings(heads)
        r_embed = self.relation_embeddings(relations)
        t_embed = self.entity_embeddings(tails)
        
        # 投影到关系空间
        h_proj = self._project(h_embed, relations)
        t_proj = self._project(t_embed, relations)
        
        # 计算距离
        score = torch.norm(h_proj + r_embed - t_proj, p=self.norm_order, dim=1)
        
        return score
    
    def compute_loss(
        self,
        positive_triples: Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
        negative_triples: Tuple[torch.Tensor, torch.Tensor, torch.Tensor]
    ) -> torch.Tensor:
        """计算边界排序损失"""
        pos_scores = self.forward(*positive_triples)
        neg_scores = self.forward(*negative_triples)
        loss = F.relu(pos_scores - neg_scores + self.margin)
        return loss.mean()


class TransD(nn.Module):
    """
    TransD知识图谱嵌入模型
    
    TransD为每个实体和关系学习两个向量：嵌入向量和投影向量
    
    参考文档5.3节扩展：
    TransD动态构建投影矩阵，更加灵活
    
    公式：
    M_rh = r_p * h_p^T + I
    M_rt = r_p * t_p^T + I
    """
    
    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        embedding_dim: int = 128,
        margin: float = 1.0,
        norm: str = 'l2'
    ):
        """
        初始化TransD模型
        
        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            embedding_dim: 嵌入维度
            margin: 边界超参数
            norm: 距离度量
        """
        super().__init__()
        
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        self.margin = margin
        self.norm_order = 1 if norm == 'l1' else 2
        
        # 实体嵌入和投影向量
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        self.entity_projections = nn.Embedding(num_entities, embedding_dim)
        
        # 关系嵌入和投影向量
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
        self.relation_projections = nn.Embedding(num_relations, embedding_dim)
        
        self._init_embeddings()
    
    def _init_embeddings(self):
        """初始化嵌入参数"""
        nn.init.xavier_uniform_(self.entity_embeddings.weight)
        nn.init.xavier_uniform_(self.entity_projections.weight)
        nn.init.xavier_uniform_(self.relation_embeddings.weight)
        nn.init.xavier_uniform_(self.relation_projections.weight)
    
    def _project(
        self,
        entity_embed: torch.Tensor,
        entity_proj: torch.Tensor,
        relation_proj: torch.Tensor
    ) -> torch.Tensor:
        """
        动态投影
        
        Args:
            entity_embed: 实体嵌入 [batch, dim]
            entity_proj: 实体投影向量 [batch, dim]
            relation_proj: 关系投影向量 [batch, dim]
        
        Returns:
            投影后的嵌入 [batch, dim]
        """
        # M = r_p * e_p^T + I
        # projected = M * e = r_p * (e_p^T * e) + e
        
        # e_p^T * e: [batch, 1, dim] @ [batch, dim, 1] -> [batch, 1, 1]
        inner_product = torch.bmm(
            entity_proj.unsqueeze(1),
            entity_embed.unsqueeze(2)
        ).squeeze(-1)
        
        # r_p * inner_product + e
        projected = relation_proj * inner_product + entity_embed
        
        return projected
    
    def forward(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor
    ) -> torch.Tensor:
        """计算三元组得分"""
        # 获取嵌入
        h_embed = self.entity_embeddings(heads)
        h_proj = self.entity_projections(heads)
        r_embed = self.relation_embeddings(relations)
        r_proj = self.relation_projections(relations)
        t_embed = self.entity_embeddings(tails)
        t_proj = self.entity_projections(tails)
        
        # 投影
        h_projected = self._project(h_embed, h_proj, r_proj)
        t_projected = self._project(t_embed, t_proj, r_proj)
        
        # 计算距离
        score = torch.norm(h_projected + r_embed - t_projected, p=self.norm_order, dim=1)
        
        return score
    
    def compute_loss(
        self,
        positive_triples: Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
        negative_triples: Tuple[torch.Tensor, torch.Tensor, torch.Tensor]
    ) -> torch.Tensor:
        """计算边界排序损失"""
        pos_scores = self.forward(*positive_triples)
        neg_scores = self.forward(*negative_triples)
        loss = F.relu(pos_scores - neg_scores + self.margin)
        return loss.mean()


class KnowledgeGraphEmbedding:
    """
    知识图谱嵌入管理器
    
    整合TransE/TransR/TransD模型，提供统一接口
    """
    
    def __init__(
        self,
        entities: List[str],
        relations: List[str],
        triples: List[Tuple[str, str, str]],
        model_type: str = 'transe',
        embedding_dim: int = 128,
        margin: float = 1.0
    ):
        """
        初始化知识图谱嵌入管理器
        
        Args:
            entities: 实体列表
            relations: 关系列表
            triples: 三元组列表
            model_type: 模型类型 ('transe', 'transr', 'transd')
            embedding_dim: 嵌入维度
            margin: 边界超参数
        """
        self.entities = entities
        self.relations = relations
        self.triples = triples
        
        # 构建索引
        self.entity2id = {e: i for i, e in enumerate(entities)}
        self.id2entity = {i: e for i, e in enumerate(entities)}
        self.relation2id = {r: i for i, r in enumerate(relations)}
        self.id2relation = {i: r for i, r in enumerate(relations)}
        
        # 转换三元组为ID
        self.triple_ids = self._convert_triples_to_ids(triples)
        
        # 创建模型
        self.model_type = model_type
        self.model = self._create_model(model_type, embedding_dim, margin)
        
        # 创建训练器
        if model_type == 'transe':
            self.trainer = TransETrainer(self.model)
        else:
            self.trainer = None
    
    def _convert_triples_to_ids(
        self,
        triples: List[Tuple[str, str, str]]
    ) -> List[Tuple[int, int, int]]:
        """将三元组转换为ID"""
        triple_ids = []
        for h, r, t in triples:
            if h in self.entity2id and r in self.relation2id and t in self.entity2id:
                triple_ids.append((
                    self.entity2id[h],
                    self.relation2id[r],
                    self.entity2id[t]
                ))
        return triple_ids
    
    def _create_model(
        self,
        model_type: str,
        embedding_dim: int,
        margin: float
    ) -> nn.Module:
        """创建嵌入模型"""
        num_entities = len(self.entities)
        num_relations = len(self.relations)
        
        if model_type == 'transe':
            return TransE(
                num_entities=num_entities,
                num_relations=num_relations,
                embedding_dim=embedding_dim,
                margin=margin
            )
        elif model_type == 'transr':
            return TransR(
                num_entities=num_entities,
                num_relations=num_relations,
                entity_dim=embedding_dim,
                relation_dim=embedding_dim // 2,
                margin=margin
            )
        elif model_type == 'transd':
            return TransD(
                num_entities=num_entities,
                num_relations=num_relations,
                embedding_dim=embedding_dim,
                margin=margin
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def train(
        self,
        num_epochs: int = 100,
        batch_size: int = 256,
        verbose: bool = True
    ):
        """
        训练嵌入模型
        
        Args:
            num_epochs: 训练轮数
            batch_size: 批次大小
            verbose: 是否打印训练信息
        """
        if self.trainer is None:
            raise NotImplementedError(f"{self.model_type}暂不支持自动训练")
        
        # 准备数据
        all_heads = torch.tensor([t[0] for t in self.triple_ids])
        all_relations = torch.tensor([t[1] for t in self.triple_ids])
        all_tails = torch.tensor([t[2] for t in self.triple_ids])
        
        num_triples = len(self.triple_ids)
        
        for epoch in range(num_epochs):
            # 打乱数据
            perm = torch.randperm(num_triples)
            all_heads = all_heads[perm]
            all_relations = all_relations[perm]
            all_tails = all_tails[perm]
            
            total_loss = 0
            num_batches = 0
            
            for i in range(0, num_triples, batch_size):
                batch_heads = all_heads[i:i+batch_size]
                batch_relations = all_relations[i:i+batch_size]
                batch_tails = all_tails[i:i+batch_size]
                
                loss = self.trainer.train_step(
                    batch_heads, batch_relations, batch_tails
                )
                total_loss += loss
                num_batches += 1
            
            if verbose and (epoch + 1) % 10 == 0:
                avg_loss = total_loss / num_batches
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
    
    def predict_tail(
        self,
        head: str,
        relation: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        预测尾实体
        
        Args:
            head: 头实体名称
            relation: 关系名称
            top_k: 返回top-k结果
        
        Returns:
            候选尾实体列表 [(实体名, 得分)]
        """
        if head not in self.entity2id or relation not in self.relation2id:
            return []
        
        results = self.model.predict_tail(
            head, relation,
            entity2id=self.entity2id,
            relation2id=self.relation2id,
            top_k=top_k
        )
        
        return [(self.id2entity[eid], score) for eid, score in results]
    
    def predict_head(
        self,
        relation: str,
        tail: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        预测头实体
        
        Args:
            relation: 关系名称
            tail: 尾实体名称
            top_k: 返回top-k结果
        
        Returns:
            候选头实体列表 [(实体名, 得分)]
        """
        if tail not in self.entity2id or relation not in self.relation2id:
            return []
        
        results = self.model.predict_head(
            relation, tail,
            entity2id=self.entity2id,
            relation2id=self.relation2id,
            top_k=top_k
        )
        
        return [(self.id2entity[eid], score) for eid, score in results]
    
    def get_entity_embedding(self, entity: str) -> Optional[torch.Tensor]:
        """
        获取实体嵌入
        
        Args:
            entity: 实体名称
        
        Returns:
            实体嵌入向量
        """
        if entity not in self.entity2id:
            return None
        
        return self.model.get_entity_embedding(self.entity2id[entity])
    
    def find_similar_entities(
        self,
        entity: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        查找相似实体
        
        Args:
            entity: 实体名称
            top_k: 返回top-k结果
        
        Returns:
            相似实体列表
        """
        if entity not in self.entity2id:
            return []
        
        entity_embed = self.get_entity_embedding(entity)
        if entity_embed is None:
            return []
        
        # 计算与所有实体的余弦相似度
        all_embeds = self.model.entity_embeddings.weight
        similarities = F.cosine_similarity(
            entity_embed.unsqueeze(0),
            all_embeds
        )
        
        # 排除自身
        similarities[self.entity2id[entity]] = -float('inf')
        
        # 获取top-k
        top_scores, top_indices = torch.topk(similarities, top_k)
        
        return [
            (self.id2entity[idx.item()], score.item())
            for idx, score in zip(top_indices, top_scores)
        ]


def demo_transe():
    """演示TransE模型"""
    print("=" * 70)
    print("📊 TransE知识图谱嵌入演示")
    print("=" * 70)
    
    # 小麦病害知识图谱
    entities = [
        "条锈病", "叶锈病", "白粉病", "赤霉病", "纹枯病",
        "条形柄锈菌", "小麦隐匿柄锈菌", "禾本科布氏白粉菌", "禾谷镰刀菌",
        "三唑酮", "戊唑醇", "多菌灵", "丙环唑",
        "高湿", "低温", "连阴雨", "温暖潮湿",
        "叶片", "穗部", "茎秆"
    ]
    
    relations = [
        "HAS_PATHOGEN",      # 病原菌
        "TREATED_BY",        # 治疗药物
        "OCCURS_IN",         # 发生环境
        "AFFECTS",           # 影响部位
        "CAUSES"             # 导致
    ]
    
    triples = [
        ("条锈病", "HAS_PATHOGEN", "条形柄锈菌"),
        ("叶锈病", "HAS_PATHOGEN", "小麦隐匿柄锈菌"),
        ("白粉病", "HAS_PATHOGEN", "禾本科布氏白粉菌"),
        ("赤霉病", "HAS_PATHOGEN", "禾谷镰刀菌"),
        ("条锈病", "TREATED_BY", "三唑酮"),
        ("条锈病", "TREATED_BY", "戊唑醇"),
        ("叶锈病", "TREATED_BY", "三唑酮"),
        ("白粉病", "TREATED_BY", "三唑酮"),
        ("赤霉病", "TREATED_BY", "多菌灵"),
        ("纹枯病", "TREATED_BY", "丙环唑"),
        ("条锈病", "OCCURS_IN", "高湿"),
        ("条锈病", "OCCURS_IN", "低温"),
        ("赤霉病", "OCCURS_IN", "连阴雨"),
        ("赤霉病", "OCCURS_IN", "温暖潮湿"),
        ("条锈病", "AFFECTS", "叶片"),
        ("赤霉病", "AFFECTS", "穗部"),
        ("纹枯病", "AFFECTS", "茎秆"),
        ("条形柄锈菌", "CAUSES", "条锈病"),
        ("禾谷镰刀菌", "CAUSES", "赤霉病"),
    ]
    
    # 创建知识图谱嵌入
    kge = KnowledgeGraphEmbedding(
        entities=entities,
        relations=relations,
        triples=triples,
        model_type='transe',
        embedding_dim=64,
        margin=1.0
    )
    
    print(f"\n📊 知识图谱统计:")
    print(f"   实体数: {len(entities)}")
    print(f"   关系数: {len(relations)}")
    print(f"   三元组数: {len(triples)}")
    
    # 训练模型
    print("\n🔧 训练TransE模型...")
    kge.train(num_epochs=50, batch_size=32, verbose=True)
    
    # 预测尾实体
    print("\n🔍 尾实体预测:")
    results = kge.predict_tail("条锈病", "TREATED_BY", top_k=3)
    print(f"\n查询: 条锈病 --[TREATED_BY]--> ?")
    for entity, score in results:
        print(f"   候选: {entity} (得分: {score:.4f})")
    
    # 预测头实体
    print("\n🔍 头实体预测:")
    results = kge.predict_head("HAS_PATHOGEN", "禾谷镰刀菌", top_k=3)
    print(f"\n查询: ? --[HAS_PATHOGEN]--> 禾谷镰刀菌")
    for entity, score in results:
        print(f"   候选: {entity} (得分: {score:.4f})")
    
    # 查找相似实体
    print("\n🔍 相似实体查询:")
    similar = kge.find_similar_entities("条锈病", top_k=5)
    print(f"\n与'条锈病'相似的实体:")
    for entity, score in similar:
        print(f"   {entity} (相似度: {score:.4f})")
    
    print("\n" + "=" * 70)
    print("✅ TransE演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_transe()
