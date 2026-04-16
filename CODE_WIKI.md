# IWDDA 项目 Code Wiki

## 1. 项目概览

IWDDA (Intelligent Wheat Disease Diagnosis Agent) 是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、自然语言处理和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。

### 核心优势
- **多模态融合**：结合图像视觉特征、文本语义描述和结构化知识图谱，提高诊断准确性
- **智能推理**：基于知识图谱的 GraphRAG 机制，提供科学的防治建议
- **自进化能力**：支持增量学习和人机反馈，持续优化模型性能
- **实时检测**：基于 YOLOv8 的高效视觉检测，支持边缘端部署
- **友好交互**：提供 Gradio Web 界面和命令行接口

### 应用场景
- 农业生产中的小麦病害快速诊断
- 基层农技人员的辅助诊断工具
- 农业知识普及和教育
- 智能农业系统的核心组件

## 2. 系统架构

IWDDA 采用分层架构设计，从感知层到认知层再到行动层，形成完整的诊断闭环。

### 系统架构图

```
IWDDA System
├── 感知层 (Perception Layer)
│   ├── VisionAgent (YOLOv8)     - 图像检测与定位
│   └── LanguageAgent (BERT)     - 文本语义理解
├── 认知层 (Cognition Layer)
│   ├── KnowledgeAgent (Neo4j)    - 知识图谱推理
│   ├── FusionAgent              - 多模态融合决策
│   └── CognitionEngine          - Agri-LLaVA 语义理解
└── 行动层 (Action Layer)
    ├── ActiveLearner             - 反馈收集
    └── EvolutionEngine           - 增量训练
```

### 技术栈

| 模块 | 技术框架 | 用途 |
|------|---------|------|
| 视觉检测 | YOLOv8 (Ultralytics) | 目标检测与定位 |
| 文本理解 | Transformers (BERT) | 语义相似度计算 |
| 知识图谱 | Neo4j | 结构化知识存储与推理 |
| 多模态理解 | Agri-LLaVA | 图像-文本联合理解 |
| Web界面 | Gradio | 交互式诊断界面 |
| 深度学习 | PyTorch | 模型训练与推理 |

## 3. 目录结构

```
WheatAgent/
├── src/                      # 源代码
│   ├── vision/               # 视觉感知模块
│   │   ├── vision_engine.py   # 视觉检测引擎
│   │   └── train.py          # 模型训练脚本
│   ├── text/                 # 文本理解模块
│   │   └── text_engine.py    # 文本处理引擎
│   ├── graph/                # 知识图谱模块
│   │   └── graph_engine.py   # Neo4j 交互引擎
│   ├── fusion/               # 融合模块
│   │   └── fusion_engine.py # 多模态融合引擎
│   ├── cognition/            # 认知模块
│   │   └── cognition_engine.py # Agri-LLaVA 引擎
│   ├── action/               # 行动模块
│   │   ├── learner_engine.py # 反馈收集引擎
│   │   └── evolve.py        # 增量训练引擎
│   ├── web/                  # Web 界面
│   │   └── app.py           # Gradio 应用
│   └── utils/               # 工具模块
├── datasets/                 # 数据集目录
│   ├── wheat_data/          # 小麦病害数据集
│   └── agri_instruct/       # 农业指令数据集
├── configs/                  # 配置文件
│   ├── wheat_agent.yaml     # 全局配置
│   └── wheat_disease.yaml   # 数据集配置
├── data/                    # 测试数据
│   ├── images/              # 测试图片
│   └── texts/              # 文本数据
├── checkpoints/             # 模型检查点
└── runs/                    # 训练输出目录
```

## 4. 核心模块详解

### 4.1 视觉感知模块 (VisionAgent)

**功能**：负责图像检测和病害定位，基于 YOLOv8 实现高精度目标检测。

**关键文件**：[vision_engine.py](file:///workspace/src/vision/vision_engine.py)

**核心类**：`VisionAgent`

**主要方法**：
- `__init__(model_path=None)`: 初始化视觉引擎，自动搜索并加载合适的模型
- `detect(image_path, conf_threshold=0.25, iou_threshold=0.45, save_result=False)`: 执行检测，返回格式化结果
- `detect_and_visualize(image_path, conf_threshold=0.25, iou_threshold=0.45, output_path=None)`: 执行检测并生成可视化结果

**技术特点**：
- 支持17类小麦病害和虫害识别
- 自动定位病灶区域并绘制可视化结果
- 支持自定义模型权重加载
- 集成了动态蛇形卷积、SPPELAN多尺度特征聚合、超级令牌注意力等增强技术

### 4.2 认知模块 (CognitionEngine)

**功能**：集成 Agri-LLaVA 模型，提供高级语义理解和诊断报告生成功能。

**关键文件**：[cognition_engine.py](file:///workspace/src/cognition/cognition_engine.py)

**核心类**：`CognitionEngine`

**主要方法**：
- `__init__(model_path=None, vision_encoder_name="openai/clip-vit-large-patch14", llm_name="lmsys/vicuna-7b-v1.5", device="cuda")`: 初始化认知引擎
- `analyze_image(image, detection_results=None, user_description=None)`: 分析图像并生成诊断报告
- `answer_question(question, image=None, detection_results=None, chat_history=None)`: 回答用户问题
- `generate_diagnosis_report(disease_name, confidence, detection_results, user_description=None)`: 生成格式化的诊断报告

**技术特点**：
- 多模态输入（图像+文本）
- 基于 LLaVA 的语义理解
- 交互式对话
- 专业诊断报告生成
- 备用模式（当 LLaVA 不可用时）

### 4.3 融合模块 (FusionAgent)

**功能**：实现多模态特征融合，结合视觉、文本和知识图谱信息进行综合诊断。

**关键文件**：[fusion_engine.py](file:///workspace/src/fusion/fusion_engine.py)

**核心类**：`FusionAgent`

**主要方法**：
- `__init__(knowledge_agent)`: 初始化融合引擎
- `deep_feature_fusion(vision_features, text_features, knowledge_embedding)`: 执行深度特征融合
- `fuse_and_decide(vision_result, text_result, user_text, is_auto_generated=False)`: 执行决策级融合
- `diagnose(image_path, use_knowledge=True, top_k=3, vision_engine=None, cognition_engine=None)`: 执行图像诊断

**技术特点**：
- KAD-Fusion (Knowledge-Aware Diffusion Fusion) 融合策略
- 决策级融合：视觉主导 + 文本辅助 + 知识仲裁
- 提供详细的推理过程和置信度评估
- 集成 GraphRAG 机制，增强诊断能力

### 4.4 知识图谱模块 (KnowledgeAgent)

**功能**：基于 Neo4j 存储和管理农业知识，提供知识推理和查询功能。

**关键文件**：[graph_engine.py](file:///workspace/src/graph/graph_engine.py)

**核心类**：`KnowledgeAgent`

**主要方法**：
- `__init__(uri="neo4j://localhost:7687", user="neo4j", password="123456789s")`: 初始化知识图谱连接
- `_init_knowledge_base()`: 初始化知识库，注入病害、成因、预防和治疗信息
- `get_disease_details(disease_name)`: 获取病害的全方位详情
- `get_treatment_info(disease_name)`: 获取病害的治疗信息

**技术特点**：
- 包含16类核心病害节点
- 定义环境成因、预防措施和治疗药剂
- 建立病害与成因、预防、治疗之间的关联
- 支持多跳推理和关联查询

### 4.5 Web 界面模块

**功能**：提供用户友好的交互式诊断界面，支持图像诊断、文本诊断和知识库查询。

**关键文件**：[app.py](file:///workspace/src/web/app.py)

**核心类**：`WheatAgentWebApp`

**主要方法**：
- `__init__()`: 初始化Web应用
- `diagnose_image(image, use_knowledge=True, top_k=3)`: 图像诊断
- `diagnose_text(text, use_knowledge=True, top_k=3)`: 文本症状诊断
- `get_disease_list()`: 获取病害列表
- `get_disease_detail(disease_name)`: 获取病害详细信息

**技术特点**：
- Gradio Web 界面
- 多标签页设计：图像诊断、文本诊断、知识库查询、使用说明
- 实时诊断结果展示
- 可视化检测结果

## 5. 核心 API/类/函数

### 5.1 主要类

| 类名 | 模块 | 描述 | 关键方法 |
|------|------|------|----------|
| `VisionAgent` | vision_engine | 视觉检测引擎 | detect, detect_and_visualize |
| `CognitionEngine` | cognition_engine | 认知引擎 | analyze_image, answer_question, generate_diagnosis_report |
| `FusionAgent` | fusion_engine | 多模态融合引擎 | deep_feature_fusion, fuse_and_decide, diagnose |
| `KnowledgeAgent` | graph_engine | 知识图谱引擎 | get_disease_details, get_treatment_info |
| `WheatAgentWebApp` | web/app | Web应用 | diagnose_image, diagnose_text, get_disease_list, get_disease_detail |

### 5.2 关键函数

| 函数名 | 模块 | 描述 | 参数 | 返回值 |
|--------|------|------|------|--------|
| `detect` | vision_engine | 执行图像检测 | image_path, conf_threshold, iou_threshold, save_result | 检测结果列表 |
| `analyze_image` | cognition_engine | 分析图像并生成诊断报告 | image, detection_results, user_description | 诊断报告字典 |
| `diagnose` | fusion_engine | 执行图像诊断 | image_path, use_knowledge, top_k, vision_engine, cognition_engine | 诊断结果列表 |
| `get_disease_details` | graph_engine | 获取病害详情 | disease_name | 病害详情字典 |
| `create_app` | web/app | 创建Gradio应用 | 无 | Gradio Blocks实例 |

## 6. 技术流程

### 6.1 诊断流程

1. **输入处理**：接收用户上传的图像和/或文本描述
2. **视觉检测**：使用 YOLOv8 进行图像检测，识别病害类型和位置
3. **文本分析**：使用 BERT 或 Agri-LLaVA 分析用户描述
4. **知识检索**：从知识图谱中检索相关病害信息
5. **多模态融合**：使用 KAD-Fusion 架构融合视觉、文本和知识信息
6. **诊断生成**：生成诊断报告和防治建议
7. **结果展示**：在 Web 界面展示诊断结果和可视化图像

### 6.2 知识图谱推理流程

1. **初始化**：启动时注入病害、成因、预防和治疗信息
2. **查询**：根据检测到的病害名称查询相关信息
3. **验证**：验证检测结果与用户描述的一致性
4. **推理**：基于知识图谱进行多跳推理，提供防治建议
5. **增强**：使用 GraphRAG 机制增强诊断报告

### 6.3 自进化流程

1. **反馈收集**：收集用户对诊断结果的反馈
2. **数据处理**：处理反馈数据，构建增量学习数据集
3. **模型更新**：使用增量学习更新模型权重
4. **性能评估**：评估更新后模型的性能
5. **知识更新**：根据反馈更新知识图谱

## 7. 配置与部署

### 7.1 环境要求

- Python 3.8+
- PyTorch 1.10+ (推荐使用 CUDA 支持)
- Neo4j 5.x
- 8GB+ RAM (推荐 16GB)

### 7.2 安装步骤

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

6. **启动 Web 界面**
```bash
python src/web/app.py
```

访问 `http://localhost:7861` 开始使用

### 7.3 配置文件

**全局配置** (`configs/wheat_agent.yaml`)：
- 项目信息
- 视觉模块配置
- 知识图谱配置

**数据集配置** (`configs/wheat_disease.yaml`)：
- 数据集路径
- 类别定义
- 训练参数

## 8. 支持的病害类别

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

## 9. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| mAP@0.5 | > 95% | 视觉检测准确率 |
| CIoU | > 0.85 | 边界框定位精度 |
| 语义相似度 | > 0.85 | 文本理解准确率 |
| 推理速度 | > 30 FPS | 实时检测能力 |

## 10. 开发与扩展

### 10.1 模型训练

**视觉模型训练**：
```bash
python src/vision/train.py --data configs/wheat_disease.yaml --epochs 100 --batch-size 16
```

**Agri-LLaVA 训练**：
```bash
python src/training/agri_llava_trainer.py --data datasets/agri_instruct/phase1_data.json
```

### 10.2 扩展新病害

1. **更新数据集**：在 `datasets/wheat_data/` 中添加新病害的图像和标签
2. **更新配置**：修改 `configs/wheat_disease.yaml` 中的类别定义
3. **重新训练**：使用新数据训练视觉模型
4. **更新知识图谱**：在 `graph_engine.py` 中添加新病害的知识信息

### 10.3 边缘部署

项目支持通过 TensorRT 导出模型，部署到边缘设备：
```bash
python src/deploy/tensorrt_exporter.py --model runs/detect/train/weights/best.pt
```

## 11. 故障排除

### 11.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| 模型加载失败 | 模型路径不存在 | 检查模型路径，确保模型文件存在 |
| 知识图谱连接失败 | Neo4j 服务未启动 | 启动 Neo4j 服务，确保端口正确 |
| 诊断结果不准确 | 图像质量差 | 上传清晰、光线充足的图像 |
| Web 界面无法访问 | 端口被占用 | 更改 `app.py` 中的端口号 |

### 11.2 日志与监控

- 系统运行日志：控制台输出
- 模型训练日志：`runs/` 目录下的训练日志
- Neo4j 日志：Neo4j 服务日志

## 12. 总结与亮点回顾

IWDDA 项目是一个融合多模态技术的智能农业诊断系统，具有以下核心亮点：

1. **多模态融合**：创新性地结合视觉、文本和知识图谱信息，提高诊断准确性
2. **智能推理**：基于 GraphRAG 机制，提供科学的防治建议
3. **自进化能力**：支持增量学习和人机反馈，持续优化模型性能
4. **实时检测**：基于 YOLOv8 的高效视觉检测，支持边缘端部署
5. **友好交互**：提供 Gradio Web 界面，方便用户使用
6. **完整知识体系**：基于 Neo4j 的农业知识图谱，包含病害成因、预防措施、治疗药剂等完整信息
7. **技术先进性**：集成了最新的深度学习技术，如 YOLOv8、LLaVA 等

该项目为农业病害诊断提供了一个智能化、标准化的解决方案，具有广阔的应用前景和推广价值。

## 13. 参考资料

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 目标检测框架
- [Hugging Face Transformers](https://github.com/huggingface/transformers) - 自然语言处理工具
- [Neo4j](https://neo4j.com/) - 图数据库
- [Gradio](https://gradio.app/) - Web 界面框架
- [PyTorch](https://pytorch.org/) - 深度学习框架
