# Tasks

## Phase 1: 后端融合服务开发

- [x] Task 1.1: 创建统一融合诊断 API
  - [x] 创建 `/diagnosis/fusion` 端点，支持图像+文本同时输入
  - [x] 实现图像和文本输入的统一处理逻辑
  - [x] 添加环境因素参数（天气、生长阶段、发病部位）
  - [x] 返回融合诊断结果，包含推理链和知识引用

- [x] Task 1.2: 实现 KAD-Former 知识引导注意力模块
  - [x] 创建 `kad_attention.py` 知识引导注意力模块
  - [x] 实现知识图谱特征提取和嵌入
  - [x] 实现 KGA 注意力权重计算
  - [x] 实现视觉特征与知识特征的门控融合

- [x] Task 1.3: 实现 GraphRAG 知识增强服务
  - [x] 创建 `graphrag_service.py` 知识检索服务
  - [x] 实现知识子图检索（基于症状关键词）
  - [x] 实现知识三元组到 Token 的转换
  - [x] 实现知识 Token 注入 Qwen3-VL 上下文

- [x] Task 1.4: 实现特征融合服务
  - [x] 创建 `fusion_service.py` 多模态融合服务
  - [x] 实现 YOLOv8 ROI 特征提取
  - [x] 实现 Qwen3-VL 语义特征提取
  - [x] 实现双引擎特征融合逻辑

## Phase 2: 前端诊断页面重构

- [x] Task 2.1: 创建多模态输入组件
  - [x] 创建 `MultiModalInput.vue` 组件
  - [x] 实现图像上传区域（支持拖拽）
  - [x] 实现文本症状输入区域（富文本）
  - [x] 实现环境因素选择（天气、生长阶段、发病部位）

- [x] Task 2.2: 创建融合结果展示组件
  - [x] 创建 `FusionResult.vue` 组件
  - [x] 实现病害名称和置信度展示
  - [x] 实现推理链展示（Thinking 模式）
  - [x] 实现知识引用溯源展示
  - [x] 实现防治建议列表

- [x] Task 2.3: 重构诊断页面
  - [x] 更新 `Diagnosis.vue` 使用新组件
  - [x] 集成统一融合诊断 API
  - [x] 实现诊断流程状态管理
  - [x] 添加诊断历史记录功能

## Phase 3: 集成测试与验证

- [ ] Task 3.1: 后端单元测试
  - [ ] 测试 KAD-Former 注意力模块
  - [ ] 测试 GraphRAG 检索服务
  - [ ] 测试特征融合服务
  - [ ] 测试统一诊断 API

- [ ] Task 3.2: 前后端集成测试
  - [ ] 测试图像+文本联合诊断流程
  - [ ] 测试仅图像诊断流程
  - [ ] 测试仅文本诊断流程
  - [ ] 测试 GraphRAG 知识增强

- [ ] Task 3.3: 性能测试
  - [ ] 测试诊断响应时间
  - [ ] 测试缓存命中率
  - [ ] 测试并发诊断能力

## Phase 4: 文档更新

- [ ] Task 4.1: 更新技术文档
  - [ ] 更新 `GRAPH_RAG_SPEC.md` 添加 KAD-Former 说明
  - [ ] 更新 `WEB_ARCHITECTURE.md` 诊断流程说明
  - [ ] 创建 `KAD_FORMER_SPEC.md` 详细设计文档

# Task Dependencies

- [Task 1.2] depends on [Task 1.3] - KAD-Former 需要知识图谱特征
- [Task 1.4] depends on [Task 1.2] - 融合服务依赖 KAD-Former
- [Task 1.1] depends on [Task 1.4] - API 依赖融合服务
- [Task 2.3] depends on [Task 2.1, Task 2.2] - 页面依赖组件
- [Task 3.1] depends on [Task 1.1, Task 1.2, Task 1.3, Task 1.4] - 测试依赖后端开发
- [Task 3.2] depends on [Task 2.3] - 集成测试依赖前端开发
