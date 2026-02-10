# IWDDA 智能体开发计划

## 一、当前项目状态分析

### 1.1 已完成功能模块

| 模块类别 | 模块名称 | 文件路径 | 状态 | 测试状态 |
|---------|---------|---------|------|---------|
| **感知层增强** | 动态蛇形卷积 (DySnakeConv) | `src/vision/dy_snake_conv.py` | ✅ 完成 | ✅ 通过 |
| | SPPELAN多尺度聚合 | `src/vision/sppelan_module.py` | ✅ 完成 | ✅ 通过 |
| | 超级令牌注意力 (STA) | `src/vision/sta_module.py` | ✅ 完成 | ✅ 通过 |
| **认知层** | CLIP视觉编码器 | `src/cognition/llava_engine.py` | ✅ 完成 | ✅ 通过 |
| | 投影层 (Projection) | `src/cognition/llava_engine.py` | ✅ 完成 | ✅ 通过 |
| | Agri-LLaVA模型 | `src/cognition/llava_engine.py` | ✅ 完成 | ✅ 通过 |
| | 提示工程 | `src/cognition/prompt_templates.py` | ✅ 完成 | ✅ 通过 |
| | 两阶段训练器 | `src/cognition/trainer.py` | ✅ 完成 | ✅ 通过 |
| | 认知引擎 | `src/cognition/cognition_engine.py` | ✅ 完成 | ✅ 通过 |
| **融合层** | 知识引导注意力 (KGA) | `src/fusion/kga_module.py` | ✅ 完成 | ✅ 通过 |
| | 跨模态注意力 | `src/fusion/cross_attention.py` | ✅ 完成 | ✅ 通过 |
| | GraphRAG引擎 | `src/graph/graphrag_engine.py` | ✅ 完成 | ✅ 通过 |
| **自进化** | 经验回放 | `src/action/experience_replay.py` | ✅ 完成 | ✅ 通过 |
| | 人机协同反馈 | `src/action/human_in_the_loop.py` | ✅ 完成 | ✅ 通过 |
| **基础模块** | VisionAgent | `src/vision/vision_engine.py` | ✅ 完成 | ✅ 运行中 |
| | LanguageAgent | `src/text/text_engine.py` | ✅ 完成 | ✅ 运行中 |
| | KnowledgeAgent | `src/graph/graph_engine.py` | ✅ 完成 | ✅ 运行中 |
| | FusionAgent | `src/fusion/fusion_engine.py` | ✅ 完成 | ✅ 运行中 |
| | ActiveLearner | `src/action/learner_engine.py` | ✅ 完成 | ⚠️ 待增强 |

### 1.2 系统架构现状

```
当前系统架构:
┌─────────────────────────────────────────────────────────────┐
│                      WheatDoctor (main.py)                   │
│                         主控制器                             │
└──────────────┬──────────────┬──────────────┬────────────────┘
               │              │              │
    ┌──────────▼──┐  ┌───────▼────┐  ┌──────▼──────┐
    │ VisionAgent │  │LanguageAgent│  │KnowledgeAgent│
    │   (eye)     │  │   (ear)    │  │   (brain)   │
    └──────┬──────┘  └──────┬─────┘  └──────┬──────┘
           │                │               │
           └────────┬───────┴───────┬───────┘
                    │               │
           ┌────────▼────────┐ ┌────▼──────────┐
           │   FusionAgent   │ │ 新模块待集成   │
           │  (fusion_core)  │ │               │
           └─────────────────┘ └───────────────┘
```

---

## 二、下一阶段开发任务目标

### 2.1 核心目标

根据文档《基于多模态特征融合的小麦病害诊断智能体》要求，下一阶段需要完成：

1. **模块集成**：将新开发的DySnakeConv、SPPELAN、STA、KGA、LLaVA等模块集成到主系统
2. **系统增强**：增强ActiveLearner，集成经验回放和人机协同
3. **数据工程**：实现文档要求的数据增强策略
4. **部署优化**：支持TensorRT导出和边缘端部署
5. **性能评估**：建立完整的评估体系

### 2.2 性能目标（文档8.3节）

| 维度 | 指标 | 目标值 | 当前状态 |
|------|------|--------|---------|
| 视觉检测 | mAP@0.5, CIoU | > 95% | 待评估 |
| 语义生成 | BLEU-4, ROUGE-L | > 0.45 | 待实现 |
| 知识一致性 | Consistency@k | > 85% | 待实现 |
| 推理效率 | FPS (Jetson Orin) | > 30 FPS | 待优化 |

---

## 三、模块间依赖关系分析

### 3.1 依赖关系图

```
模块依赖关系:

Phase 1: 核心集成（高优先级）
┌─────────────────────────────────────────────────────────┐
│  DySnakeConv ──┐                                        │
│  SPPELAN ──────┼──► VisionAgent增强 ──► WheatDoctor     │
│  STA ──────────┘                                        │
└─────────────────────────────────────────────────────────┘

Phase 2: 认知增强（高优先级）
┌─────────────────────────────────────────────────────────┐
│  Agri-LLaVA ───┐                                        │
│  KGA ──────────┼──► FusionAgent增强 ──► WheatDoctor     │
│  GraphRAG ─────┘                                        │
└─────────────────────────────────────────────────────────┘

Phase 3: 自进化（中优先级）
┌─────────────────────────────────────────────────────────┐
│  ExperienceReplay ──┐                                   │
│  HumanInTheLoop ────┼──► ActiveLearner增强             │
│                     └────────────────► WheatDoctor      │
└─────────────────────────────────────────────────────────┘

Phase 4: 部署优化（中优先级）
┌─────────────────────────────────────────────────────────┐
│  VisionAgent ──► TensorRT导出 ──► Jetson部署           │
└─────────────────────────────────────────────────────────┘
```

### 3.2 关键依赖路径

| 功能 | 依赖模块 | 被依赖模块 |
|------|---------|-----------|
| 视觉检测增强 | DySnakeConv, SPPELAN, STA | VisionAgent |
| 多模态融合 | KGA, CrossAttention, GraphRAG | FusionAgent |
| 认知理解 | Agri-LLaVA | LanguageAgent替换 |
| 自进化学习 | ExperienceReplay, HumanInTheLoop | ActiveLearner |
| 边缘部署 | 所有视觉模块 | Export模块 |

---

## 四、详细开发计划

### 4.1 阶段划分

#### 🔴 Phase 1: 核心模块集成（第1-2周）

**目标**：将新开发的模块集成到现有系统架构

**任务清单**:

1. **VisionAgent增强** (3天)
   - [ ] 修改 `src/vision/vision_engine.py`
   - [ ] 集成DySnakeConv到YOLOv8骨干网络
   - [ ] 添加SPPELAN多尺度特征聚合
   - [ ] 在检测头前加入STA全局注意力
   - [ ] 创建 `SerpensGate_YOLOv8` 模型类
   - [ ] 更新模型加载逻辑

2. **FusionAgent增强** (3天)
   - [ ] 修改 `src/fusion/fusion_engine.py`
   - [ ] 集成KGA知识引导注意力
   - [ ] 添加跨模态特征对齐
   - [ ] 集成GraphRAG检索增强
   - [ ] 实现三流融合（视觉+文本+知识）

3. **LanguageAgent替换** (2天)
   - [ ] 修改 `src/text/text_engine.py`
   - [ ] 集成Agri-LLaVA模型
   - [ ] 实现多模态文本生成
   - [ ] 添加提示工程支持
   - [ ] 保持向后兼容接口

4. **主系统集成** (2天)
   - [ ] 修改 `main.py`
   - [ ] 更新WheatDoctor初始化逻辑
   - [ ] 集成新的VisionAgent
   - [ ] 集成新的FusionAgent
   - [ ] 测试端到端流程

**验收标准**:
- VisionAgent能够使用DySnakeConv进行推理
- FusionAgent支持KGA和GraphRAG
- 系统能够生成多模态诊断报告
- mAP@0.5 > 0.95（视觉检测）

---

#### 🔴 Phase 2: 自进化机制集成（第3-4周）

**目标**：实现系统的持续学习能力

**任务清单**:

1. **ActiveLearner增强** (3天)
   - [ ] 修改 `src/action/learner_engine.py`
   - [ ] 集成ExperienceReplayBuffer
   - [ ] 实现增量学习训练循环
   - [ ] 添加LoRA微调支持
   - [ ] 实现定期模型更新机制

2. **人机协同集成** (2天)
   - [ ] 修改 `app.py`
   - [ ] 添加专家反馈界面
   - [ ] 实现待审核样本展示
   - [ ] 集成HumanInTheLoop反馈闭环

3. **知识注入** (2天)
   - [ ] 修改 `src/graph/graph_engine.py`
   - [ ] 实现专家解释到知识图谱的转换
   - [ ] 添加自动三元组抽取
   - [ ] 实现知识图谱增量更新

4. **训练流程** (3天)
   - [ ] 创建 `scripts/train_incremental.py`
   - [ ] 实现两阶段训练pipeline
   - [ ] 添加训练监控和日志
   - [ ] 实现模型版本管理

**验收标准**:
- 系统能够从专家反馈中学习
- 新增类别时不会遗忘旧知识
- 支持LoRA轻量化更新

---

#### 🟡 Phase 3: 数据工程（第5周）

**目标**：实现文档要求的数据增强策略

**任务清单**:

1. **数据增强模块** (3天)
   - [ ] 创建 `src/vision/data_augmentation.py`
   - [ ] 实现Mosaic增强
   - [ ] 实现Mixup策略
   - [ ] 实现CopyPaste增强

2. **环境模拟增强** (2天)
   - [ ] 实现色调/饱和度/亮度调整
   - [ ] 实现高光模拟（露水反光）
   - [ ] 实现天气模拟（阴天/强光）
   - [ ] 实现时间模拟（清晨/正午）

3. **生成式合成** (2天)
   - [ ] 集成Stable Diffusion
   - [ ] 实现文本到图像生成
   - [ ] 添加知识图谱引导的生成
   - [ ] 实现样本平衡策略

4. **数据预处理** (2天)
   - [ ] 创建 `src/data/preprocessor.py`
   - [ ] 实现NER实体识别
   - [ ] 实现关系抽取
   - [ ] 添加数据清洗流程

**验收标准**:
- 数据增强模块能够生成多样化样本
- 模型鲁棒性提升（在不同光照条件下）
- 长尾病害样本得到补充

---

#### 🟡 Phase 4: 部署优化（第6-7周）

**目标**：支持边缘端部署和推理加速

**任务清单**:

1. **模型导出** (3天)
   - [ ] 修改 `src/deploy/export.py`
   - [ ] 支持DySnakeConv模型导出
   - [ ] 实现ONNX格式导出
   - [ ] 实现TensorRT格式导出
   - [ ] 添加INT8量化支持

2. **推理优化** (3天)
   - [ ] 创建 `src/deploy/optimize.py`
   - [ ] 实现模型剪枝
   - [ ] 实现知识蒸馏
   - [ ] 添加批处理推理

3. **边缘端适配** (3天)
   - [ ] 创建 `src/deploy/edge.py`
   - [ ] 实现Jetson Orin适配
   - [ ] 添加边缘端知识图谱子集
   - [ ] 实现离线推理模式

4. **云边协同** (3天)
   - [ ] 创建 `src/deploy/cloud_edge.py`
   - [ ] 实现任务调度
   - [ ] 添加结果同步
   - [ ] 实现模型分发

**验收标准**:
- 模型能够导出为TensorRT格式
- 边缘端推理速度 > 30 FPS
- 支持离线推理

---

#### 🟢 Phase 5: 性能评估（第8周）

**目标**：建立完整的评估体系

**任务清单**:

1. **评估框架** (3天)
   - [ ] 创建 `tests/evaluation/` 目录
   - [ ] 实现mAP@0.5评估
   - [ ] 实现CIoU评估
   - [ ] 实现BLEU-4评估
   - [ ] 实现ROUGE-L评估

2. **知识一致性评估** (2天)
   - [ ] 实现Consistency@k评估
   - [ ] 添加注意力热图可视化
   - [ ] 实现KG对齐检查

3. **性能基准** (2天)
   - [ ] 创建 `tests/benchmark.py`
   - [ ] 实现FPS测试
   - [ ] 实现内存占用测试
   - [ ] 实现功耗测试

4. **自动化测试** (2天)
   - [ ] 创建 `tests/integration_test.py`
   - [ ] 实现端到端测试
   - [ ] 添加回归测试
   - [ ] 实现CI/CD集成

**验收标准**:
- 所有评估指标可自动化计算
- 生成详细的性能报告
- 建立性能基准线

---

### 4.2 开发时间表

| 周次 | 阶段 | 主要任务 | 关键产出 |
|------|------|---------|---------|
| 第1周 | Phase 1 | VisionAgent增强 | 改进版YOLOv8模型 |
| 第2周 | Phase 1 | FusionAgent+LanguageAgent | 多模态融合系统 |
| 第3周 | Phase 2 | ActiveLearner增强 | 增量学习框架 |
| 第4周 | Phase 2 | 人机协同集成 | 专家反馈系统 |
| 第5周 | Phase 3 | 数据增强 | 数据增强模块 |
| 第6周 | Phase 4 | 模型导出+优化 | TensorRT模型 |
| 第7周 | Phase 4 | 边缘端部署 | Jetson适配版 |
| 第8周 | Phase 5 | 性能评估 | 评估报告 |

**总计：8周（2个月）**

---

## 五、性能和安全要求

### 5.1 性能要求

#### 5.1.1 准确性指标

| 模块 | 指标 | 目标值 | 测试方法 |
|------|------|--------|---------|
| 视觉检测 | mAP@0.5 | > 95% | COCO评估工具 |
| | CIoU | > 0.85 | 自定义评估 |
| 语义生成 | BLEU-4 | > 0.45 | NLTK/NLG-Eval |
| | ROUGE-L | > 0.45 | rouge-score |
| 知识一致性 | Consistency@k | > 85% | 自定义评估 |

#### 5.1.2 效率指标

| 场景 | 指标 | 目标值 | 测试环境 |
|------|------|--------|---------|
| 云端推理 | FPS | > 60 | RTX 4090 |
| 边缘推理 | FPS | > 30 | Jetson Orin NX |
| 内存占用 | RAM | < 8GB | 运行时监控 |
| 模型大小 | 存储 | < 2GB | 文件系统 |

### 5.2 安全要求

#### 5.2.1 数据安全
- [ ] 用户上传图像加密存储
- [ ] 诊断报告访问控制
- [ ] 专家反馈数据脱敏
- [ ] 定期数据备份

#### 5.2.2 模型安全
- [ ] 模型权重文件权限控制
- [ ] 防止模型窃取（API限流）
- [ ] 对抗样本检测
- [ ] 模型输出校验

#### 5.2.3 系统安全
- [ ] 输入验证（防止注入攻击）
- [ ] 错误处理（不泄露敏感信息）
- [ ] 日志审计
- [ ] 定期安全扫描

---

## 六、风险与缓解措施

### 6.1 技术风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| DySnakeConv与YOLOv8集成复杂 | 中 | 高 | 分步集成，先单元测试 |
| TensorRT不支持动态卷积 | 中 | 中 | 准备ONNX备用方案 |
| LLaVA模型过大，边缘端部署困难 | 高 | 高 | 使用量化+蒸馏压缩 |
| 增量学习导致灾难性遗忘 | 中 | 高 | 经验回放+参数隔离 |

### 6.2 资源风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| GPU显存不足 | 中 | 高 | 使用梯度累积+混合精度 |
| 训练数据不足 | 低 | 高 | 数据增强+生成式合成 |
| 开发时间延期 | 中 | 中 | 分阶段交付，优先核心功能 |

---

## 七、下一步行动

### 7.1 立即执行（本周）

1. **环境准备**
   ```bash
   # 安装新增依赖
   pip install transformers>=4.35.0 peft>=0.6.0 accelerate>=0.24.0
   ```

2. **代码审查**
   - 审查所有新开发模块的接口兼容性
   - 确保与现有系统组件兼容

3. **开始Phase 1开发**
   - 优先实现VisionAgent增强
   - 这是所有后续功能的基础

### 7.2 关键决策点

| 决策 | 选项 | 建议 |
|------|------|------|
| LLaVA模型选择 | Vicuna-7B / LLaMA-2-7B | 建议使用Vicuna-7B（更好的指令遵循） |
| 边缘端优化 | TensorRT / ONNX Runtime | 优先TensorRT，备用ONNX |
| 增量学习策略 | 经验回放 / 参数隔离 | 两者结合使用 |

---

## 八、附录

### 8.1 文件清单

```
项目结构:
WheatAgent/
├── main.py                      # 主程序入口
├── app.py                       # Web界面
├── src/
│   ├── vision/                  # 感知层
│   │   ├── vision_engine.py     # VisionAgent（待增强）
│   │   ├── dy_snake_conv.py     # 动态蛇形卷积 ✅
│   │   ├── sppelan_module.py    # SPPELAN ✅
│   │   ├── sta_module.py        # STA ✅
│   │   └── data_augmentation.py # 数据增强（待开发）
│   ├── cognition/               # 认知层
│   │   ├── llava_engine.py      # Agri-LLaVA ✅
│   │   ├── prompt_templates.py  # 提示工程 ✅
│   │   ├── trainer.py           # 训练器 ✅
│   │   └── cognition_engine.py  # 认知引擎 ✅
│   ├── fusion/                  # 融合层
│   │   ├── fusion_engine.py     # FusionAgent（待增强）
│   │   ├── kga_module.py        # KGA ✅
│   │   └── cross_attention.py   # 跨模态注意力 ✅
│   ├── graph/                   # 知识层
│   │   ├── graph_engine.py      # KnowledgeAgent
│   │   └── graphrag_engine.py   # GraphRAG ✅
│   ├── action/                  # 行动层
│   │   ├── learner_engine.py    # ActiveLearner（待增强）
│   │   ├── experience_replay.py # 经验回放 ✅
│   │   └── human_in_the_loop.py # 人机协同 ✅
│   └── deploy/                  # 部署层
│       ├── export.py            # 模型导出（待增强）
│       ├── optimize.py          # 推理优化（待开发）
│       └── edge.py              # 边缘端适配（待开发）
├── tests/                       # 测试目录（待完善）
├── scripts/                     # 脚本目录（待创建）
└── docs/                        # 文档目录
```

### 8.2 依赖更新

```
# requirements.txt 新增依赖
transformers>=4.35.0
peft>=0.6.0
accelerate>=0.24.0
bitsandbytes>=0.41.0
onnx>=1.15.0
onnxruntime-gpu>=1.16.0
# tensorrt>=8.6.0  # 可选，需手动安装
```

---

**文档版本**: v1.0  
**制定日期**: 2026-02-10  
**下次评审**: 2026-02-17
