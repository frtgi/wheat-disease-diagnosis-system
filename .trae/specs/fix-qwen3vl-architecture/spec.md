# Qwen3-VL 模型架构不匹配修复 Spec

## Why
使用 `Qwen2VLForConditionalGeneration` 加载 `Qwen3-VL-4B-Instruct` 模型时发生架构不匹配错误，导致模型加载失败。Qwen3-VL 和 Qwen2-VL 架构存在差异，需要使用正确的加载方式。

## What Changes
- 修改 `qwen_service.py` 中的模型加载逻辑
- 添加 `ignore_mismatched_sizes=True` 参数支持
- 使用 `AutoModelForVision2Seq` 或正确的模型类
- 优化降级模式处理

## Impact
- Affected specs: AI 模型加载、诊断服务
- Affected code: `src/web/backend/app/services/qwen_service.py`

## ADDED Requirements

### Requirement: Qwen3-VL 模型正确加载
系统 SHALL 正确加载 Qwen3-VL-4B-Instruct 模型，处理架构差异。

#### Scenario: 模型加载成功
- **WHEN** 系统启动并加载 Qwen3-VL 模型
- **THEN** 模型应正确加载，无 MISMATCH 错误

#### Scenario: 降级模式
- **WHEN** 模型加载失败
- **THEN** 系统应自动降级到文本诊断模式

## 错误详情

### 错误类型
模型架构不匹配 (Model Architecture Mismatch)

### 错误信息
```
ERROR:app.services.qwen_service:Qwen3-VL 模型加载失败：You set `ignore_mismatched_sizes` to `False`, thus raising an error.
```

### 关键警告
```
You are using a model of type qwen3_vl to instantiate a model of type qwen2_vl. This is not supported for all configurations of models and can yield errors.
```

### 触发条件
1. 使用 `Qwen2VLForConditionalGeneration` 加载 Qwen3-VL 模型
2. 模型权重形状与预期架构不匹配
3. `ignore_mismatched_sizes` 参数设置为 `False`

### 根本原因
Qwen3-VL 是 Qwen2-VL 的升级版本，架构有所变化：
- 视觉编码器维度不同 (1024 vs 1280)
- 注意力层结构不同
- MLP 层结构不同
