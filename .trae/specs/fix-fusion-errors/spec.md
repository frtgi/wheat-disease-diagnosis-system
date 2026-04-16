# KAD-Former + GraphRAG 融合诊断错误修复 Spec

## Why

根据终端日志分析，当前融合诊断系统存在以下错误需要修复：

1. **错误1**: `object supporting the buffer API required` - 仅文本诊断时发生
2. **错误2**: `No module named 'src'` - GraphRAG 引擎初始化失败
3. **错误3**: `'Qwen3VLModel' object has no attribute 'generate'` - Qwen3-VL 诊断失败

## What Changes

### 错误1: buffer API 错误
- **位置**: `fusion_service.py` 或 `graphrag_service.py`
- **原因**: 尝试将字符串当作字节操作
- **修复**: 确保所有字符串和字节正确处理

### 错误2: 模块导入错误
- **位置**: `graphrag_service.py`
- **原因**: `from src.graph.graphrag_engine import GraphRAGEngine` 使用了绝对导入
- **修复**: 改用相对导入或添加路径

### 错误3: Qwen3-VL generate 方法错误
- **位置**: `qwen_service.py` 或 `fusion_service.py`
- **原因**: Qwen3VLModel 对象没有 `generate` 属性
- **修复**: 检查正确的 API 调用方式

## Impact

- Affected specs: kad-former-graphrag-fusion
- Affected code: 
  - `src/web/backend/app/services/graphrag_service.py`
  - `src/web/backend/app/services/fusion_service.py`
  - `src/web/backend/app/services/qwen_service.py`

## ADDED Requirements

### Requirement: 修复 GraphRAG 服务初始化
The system SHALL 修复 GraphRAG 服务初始化错误，正确导入模块

#### Scenario: GraphRAG 服务初始化
- **WHEN** 系统启动时
- **THEN** GraphRAG 服务正确初始化，不报 "No module named 'src'" 错误

### Requirement: 修复 Qwen3-VL 诊断方法
The system SHALL 修复 Qwen3-VL 诊断方法调用错误

#### Scenario: Qwen3-VL 诊断
- **WHEN** 调用 Qwen3-VL 进行诊断时
- **THEN** 正确调用模型方法，不报 "'generate' attribute" 错误

### Requirement: 修复 buffer API 错误
The system SHALL 修复 buffer API 错误

#### Scenario: 仅文本诊断
- **WHEN** 用户仅输入症状描述进行诊断时
- **THEN** 正确处理字符串/字节，不报 "buffer API" 错误
