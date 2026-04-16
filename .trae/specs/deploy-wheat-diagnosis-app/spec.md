# 小麦病害诊断实际应用部署 Spec

## Why

基于已完成的深度集成成果（Qwen3.5-4B 原生多模态架构、KAD-Former、DeepStack、Graph-RAG 等），现在需要将这些先进技术转化为实际应用，实现小麦病害诊断的落地部署和演示验证。

## What Changes

### 新增功能
- **诊断 API 端点增强**：支持 Thinking 模式、Graph-RAG 增强、多模态融合等高级特性
- **演示界面集成**：提供 Web UI 或 API 演示界面
- **诊断报告生成**：生成专业的图文诊断报告
- **批量诊断支持**：支持批量图像诊断和数据分析

### 修改内容
- **AI 诊断 API**：扩展参数支持，优化响应格式
- **服务配置**：优化推理参数和缓存策略
- **日志与监控**：添加诊断日志和性能监控

## Impact

- **Affected specs**: 
  - ai-service-integration (扩展)
  - deep-integration-fix (应用落地)
  
- **Affected code**:
  - `app/api/v1/ai_diagnosis.py` - 诊断 API 增强
  - `app/services/qwen_service.py` - 服务优化
  - `app/main.py` - 路由更新
  - `src/web/frontend/` - 演示界面（可选）

## ADDED Requirements

### Requirement: 诊断 API 端点
The system SHALL 提供完整的诊断 API 端点

#### Scenario: 单图像诊断
- **WHEN** 用户上传小麦病害图像
- **THEN** 系统返回诊断结果（病害名称、置信度、防治建议）

#### Scenario: Thinking 模式诊断
- **WHEN** 用户请求详细推理过程
- **THEN** 系统输出完整的推理链和诊断依据

#### Scenario: Graph-RAG 增强诊断
- **WHEN** 系统启用 Graph-RAG
- **THEN** 诊断结果包含知识图谱检索的相关知识和多跳推理

### Requirement: 诊断报告生成
The system SHALL 生成专业的图文诊断报告

#### Scenario: 标准报告
- **WHEN** 诊断完成
- **THEN** 生成包含症状、诊断、防治建议的完整报告

#### Scenario: 详细报告
- **WHEN** 用户请求详细报告
- **THEN** 额外包含推理链、知识图谱引用、环境分析

### Requirement: 批量诊断支持
The system SHALL 支持批量图像诊断

#### Scenario: 批量上传
- **WHEN** 用户上传多张图像
- **THEN** 系统依次诊断并返回汇总结果

### Requirement: 性能监控
The system SHALL 提供诊断性能监控

#### Scenario: 实时监控
- **WHEN** 诊断服务运行
- **THEN** 实时收集延迟、吞吐量、错误率等指标

### Requirement: 演示界面
The system SHALL 提供演示界面（可选）

#### Scenario: Web 演示
- **WHEN** 用户访问演示界面
- **THEN** 可以上传图像、查看诊断结果、导出报告

## MODIFIED Requirements

### Requirement: AI 诊断 API (修改)
**Original**: 支持图像、多模态、文本三种诊断模式
**Modified**: 增强为支持 Thinking 模式、Graph-RAG 增强、KAD-Former 融合、批量诊断等多种高级特性

### Requirement: 响应格式 (修改)
**Original**: 基础诊断结果 JSON
**Modified**: 扩展为包含推理链、知识引用、置信度分析、性能指标的详细 JSON 结构

## REMOVED Requirements

无 - 原有功能保持不变，新增功能为增强
