# 修复Conda环境Qwen3-VL加载问题 Spec

## Why
当前后端服务在conda环境中启动时，Qwen3-VL模型未正常加载到GPU，显存占用仅为0.3GB（正常应为2.6GB）。日志显示"bitsandbytes 未安装，使用默认精度加载"，导致模型无法使用INT4量化。

## What Changes
- 分析并修复conda环境配置问题
- 确保bitsandbytes正确安装
- 验证CUDA和PyTorch兼容性
- 重新测试Qwen3-VL GPU加载

## Impact
- Affected specs: fix-fusion-diagnosis-qwen-loading, e2e-integration-test
- Affected code: 
  - qwen_service.py
  - ai_preloader.py
  - conda环境配置

## ADDED Requirements

### Requirement: Conda环境正确配置
系统 SHALL 在conda环境中正确加载所有依赖包。

#### Scenario: bitsandbytes安装验证
- **WHEN** 检查conda环境中的bitsandbytes
- **THEN** bitsandbytes正确安装且可导入

#### Scenario: CUDA可用性验证
- **WHEN** 检查PyTorch CUDA支持
- **THEN** torch.cuda.is_available() 返回 True

### Requirement: Qwen3-VL GPU加载
系统 SHALL 正确加载Qwen3-VL模型到GPU。

#### Scenario: INT4量化加载
- **WHEN** 后端服务启动
- **THEN** Qwen3-VL使用INT4量化加载到GPU，显存占用约2.6GB

#### Scenario: 模型加载日志验证
- **WHEN** 查看后端启动日志
- **THEN** 显示"启用 INT4 量化加载（GPU 模式）"而非"bitsandbytes 未安装"

### Requirement: 端到端测试验证
系统 SHALL 通过端到端集成测试验证模型功能。

#### Scenario: 诊断API响应测试
- **WHEN** 调用诊断API
- **THEN** 返回正确的诊断结果，响应时间在预期范围内

## MODIFIED Requirements
无

## REMOVED Requirements
无
