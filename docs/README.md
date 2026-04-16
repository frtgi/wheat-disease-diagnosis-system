# 基于多模态融合的小麦病害诊断系统 (WheatAgent)

> 🌾 基于 YOLOv8 视觉检测 × Qwen3-VL 多模态理解 × KAD-Former 特征融合 × GraphRAG 知识图谱增强的新一代小麦病害智能诊断平台
>
> ⭐ 架构成熟度 3.7/5 | 🧪 测试 1448+ | 📄 文档 15 | 🔌 API 45+

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)
![Vue](https://img.shields.io/badge/Vue.js-3.5+-41b883.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-V12.0-orange.svg)

---

## ✨ 核心特性

### 🎯 一键智能诊断

上传小麦病害照片，系统自动完成：

1. **视觉检测** — YOLOv8 识别 16 类常见小麦病害及病灶区域
2. **多模态理解** — Qwen3-VL 分析图像语义 + 用户描述的症状文本
3. **特征融合** — KAD-Former 跨注意力机制融合视觉与文本特征
4. **知识增强** — GraphRAG 检索农业知识图谱提供防治建议
5. **流式输出** — SSE 实时推送诊断进度，平均首事件延迟 <0.01ms

### 🏗️ 企业级架构

- 四层分离架构 (API → Service → Core → Model)
- Facade 门面模式解耦复杂融合流程
- JWT 双令牌认证 + 并发限流 + GPU 显存监控
- 异步全链路 (async/await) + 懒加载模型

### 📊 可观测性

- 9 项性能基准指标 (YOLO/SSE/Qwen/完整诊断)
- PipelineTimer 各阶段耗时可视化
- SSE 心跳保活 + 背压控制
- 操作审计日志完整记录

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐 conda wheatagent-py310 |
| MySQL | 8.0+ | wheat_agent_db |
| Redis | 7.0+ | 缓存 + Token 黑名单 |
| Neo4j | 5.x | 知识图谱 (可选) |
| Node.js | 18+ | 前端构建 |

### 三步启动

```bash
# Step 1: 克隆并进入项目
git clone <repo-url> && cd WheatAgent

# Step 2: 安装依赖
conda activate wheatagent-py310
pip install -r requirements.txt

# Step 3: 启动服务
cd src/web/backend
python -m uvicorn app.main:app --reload --port 8000
```

**首次访问**: http://localhost:8000/docs (API 文档) | http://localhost:8000 (前端)

---

## 🏛️ 技术架构概览

```
┌─────────────────────────────────────────────────────┐
│                    用户界面层                         │
│              Vue 3.5 + TypeScript 5.9               │
│         Element Plus 2.13 + ECharts 可视化          │
├─────────────────────────────────────────────────────┤
│                    API 路由层                        │
│   FastAPI + Pydantic V2 | 45+ REST 端点 | SSE 流式   │
│   认证(JWT) / 限流(SlowAPI) / 验证(Magic Number)    │
├───┬─────────┬─────────┬──────────┬──────────────────┤
│验 │  服务层  │  核心层  │  AI 模型  │    数据层        │
│证 │ Facade  │ Config  │ YOLOv8s  │  MySQL (12表)    │
│器 │ Feature │ Security│ Qwen3-VL  │  Redis (缓存)    │
│SSE │ Engine │ GPU Mon │ KAD-Former│  Neo4j (知识图谱)│
│流 │ Annotat │ Logger  │ GraphRAG  │                  │
└───┴─────────┴─────────┴──────────┴──────────────────┘
```

**架构亮点**:
- **四层分离**: API路由 → 业务服务 → 核心基础设施 → 数据模型
- **Facade模式**: FusionService 协调 FeatureExtractor→FusionEngine→ResultAnnotator 三阶段流水线
- **SSE流式**: 4种事件类型(Progress/Log/Heartbeat/StepIndicator)，15s心跳保活
- **懒加载**: Qwen3-VL模型按需加载，支持CPU Offload和Flash Attention优化

---

## 📁 功能模块一览

| 模块 | 功能 | 核心技术 | 状态 |
|------|------|----------|------|
| 视觉病害检测 | 16类病害识别 + ROI 定位 | YOLOv8s FP16 + LRU 缓存 | ✅ 生产就绪 |
| 多模态融合诊断 | 图像+文本联合推理 | KAD-Former 跨注意力 | ✅ 生产就绪 |
| 知识图谱增强 | 防治建议生成 | GraphRAG + TransE 嵌入 | ✅ 生产就绪 |
| SSE 流式响应 | 实时进度推送 | EventSource + 心跳保活 | ✅ 生产就绪 |
| 用户认证管理 | 注册/登录/JWT双Token | bcrypt + Redis 黑名单 | ✅ 生产就绪 |
| 诊断记录管理 | CRUD + 统计 + 报告 | SQLAlchemy 2.0 async | ✅ 生产就绪 |
| 批量诊断支持 | 多图并行处理 | 并发控制(≤3) + 队列(10) | ✅ 生产就绪 |
| 系统健康监控 | AI模型/GPU/DB状态 | nvidia-smi + 健康端点 | ✅ 生产就绪 |

**支持的病害类别** (16类):
条锈病、叶锈病、秆锈病、白粉病、赤霉病、壳针孢叶斑病、褐斑病、叶枯病、稻瘟病、蚜虫、螨虫、茎蝇、根腐病、黑粉病、健康植株

---

## 📚 文档导航

> 📁 **V12 整理后结构**: 15 个文件分布于 5 个子目录

### 📖 核心文档 (`core/`)

- [📘 用户操作手册](./core/USER_GUIDE.md) — 5 场景操作指南 + 20 FAQ + 50 术语
- [🚀 生产部署指南](./core/DEPLOYMENT.md) — 环境矩阵 + 30 项检查清单 + Gunicorn/Nginx 配置
- [📡 API 参考文档](./core/API_REFERENCE.md) — 60+ 端点 + 105 示例 + 错误码索引
- [🏛️ 技术白皮书](./core/PROJECT_DOCUMENTATION.md) — 9 章系统全景 + ER 图 + Facade 详解

### 🏗️ 架构设计 (`architecture/`)

- [🤖 智能体架构](./architecture/AGENT_ARCHITECTURE.md) — 四层分离架构 + 5种设计模式 + 诊断核心链路
- [🌐 Web 层架构](./architecture/WEB_ARCHITECTURE.md) — 前后端分离 + SSE流式 + JWT双令牌

### 🛠️ 操作指南 (`guides/`)

- [🧪 测试指南](./guides/TEST_GUIDE.md) — 单元/集成/基准测试完整流程
- [⚙️ 环境管理](./guides/ENVIRONMENT_MANAGEMENT.md) — conda/依赖/版本规范
- [🐳 云边部署](./guides/CLOUD_EDGE_DEPLOYMENT.md) — K8s/Docker 扩展部署方案
- [🔢 端口分配](./guides/PORT_ALLOCATION.md) — 服务端口规范化表

### 📊 历史报告 (`reports/`)

- [🕸️ KAD-Former+GraphRAG 架构详解](./reports/KAD_FORMER_GRAPHRAG_ARCHITECTURE_EXPLANATION.md) — 核心融合算法
- [🧠 多模块技术深度分析](./reports/MULTI_MODULE_TECHNICAL_ANALYSIS_REPORT.md) — 8 大模块剖析

### 🔧 参考资料 (`reference/`)

- [⚙️ 基础设施组件指南](./reference/INFRASTRUCTURE_COMPONENTS.md) — SSE + Redis + SlowAPI + GPU监控

### 📋 其他

- [🔄 变更日志](./CHANGELOG.md) — V3→V12 版本变更集中管理

---

## 🛠️ 技术栈详情

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **前端** | Vue 3.5 | 3.5+ | 渐进式框架 |
| | TypeScript | 5.9 | 类型安全 |
| | Element Plus | 2.13 | UI 组件库 |
| | ECharts | 5.x | 数据可视化 |
| **后端** | FastAPI | 0.110+ | 异步 Web 框架 |
| | Pydantic V2 | 2.x | 数据校验 |
| | SQLAlchemy | 2.0 (async) | ORM |
| **AI 视觉** | YOLOv8s | 8.x | 病害区域检测 |
| **AI 语言** | Qwen3-VL | 2B INT4 | 多模态理解 |
| **AI 融合** | KAD-Former | 自研 | 特征交叉注意力 |
| **知识图谱** | GraphRAG | - | Neo4j 知识增强 |
| **数据库** | MySQL | 8.0+ | 主存储 (12表) |
| | Redis | 7.0+ | 缓存/会话 |
| | Neo4j | 5.x | 知识图谱 (106实体,178三元组) |
| **存储** | MySQL | 8.0+ | 主存储 |
| **部署** | Docker | - | 容器化 |
| | Nginx | - | 反向代理 |

**代码规模**: ~20,200 行 Python / 96 个文件 / 最大单文件 1626 行

---

## 📈 项目历程

| 版本 | 日期 | 核心变更 | 评分 |
|------|------|----------|------|
| V3 | 2026-03 | 初始版本，基础功能 | 86.5 |
| V4 | 2026-04 | 大文件拆分、Facade 重构、安全修复 | 89.8 (+3.3) |
| V5 | 2026-04 | 异步迁移、类型注解100%、配置外部化 | 92.3 (+2.5) |
| V6 | 2026-04 | P0 修复、测试+107、文档28文件同步 | 93.6 (+1.3) |
| V7 | 2026-04 | 文档质量提升、专业性重构 | 94.0 |
| V8 | 2026-04 | 架构审计与文档精炼 | 94.0 |
| V9 | 2026-04 | 文档目录系统性整理与冗余清理(30→22文件) | 94.0 |
| V10 | 2026-04 | 前后端全系统完整测试(1102后端,99.4%通过) | - |
| V11 | 2026-04 | Web前端综合测试(346测试,98.8%通过) | - |
| **V12** | **2026-04** | **架构深度分析(3.7/5) + 文档V12对齐重写(22→15文件)** | **3.7/5** |

**关键里程碑**:
- ✅ God File 消除: `ai_diagnosis.py` 2202行 → 54行
- ✅ Facade 重构: `fusion_service.py` 拆分为 4 子模块
- ✅ 测试覆盖: 1448+ 测试用例 (V10后端1102 + V11前端346)
- ✅ 异步迁移: 全链路 async/await + SQLAlchemy 2.0 async
- ✅ 安全加固: JWT双Token + XSS防护 + CSP + 审计日志

---

## 🤝 贡献指南

欢迎 Issue 和 PR！详见 [贡献指南](./CONTRIBUTING.md)

**开发环境快速搭建**:

```bash
# 1. 创建并激活 conda 环境
conda create -n wheatagent-py310 python=3.10
conda activate wheatagent-py310

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填写数据库连接等配置

# 4. 初始化数据库
alembic upgrade head

# 5. 启动开发服务器
cd src/web/backend
python -m uvicorn app.main:app --reload --port 8000
```

## 📄 许可证

[MIT License](./LICENSE)

---

## 📊 项目统计

| 维度 | 数值 | 说明 |
|------|------|------|
| 架构成熟度 | **3.7/5** | Level 3 Defined (V12架构深度分析) |
| 测试用例 | **1448+** | V10后端1102(99.4%) + V11前端346(98.8%) |
| 文档数量 | **15 个** | V12整理后: 5子目录分类 (原22个) |
| API 端点 | **45+ 个** | 认证 + 诊断 + 知识库 + 监控 |
| 数据库表 | **5+ 张** | users + diagnoses + diagnosis_confidences + image_metadata + audit_logs |
| AI 模型 | **4 个** | YOLOv8s + Qwen3-VL-2B + KAD-Former + GraphRAG |
| 技术债务 | **19 项** | P1:4 + P2:12 + P3:3, 修复成本~50h |

---

> 🌾 **WheatAgent** — 让每一株小麦都能得到精准的诊断与呵护
>
> 📧 问题反馈: [GitHub Issues] | 💬 技术讨论: [Discussions]
>
> ⭐ 如果这个项目对您有帮助，请给一个 Star 支持一下！
