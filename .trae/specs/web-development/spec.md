# Web 端开发规格文档

## Why

基于已完成的 Web 架构设计文档（`WEB_ARCHITECTURE.md`），需要搭建完整的 Web 应用系统，包括 Vue3 前端和 FastAPI 后端，实现用户认证、病害诊断、诊断记录管理等核心功能，为农户和农技人员提供便捷的 AI 诊断服务。

## What Changes

- **新增 Vue3 前端项目**: 基于 Vue 3 + Element Plus + TypeScript 的前端应用
- **新增 FastAPI 后端项目**: 基于 FastAPI + Python 3.10 的后端服务
- **新增数据库设计**: MySQL 8.0 数据库表结构和初始化数据
- **新增用户认证模块**: JWT Token 认证和 RBAC 权限管理
- **新增诊断功能模块**: 图像上传、AI 诊断、结果展示
- **新增知识库模块**: 病害知识展示和查询
- **新增数据可视化**: ECharts 图表展示诊断统计

## Impact

- **Affected specs**: 
  - 智能体架构（六层智能体集成）
  - 多模态融合架构（图像 + 文本处理）
  - 云边部署架构（云端和边缘端部署）
  
- **Affected code**:
  - 前端：`src/web/vue-app/` (新建)
  - 后端：`src/web/backend/` (新建)
  - 数据库：`src/database/` (新建)
  - 现有 AI 引擎集成：`src/cognition/`, `src/vision/`, `src/fusion/`

## ADDED Requirements

### Requirement: Vue3 前端系统
The system SHALL provide a Vue 3 based frontend application with Element Plus UI components.

#### Scenario: 用户访问诊断页面
- **WHEN** 用户访问 `/diagnosis` 页面
- **THEN** 系统展示图像上传组件，支持拖拽和点击上传
- **THEN** 系统展示诊断结果展示区域，包括病害名称、置信度、防治建议

### Requirement: FastAPI 后端系统
The system SHALL provide a FastAPI based backend service with RESTful API endpoints.

#### Scenario: 用户进行图像诊断
- **WHEN** 用户上传图像并调用 `POST /api/v1/diagnosis/image`
- **THEN** 后端验证用户身份（JWT Token）
- **THEN** 后端调用 AI Agent 进行诊断
- **THEN** 后端返回诊断结果并保存到数据库

### Requirement: 用户认证系统
The system SHALL provide JWT-based authentication with RBAC permission control.

#### Scenario: 用户登录
- **WHEN** 用户提交用户名和密码
- **THEN** 系统验证凭据
- **THEN** 系统返回 JWT Token（24 小时有效期）
- **THEN** 后续请求携带 Token 进行认证

### Requirement: 数据库系统
The system SHALL provide MySQL database with tables for users, diseases, diagnosis records, and knowledge graph.

#### Scenario: 保存诊断记录
- **WHEN** 诊断完成
- **THEN** 系统保存诊断记录到 `diagnosis_records` 表
- **THEN** 系统关联用户 ID 和图像 URL
- **THEN** 系统记录病害名称、置信度、防治建议

### Requirement: 数据可视化
The system SHALL provide ECharts-based dashboards for diagnosis statistics.

#### Scenario: 查看 Dashboard
- **WHEN** 用户访问 `/dashboard` 页面
- **THEN** 系统展示病害统计图表（饼图/柱状图）
- **THEN** 系统展示最近诊断记录列表
- **THEN** 系统展示诊断趋势图（折线图）

## MODIFIED Requirements

### Requirement: AI Agent 集成
The system SHALL integrate existing AI Agent (YOLOv8 + Qwen3-VL-4B-Instruct + Fusion Engine).

**修改说明**: 将现有的命令行/Gradio 接口改为 RESTful API 接口，支持 Web 前端调用。

```python
# 原接口：直接调用引擎
# 新接口：POST /api/v1/diagnosis/image
# 请求：FormData (image, symptoms)
# 响应：JSON (diagnosis_id, disease_name, confidence, recommendations)
```

## REMOVED Requirements

### Requirement: Gradio 单页面应用
**Reason**: 被完整的 Vue3 + FastAPI 前后端分离架构替代
**Migration**: Gradio 应用保留作为开发测试工具，生产环境使用 Vue3 前端

---

## 技术规格详情

### 1. 前端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| Vue 3 | 3.4+ | 前端框架 |
| Element Plus | 2.5+ | UI 组件库 |
| TypeScript | 5.3+ | 类型系统 |
| Axios | 1.6+ | API 通信 |
| ECharts | 5.4+ | 数据可视化 |
| Vue Router | 4.2+ | 页面路由 |
| Pinia | 2.1+ | 状态管理 |
| Vite | 5.0+ | 构建工具 |

### 2. 后端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| FastAPI | 0.109+ | API 框架 |
| Python | 3.10+ | 编程语言 |
| PyTorch | 2.10+ | 深度学习 |
| MySQL | 8.0+ | 关系数据库 |
| Redis | 7.2+ | 缓存 |
| MinIO | 2024+ | 对象存储 |
| Celery | 5.3+ | 异步任务 |
| JWT | 2.8+ | 认证 |

### 3. 数据库表结构

#### 3.1 users 表
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('farmer', 'technician', 'admin') DEFAULT 'farmer',
    phone VARCHAR(20),
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3.2 diseases 表
```sql
CREATE TABLE diseases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(100),
    category ENUM('fungal', 'bacterial', 'viral', 'pest', 'nutritional') NOT NULL,
    symptoms TEXT NOT NULL,
    description TEXT,
    prevention_methods JSON,
    treatment_methods JSON,
    suitable_growth_stage VARCHAR(100),
    image_urls JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3.3 diagnosis_records 表
```sql
CREATE TABLE diagnosis_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    disease_name VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    severity VARCHAR(20),
    description TEXT,
    recommendations JSON,
    growth_stage VARCHAR(50),
    weather_data JSON,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3.4 knowledge_graph 表
```sql
CREATE TABLE knowledge_graph (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    entity VARCHAR(100) NOT NULL,
    entity_type ENUM('disease', 'symptom', 'pest', 'treatment', 'growth_stage') NOT NULL,
    relation VARCHAR(100),
    target_entity VARCHAR(100),
    attributes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity),
    INDEX idx_entity_type (entity_type),
    INDEX idx_relation (relation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 4. API 接口设计

#### 4.1 用户接口
```
POST   /api/v1/user/register      # 用户注册
POST   /api/v1/user/login         # 用户登录
GET    /api/v1/user/me            # 获取当前用户信息
PUT    /api/v1/user/me            # 更新当前用户信息
POST   /api/v1/user/logout        # 用户登出
```

#### 4.2 诊断接口
```
POST   /api/v1/diagnosis/image    # 图像诊断（上传图像）
POST   /api/v1/diagnosis/text     # 文本症状诊断
GET    /api/v1/diagnosis/records  # 获取诊断历史
GET    /api/v1/diagnosis/{id}     # 获取诊断详情
GET    /api/v1/diagnosis/{id}/export  # 导出诊断报告
DELETE /api/v1/diagnosis/{id}     # 删除诊断记录
```

#### 4.3 知识库接口
```
GET    /api/v1/knowledge/diseases      # 获取病害列表
GET    /api/v1/knowledge/diseases/{id} # 获取病害详情
GET    /api/v1/knowledge/search        # 搜索病害知识
GET    /api/v1/knowledge/categories    # 获取病害分类
```

#### 4.4 统计接口
```
GET    /api/v1/stats/overview     # 获取统计概览
GET    /api/v1/stats/trends       # 获取诊断趋势
GET    /api/v1/stats/diseases     # 获取病害分布
```

### 5. 前端页面设计

#### 5.1 页面路由
```
/dashboard          # 首页仪表盘
/diagnosis          # 病害诊断页面
/records            # 诊断记录页面
/knowledge          # 农业知识库页面
/knowledge/:id      # 病害详情页
/user               # 用户中心页面
/login              # 登录页面
/register           # 注册页面
```

#### 5.2 核心组件
```
components/
├── common/
│   ├── Header.vue          # 顶部导航栏
│   ├── Sidebar.vue         # 侧边栏
│   ├── Footer.vue          # 页脚
│   └── Loading.vue         # 加载动画
├── diagnosis/
│   ├── ImageUploader.vue   # 图像上传组件
│   ├── DiagnosisResult.vue # 诊断结果展示
│   └── SymptomInput.vue    # 症状输入组件
├── dashboard/
│   ├── DiseaseChart.vue    # 病害统计图表
│   ├── TrendChart.vue      # 诊断趋势图
│   └── RecentRecords.vue   # 最近诊断记录
└── knowledge/
    ├── DiseaseCard.vue     # 病害卡片
    └── SearchBox.vue       # 搜索框
```

### 6. 安全设计

#### 6.1 JWT 认证
```python
JWT_CONFIG = {
    "secret_key": "your-secret-key",  # 从环境变量读取
    "algorithm": "HS256",
    "expire_minutes": 1440,  # 24 小时
}
```

#### 6.2 限流配置
```python
RATE_LIMIT_CONFIG = {
    "default": "100/minute",
    "diagnosis": "20/minute",
    "upload": "10/minute",
    "auth": "5/minute",
}
```

#### 6.3 CORS 配置
```python
CORS_CONFIG = {
    "allow_origins": ["http://localhost:5173", "https://your-domain.com"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
```

### 7. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 页面加载时间 | < 2s | 首屏加载 |
| API 响应时间 | < 500ms | 平均响应 |
| 诊断响应时间 | < 5s | 包含 AI 推理 |
| 并发用户数 | > 1000 | 同时在线 |
| 系统可用性 | > 99.9% | SLA 保证 |

---

## 项目目录结构

```
WheatAgent/
├── src/
│   ├── web/
│   │   ├── frontend/              # Vue3 前端项目
│   │   │   ├── public/
│   │   │   ├── src/
│   │   │   │   ├── assets/        # 静态资源
│   │   │   │   ├── components/    # Vue 组件
│   │   │   │   ├── views/         # 页面视图
│   │   │   │   ├── router/        # 路由配置
│   │   │   │   ├── stores/        # Pinia 状态管理
│   │   │   │   ├── utils/         # 工具函数
│   │   │   │   ├── types/         # TypeScript 类型
│   │   │   │   ├── App.vue
│   │   │   │   └── main.ts
│   │   │   ├── package.json
│   │   │   ├── tsconfig.json
│   │   │   └── vite.config.ts
│   │   │
│   │   └── backend/               # FastAPI 后端项目
│   │       ├── app/
│   │       │   ├── api/           # API 路由
│   │       │   │   ├── v1/
│   │       │   │   │   ├── user.py
│   │       │   │   │   ├── diagnosis.py
│   │       │   │   │   ├── knowledge.py
│   │       │   │   │   └── stats.py
│   │       │   ├── core/          # 核心配置
│   │       │   │   ├── config.py
│   │       │   │   ├── security.py
│   │       │   │   └── database.py
│   │       │   ├── models/        # 数据模型
│   │       │   │   ├── user.py
│   │       │   │   ├── disease.py
│   │       │   │   └── diagnosis.py
│   │       │   ├── schemas/       # Pydantic 模式
│   │       │   │   ├── user.py
│   │       │   │   ├── diagnosis.py
│   │       │   │   └── knowledge.py
│   │       │   ├── services/      # 业务逻辑
│   │       │   │   ├── auth.py
│   │       │   │   ├── diagnosis.py
│   │       │   │   └── knowledge.py
│   │       │   ├── utils/         # 工具函数
│   │       │   └── main.py
│   │       ├── tests/             # 测试
│   │       ├── requirements.txt
│   │       └── .env.example
│   │
│   └── database/                  # 数据库脚本
│       ├── migrations/            # 数据库迁移
│       ├── seeds/                 # 种子数据
│       └── init.sql               # 初始化 SQL
│
├── docs/
│   ├── WEB_ARCHITECTURE.md        # Web 架构设计
│   └── WEB_ARCHITECTURE_REPORT.md # 完成报告
│
└── .trae/
    └── specs/
        └── web-development/
            ├── spec.md
            ├── tasks.md
            └── checklist.md
```
