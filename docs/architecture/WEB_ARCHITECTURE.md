# 基于多模态融合的小麦病害诊断系统 - Web端架构设计文档

**版本**: V12.0
**更新日期**: 2026-04-16
**项目**: 基于多模态融合的小麦病害诊断系统
**基于**: V12 架构深度分析报告

---

## 1. Web 系统总体架构设计

AI 农业诊断系统采用**前后端分离架构**，整体系统由用户交互层、业务服务层、AI决策层和数据层组成。

### 1.1 系统总体结构

```
┌──────────────────────────────────────┐
│              用户层                  │
│  农户 / 农技人员 / 管理员             │
└──────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│            Web 前端层                 │
│ Vue3 + Element Plus + ECharts       │
│ 图像上传 | 病害诊断 | 结果展示 | 历史记录 │
└──────────────────────────────────────┘
                │
         RESTful API + SSE
                │
                ▼
┌──────────────────────────────────────┐
│            后端服务层                │
│        FastAPI (四层分离)            │
│ API层→Service层→Core层→Model层      │
└──────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│         AI 决策层                    │
│ MultimodalFusionService (Facade)    │
│ YOLOv8s + Qwen3-VL + KAD-Former    │
│ + GraphRAG + Neo4j                  │
└──────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│             数据层                   │
│ MySQL / Redis / Neo4j              │
│ 用户数据 | 诊断记录 | 知识图谱        │
└──────────────────────────────────────┘
```

### 1.2 架构特点

- **前后端分离**: 前端负责展示和交互，后端负责业务逻辑和数据处理
- **四层分离**: API→Service→Core→Model，层间接口契约明确
- **SSE流式响应**: 实时进度推送，心跳保活，背压控制
- **多模态融合**: YOLOv8s + Qwen3-VL + KAD-Former + GraphRAG联合诊断
- **JWT双令牌**: Access 30min + Refresh 7days，Redis黑名单

---

## 2. Web 前端系统设计

前端主要负责用户交互、图像上传、诊断结果展示和数据可视化。

### 2.1 前端技术栈

| 技术 | 作用 | 版本 |
|------|------|------|
| Vue 3 | 前端框架 | ^3.5 |
| Element Plus | UI 组件库 | ^2.13.5 |
| Axios | API 通信 | 1.6+ |
| ECharts | 数据可视化 | 5.x |
| Vue Router | 页面路由 | ^4.x |
| Pinia | 状态管理 | ^3.0.4 |
| TypeScript | 类型系统 | ~5.9 |
| Vite | 构建工具 | ^7.3.1 |

### 2.2 前端页面结构

| 页面 | 路由 | 核心功能 |
|------|------|---------|
| 首页(Dashboard) | `/dashboard` | 系统介绍、病害统计、实时诊断数据 |
| 病害诊断 | `/diagnosis` | 上传图片、SSE实时进度、诊断结果展示 |
| 诊断记录 | `/records` | 历史记录、图像查看、统计图表 |
| 农业知识库 | `/knowledge` | 病害卡片、防治方法、生长阶段 |
| 用户管理 | `/user` | 注册登录、JWT认证、角色权限 |

### 2.3 前端目录结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── assets/            # 资源文件
│   ├── components/        # 公共组件
│   │   ├── ImageUploader.vue    # 图像上传组件
│   │   ├── DiagnosisResult.vue  # 诊断结果组件
│   │   ├── DiseaseCard.vue      # 病害卡片组件
│   │   └── ChartPanel.vue       # 图表面板组件
│   ├── views/             # 页面组件
│   │   ├── Dashboard.vue        # 首页
│   │   ├── Diagnosis.vue        # 诊断页
│   │   ├── Records.vue          # 记录页
│   │   ├── Knowledge.vue        # 知识库
│   │   └── User.vue             # 用户页
│   ├── router/            # 路由配置
│   │   └── index.ts
│   ├── stores/            # Pinia状态管理
│   │   ├── index.ts             # Store入口
│   │   ├── user.ts              # 用户状态
│   │   ├── diagnosis.ts         # 诊断状态
│   │   └── knowledge.ts         # 知识库状态
│   ├── api/               # API 接口
│   │   ├── request.ts     # Axios 封装
│   │   ├── diagnosis.ts   # 诊断接口
│   │   ├── user.ts        # 用户接口
│   │   └── knowledge.ts   # 知识库接口
│   ├── utils/             # 工具函数
│   │   ├── image.ts       # 图像处理
│   │   ├── format.ts      # 格式化
│   │   └── validate.ts    # 验证
│   ├── types/             # TypeScript 类型
│   │   ├── diagnosis.ts
│   │   ├── user.ts
│   │   └── common.ts
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 3. 后端系统架构

后端采用**四层分离架构**（API→Service→Core→Model），层间接口契约明确。

### 3.1 后端技术栈

| 技术 | 作用 | 版本 |
|------|------|------|
| FastAPI | 后端 API 框架 | 0.110+ |
| Python | 编程语言 | 3.10+ |
| PyTorch | 深度学习框架 | 2.10+ |
| SQLAlchemy | ORM | 2.0+ (async) |
| Pydantic | 数据校验 | V2 |
| Redis | 缓存/黑名单 | 7.2+ |
| MySQL | 数据存储 | 8.0+ |
| Neo4j | 知识图谱 | 5.x |

### 3.2 后端模块结构

```
src/web/backend/app/
├── api/                           # API 层 (路由 + 薄包装)
│   ├── v1/
│   │   ├── ai_diagnosis.py        # AI诊断主路由(SSE流式)
│   │   ├── diagnosis.py           # 诊断记录CRUD
│   │   ├── user.py                # 用户接口
│   │   ├── knowledge.py           # 知识库接口
│   │   ├── stats.py               # 统计接口
│   │   └── health.py              # 健康检查
│   ├── deps.py                    # 依赖注入
│   └── middleware.py              # 中间件
│
├── services/                      # Service 层 (业务逻辑)
│   ├── fusion_service.py          # 多模态融合门面 (Facade)
│   ├── fusion_feature_extractor.py# 特征提取器
│   ├── fusion_engine.py           # KAD-Former 融合引擎
│   ├── fusion_annotator.py        # 结果标注 + 知识增强
│   ├── qwen/                      # Qwen3-VL 子系统
│   │   ├── qwen_service.py        # Qwen Facade门面
│   │   ├── qwen_loader.py         # 模型加载器(Singleton+State)
│   │   ├── qwen_preprocessor.py   # 预处理
│   │   ├── qwen_inferencer.py     # 推理
│   │   └── qwen_postprocessor.py  # 后处理
│   ├── yolo_service.py            # YOLOv8 服务(FP16+LRU)
│   ├── graphrag_service.py        # GraphRAG 服务
│   ├── user_service.py            # 用户服务
│   └── knowledge_service.py       # 知识服务
│
├── core/                          # Core 层 (核心组件)
│   ├── security.py                # JWT双Token认证(30min/7d)
│   ├── config.py                  # 配置管理
│   ├── rate_limiter.py            # 并发限流器(≤3)
│   ├── gpu_monitor.py             # GPU显存监控
│   └── error_codes.py             # 统一错误码
│
├── models/                        # Model 层 (数据模型)
│   ├── user.py                    # 用户模型
│   ├── diagnosis.py               # 诊断记录 + 置信度
│   ├── image_metadata.py          # 图像元数据
│   └── audit_log.py               # 审计日志
│
├── database/                      # 数据库层
│   ├── mysql.py                   # MySQL 异步连接
│   └── redis.py                   # Redis 连接
│
└── utils/                         # 工具函数
    ├── xss_protection.py          # XSS防护
    ├── image_process.py           # 图像处理
    └── logger.py                  # 日志工具
```

### 3.3 API 接口设计

#### 3.3.1 用户接口

```python
POST /api/v1/user/register          # 用户注册
POST /api/v1/user/login             # 用户登录 → JWT双Token
POST /api/v1/user/refresh           # 刷新Access Token
GET  /api/v1/user/me                # 获取当前用户信息
PUT  /api/v1/user/me                # 更新用户信息
PUT  /api/v1/user/password          # 修改密码
```

#### 3.3.2 诊断接口

```python
POST /api/v1/diagnosis/multimodal   # SSE流式多模态诊断
  Content-Type: multipart/form-data
  → Response: text/event-stream (SSE)
  → Events: start | progress | heartbeat | log | step_indicator | complete | error

GET  /api/v1/diagnosis/records      # 诊断记录列表(分页)
GET  /api/v1/diagnosis/{id}         # 诊断详情
DELETE /api/v1/diagnosis/{id}       # 删除诊断记录
GET  /api/v1/diagnosis/stats        # 诊断统计
```

#### 3.3.3 知识库接口

```python
GET  /api/v1/knowledge/diseases     # 病害列表
GET  /api/v1/knowledge/diseases/{id}# 病害详情
GET  /api/v1/knowledge/search       # 搜索病害
```

---

## 4. AI 模型服务架构

### 4.1 模型组成

| 模型 | 用途 | 量化方式 | 显存占用 |
|------|------|---------|---------|
| YOLOv8s | 目标检测(17类病害) | FP16 | ~50MB |
| Qwen3-VL-2B-Instruct | 多模态理解 | INT4 | ~2.6GB |
| KAD-Former | 多模态融合 | FP32 | ~200MB |
| TransE | 知识嵌入 | FP32 | ~10MB |

### 4.2 处理流程

```
图像输入 + 症状描述
   │
   ▼
YOLOv8s 目标检测 (FP16)
   │ → DetectionResult(boxes, classes, scores)
   ▼
Qwen3-VL 多模态理解 (INT4)
   │ → AnalysisResult(disease_name, reasoning)
   ▼
GraphRAG 知识检索 (Neo4j + TransE)
   │ → KnowledgeContext(triples, embeddings)
   ▼
KAD-Former 多模态融合
   │ → FusionResult(disease, confidence, severity)
   ▼
FusionAnnotator 知识增强标注
   │ → 诊断报告(含防治建议、知识链接)
   ▼
SSE流式推送 → 前端实时渲染
```

### 4.3 输出结果

```json
{
    "disease_name": "小麦条锈病",
    "confidence": 0.95,
    "severity": "中度",
    "all_confidences": [
        {"disease": "小麦条锈病", "confidence": 0.95},
        {"disease": "小麦叶锈病", "confidence": 0.03}
    ],
    "description": "叶片出现黄色条纹状病斑...",
    "recommendations": [
        "选用抗病品种",
        "适时喷洒三唑酮可湿性粉剂",
        "加强田间管理"
    ],
    "knowledge_links": [
        {"entity": "条锈病", "relation": "CAUSED_BY", "target": "条形柄锈菌"}
    ],
    "annotated_image": "data:image/jpeg;base64,..."
}
```

---

## 5. 数据库设计

### 5.1 用户表

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    role ENUM('farmer', 'technician', 'admin') DEFAULT 'farmer',
    nickname VARCHAR(50),
    avatar VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.2 诊断记录表

```sql
CREATE TABLE diagnoses (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    disease_name VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    severity VARCHAR(20),
    description TEXT,
    recommendations JSON,
    growth_stage VARCHAR(50),
    location VARCHAR(100),
    model_version VARCHAR(50),
    inference_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_disease_name (disease_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.3 诊断置信度表

```sql
CREATE TABLE diagnosis_confidences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    diagnosis_id BIGINT NOT NULL,
    disease_name VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    rank_order INT NOT NULL,
    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE,
    INDEX idx_diagnosis_id (diagnosis_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.4 图像元数据表

```sql
CREATE TABLE image_metadata (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    diagnosis_id BIGINT NOT NULL,
    original_filename VARCHAR(255),
    file_size INT,
    width INT,
    height INT,
    format VARCHAR(20),
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.5 审计日志表

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.6 Redis 缓存设计

```python
CACHE_KEYS = {
    "token_blacklist": "blacklist:token:{jti}",     # JWT黑名单
    "diagnosis_result": "diagnosis:{image_hash}",    # 诊断结果缓存
    "knowledge_disease": "knowledge:disease:{id}",   # 病害知识缓存
    "rate_limit": "rate_limit:{ip}:{endpoint}",      # 限流计数
    "concurrent_diagnosis": "concurrent:diagnosis",  # 并发诊断计数
}

CACHE_TTL = {
    "token_blacklist": 1800,              # 30分钟(Access Token有效期)
    "diagnosis_result": 3600 * 24 * 7,    # 7天
    "knowledge_disease": 3600 * 24 * 30,  # 30天
    "rate_limit": 60,                     # 60秒
    "concurrent_diagnosis": 300,          # 5分钟
}
```

---

## 6. 系统数据流程

### 6.1 SSE流式诊断流程

```
1. 用户在前端上传图片 + 症状描述
   ↓
2. 前端调用 POST /api/v1/diagnosis/multimodal
   ↓
3. 后端接收请求 → JWT认证 → 并发限流检查 → GPU显存检查
   ↓
4. 创建SSE连接 → 返回 text/event-stream
   ↓
5. SSE事件推送:
   ├── start: {diagnosis_id}
   ├── progress: {step: "visual", progress: 100, message: "检测完成"}
   ├── heartbeat: (每15秒)
   ├── progress: {step: "cognition", progress: 100, message: "分析完成"}
   ├── progress: {step: "knowledge", progress: 100, message: "知识检索完成"}
   ├── progress: {step: "fusion", progress: 100, message: "融合完成"}
   └── complete: {data: {完整诊断结果}}
   ↓
6. 前端EventSource接收事件 → 实时更新UI
   ↓
7. 诊断结果持久化到MySQL
```

### 6.2 前后端交互时序图

```
┌──────┐    ┌──────────┐   ┌──────────┐  ┌───────────┐ ┌──────────┐ ┌──────┐ ┌──────┐
│ 用户  │    │ Vue3 前端 │   │FastAPI   │  │FusionService││ YOLOv8   ││ Qwen ││ Neo4j│
│      │    │          │   │ API层    │  │            │ │         ││ -VL  ││      │
└──┬───┘    └────┬─────┘   └────┬─────┘  └─────┬─────┘ └────┬────┘└──┬───┘└──┬───┘
   │             │              │               │            │        │       │
   │ ① 上传图像   │              │               │            │        │       │
   │────────────►│              │               │            │        │       │
   │             │ ② POST SSE   │               │            │        │       │
   │             │─────────────►│               │            │        │       │
   │             │              │ ③ JWT+限流检查  │            │        │       │
   │             │ ④ SSE: start │               │            │        │       │
   │             │◄─────────────│               │            │        │       │
   │             │              │ ⑤ diagnose_   │            │        │       │
   │             │              │    async()    │            │        │       │
   │             │              │──────────────►│            │        │       │
   │             │              │               │⑥ YOLO检测  │        │       │
   │             │ SSE:progress │               │───────────►│        │       │
   │             │◄─────────────│               │            │        │       │
   │             │              │               │⑦ Qwen分析  │        │       │
   │             │ SSE:progress │               │────────────────────►│       │
   │             │◄─────────────│               │            │        │       │
   │             │              │               │⑧ GraphRAG  │        │       │
   │             │ SSE:progress │               │────────────────────────────►│
   │             │◄─────────────│               │            │        │       │
   │             │              │               │⑨ KAD融合   │        │       │
   │             │              │               │◄───────────┼────────┼───────│
   │             │ SSE:complete │               │            │        │       │
   │             │◄─────────────│               │            │        │       │
   │ ⑩ 展示结果  │              │               │            │        │       │
   │◄────────────│              │               │            │        │       │
```

---

## 7. 系统部署架构

### 7.1 开发环境部署

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  backend:
    build: ./src/web/backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@mysql:3306/wheat_agent
      - REDIS_URL=redis://redis:6379/0
      - NEO4J_URI=bolt://neo4j:7687
    depends_on:
      - mysql
      - redis
      - neo4j
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]

  frontend:
    build: ./src/web/frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: wheat_agent

  redis:
    image: redis:7.2
    ports:
      - "6379:6379"

  neo4j:
    image: neo4j:5.x
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password
```

### 7.2 生产环境部署

```
用户浏览器
     │
     ▼
  Nginx 反向代理
     │
     ├── / → Vue3 静态资源
     └── /api → FastAPI 后端
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    MySQL 主库   Redis      Neo4j
         │        (单机)     (单机)
         ▼
    MySQL 从库(可选)
```

---

## 8. 安全设计

### 8.1 认证与授权

**JWT双令牌认证机制**:

| 令牌类型 | 有效期 | 用途 | 存储 |
|----------|--------|------|------|
| Access Token | 30分钟 | API请求认证 | 前端内存 |
| Refresh Token | 7天 | 刷新Access Token | HttpOnly Cookie |

**RBAC权限控制**:

| 角色 | 权限范围 |
|------|---------|
| farmer | 诊断、查看记录、知识库 |
| technician | farmer + 统计分析 |
| admin | 全部 + 用户管理 + 系统配置 |

**认证覆盖率**: 100%（所有业务端点均需认证，健康检查除外）

### 8.2 安全能力

| 安全能力 | 实现方式 |
|---------|---------|
| JWT双令牌 | Access 30min + Refresh 7days |
| Token黑名单 | Redis Set + TTL自动过期 |
| 密码安全 | bcrypt哈希存储 |
| XSS防护 | 输入净化 + 输出转义 |
| 速率限制 | SlowAPI频率限流 |
| 并发限流 | DiagnosisRateLimiter(≤3并发) |
| GPU保护 | 显存≥90%返回503 |
| CORS | 可配置白名单 |
| 输入验证 | Pydantic V2 Schema校验 |

### 8.3 限流配置

```python
RATE_LIMIT_CONFIG = {
    "default": "100/minute",
    "diagnosis": "20/minute",
    "upload": "10/minute",
    "auth": "5/minute",
}

CONCURRENCY_CONFIG = {
    "max_concurrent_diagnosis": 3,
    "max_diagnosis_queue_size": 10,
    "gpu_memory_threshold": 0.9,
}
```

---

## 9. 性能优化

### 9.1 前端优化

- **懒加载**: 路由懒加载、图片懒加载
- **代码分割**: 按需加载模块
- **Gzip压缩**: 资源压缩传输
- **缓存策略**: 浏览器缓存 + Service Worker

### 9.2 后端优化

- **异步处理**: FastAPI async接口 + asyncio
- **SSE流式**: 实时进度推送，避免轮询
- **推理缓存**: LRU缓存(64条) + 图像哈希
- **模型量化**: Qwen3-VL INT4 + YOLOv8s FP16
- **懒加载**: QwenModelLoader延迟初始化
- **GPU监控**: 显存过载自动降级

### 9.3 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| YOLO推理延迟 | ≤150ms | 225ms (CPU) |
| SSE首事件延迟 | ≤500ms | 0.01ms |
| 完整诊断延迟 | ≤40s | 185.8ms (YOLO-only) |
| Qwen显存占用 | ≤4GB | ~2.6GB (INT4) |
| 知识覆盖率 | ≥95% | 100% |

---

## 10. 相关文档

- [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) - 智能体架构设计
- [INFRASTRUCTURE_COMPONENTS.md](../reference/INFRASTRUCTURE_COMPONENTS.md) - 基础设施组件
- [API_REFERENCE.md](../core/API_REFERENCE.md) - API参考文档
- [DEPLOYMENT.md](../core/DEPLOYMENT.md) - 部署指南

---

*文档更新时间：2026-04-16*
*版本：V12.0 (基于V12架构深度分析报告重写)*
