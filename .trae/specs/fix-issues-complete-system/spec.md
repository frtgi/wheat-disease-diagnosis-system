# 问题修复与系统完善 Spec

## Why

根据全面测试报告（TEST_REPORT_FULL.md），发现 6 个关键问题影响系统正常运行：
1. 用户注册接口 500 错误（严重）
2. 重复注册错误处理不当（严重）
3. 后端服务连接不稳定（严重）
4. 诊断服务集成问题（中等）
5. 前端服务未运行（中等）
6. 测试覆盖率不足（轻微）

需要修复这些问题以确保项目可以正常运行并实现所有功能。

## What Changes

- 修复用户注册接口的 500 错误
- 添加重复注册的 409 错误处理
- 优化后端服务配置（uvicorn、数据库连接池）
- 添加请求重试机制
- 集成诊断 AI 服务或使用 Mock
- 启动前端服务并配置测试
- 提升测试覆盖率至 80%+
- 运行完整系统测试验证

## Impact

- Affected specs: comprehensive-testing, web-development, web-integration
- Affected code: 
  - `src/web/backend/app/api/v1/user.py` - 用户注册逻辑
  - `src/web/backend/app/core/database.py` - 数据库配置
  - `src/web/backend/app/main.py` - 中间件配置
  - `src/web/frontend/` - 前端服务
  - `src/ai_engine/` - 诊断 AI 服务

## ADDED Requirements

### Requirement: 用户注册功能修复
The system SHALL 正确处理用户注册请求并返回适当的错误码

#### Scenario: 新用户注册成功
- **WHEN** 用户提交有效的注册信息
- **THEN** 返回 200 OK 和用户信息

#### Scenario: 重复注册处理
- **WHEN** 用户使用已存在的邮箱或用户名注册
- **THEN** 返回 409 Conflict 和清晰的错误信息

### Requirement: 后端服务稳定性
The system SHALL 在高并发请求下保持稳定连接

#### Scenario: 并发请求处理
- **WHEN** 50 个并发请求同时到达
- **THEN** 成功率 > 99%，平均响应时间 < 200ms

### Requirement: 诊断服务集成
The system SHALL 提供诊断服务（真实或 Mock）

#### Scenario: 文本诊断
- **WHEN** 用户提供症状描述
- **THEN** 返回准确的病害诊断结果

### Requirement: 前端服务
The system SHALL 提供可访问的前端界面

#### Scenario: 前端页面加载
- **WHEN** 用户访问前端 URL
- **THEN** 页面正常加载并显示 WheatAgent 界面

## MODIFIED Requirements

### Requirement: 数据库连接池配置
原配置可能太小，需要优化：
- pool_size: 20
- max_overflow: 40
- pool_pre_ping: true
- pool_recycle: 3600

### Requirement: uvicorn 配置
优化并发处理：
- workers: 4
- loop: uvloop
- http: httptools

## REMOVED Requirements

无
