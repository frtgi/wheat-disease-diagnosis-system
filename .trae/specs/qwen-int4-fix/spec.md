# Qwen3-VL-4B INT4 量化修复与重测 Spec

## Why

在之前的集成测试中，Qwen3-VL-4B 模型因 GPU 显存不足无法加载，即使使用 INT4 量化也失败。需要修复量化加载逻辑，确保模型能正常加载并重新执行集成测试。

## What Changes

### Qwen 服务修复
- 修复 INT4 量化加载逻辑
- 添加 CPU offload 支持
- 优化显存分配策略

### 重新测试
- 重启后端服务
- 执行完整集成测试
- 验证所有功能正常

**无破坏性变更**

## Impact

- **影响的代码**:
  - `app/services/qwen_service.py` - Qwen 服务加载逻辑
  - `app/services/ai_preloader.py` - AI 预加载模块

- **影响的功能**:
  - 多模态诊断功能
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
- **THEN** 自动启用 llm_int8_enable_fp32_cpu_offload
- **THEN** 模型部分加载到 CPU
- **THEN** 服务正常启动

## MODIFIED Requirements

无

## REMOVED Requirements

无
