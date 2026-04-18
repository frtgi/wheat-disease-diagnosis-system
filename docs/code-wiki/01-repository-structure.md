# 仓库结构分析

## 项目目录结构

项目是一个小麦病害诊断系统，包含多个模块和组件。以下是主要目录结构：

```
├── .github/              # GitHub 配置文件
├── .trae/                # Trae 工具相关文件
├── configs/              # 配置文件
├── data/                 # 数据文件
│   ├── case_records/     # 病例记录
│   └── followup_tasks/   # 后续任务
├── deploy/               # 部署相关文件
│   ├── edge/             # 边缘部署
│   ├── k8s/              # Kubernetes 部署
│   └── docker-compose.yml # Docker 部署配置
├── docs/                 # 文档
├── reports/              # 报告文件
├── runs/                 # 运行结果
├── scripts/              # 脚本文件
│   ├── data/             # 数据处理脚本
│   ├── deploy/           # 部署脚本
│   ├── download/         # 下载脚本
│   ├── optimization/     # 优化脚本
│   ├── performance/      # 性能测试脚本
│   ├── setup/            # 环境设置脚本
│   ├── training/         # 训练脚本
│   └── utils/            # 工具脚本
├── src/                  # 源代码
│   ├── action/           # 动作模块
│   ├── api/              # API 模块
│   ├── cognition/        # 认知模块
│   ├── data/             # 数据模块
│   ├── database/         # 数据库模块
│   ├── deploy/           # 部署模块
│   ├── diagnosis/        # 诊断模块
│   ├── evaluation/       # 评估模块
│   ├── evolution/        # 进化模块
│   ├── fusion/           # 融合模块
│   ├── graph/            # 图模块
│   ├── input/            # 输入模块
│   ├── memory/           # 记忆模块
│   ├── perception/       # 感知模块
│   ├── planning/         # 规划模块
│   ├── tests/            # 测试模块
│   ├── text/             # 文本模块
│   ├── tools/            # 工具模块
│   ├── training/         # 训练模块
│   ├── utils/            # 工具函数
│   ├── vision/           # 视觉模块
│   └── web/              # Web 模块
│       ├── backend/      # 后端
│       ├── frontend/     # 前端
│       └── tests/        # Web 测试
├── test_output/          # 测试输出
├── test_results/         # 测试结果
├── tests/                # 测试文件
└── README.md             # 项目说明
```

## 目录结构说明

### 核心目录

1. **src/** - 源代码目录，包含所有核心功能模块：
   - **action/**: 处理系统动作和反馈
   - **api/**: API 接口实现
   - **cognition/**: 认知引擎，处理文本和推理
   - **data/**: 数据处理和增强
   - **diagnosis/**: 病害诊断核心逻辑
   - **fusion/**: 多模态融合模块
   - **graph/**: 知识图谱相关功能
   - **perception/**: 感知模块，包含视觉识别
   - **vision/**: 视觉处理模块，包含 YOLO 模型
   - **web/**: Web 界面实现

2. **configs/** - 配置文件目录：
   - 包含模型训练参数、系统配置等

3. **data/** - 数据目录：
   - 存储病例记录和后续任务数据

4. **scripts/** - 脚本目录：
   - 包含各种工具脚本，如数据处理、模型训练、部署等

5. **deploy/** - 部署目录：
   - 包含边缘部署、Kubernetes 部署和 Docker 部署配置

6. **tests/** - 测试目录：
   - 包含单元测试、集成测试和性能测试

### 辅助目录

1. **docs/** - 文档目录：
   - 包含架构文档、API 参考、部署指南等

2. **reports/** - 报告目录：
   - 存储性能报告和分析结果

3. **runs/** - 运行结果目录：
   - 存储模型检测结果和评估指标

4. **test_output/** - 测试输出目录：
   - 存储测试过程中生成的输出文件

5. **test_results/** - 测试结果目录：
   - 存储测试结果和性能数据

## 项目组织方式

项目采用模块化设计，各模块之间职责清晰：

1. **分层架构**：
   - 感知层：处理输入数据（图像、文本等）
   - 认知层：进行推理和决策
   - 融合层：整合多模态信息
   - 应用层：提供 API 和 Web 界面

2. **数据流**：
   - 输入数据 → 感知处理 → 多模态融合 → 诊断推理 → 结果输出

3. **扩展点**：
   - 模型训练和优化
   - 知识图谱扩展
   - 边缘部署支持

## 技术栈

- **后端**：Python，FastAPI
- **前端**：Vue.js，TypeScript
- **数据库**：Neo4j（知识图谱）
- **机器学习**：PyTorch，YOLOv8
- **部署**：Docker，Kubernetes
