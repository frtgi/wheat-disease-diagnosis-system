# 🏗️ IWDDA 系统架构详解

本文档详细阐述 IWDDA（Intelligent Wheat Disease Diagnosis Agent）的系统架构设计、各模块实现原理以及多模态融合机制。

## 📋 目录

- [架构概览](#架构概览)
- [感知层 (Perception Layer)](#感知层-perception-layer)
- [认知层 (Cognition Layer)](#认知层-cognition-layer)
- [行动层 (Action Layer)](#行动层-action-layer)
- [多模态融合机制](#多模态融合机制)
- [数据流与交互](#数据流与交互)
- [性能优化](#性能优化)

---

## 🎯 架构概览

IWDDA 采用"感知-认知-行动"三层架构，实现了从数据输入到智能决策的完整闭环。

```
┌─────────────────────────────────────────────────────────────────┐
│                    IWDDA 系统架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  感知层 (Perception Layer)                        │  │
│  │  ┌─────────────┐  ┌─────────────┐              │  │
│  │  │ VisionAgent │  │LanguageAgent│              │  │
│  │  │  (YOLOv8)  │  │  (BERT)     │              │  │
│  │  └─────────────┘  └─────────────┘              │  │
│  │       ↓ 视觉特征        ↓ 文本嵌入               │  │
│  └───────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  认知层 (Cognition Layer)                       │  │
│  │  ┌─────────────┐  ┌─────────────┐              │  │
│  │  │KnowledgeAgent│  │ FusionAgent │              │  │
│  │  │  (Neo4j)   │  │ (KAD-Fusion)│              │  │
│  │  └─────────────┘  └─────────────┘              │  │
│  │       ↓ 知识检索        ↓ 融合决策               │  │
│  └───────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  行动层 (Action Layer)                           │  │
│  │  ┌─────────────┐  ┌─────────────┐              │  │
│  │  │ActiveLearner │  │EvolutionEngine│             │  │
│  │  │ (反馈收集)   │  │ (增量训练)    │             │  │
│  │  └─────────────┘  └─────────────┘              │  │
│  └───────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│                    诊断报告与防治建议                        │
└─────────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **模块化设计**：各模块职责清晰，松耦合，易于扩展和维护
2. **多模态协同**：视觉、文本、知识三种模态深度融合，互为补充
3. **可解释性**：提供详细的推理过程和置信度评估
4. **自进化能力**：支持增量学习和人机反馈，持续优化

---

## 👁️ 感知层 (Perception Layer)

感知层负责从原始数据中提取特征，包括视觉特征和文本语义特征。

### VisionAgent - 视觉感知引擎

#### 架构设计

```python
class VisionAgent:
    def __init__(self, model_path=None):
        # 自动搜索最新训练模型
        # 支持自定义模型路径
        self.model = YOLO(model_path or 'yolov8n.pt')
    
    def detect(self, image_path, conf_threshold=0.15):
        # 执行目标检测
        # 返回检测结果列表
        results = self.model.predict(...)
        return results
```

#### 核心功能

1. **自动模型加载**
   - 优先使用用户指定的模型路径
   - 自动搜索 `runs/detect/runs/train/wheat_evolution/weights/best.pt`
   - 未找到时使用预训练的 `yolov8n.pt`

2. **实时检测**
   - 支持批量图像处理
   - 可配置置信度阈值
   - 返回边界框、类别、置信度

3. **可视化输出**
   - 自动绘制检测框
   - 显示类别标签和置信度
   - 支持保存标注图像

#### YOLOv8 模型特性

| 特性 | 说明 |
|------|------|
| 骨干网络 | CSPDarknet |
| 检测头 | Anchor-free 解耦头 |
| 损失函数 | CIoU Loss + 分类损失 |
| 输入尺寸 | 512x512 (可配置) |
| 推理速度 | >30 FPS (GPU) |

### LanguageAgent - 文本理解引擎

#### 架构设计

```python
class LanguageAgent:
    def __init__(self, model_name='bert-base-chinese'):
        # 加载预训练的 BERT 模型
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
    
    def get_embedding(self, text):
        # 将文本转换为向量嵌入
        inputs = self.tokenizer(text, ...)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state[:, 0, :]
    
    def compute_similarity(self, text_a, text_b):
        # 计算两段文本的余弦相似度
        vec_a = self.get_embedding(text_a)
        vec_b = self.get_embedding(text_b)
        return F.cosine_similarity(vec_a, vec_b)
```

#### 核心功能

1. **文本嵌入**
   - 使用 BERT-base-chinese 模型
   - 提取 [CLS] token 作为句子级表示
   - 支持 128 token 最大长度

2. **语义相似度计算**
   - 余弦相似度度量
   - 用于症状描述与标准症状库的匹配
   - 阈值过滤（<0.35 视为不匹配）

3. **标准症状库**

```python
standard_symptoms = {
    "蚜虫": "黑色或绿色小虫，分泌蜜露",
    "螨虫": "叶片卷曲发黄，植株矮小",
    "茎蝇": "茎秆有蛀孔，植株枯萎",
    "锈病": "叶片上有黄色或红褐色粉末孢子堆",
    "茎锈病": "茎秆上有红褐色锈斑",
    "叶锈病": "叶片上有红褐色粉末状斑点",
    "条锈病": "叶片上有黄色条纹状锈斑",
    "白粉病": "白色绒毛状霉层",
    "赤霉病": "穗部枯白，粉红色霉层",
    # ... 更多症状
}
```

---

## 🧠 认知层 (Cognition Layer)

认知层负责融合多模态信息，进行知识推理和决策。

### KnowledgeAgent - 知识图谱引擎

#### 架构设计

```python
class KnowledgeAgent:
    def __init__(self, uri="neo4j://localhost:7687", 
                 user="neo4j", password="123456789s"):
        # 连接 Neo4j 图数据库
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._init_knowledge_base()
    
    def get_disease_details(self, disease_name):
        # 获取病害的完整信息
        # 包括：成因、预防措施、治疗药剂
        query = """
        MATCH (d:Disease {name: $name})
        OPTIONAL MATCH (d)-[:CAUSED_BY]->(c:Cause)
        OPTIONAL MATCH (d)-[:PREVENTED_BY]->(p:Prevention)
        OPTIONAL MATCH (d)-[:TREATED_BY]->(t:Treatment)
        RETURN collect(DISTINCT c.name) as causes,
               collect(DISTINCT p.name) as preventions,
               collect(DISTINCT t.name) as treatments
        """
        # 执行查询并返回结果
```

#### 知识图谱本体设计

##### 核心实体节点

| 实体类型 | 属性 | 示例 |
|---------|------|------|
| Disease | name, type | 条锈病, Fungus |
| Symptom | name, description | 黄色条纹, 叶片褪绿 |
| Pathogen | name, latin_name | Puccinia striiformis |
| Environment | name, condition | 高湿环境, 低温寡照 |
| Prevention | name, desc | 抗病选种, 清沟沥水 |
| Treatment | name, usage | 三唑酮, 喷雾 |

##### 语义关系边

| 关系 | 描述 | 示例 |
|------|------|------|
| CAUSED_BY | 病害由...引起 | 条锈病 -CAUSED_BY-> 高湿环境 |
| PREVENTED_BY | 病害可由...预防 | 条锈病 -PREVENTED_BY-> 抗病选种 |
| TREATED_BY | 病害可由...治疗 | 条锈病 -TREATED_BY-> 三唑酮 |
| MANIFESTS_AS | 病害表现为... | 条锈病 -MANIFESTS_AS-> 黄色条纹 |

#### 知识图谱初始化

系统首次启动时自动初始化知识图谱，包括：

1. **16类病害节点**
   - 蚜虫、螨虫、茎蝇（昆虫类）
   - 锈病、茎锈病、叶锈病、条锈病等（真菌类）

2. **环境成因节点**
   - 高湿环境、低温寡照、高温干旱、土壤连作、气流传播

3. **预防措施节点**
   - 抗病选种、轮作倒茬、清沟沥水、清除病残体

4. **治疗药剂节点**
   - 三唑酮/戊唑醇、吡虫啉、氰烯菌酯

5. **建立关联关系**
   - 根据农学知识建立实体间的语义关系

### FusionAgent - 多模态融合引擎

#### 架构设计

```python
class FusionAgent:
    def __init__(self, knowledge_agent):
        self.kg = knowledge_agent
        # 融合权重
        self.WEIGHT_VISION = 0.6
        self.WEIGHT_TEXT = 0.4
    
    def fuse_and_decide(self, vision_result, text_result, user_text):
        # 执行决策级融合
        v_label = vision_result.get('label', '未知')
        v_conf = vision_result.get('conf', 0.0)
        t_label = text_result.get('label', '未知')
        t_conf = text_result.get('conf', 0.0)
        
        # 融合策略
        if v_label == t_label and v_label != "未知":
            # 强一致性
            final_diagnosis = v_label
            final_conf = (v_conf * self.WEIGHT_VISION) + (t_conf * self.WEIGHT_TEXT)
        elif v_conf > 0.8:
            # 视觉主导
            final_diagnosis = v_label
            final_conf = v_conf
        else:
            # 知识图谱仲裁
            final_diagnosis = self._kg_arbitration(v_label, t_label, user_text)
        
        # GraphRAG: 检索增强生成
        treatment_advice = self.kg.get_treatment_info(final_diagnosis)
        
        return {
            "diagnosis": final_diagnosis,
            "confidence": final_conf,
            "reasoning": reasoning_log,
            "treatment": treatment_advice
        }
```

#### 融合策略

##### 1. 强一致性 (Strong Consistency)

**条件**：视觉和文本结果一致

```python
if v_label == t_label and v_label != "未知":
    final_diagnosis = v_label
    final_conf = (v_conf * 0.6) + (t_conf * 0.4)
    reasoning_log.append(f"✅ 视觉与文本证据一致，均指向【{v_label}】")
```

**优势**：高置信度，可信度强

##### 2. 视觉主导 (Vision Dominance)

**条件**：视觉置信度 > 0.8

```python
elif v_conf > 0.8:
    final_diagnosis = v_label
    final_conf = v_conf
    reasoning_log.append(f"👁️ 视觉特征极其明显 (置信度 {v_conf:.2f})，优先采信视觉结果")
```

**优势**：避免文本描述不准确导致的误判

##### 3. 知识图谱仲裁 (KG Arbitration)

**条件**：两者冲突且置信度都不极高

```python
else:
    # 验证视觉结果
    v_support = self.kg.verify_consistency(v_label, user_text)
    # 验证文本结果
    t_support = self.kg.verify_consistency(t_label, user_text)
    
    if v_support and not t_support:
        final_diagnosis = v_label
        final_conf = v_conf * 0.9
    elif t_support and not v_support:
        final_diagnosis = t_label
        final_conf = t_conf * 0.9
    else:
        # 取置信度高的
        final_diagnosis = v_label if v_conf >= t_conf else t_label
```

**优势**：利用知识图谱约束，提高推理准确性

#### GraphRAG 机制

GraphRAG（Graph-based Retrieval-Augmented Generation）是系统的核心创新：

```
1. 检索 (Retrieval)
   ↓
   根据初步诊断结果，在 Neo4j 中检索相关子图
   
2. 上下文构建 (Context Construction)
   ↓
   将子图序列化为自然语言描述
   
3. 生成 (Generation)
   ↓
   结合图像特征和背景知识生成诊断报告
```

**示例**：

```
输入：图像检测为"条锈病"

检索：
- 条锈病 -CAUSED_BY-> 高湿环境
- 条锈病 -CAUSED_BY-> 气流传播
- 条锈病 -PREVENTED_BY-> 抗病选种
- 条锈病 -TREATED_BY-> 三唑酮/戊唑醇

上下文：
"条锈病常伴有鲜黄色孢子堆，适宜温度9-16度，高湿环境下易流行"

生成：
"根据图像特征，叶片呈现典型的条锈病症状。条锈病由条形柄锈菌引起，适宜温度9-16度，高湿环境下易流行。建议使用三唑酮或戊唑醇进行防治，同时注意田间通风降湿。"
```

---

## 🎬 行动层 (Action Layer)

行动层负责收集用户反馈并执行增量学习，实现系统的自进化。

### ActiveLearner - 反馈收集引擎

#### 架构设计

```python
class ActiveLearner:
    def __init__(self, data_root="datasets/feedback_data"):
        self.data_root = data_root
        # 创建反馈数据目录
    
    def collect_feedback(self, image_path, system_diagnosis, 
                       user_correction=None, comments=""):
        # 收集用户反馈
        final_label = user_correction or system_diagnosis
        
        # 保存图像到对应类别文件夹
        save_dir = os.path.join(self.data_root, final_label)
        # 生成带时间戳的文件名
        # 记录反馈日志
```

#### 反馈数据结构

```
datasets/feedback_data/
├── 条锈病/
│   ├── 20240110_143022_confirmed_条锈病.jpg
│   ├── 20240110_143523_err_白粉病_corr_条锈病.jpg
│   └── feedback_log.txt
├── 赤霉病/
│   └── ...
└── archived/  # 已处理的反馈数据
    ├── 条锈病/
    └── ...
```

#### 反馈日志格式

```
[20240110_143022] Image: 20240110_143022_confirmed_条锈病.jpg | System: 条锈病 | Final: 条锈病 | Comment: 诊断正确
[20240110_143523] Image: 20240110_143523_err_白粉病_corr_条锈病.jpg | System: 白粉病 | Final: 条锈病 | Comment: 实际是条锈病，白粉病误判
```

### EvolutionEngine - 增量训练引擎

#### 架构设计

```python
class EvolutionEngine:
    def __init__(self, feedback_root="datasets/feedback_data", 
                 dataset_root="datasets/wheat_data"):
        self.feedback_root = feedback_root
        self.dataset_root = dataset_root
        self.class_map = {
            "蚜虫": 0, "螨虫": 1, "茎蝇": 2,
            "锈病": 3, "茎锈病": 4, "叶锈病": 5,
            "条锈病": 6, "黑粉病": 7, "根腐病": 8,
            # ... 更多类别
        }
    
    def digest_feedback(self):
        # 消化反馈数据
        # 将反馈数据移动到训练集
        # 生成 YOLO 格式标签
        # 归档已处理数据
```

#### 增量学习流程

```
1. 扫描反馈数据池
   ↓
2. 遍历每个病害类别文件夹
   ↓
3. 对每张图片：
   - 移动到训练集 images/train/
   - 生成 YOLO 格式标签 (默认中心框)
   - 归档到 archived/
   ↓
4. 返回处理数量
```

#### 弱监督标签生成

对于用户反馈的图像，系统自动生成弱监督标签：

```python
# 默认中心框 (0.5, 0.5, 0.7, 0.7)
f.write(f"{class_id} 0.5 0.5 0.7 0.7\n")
```

**注意**：弱监督标签仅用于增量学习的初始阶段，后续可通过人工标注优化。

---

## 🔄 多模态融合机制

### KAD-Fusion (Knowledge-Aware Diffusion Fusion)

KAD-Fusion 是 IWDDA 的核心融合架构，实现了视觉、文本和知识的深度协同。

#### 融合流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ VisionAgent │     │LanguageAgent│     │KnowledgeAgent│
│  (YOLOv8)  │     │  (BERT)     │     │  (Neo4j)    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       ↓ 视觉特征          ↓ 文本嵌入          ↓ 知识检索
       │                   │                   │
       └─────────┬─────────┴───────────────────┘
                 ↓
         ┌───────────────┐
         │ FusionAgent   │
         │ (KAD-Fusion) │
         └───────┬───────┘
                 ↓
         ┌───────────────┐
         │ GraphRAG     │
         │ (检索增强生成) │
         └───────┬───────┘
                 ↓
         诊断报告与防治建议
```

#### 融合权重策略

| 模态 | 权重 | 说明 |
|------|------|------|
| 视觉 | 0.6 | 视觉特征在定位上更强 |
| 文本 | 0.4 | 文本描述提供语义补充 |
| 知识 | 动态 | 根据置信度和一致性动态调整 |

---

## 📊 数据流与交互

### 完整诊断流程

```
用户输入
  ↓
┌─────────────────────────────────────────┐
│ 1. 图像上传 + 症状描述输入          │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 2. 视觉感知 (VisionAgent)            │
│    - YOLOv8 检测                    │
│    - 提取视觉特征                    │
│    - 返回: {label, conf, bbox}        │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 3. 文本理解 (LanguageAgent)           │
│    - BERT 嵌入                      │
│    - 语义相似度计算                  │
│    - 返回: {label, conf}              │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 4. 多模态融合 (FusionAgent)         │
│    - 决策级融合                      │
│    - 知识图谱仲裁                    │
│    - 返回: {diagnosis, confidence,    │
│            reasoning, treatment}      │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 5. GraphRAG 增强生成               │
│    - 检索知识图谱                    │
│    - 上下文构建                      │
│    - 生成诊断报告                    │
└─────────────────────────────────────────┘
  ↓
用户反馈
  ↓
┌─────────────────────────────────────────┐
│ 6. 反馈收集 (ActiveLearner)         │
│    - 保存反馈数据                    │
│    - 记录修正信息                    │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 7. 增量训练 (EvolutionEngine)       │
│    - 消化反馈数据                    │
│    - 更新模型权重                    │
└─────────────────────────────────────────┘
```

### 模块间交互接口

#### VisionAgent → FusionAgent

```python
# 视觉结果格式
vision_result = {
    'label': '条锈病',
    'conf': 0.92,
    'bbox': [x, y, w, h]
}
```

#### LanguageAgent → FusionAgent

```python
# 文本结果格式
text_result = {
    'label': '条锈病',
    'conf': 0.85
}
```

#### KnowledgeAgent → FusionAgent

```python
# 知识详情格式
disease_details = {
    'name': '条锈病',
    'causes': ['高湿环境', '气流传播'],
    'preventions': ['抗病选种', '清沟沥水'],
    'treatments': ['三唑酮(喷雾)', '戊唑醇(喷雾)']
}
```

---

## ⚡ 性能优化

### 视觉模块优化

1. **模型量化**
   - 支持 INT8 量化
   - 减少 75% 模型大小
   - 适合边缘端部署

2. **TensorRT 加速**
   - YOLOv8-TensorRT 推理
   - 推理速度提升 3-5 倍
   - 支持 NVIDIA Jetson 系列

3. **批处理**
   - 支持批量图像处理
   - 提高 GPU 利用率
   - 减少推理延迟

### 文本模块优化

1. **模型缓存**
   - BERT 模型常驻内存
   - 避免重复加载
   - 减少初始化时间

2. **批嵌入**
   - 支持批量文本嵌入
   - 提高 GPU 利用率

### 知识图谱优化

1. **索引优化**
   - 为常用查询创建索引
   - 加速知识检索

2. **缓存机制**
   - 缓存常用查询结果
   - 减少 Neo4j 访问次数

3. **子图查询**
   - 只检索相关子图
   - 减少数据传输量

---

## 🔧 扩展性设计

### 新增病害类别

1. **更新类别映射**
```python
# configs/wheat_disease.yaml
names:
  17: 新病害名称
```

2. **更新知识图谱**
```python
# 添加新病害节点
CREATE (d:Disease {name: '新病害', type: 'Fungus'})
```

3. **收集训练数据**
- 收集新病害图像
- 标注 YOLO 格式标签
- 添加到训练集

4. **增量训练**
```bash
python src/vision/train.py
```

### 新增知识类型

1. **定义新实体类型**
```python
# 在 graph_engine.py 中添加
CREATE (e:NewEntityType {name: '...', ...})
```

2. **定义新关系类型**
```python
CREATE (d:Disease)-[:NEW_RELATION]->(e:NewEntityType)
```

3. **更新查询接口**
```python
# 在 get_disease_details 中添加新查询
```

---

## 📚 参考资料

- [YOLOv8 官方文档](https://docs.ultralytics.com/)
- [BERT 论文](https://arxiv.org/abs/1810.04805)
- [Neo4j 文档](https://neo4j.com/docs/)
- [GraphRAG 论文](https://arxiv.org/abs/2004.07180)

---

<div align="center">

**如需了解更多实现细节，请查看源代码和 [API文档](API_USAGE.md)**

</div>
