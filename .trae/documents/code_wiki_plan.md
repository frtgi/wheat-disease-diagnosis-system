# 小麦病害诊断系统 Code Wiki 文档

## 1. 仓库概览

IWDDA（Intelligent Wheat Disease Diagnosis Agent）是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、自然语言处理和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。

### 核心优势
- **多模态融合**：结合图像视觉特征、文本语义描述和结构化知识图谱，提高诊断准确性
- **智能推理**：基于知识图谱的 GraphRAG 机制，提供科学的防治建议
- **自进化能力**：支持增量学习和人机反馈，持续优化模型性能
- **实时检测**：基于 YOLOv8 的高效视觉检测，支持边缘端部署
- **友好交互**：提供 Web 界面和命令行接口

## 2. 目录结构

```
/├── .github/             # GitHub 配置文件
├── .trae/               # 项目配置和文档
├── configs/             # 配置文件目录
├── data/                # 数据目录
│   ├── case_records/    # 病例记录
│   └── followup_tasks/  # 后续任务
├── deploy/              # 部署相关文件
│   ├── edge/            # 边缘部署
│   ├── k8s/             # Kubernetes 部署
│   └── docker-compose.yml
├── docs/                # 项目文档
├── reports/             # 报告目录
├── runs/                # 训练输出目录
├── scripts/             # 脚本文件
│   ├── data/            # 数据处理脚本
│   ├── deploy/          # 部署脚本
│   ├── download/        # 模型下载脚本
│   ├── optimization/    # 优化脚本
│   ├── performance/     # 性能测试脚本
│   ├── setup/           # 环境设置脚本
│   ├── training/        # 训练脚本
│   └── utils/           # 工具脚本
├── src/                 # 源代码
│   ├── action/          # 行动模块
│   ├── api/             # API 模块
│   ├── cognition/       # 认知模块
│   ├── data/            # 数据模块
│   ├── database/        # 数据库模块
│   ├── deploy/          # 部署模块
│   ├── diagnosis/       # 诊断模块
│   ├── evaluation/      # 评估模块
│   ├── evolution/       # 进化模块
│   ├── fusion/          # 融合模块
│   ├── graph/           # 知识图谱模块
│   ├── input/           # 输入处理模块
│   ├── memory/          # 记忆模块
│   ├── perception/      # 感知模块
│   ├── planning/        # 规划模块
│   ├── tests/           # 测试模块
│   ├── text/            # 文本处理模块
│   ├── tools/           # 工具模块
│   ├── training/        # 训练模块
│   ├── utils/           # 工具库
│   ├── vision/          # 视觉模块
│   └── web/             # Web 界面
│       ├── backend/      # 后端 API
│       ├── frontend/     # 前端界面
│       └── tests/        # Web 测试
├── test_output/         # 测试输出
├── test_results/        # 测试结果
├── tests/               # 测试文件
├── README.md            # 项目说明
└── run_web.py           # 启动 Web 服务
```

## 3. 系统架构

### 分层架构

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

### 技术栈

| 模块 | 技术框架 | 用途 |
|------|---------|------|
| 视觉检测 | YOLOv8 (Ultralytics) | 目标检测与定位 |
| 文本理解 | Transformers (BERT) | 语义相似度计算 |
| 知识图谱 | Neo4j | 结构化知识存储与推理 |
| Web界面 | FastAPI + Vue.js | 交互式诊断界面 |
| 深度学习 | PyTorch | 模型训练与推理 |

## 4. 核心模块

### 4.1 视觉感知模块

**主要职责**：使用 YOLOv8 进行小麦病害的检测和定位，支持 17 类小麦病害和虫害识别。

**核心组件**：
- `YOLOEngine`：YOLOv8 引擎优化类，实现了注意力机制、多尺度特征提取和小目标检测优化
- `CBAM`：注意力模块，增强 ROI 定位精度
- `MultiScaleFeatureExtractor`：多尺度特征提取器，提升小病斑检测能力
- `SmallObjectDetectionHead`：小目标检测头，针对早期病斑进行优化

**关键功能**：
- 病斑区域检测与定位
- 多尺度特征提取
- 小目标（早期病斑）检测
- ROI 特征增强

### 4.2 多模态融合模块

**主要职责**：整合视觉特征、文本特征和知识图谱嵌入，进行多模态决策。

**核心组件**：
- `MultimodalFusionEngine`：多模态融合引擎，实现特征融合和决策生成
- 交叉注意力机制：实现不同模态间的信息交互
- 门控机制：动态调整各模态的贡献权重

**关键功能**：
- 多模态特征融合
- 模态权重动态调整
- 融合决策生成

### 4.3 知识图谱模块

**主要职责**：存储和管理农业知识，支持智能推理和防治建议生成。

**核心组件**：
- `GraphEngine`：知识图谱交互引擎
- `GraphRAGEngine`：基于知识图谱的检索增强生成
- `KnowledgeGraphBuilder`：知识图谱构建器

**关键功能**：
- 知识存储与管理
- 多跳推理
- 关联查询
- 防治建议生成

### 4.4 诊断模块

**主要职责**：整合各模块信息，生成最终诊断结果和防治建议。

**核心组件**：
- `DiagnosisEngine`：诊断引擎
- `ReportGenerator`：诊断报告生成器

**关键功能**：
- 综合诊断分析
- 置信度评估
- 详细报告生成
- 防治建议提供

### 4.5 Web 后端模块

**主要职责**：提供 RESTful API 接口，支持前端与后端服务的交互。

**核心组件**：
- FastAPI 应用
- 路由管理
- 中间件（CORS、安全头、请求重试等）
- 服务组件（YOLO 服务、Qwen 服务、GraphRAG 服务等）

**关键功能**：
- API 接口提供
- 服务状态管理
- 错误处理
- 性能监控

## 5. 核心 API/类/函数

### 5.1 YOLOEngine

**位置**：`src/perception/yolo_engine.py`

**功能**：YOLOv8 引擎优化类，实现小麦病害检测的完整优化方案。

**主要方法**：
- `detect(image_path, conf_threshold, iou_threshold, use_enhanced)`：执行病害检测
- `extract_roi_features(image, detections, feature_scale)`：提取 ROI 区域特征
- `extract_multi_scale_features(image)`：提取多尺度特征
- `detect_small_objects(image, conf_threshold)`：检测小目标病斑
- `get_enhanced_features(image_path)`：获取增强特征（用于融合）

### 5.2 MultimodalFusionEngine

**位置**：`src/fusion/fusion_engine.py`

**功能**：多模态融合引擎，整合视觉、文本和知识图谱特征。

**主要方法**：
- `fuse(vision_features, text_features, knowledge_embeddings)`：执行多模态特征融合
- `fuse_and_decide(vision_features, text_features, knowledge_embeddings, weights)`：融合特征并生成决策

### 5.3 FastAPI 应用

**位置**：`src/web/backend/app/main.py`

**功能**：创建和配置 FastAPI 应用实例，提供 RESTful API 接口。

**主要组件**：
- `create_application()`：创建 FastAPI 应用
- 中间件：请求 ID 追踪、安全头、请求重试
- 路由：用户、诊断、知识、统计、健康检查等
- 启动事件：服务初始化、模型加载、状态检查

### 5.4 诊断服务

**位置**：`src/web/backend/app/services/diagnosis.py`

**功能**：提供小麦病害诊断服务，整合多模态信息生成诊断结果。

**主要方法**：
- `run_diagnosis(image_path, user_text)`：执行完整诊断流程
- `generate_report(diagnosis_result)`：生成诊断报告
- `get_treatment_recommendations(disease_id)`：获取防治建议

## 6. 技术栈与依赖

### 6.1 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| PyTorch | 1.10+ | 深度学习框架 |
| Ultralytics YOLOv8 | - | 目标检测 |
| Transformers | - | 自然语言处理 |
| Neo4j | 5.x | 知识图谱数据库 |
| FastAPI | - | 后端 API 框架 |
| Vue.js | - | 前端框架 |
| NumPy | - | 数值计算 |
| PIL | - | 图像处理 |

### 6.2 环境配置

- **硬件要求**：
  - 8GB+ RAM (推荐 16GB)
  - GPU 支持（推荐，用于加速模型推理）
  - 10GB+ 磁盘空间

- **软件要求**：
  - Python 3.10+
  - CUDA 11.7+（如果使用 GPU）
  - Neo4j 5.x

## 7. 关键模块与典型用例

### 7.1 图像诊断

**功能说明**：通过上传小麦叶片图片，系统自动检测病灶区域并生成诊断结果。

**配置与依赖**：
- YOLOv8 模型权重
- 足够的 GPU 显存（推荐 8GB+）

**使用示例**：
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

### 7.2 知识问答

**功能说明**：基于知识图谱回答农业相关问题，如病害预防、治疗等。

**配置与依赖**：
- Neo4j 数据库连接
- 知识图谱数据

**使用示例**：
```python
from src.graph.graph_engine import GraphEngine

# 初始化知识图谱引擎
graph_engine = GraphEngine()

# 执行知识查询
result = graph_engine.query_knowledge(
    question="赤霉病怎么预防？"
)

# 查看结果
print(f"答案: {result['answer']}")
print(f"相关知识: {result['related_knowledge']}")
```

### 7.3 反馈学习

**功能说明**：收集用户反馈，用于系统的自进化和模型优化。

**配置与依赖**：
- 反馈数据存储
- 增量学习机制

**使用示例**：
```python
from src.action.learner_engine import LearnerEngine

# 初始化学习引擎
learner = LearnerEngine()

# 提交反馈
learner.submit_feedback(
    diagnosis_id="diagnosis_123",
    correct_disease="条锈病",
    user_notes="实际症状是叶片上的条纹状锈斑"
)

# 触发增量学习
learner.trigger_incremental_learning()
```

## 8. 配置、部署与开发

### 8.1 配置文件

**主要配置文件**：
- `configs/wheat_disease.yaml`：视觉模块配置
- `configs/config.yaml`：全局配置
- `src/web/backend/.env`：环境变量配置

**关键配置项**：
- 模型路径
- 数据库连接参数
- 服务端口
- GPU 设备设置

### 8.2 部署方式

**Docker 部署**：
```bash
docker-compose up -d
```

**Kubernetes 部署**：
```bash
kubectl apply -f deploy/k8s/
```

**边缘部署**：
```bash
bash deploy/edge/deploy_edge.sh
```

### 8.3 开发流程

1. **环境搭建**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **数据库初始化**：
   ```bash
   python src/database/init_db.py
   ```

3. **启动开发服务**：
   ```bash
   python run_web.py
   ```

4. **运行测试**：
   ```bash
   python run_tests.py
   ```

## 9. 监控与维护

### 9.1 监控指标

- **系统指标**：
  - API 响应时间
  - 模型推理速度
  - GPU 使用率
  - 内存使用情况

- **业务指标**：
  - 诊断准确率
  - 用户反馈率
  - 系统可用性

### 9.2 日志管理

- **日志级别**：DEBUG、INFO、WARNING、ERROR
- **日志存储**：本地文件 + 可选的日志聚合服务
- **日志轮转**：按大小和时间自动轮转

### 9.3 常见问题与解决方案

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 模型加载失败 | GPU 显存不足 | 减小批量大小或使用 CPU 模式 |
| 数据库连接失败 | Neo4j 服务未启动 | 检查 Neo4j 服务状态和连接参数 |
| 诊断结果不准确 | 模型未训练充分 | 增加训练数据或调整模型参数 |
| API 响应缓慢 | 并发请求过多 | 增加服务实例或优化代码 |

## 10. 总结与亮点回顾

IWDDA 项目是一个融合多模态技术的智能农业诊断系统，具有以下核心亮点：

1. **多模态融合**：创新性地整合视觉、文本和知识图谱信息，提高诊断准确性
2. **技术先进性**：采用 YOLOv8、BERT、Neo4j 等先进技术
3. **自进化能力**：支持增量学习和人机反馈，持续优化性能
4. **边缘部署支持**：针对资源受限环境进行优化
5. **完整的系统架构**：从感知到认知再到行动的完整闭环

该系统不仅为农业病害诊断提供了智能化解决方案，也为多模态融合技术在实际应用中的落地提供了参考。通过不断的迭代和优化，有望在农业生产中发挥更大的作用，帮助农民及时发现和防治小麦病害，提高农作物产量和质量。