# IWDDA Agent 架构升级 Checklist

## Phase 1: 规划决策层开发 ✅
- [x] PlanningEngine 类已创建并实现诊断计划生成器
- [x] 诊断计划固定输出结构（6 部分）已实现
- [x] TaskPlanner 类已创建并实现任务规划逻辑
- [x] 复查任务生成逻辑正确
- [x] 防治步骤分解正确
- [x] Qwen3-VL-4B-Instruct 规划能力集成（Interleaved-MRoPE、DeepStack、CoT）

## Phase 2: 工具执行层开发 ✅
- [x] ToolManager 类已创建并实现工具注册机制
- [x] 工具调用接口已实现
- [x] 6 类核心工具已开发：
  - [x] DiagnosisTool（图像诊断工具）
  - [x] KnowledgeRetrievalTool（知识检索工具）
  - [x] TreatmentTool（防治方案生成工具）
  - [x] CaseRecordTool（病例记录工具）
  - [x] FollowupTool（复查计划工具）
  - [x] HistoryComparisonTool（历史对比工具）
- [x] 规划→工具调用映射已实现
- [x] 工具执行结果反馈已实现

## Phase 3: 反馈记忆层开发 ✅
- [x] CaseMemory 类已创建并实现记忆存储结构
- [x] 记忆检索接口已实现
- [x] FeedbackHandler 类已创建并实现用户反馈解析
- [x] 反馈→策略调整映射已实现
- [x] 再次诊断时历史病例检索已实现
- [x] 上下文注入已实现
- [x] 病情变化对比已实现

## Phase 4: 自进化机制强化 ✅
- [x] GRPOTrainer 类已创建并实现奖励函数
- [x] 奖励函数包含诊断准确性、推理逻辑、输出简洁度
- [x] 策略优化已实现
- [x] LoRAFinetuner 类已创建
- [x] 新病害快速适配已实现
- [x] 区域专属模型已实现
- [x] GRPO 优化与 LoRA 微调已集成到反馈闭环

## Phase 5: Qwen3-VL-4B-Instruct 深度集成 ✅
- [x] 原生多模态早融合已实现（视觉 Token+ 文本 Token 统一建模）
- [x] Gated DeltaNet 注意力已实现（复杂度 O(n²) → O(n)）
- [x] 长序列推理支持（无人机视频、长报告）
- [x] Interleaved-MRoPE 已实现（3D 位置编码）
- [x] 病斑空间分布特征识别已实现
- [x] DeepStack 多层视觉注入已实现
- [x] 低层特征（边缘纹理）注入已实现
- [x] 高层特征（语义特征）注入已实现
- [x] 细粒度识别能力提升已验证

## Phase 6: Graph-RAG 增强
- [ ] 知识子图检索已实现（从简单查询升级）
- [ ] 知识子图转换为 token 已实现
- [ ] Graph-RAG 上下文注入已实现
- [ ] 知识图谱实体扩展（106→200+）
- [ ] 知识图谱关系扩展（15→30+）
- [ ] 新增实体已添加（环境因素、防治方法、农药类型、生长阶段）
- [ ] 新增关系已添加（影响、适用于、禁用、推荐）
- [ ] Graph-RAG 检索性能达标（<100ms）

## Phase 7: Web 智能体界面重构
- [ ] 6 大页面已创建：
  - [ ] 病害诊断页（上传 + 症状）
  - [ ] 诊断结果页（病害判断）
  - [ ] 推理依据页（解释原因）
  - [ ] 行动计划页（防治建议）
  - [ ] 复查任务页（复查提醒）
  - [ ] 历史病例页（历史诊断）
- [ ] 多轮对话支持已实现
- [ ] 病例记忆展示已实现
- [ ] 反馈收集界面已实现
- [ ] 诊断计划展示已实现
- [ ] 工具调用可视化已实现
- [ ] 复查任务管理已实现
- [ ] React + TypeScript 技术栈已配置
- [ ] TailwindCSS 样式已应用
- [ ] WebSocket 实时通信已实现
- [ ] 页面响应式设计已实现（桌面 + 移动）

## Phase 8: 云边协同部署
- [ ] YOLOv8 边缘部署已实现（TensorRT/ONNX）
- [ ] 初步诊断逻辑已实现
- [ ] 边缘 - 云通信协议已实现
- [ ] 边缘设备资源监控已实现
- [ ] Qwen3-VL-4B-Instruct 云端部署已实现（4bit 量化）
- [ ] 知识图谱云端服务已实现（Neo4j Aura）
- [ ] 诊断智能体云端运行已实现
- [ ] API 网关配置已实现
- [ ] 协同推理已实现（边缘检测→云端推理→结果返回）
- [ ] 离线模式支持已实现（边缘缓存）
- [ ] 断点续传机制已实现
- [ ] 云边通信延迟<500ms

## Phase 9: 用户输入层增强
- [ ] 图像预处理已实现（resize, normalize, augment）
- [ ] 文本症状解析已实现（NER 提取关键症状）
- [ ] 结构化数据生成已实现（JSON Schema）
- [ ] 天气数据解析已实现（温度、湿度、降水）
- [ ] 生长阶段编码已实现（苗期、拔节期、抽穗期等）
- [ ] 发病部位编码已实现（叶片、茎秆、穗部）
- [ ] 环境风险评分计算已实现
- [ ] 图像质量检查已实现（分辨率、亮度、模糊度）
- [ ] 数据完整性验证已实现（必填字段检查）
- [ ] 异常处理已实现（错误提示、恢复建议）
- [ ] 输入层端到端测试通过

## Phase 10: 感知诊断层优化
- [ ] YOLOv8 ROI 定位精度已提升（注意力机制）
- [ ] 病斑特征提取已优化（多尺度特征）
- [ ] 小目标检测已优化（病斑早期检测）
- [ ] Qwen3-VL 图像理解能力已提升（fine-tuning）
- [ ] 初步病害候选生成已实现（top-k 候选）
- [ ] 视觉 - 文本对齐已优化
- [ ] YOLOv8 + Qwen3-VL 特征融合已实现（early fusion）
- [ ] 联合特征输出已实现（concat + attention）
- [ ] 融合权重学习已实现（gating mechanism）
- [ ] 双引擎融合诊断精度提升（mAP 提升>5%）

## Phase 11: 集成测试与验证
- [ ] 规划决策层单元测试通过（PlanningEngine, TaskPlanner）
- [ ] 工具执行层单元测试通过（6 个工具）
- [ ] 反馈记忆层单元测试通过（CaseMemory, FeedbackHandler）
- [ ] 用户输入层单元测试通过（InputParser, InputValidator）
- [ ] 感知诊断层单元测试通过（YOLOv8Engine, QwenVLEngine）
- [ ] 六层架构端到端测试通过
- [ ] 工具调用集成测试通过
- [ ] 记忆引用测试通过
- [ ] Graph-RAG 上下文注入测试通过
- [ ] 双引擎融合测试通过
- [ ] Web 智能体界面测试通过（6 大页面）
- [ ] 云边协同测试通过
- [ ] 自进化机制测试通过（GRPO, LoRA）
- [ ] 多轮对话测试通过
- [ ] 推理延迟测试通过（p50<1s, p95<3s, p99<5s）
- [ ] 并发性能测试通过（10/50/100 并发）
- [ ] 显存占用测试通过（Qwen3-VL 4bit<3GB）
- [ ] 边缘设备资源占用测试通过

## Phase 12: 文档与部署
- [ ] IWDDA_ARCHITECTURE.md 已更新（六层架构）
- [ ] AGENT_ARCHITECTURE.md 已创建（智能体架构）
- [ ] GRAPH_RAG_SPEC.md 已创建（Graph-RAG 设计）
- [ ] CLOUD_EDGE_DEPLOYMENT.md 已创建（云边协同部署）
- [ ] NEXT_STEPS.md 已更新
- [ ] PROJECT_PROGRESS.md 已更新（完成度 100%）
- [ ] MODIFICATION_MANUAL.md 已更新
- [ ] USER_GUIDE.md 已创建（用户使用指南）
- [ ] API_REFERENCE.md 已创建（API 参考）
- [ ] 云端部署脚本已创建（Docker Compose + K8s）
- [ ] 边缘端部署脚本已创建（Raspberry Pi/Jetson Nano）
- [ ] 云边协同配置已创建（配置文件 + 环境变量）
- [ ] CI/CD 流水线配置已创建（GitHub Actions）

## 总体验证
- [ ] 六层智能体架构完整实现（用户输入层、感知诊断层、认知推理层、规划决策层、工具执行层、反馈记忆层）
- [ ] 系统目标从"图像识别"升级为"目标驱动的农业智能体"
- [ ] 完整农业决策闭环已实现（输入→诊断→防治→复查→反馈→更新）
- [ ] Qwen3-VL-4B-Instruct 特性充分利用（早融合、Gated DeltaNet、Interleaved-MRoPE、DeepStack）
- [ ] Graph-RAG 机制正常工作（子图检索、知识 token 化、上下文注入）
- [ ] 病例记忆与自进化机制正常工作（CaseMemory, FeedbackHandler, GRPO, LoRA）
- [ ] Web 智能体界面 6 大页面正常工作
- [ ] 云边协同部署正常工作（边缘 YOLOv8、云端 Qwen3-VL）
- [ ] 双引擎融合诊断正常工作（YOLOv8 + Qwen3-VL）
- [ ] 所有测试通过（单元测试、集成测试、系统测试、性能测试）
- [ ] 项目完成度达到 100%
- [ ] 文档完整（架构文档、使用文档、API 参考、部署脚本）
