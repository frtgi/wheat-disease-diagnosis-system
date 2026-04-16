# 项目问题修复规范

## Why

根据全面问题检查报告，发现 17 个需要修复的问题（排除已确认的 conda 环境依赖）。需要按优先级修复这些问题以确保系统稳定运行。

## What Changes

- 修复 auth.py 模型导入占位符问题
- 修复 GraphRAG 路径计算和接口统一问题
- 修复前端 User.vue 组件导入问题
- 优化模型加载和批处理机制

## Impact

- Affected specs: 认证模块、知识检索模块、用户管理模块
- Affected code:
  - `src/web/backend/app/services/auth.py`
  - `src/web/backend/app/services/graphrag_service.py`
  - `src/web/frontend/src/views/User.vue`

## ADDED Requirements

### Requirement: 认证服务模型导入

认证服务应正确导入数据库模型，确保密码重置、令牌刷新等功能正常工作。

#### Scenario: 模型导入修复
- **WHEN** auth.py 服务初始化时
- **THEN** 应正确导入 PasswordResetToken、RefreshToken、LoginAttempt、UserSession 模型
- **AND** 相关认证功能应正常工作

### Requirement: GraphRAG 路径计算

GraphRAG 服务应正确计算项目根路径，确保引擎导入成功。

#### Scenario: 路径修复
- **WHEN** GraphRAG 服务初始化时
- **THEN** 应正确计算 wheatagent 根目录路径
- **AND** GraphRAGEngine 应成功导入

### Requirement: 前端组件导入

前端组件应正确导入所需的 Element Plus 组件。

#### Scenario: 组件导入修复
- **WHEN** User.vue 组件加载时
- **THEN** 应正确导入 ElMessage 和 ElMessageBox
- **AND** 用户管理功能应正常工作

## MODIFIED Requirements

无修改的需求。

## REMOVED Requirements

### Requirement: requirements.txt 核心依赖
**Reason**: 核心依赖已在 conda 环境 wheatagent-py310 中安装
**Migration**: 无需迁移
