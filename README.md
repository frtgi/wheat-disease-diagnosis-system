# 🌾 基于多模态融合的小麦病害诊断系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-1.10+-orange.svg)
![YOLO](https://img.shields.io/badge/YOLOv8-green.svg)
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008cc1.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Wheat Disease Diagnosis System based on Multimodal Fusion**

一个融合视觉感知、语义理解和知识推理的智能农业诊断系统

[功能特性](#-核心特性) • [快速开始](#-快速开始) • [系统架构](#-系统架构) • [文档](#-文档)

</div>

---

## 📖 项目简介

IWDDA（Intelligent Wheat Disease Diagnosis Agent）是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、自然语言处理和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。

### 核心优势

- **多模态融合**：结合图像视觉特征、文本语义描述和结构化知识图谱，提高诊断准确性
- **智能推理**：基于知识图谱的 GraphRAG 机制，提供科学的防治建议
- **自进化能力**：支持增量学习和人机反馈，持续优化模型性能
- **实时检测**：基于 YOLOv8 的高效视觉检测，支持边缘端部署
- **友好交互**：提供 Gradio Web 界面和命令行接口

## 🎯 核心特性

### 1. 视觉感知模块 (Vision Agent)
- 基于 **YOLOv8** 的高精度目标检测
- 支持 **17类** 小麦病害和虫害识别
- 自动定位病灶区域并绘制可视化结果
- 支持自定义模型权重加载

### 2. 文本理解模块 (Language Agent)
- 基于 **BERT** 的语义相似度计算
- 支持用户症状描述的智能匹配
- 多语言文本嵌入与检索

### 3. 知识图谱模块 (Knowledge Agent)
- 基于 **Neo4j** 的农业知识图谱
- 包含病害成因、预防措施、治疗药剂等完整知识体系
- 支持多跳推理和关联查询

### 4. 多模态融合模块 (Fusion Agent)
- **KAD-Fusion** (Knowledge-Aware Diffusion Fusion) 融合策略
- 决策级融合：视觉主导 + 文本辅助 + 知识仲裁
- 提供详细的推理过程和置信度评估

### 5. 自进化模块 (Active Learner)
- 用户反馈收集与困难样本挖掘
- 增量学习支持，避免灾难性遗忘
- 自动数据闭环处理

## 🏗️ 系统架构

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
| Web界面 | Gradio | 交互式诊断界面 |
| 深度学习 | PyTorch | 模型训练与推理 |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- PyTorch 1.10+ (推荐使用 CUDA 支持)
- Neo4j 5.x
- 8GB+ RAM (推荐 16GB)

### 安装步骤

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
python app.py
```

访问 `http://localhost:7860` 开始使用

### 命令行使用

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

## 📊 支持的病害类别

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

## 🎓 使用示例

### 示例 1: 图像诊断

上传一张小麦叶片图片，系统将：
1. 自动检测病灶区域
2. 分析视觉特征
3. 结合用户描述
4. 查询知识图谱
5. 生成诊断报告和防治建议

### 示例 2: 知识问答

在"专家咨询"标签页中，可以询问：
- "赤霉病怎么预防？"
- "条锈病的成因是什么？"
- "白粉病用什么药？"

系统将基于知识图谱提供专业答案。

### 示例 3: 反馈学习

如果系统诊断有误，用户可以：
1. 提供正确的诊断结果
2. 添加备注说明
3. 系统自动收集反馈数据
4. 用于下一轮增量训练

## 📈 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| mAP@0.5 | > 95% | 视觉检测准确率 |
| CIoU | > 0.85 | 边界框定位精度 |
| 语义相似度 | > 0.85 | 文本理解准确率 |
| 推理速度 | > 30 FPS | 实时检测能力 |

## 📁 项目结构

```
WheatAgent/
├── main.py                    # 主程序入口
├── app.py                     # Gradio Web 界面
├── configs/                   # 配置文件
│   ├── config.yaml            # 全局配置
│   └── wheat_disease.yaml     # 数据集配置
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
│   ├── action/               # 行动模块
│   │   ├── learner_engine.py # 反馈收集引擎
│   │   └── evolve.py        # 增量训练引擎
│   └── tools/               # 工具模块
│       ├── label_generator.py # 标注生成工具
│       └── data_converter.py # 数据转换工具
├── datasets/                 # 数据集目录
│   ├── wheat_data/          # 小麦病害数据集
│   └── feedback_data/       # 用户反馈数据
├── runs/                    # 训练输出目录
├── models/                   # 模型权重目录
└── data/                    # 数据目录
    ├── images/              # 测试图片
    └── texts/              # 文本数据
```

## 🔧 配置说明

### 视觉模块配置 (configs/wheat_disease.yaml)

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

### 全局配置 (configs/config.yaml)

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

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- 项目主页: [https://github.com/your-repo/WheatAgent](https://github.com/your-repo/WheatAgent)
- 问题反馈: [Issues](https://github.com/your-repo/WheatAgent/issues)
- 邮箱: your-email@example.com

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 目标检测框架
- [Hugging Face Transformers](https://github.com/huggingface/transformers) - 自然语言处理工具
- [Neo4j](https://neo4j.com/) - 图数据库
- [Gradio](https://gradio.app/) - Web 界面框架

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐️ Star 支持一下！**

Made with ❤️ by IWDDA Team

</div>
