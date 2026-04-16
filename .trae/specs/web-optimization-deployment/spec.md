# Web 端性能优化和部署 Spec

## Why
当前 Web 端前后端集成开发已完成核心功能开发（任务 1-6），但还需要进行性能优化和调试以提升系统性能，同时需要编写完整的部署文档和使用说明以支持实际部署和使用。

## What Changes
- **性能优化**: 添加数据库索引、配置 Redis 缓存、优化前端加载速度
- **系统调试**: 调试系统问题、进行性能测试
- **文档完善**: 编写部署文档、使用说明、更新 API 文档
- **部署配置**: 创建 Docker Compose 配置（可选）

## Impact
- 受影响系统：数据库（索引优化）、缓存层（Redis 集成）、前端（懒加载优化）
- 受影响文件：数据库模型、缓存配置、前端组件、文档文件

## ADDED Requirements

### Requirement: 数据库查询优化
系统 SHALL 为高频查询字段添加索引以提升查询性能：
- diagnosis_records 表的 user_id、created_at 字段
- users 表的 username、email 字段
- knowledge_base 表的 category、disease_name 字段

#### Scenario: 查询诊断记录
- **WHEN** 用户查询历史诊断记录
- **THEN** 系统应通过索引快速定位记录，查询时间 < 100ms

### Requirement: Redis 缓存配置
系统 SHALL 使用 Redis 缓存诊断结果以减少重复计算：
- 缓存相同图像的 MD5 哈希对应的诊断结果
- 缓存过期时间设置为 24 小时
- 缓存命中率目标 > 60%

#### Scenario: 重复图像诊断
- **WHEN** 用户上传已诊断过的图像
- **THEN** 系统应从缓存中返回结果，响应时间 < 500ms

### Requirement: 前端懒加载优化
前端 SHALL 实现组件和路由的懒加载以提升初始加载速度：
- 路由级别懒加载（使用 Vue Router 的 dynamic import）
- 大型组件懒加载（如知识库详情、诊断结果详情）
- 初始加载时间目标 < 2 秒

#### Scenario: 页面加载
- **WHEN** 用户首次访问系统
- **THEN** 初始页面应在 2 秒内加载完成

### Requirement: 部署文档
系统 SHALL 提供完整的部署文档，包括：
- 开发环境部署步骤
- 生产环境部署步骤
- 数据库初始化流程
- 环境变量配置说明

### Requirement: 使用说明文档
系统 SHALL 提供用户使用说明，包括：
- 用户注册和登录流程
- 图像诊断操作流程
- 诊断记录查看方法
- 知识库使用方法

### Requirement: API 文档更新
系统 SHALL 更新 API 文档，包括：
- 所有 API 端点的详细说明
- 请求参数和响应格式
- 认证方式和错误码说明

## MODIFIED Requirements

### Requirement: 诊断服务性能
**原要求**: 诊断响应时间 < 5 秒
**修改后**: 诊断响应时间 < 3 秒（首次诊断），< 500ms（缓存命中）

## REMOVED Requirements

无

## 性能目标

1. **数据库查询性能**: 95% 的查询响应时间 < 100ms
2. **缓存命中率**: > 60%
3. **前端加载速度**: 初始加载 < 2 秒，页面切换 < 500ms
4. **API 响应时间**: 95% 的 API 请求 < 1 秒（不含 AI 诊断）
5. **系统并发能力**: 支持 100+ 并发用户

## 技术栈

- **数据库**: MySQL 8.0（索引优化）
- **缓存**: Redis 7.2（诊断结果缓存）
- **前端**: Vue 3 + Vite（路由懒加载）
- **后端**: FastAPI（异步支持）
- **部署**: Docker + Docker Compose
