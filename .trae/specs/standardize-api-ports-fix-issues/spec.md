# 接口与端口标准化规范及问题解决 Spec

## Why
当前系统存在以下问题：
1. 现有 API 文档（API_REFERENCE.md）与实际接口存在不一致（如认证路径 `/api/v1/auth/login` vs `/api/v1/users/login`）
2. 端口使用缺乏统一规范（8000/8001 混用）
3. 存在 6 个已识别但未完全解决的问题（P001-P006）
4. 错误码体系不完整，响应格式不统一

## What Changes
1. **接口标准化**
   - 统一 API 路径前缀：`/api/v1/{module}/{resource}`
   - 统一请求/响应格式（code/message/data/error 结构）
   - 完善错误码体系（HTTP 状态码 + 业务错误码）
   - 添加 API 版本控制策略（URL 版本 vs Header 版本）

2. **端口标准化**
   - Web 服务：80/443
   - API 服务：8000
   - AI 模型服务：8001-8010
   - 数据库：3306
   - Redis：6379

3. **问题解决**
   - P001: 用户注册接口 500 错误
   - P002: 重复注册错误处理不当
   - P003: 后端服务连接不稳定
   - P004: 诊断服务集成问题
   - P005: 前端服务未运行
   - P006: 测试覆盖率不足

## Impact
- Affected specs: 所有 API 服务、端口配置、测试框架
- Affected code: `app/api/v1/*`, `app/core/config.py`, `tests/*`

## ADDED Requirements

### Requirement: 统一 API 响应格式
所有 API 响应 SHALL 使用统一的 JSON 格式：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": { ... },
  "timestamp": "2026-03-13T12:00:00Z"
}
```

错误响应：
```json
{
  "success": false,
  "code": 400,
  "error": {
    "code": "AUTH_001",
    "message": "用户名或密码错误",
    "detail": "请检查用户名和密码是否正确"
  },
  "timestamp": "2026-03-13T12:00:00Z"
}
```

### Requirement: 端口分配规范
| 端口范围 | 服务类型 | 示例 |
|---------|---------|------|
| 80/443 | Web 前端 | Nginx/Apache |
| 8000 | API 网关/主服务 | FastAPI Main |
| 8001-8010 | AI 模型服务 | YOLO, Qwen, Fusion |
| 3306 | MySQL 数据库 | - |
| 6379 | Redis 缓存 | - |
| 9000 | MinIO 对象存储 | - |

### Requirement: 问题优先级排序
| 优先级 | 问题 | 影响范围 |
|--------|------|---------|
| P0 | P001-P003 | 系统崩溃/数据丢失 |
| P1 | P004 | 核心功能不可用 |
| P2 | P005-P006 | 开发和测试受阻 |

## MODIFIED Requirements

### Requirement: API 路径规范
原：`POST /api/v1/auth/login` → 新：`POST /api/v1/users/login`

### Requirement: 错误码体系
扩展现有错误码，添加：
- `SYS_XXX`: 系统错误
- `DB_XXX`: 数据库错误
- `AI_XXX`: AI 服务错误

## 问题清单

### P001: 用户注册接口 500 错误
- **状态**: 待修复
- **根因**: 可能是 bcrypt 兼容性问题或数据库约束
- **修复方案**: 检查 user.py 注册逻辑，添加唯一性约束验证

### P002: 重复注册错误处理不当
- **状态**: 待修复
- **根因**: 缺少唯一性检查
- **修复方案**: 添加邮箱和用户名唯一性预检查

### P003: 后端服务连接不稳定
- **状态**: 待修复
- **根因**: Windows 环境下 uvicorn worker 配置不当
- **修复方案**: 优化连接池配置，添加重试机制

### P004-P006: 详见 TEST_ISSUES.md
