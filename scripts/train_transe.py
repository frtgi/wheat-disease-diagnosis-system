# -*- coding: utf-8 -*-
"""
TransE图嵌入训练脚本

训练知识图谱的TransE嵌入模型，用于：
1. 实体和关系的向量表示
2. 链接预测
3. 相似实体发现
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TransEDataset(Dataset):
    """TransE训练数据集"""
    
    def __init__(self, triples: List[Dict], entity2id: Dict, relation2id: Dict):
        """
        初始化数据集
        
        :param triples: 三元组列表
        :param entity2id: 实体到ID的映射
        :param relation2id: 关系到ID的映射
        """
        self.triples = []
        for t in triples:
            h = entity2id.get(t['head'])
            r = relation2id.get(t['relation'])
            t_tail = entity2id.get(t['tail'])
            if h is not None and r is not None and t_tail is not None:
                self.triples.append((h, r, t_tail))
    
    def __len__(self):
        return len(self.triples)
    
    def __getitem__(self, idx):
        h, r, t = self.triples[idx]
        return torch.tensor(h, dtype=torch.long), \
               torch.tensor(r, dtype=torch.long), \
               torch.tensor(t, dtype=torch.long)


class TransE(nn.Module):
    """TransE模型"""
    
    def __init__(self, num_entities: int, num_relations: int, embedding_dim: int = 100):
        """
        初始化TransE模型
        
        :param num_entities: 实体数量
        :param num_relations: 关系数量
        :param embedding_dim: 嵌入维度
        """
        super().__init__()
        
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
        
        nn.init.xavier_uniform_(self.entity_embeddings.weight)
        nn.init.xavier_uniform_(self.relation_embeddings.weight)
        
        nn.init.normal_(self.entity_embeddings.weight, std=1.0/embedding_dim)
        nn.init.normal_(self.relation_embeddings.weight, std=1.0/embedding_dim)
    
    def forward(self, heads, relations, tails):
        """
        前向传播
        
        :param heads: 头实体索引
        :param relations: 关系索引
        :param tails: 尾实体索引
        :return: 三元组得分
        """
        h_emb = self.entity_embeddings(heads)
        r_emb = self.relation_embeddings(relations)
        t_emb = self.entity_embeddings(tails)
        
        h_emb = torch.nn.functional.normalize(h_emb, p=2, dim=-1)
        t_emb = torch.nn.functional.normalize(t_emb, p=2, dim=-1)
        
        scores = torch.norm(h_emb + r_emb - t_emb, p=2, dim=-1)
        return scores
    
    def get_embeddings(self):
        """获取所有嵌入向量"""
        return {
            'entities': self.entity_embeddings.weight.detach().cpu().numpy(),
            'relations': self.relation_embeddings.weight.detach().cpu().numpy()
        }


class TransETrainer:
    """TransE训练器"""
    
    def __init__(
        self,
        kg_path: str = "checkpoints/knowledge_graph",
        embedding_dim: int = 100,
        learning_rate: float = 0.01,
        batch_size: int = 32,
        epochs: int = 100,
        margin: float = 1.0,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        初始化训练器
        
        :param kg_path: 知识图谱路径
        :param embedding_dim: 嵌入维度
        :param learning_rate: 学习率
        :param batch_size: 批大小
        :param epochs: 训练轮数
        :param margin: margin loss参数
        :param device: 计算设备
        """
        self.kg_path = Path(kg_path)
        self.embedding_dim = embedding_dim
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.margin = margin
        self.device = device
        
        self.entity2id = {}
        self.relation2id = {}
        self.id2entity = {}
        self.id2relation = {}
        self.model = None
        self.optimizer = None
        
        print(f"TransE训练器初始化")
        print(f"  设备: {device}")
        print(f"  嵌入维度: {embedding_dim}")
        print(f"  学习率: {learning_rate}")
        print(f"  批大小: {batch_size}")
        print(f"  训练轮数: {epochs}")
    
    def load_knowledge_graph(self):
        """加载知识图谱"""
        print("\n加载知识图谱...")
        
        entities_file = self.kg_path / "entities.json"
        triples_file = self.kg_path / "triples.json"
        
        if not entities_file.exists() or not triples_file.exists():
            raise FileNotFoundError(f"知识图谱文件不存在: {entities_file} 或 {triples_file}")
        
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        
        with open(triples_file, 'r', encoding='utf-8') as f:
            triples = json.load(f)
        
        for i, (entity_id, entity_data) in enumerate(entities.items()):
            self.entity2id[entity_id] = i
            self.id2entity[i] = entity_id
        
        relations = set()
        for t in triples:
            relations.add(t['relation'])
        
        for i, rel in enumerate(sorted(relations)):
            self.relation2id[rel] = i
            self.id2relation[i] = rel
        
        print(f"  实体数量: {len(self.entity2id)}")
        print(f"  关系数量: {len(self.relation2id)}")
        print(f"  三元组数量: {len(triples)}")
        
        return triples
    
    def build_dataset(self, triples: List[Dict]):
        """构建数据集"""
        print("\n构建数据集...")
        dataset = TransEDataset(triples, self.entity2id, self.relation2id)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        print(f"  训练样本数: {len(dataset)}")
        print(f"  批次数: {len(dataloader)}")
        return dataloader
    
    def build_model(self):
        """构建模型"""
        print("\n构建模型...")
        self.model = TransE(
            num_entities=len(self.entity2id),
            num_relations=len(self.relation2id),
            embedding_dim=self.embedding_dim
        ).to(self.device)
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f"  模型参数量: {total_params:,}")
    
    def generate_negative_samples(self, heads, relations, tails, num_negatives=1):
        """
        生成负样本
        
        :param heads: 头实体
        :param relations: 关系
        :param tails: 尾实体
        :param num_negatives: 负样本数量
        :return: 负样本
        """
        batch_size = heads.size(0)
        neg_heads = heads.clone()
        neg_tails = tails.clone()
        
        for i in range(batch_size):
            if torch.rand(1).item() < 0.5:
                neg_heads[i] = torch.randint(0, len(self.entity2id), (1,)).item()
            else:
                neg_tails[i] = torch.randint(0, len(self.entity2id), (1,)).item()
        
        return neg_heads, neg_tails
    
    def train(self, dataloader):
        """训练模型"""
        print("\n开始训练...")
        print("=" * 60)
        
        best_loss = float('inf')
        
        for epoch in range(self.epochs):
            self.model.train()
            total_loss = 0.0
            start_time = time.time()
            
            for batch in dataloader:
                heads, relations, tails = [x.to(self.device) for x in batch]
                
                neg_heads, neg_tails = self.generate_negative_samples(heads, relations, tails)
                neg_heads = neg_heads.to(self.device)
                neg_tails = neg_tails.to(self.device)
                
                pos_scores = self.model(heads, relations, tails)
                neg_scores = self.model(neg_heads, relations, neg_tails)
                
                loss = torch.clamp(self.margin + pos_scores - neg_scores, min=0).mean()
                
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(dataloader)
            epoch_time = time.time() - start_time
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}] Loss: {avg_loss:.4f} Time: {epoch_time:.2f}s")
            
            if avg_loss < best_loss:
                best_loss = avg_loss
                self.save_model()
        
        print("=" * 60)
        print(f"训练完成! 最佳损失: {best_loss:.4f}")
    
    def save_model(self):
        """保存模型"""
        save_path = self.kg_path / "transe_model.pt"
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'entity2id': self.entity2id,
            'relation2id': self.relation2id,
            'id2entity': self.id2entity,
            'id2relation': self.id2relation,
            'embedding_dim': self.embedding_dim,
            'num_entities': len(self.entity2id),
            'num_relations': len(self.relation2id)
        }, save_path)
        
        print(f"  模型已保存: {save_path}")
    
    def run(self):
        """运行训练流程"""
        print("\n" + "=" * 60)
        print("TransE图嵌入训练")
        print("=" * 60)
        
        triples = self.load_knowledge_graph()
        dataloader = self.build_dataset(triples)
        self.build_model()
        self.train(dataloader)
        
        print("\n训练完成!")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    kg_path = project_root / "checkpoints" / "knowledge_graph"
    
    trainer = TransETrainer(
        kg_path=str(kg_path),
        embedding_dim=100,
        learning_rate=0.01,
        batch_size=32,
        epochs=100,
        margin=1.0
    )
    trainer.run()


if __name__ == "__main__":
    main()
