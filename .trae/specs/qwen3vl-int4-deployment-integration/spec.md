# Qwen3-VL INT4量化部署与前后端集成测试 Spec

## Why
CUDA版PyTorch和BitsAndBytes已成功安装，INT4量化模型加载测试通过（显存占用2.71GB）。现在需要将量化后的Qwen3-VL模型部署到后端服务，并进行完整的前后端集成测试，确保系统各项功能正常运行。

## What Changes
- 将INT4量化的Qwen3-VL模型集成到后端服务
- 启动完整的Web系统（前端+后端+数据库）
- 执行端到端集成测试
- 记录并解决测试中发现的问题
- 生成部署验证报告

## Impact
- Affected specs: web-integration, qwen3vl-4bit-deployment-test
- Affected code: 
  - `src/web/backend/app/services/qwen_service.py` - Qwen服务配置
  - `src/web/backend/app/main.py` - 后端主应用
  - `src/web/frontend/` - 前端应用

## ADDED Requirements

### Requirement: INT4量化模型部署
系统SHALL支持使用INT4量化的Qwen3-VL-4B-Instruct模型进行推理，显存占用应低于4GB。

#### Scenario: 模型加载成功
- **WHEN** 后端服务启动时
- **THEN** Qwen3-VL模型使用INT4量化加载到GPU
- **AND** 显存占用低于4GB

#### Scenario: 模型推理正常
- **WHEN** 用户提交诊断请求
- **THEN** 模型返回正确的诊断结果
- **AND** 推理延迟低于30秒

### Requirement: 前后端集成测试
系统SHALL通过完整的前后端集成测试，确保所有功能正常工作。

#### Scenario: 用户认证流程
- **WHEN** 用户注册并登录
- **THEN** 系统返回有效的JWT Token
- **AND** 用户可以访问受保护的API

#### Scenario: 图像诊断流程
- **WHEN** 用户上传小麦病害图像
- **THEN** 系统返回病害诊断结果
- **AND** 结果包含病害名称、置信度和防治建议

#### Scenario: 文本诊断流程
- **WHEN** 用户输入症状描述
- **THEN** 系统返回基于症状的诊断结果

### Requirement: 问题记录与反馈
系统测试过程中发现的问题SHALL被记录并及时反馈解决。

#### Scenario: 问题记录
- **WHEN** 测试发现功能异常
- **THEN** 问题被记录到问题清单
- **AND** 包含问题描述、严重程度和复现步骤

#### Scenario: 问题解决
- **WHEN** 问题被修复
- **THEN** 更新问题状态为已解决
- **AND** 记录解决方案

## MODIFIED Requirements

### Requirement: 后端服务启动
后端服务SHALL使用wheatagent-py310环境启动，并加载INT4量化模型。

### Requirement: 数据库连接
后端服务SHALL正确连接MySQL数据库，使用配置文件中的连接参数。

## REMOVED Requirements
无
