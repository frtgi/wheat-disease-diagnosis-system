# 🌾 基于多模态融合的小麦病害诊断系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)
![Vue3](https://img.shields.io/badge/Vue_3-3.5+-42b883.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8s-green.svg)
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008cc1.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Wheat Disease Diagnosis System based on Multimodal Fusion**

一个融合视觉感知、语义理解和知识推理的智能农业诊断系统

[功能特性](#-核心特性) • [快速开始](#-快速开始) • [系统架构](#-系统架构) • [文档](#-文档)

</div>

***

## 📖 项目简介

IWDDA（Intelligent Wheat Disease Diagnosis Agent）是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、大语言模型和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。

### 核心优势

- **多模态融合**：结合图像视觉特征、文本语义描述和结构化知识图谱，提高诊断准确性
- **智能推理**：基于知识图谱的 GraphRAG 机制，提供科学的防治建议
- **实时交互**：基于 SSE 流式推送的实时诊断进度，支持心跳保活和背压控制
- **高效检测**：基于 YOLOv8s 的 FP16 推理，支持 17 类小麦病害识别
- **安全可靠**：JWT 双令牌认证、XSS 防护、RBAC 权限控制、并发限流

## 🎯 核心特性

### 1. 视觉感知模块 (Vision Agent)

- 基于 **YOLOv8s** 的高精度目标检测（FP16 推理）
- 支持 **17类** 小麦病害和虫害识别
- 自动定位病灶区域并绘制可视化结果
- LRU 推理缓存（64 条）+ SHA-256 图像哈希匹配

### 2. 多模态理解模块 (Language Agent)

- 基于 **Qwen3-VL-2B-Instruct** 的图文联合理解（INT4 量化）
- 支持 Thinking 推理链模式，提供详细诊断依据
- 多语言文本嵌入与检索

### 3. 知识图谱模块 (Knowledge Agent)

- 基于 **Neo4j** 的农业知识图谱
- **GraphRAG** 知识检索增强生成机制
- **TransE** 知识嵌入 + 多跳推理
- 包含病害成因、预防措施、治疗药剂等完整知识体系

### 4. 多模态融合模块 (Fusion Agent)

- **KAD-Former** (Knowledge-Aware Diffusion Fusion) 融合策略
- 决策级融合：视觉主导 + 文本辅助 + 知识仲裁
- 提供详细的推理过程和置信度评估
- **FusionAnnotator** 知识增强标注 + ROI 可视化

### 5. Web 交互系统

- **Vue 3 + TypeScript + Element Plus** 前端界面
- **FastAPI** 后端服务，四层分离架构（API→Service→Core→Model）
- **SSE 流式响应**：实时诊断进度推送，6 种事件类型
- **JWT 双令牌认证**：Access 30min + Refresh 7days，Redis 黑名单
- **RBAC 权限控制**：farmer / technician / admin 三级角色

## 🏗️ 系统架构

```
IWDDA System
├── 交互层 (Interaction Layer)
│   ├── Vue3 Web 前端 (Element Plus + ECharts)
│   └── FastAPI REST API + SSE 流式推送
├── 感知层 (Perception Layer)
│   ├── VisionAgent (YOLOv8s FP16)   - 图像检测与定位
│   └── LanguageAgent (Qwen3-VL)     - 多模态语义理解
├── 认知层 (Cognition Layer)
│   ├── KnowledgeAgent (Neo4j+TransE) - 知识图谱推理
│   └── FusionAgent (KAD-Former)      - 多模态融合决策
└── 基础设施层 (Infrastructure Layer)
    ├── JWT双令牌认证 + RBAC权限
    ├── SSE流式推送 + 心跳保活
    ├── 并发限流 + GPU监控
    └── Redis缓存 + Token黑名单
```

### 技术栈

| 模块 | 技术框架 | 用途 |
|------|---------|------|
| 视觉检测 | YOLOv8s (Ultralytics) | 目标检测与定位（FP16） |
| 多模态理解 | Qwen3-VL-2B-Instruct (INT4) | 图文联合理解与推理 |
| 知识图谱 | Neo4j + TransE | 结构化知识存储与推理 |
| 知识增强 | GraphRAG | 知识检索增强生成 |
| 融合引擎 | KAD-Former | 多模态特征融合决策 |
| 后端框架 | FastAPI + SQLAlchemy | REST API + 异步ORM |
| 前端框架 | Vue 3 + TypeScript + Element Plus | Web 交互界面 |
| 数据可视化 | ECharts | 病害分布图表 |
| 数据库 | MySQL 8.0 + Redis 7.2 | 数据存储 + 缓存 |
| 认证安全 | JWT + bcrypt + SHA-256 | 双令牌认证 + 密码安全 |

## 🚀 快速开始

### 环境要求

- Python 3.10+（推荐使用 Conda）
- Node.js 18+（前端构建）
- MySQL 8.0+
- Redis 7.2+
- Neo4j 5.x
- NVIDIA GPU（推荐，CPU 可用 Mock 模式降级）

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/your-repo/WheatAgent.git
cd WheatAgent
```

2. **创建 Conda 虚拟环境**

```bash
conda create -n wheatagent-py310 python=3.10
conda activate wheatagent-py310
```

3. **安装后端依赖**

```bash
cd src/web/backend
pip install -r requirements.txt
```

4. **安装前端依赖**

```bash
cd src/web/frontend
npm install
```

5. **配置数据库**

启动 MySQL、Redis 和 Neo4j 服务，修改 `src/web/backend/app/core/config.py` 中的连接配置：

```python
DATABASE_URL = "mysql+pymysql://root:123456@127.0.0.1:3306/wheat_agent_db"
REDIS_URL = "redis://localhost:6379/0"
NEO4J_URI = "bolt://localhost:7687"
```

6. **启动后端服务**

```bash
cd src/web/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

7. **启动前端服务**

```bash
cd src/web/frontend
npm run dev
```

访问 `http://localhost:5173` 开始使用

### 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | v21test_admin | Test1234! |

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

## 📁 项目结构

```
WheatAgent/
├── src/                           # 核心源码
│   ├── web/                       # Web 前后端
│   │   ├── frontend/              # Vue3 前端
│   │   │   ├── src/
│   │   │   │   ├── api/           # API 接口层
│   │   │   │   ├── components/    # 组件（诊断/知识/仪表盘）
│   │   │   │   ├── views/         # 页面视图
│   │   │   │   ├── router/        # Vue Router 路由
│   │   │   │   ├── stores/        # Pinia 状态管理
│   │   │   │   ├── utils/         # 工具函数
│   │   │   │   └── types/         # TypeScript 类型
│   │   │   └── package.json
│   │   └── backend/               # FastAPI 后端
│   │       └── app/
│   │           ├── api/v1/        # API 路由层
│   │           ├── services/      # 业务服务层
│   │           ├── core/          # 核心组件层
│   │           ├── models/        # 数据模型层
│   │           ├── schemas/       # Pydantic 数据校验
│   │           └── utils/         # 工具函数
│   ├── vision/                    # 视觉引擎（YOLOv8增强）
│   ├── perception/                # 感知模块（YOLO/Qwen-VL）
│   ├── fusion/                    # 融合引擎（KAD-Former/GraphRAG）
│   ├── graph/                     # 图引擎（GNN/知识图谱）
│   ├── text/                      # 文本引擎（遗留，已被Qwen3-VL替代）
│   └── cognition/                 # 认知引擎
├── configs/                       # 训练与模型配置
├── scripts/                       # 工具脚本
├── deploy/                        # 部署配置
├── docs/                          # 项目文档
├── data/                          # 数据目录
└── runs/                          # 训练输出目录
```

## 🔧 配置说明

### 后端配置 (src/web/backend/app/core/config.py)

```python
# 数据库
DATABASE_URL = "mysql+pymysql://root:123456@127.0.0.1:3306/wheat_agent_db"
REDIS_URL = "redis://localhost:6379/0"
NEO4J_URI = "bolt://localhost:7687"

# JWT 认证
JWT_SECRET_KEY = "your-secret-key"
JWT_EXPIRE_HOURS = 0.5           # Access Token 30分钟
JWT_REFRESH_EXPIRE_DAYS = 7      # Refresh Token 7天

# SSE 流式配置
SSE_TIMEOUT_SECONDS = 120        # 连接超时
SSE_HEARTBEAT_INTERVAL = 15      # 心跳间隔
SSE_BACKPRESSURE_QUEUE_SIZE = 100 # 背压队列大小

# 并发控制
MAX_CONCURRENT_DIAGNOSIS = 3     # 最大并发诊断数
GPU_MEMORY_THRESHOLD = 0.9       # GPU 显存阈值
```

### 前端路由

| 路径 | 页面 | 认证 | 管理员 |
|------|------|------|--------|
| `/login` | 登录 | 否 | - |
| `/register` | 注册 | 否 | - |
| `/forgot-password` | 忘记密码 | 否 | - |
| `/dashboard` | 首页仪表盘 | 是 | - |
| `/diagnosis` | 病害诊断 | 是 | - |
| `/records` | 诊断记录 | 是 | - |
| `/knowledge` | 农业知识库 | 是 | - |
| `/user` | 用户中心 | 是 | - |
| `/sessions` | 会话管理 | 是 | - |
| `/admin` | 管理后台 | 是 | 是 |

## 🔒 安全设计

| 安全能力 | 实现方式 |
|---------|---------|
| JWT 双令牌 | Access 30min + Refresh 7days |
| Token 黑名单 | Redis Set + TTL 自动过期 |
| 密码安全 | bcrypt 哈希存储 + 72 字节截断 |
| 密码重置 | SHA-256 令牌哈希 + 1 小时有效期 |
| XSS 防护 | html.escape 转义 + CSP 安全头 + 用户名正则验证 |
| 开放重定向防护 | 登录 redirect 参数验证 |
| 速率限制 | SlowAPI 频率限流 |
| 并发限流 | DiagnosisRateLimiter（≤3 并发） |
| GPU 保护 | 显存≥90% 返回 503 |
| CORS | 可配置白名单 |
| 输入验证 | Pydantic V2 Schema 校验 |
| 账户锁定 | 连续 5 次失败锁定 30 分钟 |
| Cookie 安全 | httpOnly + secure + samesite=lax |

## 📈 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| YOLO 推理延迟 | ≤150ms | 225ms (CPU) |
| SSE 首事件延迟 | ≤500ms | 0.01ms |
| 完整诊断延迟 | ≤40s | 185.8ms (YOLO-only) |
| Qwen 显存占用 | ≤4GB | ~2.6GB (INT4) |
| 知识覆盖率 | ≥95% | 100% |

## 📚 文档

| 文档 | 路径 | 说明 |
|------|------|------|
| Web 架构设计 | [docs/architecture/WEB_ARCHITECTURE.md](docs/architecture/WEB_ARCHITECTURE.md) | 前后端架构详细设计 |
| Agent 架构设计 | [docs/architecture/AGENT_ARCHITECTURE.md](docs/architecture/AGENT_ARCHITECTURE.md) | 智能体架构与设计模式 |
| API 参考 | [docs/core/API_REFERENCE.md](docs/core/API_REFERENCE.md) | 完整 API 接口文档 |
| 部署指南 | [docs/core/DEPLOYMENT.md](docs/core/DEPLOYMENT.md) | 生产环境部署 |
| 用户指南 | [docs/core/USER_GUIDE.md](docs/core/USER_GUIDE.md) | 用户操作手册 |
| 测试指南 | [docs/guides/TEST_GUIDE.md](docs/guides/TEST_GUIDE.md) | 测试执行指导 |

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

- 项目主页: <https://github.com/your-repo/WheatAgent>
- 问题反馈: [Issues](https://github.com/your-repo/WheatAgent/issues)
- 邮箱: [2652218967@qq.com](mailto:2652218967@qq.com)

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 目标检测框架
- [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) - 多模态大语言模型
- [Neo4j](https://neo4j.com/) - 图数据库
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI 组件库

***

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐️ Star 支持一下！**

Made with ❤️ by IWDDA Team

</div>
