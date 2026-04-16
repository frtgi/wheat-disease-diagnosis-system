# 基于多模态融合的小麦病害诊断系统 — API 参考文档

> **版本**: V12.0 | **日期**: 2026-04-05 | **端点总数**: 48+ | **基线 URL**: `http://localhost:8000/api/v1`

---

## 目录

- [快速速查表](#快速速查表)
- [① 用户认证](#①-用户认证)
- [② 病害诊断-基础](#②-病害诊断-基础)
- [③ 病害诊断-AI高级](#③-病害诊断ai高级)
- [④ 知识库管理](#④-知识库管理)
- [⑤ 统计数据](#⑤-统计数据)
- [⑥ 报告生成](#⑥-报告生成)
- [⑦ 缓存管理](#⑦-缓存管理)
- [⑧ 健康检查](#⑧-健康检查)
- [⑨ 高级特性](#⑨-高级特性)
- [错误码索引](#错误码索引)
- [数据模型](#数据模型)

---

## 快速速查表

| 方法 | 路径 | 功能 | 认证 | 限流 |
|------|------|------|------|------|
| POST | /users/register | 用户注册 | 公开 | 3/min |
| POST | /users/login | 用户登录 | 公开 | 5/min |
| POST | /users/refresh | 刷新访问令牌 | 是 | - |
| POST | /users/logout | 用户登出 | 是 | - |
| GET | /users/me | 获取当前用户信息 | 是 | - |
| PUT | /users/me | 更新当前用户信息 | 是 | - |
| POST | /users/password/reset-request | 请求密码重置 | 公开 | - |
| POST | /users/password/reset | 执行密码重置 | 公开 | - |
| GET | /users/sessions | 获取会话列表 | 是 | - |
| DELETE | /users/sessions/{id} | 终止指定会话 | 是 | - |
| DELETE | /users/sessions | 终止所有会话 | 是 | - |
| GET | /users/{user_id} | 获取指定用户信息 | 公开 | - |
| PUT | /users/{user_id} | 更新用户信息 | 是 | - |
| POST | /diagnosis/image | 图像诊断(CRUD) | 是 | - |
| GET | /diagnosis | 诊断记录列表(分页) | 是 | - |
| GET | /diagnosis/{id} | 诊断详情 | 是 | - |
| PUT | /diagnosis/{id} | 更新诊断记录 | 是 | - |
| DELETE | /diagnosis/{id} | 删除诊断记录 | 是 | - |
| POST | /diagnosis/fusion | **多模态融合诊断** ⭐ | 是 | 10/min |
| GET | /diagnosis/fusion/stream | SSE流式融合诊断(URL) | 是 | - |
| POST | /diagnosis/fusion/stream | SSE流式融合诊断(上传) | 是 | - |
| POST | /diagnosis/image | YOLOv8图像检测 | 是 | - |
| POST | /diagnosis/multimodal | Qwen3-VL多模态诊断 | 是 | - |
| POST | /diagnosis/text | LLM纯文本诊断 | 是 | - |
| GET | /diagnosis/health/ai | AI服务健康检查 | 是 | - |
| GET | /diagnosis/cache/stats | 缓存统计信息 | 是 | - |
| POST | /diagnosis/cache/clear | 清空缓存(管理员) | Admin | - |
| POST | /diagnosis/batch | 批量诊断(最多10张) | 是 | - |
| POST | /diagnosis/admin/ai/preload | 预加载AI模型(管理员) | Admin | - |
| POST | /knowledge/ | 创建病害知识 | 是 | - |
| GET | /knowledge/search | 搜索病害知识 | 公开 | - |
| GET | /knowledge/categories | 获取疾病分类列表 | 公开 | - |
| GET | /knowledge/{id} | 获取病害详情 | 公开 | - |
| PUT | /knowledge/{id} | 更新病害知识 | 是 | - |
| DELETE | /knowledge/{id} | 删除病害知识 | 是 | - |
| GET | /stats/overview | 获取概览统计 | 公开 | - |
| GET | /stats/diagnoses | 获取诊断统计 | 公开 | - |
| GET | /stats/users | 获取用户统计 | 公开 | - |
| GET | /stats/cache | 获取缓存统计 | 公开 | - |
| DELETE | /stats/cache | 清空推理缓存 | Admin | - |
| GET | /stats/cache/info | 获取缓存配置 | 公开 | - |
| POST | /reports/generate | 生成PDF/HTML报告 | 否 | - |
| GET | /reports/download/{filename} | 下载报告文件 | 公开 | - |
| GET | /reports/list | 报告文件列表 | 公开 | - |
| POST | /upload/image | 上传图像文件 | 是 | 10/min |
| GET | /metrics | Prometheus指标 | 公开 | - |
| GET | /logs/statistics | 诊断日志统计 | Admin | 60/min |
| GET | /logs/disease-distribution | 病害分布统计 | Admin | 60/min |
| GET | /health/database | 数据库健康检查 | 公开 | - |
| GET | /health/startup | 启动状态检查 | 公开 | - |
| GET | /health/ready | 就绪状态检查 | 公开 | - |
| GET | /health/components | 组件状态检查 | 公开 | - |
| GET | / | 根路径(应用信息) | 公开 | - |
| GET | /health | 简单健康检查 | 公开 | - |

---

## ① 用户认证

提供用户注册、登录、令牌管理和会话控制功能。使用 JWT (JSON Web Token) 进行身份验证。

### POST /users/register — 用户注册

**注册新用户账户。**

```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "farmer_zhang", "email": "zhang@example.com", "password": "SecurePass123!"}'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 (3-50字符，仅字母数字下划线) |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 (至少6字符) |

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "farmer_zhang",
    "email": "zhang@example.com",
    "role": "farmer",
    "is_active": true,
    "created_at": "2026-04-05T10:30:00"
  },
  "message": "注册成功"
}
```

**错误响应**:
| HTTP状态 | 错误码 | 说明 |
|----------|--------|------|
| 400 | AUTH_005 | 用户名格式无效 |
| 200 | AUTH_001 | 邮箱已被注册 |
| 200 | AUTH_002 | 用户名已被使用 |

**权限**: 公开 | **限流**: 3 次/分钟 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### POST /users/login — 用户登录

**获取 JWT 访问令牌。**

```bash
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "farmer_zhang", "password": "SecurePass123!"}'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "rt_abc123def456...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "farmer_zhang",
      "email": "farmer@example.com",
      "role": "farmer",
      "is_active": true
    }
  },
  "message": "登录成功"
}
```

**错误响应**:
| HTTP状态 | 错误码 | 说明 |
|----------|--------|------|
| 401 | AUTH_001 | 用户名或密码错误 |
| 403 | AUTH_003 | 账号已被禁用 |
| 403 | AUTH_009 | 登录失败次数过多(临时锁定) |

**权限**: 公开 | **限流**: 5 次/分钟 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### POST /users/logout — 用户登出

**将当前令牌加入黑名单。**

```bash
curl -X POST http://localhost:8000/api/v1/users/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
{
  "success": true,
  "message": "登出成功"
}
```

**权限**: 需要认证 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### POST /users/refresh — 刷新访问令牌

**使用刷新令牌获取新的访问令牌。**

```bash
curl -X POST http://localhost:8000/api/v1/users/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "rt_abc123def456..."}'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 登录时获取的刷新令牌 |

**成功响应 (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**权限**: 需要认证 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### GET /users/me — 获取当前用户信息

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
{
  "id": 1,
  "username": "farmer_zhang",
  "email": "farmer@example.com",
  "phone": "13800138000",
  "avatar_url": "/uploads/avatars/avatar_1.jpg",
  "role": "farmer",
  "is_active": true,
  "created_at": "2026-04-05T10:30:00",
  "updated_at": "2026-04-05T10:30:00"
}
```

**权限**: 需要认证 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### 密码重置流程

#### POST /users/password/reset-request — 请求密码重置

```bash
curl -X POST http://localhost:8000/api/v1/users/password/reset-request \
  -H "Content-Type: application/json" \
  -d '{"email": "farmer@example.com"}'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 注册时使用的邮箱地址 |

**成功响应 (200)**:
```json
{
  "message": "如果该邮箱已注册，您将收到密码重置邮件",
  "success": true
}
```

**权限**: 公开 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

#### POST /users/password/reset — 执行密码重置

```bash
curl -X POST http://localhost:8000/api/v1/users/password/reset \
  -H "Content-Type: application/json" \
  -d '{"token": "reset_token_here", "new_password": "NewSecurePass123!"}'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 密码重置令牌（从邮件获取） |
| new_password | string | 是 | 新密码（至少6个字符） |

**成功响应 (200)**:
```json
{
  "message": "密码重置成功",
  "success": true
}
```

**权限**: 公开 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### 会话管理

#### GET /users/sessions — 获取活跃会话列表

```bash
curl http://localhost:8000/api/v1/users/sessions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "session_token": "sess_abc...xyz",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "is_active": true,
    "created_at": "2026-04-05T10:30:00",
    "expires_at": "2026-04-12T10:30:00"
  }
]
```

**权限**: 需要认证 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

#### DELETE /users/sessions/{session_id} — 终止指定会话

```bash
curl -X DELETE http://localhost:8000/api/v1/users/sessions/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
{
  "message": "会话已终止",
  "success": true
}
```

**权限**: 需要认证 | **源码**: [user.py](../src/web/backend/app/api/v1/user.py)

---

### Token 有效期说明

| Token 类型 | 有效期 | 用途 |
|-----------|-------|------|
| access_token | 30 分钟 | 访问受保护的 API |
| refresh_token | 7 天 | 刷新 access_token |

**安全机制**:
- 密码使用 bcrypt 算法加密存储
- Token 黑名单机制防止重复使用
- 登录失败次数限制防暴力破解

---

## ② 病害诊断-基础

提供传统的图像诊断和诊断记录 CRUD 功能。

### POST /diagnosis/image — 图像诊断

**上传小麦病害图像进行智能诊断，返回病害识别结果和防治建议。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/image \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "image=@/path/to/wheat_disease.jpg" \
  -F "symptoms=叶片出现黄色条状病斑"
```

**请求头**:
```http
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image | file | 是 | 图像文件 (JPG/PNG/WEBP, 最大 10MB) |
| symptoms | string | 否 | 文本症状描述 |

**文件验证规则**:
- ✅ 格式白名单: JPG, PNG, WEBP
- ✅ 大小限制: ≤ 10MB
- ✅ Magic Number 校验: JPEG(`FF D8 FF`), PNG(`89 50 4E 47`), WEBP(`52 49 46 46`)
- ❌ 拒绝伪装扩展名的恶意文件
- ℹ️ **BMP格式说明**: 当前版本不支持 BMP 格式(因文件体积大、无压缩),如需支持可修改 `diagnosis_validator.py:20` 的 `ALLOWED_IMAGE_FORMATS` 集合

**验证流程详解** ([diagnosis_validator.py](../src/web/backend/app/api/v1/diagnosis_validator.py)):

```
上传请求 → validate_image(image_bytes, filename)
    │
    ├── 1. 文件大小检查 (>10MB? → DIAG_004 错误)
    │
    ├── 2. Magic Number 校验 (前12字节二进制头检查)
    │   ├── JPEG: FF D8 FF ✅
    │   ├── PNG: 89 50 4E 47 0D 0A 1A 0A ✅
    │   └── WEBP: RIFF....WEBP ✅
    │       其他 → DIAG_006 错误 (防止伪装扩展名攻击)
    │
    ├── 3. PIL 解析验证 (确保文件完整性)
    │   └── 解析失败 → 返回错误提示
    │
    └── 4. Mock 模式检查 (环境变量 WHEATAGENT_MOCK_AI)
        └── 启用 → 走 Mock 服务 (用于测试/降级)

并发控制集成:
├── 限流器获取令牌 (RateLimiter, 最大3个并发)
├── GPU 可用性检查 (无GPU → 自动降级CPU/Mock)
└── 缓存查找 (SHA256图像哈希匹配)
```

**成功响应 (200)**:
```json
{
  "diagnosis_id": "123",
  "disease_name": "小麦条锈病",
  "confidence": 0.92,
  "severity": "中度",
  "description": "叶片上出现条状黄色锈斑，主要分布在叶片正面",
  "recommendations": "1. 及时喷施三唑酮等杀菌剂\n2. 清除田间病残体\n3. 选用抗病品种",
  "knowledge_links": ["/api/v1/knowledge/1"],
  "created_at": "2026-04-05T12:00:00"
}
```

**错误响应**:
| HTTP状态 | 说明 | 示例 |
|----------|------|------|
| 400 | 不支持的文件类型 | `"不支持的文件类型，仅支持 JPG、PNG、WEBP 格式"` |
| 400 | 文件过大 | `"文件大小超过限制（15.50MB），最大支持 10MB"` |
| 400 | 文件损坏 | `"无法识别文件类型，文件可能已损坏"` |

**权限**: 需要认证 | **源码**: [diagnosis.py](../src/web/backend/app/api/v1/diagnosis.py)

---

### GET /diagnosis — 诊断记录列表

**分页获取诊断记录。**

```bash
curl "http://localhost:8000/api/v1/diagnosis?skip=0&limit=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| skip | integer | 否 | 0 | 跳过记录数 |
| limit | integer | 否 | 20 | 返回记录数 (1-1000) |

**成功响应 (200)**:
```json
{
  "records": [
    {
      "id": 1,
      "user_id": 1,
      "disease_id": 1,
      "symptoms": "叶片出现黄色条状锈斑",
      "diagnosis_result": "小麦条锈病",
      "confidence": 0.92,
      "suggestions": "及时喷施三唑酮等杀菌剂",
      "status": "completed",
      "created_at": "2026-04-05T10:30:00",
      "updated_at": "2026-04-05T10:30:00"
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 20
}
```

**权限**: 需要认证 | **源码**: [diagnosis.py](../src/web/backend/app/api/v1/diagnosis.py)

---

### GET /diagnosis/{id} — 诊断详情

```bash
curl http://localhost:8000/api/v1/diagnosis/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**路径参数**:
- `id`: 诊断记录 ID

**成功响应 (200)**:
```json
{
  "id": 1,
  "user_id": 1,
  "disease_id": 1,
  "symptoms": "叶片出现黄色条状锈斑",
  "diagnosis_result": "小麦条锈病",
  "confidence": 0.92,
  "suggestions": "及时喷施三唑酮等杀菌剂",
  "status": "completed",
  "created_at": "2026-04-05T10:30:00",
  "updated_at": "2026-04-05T10:30:00"
}
```

**权限**: 需要认证 | **源码**: [diagnosis.py](../src/web/backend/app/api/v1/diagnosis.py)

---

### PUT /diagnosis/{id} — 更新诊断记录

```bash
curl -X PUT http://localhost:8000/api/v1/diagnosis/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "status": "reviewed",
    "suggestions": "更新后的防治建议"
  }'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| diagnosis_result | string | 否 | 诊断结果 |
| confidence | float | 否 | 置信度 (0-1) |
| suggestions | string | 否 | 防治建议 |
| status | string | 否 | 诊断状态 (pending/completed/reviewed) |

**权限**: 需要认证 | **源码**: [diagnosis.py](../src/web/backend/app/api/v1/diagnosis.py)

---

### DELETE /diagnosis/{id} — 删除诊断记录

```bash
curl -X DELETE http://localhost:8000/api/v1/diagnosis/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
{
  "message": "诊断记录已删除"
}
```

**权限**: 需要认证 (仅能删除自己的记录) | **源码**: [diagnosis.py](../src/web/backend/app/api/v1/diagnosis.py)

---

## ③ 病害诊断-AI高级 ⭐ 核心

整合 YOLOv8 视觉检测、Qwen3-VL 多模态理解、KAD-Former 知识引导注意力机制和 GraphRAG 知识检索增强技术。

### POST /diagnosis/fusion — 多模态融合诊断

**统一多模态融合诊断 API，支持图像+文本联合诊断。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/fusion \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "image=@/path/to/wheat_disease.jpg" \
  -F "symptoms=叶片出现黄色条状病斑" \
  -F "weather=高温高湿" \
  -F "growth_stage=抽穗期" \
  -F "affected_part=叶片" \
  -F "enable_thinking=true" \
  -F "use_graph_rag=true" \
  -F "use_cache=true"
```

**请求头**:
```http
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image | file | 否 | - | 病害图像 (JPG/PNG/WEBP, ≤10MB) |
| symptoms | string | 否 | "" | 症状描述文本 |
| weather | string | 否 | "" | 天气条件 (晴朗/阴雨/高温高湿) |
| growth_stage | string | 否 | "" | 生长阶段 (苗期/拔节期/抽穗期/灌浆期) |
| affected_part | string | 否 | "" | 发病部位 (叶片/茎秆/穗部/根部) |
| enable_thinking | bool | 否 | true | 是否启用 Thinking 推理链模式 |
| use_graph_rag | bool | 否 | true | 是否使用 GraphRAG 知识增强 |
| use_cache | bool | 否 | true | 是否使用缓存优化 |

**诊断模式**:
1. **图像+文本联合诊断**: 同时上传图像和输入症状描述 (推荐)
2. **仅图像诊断**: 仅上传图像
3. **仅文本诊断**: 仅输入症状描述

**成功响应 (200)**:
```json
{
  "success": true,
  "diagnosis": {
    "disease_name": "小麦条锈病",
    "disease_name_en": "Wheat Stripe Rust",
    "confidence": 0.95,
    "visual_confidence": 0.96,
    "textual_confidence": 0.92,
    "knowledge_confidence": 0.88,
    "description": "多模态融合诊断结果：小麦条锈病",
    "symptoms": "叶片出现黄色条状病斑，沿叶脉平行排列",
    "causes": "由条形柄锈菌引起",
    "recommendations": [
      "选用抗病品种",
      "喷洒粉锈宁可湿性粉剂",
      "使用烯唑醇"
    ],
    "treatment": "发病初期喷施三唑酮可湿性粉剂",
    "medicines": ["三唑酮", "丙环唑", "烯唑醇"],
    "severity": "high",
    "knowledge_references": [
      {
        "title": "条锈病成因",
        "content": "由条形柄锈菌引起"
      }
    ],
    "roi_boxes": [
      {
        "x1": 100,
        "y1": 150,
        "x2": 300,
        "y2": 350,
        "confidence": 0.95,
        "class": "stripe_rust"
      }
    ],
    "inference_time_ms": 2345.67,
    "kad_former_used": true
  },
  "features": {
    "thinking_mode": true,
    "graph_rag": true
  },
  "performance": {
    "inference_time_ms": 2345.67,
    "cache_hit": false,
    "thinking_mode_enabled": true,
    "graph_rag_enabled": true
  },
  "message": "多模态融合诊断成功"
}
```

**Mock 模式降级响应** (当 AI 服务不可用时):
```json
{
  "success": true,
  "diagnosis": { /* Mock 诊断结果 */ },
  "model": "mock_service",
  "features": {
    "mock_mode": true,
    "thinking_mode": true,
    "graph_rag": true
  },
  "performance": {
    "inference_time_ms": 45.23,
    "cache_hit": false
  },
  "message": "Mock 模式诊断成功（AI 服务不可用）"
}
```

**错误响应**:
| HTTP状态 | 错误码 | 说明 |
|----------|--------|------|
| 400 | - | 请至少提供图像或症状描述中的一种输入 |
| 400 | DIAG_003 | 不支持的文件格式 |
| 400 | DIAG_004 | 文件大小超限 |
| 500 | AI_001 | AI 服务不可用 |
| 503 | AI_008 | GPU 内存不足 |

**权限**: 需要认证 | **限流**: 10 次/分钟 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### GET /diagnosis/fusion/stream — SSE 流式融合诊断 (URL 模式)

**通过 SSE (Server-Sent Events) 实时推送诊断进度和结果。**

```bash
curl "http://localhost:8000/api/v1/diagnosis/fusion/stream?image_url=/uploads/diagnosis/uuid.jpg&symptoms=叶片出现黄色条状病斑&enable_thinking=true" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image_url | string | 否 | - | 已上传图像的 URL |
| symptoms | string | 否 | "" | 症状描述文本 |
| weather | string | 否 | "" | 天气条件 |
| growth_stage | string | 否 | "" | 生长阶段 |
| affected_part | string | 否 | "" | 发病部位 |
| enable_thinking | bool | 否 | true | 是否启用 Thinking 模式 |
| use_graph_rag | bool | 否 | true | 是否使用 GraphRAG |
| user_id | integer | 否 | - | 用户 ID (用于保存诊断记录) |

**SSE 事件类型**:

| 事件类型 | 数据类 | 说明 |
|---------|--------|------|
| start | - | 推理开始 |
| progress | ProgressEvent | 进度更新 (stage, progress, message) |
| log | LogEvent | 日志信息 (level, message) |
| complete | - | 推理完成，包含完整结果 |
| error | - | 错误信息 |
| heartbeat | HeartbeatEvent | 心跳保活 (每 15 秒) |

**SSE 响应示例**:
```
event: start
data: {"stage":"init","progress":0,"message":"开始多模态融合诊断...","timestamp":1712000000.123}

event: progress
data: {"stage":"visual","progress":15,"message":"正在提取视觉特征 (YOLOv8)...","timestamp":1712000000.456}

event: progress
data: {"stage":"visual","progress":30,"message":"视觉特征提取完成，检测到 3 个目标","timestamp":1712000000.789}

event: progress
data: {"stage":"knowledge","progress":40,"message":"正在检索知识 (GraphRAG)...","timestamp":1712000001.012}

event: progress
data: {"stage":"textual","progress":55,"message":"正在提取文本语义特征 (Qwen3-VL)...","timestamp":1712000001.345}

event: progress
data: {"stage":"fusion","progress":80,"message":"正在融合多模态特征...","timestamp":1712000002.678}

event: complete
data: {"stage":"complete","progress":100,"message":"融合诊断完成","diagnosis":{...},"timestamp":1712000003.901}
```

**配置参数** (可通过环境变量调整):

| 参数 | 默认值 | 环境变量 | 说明 |
|------|--------|----------|------|
| SSE 超时 | 120 秒 | SSE_TIMEOUT_SECONDS | 连接超时时间 |
| 心跳间隔 | 15 秒 | SSE_HEARTBEAT_INTERVAL | 心跳发送间隔 |
| 背压队列大小 | 100 | SSE_BACKPRESSURE_QUEUE_SIZE | 最大缓冲事件数 |

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py), [sse_stream_manager.py](../src/web/backend/app/api/v1/sse_stream_manager.py)

#### SSE 事件流时间序列

**完整诊断流程的事件发送顺序**:

```
时间轴 →
─────────────────────────────────────────────────────────────→

T+0ms     event: start
          data: {"stage":"init","progress":0,"message":"开始多模态融合诊断..."}

T+15ms    event: steps (StepIndicator, 仅首次)
          data: {"steps":[{id,name,icon}, ...]}  ← 定义6个步骤

T+500ms   event: progress
          data: {"stage":"validation","progress":5,"message":"正在验证请求..."}

T+50ms    event: progress
          data: {"stage":"preprocess","progress":10,"message":"图像预处理完成"}

T+200ms   event: progress
          data: {"stage":"visual","progress":25,"message":"YOLOv8检测中..."}

T+250ms   event: log
          data: {"level":"INFO","message":"检测到3个目标区域"}

T+300ms   event: progress
          data: {"stage":"visual","progress":35,"message":"视觉特征提取完成"}

[T+15s]   event: heartbeat  (每15秒一次,持续整个流程)
          data: {"timestamp":...}

T+1000ms  event: progress
          data: {"stage":"knowledge","progress":45,"message":"GraphRAG知识检索中..."}

T+5000ms  event: progress
          data: {"stage":"textual","progress":60,"message":"Qwen3-VL推理中..."}

T+15000ms event: log
          data: {"level":"DEBUG","message":"生成推理链: step1/5"}

T+20000ms event: progress
          data: {"stage":"fusion","progress":80,"message":"KAD-Former融合中..."}

T+20500ms event: progress
          data: {"stage":"annotating","progress":90,"message":"生成标注图像..."}

T+21000ms event: progress
          data: {"stage":"complete","progress":100,"message":"诊断完成"}

T+21100ms event: complete
          data: {完整诊断结果JSON,包含disease_name,confidence,...}
```

**客户端解析指南** (JavaScript/TypeScript):

```typescript
/**
 * SSE 客户端解析示例
 * 支持自动重连、心跳保活、进度更新
 */
function connectSSEDiagnosis(url: string, token: string) {
  const eventSource = new EventSource(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  // 1. 监听开始事件
  eventSource.addEventListener('start', (e) => {
    const data = JSON.parse(e.data);
    console.log(`[${data.stage}] ${data.message} (${data.progress}%)`);
    showProgressUI(data.progress, data.message);
  });

  // 2. 监听步骤定义 (仅首次)
  eventSource.addEventListener('steps', (e) => {
    const { steps } = JSON.parse(e.data);
    initStepIndicator(steps);  // 渲染6个步骤图标
  });

  // 3. 监听进度更新 (核心事件)
  eventSource.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data);
    updateProgressBar(data.progress);
    updateStageIcon(data.stage);  // 高亮当前步骤
    appendLog(`${data.stage}: ${data.message}`);
  });

  // 4. 监听日志事件 (调试用)
  eventSource.addEventListener('log', (e) => {
    const { level, message } = JSON.parse(e.data);
    if (level === 'ERROR') {
      showErrorToast(message);
    } else {
      appendDebugLog(message);
    }
  });

  // 5. 心跳保活 (防止超时断开)
  eventSource.addEventListener('heartbeat', () => {
    // 可选: 更新连接状态指示器
    updateConnectionStatus('connected');
  });

  // 6. 接收最终结果
  eventSource.addEventListener('complete', (e) => {
    const result = JSON.parse(e.data);
    renderDiagnosisResult(result.diagnosis);
    eventSource.close();  // 关闭连接
  });

  // 7. 错误处理
  eventSource.onerror = (err) => {
    console.error('SSE连接错误:', err);
    showErrorToast('诊断服务连接中断,请刷新页面重试');
    setTimeout(() => eventSource.close(), 1000);
  };

  return eventSource;
}
```

**关键注意事项**:
- ⚠️ **必须处理心跳**: 每15秒一个 heartbeat 事件,用于保持连接活跃
- ⚠️ **超时控制**: 默认120秒无数据则关闭连接 (可配置 `SSE_TIMEOUT_SECONDS`)
- ⚠️ **背压限制**: 客户端缓冲区最大100条事件 (可配置 `SSE_BACKPRESSURE_QUEUE_SIZE`)
- ✅ **自动重连**: 浏览器的 EventSource 会自动重连 (需后端支持 Last-Event-ID)

---

### POST /diagnosis/fusion/stream — SSE 流式融合诊断 (上传模式)

**通过 multipart 上传图像进行 SSE 流式诊断。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/fusion/stream \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "image=@/path/to/wheat_disease.jpg" \
  -F "symptoms=叶片出现黄色条状病斑" \
  -F "enable_thinking=true"
```

**请求参数**: 同 POST /diagnosis/fusion

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### POST /diagnosis/multimodal — Qwen3-VL 多模态诊断

**使用 Qwen3-VL 模型进行图文联合理解诊断。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/multimodal \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "image=@/path/to/wheat_disease.jpg" \
  -F "symptoms=叶片出现黄色条状病斑" \
  -F "thinking_mode=true" \
  -F "use_graph_rag=true" \
  -F "enable_kad_former=true"
```

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image | file | 否 | - | 病害图像文件 |
| symptoms | string | 否 | "" | 症状描述 |
| thinking_mode | bool | 否 | true | 是否启用 Thinking 模式 |
| use_graph_rag | bool | 否 | true | 是否使用 GraphRAG |
| enable_kad_former | bool | 否 | true | 是否启用 KAD-Former 融合 |
| disease_context | string | 否 | - | 疾病上下文 (用于 GraphRAG 检索) |
| use_cache | bool | 否 | true | 是否使用缓存 |

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "disease_name": "小麦条锈病",
    "confidence": 0.95,
    "description": "多模态诊断结果",
    "recommendations": ["选用抗病品种", "喷洒杀菌剂"]
  },
  "model": "qwen3-vl-4b",
  "features": {
    "thinking_mode": true,
    "graph_rag": true,
    "kad_former": true
  },
  "performance": {
    "inference_time_ms": 2345.67,
    "cache_hit": false
  },
  "reasoning_chain": [
    "分析图像中的病害特征...",
    "结合症状描述进行推理...",
    "检索知识库获取相关信息...",
    "综合判断为小麦条锈病..."
  ],
  "message": "多模态诊断成功"
}
```

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### POST /diagnosis/text — LLM 纯文本诊断

**仅通过文本症状描述进行诊断。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/text \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "symptoms=小麦叶片出现黄色条状病斑，沿叶脉平行排列"
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symptoms | string | 是 | 症状描述 |

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "disease_name": "小麦条锈病",
    "confidence": 0.85,
    "description": "根据症状描述，可能是小麦条锈病",
    "recommendations": ["及时清除病残体", "合理密植", "喷施杀菌剂"]
  },
  "model": "qwen3-vl-4b",
  "message": "文本诊断成功"
}
```

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### POST /diagnosis/batch — 批量图像诊断

**批量处理多张图像的诊断请求（最多 10 张）。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/batch \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg" \
  -F "images=@/path/to/image3.jpg" \
  -F "symptoms=叶片出现黄色条状病斑"
```

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| images | file[] | 是 | - | 病害图像文件列表 (最多 10 张) |
| symptoms | string | 否 | "" | 症状描述 (应用于所有图像) |
| thinking_mode | bool | 否 | false | 是否启用 Thinking 模式 |
| use_graph_rag | bool | 否 | false | 是否使用 GraphRAG |
| use_cache | bool | 否 | true | 是否使用缓存 |

**成功响应 (200)**:
```json
{
  "success": true,
  "summary": {
    "total_images": 3,
    "success_count": 3,
    "failed_count": 0,
    "cache_hits": 1,
    "cache_hit_rate": 33.33,
    "success_rate": 100.0
  },
  "results": [
    {
      "index": 0,
      "filename": "image1.jpg",
      "success": true,
      "diagnosis": {
        "disease_name": "小麦条锈病",
        "confidence": 0.95
      }
    }
  ],
  "performance": {
    "total_time_ms": 5678.90,
    "avg_time_per_image_ms": 1892.97
  },
  "message": "批量诊断完成，成功 3/3 张，缓存命中 1 次"
}
```

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### GET /diagnosis/health/ai — AI 服务健康检查

**检查 AI 模型服务状态 (YOLO + Qwen)。**

```bash
curl http://localhost:8000/api/v1/diagnosis/health/ai \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
{
  "status": "healthy",
  "mock_mode": false,
  "services": {
    "yolov8": {
      "status": "ready",
      "model_path": "models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt",
      "device": "cuda",
      "is_loaded": true
    },
    "qwen3vl": {
      "status": "ready",
      "model_path": "models/Qwen3-VL-2B-Instruct",
      "device": "cuda",
      "int4_quantization": true,
      "vram_usage_gb": 2.6,
      "is_loaded": true
    }
  }
}
```

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### POST /diagnosis/admin/ai/preload — 预加载 AI 模型 (管理员)

**手动触发 AI 模型预加载（通常在启动时自动完成）。**

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/admin/ai/preload \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200)**:
```json
{
  "success": true,
  "message": "AI 模型预加载完成",
  "models_loaded": ["yolov8", "qwen3vl"],
  "total_time_seconds": 45.2
}
```

**权限**: 仅管理员 (Admin) | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### 请求验证与并发控制

所有诊断请求均通过 [DiagnosisRequestValidator](../src/web/backend/app/api/v1/diagnosis_validator.py) 进行多层验证：

| 验证项 | 规则 | 错误码 |
|--------|------|--------|
| 文件格式 | JPG / PNG / WEBP | DIAG_003 |
| 文件大小 | ≤ 10 MB | DIAG_004 |
| Magic Number | JPEG/PNG/WEBP 二进制头校验 | DIAG_006 |
| GPU 可用性 | 无 GPU 时自动降级至 CPU/Mock | - |
| 并发限制 | 最大 3 个并发诊断任务 | SYS_005 |

**并发控制配置** (可通过环境变量动态调整):

| 参数 | 默认值 | 环境变量 | 说明 |
|------|--------|----------|------|
| 最大并发数 | 3 | MAX_CONCURRENT_DIAGNOSIS | 同时进行的最大诊断数 |
| 最大队列长度 | 10 | MAX_DIAGNOSIS_QUEUE_SIZE | 等待队列容量 |
| 队列超时 | 300 秒 | DIAGNOSIS_QUEUE_TIMEOUT | 队列等待超时 |
| GPU 显存阈值 | 90% | GPU_MEMORY_THRESHOLD | 触发降级的显存占用率 |

---

## ④ 知识库管理

管理小麦病害知识库，支持 CRUD 操作和搜索。

### POST /knowledge/ — 创建病害知识

**向知识库添加新的病害信息。**

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "name": "小麦条锈病",
    "code": "WHEAT_STRIPE_RUST",
    "category": "真菌病害",
    "symptoms": "叶片上出现条状黄色锈斑，主要分布在叶片正面",
    "causes": "由条形柄锈菌引起，适宜温度 10-15°C",
    "treatments": "喷施三唑酮可湿性粉剂",
    "prevention": "选用抗病品种，合理密植",
    "severity": 0.7
  }'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 病害名称 (1-100 字符) |
| code | string | 否 | 病害编码 (标准化分类) |
| category | string | 否 | 病害分类 (真菌病害/细菌病害/病毒病害...) |
| symptoms | string | 否 | 症状描述 |
| causes | string | 否 | 病因 |
| treatments | string | 否 | 治疗方法 |
| prevention | string | 否 | 预防措施 |
| severity | float | 否 | 严重程度 (0-1) |

**成功响应 (200)**:
```json
{
  "id": 1,
  "name": "小麦条锈病",
  "code": "WHEAT_STRIPE_RUST",
  "category": "真菌病害",
  "symptoms": "叶片上出现条状黄色锈斑，主要分布在叶片正面",
  "causes": "由条形柄锈菌引起，适宜温度 10-15°C",
  "treatments": "喷施三唑酮可湿性粉剂",
  "prevention": "选用抗病品种，合理密植",
  "severity": 0.7,
  "created_at": "2026-04-05T10:30:00",
  "updated_at": "2026-04-05T10:30:00"
}
```

**权限**: 需要认证 | **源码**: [knowledge.py](../src/web/backend/app/api/v1/knowledge.py)

---

### GET /knowledge/search — 搜索病害知识

**根据关键词或分类搜索病害知识库。**

```bash
curl "http://localhost:8000/api/v1/knowledge/search?keyword=条锈病&category=真菌病害&skip=0&limit=10"
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 搜索关键词 |
| category | string | 否 | - | 病害分类筛选 |
| skip | integer | 否 | 0 | 跳过记录数 |
| limit | integer | 否 | 20 | 返回记录数 (1-100) |

**搜索范围**: 病害名称、症状描述、病因说明、治疗方法

**成功响应 (200)**:
```json
[
  {
    "id": 1,
    "name": "小麦条锈病",
    "code": "WHEAT_STRIPE_RUST",
    "category": "真菌病害",
    "symptoms": "叶片上出现条状黄色锈斑",
    "causes": "由条形柄锈菌引起",
    "treatments": "喷施三唑酮可湿性粉剂",
    "prevention": "选用抗病品种",
    "severity": 0.7,
    "created_at": "2026-04-05T10:30:00",
    "updated_at": "2026-04-05T10:30:00"
  }
]
```

**权限**: 公开 | **源码**: [knowledge.py](../src/web/backend/app/api/v1/knowledge.py)

---

### GET /knowledge/categories — 获取疾病分类列表

```bash
curl http://localhost:8000/api/v1/knowledge/categories
```

**成功响应 (200)**:
```json
[
  "真菌病害",
  "细菌病害",
  "病毒病害",
  "线虫病害",
  "生理性病害",
  "虫害"
]
```

**权限**: 公开 | **源码**: [knowledge.py](../src/web/backend/app/api/v1/knowledge.py)

---

### GET /knowledge/{id} — 获取病害详情

```bash
curl http://localhost:8000/api/v1/knowledge/1
```

**路径参数**:
- `id`: 疾病 ID

**成功响应 (200)**:
```json
{
  "id": 1,
  "name": "小麦条锈病",
  "code": "WHEAT_STRIPE_RUST",
  "category": "真菌病害",
  "symptoms": "叶片上出现条状黄色锈斑，主要分布在叶片正面",
  "causes": "由条形柄锈菌引起，适宜温度 10-15°C",
  "treatments": "喷施三唑酮可湿性粉剂",
  "prevention": "选用抗病品种，合理密植",
  "severity": 0.7,
  "created_at": "2026-04-05T10:30:00",
  "updated_at": "2026-04-05T10:30:00"
}
```

**错误响应 (404)**:
```json
{"detail": "疾病不存在"}
```

**权限**: 公开 | **源码**: [knowledge.py](../src/web/backend/app/api/v1/knowledge.py)

---

### PUT /knowledge/{id} — 更新病害知识

```bash
curl -X PUT http://localhost:8000/api/v1/knowledge/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "symptoms": "更新后的症状描述",
    "treatments": "更新后的治疗方法"
  }'
```

**请求参数**: 同创建接口（所有字段可选）

**权限**: 需要认证 | **源码**: [knowledge.py](../src/web/backend/app/api/v1/knowledge.py)

---

### DELETE /knowledge/{id} — 删除病害知识

```bash
curl -X DELETE http://localhost:8000/api/v1/knowledge/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 (200)**:
```json
{
  "message": "疾病知识已删除"
}
```

**权限**: 需要认证 | **源码**: [knowledge.py](../src/web/backend/app/api/v1/knowledge.py)

---

## ⑤ 统计数据

提供系统级别的统计数据和仪表盘信息。

### GET /stats/overview — 获取概览统计

```bash
curl http://localhost:8000/api/v1/stats/overview
```

**成功响应 (200)**:
```json
{
  "total_users": 150,
  "total_diagnoses": 1200,
  "total_diseases": 45
}
```

**权限**: 公开 | **源码**: [stats.py](../src/web/backend/app/api/v1/stats.py)

---

### GET /stats/diagnoses — 获取诊断统计

```bash
curl http://localhost:8000/api/v1/stats/diagnoses
```

**成功响应 (200)**:
```json
{
  "by_status": {
    "completed": 1150,
    "pending": 30,
    "failed": 20
  },
  "top_diseases": [
    {"disease_id": 1, "count": 500},
    {"disease_id": 2, "count": 350},
    {"disease_id": 3, "count": 200}
  ]
}
```

**权限**: 公开 | **源码**: [stats.py](../src/web/backend/app/api/v1/stats.py)

---

### GET /stats/users — 获取用户统计

```bash
curl http://localhost:8000/api/v1/stats/users
```

**成功响应 (200)**:
```json
{
  "total_users": 150,
  "active_users": 120,
  "inactive_users": 30,
  "by_role": {
    "farmer": 100,
    "technician": 40,
    "admin": 10
  }
}
```

**权限**: 公开 | **源码**: [stats.py](../src/web/backend/app/api/v1/stats.py)

---

## ⑥ 报告生成

生成 PDF 和 HTML 格式的诊断报告。

### POST /reports/generate — 生成诊断报告

**执行诊断并生成 PDF/HTML 报告文件。**

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -F "image=@/path/to/wheat_disease.jpg" \
  -F "symptoms=叶片出现黄色条状病斑" \
  -F "thinking_mode=true" \
  -F "use_graph_rag=true" \
  -F "report_format=pdf"
```

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image | file | 否 | - | 病害图像文件 |
| symptoms | string | 否 | "" | 症状描述 |
| thinking_mode | bool | 否 | true | 是否启用 Thinking 模式 |
| use_graph_rag | bool | 否 | true | 是否使用 Graph-RAG |
| report_format | string | 否 | both | 报告格式 (pdf/html/both) |

**成功响应 (200)**:
```json
{
  "success": true,
  "diagnosis": {
    "disease_name": "小麦条锈病",
    "confidence": 0.95
  },
  "report_files": {
    "pdf": "/reports/diagnosis_report_20260405_120000.pdf"
  },
  "message": "报告生成成功，共 1 个文件"
}
```

**权限**: 公开 | **源码**: [reports.py](../src/web/backend/app/api/v1/reports.py)

---

### GET /reports/download/{filename} — 下载报告文件

```bash
curl -O http://localhost:8000/api/v1/reports/download/diagnosis_report_20260405_120000.pdf
```

**路径参数**:
- `filename`: 报告文件名

**响应**: 报告文件 (PDF 或 HTML)

**权限**: 公开 | **源码**: [reports.py](../src/web/backend/app/api/v1/reports.py)

---

### GET /reports/list — 列出所有报告

```bash
curl http://localhost:8000/api/v1/reports/list
```

**成功响应 (200)**:
```json
{
  "success": true,
  "reports": [
    {
      "filename": "diagnosis_report_20260405_120000.pdf",
      "size": 524288,
      "created_at": 1712000000.123,
      "format": "pdf"
    }
  ],
  "total": 1
}
```

**权限**: 公开 | **源码**: [reports.py](../src/web/backend/app/api/v1/reports.py)

---

## ⑦ 缓存管理

管理推理结果缓存，提升重复查询性能。

### GET /stats/cache — 获取缓存统计

```bash
curl http://localhost:8000/api/v1/stats/cache
```

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "total_keys": 256,
    "hit_rate": 0.85,
    "miss_rate": 0.15,
    "total_hits": 1024,
    "total_misses": 180,
    "avg_response_time_ms": 12.5,
    "memory_usage_mb": 128.5
  }
}
```

**权限**: 公开 | **源码**: [stats.py](../src/web/backend/app/api/v1/stats.py)

---

### DELETE /stats/cache — 清空推理缓存 (管理员)

```bash
curl -X DELETE http://localhost:8000/api/v1/stats/cache \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200)**:
```json
{
  "success": true,
  "message": "已清空 256 个缓存键",
  "deleted_count": 256
}
```

**权限**: 仅管理员 (Admin) | **源码**: [stats.py](../src/web/backend/app/api/v1/stats.py)

---

### GET /stats/cache/info — 获取缓存配置

```bash
curl http://localhost:8000/api/v1/stats/cache/info
```

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "ttl_seconds": 3600,
    "similar_search_enabled": true,
    "similarity_threshold": 0.95,
    "cache_prefix": "wheatagent:cache:",
    "phash_index_prefix": "wheatagent:phash:"
  }
}
```

**权限**: 公开 | **源码**: [stats.py](../src/web/backend/app/api/v1/stats.py)

---

### GET /diagnosis/cache/stats — AI 诊断缓存统计

```bash
curl http://localhost:8000/api/v1/diagnosis/cache/stats \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**权限**: 需要认证 | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

### POST /diagnosis/cache/clear — 清空 AI 诊断缓存 (管理员)

```bash
curl -X POST http://localhost:8000/api/v1/diagnosis/cache/clear \
  -H "Authorization: Bearer <admin_token>"
```

**权限**: 仅管理员 (Admin) | **源码**: [diagnosis_router.py](../src/web/backend/app/api/v1/diagnosis_router.py)

---

## ⑧ 健康检查

监控系统各组件的运行状态。

### GET /health — 简单健康检查

```bash
curl http://localhost:8000/health
```

**成功响应 (200)**:
```json
{
  "status": "healthy"
}
```

**权限**: 公开 | **源码**: [main.py](../src/web/backend/app/main.py)

---

### GET /api/v1/health — 详细健康检查

```bash
curl http://localhost:8000/api/v1/health
```

**成功响应 (200)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ready": true,
  "degraded": false,
  "components": {
    "database": {...},
    "yolo": {...},
    "qwen": {...},
    "cache": {...}
  }
}
```

**权限**: 公开 | **源码**: [main.py](../src/web/backend/app/main.py)

---

### GET /health/database — 数据库健康检查

```bash
curl http://localhost:8000/api/v1/health/database
```

**成功响应 (200)**:
```json
{
  "status": "healthy",
  "database": "wheatagent",
  "connection_time_ms": 2.34,
  "table_count": 15,
  "pool_status": "active"
}
```

**错误响应 (503)**:
```json
{
  "detail": "数据库连接失败：Connection refused"
}
```

**权限**: 公开 | **源码**: [health.py](../src/web/backend/app/api/v1/health.py)

---

### GET /health/startup — 启动状态检查

**返回应用启动进度和各组件初始化状态。**

```bash
curl http://localhost:8000/api/v1/health/startup
```

**成功响应 (200)**:
```json
{
  "status": "ready",
  "progress": 100,
  "phase": "ready",
  "components": {
    "database": {
      "status": "ready",
      "progress": 100,
      "message": "数据库就绪"
    },
    "yolo": {
      "status": "ready",
      "progress": 100,
      "message": "YOLO 模型加载完成"
    },
    "qwen": {
      "status": "ready",
      "progress": 100,
      "message": "Qwen 模型加载完成"
    },
    "cache": {
      "status": "ready",
      "progress": 100,
      "message": "缓存就绪"
    }
  },
  "elapsed_time": 45.2,
  "estimated_remaining_time": 0
}
```

**启动阶段说明**:

| 阶段 | 进度范围 | 说明 |
|------|---------|------|
| INIT | 0-20% | 基础服务初始化 (配置/GPU检测) |
| DATABASE | 20-40% | 数据库连接池初始化 |
| AI_LOADING | 40-90% | AI 模型加载 (YOLO + Qwen) |
| SERVICES | 90-100% | 服务组件初始化 (缓存/融合验证) |

**权限**: 公开 | **源码**: [health.py](../src/web/backend/app/api/v1/health.py)

---

### GET /health/ready — 就绪状态检查

**检查应用是否已完全就绪可以接受请求。**

```bash
curl http://localhost:8000/api/v1/health/ready
```

**成功响应 (200)**:
```json
{
  "ready": true,
  "degraded": false,
  "failed": false,
  "status": "ready",
  "critical_components": {
    "database": true,
    "yolo": true,
    "qwen": true
  },
  "all_components_ready": true,
  "message": "服务已就绪"
}
```

**权限**: 公开 | **源码**: [health.py](../src/web/backend/app/api/v1/health.py)

---

### GET /health/components — 组件状态检查

**返回所有组件的详细状态信息。**

```bash
curl http://localhost:8000/api/v1/health/components
```

**成功响应 (200)**:
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "ready",
      "name": "wheatagent",
      "connection_time_ms": 1.23
    },
    "yolo": {
      "status": "ready",
      "model_path": "pretrained",
      "confidence_threshold": 0.5
    },
    "qwen": {
      "status": "ready",
      "model_path": "/models/qwen",
      "device": "cuda",
      "int4_quantization": true,
      "features": {
        "kad_former": true,
        "graph_rag": true
      }
    },
    "cache": {
      "status": "ready",
      "cache_size": 128
    }
  },
  "summary": {
    "total": 4,
    "ready": 4,
    "failed": 0,
    "degraded": 0
  }
}
```

**权限**: 公开 | **源码**: [health.py](../src/web/backend/app/api/v1/health.py)

---

## ⑨ 高级特性

### POST /upload/image — 上传图像文件

**上传图像文件到服务器（用于后续诊断）。**

```bash
curl -X POST http://localhost:8000/api/v1/upload/image \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "image=@/path/to/wheat_disease.jpg"
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image | file | 是 | 图像文件 (JPG/PNG/WEBP, ≤10MB) |

**文件验证**:
- ✅ MIME 类型白名单
- ✅ Magic Number 二进制校验
- ✅ 文件大小限制 (≤10MB)
- ✅ UUID 重命名防冲突

**成功响应 (200)**:
```json
{
  "success": true,
  "url": "/uploads/diagnosis/550e8400-e29b-41d4-a716-446655440000.jpg",
  "filename": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "size": 1048576,
  "content_type": "image/jpeg",
  "message": "文件上传成功"
}
```

**权限**: 需要认证 | **限流**: 10 次/分钟 | **源码**: [upload.py](../src/web/backend/app/api/v1/upload.py)

---

### GET /metrics — Prometheus 监控指标

**暴露 Prometheus 格式的性能指标。**

```bash
curl http://localhost:8000/api/v1/metrics
```

**响应内容**: Prometheus 文本格式指标

**指标类型**:
- 推理延迟 (p50, p95, p99)
- 吞吐量 (req/s)
- 错误率
- GPU 显存占用
- 缓存命中率

**权限**: 公开 | **源码**: [metrics.py](../src/web/backend/app/api/v1/metrics.py)

---

### GET /logs/statistics — 诊断日志统计 (管理员)

**获取诊断操作的统计分析数据。**

```bash
curl "http://localhost:8000/api/v1/logs/statistics?duration_hours=24" \
  -H "Authorization: Bearer <admin_token>"
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| duration_hours | integer | 否 | 24 | 统计时长 (小时, 1-720) |

**成功响应 (200)**:
```json
{
  "success": true,
  "data": {
    "total_diagnoses": 1500,
    "success_rate": 0.95,
    "avg_confidence": 0.87,
    "top_diseases": [...]
  },
  "timestamp": "2026-04-05T12:00:00"
}
```

**权限**: 仅管理员 (Admin) | **限流**: 60 次/分钟 | **源码**: [logs.py](../src/web/backend/app/api/v1/logs.py)

---

### GET /logs/disease-distribution — 病害分布统计 (管理员)

**获取病害类型分布统计数据。**

```bash
curl "http://localhost:8000/api/v1/logs/disease-distribution?duration_hours=168" \
  -H "Authorization: Bearer <admin_token>"
```

**权限**: 仅管理员 (Admin) | **限流**: 60 次/分钟 | **源码**: [logs.py](../src/web/backend/app/api/v1/logs.py)

---

### GET / — 根路径 (应用信息)

```bash
curl http://localhost:8000/
```

**成功响应 (200)**:
```json
{
  "name": "基于多模态融合的小麦病害诊断系统",
  "version": "1.0.0",
  "docs": "/docs"
}
```

**权限**: 公开 | **源码**: [main.py](../src/web/backend/app/main.py)

---

## 错误码索引

按前缀分组的完整错误码体系，用于精确定位问题原因。

### HTTP 状态码速查

| 状态码 | 类别 | 说明 |
|--------|------|------|
| 200 | 成功 | 请求成功处理 |
| 201 | 创建 | 资源创建成功 |
| 400 | 客户端错误 | 请求参数错误/验证失败 |
| 401 | 未授权 | 无效或过期 Token |
| 403 | 禁止访问 | 权限不足/账号禁用 |
| 404 | 未找到 | 资源不存在 |
| 405 | 方法不允许 | HTTP 方法不匹配 |
| 409 | 冲突 | 资源已存在 |
| 413 | 实体过大 | 请求体超出限制 |
| 422 | 验证失败 | 数据格式校验未通过 |
| 429 | 过多请求 | 请求频率超限 |
| 500 | 服务器错误 | 内部错误 |
| 502 | 网关错误 | 上游服务异常 |
| 503 | 服务不可用 | 服务维护/过载 |
| 504 | 网关超时 | 上游服务响应超时 |
| 507 | 存储不足 | 磁盘空间不够 |

---

### AUTH_ 认证授权

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| AUTH_001 | 200 | 邮箱已被注册 | 使用其他邮箱 |
| AUTH_002 | 200 | 用户名已被使用 | 选择其他用户名 |
| AUTH_003 | 403 | 账号已被禁用 | 联系管理员解除禁用 |
| AUTH_004 | 403 | 权限不足 | 检查角色权限 |
| AUTH_005 | 400 | 用户名格式无效 | 检查用户名规范 (3-50字符, 字母数字下划线) |
| AUTH_009 | 403 | 登录失败次数过多 | 等待锁定时间结束或联系管理员 |
| AUTH_010 | 400 | 密码强度不足 | 包含字母+数字, 至少6位 |

---

### DIAG_ 诊断服务

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| DIAG_001 | 500 | 诊断失败 | 稍后重试 |
| DIAG_002 | 400 | 图像上传失败 | 检查图像文件有效性 |
| DIAG_003 | 400 | 图像格式不支持 | 使用 JPG/PNG/WEBP |
| DIAG_004 | 400 | 图像大小超限 | ≤ 10MB |
| DIAG_005 | 404 | 诊断记录不存在 | 检查 ID 正确性 |
| DIAG_006 | 400 | 图像解析失败 | 上传有效图像文件 |
| DIAG_007 | 504 | 诊断任务超时 | 稍后查看结果 |
| DIAG_008 | 500 | 结果保存失败 | 稍后重试 |
| DIAG_009 | 400 | 图像质量不足 | 上传更清晰的图像 |
| DIAG_010 | 400 | 未检测到病害区域 | 确保图像包含病害 |
| DIAG_011 | 400 | 批量数量超限 | 单次 ≤ 10 张 |

---

### AI_ AI 服务

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| AI_001 | 503 | AI 服务不可用 | 服务启动/维护中, 稍后重试 |
| AI_002 | 500 | 模型加载失败 | 联系技术支持 |
| AI_003 | 500 | 模型推理失败 | 稍后重试 |
| AI_004 | 404 | 模型不存在 | 检查模型名称 |
| AI_006 | 504 | AI 服务超时 | 推理时间长, 稍后重试 |
| AI_007 | 500 | 模型配置错误 | 联系技术支持 |
| AI_008 | 503 | GPU 内存不足 | 服务器资源紧张, 稍后重试 |
| AI_009 | 500 | 多模态融合失败 | 稍后重试 |

---

### FILE_ 文件处理

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| FILE_001 | 500 | 文件上传失败 | 稍后重试 |
| FILE_002 | 400 | 文件类型不支持 | 使用允许的类型 |
| FILE_003 | 413 | 文件大小超限 | 减小文件尺寸 |
| FILE_004 | 404 | 文件不存在 | 检查路径正确性 |
| FILE_005 | 500 | 文件读取失败 | 文件可能损坏 |
| FILE_007 | 400 | 文件名非法 | 检查文件名规范 |

---

### SYS_ 系统

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| SYS_001 | 500 | 系统内部错误 | 稍后重试 |
| SYS_002 | 503 | 服务不可用 | 维护中, 稍后重试 |
| SYS_003 | 400 | 请求参数错误 | 检查参数格式 |
| SYS_004 | 405 | 方法不允许 | 使用正确的 HTTP 方法 |
| SYS_005 | 429 | 请求频率超限 | 降低频率, 稍后重试 |
| SYS_006 | 404 | 资源不存在 | 检查路径 |
| SYS_007 | 504 | 服务超时 | 稍后重试 |
| SYS_008 | 403 | 功能暂未开放 | 敬请期待 |

---

### USER_ 用户

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| USER_001 | 409 | 用户已存在 | 使用其他用户名 |
| USER_002 | 409 | 邮箱已注册 | 使用其他邮箱 |
| USER_003 | 404 | 用户不存在 | 检查用户名 |
| USER_007 | 400 | 原密码错误 | 输入正确原密码 |

---

### DB_ 数据库

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| DB_001 | 500 | 数据库连接失败 | 稍后重试 |
| DB_002 | 500 | 查询错误 | 稍后重试 |
| DB_003 | 500 | 插入失败 | 检查数据格式 |
| DB_004 | 500 | 更新失败 | 稍后重试 |
| DB_005 | 500 | 删除失败 | 稍后重试 |
| DB_006 | 409 | 数据已存在 | 检查重复数据 |
| DB_009 | 400 | 外键约束错误 | 关联数据问题 |

---

### VALIDATION_ 验证

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| VALIDATION_001 | 422 | 参数验证失败 | 检查参数格式 |
| VALIDATION_002 | 422 | 必填字段缺失 | 填写必填字段 |
| VALIDATION_003 | 422 | 字段格式错误 | 检查字段格式 |
| VALIDATION_004 | 422 | 字段长度超限 | 缩短内容 |
| VALIDATION_005 | 422 | 值不在范围内 | 使用有效值 |

---

### KG_ 知识图谱

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| KG_001 | 500 | 知识图谱查询失败 | 稍后重试 |
| KG_002 | 404 | 实体不存在 | 未找到实体 |
| KG_003 | 404 | 关系不存在 | 未找到关系 |
| KG_004 | 500 | 图谱连接失败 | Neo4j 不可用 |

---

### RATE_ 限流

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|--------|---------|------|----------|
| RATE_EXCEEDED | 429 | 请求频率超限 | 降低请求频率 |
| RATE_QUEUE_FULL | 429 | 队列已满 | 稍后重试 |
| RATE_TIMEOUT | 429 | 等待超时 | 稍后重试 |

---

## 数据模型

### DiagnosisResponse (诊断响应)

```json
{
  "diagnosis_id": "uuid-string",
  "disease_name": "小麦条锈病",
  "disease_name_en": "Wheat Stripe Rust",
  "confidence": 0.95,
  "visual_confidence": 0.96,
  "textual_confidence": 0.92,
  "knowledge_confidence": 0.88,
  "severity": "high",
  "description": "多模态融合诊断结果",
  "symptoms": "叶片出现黄色条状病斑...",
  "causes": "由条形柄锈菌引起",
  "recommendations": ["选用抗病品种", "喷洒杀菌剂"],
  "treatment": "发病初期喷施三唑酮",
  "medicines": ["三唑酮", "丙环唑"],
  "roi_boxes": [
    {
      "x1": 100,
      "y1": 150,
      "x2": 300,
      "y2": 350,
      "confidence": 0.95,
      "class": "stripe_rust"
    }
  ],
  "inference_time_ms": 2345.67,
  "kad_former_used": true,
  "created_at": "2026-04-05T12:00:00Z"
}
```

---

### UserResponse (用户信息)

```json
{
  "id": 1,
  "username": "farmer_zhang",
  "email": "farmer@example.com",
  "phone": "13800138000",
  "avatar_url": "/uploads/avatars/avatar_1.jpg",
  "role": "farmer",
  "is_active": true,
  "created_at": "2026-04-05T10:30:00Z",
  "updated_at": "2026-04-05T10:30:00Z"
}
```

**角色枚举**:
- `farmer` - 农户
- `technician` - 农技人员
- `admin` - 系统管理员

---

### DiseaseResponse (病害知识)

```json
{
  "id": 1,
  "name": "小麦条锈病",
  "code": "WHEAT_STRIPE_RUST",
  "category": "真菌病害",
  "symptoms": "叶片上出现条状黄色锈斑...",
  "causes": "由条形柄锈菌引起...",
  "treatments": "喷施三唑酮可湿性粉剂...",
  "prevention": "选用抗病品种...",
  "severity": 0.7,
  "created_at": "2026-04-05T10:30:00Z",
  "updated_at": "2026-04-05T10:30:00Z"
}
```

**病害分类**:
- `fungal` - 真菌病害
- `bacterial` - 细菌病害
- `viral` - 病毒病害
- `pest` - 虫害
- `nutritional` - 生理性病害

---

### FusionResult (融合诊断结果)

```json
{
  "success": true,
  "diagnosis": { /* DiagnosisResponse */ },
  "features": {
    "thinking_mode": true,
    "graph_rag": true,
    "mock_mode": false
  },
  "performance": {
    "inference_time_ms": 2345.67,
    "cache_hit": false,
    "thinking_mode_enabled": true,
    "graph_rag_enabled": true
  },
  "message": "多模态融合诊断成功"
}
```

---

### SSEEvent (SSE 事件数据)

**ProgressEvent (进度事件)**:
```json
{
  "stage": "visual",
  "progress": 30,
  "message": "正在提取视觉特征 (YOLOv8)...",
  "timestamp": 1712000000.789
}
```

**HeartbeatEvent (心跳事件)**:
```json
{
  "timestamp": 1712000015.123,
  "message": "heartbeat"
}
```

**LogEvent (日志事件)**:
```json
{
  "level": "INFO",
  "message": "视觉特征提取完成",
  "timestamp": 1712000001.012
}
```

**Stage 枚举值**:
- `init` - 初始化
- `visual` - 视觉特征提取 (YOLOv8)
- `knowledge` - 知识检索 (GraphRAG)
- `textual` - 文本语义提取 (Qwen3-VL)
- `fusion` - 多模态融合 (KAD-Former)
- `complete` - 完成

---

### ErrorResponse (统一错误响应)

```json
{
  "success": false,
  "error": "错误描述信息",
  "error_code": "AUTH_001"
}
```

**带解决方案的错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "邮箱已被注册",
    "solution": "请使用其他邮箱地址"
  }
}
```

**Pydantic 验证错误**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 附录

### A. 源码位置参考

| 模块 | 路径 | 行数 | 职责 |
|------|------|------|------|
| 应用入口 | `app/main.py` | 435 | FastAPI 工厂, 路由注册, 中间件链 |
| AI 诊断主路由 | `app/api/v1/diagnosis_router.py` | 1626 | **11 个 AI 诊断端点** |
| 薄包装层 | `app/api/v1/ai_diagnosis.py` | 49 | 向后兼容重导出 |
| SSE 流管理器 | `app/api/v1/sse_stream_manager.py` | 352 | SSE 事件标准化, 心跳, 背压控制 |
| 请求验证器 | `app/api/v1/diagnosis_validator.py` | 301 | 文件验证, Mock 切换, 并发控制 |
| 用户认证 | `app/api/v1/user.py` | 962 | 注册/登录/JWT/会话管理 |
| 传统诊断 | `app/api/v1/diagnosis.py` | 665 | 诊断 CRUD, 图像上传 |
| 知识库 | `app/api/v1/knowledge.py` | 326 | 病害知识 CRUD, 搜索 |
| 报告生成 | `app/api/v1/reports.py` | 139 | PDF/HTML 报告 |
| 健康检查 | `app/api/v1/health.py` | 218 | 组件状态监控 |
| 统计数据 | `app/api/v1/stats.py` | 165 | 业务统计聚合 |
| 文件上传 | `app/api/v1/upload.py` | 100 | 图像上传验证 |
| 监控指标 | `app/api/v1/metrics.py` | 391 | Prometheus 指标 |
| 日志查询 | `app/api/v1/logs.py` | 221 | 诊断日志分析 |
| 融合门面 | `app/services/fusion_service.py` | 649 | 多模态融合协调器 |
| 特征提取器 | `app/services/fusion_feature_extractor.py` | 424 | YOLO+Qwen+GraphRAG |
| 融合引擎 | `app/services/fusion_engine.py` | 467 | KAD-Former 注意力融合 |
| 结果标注器 | `app/services/fusion_annotator.py` | 269 | ROI 标注, 缓存写入 |
| 错误码定义 | `app/core/error_codes.py` | 928 | 统一错误码体系 |
| 安全认证 | `app/core/security.py` | 277 | JWT, 角色, 密码哈希 |

---

### B. 中间件链

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
- `Permissions-Policy: camera=(), microphone=(), ...`

---

### C. 测试工具

| 工具 | URL | 说明 |
|------|-----|------|
| Swagger UI | http://localhost:8000/docs | 交互式 API 文档 |
| ReDoc | http://localhost:8000/redoc | 只读 API 文档 |
| OpenAPI JSON | http://localhost:8000/openapi.json | OpenAPI 3.0 规范 |

---

### D. 请求规范

**通用请求头**:
```http
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <uuid>
```

**响应格式**:
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

**时间格式**: ISO 8601 (`2026-04-05T12:00:00Z`)

**分页参数**:
- `skip`: 跳过记录数 (默认 0)
- `limit`: 返回数量 (默认 20, 最大 1000)

---

**文档版本**: V12.0
**最后更新**: 2026-04-05
**维护者**: WheatAgent 团队
**基于代码实际状态生成** ✅
