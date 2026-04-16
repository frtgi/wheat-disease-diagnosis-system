# 基于多模态融合的小麦病害诊断系统 - 智能体架构设计文档

**版本**: V12.0
**更新日期**: 2026-04-16
**项目**: 基于多模态融合的小麦病害诊断系统
**基于**: V12 架构深度分析报告

---

## 1. 智能体设计概述

### 1.1 设计理念

本智能体采用**四层分离架构**（API→Service→Core→Model），通过5种设计模式（Facade/Singleton/State/Strategy/Observer）实现关注点分离和灵活扩展。诊断核心链路从API入口到数据库持久化经过10个关键环节，每个环节职责明确、可独立测试。

### 1.2 核心设计原则

| 原则 | 说明 | 实现方式 |
|------|------|---------|
| **分层分离** | API/Service/Core/Model四层架构 | 层间接口契约明确，依赖注入 |
| **模块化** | 功能独立、高内聚低耦合 | 四大核心模块，Facade门面封装 |
| **可扩展** | 易于添加新功能和新模型 | 策略模式、抽象基类 |
| **可解释** | 决策过程透明、可追溯 | 知识图谱增强、GraphRAG引用溯源 |
| **高效能** | 低延迟、低资源占用 | INT4量化、FP16推理、LRU缓存 |
| **流式响应** | 实时进度反馈 | SSE事件推送、心跳保活、背压控制 |

---

## 2. 智能体参考架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     小麦病害诊断智能体架构 V12.0                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     交互层 (Interaction Layer)                      │ │
│  │  ┌──────────────┐  ┌──────────────┐                               │ │
│  │  │  Vue 3 Web   │  │   REST API   │                               │ │
│  │  │  (前端SPA)   │  │  (FastAPI)   │                               │ │
│  │  └──────────────┘  └──────────────┘                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     感知层 (Perception Layer)                       │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                    VisionAgent (视觉代理)                     │  │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │ │
│  │  │  │ YOLOv8s检测  │  │ 图像预处理  │  │ FP16推理    │          │  │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     认知层 (Cognition Layer)                        │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                  CognitionEngine (认知引擎)                   │  │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │ │
│  │  │  │Qwen3-VL-2B  │  │  Prompt管理  │  │ INT4量化推理 │          │  │ │
│  │  │  │ (INT4量化)   │  │             │  │             │          │  │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     知识层 (Knowledge Layer)                        │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                   KnowledgeAgent (知识代理)                   │  │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │ │
│  │  │  │ Neo4j 图谱  │  │ TransE 嵌入  │  │ GraphRAG    │          │  │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                  融合层 (Fusion Layer) [Facade Pattern]             │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │           MultimodalFusionService (Facade 门面)               │  │ │
│  │  │  ┌───────────────────┐  ┌────────────────┐  ┌────────────┐ │  │ │
│  │  │  │ FeatureExtractor  │  │ FusionEngine   │  │FusionAnnot.│ │  │ │
│  │  │  │ (YOLO+Qwen+Graph) │  │ (KAD-Former)   │  │ (知识增强) │ │  │ │
│  │  │  └───────────────────┘  └────────────────┘  └────────────┘ │  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                  基础设施层 (Infrastructure Layer)                   │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │ SSE流式推送  │  │ JWT双令牌   │  │ 并发限流    │               │ │
│  │  │ (Observer)  │  │ (30m/7d)    │  │ (≤3并发)    │               │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │ GPU监控     │  │ Redis黑名单 │  │ XSS防护     │               │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 诊断核心链路

```
用户上传图像
    │
    ▼
[ai_diagnosis.py] POST /api/v1/diagnosis/multimodal
    │ 函数: diagnose_multimodal_stream()
    │ 职责: SSE流式响应编排、并发限流、GPU检查
    │
    ▼
[fusion_service.py] MultimodalFusionService.diagnose_async()
    │ 函数: diagnose_async() — Facade入口
    │ 职责: 编排3个子系统，PipelineTimer计时
    │
    ├─→ [fusion_feature_extractor.py] FeatureExtractor
    │      │ 职责: 提取视觉+文本+知识特征
    │      │
    │      ├─→ [yolo_service.py] YOLOService.detect()
    │      │      │ FP16半精度 + LRU缓存(64条)
    │      │
    │      ├─→ [qwen_service.py] QwenService.analyze()
    │      │      │ Facade → qwen_loader + qwen_preprocessor
    │      │      │       + qwen_inferencer + qwen_postprocessor
    │      │
    │      └─→ [graphrag_service.py] GraphRAGService.query()
    │             │ Neo4j子图检索 + TransE嵌入
    │
    ├─→ [fusion_engine.py] FusionEngine.fuse()
    │      │ KAD-Former交叉注意力融合
    │      │ 输出: FusionResult(disease_name, confidence, severity, ...)
    │
    └─→ [fusion_annotator.py] FusionAnnotator.annotate()
           │ 知识增强、防治建议生成
           │
           ▼
[diagnosis.py(DB)] 持久化
    │ diagnoses表 + diagnosis_confidences表
    │
    ▼
[ai_diagnosis.py] SSE事件推送
    │ ProgressEvent → HeartbeatEvent(15s) → CompleteEvent
    │
    ▼
前端 EventSource 接收并渲染
```

---

## 3. 智能体模块详细设计

### 3.1 VisionAgent（视觉代理）

**职责**: 负责视觉感知，检测图像中的病害目标

**核心能力**:
- 多尺度目标检测（17类小麦病害/虫害）
- 边界框回归
- 置信度评估
- FP16半精度推理
- LRU推理缓存（64条）

**类结构**:
```
YOLOService
├── __init__(model_path: str, device: str)
├── detect(image: Image) -> DetectionResult
├── detect_batch(images: List[Image]) -> List[DetectionResult]
└── get_stats() -> Dict
```

**数据流**:
```
输入图像 (H×W×3)
    │
    ▼
图像预处理 (image_preprocessor.py)
├── Resize (640×640)
├── Normalize
└── Transpose (HWC→CHW)
    │
    ▼
YOLOv8s 推理 (FP16半精度)
├── Backbone (CSPDarknet)
├── Neck (PANet)
└── Head (Detection Head)
    │
    ▼
后处理
├── NMS (IoU=0.45)
├── 置信度过滤 (conf=0.25)
└── 边界框解码
    │
    ▼
DetectionResult
├── boxes: [x1, y1, x2, y2]
├── classes: [0, 1, ...]
├── scores: [0.95, 0.87, ...]
└── visual_embeddings: Tensor
```

### 3.2 CognitionEngine（认知引擎）

**职责**: 负责多模态理解和语义推理

**核心能力**:
- 图像语义理解
- 诊断报告生成
- 知识问答
- INT4量化推理（显存优化）

**类结构**:
```
QwenService (Facade门面)
├── __init__(config: QwenConfig)
├── analyze(image: Image, symptoms: str) -> AnalysisResult
└── get_model_info() -> Dict

QwenModelLoader (Singleton单例)
├── __new__(cls, *args, **kwargs)  # __new__方式单例
├── ensure_loaded() -> None        # 状态机: UNLOADED→LOADING→READY
├── unload() -> None               # 释放GPU显存
└── reset() -> None                # ERROR→UNLOADED

ModelState (State状态机)
├── UNLOADED  # 未加载（节省显存）
├── LOADING   # 正在加载（阻塞新请求）
├── READY     # 就绪可用（接受诊断请求）
└── ERROR     # 加载失败（需手动恢复）

QwenPreprocessor
├── preprocess(image, symptoms) -> ModelInput

QwenInferencer
├── infer(model_input) -> RawOutput

QwenPostprocessor
├── postprocess(raw_output) -> AnalysisResult
```

**模型状态转换规则**:
```
UNLOADED ──ensure_loaded()──→ LOADING ──加载成功──→ READY
    ↑                           │                     │
    │                           └──加载失败──→ ERROR   │
    │                                           │     │
    └───────────reset()─────────────────────────┘     │
    └─────────────────────unload()────────────────────┘
```

**Prompt模板**:
```python
AGRICULTURE_SYSTEM_PROMPT = """你是一位专业的农业病害诊断专家，具备以下能力：
1. 准确识别小麦病害类型（真菌病害、虫害、病毒病害等）
2. 分析病害症状（病斑形状、颜色、分布等）
3. 提供科学的防治建议（农业防治、化学防治、生物防治）
4. 解释病害发生规律和环境因素

请以专业、准确、易懂的方式回答用户问题。"""
```

### 3.3 KnowledgeAgent（知识代理）

**职责**: 负责知识存储、检索和推理

**核心能力**:
- 知识图谱查询（Neo4j Cypher）
- 语义相似度计算（TransE嵌入）
- GraphRAG知识增强
- 可解释性溯源

**类结构**:
```
GraphRAGService
├── __init__(neo4j_uri: str, username: str, password: str)
├── query(disease_name: str) -> KnowledgeContext
├── retrieve(query: str, top_k: int = 5) -> List[KnowledgeTriple]
└── augment(prompt: str, context: List[KnowledgeTriple]) -> str
```

**查询流程**:
```
诊断请求 → 病害名称 → Neo4j Cypher查询
    │
    ├─→ 匹配病害节点 → 获取关联知识
    │   MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)
    │   MATCH (d)-[:HAS_TREATMENT]->(t:Treatment)
    │   MATCH (d)-[:OCCURS_IN]->(c:Condition)
    │
    ├─→ TransE嵌入计算 → 语义相似度排序
    │   ||d_embedding + r_embedding - t_embedding||
    │
    └─→ 返回增强知识 → 注入诊断结果
```

**知识图谱Schema**:
```
实体类型 (Entity Types):
- disease: 病害 (16 个)
- pathogen: 病原体 (13 个)
- symptom: 症状 (21 个)
- control: 防治方法 (15 个)
- env: 环境因素 (10 个)
- pest: 虫害 (7 个)
- stage: 生长阶段 (6 个)
- part: 感染部位 (5 个)
- variety: 抗病品种 (4 个)
- region: 地区 (4 个)
- severity: 严重程度 (3 个)
- crop: 作物 (1 个)
- health: 健康状况 (1 个)

关系类型 (Relation Types):
- CAUSED_BY: 由...引起
- HAS_SYMPTOM: 具有症状
- TREATED_BY: 被...治疗
- INFECTS: 感染
- OCCURS_AT: 发生在
- DURING: 在...期间
- FAVORS: 有利于
- TARGETS: 目标为
- SIMILAR_TO: 类似于
- PREVENTS: 预防
- HAS_SEVERITY: 严重程度为
- RESISTANT_TO: 抗...
- GROWN_IN: 种植于
- PREVALENT_IN: 流行于
- VECTOR_FOR: 传播媒介
```

### 3.4 FusionModule（多模态融合模块）[Facade Pattern]

**职责**: 负责视觉特征、文本特征和知识特征的深度融合（Facade门面模式）

**核心能力**:
- 多层级特征提取 (FeatureExtractor)
- KAD-Former交叉注意力融合 (FusionEngine)
- 知识增强标注 (FusionAnnotator)
- SSE流式事件管理

**类结构**:
```
MultimodalFusionService (Facade门面)
├── __init__(config: FusionConfig)
├── diagnose_async(request) -> AsyncGenerator[SSEEvent]
├── diagnose(request) -> FusionResult  [@deprecated]
└── get_fused_features() -> Tensor

FeatureExtractor (特征提取器)
├── extract_visual_features(image) -> VisualFeatures
├── extract_text_features(symptoms) -> TextFeatures
└── extract_knowledge_features(query) -> KnowledgeFeatures

FusionEngine (KAD-Former融合引擎)
├── __init__(vision_dim, knowledge_dim)
├── fuse(vision, text, knowledge) -> FusedFeatures
└── get_attention_weights() -> Tensor

FusionAnnotator (结果标注器)
├── annotate(result, knowledge_context) -> AnnotatedResult
├── generate_recommendations(disease_name) -> List[str]
└── build_response(fusion_result) -> Dict
```

**KAD-Former融合流程**:
```
视觉特征 (YOLOv8) ──→ [投影层] ──→ 视觉嵌入 (dim=768)
                                          │
                                    [KAD交叉注意力]
                                          │
文本特征 (Qwen3-VL) ──→ [投影层] ──→ 文本嵌入 (dim=768)
                                          │
                                    [融合决策头]
                                          │
知识特征 (GraphRAG) ──→ [投影层] ──→ 知识嵌入 (dim=768)
                                          │
                                          ▼
                                   FusionResult
```

**FusionResult数据结构**:
```python
@dataclass
class FusionResult:
    disease_name: str
    confidence: float
    severity: str
    all_confidences: List[DiseaseConfidence]
    description: str
    recommendations: List[str]
    knowledge_links: List[dict]
```

**策略模式 — 融合策略选择**:
```python
async def diagnose_async(self, image=None, symptoms=None, ...):
    if image and symptoms:
        result = await self._fuse_multimodal(features)
    elif image:
        result = await self._fuse_visual_only(features)
    else:
        result = await self._fuse_text_only(features)
```

| 策略 | 输入 | 处理流程 | 置信度 |
|------|------|---------|--------|
| 多模态融合 | 图像+症状 | YOLO检测 + Qwen分析 + KAD-Former交叉融合 | 最高 |
| 纯视觉 | 仅图像 | YOLO检测 + Qwen分析 + 视觉特征融合 | 高 |
| 纯文本 | 仅症状 | Qwen文本分析 + GraphRAG知识推理 | 中 |

---

## 4. 智能体通信机制

### 4.1 内部通信 — 直接函数调用

本系统采用**直接函数调用**模式，模块间通过Python函数调用和依赖注入进行通信：

```
┌─────────────────────────────────────────────────────────────┐
│                  直接调用 (Direct Call)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  API层 ──调用──→ fusion_service.diagnose_async()             │
│                      │                                       │
│                      ├──→ feature_extractor.extract()        │
│                      │        ├──→ yolo_service.detect()     │
│                      │        ├──→ qwen_service.analyze()    │
│                      │        └──→ graphrag_service.query()  │
│                      │                                       │
│                      ├──→ fusion_engine.fuse()               │
│                      │                                       │
│                      └──→ fusion_annotator.annotate()        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**依赖注入方式**:
```python
@router.post("/diagnosis/multimodal")
async def diagnose(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    rate_limiter = Depends(get_rate_limiter),
):
    result = await fusion_service.diagnose_async(...)
```

### 4.2 外部通信 — SSE流式响应

**SSE事件类型体系**:

| 事件类型 | 触发时机 | 数据内容 | 前端处理 |
|----------|---------|---------|---------|
| `start` | 诊断开始 | diagnosis_id | 初始化进度条 |
| `progress` | 各阶段完成 | step, progress%, message | 更新进度条 |
| `heartbeat` | 每15秒 | 空 | 重置超时计时器 |
| `log` | 关键日志 | level, message | 显示日志面板 |
| `step_indicator` | 阶段切换 | current_step, total_steps | 更新步骤指示器 |
| `complete` | 诊断完成 | 完整诊断结果 | 渲染融合结果 |
| `error` | 发生错误 | error_code, message | 显示错误提示 |

**SSE关键参数**:

| 参数 | 值 | 说明 |
|------|-----|------|
| 心跳间隔 | 15秒 | 防止代理/CDN超时断连 |
| 诊断超时 | 120秒 | 整体诊断时间上限 |
| 背压队列 | 100 | 事件缓冲区大小 |
| 重连上限 | 3次 | 客户端最大重连次数 |

---

## 5. 智能体安全机制

### 5.1 认证与鉴权

**JWT双令牌认证机制**:

```
登录请求 → 验证用户名密码(bcrypt)
    │
    ├─→ 生成 Access Token (30分钟有效)
    │   payload: {user_id, role, exp, type: "access"}
    │
    └─→ 生成 Refresh Token (7天有效)
        payload: {user_id, exp, type: "refresh"}

API请求 → 携带 Access Token
    │
    ├─→ 有效 → 正常处理请求
    │
    └─→ 过期 → 前端自动使用 Refresh Token 刷新
        │
        ├─→ 刷新成功 → 新 Access Token + 重试原请求
        │
        └─→ 刷新失败 → 跳转登录页
```

**Token黑名单**: 使用Redis Set存储已撤销的Token，TTL自动过期

### 5.2 安全能力状态

| 安全能力 | 实现状态 | 说明 |
|---------|---------|------|
| **JWT双令牌认证** | ✅ 已实现 | Access 30min + Refresh 7days |
| **bcrypt密码哈希** | ✅ 已实现 | 密码安全存储 |
| **Token黑名单** | ✅ 已实现 | Redis Set + TTL自动过期 |
| **XSS防护** | ✅ 已实现 | 输入净化 + 输出转义 |
| **速率限制** | ✅ 已实现 | SlowAPI频率限流 + DiagnosisRateLimiter并发限流 |
| **CORS策略** | ✅ 已实现 | 可配置白名单 |
| **RBAC权限控制** | ✅ 已实现 | farmer/technician/admin角色 |
| **输入验证** | ✅ 已实现 | Pydantic V2 Schema校验 |
| **GPU过载保护** | ✅ 已实现 | 显存≥90%返回503 |

### 5.3 并发限流架构

```
客户端请求 → SlowAPI(频率限流) → FastAPI(业务处理)
                                        ↓
                              DiagnosisRateLimiter(并发≤3)
                                        ↓
                                   等待队列(≤10)
                                        ↓
                                      Redis(计数存储)
```

**GPU降级策略**:
```
GPU显存使用率 < 90% → 正常接受诊断请求
GPU显存使用率 ≥ 90% → 返回 503 "计算资源繁忙，请稍后重试"
nvidia-smi 不可用   → 仅做并发限流（跳过显存检查）
并发数已达上限(3)    → 返回 429 "服务器繁忙，已加入队列"
队列已满(10)        → 返回 429 "服务器繁忙，请稍后重试"
```

---

## 6. 智能体性能优化

### 6.1 推理优化

| 优化项 | 技术 | 效果 |
|--------|------|------|
| **模型量化** | Qwen3-VL INT4量化 | 显存减少75%，~2.6GB |
| **半精度推理** | YOLOv8s FP16 | 推理速度提升2x |
| **推理缓存** | LRU缓存(64条) + 图像哈希 | 重复查询提速10x |
| **异步推理** | asyncio + 限流队列 | 延迟降低40% |
| **懒加载** | QwenModelLoader延迟初始化 | 启动速度提升 |
| **SSE流式** | 实时进度推送 | 用户体验提升 |

### 6.2 性能基准

| 指标 | 定义 | 目标值 | 实测值 |
|------|------|--------|--------|
| **YOLO推理延迟** | 单图检测时间 | ≤150ms | 225ms (CPU) |
| **SSE首事件延迟** | 首个事件到达时间 | ≤500ms | 0.01ms |
| **完整诊断延迟** | 端到端诊断时间 | ≤40s | 185.8ms (YOLO-only) |
| **显存占用** | 峰值显存使用 | ≤4GB | ~2.6GB (INT4) |
| **知识覆盖率** | 知识图谱覆盖病害比例 | ≥95% | 100% |

---

## 7. 智能体评估指标

### 7.1 测试覆盖

| 版本 | 测试数量 | 通过率 | 说明 |
|------|----------|--------|------|
| V10 后端 | 1102 | 99.4% | 全面后端验证 |
| V11 前端 | 346 | 98.8% | 前端闭环测试 |
| **总计** | **1448** | **99%+** | 含单元/集成/E2E |

### 7.2 架构成熟度

**综合评分：3.7/5（良好 — Level 3 Defined）**

| 维度 | 评分 | 说明 |
|------|------|------|
| 后端配置管理 | 3.5 | 功能完备但缺乏Pydantic BaseSettings |
| 后端应用架构 | 3.5 | 功能完善但存在过时模式（@app.on_event） |
| 前端工程化 | 3.5 | 核心依赖现代但缺ESLint/Prettier |
| 前端构建配置 | 3.5 | 基础完善但缺build.target和预压缩 |
| 测试覆盖度 | 4.0 | 1448用例，99%+通过率 |
| 文档体系 | 4.5 | 15个文档，5个分类目录 |

---

## 8. 智能体扩展性设计

### 8.1 多作物扩展

**扩展架构**:
```
小麦病害诊断
    │
    ├── 扩展点 1: 作物模型
    │   ├── WheatModel (小麦)
    │   ├── RiceModel (水稻)
    │   └── CornModel (玉米)
    │
    ├── 扩展点 2: 病害知识库
    │   ├── WheatKG (小麦知识图谱)
    │   └── RiceKG (水稻知识图谱)
    │
    └── 扩展点 3: 检测模型
        ├── WheatDetector (YOLOv8s-Wheat)
        └── RiceDetector (YOLOv8s-Rice)
```

### 8.2 融合策略扩展

新增融合策略只需在`diagnose_async`中添加新的条件分支和对应的`_fuse_xxx`方法，不影响现有策略。

---

## 9. 设计模式应用总结

| 模式 | 应用位置 | 理论定义 | 项目体现 |
|------|---------|---------|---------|
| **Facade** | fusion_service.py, qwen_service.py | 为子系统提供统一高层接口 | MultimodalFusionService封装3个子系统 |
| **Singleton** | qwen_loader.py, rate_limiter.py | 确保类只有一个实例 | QwenModelLoader(__new__) + 模块级实例 |
| **State** | qwen_loader.py | 内部状态改变时改变行为 | ModelState: UNLOADED→LOADING→READY→ERROR |
| **Strategy** | fusion_service.py | 算法族分别封装，互相替换 | 多模态/纯视觉/纯文本三种融合策略 |
| **Observer** | ai_diagnosis.py | 一对多依赖，状态改变自动通知 | SSE事件推送(start/progress/complete) |

---

## 10. 技术债务与改进方向

### 10.1 P1 高优先级

| 编号 | 描述 | 修复成本 |
|------|------|---------|
| TD-001 | SSE async generator GeneratorExit未处理 | 1-2h |
| TD-002 | SSE 取消处理同根因 | 含TD-001 |
| TD-003 | SSE 进度回调 event loop 问题 | 30min |
| TD-008 | ECharts打包体积偏大（628KB） | 2h |

### 10.2 改进方向

- ⚠️ **SSE异步边界处理**: GeneratorExit和event loop问题需优先修复
- ⚠️ **配置管理现代化**: 迁移至Pydantic BaseSettings
- ⚠️ **工程规范工具化**: 引入ESLint/Prettier/CI/CD
- ⚠️ **前端性能优化**: ECharts按需引入 + Gzip压缩

---

## 11. 源码索引

| 模块 | 文件路径 | 核心类/函数 |
|------|----------|------------|
| API路由层 | src/web/backend/app/api/v1/ai_diagnosis.py | diagnose_multimodal_stream() |
| 融合服务 | src/web/backend/app/services/fusion_service.py | MultimodalFusionService |
| 特征提取 | src/web/backend/app/services/fusion_feature_extractor.py | FeatureExtractor |
| 融合引擎 | src/web/backend/app/services/fusion_engine.py | FusionEngine |
| 结果标注 | src/web/backend/app/services/fusion_annotator.py | FusionAnnotator |
| YOLO服务 | src/web/backend/app/services/yolo_service.py | YOLOService |
| Qwen服务 | src/web/backend/app/services/qwen/qwen_service.py | QwenService |
| Qwen加载器 | src/web/backend/app/services/qwen/qwen_loader.py | QwenModelLoader, ModelState |
| GraphRAG服务 | src/web/backend/app/services/graphrag_service.py | GraphRAGService |
| 安全模块 | src/web/backend/app/core/security.py | JWT双令牌 |
| 限流器 | src/web/backend/app/core/rate_limiter.py | DiagnosisRateLimiter |
| GPU监控 | src/web/backend/app/core/gpu_monitor.py | GPUMonitor |
| 配置管理 | src/web/backend/app/core/config.py | Settings |
| XSS防护 | src/web/backend/app/utils/xss_protection.py | XSSProtection |

---

*文档更新时间：2026-04-16*
*版本：V12.0 (基于V12架构深度分析报告重写)*
