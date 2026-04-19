# 基于多模态融合的小麦病害诊断系统 - Web端架构设计文档

**版本**: V41.0
**更新日期**: 2026-04-20
**项目**: 基于多模态融合的小麦病害诊断系统
**基于**: V41 代码库实际状态

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
│ 管理后台 | 会话管理 | 知识库          │
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
- **RBAC权限控制**: farmer / technician / admin 三级角色
- **安全防护**: XSS防护、开放重定向防护、账户锁定、CSP安全头

---

## 2. Web 前端系统设计

前端主要负责用户交互、图像上传、诊断结果展示和数据可视化。

### 2.1 前端技术栈

| 技术 | 作用 | 版本 |
|------|------|------|
| Vue 3 | 前端框架 | ^3.5.25 |
| Element Plus | UI 组件库 | ^2.13.5 |
| Axios | API 通信 | ^1.13.6 |
| ECharts | 数据可视化 | ^6.0.0 |
| Vue Router | 页面路由 | ^5.0.3 |
| Pinia | 状态管理 | ^3.0.4 |
| TypeScript | 类型系统 | ~5.9.3 |
| Vite | 构建工具 | ^7.3.1 |
| Vitest | 单元测试 | ^2.0.0 |
| Playwright | E2E 测试 | ^1.59.1 |

### 2.2 前端页面结构

| 页面 | 路由 | 认证 | 管理员 | 核心功能 |
|------|------|------|--------|---------|
| 登录 | `/login` | 否 | - | JWT认证、开放重定向防护 |
| 注册 | `/register` | 否 | - | 用户注册 |
| 忘记密码 | `/forgot-password` | 否 | - | 密码重置流程 |
| 首页(Dashboard) | `/dashboard` | 是 | - | 系统介绍、病害统计、实时诊断数据 |
| 病害诊断 | `/diagnosis` | 是 | - | 上传图片、SSE实时进度、诊断结果展示 |
| 诊断记录 | `/records` | 是 | - | 历史记录、图像查看、统计图表 |
| 农业知识库 | `/knowledge` | 是 | - | 病害卡片、防治方法、知识图谱 |
| 用户中心 | `/user` | 是 | - | 个人信息、密码修改 |
| 会话管理 | `/sessions` | 是 | - | 活跃会话查看、远程终止 |
| 管理后台 | `/admin` | 是 | 是 | 系统概览、监控、日志、病害分布、AI模型管理 |

### 2.3 前端目录结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API 接口层
│   │   ├── admin.ts       # 管理员 API
│   │   ├── diagnosis.ts   # 诊断接口
│   │   ├── knowledge.ts   # 知识库接口
│   │   ├── report.ts      # 报告接口
│   │   ├── stats.ts       # 统计接口
│   │   └── user.ts        # 用户接口
│   ├── assets/            # 资源文件
│   ├── components/        # 公共组件
│   │   ├── common/
│   │   │   └── ErrorBoundary.vue    # 错误边界
│   │   ├── dashboard/
│   │   │   └── DiseaseChart.vue     # 病害图表
│   │   ├── diagnosis/              # 诊断组件组
│   │   │   ├── AnnotatedImage.vue   # 标注图像
│   │   │   ├── BatchDiagnosis.vue   # 批量诊断
│   │   │   ├── DiagnosisResult.vue  # 诊断结果
│   │   │   ├── FusionResult.vue     # 融合结果
│   │   │   ├── ImageUploader.vue    # 图片上传
│   │   │   ├── InferenceProgress.vue # 推理进度
│   │   │   └── MultiModalInput.vue  # 多模态输入
│   │   ├── knowledge/
│   │   │   └── DiseaseCard.vue      # 病害卡片
│   │   └── Layout.vue               # 布局组件
│   ├── views/             # 页面组件
│   │   ├── Admin.vue              # 管理后台
│   │   ├── Dashboard.vue          # 首页
│   │   ├── Diagnosis.vue          # 诊断页
│   │   ├── ForgotPassword.vue     # 忘记密码
│   │   ├── Knowledge.vue          # 知识库
│   │   ├── Login.vue              # 登录
│   │   ├── Records.vue            # 记录页
│   │   ├── Register.vue           # 注册
│   │   ├── Sessions.vue           # 会话管理
│   │   └── User.vue               # 用户中心
│   ├── router/            # 路由配置
│   │   └── index.ts
│   ├── stores/            # Pinia状态管理
│   │   └── index.ts             # Store入口(用户/诊断/知识)
│   ├── utils/             # 工具函数
│   │   ├── echarts.ts     # ECharts 配置
│   │   └── request.ts     # Axios 封装(拦截器/Token刷新)
│   ├── types/             # TypeScript 类型
│   │   └── index.ts
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 2.4 前端关键设计

#### 2.4.1 路由守卫

```typescript
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const hasUserInfo = (() => {
    try {
      const info = JSON.parse(localStorage.getItem('userInfo') || '{}')
      return !!info.id
    } catch { return false }
  })()
  const isAuthenticated = !!token && hasUserInfo
  const hasSession = hasUserInfo

  // 已认证用户访问登录/注册页 → 重定向到 /dashboard
  // 未认证用户访问需认证页面 → 重定向到 /login
  // 非管理员访问 /admin → 重定向到 /dashboard
})
```

#### 2.4.2 登录导航与开放重定向防护

```typescript
// Login.vue - 登录成功后导航
const redirect = (route.query.redirect as string) || '/dashboard'
if (redirect.startsWith('/') && !redirect.startsWith('//')) {
  await router.replace(redirect)
} else {
  await router.replace('/dashboard')
}
```

- 默认重定向从 `/` 改为 `/dashboard`，避免路由守卫竞态
- 使用 `router.replace` 替代 `router.push`，避免历史记录问题
- 验证 redirect 参数，防止开放重定向攻击（拒绝 `//evil.com` 等外部URL）

#### 2.4.3 Axios 响应拦截器

```typescript
// request.ts - 响应拦截器
response interceptor:
  - 自动解包 response.data（一层）
  - typeof res.code === 'number' 判断业务错误
  - Token 过期自动刷新（401 → /refresh → 重试原请求）
  - 刷新失败 → 清除认证状态 → 跳转 /login
```

#### 2.4.4 状态管理

```typescript
// stores/index.ts
isLoggedIn = computed(() => !!token.value || !!userInfo.value.id)
isAdmin = computed(() => userInfo.value.role === 'admin')
```

- `isLoggedIn` 同时检查 token 和 userInfo，兼容 httpOnly Cookie 认证
- Token 可能存储在 httpOnly Cookie 中，localStorage token 可能为空

#### 2.4.5 导航状态持久化

- **Layout.vue**: 使用 `<keep-alive :max="10">` 缓存页面组件
- **Admin.vue**: `activeTab` 从 URL query 参数同步，`onActivated` 时重新同步
- 管理后台 Tab 切换使用 `router.replace` 更新 URL 状态

---

## 3. 后端系统架构

后端采用**四层分离架构**（API→Service→Core→Model），层间接口契约明确。

### 3.1 后端技术栈

| 技术 | 作用 | 版本 |
|------|------|------|
| FastAPI | 后端 API 框架 | 0.109+ |
| Python | 编程语言 | 3.10+ |
| PyTorch | 深度学习框架 | 2.10+ |
| SQLAlchemy | ORM | 2.0+ (async) |
| Pydantic | 数据校验 | V2 |
| Redis | 缓存/黑名单 | 5.0+ |
| MySQL | 数据存储 | 8.0+ |
| Neo4j | 知识图谱 | 5.x |
| SlowAPI | 限流 | 0.1.9+ |

### 3.2 后端模块结构

```
src/web/backend/app/
├── api/                           # API 层 (路由 + 薄包装)
│   ├── v1/
│   │   ├── ai_diagnosis.py        # AI诊断主路由(SSE流式)
│   │   ├── diagnosis_router.py    # 诊断路由(11个AI诊断端点)
│   │   ├── diagnosis_validator.py # 请求验证器(文件/并发/Mock)
│   │   ├── sse_stream_manager.py  # SSE流管理(心跳/背压/超时)
│   │   ├── diagnosis.py           # 诊断记录CRUD
│   │   ├── user.py                # 用户接口(注册/登录/JWT/会话)
│   │   ├── knowledge.py           # 知识库接口(含图谱/统计)
│   │   ├── stats.py               # 统计接口(含显存管理)
│   │   ├── health.py              # 健康检查(分阶段启动)
│   │   ├── logs.py                # 日志接口(管理员)
│   │   ├── metrics.py             # Prometheus指标
│   │   ├── reports.py             # 报告生成(PDF/HTML)
│   │   └── upload.py              # 文件上传
│   ├── deps.py                    # 依赖注入
│   └── middleware.py              # 中间件
│
├── services/                      # Service 层 (业务逻辑)
│   ├── fusion_service.py          # 多模态融合门面 (Facade)
│   ├── fusion_feature_extractor.py# 特征提取器
│   ├── fusion_engine.py           # KAD-Former 融合引擎
│   ├── fusion_annotator.py        # 结果标注 + 知识增强
│   ├── kad_attention.py           # KAD 注意力模块
│   ├── qwen/                      # Qwen3-VL 子系统
│   │   ├── qwen_service.py        # Qwen Facade门面
│   │   ├── qwen_loader.py         # 模型加载器(Singleton+State)
│   │   ├── qwen_preprocessor.py   # 预处理
│   │   ├── qwen_inferencer.py     # 推理
│   │   └── qwen_postprocessor.py  # 后处理
│   ├── yolo_service.py            # YOLOv8 服务(FP16+LRU)
│   ├── graphrag_service.py        # GraphRAG 服务
│   ├── auth.py                    # 认证服务(SHA-256令牌哈希)
│   ├── user_service.py            # 用户服务
│   ├── knowledge.py               # 知识服务
│   ├── report_generator.py        # 报告生成(html.escape防XSS)
│   ├── cache.py                   # 缓存服务
│   ├── cache_manager.py           # 缓存管理器
│   ├── inference_cache_service.py # 推理缓存服务
│   ├── inference_queue.py         # 推理队列
│   ├── batch_processor.py         # 批处理器
│   ├── image_preprocessor.py      # 图像预处理
│   ├── model_manager.py           # 模型管理器
│   ├── vram_manager.py            # 显存管理器
│   ├── diagnosis_logger.py        # 诊断日志
│   └── ai_preloader.py            # AI服务预加载
│
├── core/                          # Core 层 (核心组件)
│   ├── security.py                # JWT双Token+bcrypt+黑名单+require_admin
│   ├── config.py                  # 配置管理(环境变量覆盖)
│   ├── database.py                # MySQL异步连接池
│   ├── redis_client.py            # Redis连接
│   ├── dependencies.py            # 依赖注入
│   ├── rate_limiter.py            # 并发限流器(≤3)
│   ├── gpu_monitor.py             # GPU显存监控
│   ├── error_codes.py             # 统一错误码(928行)
│   ├── exceptions.py              # 自定义异常(DEBUG隐藏traceback)
│   ├── response.py                # 统一响应封装
│   ├── startup_manager.py         # 分阶段启动管理
│   ├── logging_config.py          # 日志配置(JSON格式)
│   ├── metrics.py                 # 指标收集
│   ├── performance_config.py      # 性能配置
│   ├── query_monitor.py           # 查询监控
│   ├── index_optimizer.py         # 索引优化
│   ├── cache_decorators.py        # 缓存装饰器
│   ├── disease_knowledge.py       # 病害知识
│   ├── error_logger.py            # 错误日志
│   └── ai_config.py               # AI配置
│
├── models/                        # Model 层 (数据模型)
│   ├── user.py                    # 用户模型
│   ├── diagnosis.py               # 诊断记录 + 置信度
│   ├── image.py                   # 图像元数据
│   ├── knowledge.py               # 知识库模型
│   ├── disease.py                 # 病害模型
│   ├── audit.py                   # 审计日志
│   └── auth.py                    # 认证模型
│
├── schemas/                       # Pydantic 数据校验
│   ├── common.py                  # 通用Schema
│   ├── diagnosis.py               # 诊断Schema
│   ├── knowledge.py               # 知识库Schema
│   └── user.py                    # 用户Schema
│
├── monitoring/                    # 监控模块
│   └── monitoring_api.py          # 监控API
│
├── utils/                         # 工具函数
│   ├── xss_protection.py          # XSS防护(html.escape+装饰器+CSP)
│   ├── image_process.py           # 图像处理
│   └── logger.py                  # 日志工具
│
├── main.py                        # FastAPI主入口(435行)
└── rate_limiter.py                # 限流器
```

### 3.3 API 路由注册

```python
# main.py - 11个路由模块
app.include_router(user.router, ...)        # 用户认证
app.include_router(knowledge.router, ...)   # 知识库
app.include_router(stats.router, ...)       # 统计数据
app.include_router(health.router, ...)      # 健康检查
app.include_router(ai_diagnosis.router, ...) # AI诊断
app.include_router(metrics.router, ...)     # Prometheus指标
app.include_router(logs.router, ...)        # 日志查询(管理员)
app.include_router(reports.router, ...)     # 报告生成
app.include_router(upload.router, ...)      # 文件上传
app.include_router(monitoring_router, ...)  # 监控API
app.mount("/uploads", StaticFiles(...))     # 静态文件
```

### 3.4 API 接口设计

#### 3.4.1 用户接口

```python
POST /api/v1/users/register          # 用户注册 (公开, 3/min)
POST /api/v1/users/login             # 用户登录 → JWT双Token (公开, 5/min)
POST /api/v1/users/refresh           # 刷新Access Token (需认证)
POST /api/v1/users/logout            # 用户登出 → Token入黑名单 (需认证)
GET  /api/v1/users/me                # 获取当前用户信息 (需认证)
PUT  /api/v1/users/me                # 更新用户信息 (需认证)
PUT  /api/v1/users/password          # 修改密码 (需认证)
POST /api/v1/users/password/reset-request  # 请求密码重置 (公开)
POST /api/v1/users/password/reset    # 执行密码重置 (公开, SHA-256令牌)
GET  /api/v1/users/sessions          # 获取会话列表 (需认证)
DELETE /api/v1/users/sessions/{id}   # 终止指定会话 (需认证)
DELETE /api/v1/users/sessions        # 终止所有会话 (需认证)
GET  /api/v1/users/{user_id}         # 获取指定用户 (本人或管理员)
PUT  /api/v1/users/{user_id}         # 更新用户信息 (本人或管理员)
```

#### 3.4.2 诊断接口

```python
POST /api/v1/diagnosis/multimodal   # SSE流式多模态诊断
  Content-Type: multipart/form-data
  → Response: text/event-stream (SSE)
  → Events: start | steps | progress | heartbeat | log | complete | error

POST /api/v1/diagnosis/fusion       # 多模态融合诊断(非流式)
GET  /api/v1/diagnosis/fusion/stream # SSE流式融合诊断(URL模式)
POST /api/v1/diagnosis/fusion/stream # SSE流式融合诊断(上传模式)
POST /api/v1/diagnosis/image        # YOLOv8图像检测
POST /api/v1/diagnosis/text         # LLM纯文本诊断
POST /api/v1/diagnosis/batch        # 批量诊断(最多10张)
GET  /api/v1/diagnosis/records      # 诊断记录列表(分页)
GET  /api/v1/diagnosis/{id}         # 诊断详情
DELETE /api/v1/diagnosis/{id}       # 删除诊断记录
GET  /api/v1/diagnosis/health/ai    # AI服务健康检查
GET  /api/v1/diagnosis/cache/stats  # 缓存统计
POST /api/v1/diagnosis/cache/clear  # 清空缓存(管理员)
POST /api/v1/diagnosis/admin/ai/preload  # 预加载AI模型(管理员)
DELETE /api/v1/diagnosis/history/cleanup # 清理历史(管理员)
```

#### 3.4.3 知识库接口

```python
POST /api/v1/knowledge/             # 创建病害知识 (管理员)
GET  /api/v1/knowledge/search       # 搜索病害知识 (公开)
GET  /api/v1/knowledge/categories   # 获取分类列表 (公开)
GET  /api/v1/knowledge/graph        # 知识图谱数据 (需认证)
GET  /api/v1/knowledge/stats        # 知识库统计 (需认证)
GET  /api/v1/knowledge/{id}         # 获取病害详情 (公开)
PUT  /api/v1/knowledge/{id}         # 更新病害知识 (管理员)
DELETE /api/v1/knowledge/{id}       # 删除病害知识 (管理员)
```

#### 3.4.4 统计接口

```python
GET  /api/v1/stats/overview         # 概览统计 (需认证)
GET  /api/v1/stats/diagnoses        # 诊断统计 (需认证)
GET  /api/v1/stats/users            # 用户统计 (管理员)
GET  /api/v1/stats/cache            # 缓存统计 (需认证)
DELETE /api/v1/stats/cache          # 清空缓存 (管理员)
GET  /api/v1/stats/cache/info       # 缓存配置 (需认证)
GET  /api/v1/stats/vram             # 显存状态 (管理员)
POST /api/v1/stats/vram/cleanup     # 显存清理 (管理员)
```

#### 3.4.5 日志接口（全部管理员）

```python
GET    /api/v1/logs/                # 系统日志列表 (管理员)
GET    /api/v1/logs/{log_id}        # 日志详情 (管理员)
GET    /api/v1/logs/download/{filename} # 下载日志 (管理员)
DELETE /api/v1/logs/cleanup         # 清理日志 (管理员)
GET    /api/v1/logs/stats           # 日志统计 (管理员)
GET    /api/v1/logs/health          # 日志健康检查 (管理员)
GET    /api/v1/logs/statistics      # 诊断日志统计 (管理员, 60/min)
GET    /api/v1/logs/disease-distribution # 病害分布 (管理员, 60/min)
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
    "login_attempts": "login_attempts:{username}",   # 登录失败计数
    "password_reset": "password_reset:{token_hash}", # 密码重置令牌
}

CACHE_TTL = {
    "token_blacklist": 1800,              # 30分钟(Access Token有效期)
    "diagnosis_result": 3600 * 24 * 7,    # 7天
    "knowledge_disease": 3600 * 24 * 30,  # 30天
    "rate_limit": 60,                     # 60秒
    "concurrent_diagnosis": 300,          # 5分钟
    "login_attempts": 1800,               # 30分钟(账户锁定)
    "password_reset": 3600,               # 1小时
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
   ├── steps: {step_indicators} (仅首次)
   ├── progress: {step: "visual", progress: 25, message: "YOLOv8检测中..."}
   ├── heartbeat: (每15秒)
   ├── log: {level: "INFO", message: "检测到3个目标区域"}
   ├── progress: {step: "knowledge", progress: 45, message: "GraphRAG检索中..."}
   ├── progress: {step: "textual", progress: 60, message: "Qwen3-VL推理中..."}
   ├── progress: {step: "fusion", progress: 80, message: "KAD-Former融合中..."}
   ├── progress: {step: "complete", progress: 100, message: "诊断完成"}
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
| Access Token | 30分钟 | API请求认证 | 前端内存 + httpOnly Cookie |
| Refresh Token | 7天 | 刷新Access Token | httpOnly Cookie |

**RBAC权限控制**:

| 角色 | 权限范围 |
|------|---------|
| farmer | 诊断、查看记录、知识库 |
| technician | farmer + 统计分析 |
| admin | 全部 + 用户管理 + 系统配置 + 日志查看 + 缓存清理 |

**认证覆盖率**: 100%（所有业务端点均需认证，健康检查和知识搜索除外）

**授权检查模式**:
- **本人或管理员**: `get_user`、`update_user` 端点检查 `current_user.id != user_id and current_user.role != "admin"`
- **仅管理员**: `require_admin` 依赖项，检查 `current_user.role != "admin"` → 403

### 8.2 安全能力

| 安全能力 | 实现方式 | 代码位置 |
|---------|---------|---------|
| JWT双令牌 | Access 30min + Refresh 7days | core/security.py |
| Token黑名单 | Redis Set + TTL自动过期 | core/security.py |
| 密码安全 | bcrypt哈希存储 + 72字节截断 | core/security.py |
| 密码重置令牌 | SHA-256哈希 + 1小时有效期 + 一次性 | services/auth.py |
| XSS防护 | html.escape转义 + sanitize_response装饰器 | utils/xss_protection.py |
| 用户名验证 | 正则验证仅允许[a-zA-Z0-9_] | utils/xss_protection.py |
| 报告XSS | html.escape转义所有用户输入字段 | services/report_generator.py |
| 开放重定向防护 | 登录redirect参数验证(拒绝外部URL) | views/Login.vue |
| CSP安全头 | X-Content-Type-Options/X-Frame-Options/CSP等 | main.py中间件 |
| 速率限制 | SlowAPI频率限流 | main.py |
| 并发限流 | DiagnosisRateLimiter(≤3并发) | core/rate_limiter.py |
| GPU保护 | 显存≥90%返回503 | core/gpu_monitor.py |
| CORS | 可配置白名单 | main.py |
| 输入验证 | Pydantic V2 Schema校验 | schemas/ |
| 账户锁定 | 连续5次失败锁定30分钟 | services/auth.py |
| Cookie安全 | httpOnly + secure + samesite=lax | api/v1/user.py |
| 错误信息脱敏 | 非DEBUG模式隐藏traceback | core/exceptions.py |

### 8.3 限流配置

```python
RATE_LIMIT_CONFIG = {
    "default": "100/minute",
    "diagnosis": "20/minute",
    "upload": "10/minute",
    "auth": "5/minute",
    "register": "3/minute",
    "logs": "60/minute",
}

CONCURRENCY_CONFIG = {
    "max_concurrent_diagnosis": 3,
    "max_diagnosis_queue_size": 10,
    "gpu_memory_threshold": 0.9,
}
```

### 8.4 中间件链

```
请求进入
  ↓
[1] GZipMiddleware (minimum_size=1000)          # 响应压缩
  ↓
[2] CORSMiddleware                              # 跨域控制
  ↓
[3] request_id_middleware                       # X-Request-ID 追踪
  ↓
[4] add_security_headers                        # 安全头 (CSP/HSTS/XSS...)
  ↓
[5] retry_middleware                            # 自动重试 (3次, 指数退避)
  ↓
路由分发 → 处理函数
```

**安全头详情**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (生产环境)
- `Content-Security-Policy` (完整策略)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`

---

## 9. 性能优化

### 9.1 前端优化

- **懒加载**: 路由懒加载、图片懒加载
- **代码分割**: 按需加载模块
- **Gzip压缩**: 资源压缩传输
- **Keep-Alive**: Layout组件使用 `<keep-alive :max="10">` 缓存页面
- **导航状态持久化**: Admin Tab状态通过URL query同步

### 9.2 后端优化

- **异步处理**: FastAPI async接口 + asyncio
- **SSE流式**: 实时进度推送，避免轮询
- **推理缓存**: LRU缓存(64条) + SHA-256图像哈希
- **模型量化**: Qwen3-VL INT4 + YOLOv8s FP16
- **懒加载**: QwenModelLoader延迟初始化(Singleton+State模式)
- **GPU监控**: 显存过载自动降级
- **分阶段启动**: StartupManager管理启动顺序

### 9.3 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| YOLO推理延迟 | ≤150ms | 225ms (CPU) |
| SSE首事件延迟 | ≤500ms | 0.01ms |
| 完整诊断延迟 | ≤40s | 185.8ms (YOLO-only) |
| Qwen显存占用 | ≤4GB | ~2.6GB (INT4) |
| 知识覆盖率 | ≥95% | 100% |

---

## 10. 遗留组件说明

以下组件存在于代码库中但已被新技术替代，保留仅供参考：

| 组件 | 路径 | 状态 | 替代方案 |
|------|------|------|---------|
| Gradio Web界面 | `src/web/app.py` | 已弃用 | Vue3 Web前端 |
| BERT文本引擎 | `src/text/text_engine.py` | 已弃用 | Qwen3-VL多模态理解 |
| Celery任务队列 | `requirements.txt` | 已弃用 | 直接异步处理 |
| MinIO对象存储 | `requirements.txt` | 已弃用 | 本地文件存储 |

---

## 11. 相关文档

- [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) - 智能体架构设计
- [INFRASTRUCTURE_COMPONENTS.md](../reference/INFRASTRUCTURE_COMPONENTS.md) - 基础设施组件
- [API_REFERENCE.md](../core/API_REFERENCE.md) - API参考文档
- [DEPLOYMENT.md](../core/DEPLOYMENT.md) - 部署指南

---

*文档更新时间：2026-04-20*
*版本：V41.0 (基于V41代码库实际状态更新)*
