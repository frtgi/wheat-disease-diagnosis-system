# IWDDA Agent 架构升级 Tasks

## Phase 1: 规划决策层开发 ✅
- [x] Task 1.1: 创建规划决策层基础架构
  - [x] 设计 PlanningEngine 类
  - [x] 实现诊断计划生成器
  - [x] 定义固定输出结构（6 部分）
- [x] Task 1.2: 实现任务规划器
  - [x] 设计 TaskPlanner 类
  - [x] 实现复查任务生成逻辑
  - [x] 实现防治步骤分解
- [x] Task 1.3: 集成 Qwen3-VL-4B-Instruct 规划能力
  - [x] 利用 Interleaved-MRoPE 进行空间推理
  - [x] 利用 DeepStack 进行多层特征融合
  - [x] 实现链式思考（CoT）推理

## Phase 2: 工具执行层开发 ✅
- [x] Task 2.1: 创建工具管理器
  - [x] 设计 ToolManager 类
  - [x] 实现工具注册机制
  - [x] 实现工具调用接口
- [x] Task 2.2: 开发 6 类核心工具
  - [x] 图像诊断工具（DiagnosisTool）
  - [x] 知识检索工具（KnowledgeRetrievalTool）
  - [x] 防治方案生成工具（TreatmentTool）
  - [x] 病例记录工具（CaseRecordTool）
  - [x] 复查计划工具（FollowupTool）
  - [x] 历史对比工具（HistoryComparisonTool）
- [x] Task 2.3: 工具与规划层集成
  - [x] 实现规划→工具调用映射
  - [x] 实现工具执行结果反馈

## Phase 3: 反馈记忆层开发 ✅
- [x] Task 3.1: 创建病例记忆系统
  - [x] 设计 CaseMemory 类
  - [x] 实现记忆存储结构
  - [x] 实现记忆检索接口
- [x] Task 3.2: 实现反馈处理机制
  - [x] 设计 FeedbackHandler 类
  - [x] 实现用户反馈解析
  - [x] 实现反馈→策略调整映射
- [x] Task 3.3: 实现记忆引用机制
  - [x] 再次诊断时检索历史病例
  - [x] 实现上下文注入
  - [x] 实现病情变化对比

## Phase 4: 自进化机制强化 ✅
- [x] Task 4.1: 实现 GRPO 强化学习框架
  - [x] 设计 GRPOTrainer 类
  - [x] 实现奖励函数（准确性 + 逻辑性 + 简洁度）
  - [x] 实现策略优化
- [x] Task 4.2: 实现 LoRA 增量学习
  - [x] 设计 LoRAFinetuner 类
  - [x] 实现新病害快速适配
  - [x] 实现区域专属模型
- [x] Task 4.3: 集成到反馈闭环
  - [x] 积累诊断案例→GRPO 优化
  - [x] 积累反馈数据→LoRA 微调

## Phase 5: Qwen3-VL-4B-Instruct 深度集成 ✅
- [x] Task 5.1: 实现原生多模态早融合
  - [x] 视觉 Token 与文本 Token 统一建模
  - [x] 优化特征融合策略
- [x] Task 5.2: 实现 Gated DeltaNet 注意力
  - [x] 复杂度优化 O(n²) → O(n)
  - [x] 支持长序列推理（无人机视频、长报告）
- [x] Task 5.3: 实现 Interleaved-MRoPE
  - [x] 3D 位置编码（空间 + 时间 + 图像）
  - [x] 病斑空间分布特征识别
- [x] Task 5.4: 实现 DeepStack 多层视觉注入
  - [x] 低层特征（边缘纹理）注入
  - [x] 高层特征（语义特征）注入
  - [x] 细粒度识别能力提升

## Phase 6: Graph-RAG 增强
- [ ] Task 6.1: 升级知识图谱查询
  - [ ] 从简单查询→子图检索
  - [ ] 实现知识子图转换为 token
- [ ] Task 6.2: 实现 Graph-RAG 上下文注入
  - [ ] 检索结果→文本 token
  - [ ] 注入 Qwen3-VL-4B-Instruct 上下文
- [ ] Task 6.3: 知识图谱扩展
  - [ ] 扩展实体类型（当前 106→目标 200+）
  - [ ] 扩展关系类型（当前 15→目标 30+）
  - [ ] 新增实体：环境因素、防治方法、农药类型、生长阶段
  - [ ] 新增关系：影响、适用于、禁用、推荐

## Phase 7: Web 智能体界面重构
- [ ] Task 7.1: 创建 6 大页面
  - [ ] 病害诊断页（上传 + 症状）
  - [ ] 诊断结果页（病害判断）
  - [ ] 推理依据页（解释原因）
  - [ ] 行动计划页（防治建议）
  - [ ] 复查任务页（复查提醒）
  - [ ] 历史病例页（历史诊断）
- [ ] Task 7.2: 实现智能体交互
  - [ ] 多轮对话支持
  - [ ] 病例记忆展示
  - [ ] 反馈收集界面
- [ ] Task 7.3: 集成规划与工具层
  - [ ] 诊断计划展示
  - [ ] 工具调用可视化
  - [ ] 复查任务管理
- [ ] Task 7.4: 前端技术栈
  - [ ] 使用 React + TypeScript
  - [ ] 使用 TailwindCSS 样式
  - [ ] 使用 React Query 数据管理
  - [ ] 使用 WebSocket 实时通信

## Phase 8: 云边协同部署
- [ ] Task 8.1: 实现边缘端优化
  - [ ] YOLOv8 边缘部署（TensorRT/ONNX）
  - [ ] 初步诊断逻辑
  - [ ] 边缘 - 云通信协议
  - [ ] 边缘设备资源监控
- [ ] Task 8.2: 实现云端部署
  - [ ] Qwen3-VL-4B-Instruct 云端部署（4bit 量化）
  - [ ] 知识图谱云端服务（Neo4j Aura）
  - [ ] 诊断智能体云端运行
  - [ ] API 网关配置
- [ ] Task 8.3: 实现协同推理
  - [ ] 边缘检测→云端推理流程
  - [ ] 结果返回边缘端
  - [ ] 离线模式支持（边缘缓存）
  - [ ] 断点续传机制

## Phase 9: 用户输入层增强
- [ ] Task 9.1: 实现多模态输入解析
  - [ ] 图像预处理（resize, normalize, augment）
  - [ ] 文本症状解析（NER 提取关键症状）
  - [ ] 结构化数据生成（JSON Schema）
- [ ] Task 9.2: 实现环境因素集成
  - [ ] 天气数据解析（温度、湿度、降水）
  - [ ] 生长阶段编码（苗期、拔节期、抽穗期等）
  - [ ] 发病部位编码（叶片、茎秆、穗部）
  - [ ] 环境风险评分计算
- [ ] Task 9.3: 实现输入验证
  - [ ] 图像质量检查（分辨率、亮度、模糊度）
  - [ ] 数据完整性验证（必填字段检查）
  - [ ] 异常处理（错误提示、恢复建议）

## Phase 10: 感知诊断层优化
- [ ] Task 10.1: YOLOv8 引擎优化
  - [ ] ROI 定位精度提升（注意力机制）
  - [ ] 病斑特征提取优化（多尺度特征）
  - [ ] 小目标检测优化（病斑早期检测）
- [ ] Task 10.2: Qwen3-VL 视觉引擎优化
  - [ ] 图像理解能力提升（fine-tuning）
  - [ ] 初步病害候选生成（top-k 候选）
  - [ ] 视觉 - 文本对齐优化
- [ ] Task 10.3: 双引擎融合
  - [ ] YOLOv8 + Qwen3-VL 特征融合（early fusion）
  - [ ] 联合特征输出（concat + attention）
  - [ ] 融合权重学习（gating mechanism）

## Phase 11: 集成测试与验证
- [ ] Task 11.1: 单元测试
  - [ ] 规划决策层测试（PlanningEngine, TaskPlanner）
  - [ ] 工具执行层测试（6 个工具）
  - [ ] 反馈记忆层测试（CaseMemory, FeedbackHandler）
  - [ ] 用户输入层测试（InputParser, InputValidator）
  - [ ] 感知诊断层测试（YOLOv8Engine, QwenVLEngine）
- [ ] Task 11.2: 集成测试
  - [ ] 六层架构端到端测试
  - [ ] 工具调用集成测试
  - [ ] 记忆引用测试
  - [ ] Graph-RAG 上下文注入测试
  - [ ] 双引擎融合测试
- [ ] Task 11.3: 系统测试
  - [ ] Web 智能体界面测试（6 大页面）
  - [ ] 云边协同测试
  - [ ] 自进化机制测试（GRPO, LoRA）
  - [ ] 多轮对话测试
- [ ] Task 11.4: 性能测试
  - [ ] 推理延迟测试（p50, p95, p99）
  - [ ] 并发性能测试（10/50/100 并发）
  - [ ] 显存占用测试（Qwen3-VL 4bit 量化）
  - [ ] 边缘设备资源占用测试

## Phase 12: 文档与部署
- [ ] Task 12.1: 更新架构文档
  - [ ] 更新 IWDDA_ARCHITECTURE.md（六层架构）
  - [ ] 新增 AGENT_ARCHITECTURE.md（智能体架构）
  - [ ] 新增 GRAPH_RAG_SPEC.md（Graph-RAG 设计）
  - [ ] 新增 CLOUD_EDGE_DEPLOYMENT.md（云边协同部署）
- [ ] Task 12.2: 更新使用文档
  - [ ] 更新 NEXT_STEPS.md
  - [ ] 更新 PROJECT_PROGRESS.md（完成度 100%）
  - [ ] 更新 MODIFICATION_MANUAL.md
  - [ ] 新增 USER_GUIDE.md（用户使用指南）
  - [ ] 新增 API_REFERENCE.md（API 参考）
- [ ] Task 12.3: 部署脚本
  - [ ] 云端部署脚本（Docker Compose + K8s）
  - [ ] 边缘端部署脚本（Raspberry Pi/Jetson Nano）
  - [ ] 云边协同配置（配置文件 + 环境变量）
  - [ ] CI/CD 流水线配置（GitHub Actions）

# Task Dependencies

## 核心依赖链
- [Task 1.x 规划决策层] 是 [Task 2.x 工具执行层] 的前提
- [Task 2.x 工具执行层] 是 [Task 3.x 反馈记忆层] 的前提
- [Task 3.x 反馈记忆层] 是 [Task 4.x 自进化机制] 的前提
- [Task 5.x Qwen3-VL 深度集成] 可并行执行，但影响 [Task 1.x][Task 6.x]
- [Task 6.x Graph-RAG] 依赖 [Task 5.x] 完成
- [Task 7.x Web 界面] 依赖 [Task 1.x][Task 2.x][Task 3.x] 完成
- [Task 8.x 云边协同] 依赖 [Task 10.x 感知诊断层] 优化
- [Task 9.x 用户输入层] 可并行执行
- [Task 10.x 感知诊断层] 可并行执行
- [Task 11.x 测试验证] 依赖所有开发任务完成
- [Task 12.x 文档部署] 最后执行

## 并行执行组
- **Group A (核心架构)**: Task 1.x, Task 2.x, Task 3.x, Task 4.x (顺序执行) ✅ 已完成
- **Group B (Qwen3-VL 增强)**: Task 5.x, Task 6.x (顺序执行) - Task 5.x ✅ 已完成
- **Group C (感知优化)**: Task 9.x, Task 10.x (可并行)
- **Group D (部署界面)**: Task 7.x, Task 8.x (可并行，依赖 Group A)
- **Group E (测试文档)**: Task 11.x, Task 12.x (顺序执行，最后)

## Phase 6-12 执行策略
- **Phase 6 (Graph-RAG)**: 优先执行，为 Phase 10 提供知识增强
- **Phase 9 (用户输入层)**: 独立执行，无依赖
- **Phase 10 (感知诊断层)**: 可与 Phase 6/9 并行
- **Phase 7 (Web 界面)**: 在 Phase 6/9/10 进行中时可并行
- **Phase 8 (云边协同)**: 依赖 Phase 10 完成后执行
- **Phase 11 (测试)**: 所有开发完成后执行
- **Phase 12 (文档)**: 与 Phase 11 并行，最后完成
