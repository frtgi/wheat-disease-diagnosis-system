# 前后端集成测试 Spec

## Why

基于 Qwen3-VL-4B-Instruct 原生多模态架构的小麦病害诊断智能体（IWDDA）需要进行全面的集成测试，验证系统各项服务的功能完整性、接口通信有效性及数据流转正确性，确保诊断功能的可靠性和准确性。

## What Changes

### 测试范围
- 用户认证流程集成测试
- 小麦病害诊断功能集成测试（YOLOv8 + Qwen3-VL-4B）
- 知识图谱查询集成测试
- 多模态诊断流程测试
- 云边协同架构测试

### 测试类型
- 端到端业务流程测试
- API 接口集成测试
- 数据流转验证测试
- 边界条件测试
- 异常场景测试

**无破坏性变更**

## Impact

- **影响的代码**:
  - `app/api/v1/` - 所有 API 端点
  - `app/services/` - 核心服务层
  - `frontend/src/views/` - 前端页面
  - `frontend/src/api/` - API 调用层

- **影响的功能**:
  - 用户认证与授权
  - 小麦病害图像诊断
  - 多模态诊断（图像+文本）
  - 知识图谱查询
  - AI 模型服务

## ADDED Requirements

### Requirement: INT4 量化加载支持
系统 SHALL 支持 Qwen3-VL-4B 的 INT4 量化加载，在显存不足时自动启用 CPU offload。

#### Scenario: INT4 量化加载成功
- **WHEN** 启动后端服务
- **THEN** Qwen3-VL-4B 使用 INT4 量化加载
- **THEN** 显存占用 < 4GB
- **THEN** 模型加载成功

### Requirement: CPU Offload 支持
系统 SHALL 在 GPU 显存不足时自动启用 CPU offload，确保模型能正常加载。

#### Scenario: 自动 CPU Offload
- **WHEN** GPU 显存不足
- **THEN** 系统自动启用 llm_int8_enable_fp32_cpu_offload
- **THEN** 模型成功加载到 CPU/GPU 混合模式
- **THEN** 诊断功能正常工作

### Requirement: 端到端业务流程测试
系统 SHALL 通过完整的业务流程测试，验证从用户登录到诊断结果输出的全链路功能。

#### Scenario: 小麦病害诊断完整流程
- **WHEN** 用户上传小麦病害图像
- **THEN** YOLOv8 检测病灶区域
- **THEN** Qwen3-VL-4B 进行多模态诊断
- **THEN** 返回诊断结果和防治建议

### Requirement: API 接口集成测试
系统 SHALL 通过 API 集成测试，验证前后端接口通信的正确性。

#### Scenario: 认证 API 集成
- **WHEN** 前端调用登录 API
- **THEN** 返回有效的 JWT 令牌
- **THEN** 令牌可用于后续 API 调用

### Requirement: 数据流转验证测试
系统 SHALL 通过数据流转测试，验证数据在各模块间的正确传递。

#### Scenario: 诊断数据流转
- **WHEN** 图像上传到后端
- **THEN** 数据正确存储到数据库
- **THEN** AI 模型正确接收数据
- **THEN** 诊断结果正确返回前端

### Requirement: 边界条件测试
系统 SHALL 通过边界条件测试，验证系统在极端情况下的表现。

#### Scenario: 大文件上传测试
- **WHEN** 上传超过 10MB 的图像
- **THEN** 系统正确处理或拒绝

### Requirement: 异常场景测试
系统 SHALL 通过异常场景测试，验证系统的错误处理能力。

#### Scenario: AI 模型不可用
- **WHEN** AI 模型服务不可用
- **THEN** 系统返回友好的错误信息
- **THEN** 不影响其他功能使用

## MODIFIED Requirements

无

## REMOVED Requirements

无
