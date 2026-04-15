# IWDDA Code Wiki - 完整项目文档

> **项目名称**：基于多模态特征融合的小麦病害诊断智能体 (IWDDA)
> **版本**：v4.0 SerpensGate-KAD-Fusion版
> **最后更新**：2026-04-15

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [主要模块详细说明](#3-主要模块详细说明)
4. [关键类与函数说明](#4-关键类与函数说明)
5. [依赖关系](#5-依赖关系)
6. [项目运行方式](#6-项目运行方式)
7. [部署指南](#7-部署指南)
8. [开发指南](#8-开发指南)

---

## 1. 项目概述

### 1.1 项目简介

IWDDA（Intelligent Wheat Disease Diagnosis Agent）是一个融合视觉感知、语义理解和知识推理的智能农业诊断系统，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、自然语言处理和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。

### 1.2 核心特性

- **多模态融合**：结合图像视觉特征、文本语义描述和结构化知识图谱，提高诊断准确性
- **智能推理**：基于知识图谱的 GraphRAG 机制，提供科学的防治建议
- **自进化能力**：支持增量学习和人机反馈，持续优化模型性能
- **实时检测**：基于 YOLOv8 的高效视觉检测，支持边缘端部署
- **友好交互**：提供 Gradio Web 界面和命令行接口

### 1.3 支持的病害类别

| ID | 中文名称 | 英文名称 | 类型 |
|----|---------|---------|------|
| 0 | 蚜虫 | Aphids | 昆虫 |
| 1 | 螨虫 | Mites | 昆虫 |
| 2 | 茎蝇 | Stem Fly | 昆虫 |
| 3 | 锈病 | Rust | 真菌 |
| 4 | 茎锈病 | Stem Rust | 真菌 |
| 5 | 叶锈病 | Leaf Rust | 真菌 |
| 6 | 条锈病 | Stripe Rust | 真菌 |
| 7 | 黑粉病 | Smuts | 真菌 |
| 8 | 根腐病 | Common Root Rot | 真菌 |
| 9 | 叶斑病 | Spot Blotch | 真菌 |
| 10 | 小麦爆发病 | Wheat Blast | 真菌 |
| 11 | 赤霉病 | Fusarium Head Blight | 真菌 |
| 12 | 壳针孢叶斑病 | Septoria Leaf Blotch | 真菌 |
| 13 | 斑点叶斑病 | Speckled Leaf Blotch | 真菌 |
| 14 | 褐斑病 | Brown Spot | 真菌 |
| 15 | 白粉病 | Powdery Mildew | 真菌 |
| 16 | 健康 | Healthy | 正常 |

---

## 2. 系统架构

### 2.1 整体架构

IWDDA 采用"感知-认知-行动"三层架构：

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

### 2.2 设计原则

1. **模块化设计**：各模块职责清晰，松耦合，易于扩展和维护
2. **多模态协同**：视觉、文本、知识三种模态深度融合，互为补充
3. **可解释性**：提供详细的推理过程和置信度评估
4. **自进化能力**：支持增量学习和人机反馈，持续优化

### 2.3 技术栈

| 模块 | 技术框架 | 用途 |
|------|---------|------|
| 视觉检测 | YOLOv8 (Ultralytics) | 目标检测与定位 |
| 文本理解 | Transformers (BERT) | 语义相似度计算 |
| 知识图谱 | Neo4j | 结构化知识存储与推理 |
| Web界面 | Gradio | 交互式诊断界面 |
| 深度学习 | PyTorch | 模型训练与推理 |

---

## 3. 主要模块详细说明

### 3.1 感知层 (Perception Layer)

#### 3.1.1 VisionAgent - 视觉感知引擎

**文件路径**：[src/vision/vision_engine.py](file:///workspace/src/vision/vision_engine.py)

**核心功能**：
- 自动模型加载与选择
- 实时目标检测
- 可视化输出

**关键特性**：
- 骨干网络：CSPDarknet
- 检测头：Anchor-free 解耦头
- 损失函数：CIoU Loss + 分类损失
- 输入尺寸：512x512 (可配置)
- 推理速度：>30 FPS (GPU)

**模型搜索优先级**：
1. 用户指定的模型路径
2. `models/yolov8_wheat.pt` (小麦病害专用模型)
3. `runs/detect/runs/train/wheat_evolution/weights/best.pt` (最新训练模型)
4. `yolov8n.pt` (官方预训练模型，fallback)

#### 3.1.2 LanguageAgent - 文本理解引擎

**文件路径**：[src/text/text_engine.py](file:///workspace/src/text/text_engine.py)

**核心功能**：
- 文本嵌入
- 语义相似度计算
- 标准症状库匹配

**关键特性**：
- 使用 BERT-base-chinese 模型
- 提取 [CLS] token 作为句子级表示
- 支持 128 token 最大长度
- 余弦相似度度量
- 阈值过滤（<0.35 视为不匹配）

**标准症状库**：
```python
standard_symptoms = {
    "蚜虫": "黑色或绿色小虫，分泌蜜露",
    "螨虫": "叶片卷曲发黄，植株矮小",
    "茎蝇": "茎秆有蛀孔，植株枯萎",
    "锈病": "叶片上有黄色或红褐色粉末孢子堆",
    # ... 更多症状
}
```

### 3.2 认知层 (Cognition Layer)

#### 3.2.1 KnowledgeAgent - 知识图谱引擎

**文件路径**：[src/graph/graph_engine.py](file:///workspace/src/graph/graph_engine.py)

**核心功能**：
- 知识图谱初始化
- 病害详情查询
- GraphRAG 检索增强

**知识图谱本体设计**：

**核心实体节点**：
| 实体类型 | 属性 | 示例 |
|---------|------|------|
| Disease | name, type | 条锈病, Fungus |
| Symptom | name, description | 黄色条纹, 叶片褪绿 |
| Pathogen | name, latin_name | Puccinia striiformis |
| Environment | name, condition | 高湿环境, 低温寡照 |
| Prevention | name, desc | 抗病选种, 清沟沥水 |
| Treatment | name, usage | 三唑酮, 喷雾 |

**语义关系边**：
| 关系 | 描述 | 示例 |
|------|------|------|
| CAUSED_BY | 病害由...引起 | 条锈病 -CAUSED_BY-> 高湿环境 |
| PREVENTED_BY | 病害可由...预防 | 条锈病 -PREVENTED_BY-> 抗病选种 |
| TREATED_BY | 病害可由...治疗 | 条锈病 -TREATED_BY-> 三唑酮 |
| MANIFESTS_AS | 病害表现为... | 条锈病 -MANIFESTS_AS-> 黄色条纹 |

**初始化内容**：
1. 16类病害节点
2. 环境成因节点（高湿、低温、高温、土壤连作、气流传播）
3. 预防措施节点（抗病选种、轮作倒茬、清沟沥水、清除病残体）
4. 治疗药剂节点（三唑酮/戊唑醇、吡虫啉、氰烯菌酯）
5. 关联关系建立

#### 3.2.2 FusionAgent - 多模态融合引擎

**文件路径**：[src/fusion/fusion_engine.py](file:///workspace/src/fusion/fusion_engine.py)

**核心功能**：
- KAD-Fusion (Knowledge-Aware Diffusion Fusion) 融合策略
- 决策级融合
- 知识图谱仲裁
- GraphRAG 增强生成

**融合策略**：

**1. 纯视觉模式**
- **条件**：用户没有提供文本描述，或文本结果未知
- **策略**：直接使用视觉结果，可结合知识图谱验证微调

**2. 强一致性**
- **条件**：视觉和文本结果一致
- **策略**：加权融合，视觉权重 0.6，文本权重 0.4

**3. 视觉主导**
- **条件**：视觉置信度 > 0.8
- **策略**：优先采信视觉结果

**4. 知识图谱仲裁**
- **条件**：两者冲突且置信度都不极高
- **策略**：查询知识图谱验证一致性，选择支持度高的结果

**KAD-Fusion 核心模块**：
1. 知识引导注意力（KGA）：用知识图谱嵌入校准视觉注意力
2. 跨模态特征对齐：文本特征作为 Query 查询视觉特征
3. 残差连接与层归一化

**GraphRAG 机制**：
1. **检索**：根据初步诊断结果，在 Neo4j 中检索相关子图
2. **上下文构建**：将子图序列化为自然语言描述
3. **生成**：结合图像特征和背景知识生成诊断报告

### 3.3 行动层 (Action Layer)

#### 3.3.1 ActiveLearner - 反馈收集引擎

**文件路径**：[src/action/learner_engine.py](file:///workspace/src/action/learner_engine.py)

**核心功能**：
- 用户反馈收集
- 困难样本挖掘
- 反馈数据存储

**反馈数据结构**：
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

#### 3.3.2 EvolutionEngine - 增量训练引擎

**文件路径**：[src/action/evolve.py](file:///workspace/src/action/evolve.py)

**核心功能**：
- 反馈数据消化
- 弱监督标签生成
- 增量训练执行

**增量学习流程**：
1. 扫描反馈数据池
2. 遍历每个病害类别文件夹
3. 对每张图片：
   - 移动到训练集 images/train/
   - 生成 YOLO 格式标签 (默认中心框)
   - 归档到 archived/
4. 返回处理数量

---

## 4. 关键类与函数说明

### 4.1 主程序类

#### EnhancedWheatDoctor

**文件路径**：[main_enhanced.py](file:///workspace/main_enhanced.py)

**初始化参数**：
- `use_enhanced_vision` (bool, default=True)：是否使用增强版视觉Agent
- `use_enhanced_language` (bool, default=True)：是否使用增强版语言Agent
- `use_enhanced_fusion` (bool, default=True)：是否使用增强版融合Agent
- `device` (str, default='cuda' if available else 'cpu')：计算设备

**主要方法**：

##### `run_diagnosis(image_path, user_text="", return_features=False)`

执行完整的诊断流程。

**参数**：
- `image_path` (str)：图片路径
- `user_text` (str, optional)：用户文本描述
- `return_features` (bool, optional)：是否返回特征信息

**返回值**：
```python
{
    "plotted_image": numpy.ndarray,  # 标注图像
    "vision_data": dict,             # 视觉识别结果
    "text_data": dict,               # 文本分析结果
    "final_report": dict,            # 最终诊断报告
    "detection_results": list        # 检测结果列表
}
```

##### `chat(message, image_path=None)`

交互式对话。

**参数**：
- `message` (str)：用户消息
- `image_path` (str, optional)：可选的图片路径

**返回值**：
- (str)：助手回复

##### `submit_diagnosis_feedback(...)`

提交诊断反馈。

**参数**：
- `image_path` (str)：图像路径
- `system_diagnosis` (str)：系统诊断结果
- `confidence` (float)：置信度
- `user_correction` (str, optional)：用户修正
- `comments` (str)：评论
- `reviewer_id` (str, optional)：审核人ID

**返回值**：
- (dict)：反馈处理结果

### 4.2 视觉模块类

#### VisionAgent

**文件路径**：[src/vision/vision_engine.py](file:///workspace/src/vision/vision_engine.py)

**初始化参数**：
- `model_path` (str, optional)：模型路径

**主要方法**：

##### `detect(image_path, conf_threshold=0.25, iou_threshold=0.45, save_result=False)`

执行目标检测。

**参数**：
- `image_path` (str)：图像路径
- `conf_threshold` (float, default=0.25)：置信度阈值
- `iou_threshold` (float, default=0.45)：NMS IoU阈值
- `save_result` (bool, default=False)：是否保存可视化结果

**返回值**：
```python
[
    {
        'name': str,           # 类别名称
        'confidence': float,   # 置信度
        'bbox': list,          # 边界框 [x1, y1, x2, y2]
        'class_id': int        # 类别ID
    },
    ...
]
```

##### `detect_and_visualize(image_path, conf_threshold=0.25, iou_threshold=0.45, output_path=None)`

执行检测并生成可视化结果。

**参数**：
- `image_path` (str)：输入图像路径
- `conf_threshold` (float, default=0.25)：置信度阈值
- `iou_threshold` (float, default=0.45)：NMS IoU阈值
- `output_path` (str, optional)：输出图像路径

**返回值**：
- (tuple)：(检测结果列表, 可视化图像路径)

### 4.3 知识图谱模块类

#### KnowledgeAgent

**文件路径**：[src/graph/graph_engine.py](file:///workspace/src/graph/graph_engine.py)

**初始化参数**：
- `uri` (str, default="neo4j://localhost:7687")：Neo4j URI
- `user` (str, default="neo4j")：用户名
- `password` (str, default="123456789s")：密码

**主要方法**：

##### `get_disease_details(disease_name)`

获取病害的全方位详情：成因、预防、治疗。

**参数**：
- `disease_name` (str)：病害名称

**返回值**：
```python
{
    "name": str,
    "causes": list,
    "preventions": list,
    "treatments": list
}
```

##### `get_treatment_info(disease_name)`

获取病害的治疗信息（兼容旧代码）。

**参数**：
- `disease_name` (str)：病害名称

**返回值**：
- (str)：治疗建议字符串

### 4.4 融合模块类

#### FusionAgent

**文件路径**：[src/fusion/fusion_engine.py](file:///workspace/src/fusion/fusion_engine.py)

**初始化参数**：
- `knowledge_agent`：已初始化的 KnowledgeAgent 实例

**主要方法**：

##### `fuse_and_decide(vision_result, text_result, user_text, is_auto_generated=False)`

执行决策级融合。

**参数**：
- `vision_result` (dict)：视觉识别结果
- `text_result` (dict)：文本识别结果
- `user_text` (str)：用户文本描述
- `is_auto_generated` (bool, default=False)：是否自动生成的症状描述

**返回值**：
```python
{
    "diagnosis": str,        # 最终诊断
    "confidence": float,     # 置信度
    "reasoning": list,       # 推理日志
    "treatment": str         # 治疗建议
}
```

##### `diagnose(image_path, use_knowledge=True, top_k=3, vision_engine=None, cognition_engine=None)`

执行图像诊断 - 整合视觉检测和知识图谱。

**参数**：
- `image_path` (str)：图像路径
- `use_knowledge` (bool, default=True)：是否使用知识图谱
- `top_k` (int, default=3)：返回前K个结果
- `vision_engine`：视觉引擎实例（可选）
- `cognition_engine`：认知引擎实例（可选）

**返回值**：
- (list)：诊断结果列表

---

## 5. 依赖关系

### 5.1 核心依赖

**文件路径**：[requirements.txt](file:///workspace/requirements.txt)

#### 深度学习框架
- `torch>=2.0.0` - PyTorch 深度学习框架
- `torchvision>=0.15.0` - 计算机视觉库
- `ultralytics>=8.0.0` - YOLOv8 目标检测框架

#### 自然语言处理
- `transformers>=4.30.0` - Hugging Face Transformers
- `tokenizers>=0.13.0` - Tokenizers 库

#### 知识图谱
- `neo4j>=5.14.0` - Neo4j Python 驱动

#### Web 界面
- `gradio>=4.0.0` - Gradio Web 界面框架

#### 图像处理
- `opencv-python>=4.8.0` - OpenCV
- `pillow>=10.0.0` - PIL
- `albumentations>=1.3.0` - 数据增强库

#### 数据处理
- `numpy>=1.24.0` - 数值计算
- `pandas>=2.0.0` - 数据处理
- `pyyaml>=6.0` - YAML 配置

#### 可视化
- `matplotlib>=3.7.0` - 绘图
- `seaborn>=0.12.0` - 统计可视化

#### 工具库
- `tqdm>=4.65.0` - 进度条
- `requests>=2.31.0` - HTTP 请求
- `scipy>=1.11.0` - 科学计算

### 5.2 模块间依赖关系

```
EnhancedWheatDoctor (主程序)
├── EnhancedVisionAgent (视觉感知)
│   └── YOLO (Ultralytics)
├── EnhancedLanguageAgent (文本理解)
│   └── BERT (Transformers)
├── KnowledgeAgent (知识图谱)
│   └── Neo4j
├── EnhancedFusionAgent (多模态融合)
│   ├── KnowledgeGuidedAttention
│   └── CrossModalAttention
├── EnhancedActiveLearner (反馈收集)
└── FeedbackLoopIntegrator (反馈闭环)
    └── EvolutionEngine (增量训练)
```

---

## 6. 项目运行方式

### 6.1 环境要求

- **Python**: 3.8+ (推荐 3.10)
- **PyTorch**: 1.10+ (推荐 2.0+)
- **CUDA**: 11.0+ (GPU 加速)
- **Neo4j**: 5.x
- **RAM**: 8GB+ (推荐 16GB)

### 6.2 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/WheatAgent.git
cd WheatAgent
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置 Neo4j**

启动 Neo4j 服务（默认端口 7687）：
```bash
# 使用 Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/123456789s \
  neo4j:5.x
```

或本地安装 Neo4j Desktop，设置密码为 `123456789s`

5. **准备数据集**

将小麦病害数据集放置在 `datasets/wheat_data/` 目录下：
```
datasets/wheat_data/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### 6.3 启动方式

#### 方式一：Web 界面 (Gradio)

```bash
python run_web.py
```

访问 `http://localhost:7860` 开始使用

#### 方式二：API 服务

```bash
python run_api.py
```

#### 方式三：命令行使用

```python
from main_enhanced import EnhancedWheatDoctor

# 初始化诊断系统
doctor = EnhancedWheatDoctor()

# 执行诊断
result = doctor.run_diagnosis(
    image_path="data/images/test_wheat.jpg",
    user_text="叶片上有黄色条纹状锈斑"
)

# 查看结果
print(f"诊断结果: {result['final_report']['diagnosis']}")
print(f"置信度: {result['final_report']['confidence']:.2f}")
print(f"推理过程: {result['final_report']['reasoning']}")
```

### 6.4 运行测试

```bash
# 运行所有测试
python run_tests.py

# 运行视觉模块测试
python tests/test_vision.py

# 运行集成测试
python tests/integration/test_end_to_end.py
```

---

## 7. 部署指南

### 7.1 模型优化部署

#### TensorRT 加速

```bash
# 导出 TensorRT 模型
python src/deploy/tensorrt_exporter.py
```

#### 边缘设备优化

```bash
# 优化模型用于边缘设备
python src/deploy/edge_optimizer.py
```

### 7.2 Docker 部署

```dockerfile
# Dockerfile 示例
FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "run_web.py"]
```

---

## 8. 开发指南

### 8.1 项目结构

```
WheatAgent/
├── main_enhanced.py         # 主程序入口（增强版）
├── app.py                    # Gradio Web 界面
├── configs/                  # 配置文件
│   ├── wheat_agent.yaml
│   └── wheat_disease.yaml
├── src/                      # 源代码
│   ├── vision/               # 视觉感知模块
│   │   ├── vision_engine.py
│   │   ├── enhanced_vision_engine.py
│   │   ├── dy_snake_conv.py
│   │   ├── sppelan_module.py
│   │   ├── sta_module.py
│   │   └── train.py
│   ├── text/                 # 文本理解模块
│   │   ├── text_engine.py
│   │   └── enhanced_text_engine.py
│   ├── graph/                # 知识图谱模块
│   │   ├── graph_engine.py
│   │   ├── graphrag_engine.py
│   │   └── knowledge_graph_builder.py
│   ├── fusion/               # 融合模块
│   │   ├── fusion_engine.py
│   │   ├── enhanced_fusion_engine.py
│   │   ├── kga_module.py
│   │   └── cross_attention.py
│   ├── action/               # 行动模块
│   │   ├── learner_engine.py
│   │   ├── enhanced_learner_engine.py
│   │   ├── evolve.py
│   │   └── feedback_integration.py
│   ├── evolution/            # 进化模块
│   │   ├── experience_replay.py
│   │   └── human_in_the_loop.py
│   ├── cognition/            # 认知模块
│   │   ├── llava_engine.py
│   │   ├── cognition_engine.py
│   │   ├── trainer.py
│   │   └── prompt_templates.py
│   ├── training/             # 训练模块
│   │   ├── yolo_trainer.py
│   │   └── agri_llava_trainer.py
│   ├── evaluation/           # 评估模块
│   │   └── evaluation_framework.py
│   ├── data/                 # 数据模块
│   │   ├── dataset_builder.py
│   │   └── augmentation_engine.py
│   ├── deploy/               # 部署模块
│   │   ├── tensorrt_exporter.py
│   │   ├── edge_optimizer.py
│   │   └── export.py
│   ├── web/                  # Web 模块
│   │   └── app.py
│   ├── api/                  # API 模块
│   │   └── main.py
│   ├── utils/                # 工具模块
│   │   ├── logger.py
│   │   ├── config_manager.py
│   │   └── error_handler.py
│   └── tools/                # 工具脚本
│       ├── label_generator.py
│       └── data_converter.py
├── datasets/                 # 数据集目录
│   ├── wheat_data/          # 小麦病害数据集
│   └── agri_instruct/       # 农业指令数据集
├── checkpoints/              # 检查点目录
│   └── knowledge_graph/     # 知识图谱检查点
├── data/                     # 数据目录
│   ├── images/              # 测试图片
│   ├── texts/               # 文本数据
│   └── human_feedback/      # 人类反馈数据
├── models/                   # 模型权重目录
├── runs/                     # 训练输出目录
├── tests/                    # 测试目录
│   ├── test_vision.py
│   ├── test_api.py
│   ├── test_system_comprehensive.py
│   └── integration/
├── scripts/                  # 脚本目录
│   ├── check_env.py
│   ├── check_gpu.py
│   ├── check_dataset.py
│   └── train_all_models.py
├── requirements.txt          # 依赖列表
└── CODE_WIKI.md             # 本文档
```

### 8.2 新增病害类别

1. **更新类别映射**
```yaml
# configs/wheat_disease.yaml
names:
  17: 新病害名称
```

2. **更新知识图谱**
```python
# 在 knowledge_graph_builder.py 中添加
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

### 8.3 代码规范

- 遵循 PEP 8 编码规范
- 使用类型提示 (Type Hints)
- 编写 docstring 文档
- 添加单元测试

---

## 9. 附录

### 9.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| mAP@0.5 | > 95% | 视觉检测准确率 |
| CIoU | > 0.85 | 边界框定位精度 |
| 语义相似度 | > 0.85 | 文本理解准确率 |
| 推理速度 | > 30 FPS | 实时检测能力 |

### 9.2 参考资料

- [YOLOv8 官方文档](https://docs.ultralytics.com/)
- [BERT 论文](https://arxiv.org/abs/1810.04805)
- [Neo4j 文档](https://neo4j.com/docs/)
- [GraphRAG 论文](https://arxiv.org/abs/2004.07180)

### 9.3 联系方式

- 项目主页: [https://github.com/your-repo/WheatAgent](https://github.com/your-repo/WheatAgent)
- 问题反馈: [Issues](https://github.com/your-repo/WheatAgent/issues)

---

**文档版本**：v1.0  
**最后更新**：2026-04-15  
**维护者**：IWDDA Team

