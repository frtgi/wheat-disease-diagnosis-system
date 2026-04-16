# Web 端前后端集成开发规格文档

## Why

基于已完成的 Web 架构设计和前后端框架搭建，需要进行前后端集成联调，实现完整的系统功能，包括数据库初始化、AI 引擎集成、接口对接、系统测试和运行验证。

## What Changes

- **新增数据库连接配置**: 配置 MySQL 数据库连接（127.0.0.1:3306, root/123456）
- **新增 AI 引擎集成**: 集成现有的 YOLOv8、Qwen3-VL-4B-Instruct、Fusion 引擎
- **新增诊断功能接口**: 实现完整的图像诊断流程
- **新增前后端联调**: 测试所有 API 接口和前端页面
- **新增系统运行脚本**: 创建一键启动脚本
- **新增集成测试**: 端到端功能测试

## Impact

- **Affected specs**: 
  - Web 开发规格（web-development）
  - 智能体架构（AI 引擎集成）
  - 多模态融合架构（诊断流程）
  
- **Affected code**:
  - 后端：`src/web/backend/app/services/diagnosis.py`（集成 AI 引擎）
  - 后端：`src/web/backend/app/api/v1/diagnosis.py`（诊断 API）
  - 前端：`src/web/frontend/src/views/Diagnosis.vue`（对接后端 API）
  - 数据库：`src/database/init.sql`（数据库初始化）
  - 配置：`src/web/backend/.env`（数据库连接配置）

## ADDED Requirements

### Requirement: 数据库连接和初始化
The system SHALL connect to MySQL database at 127.0.0.1:3306 with root/123456 credentials and initialize all tables.

#### Scenario: 数据库初始化成功
- **WHEN** 系统首次启动
- **THEN** 自动连接 MySQL 数据库（127.0.0.1:3306）
- **THEN** 使用 root 用户和密码 123456 认证
- **THEN** 创建 wheat_agent_db 数据库
- **THEN** 创建所有表结构（users, diseases, diagnosis_records, knowledge_graph）
- **THEN** 插入测试数据（至少 5 种病害、5 个用户）

### Requirement: AI 引擎集成
The system SHALL integrate existing AI engines (YOLOv8, Qwen3-VL-4B-Instruct, Fusion Engine) for diagnosis.

#### Scenario: 图像诊断流程
- **WHEN** 用户上传小麦病害图像
- **THEN** 后端调用 YOLOv8 进行视觉检测
- **THEN** 后端调用 Qwen3-VL-4B-Instruct 进行认知分析
- **THEN** 后端调用 Fusion Engine 进行多模态融合
- **THEN** 返回综合诊断结果（病害名称、置信度、防治建议）
- **THEN** 诊断响应时间 < 5 秒

### Requirement: 前后端 API 对接
The system SHALL connect frontend Vue3 app with backend FastAPI services.

#### Scenario: 用户登录流程
- **WHEN** 用户在前端提交登录表单
- **THEN** 前端发送 POST 请求到 /api/v1/user/login
- **THEN** 后端验证用户名密码
- **THEN** 后端返回 JWT Token
- **THEN** 前端保存 Token 到 localStorage
- **THEN** 前端跳转到 Dashboard 页面

#### Scenario: 图像诊断流程
- **WHEN** 用户在前端上传图像
- **THEN** 前端发送 POST 请求到 /api/v1/diagnosis/image
- **THEN** 前端携带 JWT Token 进行认证
- **THEN** 后端处理图像并调用 AI 引擎
- **THEN** 后端返回诊断结果
- **THEN** 前端展示诊断结果（病害名称、置信度、防治建议）

### Requirement: 系统一键启动
The system SHALL provide one-click startup scripts for development.

#### Scenario: 开发环境启动
- **WHEN** 运行启动脚本
- **THEN** 自动启动 MySQL 数据库（如未启动）
- **THEN** 自动启动 Redis 服务（如未启动）
- **THEN** 自动启动 FastAPI 后端服务（端口 8000）
- **THEN** 自动启动 Vue3 前端开发服务器（端口 5173）
- **THEN** 显示所有服务状态和访问地址

### Requirement: 集成测试
The system SHALL provide end-to-end integration tests.

#### Scenario: 端到端测试
- **WHEN** 运行集成测试脚本
- **THEN** 测试用户注册和登录
- **THEN** 测试图像上传和诊断
- **THEN** 测试诊断记录查询
- **THEN** 测试知识库浏览
- **THEN** 测试 Dashboard 统计
- **THEN** 生成测试报告（通过率 > 90%）

## MODIFIED Requirements

### Requirement: 后端诊断服务
The system SHALL modify `src/web/backend/app/services/diagnosis.py` to integrate AI engines.

**修改说明**: 
- 原服务：空的诊断服务框架
- 新服务：集成 YOLOv8、Qwen3-VL-4B-Instruct、Fusion Engine

```python
# 新增方法
async def diagnose_image(
    image_path: str,
    symptoms: Optional[str] = None
) -> DiagnosisResult:
    """
    图像诊断
    1. 调用 YOLOv8 进行视觉检测
    2. 调用 Qwen3-VL 进行认知分析
    3. 调用 Fusion Engine 进行多模态融合
    4. 返回综合诊断结果
    """
```

### Requirement: 前端诊断页面
The system SHALL modify `src/web/frontend/src/views/Diagnosis.vue` to connect backend API.

**修改说明**:
- 原页面：使用模拟数据
- 新页面：调用真实后端 API

```typescript
// 新增 API 调用
const handleDiagnose = async () => {
  const response = await request.post('/diagnosis/image', formData)
  diagnosisResult.value = response.data
  showResult.value = true
}
```

## REMOVED Requirements

### Requirement: 模拟数据
**Reason**: 被真实的后端 API 和数据库数据替代
**Migration**: 移除前端中的模拟数据，使用真实 API 调用

---

## 技术规格详情

### 1. 数据库连接配置

#### 1.1 数据库信息
- **主机**: 127.0.0.1
- **端口**: 3306
- **用户名**: root
- **密码**: 123456
- **数据库名**: wheat_agent_db

#### 1.2 连接字符串
```
mysql+pymysql://root:123456@127.0.0.1:3306/wheat_agent_db
```

#### 1.3 环境变量配置
```bash
# .env 文件
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=123456
DATABASE_NAME=wheat_agent_db
```

### 2. AI 引擎集成路径

#### 2.1 引擎路径
- **YOLOv8**: `src/vision/vision_engine.py`
- **Qwen3-VL**: `src/cognition/qwen_vl_engine.py`
- **Fusion Engine**: `src/fusion/fusion_engine.py`

#### 2.2 集成方式
```python
# 导入现有引擎
from src.vision.vision_engine import VisionEngine
from src.cognition.qwen_vl_engine import QwenVLEngine
from src.fusion.fusion_engine import FusionEngine

# 创建单例实例
vision_engine = VisionEngine()
qwen_engine = QwenVLEngine()
fusion_engine = FusionEngine()
```

### 3. API 接口规范

#### 3.1 诊断接口
```
POST /api/v1/diagnosis/image
Content-Type: multipart/form-data
Authorization: Bearer {token}

Request:
- image: File (图像文件)
- symptoms: string (可选，文本症状描述)

Response: 200 OK
{
  "diagnosis_id": "string",
  "disease_name": "string",
  "confidence": 0.95,
  "severity": "high",
  "description": "string",
  "recommendations": ["string"],
  "knowledge_links": [
    {
      "id": 1,
      "title": "string",
      "url": "string"
    }
  ],
  "created_at": "2026-03-10T10:00:00Z"
}
```

#### 3.2 错误响应
```json
{
  "error_code": "DIAGNOSIS_FAILED",
  "message": "诊断失败，请重试",
  "details": "详细错误信息"
}
```

### 4. 前端 API 配置

#### 4.1 Axios 配置
```typescript
// src/utils/request.ts
const request = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000 // 30 秒超时
})

// 请求拦截器：添加 Token
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理错误
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### 5. 系统启动脚本

#### 5.1 Windows PowerShell 启动脚本
```powershell
# start-dev.ps1
# 1. 检查 MySQL 服务
# 2. 检查 Redis 服务
# 3. 启动后端服务
# 4. 启动前端服务
# 5. 显示访问地址
```

#### 5.2 启动流程
```
1. 检查 MySQL 是否运行 → 如未运行，提示用户启动
2. 检查 Redis 是否运行 → 如未运行，提示用户启动
3. 激活 Conda 环境 → conda activate wheatagent-py310
4. 启动后端 → python -m uvicorn app.main:app --reload
5. 启动前端 → npm run dev
6. 显示访问地址：
   - 前端：http://localhost:5173
   - 后端 API 文档：http://localhost:8000/docs
```

### 6. 集成测试用例

#### 6.1 测试用例列表
1. **用户注册测试**
   - 输入：用户名、邮箱、密码
   - 预期：注册成功，返回用户信息

2. **用户登录测试**
   - 输入：用户名、密码
   - 预期：登录成功，返回 JWT Token

3. **图像诊断测试**
   - 输入：测试图像（test_e2e_0.jpg）
   - 预期：返回诊断结果，置信度 > 0.5

4. **诊断记录查询测试**
   - 输入：JWT Token
   - 预期：返回诊断记录列表

5. **知识库浏览测试**
   - 输入：无
   - 预期：返回病害知识列表

6. **Dashboard 统计测试**
   - 输入：JWT Token
   - 预期：返回统计数据

---

## 项目目录结构（更新）

```
WheatAgent/
├── src/
│   ├── web/
│   │   ├── frontend/
│   │   │   ├── src/
│   │   │   │   ├── utils/
│   │   │   │   │   └── request.ts          # ✅ 新增：API 请求配置
│   │   │   │   └── views/
│   │   │   │       └── Diagnosis.vue       # 🔄 修改：对接后端 API
│   │   │   └── start-dev.ps1               # ✅ 新增：启动脚本
│   │   │
│   │   └── backend/
│   │       ├── app/
│   │       │   ├── api/v1/
│   │       │   │   └── diagnosis.py        # 🔄 修改：完善诊断 API
│   │       │   ├── services/
│   │       │   │   └── diagnosis.py        # 🔄 修改：集成 AI 引擎
│   │       │   └── core/
│   │       │       └── config.py           # 🔄 修改：数据库配置
│   │       ├── .env                        # ✅ 新增：环境变量
│   │       └── start-dev.ps1               # ✅ 新增：启动脚本
│   │
│   ├── vision/vision_engine.py             # 🔄 现有：YOLOv8 引擎
│   ├── cognition/qwen_vl_engine.py         # 🔄 现有：Qwen3-VL 引擎
│   └── fusion/fusion_engine.py             # 🔄 现有：融合引擎
│
├── src/database/
│   ├── init.sql                            # ✅ 新增：数据库初始化脚本
│   └── README.md                           # ✅ 新增：数据库说明
│
├── scripts/
│   └── integration/
│       ├── test_e2e.py                     # ✅ 新增：端到端测试
│       └── test_data/                      # ✅ 新增：测试数据
│           └── test_e2e_0.jpg
│
└── .trae/
    └── specs/
        └── web-integration/
            ├── spec.md                     # ✅ 当前文件
            ├── tasks.md                    # ✅ 任务列表
            └── checklist.md                # ✅ 检查清单
```

---

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 页面加载时间 | < 2s | 首屏加载 |
| API 响应时间 | < 500ms | 平均响应（不含 AI 推理） |
| 诊断响应时间 | < 5s | 包含 AI 推理 |
| 并发用户数 | > 100 | 开发环境 |
| 测试通过率 | > 90% | 集成测试 |

---

## 安全要求

1. **JWT Token 认证**: 所有诊断接口必须携带 Token
2. **CORS 配置**: 仅允许 localhost:5173 访问
3. **SQL 注入防护**: 使用参数化查询
4. **文件上传限制**: 最大 5MB，仅允许 JPG/PNG
5. **密码加密**: 使用 bcrypt 哈希

---

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| MySQL | 8.0+ | 数据库 |
| Redis | 7.2+ | 缓存 |
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端运行环境 |
| CUDA | 12.6+ | GPU 加速（可选） |
