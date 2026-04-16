# IWDDA Agent 架构升级 Spec (Phase 6-12)

## Why
完成 IWDDA 六层智能体架构的最后阶段，实现从"图像识别系统"到"目标驱动的农业智能体"的完整升级，包括 Graph-RAG 增强、Web 智能体界面、云边协同部署、用户输入层增强、感知诊断层优化、集成测试与验证、文档与部署。

## What Changes
- **Phase 6: Graph-RAG 增强**
  - 升级知识图谱查询从简单查询到子图检索
  - 实现知识子图转换为 token
  - 实现 Graph-RAG 上下文注入到 Qwen3-VL-4B-Instruct
  - 扩展知识图谱实体从 106 到 200+
  - 扩展关系类型从 15 到 30+

- **Phase 7: Web 智能体界面重构**
  - 创建 6 大核心页面（病害诊断、诊断结果、推理依据、行动计划、复查任务、历史病例）
  - 实现多轮对话支持
  - 实现病例记忆展示
  - 实现反馈收集界面
  - 集成规划与工具层可视化

- **Phase 8: 云边协同部署**
  - 实现 YOLOv8 边缘端优化部署（TensorRT/ONNX）
  - 实现 Qwen3-VL-4B-Instruct 云端部署
  - 实现知识图谱云端服务
  - 实现边缘 - 云协同推理
  - 实现离线模式支持

- **Phase 9: 用户输入层增强**
  - 实现多模态输入解析（图像、文本、结构化数据）
  - 实现环境因素集成（天气、生长阶段、发病部位）
  - 实现输入验证（图像质量、数据完整性、异常处理）

- **Phase 10: 感知诊断层优化**
  - 优化 YOLOv8 ROI 定位精度
  - 优化病斑特征提取
  - 提升 Qwen3-VL 图像理解能力
  - 实现 YOLOv8 + Qwen3-VL 双引擎特征融合
  - 实现联合特征输出

- **Phase 11: 集成测试与验证**
  - 实现规划决策层、工具执行层、反馈记忆层单元测试
  - 实现六层架构端到端集成测试
  - 实现 Web 智能体界面系统测试
  - 实现推理延迟、并发性能、显存占用性能测试

- **Phase 12: 文档与部署**
  - 更新 IWDDA_ARCHITECTURE.md
  - 创建 AGENT_ARCHITECTURE.md
  - 更新 NEXT_STEPS.md, PROJECT_PROGRESS.md, MODIFICATION_MANUAL.md
  - 创建云端、边缘端部署脚本
  - 创建云边协同配置

## Impact
- **Affected specs**: agent-architecture-upgrade (Phase 1-5 已完成)
- **Affected code**: 
  - `src/graph/graphrag_engine.py` - Graph-RAG 增强
  - `src/input/` - 用户输入层新建
  - `src/perception/` - 感知诊断层优化
  - `src/web/` - Web 智能体界面新建
  - `src/deployment/` - 云边协同部署新建
  - `tests/` - 集成测试套件新建
  - `docs/` - 架构与部署文档更新

## ADDED Requirements

### Requirement: Graph-RAG 增强
The system SHALL provide 知识子图检索和 token 化能力，将检索结果注入 Qwen3-VL-4B-Instruct 上下文。

#### Scenario: 病害诊断时知识增强
- **WHEN** 用户提交病害图像和症状描述
- **THEN** 系统检索相关知识子图，转换为 token，注入到 Qwen3-VL-4B-Instruct 的推理上下文，提升诊断准确性

### Requirement: Web 智能体界面
The system SHALL provide 6 大核心页面，支持多轮对话、病例记忆展示和反馈收集。

#### Scenario: 完整诊断流程
- **WHEN** 用户上传图像并描述症状
- **THEN** 系统在病害诊断页展示结果，诊断结果页显示病害判断，推理依据页解释原因，行动计划页提供防治建议，复查任务页设置提醒，历史病例页展示历史诊断

### Requirement: 云边协同部署
The system SHALL provide 边缘端 YOLOv8 优化部署和云端 Qwen3-VL-4B-Instruct 部署，支持协同推理和离线模式。

#### Scenario: 边缘 - 云协同诊断
- **WHEN** 边缘设备采集图像
- **THEN** 边缘端执行 YOLOv8 初步检测，云端执行 Qwen3-VL 深度推理，结果返回边缘端展示

### Requirement: 用户输入层增强
The system SHALL provide 多模态输入解析、环境因素集成和输入验证能力。

#### Scenario: 多模态输入处理
- **WHEN** 用户提供图像、文本症状、环境数据
- **THEN** 系统解析所有输入，编码环境因素，验证数据完整性，生成结构化输入数据

### Requirement: 感知诊断层优化
The system SHALL provide YOLOv8 和 Qwen3-VL 双引擎特征融合能力。

#### Scenario: 双引擎融合诊断
- **WHEN** 系统接收图像输入
- **THEN** YOLOv8 提取 ROI 和病斑特征，Qwen3-VL 提取语义特征，双引擎融合输出联合特征

### Requirement: 集成测试与验证
The system SHALL provide 完整的测试套件，覆盖单元测试、集成测试、系统测试和性能测试。

#### Scenario: 端到端测试
- **WHEN** 所有模块开发完成
- **THEN** 执行六层架构端到端测试，所有测试用例通过

### Requirement: 文档与部署
The system SHALL provide 完整的架构文档、使用文档和部署脚本。

#### Scenario: 云端部署
- **WHEN** 部署到云端服务器
- **THEN** 执行云端部署脚本，Qwen3-VL-4B-Instruct 和知识图谱服务正常运行

## MODIFIED Requirements

### Requirement: 知识图谱查询 (Phase 6 修改)
**Original**: 简单 Cypher 查询
**Modified**: 子图检索 + 知识 token 化 + Graph-RAG 上下文注入

### Requirement: 诊断引擎 (Phase 10 修改)
**Original**: 单一 YOLOv8 或 Qwen3-VL 引擎
**Modified**: YOLOv8 + Qwen3-VL 双引擎融合

## REMOVED Requirements

无

## Migration
无 - Phase 1-5 已实现的功能保持不变，Phase 6-12 为新增功能
