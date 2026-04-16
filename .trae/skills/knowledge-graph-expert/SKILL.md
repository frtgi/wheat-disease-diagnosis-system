---
name: "knowledge-graph-expert"
description: "Neo4j知识图谱管理专家，用于农业知识图谱的构建、扩展和查询。Invoke when building knowledge graphs, managing entities/relations, or training TransE embeddings."
---

# 知识图谱管理专家

## 角色定位

IWDDA 项目知识图谱专家，负责 AgriKG 农业知识图谱的构建、扩展和推理。

## 核心能力

- **图谱构建**：Neo4j 数据库管理、实体关系定义
- **知识抽取**：从文本中提取实体和关系
- **嵌入训练**：TransE 图嵌入模型训练
- **推理查询**：多跳推理、关联分析

## 项目关键文件

| 文件 | 用途 |
|------|------|
| `src/graph/knowledge_graph_builder.py` | 知识图谱构建器 |
| `src/graph/graphrag_engine.py` | GraphRAG 引擎 |
| `scripts/data/expand_knowledge_graph.py` | 图谱扩展脚本 |
| `scripts/sync_to_neo4j.py` | Neo4j 同步脚本 |
| `checkpoints/knowledge_graph/` | 图谱数据目录 |

## 知识图谱规模

| 指标 | 数值 |
|------|------|
| 实体总数 | 106 |
| 三元组总数 | 178 |
| 关系类型 | 15 |

## 本体结构

### 核心实体类型

| 类型 | 数量 | 示例 |
|------|------|------|
| Disease (病害) | 16 | 条锈病、赤霉病 |
| Symptom (症状) | 21 | 黄色条纹、白色霉层 |
| Pathogen (病原体) | 13 | Puccinia striiformis |
| ControlMeasure (防治措施) | 15 | 三唑酮、戊唑醇 |
| Environment (环境) | 10 | 高湿、低温 |
| Pest (虫害) | 7 | 蚜虫、螨类 |

### 关系类型

| 关系 | 数量 | 说明 |
|------|------|------|
| HAS_SYMPTOM | 21 | 病害-症状 |
| INFECTS | 21 | 病原体-感染 |
| TREATED_BY | 16 | 病害-治疗 |
| CAUSED_BY | 13 | 病害-病原体 |
| FAVORS | 13 | 环境-病害 |
| PREVENTS | 10 | 措施-预防 |

## Neo4j 连接配置

```python
uri = "neo4j://localhost:7687"
user = "neo4j"
password = "123456789s"
```

## 常用操作

### 添加实体与关系

```python
from src.graph.knowledge_graph_builder import AgriKnowledgeGraph

kg = AgriKnowledgeGraph()
kg.add_entity("Disease", {
    "name": "小麦条锈病",
    "english_name": "Stripe Rust",
    "pathogen": "Puccinia striiformis"
})
kg.add_relation("条锈病", "HAS_SYMPTOM", "黄色条状孢子堆")
kg.add_relation("条锈病", "TREATED_BY", "三唑酮")
```

### 多跳推理与检索

```python
from src.graph.graphrag_engine import GraphRAGEngine

engine = GraphRAGEngine()
result = engine.multi_hop_reasoning(
    start_entity="黄化",
    relation_path=["HAS_SYMPTOM", "FAVORED_BY"],
    max_hops=2
)
subgraph = engine.retrieve_subgraph("条锈病", depth=2)
context = engine.construct_context(subgraph)
```

### TransE 嵌入训练

```python
kg.train_transe(embedding_dim=100, epochs=100, learning_rate=0.01)
kg.save("checkpoints/knowledge_graph")
```

### 图谱扩展与同步

```bash
python scripts/data/expand_knowledge_graph.py
python scripts/sync_to_neo4j.py
```

## 注意事项

1. **密码安全**：建议将 Neo4j 密码移至环境变量
2. **服务状态**：确保 Neo4j 服务正在运行
3. **嵌入更新**：扩展图谱后需重新训练 TransE 嵌入
4. **数据备份**：定期备份图谱数据
