# 修复前端融合诊断和Qwen3-VL加载问题 Spec

## Why
当前系统存在以下问题：
1. 前端融合诊断API没有返回诊断结果
2. GraphRAG引擎初始化失败（graphrag_engine.py语法错误）
3. Qwen3-VL显存占用仅0.3GB，未正确加载到GPU

## What Changes
- 修复 graphrag_engine.py 语法错误（第227行）
- 修复融合诊断API返回问题
- 修复 Qwen3-VL GPU加载问题，确保显存占用正常

## Impact
- Affected specs: frontend-backend-integration-test
- Affected code: 
  - graphrag_engine.py
  - qwen_service.py
  - diagnosis.py
  - 融合诊断API

## ADDED Requirements

### Requirement: 修复 GraphRAG 引擎语法错误
系统 SHALL 提供可用的 GraphRAG 引擎。

#### Scenario: GraphRAG 初始化
- **WHEN** 后端服务启动时
- **THEN** GraphRAG 引擎成功初始化，不报语法错误

### Requirement: 融合诊断API返回诊断结果
系统 SHALL 在调用融合诊断API后返回完整的诊断结果。

#### Scenario: 融合诊断API调用
- **WHEN** 前端调用 POST /api/v1/diagnosis/fusion
- **THEN** 返回包含 disease_name, confidence, knowledge_links 的结果

### Requirement: Qwen3-VL GPU加载
系统 SHALL 正确加载 Qwen3-VL 模型到GPU，显存占用应大于2GB。

#### Scenario: Qwen3-VL 模型加载
- **WHEN** 后端服务启动时
- **THEN** 模型加载到GPU，显存占用约2.6GB

## MODIFIED Requirements
无

## REMOVED Requirements
无
