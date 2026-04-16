# KAD-Former + GraphRAG 多模态特征融合诊断 Spec

## Why

基于 Qwen3-VL-4B-Instruct 原生多模态架构的研究文档，需要将当前系统的诊断服务升级为支持图片和文本同时诊断的多模态特征融合诊断模式，整合 KAD-Former（知识引导注意力）和 GraphRAG（图检索增强生成）技术，实现从"图像识别系统"到"目标驱动的农业智能体"的完整升级。

当前系统存在以下问题：
1. 前后端诊断接口分散（图像诊断 `/diagnosis/image`、文本诊断 `/diagnosis/text`、多模态诊断 `/diagnosis/multimodal` 分离）
2. KAD-Former 知识引导注意力机制未完全集成
3. GraphRAG 知识增强与诊断流程未深度整合
4. 前端诊断页面仅支持图像上传，不支持文本症状输入

## What Changes

### 后端服务整合
- **统一诊断 API**: 合并图像诊断、文本诊断、多模态诊断为单一 `/diagnosis/fusion` 端点
- **KAD-Former 融合引擎**: 实现知识引导注意力（KGA）机制
- **GraphRAG 深度集成**: 知识子图检索 → Token 化 → 上下文注入
- **双引擎特征融合**: YOLOv8 ROI 特征 + Qwen3-VL 语义特征融合

### 前端诊断页面重构
- **多模态输入**: 同时支持图像上传和文本症状描述
- **环境因素输入**: 天气、生长阶段、发病部位等结构化数据
- **诊断结果增强**: 显示推理链、知识引用、置信度分析
- **实时诊断反馈**: 流式输出诊断过程

### 架构升级
- **感知层**: YOLOv8 目标检测 + ROI 提取
- **认知层**: Qwen3-VL 多模态理解 + Thinking 推理链
- **融合层**: KAD-Former 知识引导注意力融合
- **增强层**: GraphRAG 知识检索增强

## Impact

- **Affected specs**: 
  - deep-integration-fix (KAD-Former 实现)
  - agent-architecture-upgrade (Phase 6-10)
  - web-development (前端诊断页面)

- **Affected code**:
  - `src/web/backend/app/api/v1/ai_diagnosis.py` - 统一诊断 API
  - `src/web/backend/app/services/fusion_service.py` - 新建融合服务
  - `src/web/backend/app/services/kad_attention.py` - KAD-Former 模块
  - `src/web/backend/app/services/graphrag_service.py` - GraphRAG 服务
  - `src/web/frontend/src/views/Diagnosis.vue` - 多模态诊断页面
  - `src/web/frontend/src/components/diagnosis/MultiModalInput.vue` - 新建多模态输入组件
  - `src/web/frontend/src/components/diagnosis/FusionResult.vue` - 新建融合结果组件

- **Affected documentation**:
  - `docs/GRAPH_RAG_SPEC.md` - 更新 GraphRAG 集成说明
  - `docs/WEB_ARCHITECTURE.md` - 更新诊断流程说明

## ADDED Requirements

### Requirement: 统一多模态诊断 API
The system SHALL 提供统一的多模态融合诊断接口 `/diagnosis/fusion`，同时接受图像和文本输入。

#### Scenario: 图像+文本联合诊断
- **WHEN** 用户上传病害图像并输入症状描述
- **THEN** 系统同时处理图像和文本，融合 YOLOv8 视觉特征和 Qwen3-VL 语义特征，输出综合诊断结果

#### Scenario: 仅图像诊断
- **WHEN** 用户仅上传图像，无文本描述
- **THEN** 系统使用 YOLOv8 检测病害区域，Qwen3-VL 分析图像内容，输出诊断结果

#### Scenario: 仅文本诊断
- **WHEN** 用户仅输入症状描述，无图像
- **THEN** 系统使用 GraphRAG 检索相关知识，Qwen3-VL 进行文本诊断，输出诊断建议

### Requirement: KAD-Former 知识引导注意力融合
The system SHALL 实现 KAD-Former 知识引导注意力机制，将知识图谱特征注入视觉注意力计算。

#### Scenario: 知识引导病害识别
- **WHEN** 系统进行病害诊断
- **THEN** KAD-Former 检索知识图谱中相关病害知识，通过 KGA 机制引导视觉注意力聚焦于病斑区域，提升识别准确率

#### Scenario: 多源特征融合
- **WHEN** YOLOv8 提取 ROI 特征和 Qwen3-VL 提取语义特征
- **THEN** KAD-Former 融合视觉特征、语义特征和知识特征，输出联合特征向量

### Requirement: GraphRAG 知识增强诊断
The system SHALL 实现 GraphRAG 知识检索增强，将知识子图转换为 Token 注入诊断上下文。

#### Scenario: 知识子图检索
- **WHEN** 用户描述病害症状
- **THEN** 系统从 Neo4j 知识图谱检索相关病害、症状、防治方法子图

#### Scenario: 知识 Token 化注入
- **WHEN** 检索到知识子图
- **THEN** 系统将知识三元组转换为 Token 序列，注入 Qwen3-VL 上下文，增强诊断推理

#### Scenario: 知识引用溯源
- **WHEN** 输出诊断结果
- **THEN** 系统标注知识来源，提供引用溯源信息

### Requirement: 前端多模态诊断界面
The system SHALL 提供支持图像和文本同时输入的诊断界面。

#### Scenario: 多模态输入
- **WHEN** 用户访问诊断页面
- **THEN** 页面同时显示图像上传区域和文本输入区域，支持拖拽上传和富文本编辑

#### Scenario: 环境因素输入
- **WHEN** 用户需要提供环境信息
- **THEN** 页面提供天气选择、生长阶段选择、发病部位选择等结构化输入

#### Scenario: 诊断结果展示
- **WHEN** 诊断完成
- **THEN** 页面展示病害名称、置信度、推理链、知识引用、防治建议

### Requirement: Thinking 推理链模式
The system SHALL 支持 Thinking 推理链模式，输出逐步推理过程。

#### Scenario: 复杂诊断推理
- **WHEN** 用户启用 Thinking 模式进行诊断
- **THEN** 系统输出逐步推理链，包括症状分析、病害判断、知识验证、防治建议

### Requirement: 诊断结果缓存优化
The system SHALL 实现诊断结果缓存，支持相似图像快速诊断。

#### Scenario: 缓存命中
- **WHEN** 用户上传与历史诊断相似的图像
- **THEN** 系统从缓存返回诊断结果，响应时间 < 100ms

## MODIFIED Requirements

### Requirement: 诊断 API 端点 (修改)
**Original**: 分离的 `/diagnosis/image`、`/diagnosis/text`、`/diagnosis/multimodal` 端点
**Modified**: 统一为 `/diagnosis/fusion` 端点，支持图像、文本、或两者同时输入

### Requirement: 诊断服务调用 (修改)
**Original**: 前端分别调用不同诊断 API
**Modified**: 前端统一调用 `/diagnosis/fusion`，根据输入类型自动选择诊断模式

### Requirement: 诊断结果格式 (修改)
**Original**: 简单的病害名称和置信度
**Modified**: 增强结果包含推理链、知识引用、置信度分析、防治建议

## REMOVED Requirements

无 - 原有诊断接口保持向后兼容，新接口为增强功能

## Migration

- **API 迁移**: 原有 `/diagnosis/image`、`/diagnosis/text`、`/diagnosis/multimodal` 保持兼容，新增 `/diagnosis/fusion` 为推荐接口
- **前端迁移**: Diagnosis.vue 重构为多模态输入模式，原有功能保持不变
- **服务迁移**: 新增 fusion_service.py、kad_attention.py、graphrag_service.py，原有服务保持不变
