# CUDA版PyTorch + BitsAndBytes安装与INT4量化部署 Spec

## Why

在完成4bit量化部署测试后，识别出当前环境存在以下问题：
1. PyTorch为CPU版本（2.10.0+cpu），不支持CUDA GPU加速
2. BitsAndBytes未安装，无法进行INT4量化

需要安装CUDA版PyTorch和BitsAndBytes，以实现真正的INT4量化GPU部署，显著提升模型推理速度。

## What Changes

### 环境安装
- 卸载CPU版PyTorch
- 安装CUDA 12.1版PyTorch（GPU版本）
- 安装BitsAndBytes（INT4量化库）
- 验证CUDA环境可用性

### 模型配置
- 更新qwen_service.py量化配置
- 验证INT4量化加载
- 测试GPU推理性能

### 部署验证
- 重启后端服务
- 验证模型GPU加载成功
- 测试诊断功能完整性

**无破坏性变更**

## Impact

- **影响的代码**:
  - `app/services/qwen_service.py` - Qwen服务加载逻辑
  - conda环境配置
  - Python依赖包

- **影响的功能**:
  - 多模态诊断功能
  - AI模型推理性能
  - GPU加速能力

## ADDED Requirements

### Requirement: CUDA版PyTorch安装
系统 SHALL 安装CUDA版PyTorch，支持GPU加速计算。

#### Scenario: PyTorch GPU版本安装成功
- **WHEN** 执行PyTorch安装命令
- **THEN** PyTorch GPU版本安装成功
- **THEN** CUDA版本匹配（12.1）
- **THEN** `torch.cuda.is_available()` 返回 True

### Requirement: BitsAndBytes安装
系统 SHALL 安装BitsAndBytes库，支持INT4量化。

#### Scenario: BitsAndBytes安装成功
- **WHEN** 执行BitsAndBytes安装
- **THEN** 安装成功
- **THEN** 可导入 `bitsandbytes`
- **THEN** `BitsAndBytesConfig` 可用

### Requirement: INT4量化GPU加载
系统 SHALL 使用INT4量化加载Qwen3-VL模型到GPU。

#### Scenario: GPU量化加载成功
- **WHEN** 启动后端服务
- **THEN** 模型使用INT4量化加载
- **THEN** 模型加载到GPU
- **THEN** 显存占用 < 4GB
- **THEN** 推理功能正常

### Requirement: GPU推理性能验证
系统 SHALL 验证GPU推理性能优于CPU。

#### Scenario: 性能验证
- **WHEN** 执行推理测试
- **THEN** GPU推理延迟显著降低
- **THEN** 诊断功能返回正确结果

## MODIFIED Requirements

无

## REMOVED Requirements

无
