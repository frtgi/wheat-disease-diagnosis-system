# AI 服务集成与系统修复 Spec

## Why

在系统运行测试中发现以下问题需要解决：
1. 后端服务启动时缺少 `dotenv` 模块导致无法启动
2. 需要确保数据库连接稳定可靠
3. 需要将已开发的 AI 服务（YOLOv8、Qwen3-VL）集成到 Web 系统，提供真实的诊断功能

## What Changes

- 安装缺失的依赖包（python-dotenv）
- 验证并优化数据库连接配置
- 集成 AI 诊断服务到 Web API
- 创建 AI 服务配置和管理接口
- 添加服务健康检查端点

## Impact

- Affected specs: system-run-verification, web-integration
- Affected code: 后端依赖配置、API 端点、AI 服务集成
- Affected documentation: 部署文档、API 文档

## ADDED Requirements

### Requirement: 依赖管理
The system SHALL 包含所有必需的依赖包

#### Scenario: 后端服务启动
- **WHEN** 启动后端服务
- **THEN** 所有依赖包已安装，无 ModuleNotFoundError

### Requirement: AI 服务集成
The system SHALL 提供 AI 诊断服务接口

#### Scenario: 文本诊断
- **WHEN** 用户提交症状描述
- **THEN** 系统调用 AI 服务并返回诊断结果

#### Scenario: 图像诊断
- **WHEN** 用户上传病害图像
- **THEN** 系统调用 YOLOv8 和 Qwen3-VL 进行分析并返回结果

### Requirement: 服务健康检查
The system SHALL 提供 AI 服务状态监控

#### Scenario: 检查 AI 服务
- **WHEN** 调用 /health/ai 端点
- **THEN** 返回 AI 服务连接状态和模型信息

## MODIFIED Requirements

### Requirement: 数据库连接
原要求数据库连接正常，现增强为：
- 数据库连接池配置优化
- 添加连接健康检查
- 提供数据库状态监控端点

## REMOVED Requirements

无
