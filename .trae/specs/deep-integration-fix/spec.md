# 深度集成与问题修复 Spec

## Why

基于最新研究文档（Qwen3-VL-4B-Instruct 和 Qwen3.5-4B 原生多模态架构）和当前系统运行中发现的问题，需要进行深度集成开发和问题修复：

1. **数据库初始化问题**：启动时出现 `'AsyncEngine' object has no attribute '_run_ddl_visitor'` 警告
2. **架构升级需求**：需要基于最新原生多模态架构特性进行深度集成
3. **性能优化需求**：需要实现知识引导注意力、多层特征融合等高级特性
4. **推理模式增强**：需要添加 Thinking 推理链模式支持

## What Changes

### 问题修复
- 修复 SQLAlchemy 2.x 中 AsyncEngine 的 DDL 方法调用问题
- 优化 init_db 实现，避免异步引擎的同步 DDL 操作
- 修正模型路径和配置问题

### 架构增强
- **Qwen3.5-4B 原生多模态深度集成**
  - 实现原生 Early Fusion 架构（vs Late Fusion）
  - 集成 Gated DeltaNet 线性注意力机制（O(n) 复杂度）
  - 实现 3D Interleaved-MRoPE 位置编码
  - 支持 Thinking 推理链模式

- **KAD-Former 知识引导注意力**
  - 创建知识引导注意力模块
  - 实现知识图谱特征注入
  - 添加门控融合机制

- **DeepStack 多层视觉特征注入**
  - 实现低层特征（边缘纹理）注入
  - 实现高层特征（语义特征）注入
  - 优化细粒度识别能力

- **Graph-RAG 增强**
  - 升级知识图谱查询为子图检索
  - 实现知识子图 token 化
  - 实现上下文注入到 Qwen3-VL

### 性能优化
- 实现模型 INT4 量化支持
- 添加批处理推理
- 优化显存管理
- 实现推理缓存机制

## Impact

- **Affected specs**: 
  - ai-service-integration (增强)
  - agent-architecture-upgrade (Phase 6-10 深度实现)
  
- **Affected code**:
  - `app/core/database.py` - 数据库初始化优化
  - `app/services/qwen_service.py` - Qwen3.5-4B 深度集成
  - `app/services/fusion_service.py` - 新建多模态融合服务
  - `app/services/kad_attention.py` - 新建 KAD-Former 模块
  - `app/api/v1/ai_diagnosis.py` - 增强诊断 API
  - `src/graph/graphrag_engine.py` - Graph-RAG 增强

- **Affected documentation**:
  - `docs/DEEP_INTEGRATION_REPORT.md` - 深度集成报告
  - `docs/QWEN35_ARCHITECTURE.md` - Qwen3.5-4B 架构说明

## ADDED Requirements

### Requirement: 数据库初始化优化
The system SHALL 正确初始化数据库而无 AsyncEngine 警告

#### Scenario: 应用启动
- **WHEN** 启动后端服务
- **THEN** 数据库初始化成功，无 `'AsyncEngine' object has no attribute '_run_ddl_visitor'` 警告

### Requirement: Qwen3.5-4B 原生多模态集成
The system SHALL 提供原生 Early Fusion 多模态推理能力

#### Scenario: 多模态诊断
- **WHEN** 用户提供图像和症状描述
- **THEN** 系统使用原生 Early Fusion 架构，视觉 Token 与文本 Token 统一建模，输出诊断结果

### Requirement: Gated DeltaNet 注意力
The system SHALL 提供线性复杂度注意力机制

#### Scenario: 长序列推理
- **WHEN** 处理长文本或视频帧序列
- **THEN** 使用 Gated DeltaNet，复杂度 O(n) vs O(n²)，支持长序列高效处理

### Requirement: 3D Interleaved-MRoPE 位置编码
The system SHALL 提供 3D 位置编码能力（空间 + 时间 + 图像）

#### Scenario: 病斑空间分布识别
- **WHEN** 分析病害图像
- **THEN** 利用 3D 位置编码识别病斑的空间分布特征

### Requirement: KAD-Former 知识引导注意力
The system SHALL 提供知识图谱引导的注意力机制

#### Scenario: 知识增强诊断
- **WHEN** 进行病害诊断
- **THEN** 检索知识图谱，通过 KAD-Former 注入知识特征，提升诊断准确性

### Requirement: DeepStack 多层视觉特征注入
The system SHALL 提供多层视觉特征融合能力

#### Scenario: 细粒度病害识别
- **WHEN** 识别相似病害（如条锈病 vs 叶锈病）
- **THEN** 融合低层（边缘纹理）和高层（语义）特征，提升细粒度识别能力

### Requirement: Thinking 推理链模式
The system SHALL 提供链式思考推理能力

#### Scenario: 复杂诊断
- **WHEN** 用户需要详细诊断推理过程
- **THEN** 启用 Thinking 模式，输出逐步推理链和诊断依据

### Requirement: Graph-RAG 上下文注入
The system SHALL 提供知识子图检索和上下文注入能力

#### Scenario: 诊断时知识增强
- **WHEN** 进行病害诊断
- **THEN** 检索相关知识子图，转换为 token，注入到 Qwen3-VL 上下文

### Requirement: INT4 量化支持
The system SHALL 提供模型量化能力

#### Scenario: 低显存部署
- **WHEN** 显存资源有限（<8GB）
- **THEN** 使用 INT4 量化，显存占用从 9.8GB 降至 2.6GB

## MODIFIED Requirements

### Requirement: 多模态诊断 API (修改)
**Original**: 支持图像 + 文本、仅图像、仅文本三种模式
**Modified**: 增强为支持原生 Early Fusion、Thinking 模式、知识增强等多种推理模式

### Requirement: Qwen 服务配置 (修改)
**Original**: 基础模型路径和推理参数配置
**Modified**: 增加 Gated DeltaNet、Interleaved-MRoPE、DeepStack、KAD-Former 等高级特性配置

## REMOVED Requirements

无 - 原有功能保持不变，新增功能为增强

## Migration

- **数据库初始化**: 迁移到新的异步 DDL 实现，保持表结构不变
- **AI 服务**: 向后兼容，原有 API 接口不变，新增可选参数支持高级特性
- **模型文件**: 无需迁移，支持动态加载 Qwen3-VL-4B-Instruct 或 Qwen3.5-4B
