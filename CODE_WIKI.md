# WheatAgent 项目代码 Wiki

## 1. 项目概述

### 1.1 项目简介

**WheatAgent** 是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、自然语言处理和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。

### 1.2 核心优势

- **多模态融合**：结合图像视觉特征、文本语义描述和结构化知识图谱，提高诊断准确性
- **智能推理**：基于知识图谱的 GraphRAG 机制，提供科学的防治建议
- **自进化能力**：支持增量学习和人机反馈，持续优化模型性能
- **实时检测**：基于 YOLOv8 的高效视觉检测，支持边缘端部署
- **友好交互**：提供 Gradio Web 界面和命令行接口

## 2. 系统架构

### 2.1 整体架构

```
IWDDA System
├── 感知层 (Perception Layer)
│   ├── VisionAgent (YOLOv8)     - 图像检测与定位
│   └── LanguageAgent (BERT)     - 文本语义理解
├── 认知层 (Cognition Layer)
│   ├── KnowledgeAgent (Neo4j)    - 知识图谱推理
│   └── FusionAgent              - 多模态融合决策
└── 行动层 (Action Layer)
    ├── ActiveLearner             - 反馈收集
    └── EvolutionEngine           - 增量训练
```

### 2.2 技术栈

| 模块 | 技术框架 | 用途 |
|------|---------|------|
| 视觉检测 | YOLOv8 (Ultralytics) | 目标检测与定位 |
| 文本理解 | Transformers (BERT) | 语义相似度计算 |
| 知识图谱 | Neo4j | 结构化知识存储与推理 |
| Web界面 | Gradio | 交互式诊断界面 |
| 深度学习 | PyTorch | 模型训练与推理 |

## 3. 项目结构

```
WheatAgent/
├── run_web.py                    # Web界面启动脚本
├── run_api.py                    # API服务启动脚本
├── configs/                      # 配置文件
│   ├── wheat_disease.yaml        # 数据集配置
│   └── training_params.yaml      # 训练参数配置
├── src/                          # 源代码
│   ├── vision/                   # 视觉感知模块
│   │   ├── vision_engine.py      # 视觉检测引擎
│   │   └── enhanced_yolo.py      # 增强型YOLO实现
│   ├── text/                     # 文本理解模块
│   │   └── text_engine.py        # 文本处理引擎
│   ├── graph/                    # 知识图谱模块
│   │   ├── graph_engine.py       # Neo4j交互引擎
│   │   └── knowledge_graph_builder.py # 知识图谱构建
│   ├── fusion/                   # 融合模块
│   │   └── fusion_engine.py      # 多模态融合引擎
│   ├── cognition/                # 认知模块
│   │   └── cognition_engine.py   # 认知推理引擎
│   ├── action/                   # 行动模块
│   │   ├── learner_engine.py     # 反馈收集引擎
│   │   └── evolve.py             # 增量训练引擎
│   ├── tools/                    # 工具模块
│   ├── utils/                    # 通用工具
│   └── web/                      # Web界面
│       └── app.py                # Gradio Web应用
├── datasets/                     # 数据集目录
├── models/                       # 模型权重目录
├── runs/                         # 训练输出目录
└── data/                         # 测试数据目录
```

## 4. 核心模块详解

### 4.1 视觉感知模块 (VisionAgent)

**主要职责**：负责小麦病害的图像检测与定位，支持17类小麦病害和虫害识别。

**核心类**：
- **VisionAgent**：视觉感知智能体，基于SerpensGate-YOLOv8实现
- **BBoxOptimizer**：边界框优化器，提供CIoU计算和细长病斑检测框优化

**关键功能**：
- 单图检测与批量检测
- 模型预热机制
- 推理缓存
- 边界框优化（针对细长病斑）
- 可视化结果生成

**使用示例**：
```python
from src.vision.vision_engine import VisionAgent

# 初始化视觉引擎
vision_agent = VisionAgent()

# 执行检测
results = vision_agent.detect(
    image_path="data/images/test_wheat.jpg",
    conf_threshold=0.25
)

# 检测并可视化
results, vis_path = vision_agent.detect_and_visualize(
    image_path="data/images/test_wheat.jpg"
)
```

### 4.2 文本理解模块 (LanguageAgent)

**主要职责**：处理用户输入的症状描述，进行语义理解和匹配。

**核心类**：
- **TextEngine**：文本处理引擎，基于BERT实现语义相似度计算

**关键功能**：
- 症状描述分析
- 多语言文本嵌入
- 语义相似度计算

### 4.3 知识图谱模块 (KnowledgeAgent)

**主要职责**：存储和管理农业知识，提供知识推理和查询功能。

**核心类**：
- **KnowledgeAgent**：知识图谱智能体，基于Neo4j实现
- **GraphRAGEngine**：GraphRAG推理引擎

**关键功能**：
- 病害信息查询
- 防治建议生成
- 多跳推理
- 知识图谱统计

### 4.4 融合模块 (FusionAgent)

**主要职责**：融合视觉、文本和知识图谱信息，做出最终诊断决策。

**核心类**：
- **FusionAgent**：多模态融合智能体
- **KADFormer**：知识感知扩散融合模型

**关键功能**：
- 多模态特征融合
- 决策级融合
- 置信度评估
- 推理过程生成

### 4.5 Web界面模块

**主要职责**：提供用户友好的Web交互界面。

**核心类**：
- **WheatAgentWebApp**：Web应用主类
- **LazyEngineManager**：懒加载引擎管理器
- **ConcurrencyManager**：并发控制管理器

**关键功能**：
- 图像上传与诊断
- 文本症状诊断
- 知识库查询
- 诊断历史记录
- 批量诊断
- 报告导出

## 5. 核心 API/类/函数

### 5.1 VisionAgent 类

**位置**：`src/vision/vision_engine.py`

**主要方法**：

| 方法名 | 描述 | 参数 | 返回值 |
|-------|------|------|-------|
| `__init__` | 初始化视觉感知智能体 | model_path: str, enable_cache: bool, enable_monitoring: bool, auto_warmup: bool, enable_bbox_optimization: bool, ciou_threshold: float | None |
| `detect` | 执行单图检测 | image_path: str, conf_threshold: float, iou_threshold: float, save_result: bool, use_cache: bool, optimize_bbox: bool | List[Dict[str, Any]] |
| `batch_detect` | 批量图像检测 | image_paths: List[str], conf_threshold: float, iou_threshold: float, batch_size: int, save_results: bool, optimize_bbox: bool | Dict[str, List[Dict[str, Any]]] |
| `detect_and_visualize` | 执行检测并生成可视化结果 | image_path: str, conf_threshold: float, iou_threshold: float, output_path: Optional[str] | Tuple[List[Dict[str, Any]], Optional[str]] |
| `warmup` | 模型预热 | num_runs: int | Dict[str, Any] |
| `get_performance_stats` | 获取性能统计信息 | None | Dict[str, Any] |

### 5.2 BBoxOptimizer 类

**位置**：`src/vision/vision_engine.py`

**主要方法**：

| 方法名 | 描述 | 参数 | 返回值 |
|-------|------|------|-------|
| `calculate_iou` | 计算两个边界框的IoU | box1: List[float], box2: List[float] | float |
| `calculate_ciou` | 计算CIoU (Complete Intersection over Union) | pred_box: List[float], true_box: List[float] | float |
| `is_elongated` | 判断是否为细长目标 | bbox: List[float] | bool |
| `optimize_elongated_bbox` | 优化细长目标边界框 | bbox: List[float], image_shape: Tuple[int, int], expand_ratio: float | List[float] |

### 5.3 WheatAgentWebApp 类

**位置**：`src/web/app.py`

**主要方法**：

| 方法名 | 描述 | 参数 | 返回值 |
|-------|------|------|-------|
| `__init__` | 初始化Web应用 | None | None |
| `diagnose_image` | 图像诊断 | image: Optional[np.ndarray], use_knowledge: bool, top_k: int, progress: gr.Progress | Tuple[str, Optional[Image.Image], str] |
| `diagnose_text` | 文本症状诊断 | text: str, use_knowledge: bool, top_k: int, progress: gr.Progress | Tuple[str, str] |
| `diagnose_batch` | 批量图像诊断 | images: List[np.ndarray], use_knowledge: bool, top_k: int, progress: gr.Progress | Tuple[str, str] |
| `get_disease_list` | 获取病害列表 | None | str |
| `get_disease_detail` | 获取病害详细信息 | disease_name: str | str |
| `export_report` | 导出诊断报告 | result_text: str, format_type: str | str |
| `get_knowledge_stats` | 获取知识图谱统计信息 | None | str |
| `get_system_status` | 获取系统状态 | None | str |

### 5.4 LazyEngineManager 类

**位置**：`src/web/app.py`

**主要方法**：

| 方法名 | 描述 | 参数 | 返回值 |
|-------|------|------|-------|
| `vision_engine` | 懒加载视觉引擎 | None | VisionEngine |
| `cognition_engine` | 懒加载认知引擎 | None | CognitionEngine |
| `graph_engine` | 懒加载知识图谱引擎 | None | GraphEngine |
| `fusion_engine` | 懒加载融合引擎 | None | FusionEngine |
| `preload_all_engines` | 后台预加载所有引擎 | None | None |
| `diagnose_image_parallel` | 并行诊断图像 | image_path: str, use_knowledge: bool, top_k: int | Dict |

## 6. 依赖关系

### 6.1 核心依赖

| 依赖 | 版本 | 用途 | 位置 |
|------|------|------|------|
| Python | 3.10+ | 运行环境 | 全局 |
| PyTorch | 1.10+ | 深度学习框架 | 全局 |
| Ultralytics | 最新版 | YOLOv8实现 | `src/vision/vision_engine.py` |
| Transformers | 最新版 | BERT模型 | `src/text/text_engine.py` |
| Neo4j | 5.x | 知识图谱数据库 | `src/graph/graph_engine.py` |
| Gradio | 最新版 | Web界面框架 | `src/web/app.py` |
| NumPy | 最新版 | 数值计算 | 全局 |
| PIL | 最新版 | 图像处理 | `src/vision/vision_engine.py` |
| Requests | 最新版 | HTTP请求 | `src/vision/vision_engine.py` |

### 6.2 模块依赖关系

```
Web界面 (app.py)
├── VisionAgent (视觉检测)
├── CognitionEngine (文本理解)
├── GraphEngine (知识图谱)
└── FusionAgent (多模态融合)

FusionAgent
├── VisionAgent
├── CognitionEngine
└── GraphEngine
```

## 7. 项目运行方式

### 7.1 环境准备

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置 Neo4j**
```bash
# 使用 Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/123456789s \
  neo4j:5.x
```

3. **准备数据集**
```
datasets/wheat_data/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### 7.2 启动 Web 界面

```bash
python run_web.py
```

访问 `http://localhost:7860` 开始使用

### 7.3 命令行使用

```python
from main import WheatDoctor

# 初始化诊断系统
doctor = WheatDoctor()

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

## 10. 配置说明

### 10.1 视觉模块配置 (configs/wheat_disease.yaml)

```yaml
# 数据集路径
path: ../datasets/wheat_data
train: images/train
val: images/val

# 类别定义
nc: 17  # 类别总数
names:
  0: 蚜虫 (Aphids)
  1: 螨虫 (Mites)
  # ... 其他类别

# 训练参数
box: 0.05   # 边框损失权重
cls: 0.5    # 分类损失权重
fliplr: 0.5 # 水平翻转增强
```

### 10.2 全局配置 (configs/config.yaml)

```yaml
# 项目信息
project:
  name: "WheatAgent"
  version: "0.1.0"

# 视觉模块
vision:
  model_name: "yolov8"
  confidence_threshold: 0.5
  device: "cuda"

# 知识图谱
graph:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "123456789s"
```

## 11. 部署方式

### 11.1 本地部署

1. 安装依赖
2. 启动 Neo4j 服务
3. 运行 `python run_web.py`

### 11.2 Docker 部署

使用项目根目录的 `docker-compose.yml` 文件：

```bash
docker-compose up -d
```

### 11.3 边缘设备部署

使用 `deploy/edge/deploy_edge.sh` 脚本：

```bash
bash deploy/edge/deploy_edge.sh
```

## 12. 开发与贡献

### 12.1 开发流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 12.2 代码规范

- 遵循 PEP 8 编码规范
- 使用类型提示
- 编写详细的文档字符串
- 添加单元测试

## 13. 故障排除

### 13.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| 模型加载失败 | 模型文件不存在或损坏 | 检查模型路径，重新下载模型 |
| Neo4j 连接失败 | 服务未启动或配置错误 | 检查 Neo4j 服务状态和配置 |
| 推理速度慢 | GPU 未启用或模型过大 | 启用 GPU 加速，使用量化模型 |
| 检测结果不准确 | 模型训练不足或参数设置不当 | 调整置信度阈值，使用更准确的模型 |

### 13.2 日志与监控

- 系统日志：`logs/` 目录
- 性能监控：通过 `PerformanceMonitor` 类
- 诊断历史：`logs/diagnosis_history.json`

## 14. 未来规划

1. **模型优化**：持续改进 YOLOv8 模型，提高检测精度和速度
2. **知识图谱扩展**：增加更多农业知识，支持更多作物和病害
3. **多语言支持**：扩展文本理解模块，支持多语言输入
4. **移动端应用**：开发移动应用，方便现场使用
5. **边缘计算**：优化模型，支持在资源受限设备上运行
6. **预测功能**：基于历史数据，预测病害发展趋势

## 15. 参考资料

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [Hugging Face Transformers](https://github.com/huggingface/transformers)
- [Neo4j](https://neo4j.com/)
- [Gradio](https://gradio.app/)
- [PyTorch](https://pytorch.org/)

## 16. 联系信息

- 项目主页: [https://github.com/your-repo/WheatAgent](https://github.com/your-repo/WheatAgent)
- 问题反馈: [Issues](https://github.com/your-repo/WheatAgent/issues)
- 邮箱: your-email@example.com

---

**WheatAgent - 基于多模态融合的小麦病害诊断智能体**

Made with ❤️ by IWDDA Team
