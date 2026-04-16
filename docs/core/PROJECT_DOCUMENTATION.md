# 基于多模态融合的小麦病害诊断系统 — 技术白皮书

> **版本**: V12.0 | **日期**: 2026-04-05 | **综合评分**: 93.6/100
> **项目名称**: WheatAgent (小麦智能体)
> **代码规模**: ~20,200 行 Python (96 文件) + Vue 3 前端

---

## 目录

- [第1章: 项目背景与目标](#第1章-项目背景与目标)
- [第2章: 技术架构总览](#第2章-技术架构总览)
- [第3章: 多模态融合诊断流程](#第3章-多模态融合诊断流程)
- [第4章: AI 模型体系](#第4章-ai-模型体系)
- [第5章: 安全机制](#第5章-安全机制)
- [第6章: 数据库设计](#第6章-数据库设计)
- [第7章: 配置管理](#第7章-配置管理)
- [第8章: 性能与优化](#第8章-性能与优化)
- [第9章: 部署与运维](#第9章-部署与运维)

---

## 第1章: 项目背景与目标

### 1.1 问题背景

小麦是中国第一大粮食作物，年种植面积约 **2400 万公顷**，占全国粮食总产量的 **20% 以上**。传统病害诊断依赖农技人员现场目视判断，存在以下核心痛点：

| 痛点维度 | 现状描述 | 量化指标 |
|---------|---------|----------|
| **时效性差** | 农技人员需到现场勘察，响应周期长 | 平均响应时间 **2-7 天** |
| **覆盖率低** | 基层农技人员严重不足，难以覆盖所有农户 | 人均服务面积 >5000 亩 |
| **主观性强** | 不同技术人员经验水平差异大 | 诊断一致性仅 **60-70%** |
| **知识断层** | 年轻农技人员缺乏实践经验 | 新手误诊率高达 **30%+** |
| **成本高昂** | 专家现场指导成本高，农民负担重 | 单次专家出诊费用 **200-500 元** |

### 1.2 解决方案

WheatAgent 采用**多模态融合 AI** 技术，整合视觉检测、语言理解和领域知识三大能力：

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WheatAgent 多模态融合架构                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   📸 图像感知层        🧠 语义理解层         🕸️ 知识推理层          │
│   ┌─────────────┐    ┌─────────────┐      ┌─────────────┐          │
│   │ YOLOv8      │    │ Qwen3-VL    │      │ GraphRAG    │          │
│   │ 视觉检测     │ →  │ 多模态理解   │ →    │ 知识检索     │          │
│   └─────────────┘    └─────────────┘      └─────────────┘          │
│         │                   │                    │                 │
│         ▼                   ▼                    ▼                 │
│   ┌─────────────────────────────────────────────────────┐          │
│   │              KAD-Former 融合引擎                      │          │
│   │       Knowledge-Aware Dual-modal Transformer         │          │
│   └─────────────────────────────────────────────────────┘          │
│                              │                                      │
│                              ▼                                      │
│                   ┌──────────────────┐                             │
│                   │   诊断结果输出     │                             │
│                   │ 置信度 + 防治建议  │                             │
│                   └──────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 三大核心技术能力

1. **📸 图像感知 (Visual Perception)**
   - **技术**: YOLOv8s 目标检测模型
   - **能力**: 自动定位病害区域（ROI），识别 16 类小麦病害/虫害
   - **精度**: mAP@50 = 95.39%, mAP@50-95 = 90.02%
   - **推理速度**: GPU 模式 <50ms, CPU 模式 ~187ms

2. **🧠 语义理解 (Semantic Understanding)**
   - **技术**: Qwen3-VL-2B-Instruct 多模态大语言模型
   - **能力**: 理解病害视觉特征，生成自然语言诊断描述
   - **优化**: INT4 量化（显存 ~2.6GB），Flash Attention 2 加速
   - **特性**: 支持 Thinking 推理链模式，可解释性强

3. **🕸️ 知识推理 (Knowledge Reasoning)**
   - **技术**: GraphRAG (Graph Retrieval-Augmented Generation)
   - **数据源**: Neo4j 图数据库（106 实体, 178 三元组）
   - **能力**: 检索农业专家知识库，提供防治建议和病因分析
   - **实体类型**: disease/symptom/pest/treatment/growth_stage

### 1.3 设计目标

| 目标维度 | 技术指标 | 当前达成状态 | 验证方法 |
|---------|---------|-------------|---------|
| **诊断准确率** | Top-1 >85% | 基准测试中 | 人工标注验证集 |
| **响应延迟** | 首结果 <3s | ✅ SSE首事件 **0.01ms** | BASELINE_PERFORMANCE.md |
| **并发能力** | ≥3 并发诊断 | ✅ RateLimiter 限制 | inference_queue.py |
| **系统可用性** | >99% | ✅ 健康检查完善 | health.py / main.py |
| **代码质量** | 评分 >90 | ✅ **93.6/100** | V7_PROJECT_ANALYSIS.md |
| **安全合规** | OWASP Top 10 | ✅ 认证覆盖率 **90.9%** | security.py / audit.py |
| **可观测性** | 完整监控链路 | ✅ Prometheus + SSE 推送 | monitoring/ 目录 |

### 1.4 核心业务价值

```
┌─────────────────────────────────────────────────────────────────┐
│                     三端业务价值体系                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   农户端     │    │   农技端     │    │   管理端     │         │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤         │
│  │ • 快速诊断   │    │ • 辅助决策   │    │ • 数据追踪   │         │
│  │ • 防治建议   │    │ • 提升准确率  │    │ • 质量监控   │         │
│  │ • 成本降低   │    │ • 知识传承   │    │ • 合规审计   │         │
│  │ • 24h可用   │    │ • 减少误诊   │    │ • 趋势预测   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第2章: 技术架构总览

### 2.1 整体架构图 (四层 + AI + Data)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           前端展示层 (Presentation Layer)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Diagnosis │  │ Records  │  │Knowledge │  │ Dashboard │  │   User   │       │
│  │   .vue   │  │   .vue   │  │   .vue   │  │   .vue   │  │   .vue   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                                    │
│  │SSE Progress│  │FusionResult│  │MultiModalInput│                               │
│  │   .vue   │  │   .vue   │  │    .vue   │                                    │
│  └──────────┘  └──────────┘  └──────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ HTTP/SSE/WebSocket
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API 路由层 (API Layer)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        FastAPI Application                          │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │              中间件链 (Middleware Chain)                     │    │   │
│  │  │  GZip → CORS → Request-ID → Security-Headers → Retry(3x)   │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ diagnosis_ │ │   user.py  │ │knowledge.py│ │  upload.py │       │   │
│  │  │ router.py  │ │  (962行)   │ │  (326行)   │ │   (87行)   │       │   │
│  │  │ (1626行) ⭐ │ │            │ │            │ │            │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ reports.py │ │ metrics.py │ │  logs.py   │ │  stats.py  │       │   │
│  │  │  (139行)   │ │  (391行)   │ │  (221行)   │ │  (146行)   │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          服务编排层 (Service Layer)                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                  MultimodalFusionService (Facade) ⭐                │     │
│  │                       fusion_service.py (649行)                     │     │
│  ├────────────────────────────────────────────────────────────────────┤     │
│  │                                                                    │     │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │     │
│  │  │ FeatureExtractor  │  │   FusionEngine    │  │ ResultAnnotator │  │     │
│  │  │ (424行)          │  │   (467行)         │  │   (269行)       │  │     │
│  │  ├──────────────────┤  ├──────────────────┤  ├─────────────────┤  │     │
│  │  │• YOLO视觉特征    │  │• KAD-Former融合   │  │• 置信度校准     │  │     │
│  │  │• Qwen语义特征    │  │• 动态权重计算     │  │• ROI标注        │  │     │
│  │  │• GraphRAG知识    │  │• 降级处理策略     │  │• 缓存写入       │  │     │
│  │  └──────────────────┘  └──────────────────┘  └─────────────────┘  │     │
│  │                                                                    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐       │
│  │ QwenService│ │YOLOv8Servic│ │GraphRAGServi│ │ MockDiagnosisSvc  │       │
│  │  (496行)   │ │  (538行)   │ │  (569行)    │ │    (260行)        │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          核心基础设施层 (Core Infrastructure)                 │
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │   config.py │ │  security.py│ │ database.py │ │   rate_limiter.py   │  │
│  │   (163行)   │ │  (277行)    │ │  (106行)    │ │    (160行)          │  │
│  │ 全局配置中心 │ │ JWT/RBAC    │ │ 连接池管理  │ │ 并发限流控制        │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘  │
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ ai_config.py│ │error_codes.py│ │gpu_monitor.py│ │ startup_manager.py │  │
│  │  (265行)    │ │  (928行)    │ │  (187行)    │ │    (468行)         │  │
│  │ AI模型配置  │ │ 统一错误码   │ │ 显存监控    │ │ 4阶段启动管理      │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      监控子系统 (monitoring/)                         │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────────┐   │   │
│  │  │ alert_manager  │  │metrics_collector│  │  monitoring_api     │   │   │
│  │  │   (651行)      │  │   (576行)       │  │    (526行)          │   │   │
│  │  └────────────────┘  └────────────────┘  └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            数据持久层 (Data Layer)                           │
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │   MySQL 8.0 │ │   Neo4j 5.x │ │    Redis    │ │  本地文件存储      │  │
│  │  业务数据    │ │  知识图谱    │ │  缓存/会话  │ │   (图像文件)        │  │
│  │  (12张表)   │ │ (106实体)    │ │  (7.2版本)  │ │   (图像文件)        │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        ORM 模型层 (app/models/)                       │   │
│  │  user.py | diagnosis.py | disease.py | knowledge.py | image.py | audit.py │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 分层职责说明

| 层次 | 核心职责 | 关键组件 | 技术选型 |
|------|---------|---------|---------|
| **API 层** | 路由分发、认证鉴权、参数校验、SSE 流式响应、限流控制 | `diagnosis_router.py`, `user.py`, `sse_stream_manager.py` | FastAPI + Pydantic |
| **Service 层** | 业务逻辑编排、Facade 门面模式、缓存策略、降级处理 | `fusion_service.py`, `qwen_service.py`, `yolo_service.py` | 异步 Python |
| **Core 层** | 配置管理、安全机制、日志系统、GPU 监控、AI 模型配置 | `config.py`, `security.py`, `ai_config.py`, `gpu_monitor.py` | Pydantic Settings |
| **Model 层** | ORM 映射、数据验证、Schema 定义、关系管理 | `user.py`, `diagnosis.py`, `audit.py` 等 7 个模型 | SQLAlchemy 2.0 |
| **Data 层** | 数据持久化、图存储、缓存 | MySQL 8.0, Neo4j, Redis 7.2 | 多存储引擎 |

### 2.3 关键设计模式

| 模式名称 | 应用位置 | 解决问题 | 实现细节 |
|---------|---------|---------|---------|
| **Facade 门面模式** | `fusion_service.py` | 封装融合流程复杂性 | `MultimodalFusionService` 统一协调 FeatureExtractor→FusionEngine→ResultAnnotator 三阶段 |
| **Singleton 单例模式** | `rate_limiter.py`, `gpu_monitor.py` | 全局唯一资源管理 | `RateLimiter` 令牌桶全局实例；`GPUMonitor` 单例采集器 |
| **Strategy 策略模式** | `fusion_engine.py` | 多种输入类型适配 | 根据 visual/textual/knowledge 可用性动态选择融合策略 |
| **State Machine 状态机** | `qwen_loader.py` | 模型加载生命周期管理 | `ModelState` 枚举: unloaded→loading→ready→error 四状态转换 |
| **Observer 观察者模式** | `monitoring/` 目录 | 指标收集与告警解耦 | `MetricsCollector` 收集指标 → `AlertManager` 触发告警通知 |
| **Decorator 装饰器模式** | `cache_decorators.py`, `fusion_service.py` | 横切关注点分离 | `@cache()`, `@deprecated()` 装饰器增强函数行为 |
| **Factory Method 工厂方法** | `model_manager.py` | 统一模型创建接口 | `ModelManager.create_model()` 根据配置动态实例化 YOLO/Qwen/KAD |

#### 2.3.1 @deprecated 迁移策略 (V5 引入)

**背景**: V5 版本将核心诊断接口从同步迁移到异步,以提高并发性能和 GPU 利用率

**实现位置**: [fusion_service.py:25-45](../src/web/backend/app/services/fusion_service.py#L25-L45)

**装饰器定义**:
```python
def deprecated(replacement: str) -> Callable:
    """
    标记已弃用的方法,调用时发出 DeprecationWarning

    Args:
        replacement: 推荐替代的方法名

    Returns:
        装饰器函数,包装原方法并在调用时发出警告
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} 已弃用，请使用 {replacement} 替代",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**已标记弃用的方法清单**:

| # | 旧方法 (已弃用) | 新方法 (推荐) | 所在文件 | 行号 | 迁移原因 |
|---|----------------|--------------|----------|------|----------|
| 1 | `diagnose()` [同步] | `diagnose_async()` [异步] | fusion_service.py | L366-L500 | 支持异步IO、提高GPU并发 |
| 2 | `_check_cache()` [同步包装] | 内联 `await self._result_annotator.check_cache()` | fusion_service.py | L680-L690 | 消除同步异步混用 |
| 3 | `qwen_service.diagnose()` [同步] | `qwen_service.diagnose_async()` [异步] | qwen_service.py | - | 统一异步接口 |

**开发者迁移指南**:

```python
# ❌ 旧代码 (V4 及之前,已弃用)
from app.services.fusion_service import MultimodalFusionService

service = MultimodalFusionService()
result = service.diagnose(
    image=pil_image,
    symptoms="叶片出现锈状孢子"
)
# 运行时会收到 DeprecationWarning

# ✅ 新代码 (V5+,推荐)
import asyncio
from app.services.fusion_service import MultimodalFusionService

async def async_diagnose():
    service = MultimodalFusionService()
    result = await service.diagnose_async(
        image=pil_image,
        symptoms="叶片出现锈状孢子",
        enable_thinking=True,
        use_graph_rag=True
    )
    return result

# 在 FastAPI 路由中直接调用
@router.post("/diagnosis/fusion")
async def diagnose_fusion(...):
    result = await fusion_service.diagnose_async(...)
    return JSONResponse(result)
```

**关键差异对比**:

| 特性 | diagnose() (旧) | diagnose_async() (新) |
|------|-----------------|---------------------|
| 调用方式 | 同步阻塞 | 异步非阻塞 |
| 返回类型 | Dict[str, Any] | Dict[str, Any] (相同) |
| 缓存查询 | `_check_cache()` 同步包装 | 直接 `await check_cache()` |
| 性能影响 | 阻塞事件循环 | 完全异步,高并发友好 |
| GPU利用 | 单次串行 | 可并行多请求 |
| 弃用状态 | ⚠️ @deprecated | ✅ 推荐 |
| 移除时间表 | 计划 V9.0 正式移除 | - |

**注意事项**:
1. **向后兼容**: 旧方法仍可调用,但会在运行时发出 `DeprecationWarning`
2. **测试覆盖**: 建议更新所有单元测试使用异步版本
3. **第三方集成**: 如果有外部系统调用这些 API,请尽快迁移
4. **监控告警**: 可配置日志系统捕获 DeprecationWarning,跟踪遗留调用

### 2.4 代码规模统计

```
┌─────────────────────────────────────────────────────────────────┐
│                    后端代码规模分布 (96 文件, ~20,200 行)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Top 10 最大文件 (合计 7,835 行, 占 38.8%)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. diagnosis_router.py     1626行 (8.0%)  ⭐ 最复杂      │   │
│  │ 2. user.py                 962行 (4.8%)                 │   │
│  │ 3. error_codes.py          928行 (4.6%)                 │   │
│  │ 4. disease_knowledge.py    896行 (4.4%)                 │   │
│  │ 5. model_manager.py        888行 (4.4%)                 │   │
│  │ 6. image_preprocessor.py   773行 (3.8%)                 │   │
│  │ 7. error_logger.py         710行 (3.5%)                 │   │
│  │ 8. inference_queue.py      700行 (3.5%)                 │   │
│  │ 9. performance_analyzer.py 687行 (3.4%)                 │   │
│  │ 10. diagnosis.py (传统)     665行 (3.3%)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  模块分布:                                                      │
│  ├── app/api/v1/        路由层 (~3,900行, 11文件)               │
│  ├── app/services/       服务层 (~5,200行, 18文件)              │
│  ├── app/core/           核心层 (~5,800行, 20文件)              │
│  ├── app/models/         模型层 (~600行, 7文件)                 │
│  ├── app/schemas/         Schema层 (~250行, 4文件)              │
│  ├── app/utils/          工具层 (~2,400行, 14文件)              │
│  ├── app/monitoring/      监控层 (~1,900行, 4文件)              │
│  └── benchmarks/         基准测试 (~1,000行, 6文件)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第3章: 多模态融合诊断流程

### 3.1 完整数据流 (Step 1-10)

```
用户上传图像/文本
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: 请求验证层 (diagnosis_validator.py, 301行)                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • 文件格式校验 (JPEG/PNG/WEBP)                                          │ │
│ │ • Magic Number 校验 (防止伪装文件)                                       │ │
│ │ • XSS 攻击过滤 (文件名/内容净化)                                         │ │
│ │ • 文件大小限制 (≤10MB)                                                  │ │
│ │ • 并发限制检查 (RateLimiter.acquire(), 最大3并发)                        │ │
│ │ • GPU 显存检查 (使用率 <90%)                                             │ │
│ │ • Mock 模式切换 (环境变量 WHEATAGENT_MOCK_AI=true)                      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输入: UploadFile + Optional[Text]                                          │
│ 输出: Validated Image + Symptoms Text                                      │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2: 图像预处理 (image_preprocessor.py, 773行)                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • JPEG/PNG 解码 (PIL.Image.open())                                      │ │
│ │ • Letterbox 缩放 (保持宽高比, 填充至 640x640)                            │ │
│ │ • RGB/BGR 色彩空间转换                                                   │ │
│ │ • 归一化处理 (mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])       │ │
│ │ • Tensor 转换 (numpy array → torch.Tensor)                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输入: PIL.Image                                                            │
│ 输出: Preprocessed Tensor (640x640x3)                                      │
│ 性能: ~0.9ms (CPU), 可启用 GPU 加速                                        │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3: YOLOv8 视觉检测 (yolo_service.py, 538行)                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • FP16 半精度推理 (GPU可用时)                                            │ │
│ │ • 16类病害/虫害 ROI 检测                                                │ │
│ │ • 置信度过滤 (阈值=0.5)                                                 │ │
│ │ • NMS 非极大值抑制 (IoU=0.45)                                           │ │
│ │ • LRU 缓存查询 (maxsize=64, 相同图像复用)                                │ │
│ │ • 中英文类别映射 (Yellow Rust → 条锈病)                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输入: Preprocessed Tensor                                                 │
│ 输出: detections[] = [{bbox, class_name, confidence}, ...]                 │
│ 性能: GPU <50ms / CPU ~187ms (稳定态)                                      │
│ 检测类别: 条锈病/叶锈病/秆锈病/白粉病/赤霉病/纹枯病/根腐病/蚜虫等16类       │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 4: Qwen3-VL 语义分析 (qwen_service.py, 496行 + qwen/子目录)          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 【Loader】懒加载/预加载 (qwen_loader.py, 546行)                          │ │
│ │   ├─ 状态机: unloaded → loading → ready → error                         │ │
│ │   ├─ INT4 量化加载 (bitsandbytes, ~2.6GB显存)                           │ │
│ │   ├─ CPU Offload (显存不足时卸载至内存)                                   │ │
│ │   └─ Flash Attention 2 加速 (需 Ampere GPU)                              │ │
│ │                                                                         │ │
│ │ 【Preprocessor】输入预处理 (qwen_preprocessor.py, 151行)                 │ │
│ │   ├─ Prompt 模板组装 (system_base / system_thinking)                     │ │
│ │   ├─ Thinking 模式指令注入                                               │ │
│ │   └─ 图像归一化 + Tokenizer 编码                                         │ │
│ │                                                                         │ │
│ │ 【Inferencer】推理执行 (qwen_inferencer.py, 240行)                      │ │
│ │   ├─ 前向传播 (model.generate())                                         │ │
│ │   ├─ KV Cache 管理 (量化至4bit)                                          │ │
│ │   └─ 超时控制 (60s)                                                     │ │
│ │                                                                         │ │
│ │ 【Postprocessor】输出后处理 (qwen_postprocessor.py, 232行)              │ │
│ │   ├─ 结果解析 (JSON提取)                                                │ │
│ │   ├─ 置信度关键词匹配 (高度怀疑/很可能是/可能是/疑似/不确定)             │ │
│ │   ├─ 推理链提取 (Thinking模式)                                           │ │
│ │   └─ 错误码映射                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输入: Original Image + YOLO Detections + Symptoms Text                     │
│ 输出: textual_result = {diagnosis: {disease_name, confidence, description}, │
│                         reasoning_chain: [...], recommendations: [...]}   │
│ 性能: 首次推理 <35s (含懒加载), 后续推理 <30s                               │
│ 参数: max_new_tokens=384, temperature=0.1, top_p=0.85, do_sample=False    │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 5: KAD-Former 特征融合 (fusion_engine.py, 467行)                      │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 【DeepStack 多层特征注入】(deepstack_injection.py)                       │ │
│ │   ├─ 浅层特征注入 (纹理/边缘) → LLM Layer 4                             │ │
│ │   ├─ 中层特征注入 (部件/结构) → LLM Layer 16                            │ │
│ │   └─ 高层特征注入 (语义/物体) → LLM Layer 28                            │ │
│ │                                                                         │ │
│ │ 【SE 增强跨模态注意力】(cross_attention.py)                             │ │
│ │   ├─ Cross-Attention: 文本 Query 查询视觉 Key-Value                     │ │
│ │   ├─ SE Module: 动态加权关键文本特征                                     │ │
│ │   └─ 背景噪声抑制                                                       │ │
│ │                                                                         │ │
│ │ 【KAD 注意力机制】(kad_attention.py, 331行)                             │ │
│ │   ├─ 视觉注意力分支 (Visual Attention)                                   │ │
│ │   ├─ 知识注意力分支 (Knowledge Attention)                                │ │
│ │   └─ 双路融合 + Sigmoid 输出                                            │ │
│ │                                                                         │ │
│ │ 【置信度融合算法】                                                        │ │
│ │   ├─ 三模态完整: vision×0.6 + text×0.35 + knowledge×0.25               │ │
│ │   ├─ 双模态降级: 应用 degradation_factor=0.9                            │ │
│ │   └─ KAD增强: +sigmoid(fused_features).mean() × 0.15                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输入: visual_result, textual_result, knowledge_context                    │
│ 输出: FusionResult {confidence, visual_conf, textual_conf, knowledge_conf}│
│ 性能: <1ms (纯矩阵运算, 无神经网络前向传播)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 6: GraphRAG 知识增强 (graphrag_service.py, 569行)                    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • Neo4j 子图检索 (Cypher 查询)                                          │ │
│ │ • TransE 嵌入相似度计算                                                 │ │
│ │ • 实体检索 (disease/symptom/pest/treatment/growth_stage)                │ │
│ │ • 关系路径检索 (caused_by → treated_by → prevented_by)                  │ │
│ │ • 知识上下文构建 (citations[] 格式)                                      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输入: disease_name (来自 Step 3-5 融合结果)                                │
│ 输出: knowledge_context = {citations: [{entity_name, relation, tail, ...}]}│
│ 数据规模: 106 实体, 178 三元组, 15 种关系类型                               │
│ 连接: bolt://localhost:7687 (Neo4j)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 7: 结果组装 (FusionResult 构建)                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • confidences 数组构建 (多候选置信度排序)                                 │ │
│ │ • primary_confidence 提取 (排名第一候选)                                  │ │
│ │ • severity 计算 (low/medium/high 基于 confidence 阈值)                   │ │
│ │ • disease_info 补充 (从 disease_knowledge.py 内置知识库)                 │ │
│ │   ├─ symptoms (症状列表)                                                │ │
│ │   ├─ causes (病因列表)                                                  │ │
│ │   ├─ treatment (治疗方案)                                                │ │
│ │   ├─ medicines (用药建议)                                               │ │
│ │   └─ prevention (预防措施)                                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 输出: FusionResult (完整诊断结果对象)                                       │
│ 字段: disease_name, confidence, severity, symptoms, causes, treatment, ... │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 8: 持久化写入 (Database Persistence)                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • diagnoses 主表插入 (user_id, disease_id, primary_confidence, ...)     │ │
│ │ • diagnosis_confidences 子表批量插入 (CASCADE 删除)                      │ │
│ │ │   ├─ id, diagnosis_id (FK), disease_name, confidence, rank            │ │
│ │ │   └─ 复合索引: (diagnosis_id, confidence DESC)                        │ │
│ │ • image_metadata 表插入/去重 (SHA256 hash_value UNIQUE)                  │ │
│ │ • 事务保证 (ACID)                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 涉及表: diagnoses, diagnosis_confidences, image_metadata                   │
│ ORM: SQLAlchemy 2.0 async (aiomysql)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 9: 资源清理 (Resource Cleanup)                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ • 临时文件删除 (os.remove(temp_path))                                    │ │
│ │ • 限流许可释放 (RateLimiter.release())                                   │ │
│ │ • GPU 显存清理 (torch.cuda.empty_cache())                               │ │
│ │ • 数据库会话关闭 (await db.close())                                      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 保证: 无资源泄漏, 即使异常发生也能通过 try-finally 清理                     │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 10: SSE 流式输出 (sse_stream_manager.py, 352行)                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 【事件类型】                                                              │ │
│ │   ├─ ProgressEvent  (stage, progress%, message)                          │ │
│ │   ├─ LogEvent       (level, message, stage)                              │ │
│ │   ├─ HeartbeatEvent (timestamp, 间隔15s)                                 │ │
│ │   └─ CompleteEvent  (final_result, status=success/error)                 │ │
│ │                                                                         │ │
│ │ 【SSE 协议特性】                                                          │ │
│ │   ├─ event: {type}\ndata: {json}\n\n (标准格式)                         │ │
│ │   ├─ 背压控制 (asyncio.Queue, maxsize=100)                               │ │
│ │   ├─ 超时保护 (120s 总超时)                                              │ │
│ │   ├─ 断线优雅关闭 (GeneratorExit 处理)                                    │ │
│ │   └─ 心跳保活 (防止代理/负载均衡器超时断开)                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ 性能: 首事件延迟 0.01ms (目标<500ms, 达标50,000倍!)                        │
│ 格式化: ProgressEvent 6.19μs, HeartbeatEvent 4.28μs                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 各阶段详细说明

| 步骤 | 阶段名称 | 输入数据 | 输出数据 | 关键技术 | 耗时(CPU) | 耗时(GPU预估) |
|------|---------|---------|---------|---------|-----------|--------------|
| **1** | 请求验证 | UploadFile+Text | Validated Input | Magic Number/XSS/RateLimit | <1ms | <1ms |
| **2** | 图像预处理 | PIL.Image | Tensor(640x640x3) | Letterbox/Normalize | ~0.9ms | <0.5ms |
| **3** | YOLOv8检测 | Tensor | detections[] | FP16/NMS/LRU Cache | ~187ms | <50ms |
| **4** | Qwen3-VL分析 | Image+Detections+Text | textual_result | INT4/FlashAttn/KVCache | N/A | <30s |
| **5** | KAD-Former融合 | 3路特征 | FusionResult | CrossAttention/SE/Degradation | <1ms | <1ms |
| **6** | GraphRAG增强 | disease_name | knowledge_context | Cypher/TransE | ~50ms | ~30ms |
| **7** | 结果组装 | 所有中间结果 | Final FusionResult | ConfidenceCalc/Severity | <1ms | <1ms |
| **8** | 持久化写入 | Final Result | DB Rows | SQLAlchemy Async | ~10ms | ~10ms |
| **9** | 资源清理 | - | - | try-finally/GC | <1ms | <1ms |
| **10** | SSE流输出 | Final Result | SSE Events | asyncio.Queue/Heartbeat | 0.01ms* | 0.01ms* |

> *注: SSE首事件延迟, 非总耗时

### 3.3 Fusion Service Facade 内部组件关系

```
MultimodalFusionService (Facade Pattern)
│
├── FeatureExtractor (特征提取器, 424行)
│   │
│   ├── extract_visual(image) → YOLOv8 ROI 特征
│   │   输出: {
│   │     "detections": [{"bbox": [x1,y1,x2,y2], "class_name": "条锈病", "confidence": 0.92}],
│   │     "visual_features": tensor([B, N_v, 768])
│   │   }
│   │
│   ├── extract_textual(image, symptoms) → Qwen3-VL 语义特征
│   │   输出: {
│   │     "diagnosis": {"disease_name": "条锈病", "confidence": 0.88, "description": "..."},
│   │     "reasoning_chain": ["观察到叶片上有黄色条纹状病斑...", "初步判断为条锈病..."],
│   │     "textual_features": tensor([B, N_t, 2560])
│   │   }
│   │
│   └── extract_knowledge(disease_name) → GraphRAG 知识特征
│       输出: {
│         "citations": [
│           {"entity_name": "条锈病", "relation": "caused_by", "tail": "条形柄锈菌"},
│           {"entity_name": "条锈病", "relation": "treated_by", "tail": "三唑酮"}
│         ],
│         "knowledge_embeddings": tensor([B, N_k, 256])
│       }
│
├── FusionEngine (KAD-Former 融合引擎, 467行)
│   │
│   ├── cross_attention(visual, text, knowledge) → KAD 注意力加权
│   │   算法: Knowledge-Aware Dual-modal Transformer
│   │   输出: fused_features tensor([B, N_v, 768])
│   │
│   ├── feature_fusion(vision_conf, text_conf, knowledge_conf) → 多模态置信度融合
│   │   权重: vision=0.6, text=0.35, knowledge=0.25 (ai_config.py)
│   │   降级: 双模态 ×0.9, 单模态 ×0.81
│   │   增强: KAD boost = sigmoid(mean(fused)) × 0.15
│   │   输出: final_confidence float [0, 1]
│   │
│   └── decision_fusion(all_results) → 最终诊断决策
│       输出: FusionResult dataclass (55个字段)
│
└── ResultAnnotator (结果标注器, 269行)
    │
    ├── annotate_roi(image, detections) → ROI 区域标注图
    │   输出: annotated_image (Base64 encoded JPEG)
    │
    ├── encode_base64(image) → Base64 图像编码
    │   格式: data:image/jpeg;base64,{base64_string}
    │
    ├── calibrate_confidence(raw_confidence) → 置信度校准
    │   算法: Platt Scaling / Temperature Scaling
    │
    └── cache_async(result, cache_key) → 异步缓存写入
        存储: Redis Hash (TTL=24h)
        键名: inference:{md5(image_hash+symptoms)}
```

### 3.4 SSE 流式事件协议

```typescript
// 前端 EventSource 消费示例 (TypeScript)
const eventSource = new EventSource('/api/v1/diagnosis/fusion/stream?image_url=...');

// 1. 进度更新事件
eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  // { stage: "yolo_detection", progress: 60, message: "正在执行YOLOv8视觉检测..." }
  updateProgressBar(data.progress);
  updateStatusText(data.message);
});

// 2. 日志事件
eventSource.addEventListener('log', (e) => {
  const data = JSON.parse(e.data);
  // { level: "info", message: "检测到3个病害区域", stage: "yolo_detection" }
  appendToConsole(data);
});

// 3. 心跳保活 (每15秒)
eventSource.addEventListener('heartbeat', (e) => {
  // { timestamp: 1712345678.901 }
  // 用于检测连接是否存活, 无需特殊处理
});

// 4. 完成事件
eventSource.addEventListener('complete', (e) => {
  const result = JSON.parse(e.data);
  // { status: "success", data: FusionResult }
  displayDiagnosisResult(result.data);
  eventSource.close(); // 关闭连接
});

// 5. 错误事件
eventSource.addEventListener('error', (e) => {
  const error = JSON.parse(e.data);
  // { code: "DIAG_005", message: "Qwen模型加载失败", stage: "qwen_analysis" }
  showErrorNotification(error);
});
```

---

## 第4章: AI 模型体系

### 4.1 YOLOv8s 视觉检测模型

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOLOv8s 模型规格卡片                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【基础信息】                                                    │
│  ├── 模型名称: YOLOv8s (Ultralytics 8.4.13)                    │
│  ├── 模型大小: ~50MB (best.pt)                                  │
│  ├── 参数量: ~11.2M                                             │
│  ├── FLOPs: 28.6G                                               │
│  └── 输入尺寸: 640×640×3 (RGB)                                  │
│                                                                 │
│  【训练数据集】                                                  │
│  ├── 数据来源: 小麦病害公开数据集 + 自采数据                     │
│  ├── 训练阶段: phase1_warmup (迁移学习预热)                      │
│  ├── 类别数: 16 类 (15种病害/虫害 + 1种健康)                    │
│  └── 数据增强: Mosaic/MixUp/RandomAffine                        │
│                                                                 │
│  【推理配置】                                                    │
│  ├── 精度模式: FP16 半精度 (GPU) / FP32 (CPU)                   │
│  ├── 置信度阈值: 0.5 (ai_config.YOLO_CONFIDENCE_THRESHOLD)      │
│  ├── IoU阈值: 0.45 (NMS)                                        │
│  ├── 最大检测数: 100 (YOLO_MAX_DETECTIONS)                      │
│  └── LRU缓存: 64条 (相同图像复用检测结果)                        │
│                                                                 │
│  【性能指标】                                                    │
│  ├── mAP@50: 95.39%                                             │
│  ├── mAP@50-95: 90.02%                                          │
│  ├── 推理速度(GPU): <50ms (FP16)                                │
│  ├── 推理速度(CPU): ~187ms (稳定态)                             │
│  └── 首次推理: ~314ms (含模型初始化)                             │
│                                                                 │
│  【支持的病害类别 (16类)】                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 英文名          │ 中文名      │ 类型                     │   │
│  ├─────────────────┼─────────────┼─────────────────────────┤   │
│  │ Yellow Rust     │ 条锈病      │ 真菌性病害               │   │
│  │ Brown Rust      │ 叶锈病      │ 真菌性病害               │   │
│  │ Black Rust      │ 秆锈病      │ 真菌性病害               │   │
│  │ Mildew          │ 白粉病      │ 真菌性病害               │   │
│  │ Fusarium H.Blight│ 赤霉病     │ 真菌性病害               │   │
│  │ Septoria        │ 壳针孢叶斑病 │ 真菌性病害               │   │
│  │ Tan spot        │ 褐斑病      │ 真菌性病害               │   │
│  │ Leaf Blight     │ 叶枯病      │ 真菌性病害               │   │
│  │ Blast           │ 稻瘟病      │ 真菌性病害               │   │
│  │ Aphid           │ 蚜虫        │ 虫害                     │   │
│  │ Mite            │ 螨虫        │ 虫害                     │   │
│  │ Stem fly        │ 茎蝇        │ 虫害                     │   │
│  │ Common Root Rot │ 根腐病      │ 真菌性病害               │   │
│  │ Smut            │ 黑粉病      │ 真菌性病害               │   │
│  │ Armyworm        │ 粘虫        │ 虫害                     │   │
│  │ Healthy         │ 健康        │ 正常样本                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Qwen3-VL-2B 多模态理解模型

```
┌─────────────────────────────────────────────────────────────────┐
│                 Qwen3-VL-2B-Instruct 规格卡片                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【基础信息】                                                    │
│  ├── 模型名称: Qwen3-VL-2B-Instruct (通义千问视觉语言模型)      │
│  ├── 参数量: 2B (20亿)                                          │
│  ├── 架构: Transformer Decoder-only + ViT 视觉编码器            │
│  ├── 上下文长度: 512 tokens (QWEN_MAX_LENGTH)                   │
│  └── 模型路径: models/Qwen3-VL-2B-Instruct/                    │
│                                                                 │
│  【量化配置】(QUANTIZATION_CONFIG)                               │
│  ├── 量化方式: INT4 (bitsandbytes)                              │
│  ├── 量化类型: nf4 (NormalFloat 4-bit)                          │
│  ├── 计算精度: FP16 (bnb_4bit_compute_dtype)                    │
│  ├── 双重量化: True (bnb_4bit_use_double_quant)                 │
│  └── 显存占用: ~2.6GB (原始 ~9.8GB, 降低 73.5%)                 │
│                                                                 │
│  【推理参数】(INFERENCE_PARAMS)                                  │
│  ├── max_new_tokens: 384 (最大生成长度)                         │
│  ├── temperature_diagnosis: 0.1 (诊断模式, 低随机性)            │
│  ├── temperature_thinking: 0.5 (思考模式, 中等随机性)           │
│  ├── top_p: 0.85 (核采样概率)                                   │
│  ├── do_sample: False (贪婪解码, 提高确定性)                    │
│  ├── repetition_penalty: 1.1 (防重复惩罚)                       │
│  ├── max_tokens_thinking: 768 (思考模式最大长度)                │
│  └── max_tokens_normal: 384 (普通模式最大长度)                  │
│                                                                 │
│  【高级优化】                                                    │
│  ├── Flash Attention 2: True (需要 Ampere GPU + flash-attn包)  │
│  ├── Torch Compile: True (reduce-overhead 模式)                 │
│  ├── KV Cache 量化: True (4-bit, group_size=64)                │
│  ├── CPU Offload: True (显存不足时自动卸载)                     │
│  └── 懒加载: True (首次请求时才加载模型)                         │
│                                                                 │
│  【状态机生命周期】(ModelState Enum)                             │
│                                                                 │
│     unloaded ──→ loading ──→ ready                              │
│        │             │          │                               │
│        │             └──→ error ─┘                              │
│        │                     │                                 │
│        └─────────────────────┘ (可重试)                         │
│                                                                 │
│  【状态转换详解】                                                │
│  ┌──────┬───────────┬────────────────┬─────────────────────────┐│
│  │状态  │   含义    │  触发事件      │  行为                   ││
│  ├──────┼───────────┼────────────────┼─────────────────────────┤│
│  │UNLOADED│未加载  │初始状态/卸载后  │拒绝推理请求            ││
│  │      │          │                │                         ││
│  │LOADING │正在加载 │ensure_loaded() │排队等待,并发安全       ││
│  │      │          │首次调用         │(asyncio.Lock)           ││
│  │      │          │                │                         ││
│  │READY  │已就绪   │加载成功        │正常响应推理请求        ││
│  │      │          │预热完成        │                         ││
│  │ERROR  │加载失败 │异常/OOM/超时   │记录错误信息            ││
│  │      │          │                │允许从 UNLOADED 重试     ││
│  └──────┴───────────┴────────────────┴─────────────────────────┘│
│                                                                 │
│  【错误恢复机制】                                                │
│  ├── ERROR → UNLOADED: 调用 reset() 或自动重试                  │
│  ├── 超时保护: 单次加载超时 300s (可配置)                       │
│  ├── 内存不足: 自动触发 CPU Offload (如启用)                    │
│  └── 并发安全: asyncio.Lock 防止重复加载                        │
│                                                                 │
│  【典型生命周期示例】                                            │
│  服务启动 → UNLOADED (懒加载模式)                                │
│     ↓ 首次诊断请求                                               │
│  ensure_loaded() → LOADING (asyncio.Lock 加锁)                 │
│     ↓ INT4量化 + FlashAttention 初始化                          │
│  模型就绪 → READY (解锁,返回模型实例)                           │
│     ↓ 正常推理...                                               │
│  [显存不足] → 自动 CPU Offload → 继续 READY                     │
│     ↓ [严重错误]                                                 │
│  异常捕获 → ERROR (记录 _last_error)                            │
│     ↓ 下次调用 ensure_loaded()                                  │
│  重置为 UNLOADED → 重新 LOADING → READY                        │
│                                                                 │

│  【Prompt 模板系统】(PROMPT_TEMPLATES)                          │
│  ├── system_base: 专业小麦病害诊断专家角色定义                  │
│  ├── system_thinking: 推理模式指令 (逐步推理)                   │
│  ├── multimodal_query: 图像+文本联合查询模板                    │
│  ├── image_query: 纯图像查询模板                                │
│  ├── text_query: 纯文本症状查询模板                             │
│  ├── graphrag_context: GraphRAG 知识注入模板                    │
│  └── thinking_suffix: 思考模式后缀提示                          │
│                                                                 │
│  【置信度关键词映射】(CONFIDENCE_KEYWORDS)                      │
│  ├── "高度怀疑" → 0.95                                         │
│  ├── "很可能是" → 0.85                                         │
│  ├── "可能是" → 0.75                                           │
│  ├── "疑似" → 0.65                                            │
│  └── "不确定" → 0.50                                           │
│                                                                 │
│  【性能预期】                                                    │
│  ├── 首次推理 (含懒加载): <35s                                  │
│  ├── 后续推理 (模型已加载): <25-30s                             │
│  └── Thinking模式: +5-10s (生成更长推理链)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 KAD-Former 特征融合引擎 (自研)

```
┌─────────────────────────────────────────────────────────────────┐
│              KAD-Former 架构图 (Knowledge-Aware Dual former)     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Visual Features          Knowledge Embeddings                │
│   [B, N_v, 768]            [B, N_k, 256]                       │
│        │                         │                             │
│        ▼                         │                             │
│   ┌─────────┐                   │                             │
│   │ Visual  │                   │                             │
│   │Attention│                   │                             │
│   │(Multi-  │                   │                             │
│   │ Head)   │                   │                             │
│   └────┬────┘                   │                             │
│        │                         │                             │
│        ▼                         ▼                             │
│   ┌─────────────────────────────────────────┐                 │
│   │        Cross-Modal Attention            │                 │
│   │  ┌─────────────────────────────────┐   │                 │
│   │  │ Query: Text Features [B,N_t,2560]│   │                 │
│   │  │ Key: Visual Features [B,N_v,768]│   │                 │
│   │  │ Value: Visual Features         │   │                 │
│   │  └─────────────────────────────────┘   │                 │
│   │                                         │                 │
│   │  ┌─────────────────────────────────┐   │                 │
│   │  │ SE Block (Squeeze-Excitation)   │   │                 │
│   │  │ • Global Avg Pool → Excitation  │   │                 │
│   │  │ • Channel-wise Recalibration    │   │                 │
│   │  └─────────────────────────────────┘   │                 │
│   └────────────────────┬────────────────┘                 │
│                        │                                  │
│                        ▼                                  │
│              ┌─────────────────┐                          │
│              │ Feature Fusion  │                          │
│              │ (Concat + MLP)  │                          │
│              └────────┬────────┘                          │
│                       │                                   │
│                       ▼                                   │
│              ┌─────────────────┐                          │
│              │  Sigmoid Output │ ← Knowledge Boost (+15%) │
│              │  [B, N_v, 768]  │                          │
│              └─────────────────┘                          │
│                                                                 │
│   【融合算法伪代码】                                             │
│                                                                 │
│   def fuse_features(visual, textual, knowledge):               │
│       # 1. 基础加权融合                                          │
│       weights = {vision: 0.6, text: 0.35, knowledge: 0.25}    │
│       base_conf = weighted_avg(visual.conf, textual.conf,      │
│                                knowledge.conf, weights)        │
│                                                                 │
│       # 2. 降级因子 (模态不完整时降低置信度)                     │
│       n_modals = count_available(visual, textual, knowledge)  │
│       if n_modals < 3:                                         │
│           base_conf *= (0.9 ** (3 - n_modals))                │
│                                                                 │
│       # 3. KAD-Former 深度融合增强                               │
│       if kad_former is not None:                               │
│           fused_tensor = kad_former(visual_feat, text_feat,    │
│                                      knowledge_emb)            │
│           boost = sigmoid(fused_tensor.mean()).item() * 0.15   │
│           final_conf = min(1.0, base_conf + boost)             │
│                                                                 │
│       return final_conf                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 GraphRAG 知识图谱增强

```
┌─────────────────────────────────────────────────────────────────┐
│                   GraphRAG 知识检索架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【图数据库】Neo4j 5.x                                          │
│  ├── 连接协议: bolt://localhost:7687                           │
│  ├── 用户名: neo4j                                             │
│  ├── 数据库名: neo4j                                           │
│  └── 连接池: 最大 50 连接                                       │
│                                                                 │
│  【知识规模】                                                    │
│  ├── 实体总数: 106 个                                           │
│  ├── 三元组总数: 178 条                                          │
│  ├── 关系类型: 15 种                                            │
│  └── 实体类型: 5 类                                             │
│                                                                 │
│  【实体类型】                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 类型           │ 示例                    │ 属性          │   │
│  ├────────────────┼─────────────────────────┼──────────────┤   │
│  │ disease        │ 条锈病, 白粉病, 赤霉病   │ name, severity│   │
│  │ symptom        │ 黄色条纹, 白色粉霉斑     │ description  │   │
│  │ pest           │ 蚜虫, 螨虫, 吸浆虫       │ name, lifecycle│   │
│  │ treatment      │ 三唑酮, 戊唑醇, 百菌清   │ name, dosage  │   │
│  │ growth_stage   │ 苗期, 拔节期, 抽穗期     │ name, susceptibility│   │
│  └────────────────┴─────────────────────────┴──────────────┘   │
│                                                                 │
│  【关系类型示例】                                                │
│  ├── caused_by: 条锈病 --caused_by--> 条形柄锈菌                │
│  ├── treated_by: 条锈病 --treated_by--> 三唑酮                  │
│  ├── has_symptom: 条锈病 --has_symptom--> 黄色条纹              │
│  ├── prevented_by: 白粉病 --prevented_by--> 轮作                │
│  └── occurs_at: 赤霉病 --occurs_at--> 抽穗期                    │
│                                                                 │
│  【检索模式】                                                    │
│  1. 实体检索: MATCH (d:Disease {name: $name}) RETURN d         │
│  2. 关系检索: MATCH ()-[r]->() WHERE type(r)=$rel RETURN r     │
│  3. 路径检索: shortestPath((start)-[*..3]-(end))               │
│  4. 子图检索: MATCH p=(d)-[:*]->(related) WHERE d.name=$name   │
│                                                                 │
│  【嵌入计算】TransE                                             │
│  ├── 维度: 256 dim                                             │
│  ├── 相似度度量: 余弦相似度                                      │
│  └── 用途: 实体对齐 + 关系预测                                   │
│                                                                 │
│  【输出格式】citations[]                                        │
│  [                                                                │
│    {                                                              │
│      "entity_name": "条锈病",                                    │
│      "relation": "treated_by",                                   │
│      "tail": "三唑酮",                                           │
│      "source": "neo4j",                                         │
│      "confidence": 0.92                                          │
│    }                                                             │
│  ]                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 DeepStack 多层特征注入 (V2.0 增强)

```
┌─────────────────────────────────────────────────────────────────┐
│              DeepStack 多层特征注入架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ViT Encoder (Vision Transformer)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Layer 0-3:   浅层特征 (纹理/边缘/颜色)  → dim=1024      │   │
│  │ Layer 4-15:  中层特征 (部件/形状/结构)  → dim=1024      │   │
│  │ Layer 16-27: 高层特征 (语义/物体/场景)  → dim=1024      │   │
│  └─────────────────────────────────────────────────────────┘   │
│        │              │                │                       │
│        ▼              ▼                ▼                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │Linear Proj│  │Linear Proj│  │Identity │                     │
│  │1024→4096 │  │2048→4096 │  │(pass)   │                     │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘                     │
│        │              │              │                          │
│        ▼              ▼              ▼                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM Layers (Qwen3-VL-2B)                     │   │
│  │                                                          │   │
│  │  Layer 4  ◄──── 注入浅层特征 (增强纹理感知)               │   │
│  │     │                                                     │   │
│  │  Layer 16 ◄──── 注入中层特征 (增强形状识别)               │   │
│  │     │                                                     │   │
│  │  Layer 28 ◄──── 注入高层特征 (增强语义理解)               │   │
│  │     │                                                     │   │
│  │  Layer 31 → Output (诊断结果生成)                         │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  【环境数据嵌入分支】(environment_embedding.py)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  温度编码 ──┐                                            │   │
│  │  湿度编码 ──┼──→ MLP → Token Dim (768)                   │   │
│  │  位置编码 ──┤                                            │   │
│  │  生长阶段编码┘                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  【融合权重更新】(V2.0 新增 environment 权重)                   │
│  FUSION_WEIGHTS = {                                            │
│    "vision": 0.6,      # 视觉检测权重 (原0.4↑)                │
│    "text": 0.4,        # 文本理解权重 (不变)                   │
│    "knowledge": 0.3,   # 知识增强权重 (原0.2↑)                 │
│    "environment": 0.1  # 环境数据权重 (新增)                   │
│  }                                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.6 模型优化配置总表 (ai_config.py 完整参数)

| 配置分类 | 参数名 | 默认值 | 说明 |
|---------|--------|-------|------|
| **模型路径** | `QWEN_MODEL_PATH` | `models/Qwen3-VL-2B-Instruct` | Qwen模型目录 |
| | `YOLO_MODEL_PATH` | `models/wheat_disease_v10_yolov8s/.../best.pt` | YOLO训练模型 |
| **YOLO配置** | `YOLO_CONFIDENCE_THRESHOLD` | 0.5 | 检测置信度阈值 |
| | `YOLO_IOU_THRESHOLD` | 0.45 | NMS IoU阈值 |
| | `YOLO_MAX_DETECTIONS` | 100 | 最大检测框数量 |
| **Qwen推理** | `QWEN_MAX_NEW_TOKENS` | 384 | 最大生成长度 |
| | `QWEN_TEMPERATURE_DIAGNOSIS` | 0.1 | 诊断温度(低随机性) |
| | `QWEN_TOP_P` | 0.85 | 核采样概率 |
| | `QWEN_DO_SAMPLE` | False | 是否采样(贪婪解码) |
| | `QWEN_REPETITION_PENALTY` | 1.1 | 防重复惩罚 |
| **高级特性** | `ENABLE_KAD_FORMER` | True | KAD-Former融合 |
| | `ENABLE_GRAPH_RAG` | True | GraphRAG增强 |
| | `ENABLE_THINKING` | False | Thinking模式(默认关) |
| | `ENABLE_DEEPSTACK` | True | DeepStack注入 |
| **模型优化** | `ENABLE_FLASH_ATTENTION` | True | Flash Attn 2加速 |
| | `KV_CACHE_QUANTIZATION` | True | KV Cache 4bit量化 |
| | `TORCH_COMPILE_ENABLE` | True | torch.compile优化 |
| **CUDA内存** | `CUDA_MEMORY_ALLOCATOR` | "pytorch" | 内存分配器类型 |
| | `CUDA_MEMORY_WARNING_THRESHOLD` | 0.85 | 显存警告阈值 |
| | `CUDA_MEMORY_CRITICAL_THRESHOLD` | 0.95 | 显存临界阈值 |
| **推理队列** | `INFERENCE_QUEUE_MAX_CONCURRENT` | 2 | 最大并发推理数 |
| | `INFERENCE_QUEUE_MAX_SIZE` | 100 | 队列容量 |
| | `INFERENCE_QUEUE_TIMEOUT` | 120 | 超时时间(秒) |
| **图像预处理** | `IMAGE_PREPROCESS_TARGET_SIZE` | (640, 640) | 目标尺寸 |
| | `IMAGE_PREPROCESS_NORMALIZE_MEAN` | (0.485, 0.456, 0.406) | 归一化均值 |
| | `IMAGE_PREPROCESS_NORMALIZE_STD` | (0.229, 0.224, 0.225) | 归一化标准差 |
| **动态批处理** | `DYNAMIC_BATCH_ENABLE` | True | 启用动态批处理 |
| | `DYNAMIC_BATCH_MAX_SIZE` | 16 | 最大批处理大小 |
| | `DYNAMIC_BATCH_MAX_WAIT_MS` | 50 | 最大等待时间 |
| **融合权重** | `FUSION_WEIGHTS.vision` | 0.6 | 视觉权重 |
| | `FUSION_WEIGHTS.text` | 0.4 | 文本权重 |
| | `FUSION_WEIGHTS.knowledge` | 0.3 | 知识权重 |

---

## 第5章: 安全机制

### 5.1 认证体系 (JWT 双Token)

```
┌─────────────────────────────────────────────────────────────────┐
│                    JWT 双Token认证流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户登录                                                        │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐                                               │
│  │ 验证凭据     │  username + password                          │
│  │ bcrypt校验   │  (72字节限制, 自动截断)                       │
│  └──────┬──────┘                                               │
│         │                                                      │
│         ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Token 生成                             │   │
│  │                                                          │   │
│  │  Access Token (短期):                                    │   │
│  │  ├── 有效期: 30分钟 (ACCESS_TOKEN_EXPIRE_MINUTES)       │   │
│  │  ├── 用途: API请求认证                                   │   │
│  │  ├── 存储位置: localStorage (前端) / Header (后端)       │   │
│  │  └── Payload: {sub: username, exp: timestamp}           │   │
│  │                                                          │   │
│  │  Refresh Token (长期):                                   │   │
│  │  ├── 有效期: 7天 (REFRESH_TOKEN_EXPIRE_DAYS)             │   │
│  │  ├── 用途: 刷新Access Token                              │   │
│  │  ├── 存储位置: HttpOnly Cookie (推荐)                    │   │
│  │  └── Payload: {sub: username, exp: timestamp, type: refresh}│  │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                      │
│         ▼                                                      │
│  返回 {access_token, refresh_token, token_type: "bearer"}       │
│                                                                 │
│  ═══════════════════════════════════════════════════════════    │
│                                                                 │
│  后续API请求                                                     │
│      │                                                          │
│      ▼                                                          │
│  Header: Authorization: Bearer {access_token}                   │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Token 验证流程                            │   │
│  │                                                          │   │
│  │  1. decode_access_token() → 解码JWT                      │   │
│  │  2. 检查过期时间 (exp)                                    │   │
│  │  3. is_token_blacklisted() → Redis黑名单检查              │   │
│  │  4. get_current_user() → 数据库查询用户                   │   │
│  │  5. 检查 is_active 状态                                    │   │
│  │  6. 返回 User 对象给路由处理函数                           │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Token失效处理:                                                  │
│  ├── Access Token过期 → 使用Refresh Token刷新                  │
│  ├── Refresh Token过期 → 重新登录                               │
│  └── Token被撤销(登出) → 加入Redis黑名单(TTL=剩余有效期)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**JWT 配置参数**:

| 参数 | 值 | 说明 |
|------|-----|------|
| 算法 | HS256 | HMAC-SHA256签名 |
| Secret Key | 环境变量 `JWT_SECRET_KEY` | 生产环境必填, 开发环境自动生成 |
| Access Token有效期 | 30分钟 | 短期有效, 降低泄露风险 |
| Refresh Token有效期 | 7天 | 长期有效, 支持免登体验 |
| 黑名单前缀 | `token:blacklist:` | Redis Key前缀 |
| OAuth2 Scheme | Bearer Token | 标准HTTP认证方案 |

### 5.2 授权体系 (RBAC 角色)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RBAC 角色权限矩阵                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┬─────────────────────────────────────────┐  │
│  │   功能模块      │  farmer (农户) │ technician (农技员) │ admin (管理员) │  │
│  ├────────────────┼───────────────┼──────────────────┼───────────────┤  │
│  │ 图像诊断       │      ✓        │        ✓         │       ✓       │  │
│  │ 文本诊断       │      ✓        │        ✓         │       ✓       │  │
│  │ 融合诊断(SSE)  │      ✓        │        ✓         │       ✓       │  │
│  │ 查看历史记录   │      ✓(own)   │        ✓(all)    │       ✓       │  │
│  │ 知识库浏览     │      ✓        │        ✓         │       ✓       │  │
│  │ 知识库管理     │      ✗        │        ✓         │       ✓       │  │
│  │ 报告生成       │      ✓        │        ✓         │       ✓       │  │
│  │ 用户管理       │      ✗        │        ✗         │       ✓       │  │
│  │ AI模型预热     │      ✗        │        ✗         │       ✓       │  │
│  │ 缓存管理       │      ✗        │        ✗         │       ✓       │  │
│  │ 系统监控       │      ✗        │        ✗         │       ✓       │  │
│  │ 审计日志查看   │      ✗        │        ✗         │       ✓       │  │
│  └────────────────┴───────────────┴──────────────────┴───────────────┘  │
│                                                                 │
│  【权限实现方式】                                                │
│  ├── 依赖注入: Depends(get_current_user)                        │
│  ├── 角色检查: require_admin() → HTTP 403 if role != "admin"    │
│  ├── 数据隔离: farmer只能查看 own user_id 的诊断记录             │
│  └── 路由装饰器: @router.post(..., dependencies=[Depends(require_admin)]) │
│                                                                 │
│  【用户角色字段】                                                │
│  └── users.role: Enum('farmer', 'technician', 'admin')         │
│      默认值: 'farmer' (新注册用户默认为农户角色)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 防护体系 (XSS/CSRF/CORS/RateLimit)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web 安全防护层级                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 中间件链 (main.py L158-237)                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [1] GZipMiddleware (minimum_size=1000)                   │   │
│  │     → 响应压缩, 减少带宽占用                              │   │
│  │                                                         │   │
│  │ [2] CORSMiddleware                                      │   │
│  │     → 允许 origins: localhost:3000,5173,8080            │   │
│  │     → allow_credentials: true                           │   │
│  │     → max_age: 600s (预检缓存10分钟)                    │   │
│  │                                                         │   │
│  │ [3] request_id_middleware                                │   │
│  │     → X-Request-ID 追踪头 (请求链路追踪)                 │   │
│  │                                                         │   │
│  │ [4] add_security_headers                                │   │
│  │     → 完整安全头集合 (见下文详述)                         │   │
│  │                                                         │   │
│  │ [5] retry_middleware                                    │   │
│  │     → 自动重试3次, 指数退避策略                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 2: 安全响应头 (Security Headers)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ X-Content-Type-Options: nosniff                         │   │
│  │   → 防止MIME嗅探攻击                                     │   │
│  │                                                         │   │
│  │ X-Frame-Options: DENY                                   │   │
│  │   → 防止点击劫持 (Clickjacking)                          │   │
│  │                                                         │   │
│  │ X-XSS-Protection: 1; mode=block                         │   │
│  │   → 浏览器内置XSS过滤器 (虽然现代浏览器已弃用)           │   │
│  │                                                         │   │
│  │ Strict-Transport-Security: max-age=31536000; includeSubDomains│
│  │   → 强制HTTPS (仅生产环境)                               │   │
│  │                                                         │   │
│  │ Content-Security-Policy:                                 │   │
│  │   default-src 'self'; script-src 'self' 'unsafe-inline'; │
│  │   style-src 'self' 'unsafe-inline'; img-src 'self' data:;│
│  │   font-src 'self'; connect-src 'self'                    │   │
│  │   → 防止XSS和数据注入攻击                                 │   │
│  │                                                         │   │
│  │ Referrer-Policy: strict-origin-when-cross-origin         │   │
│  │   → 控制Referer头泄露                                    │   │
│  │                                                         │   │
│  │ Permissions-Policy: camera=(), microphone=(),            │   │
│  │   geolocation=(), payment=()                             │   │
│  │   → 禁用敏感API权限                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 3: XSS 防护 (xss_protection.py, 266行)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ sanitize_response(response_data)                         │   │
│  │   → HTML实体转义 (<, >, &, ", ')                         │   │
│  │   → JavaScript关键字过滤 (script, javascript:, vbscript:)│   │
│  │   → CSS表达式过滤 (expression(), url(javascript:))       │   │
│  │   → 事件属性过滤 (onclick, onerror, onload...)           │   │
│  │                                                         │   │
│  │ validate_username(username)                              │   │
│  │   → 长度限制 (3-50字符)                                  │   │
│  │   → 字符白名单 (字母数字+中文+_-.)                      │   │
│  │   → 特殊序列拒绝 (../, ./, \0)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 4: CSRF 防护                                            │
│  ├── SameSite Cookie: Strict (防止跨站请求伪造)               │
│  ├── Origin头验证 (CORS白名单)                                │
│  └── 自定义Header验证 (可选: X-CSRF-Token)                   │
│                                                                 │
│  Layer 5: Rate Limiting (SlowAPI + RateLimiter)               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 全局限流: 60 requests/minute                             │   │
│  │ 诊断接口: 10 requests/minute                             │   │
│  │ 上传接口: 20 requests/minute                             │   │
│  │ 注册接口: 3 requests/minute (防暴力注册)                 │   │
│  │ 并发限制: 3 concurrent diagnoses (令牌桶算法)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 6: 文件上传安全 (upload.py + file_validator.py)        │
│  ├── MIME类型白名单: image/jpeg, image/png, image/webp        │
│  ├── Magic Number校验 (防止扩展名伪装)                        │
│  ├── 文件大小限制: ≤10MB                                      │
│  ├── UUID重命名 (防止路径遍历和猜测)                          │
│  └── 病毒扫描接口预留 (可集成ClamAV)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 审计体系 (AuditLog 完整记录)

```
┌─────────────────────────────────────────────────────────────────┐
│                    操作审计日志体系                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【审计日志模型】(audit.py, 214行)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Table: audit_logs                                        │   │
│  │                                                         │   │
│  │ id              Integer PK                              │   │
│  │ user_id         Integer FK → users.id                   │   │
│  │ action          Enum (14种操作类型)                      │   │
│  │ resource_type   String (资源类型: diagnosis/user/...)   │   │
│  │ resource_id     String (资源ID)                          │   │
│  │ details         JSON (操作详情)                          │   │
│  │ ip_address      String (客户端IP)                        │   │
│  │ user_agent      String (浏览器/客户端信息)               │   │
│  │ created_at      DateTime (操作时间戳)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  【支持的操作类型 (14种)】                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 用户相关:                                                │   │
│  │   USER_REGISTER, USER_LOGIN, USER_LOGOUT,                │   │
│  │   PASSWORD_CHANGE, PASSWORD_RESET                       │   │
│  │                                                         │   │
│  │ 诊断相关:                                                │   │
│  │   DIAGNOSIS_CREATE, DIAGNOSIS_VIEW, DIAGNOSIS_DELETE    │   │
│  │                                                         │   │
│  │ 系统相关:                                                │   │
│  │   MODEL_PRELOAD, CACHE_CLEAR, ADMIN_ACTION,              │   │
│  │   FILE_UPLOAD, KNOWLEDGE_UPDATE, SESSION_REVOKE          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  【辅助审计表】                                                  │
│  ├── login_attempts: 登录尝试记录 (防暴力破解)                  │
│  ├── refresh_tokens: 刷新令牌记录 (可撤销)                      │
│  ├── password_reset_tokens: 密码重置令牌                        │
│  └── user_sessions: 会话管理 (支持多设备踢出)                   │
│                                                                 │
│  【审计查询API】                                                 │
│  GET /api/v1/logs/audit?user_id={}&action={}&start_date={}&end_date={}│
│  → 仅 admin 角色可访问                                          │
│  → 支持分页 (PaginationParams)                                  │
│  → 支持按时间范围/操作类型/用户筛选                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.5 安全评分: 认证覆盖率 90.9%

| 安全维度 | 覆盖率 | 实现状态 | 说明 |
|---------|--------|---------|------|
| **身份认证** | 100% | ✅ 完善 | JWT双Token + bcrypt密码哈希 |
| **授权控制** | 95% | ✅ 完善 | RBAC三角色 + 依赖注入 |
| **输入验证** | 90% | ✅ 完善 | Pydantic Schema + Magic Number + XSS过滤 |
| **SQL注入防护** | 100% | ✅ 完善 | SQLAlchemy ORM 参数化查询 |
| **XSS防护** | 85% | ✅ 较好 | CSP头 + sanitize_response() + 转义 |
| **CSRF防护** | 80% | ✅ 较好 | SameSite Cookie + CORS白名单 |
| **速率限制** | 95% | ✅ 完善 | SlowAPI + RateLimiter (令牌桶) |
| **审计日志** | 90% | ✅ 完善 | 14种操作类型 + IP/UA记录 |
| **敏感数据保护** | 85% | ⚠️ 待加强 | JWT_SECRET需生产环境配置 |
| **综合评分** | **90.9%** | ✅ 优秀 | 符合OWASP Top 10防护要求 |

---

## 第6章: 数据库设计

### 6.1 ER 图 (12 表 ASCII 图)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WheatAgent 数据库 ER 图                            │
│                           (MySQL 8.0 + 12张表)                              │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │       users         │
                    │─────────────────────│
                    │ id (PK) AutoInc     │
                    │ username (UQ, IDX)  │
                    │ email (UQ, IDX)     │
                    │ password_hash       │←───────┐
                    │ role (ENUM)         │        │ 1:N
                    │ phone               │        │
                    │ avatar_url          │        │
                    │ is_active           │        │
                    │ created_at          │        │
                    │ updated_at          │        │
                    │ deleted_at (软删除)   │        │
                    │ last_login_at       │        │
                    └──────────┬──────────┘        │
                               │                   │
              ┌────────────────┼────────────────┐  │
              │                │                │  │
              ▼                ▼                ▼  │
    ┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
    │   diagnoses     │ │diseases  │ │ image_metadata    │
    │─────────────────│ │──────────│ │──────────────────│
    │ id (PK)         │ │ id (PK)  │ │ id (PK)           │
    │ user_id (FK)───→│→users.id  │ │ user_id (FK)      │
    │ disease_id (FK) │→diseases.id│ hash_value (UQ)    │ ← 去重键
    │ image_id (FK)───│→image_meta│ original_filename  │
    │ symptoms        │ name      │ file_path          │
    │ severity        │ scientific│ file_size          │
    │ description     │ _name     │ mime_type          │
    │ recommendations│ code (UQ) │ width / height      │
    │ growth_stage    │ category  │ storage_provider   │
    │ weather_data    │ symptoms  │ is_processed       │
    │ location        │ description│ created_at        │
    │ status          │ causes    │                   │
    │ primary_confid- │ treatment_│                   │
    │ ence            │ methods   │                   │
    │ created_at      │ prevention│                   │
    └───────┬─────────│ _methods  │                   │
            │         │ severity  │                   │
            │         │ image_urls│                   │
            │         │ suitable_ │                   │
            │         │ growth... │                   │
            │         └──────────┘                   │
            │                                        │
            ▼ 1:N                                    │
    ┌──────────────────────┐                         │
    │ diagnosis_confidences│                         │
    │──────────────────────│                         │
    │ id (PK)              │                         │
    │ diagnosis_id (FK,CAS)│← diagnoses.id           │
    │ disease_name (IDX)   │                         │
    │ confidence (DEC5,4)  │                         │
    │ disease_class        │                         │
    │ rank                 │                         │
    │ created_at           │                         │
    └──────────────────────┘                         │
                                                    │
    ┌─────────────────────┐                          │
    │   knowledge_graph   │                          │
    │─────────────────────│                          │
    │ id (PK)             │                          │
    │ entity (IDX)        │                          │
    │ entity_type (ENUM)  │                          │
    │ relation (IDX)      │                          │
    │ target_entity       │                          │
    │ attributes (JSON)   │                          │
    │ created_at          │                          │
    └─────────────────────┘                          │
                                                    │
    ┌─────────────────────────────────────────────────┤
    │              认证辅助表 (Auth Tables)             │
    ├─────────────────┬───────────────┬───────────────┤
    │password_reset_  │ refresh_tokens│ login_attempts │
    │tokens           │               │               │
    ├─────────────────┼───────────────┼───────────────┤
    │ id (PK)         │ id (PK)       │ id (PK)        │
    │ user_id (FK,CAS)│ user_id(FK,CAS)│ username(IDX) │
    │ token (UQ)      │ token (UQ)    │ ip_address(IDX)│
    │ expires_at      │ expires_at    │ success        │
    │ used (BOOL)     │ revoked(BOOL) │ timestamp(IDX) │
    │ created_at      │ created_at    │               │
    └─────────────────┴───────────────┴───────────────┘

    ┌─────────────────┐  ┌─────────────────┐
    │  user_sessions   │  │   audit_logs    │
    ├─────────────────┤  ├─────────────────┤
    │ id (PK)         │  │ id (PK)         │
    │ user_id (FK,CAS)│  │ user_id (FK)    │
    │ session_token(UQ)│ action (ENUM,IDX)│
    │ device_info     │  │ resource_type   │
    │ ip_address      │  │ resource_id     │
    │ expires_at      │  │ ip_address      │
    │ is_active       │  │ user_agent      │
    │ created_at      │  │ details (JSON)  │
    └─────────────────┘  │ created_at (IDX)│
                         └─────────────────┘
```

### 6.2 表结构详细说明

#### 6.2.1 users 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 用户 ID |
| `username` | String(50) | UQ, IDX, NOT NULL | 用户名（唯一索引） |
| `email` | String(100) | UQ, IDX, NOT NULL | 邮箱（唯一索引） |
| `password_hash` | String(255) | NOT NULL | bcrypt 密码哈希（72字节限制） |
| `role` | ENUM | DEFAULT 'farmer' | 角色：farmer/technician/admin |
| `phone` | String(20) | NULLABLE | 手机号 |
| `avatar_url` | String(255) | NULLABLE | 头像 URL |
| `is_active` | Boolean | DEFAULT True | 是否激活 |
| `created_at` | DateTime | DEFAULT utcnow | 创建时间 |
| `updated_at` | DateTime | ON UPDATE utcnow | 更新时间 |
| `deleted_at` | DateTime | IDX, NULLABLE | 软删除时间戳 |

**复合索引**: `idx_users_active_deleted(is_active, deleted_at)` — 快速查询活跃用户

#### 6.2.2 diagnoses 诊断记录主表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 诊断记录 ID |
| `user_id` | Integer | FK→users.id, IDX, NOT NULL | 所属用户 |
| `disease_id` | Integer | FK→diseases.id, NULLABLE | 关联病害 |
| `image_id` | Integer | FK→image_metadata.id, SET NULL | 关联图像 |
| `image_url` | String(255) | NULLABLE | 诊断图像 URL |
| `symptoms` | Text | NOT NULL | 症状描述 |
| `severity` | String(20) | NULLABLE | 严重程度 |
| `description` | Text | NULLABLE | 诊断描述 |
| `recommendations` | JSON | NULLABLE | 防治建议（JSON格式） |
| `growth_stage` | String(50) | NULLABLE | 生长阶段 |
| `weather_data` | JSON | NULLABLE | 天气数据 |
| `location` | String(100) | NULLABLE | 地理位置 |
| `status` | String(20) | IDX, DEFAULT 'completed' | 状态：pending/completed |
| `primary_confidence` | DECIMAL(5,4) | NULLABLE | 首选置信度 |
| `created_at` | DateTime | DEFAULT utcnow | 创建时间 |

#### 6.2.3 diagnosis_confidences 多候选置信度子表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 记录 ID |
| `diagnosis_id` | Integer | FK→diagnoses.id CASCADE, NOT NULL | 关联诊断 |
| `disease_name` | String(100) | IDX, NOT NULL | 病害名称 |
| `confidence` | DECIMAL(5,4) | NOT NULL | 置信度 [0,1] |
| `disease_class` | Integer | NULLABLE | YOLO 类别索引 |
| `rank` | Integer | DEFAULT 0 | 排序序号（0=最高） |
| `created_at` | DateTime | DEFAULT utcnow | 创建时间 |

**复合索引**:
- `idx_diagconf_diagnosis_confidence(diagnosis_id, confidence DESC)` — 按置信度降序查询
- `idx_diagconf_disease_name(disease_name)` — 按病害名统计

#### 6.2.4 diseases 病害知识表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 病害 ID |
| `name` | String(100) | IDX, NOT NULL | 病害名称 |
| `scientific_name` | String(100) | NULLABLE | 学名 |
| `code` | String(50) | UQ, IDX | 疾病编码（如 WD001） |
| `category` | ENUM | IDX, NOT NULL | 分类：fungal/bacterial/viral/pest/nutritional |
| `symptoms` | Text | NOT NULL | 症状描述 |
| `description` | Text | NULLABLE | 详细描述 |
| `causes` | Text | NULLABLE | 病因 |
| `prevention_methods` | JSON | NULLABLE | 预防方法 |
| `treatment_methods` | JSON | NULLABLE | 治疗方法 |
| `suitable_growth_stage` | String(100) | NULLABLE | 适用生长阶段 |
| `image_urls` | JSON | NULLABLE | 图片 URL 列表 |
| `severity` | Float | IDX, DEFAULT 0.0 | 严重程度 [0,1] |

#### 6.2.5 knowledge_graph 知识图谱表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 记录 ID |
| `entity` | String(100) | IDX, NOT NULL | 实体名称 |
| `entity_type` | ENUM | IDX, NOT NULL | 实体类型：disease/symptom/pest/treatment/growth_stage |
| `relation` | String(100) | IDX, NULLABLE | 关系类型 |
| `target_entity` | String(100) | NULLABLE | 目标实体 |
| `attributes` | JSON | NULLABLE | 实体属性 |
| `created_at` | DateTime | DEFAULT utcnow | 创建时间 |

**复合索引**:
- `idx_kg_entity_type_entity(entity_type, entity)` — 按类型+名称查询
- `idx_kg_relation_target(relation, target_entity)` — 路径检索优化

#### 6.2.6 image_metadata 图像元数据表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 图像 ID |
| `user_id` | Integer | FK→users.id SET NULL | 上传用户 |
| `hash_value` | String(64) | **UQ**, IDX, NOT NULL | SHA256 哈希值（去重键） |
| `original_filename` | String(255) | NOT NULL | 原始文件名 |
| `file_path` | String(500) | NOT NULL | 存储路径 |
| `file_size` | Integer | NOT NULL | 文件大小（字节） |
| `mime_type` | String(50) | NULLABLE | MIME 类型 |
| `width` | Integer | NULLABLE | 图像宽度 |
| `height` | Integer | NULLABLE | 图像高度 |
| `storage_provider` | ENUM | DEFAULT 'local' | local/minio |
| `is_processed` | Boolean | DEFAULT False | 是否已处理 |
| `created_at` | DateTime | IDX, DEFAULT utcnow | 上传时间 |

**核心设计**: `hash_value UNIQUE` 约束确保相同图像不会重复存储，实现自动去重。

#### 6.2.7 认证辅助表 (4 表)

| 表名 | 用途 | 核心字段 | 特殊约束 |
|------|------|---------|---------|
| **refresh_tokens** | JWT 刷新令牌 | user_id, token(UQ), expires_at, revoked | 用户级唯一令牌 |
| **password_reset_tokens** | 密码重置 | user_id, token(UQ), expires_at, used | 防重复重置 |
| **login_attempts** | 登录审计 | username, ip_address, success, timestamp | IP+时间复合索引防暴力破解 |
| **user_sessions** | 会话管理 | user_id, session_token(UQ), device_info, is_active | 支持多设备踢出 |

#### 6.2.8 audit_logs 审计日志表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AutoInc | 日志 ID |
| `user_id` | Integer | FK→users.id SET NULL | 操作用户（系统操作为NULL） |
| `action` | ENUM | IDX, NOT NULL | 操作类型（14种） |
| `resource_type` | String(50) | IDX, NULLABLE | 资源类型 |
| `resource_id` | Integer | NULLABLE | 资源 ID |
| `ip_address` | String(45) | NULLABLE | IPv4/IPv6 地址 |
| `user_agent` | Text | NULLABLE | 客户端信息 |
| `details` | JSON | NULLABLE | 操作详情 |
| `created_at` | DateTime | IDX, DEFAULT utcnow | 操作时间 |

**操作类型枚举 (14种)**:
```
用户操作: login, logout, register, password_change, password_reset
数据操作: data_create, data_update, data_delete, diagnosis_request
系统操作: role_update, admin_action, token_refresh
```

**复合索引**:
- `idx_audit_user_action_created(user_id, action, created_at)` — 用户行为追踪
- `idx_audit_resource(resource_type, resource_id)` — 资源变更审计
- `idx_audit_action_created(action, created_at)` — 按操作类型统计

### 6.3 索引策略总览

| 索引类别 | 数量 | 设计原则 | 典型场景 |
|---------|------|---------|---------|
| **主键索引** | 12 | 每表一个自增主键 | 单行精确查找 |
| **唯一索引** | 6 | username/email/hash_value/token | 数据完整性约束 |
| **单列索引** | ~20 | 高频查询字段 | WHERE 条件过滤 |
| **复合索引** | 8 | 多条件联合查询 | 分页/排序/统计 |
| **外键索引** | 10 | 所有 FK 字段自动加索引 | JOIN 连接加速 |

**关键性能优化点**:

1. **diagnosis_confidences 复合索引**: `(diagnosis_id, confidence DESC)` — 每次诊断结果按置信度降序排列，避免额外排序
2. **users 软删除模式**: `(is_active, deleted_at)` — 过滤已删除用户的常用查询
3. **image_metadata 去重**: `hash_value UNIQUE` — SHA256 哈希自动防止重复上传
4. **audit_logs 时间序列**: `(action, created_at)` — 审计日志按时间范围高效查询

### 6.4 数据关系图 (Mermaid 兼容)

```
users ||--o{ diagnoses : "1:N (拥有)"
users ||--o{ image_metadata : "1:N (上传)"
users ||--o{ audit_logs : "1:N (操作)"
users ||--o{ refresh_tokens : "1:N (令牌)"
users ||--o{ password_reset_tokens : "1:N (重置)"
users ||--o{ user_sessions : "1:N (会话)"

diseases ||--o{ diagnoses : "1:N (被诊断)"
image_metadata ||--o{ diagnoses : "1:N (被使用)"
diagnoses ||--|{ diagnosis_confidences : "1:N (候选)"
```

---

## 第7章: 配置管理

### 7.1 配置架构概览

WheatAgent 采用**分层配置 + 外部化**策略，支持开发/测试/生产环境无缝切换：

```
┌─────────────────────────────────────────────────────────────────┐
│                     配置层级优先级 (高→低)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 运行时配置 (Runtime)                                   │
│  ├── API 动态修改                                                │
│  ├── 热更新通知                                                   │
│  └── 优先级: ⭐⭐⭐⭐⭐ 最高                                      │
│                                                                 │
│  Layer 2: 环境变量 (.env)                                        │
│  ├── 生产环境敏感信息                                             │
│  ├── Docker/K8s 注入                                              │
│  └── 优先级: ⭐⭐⭐⭐                                            │
│                                                                 │
│  Layer 3: 用户配置 (config/user.yaml)                             │
│  ├── 运维自定义参数                                               │
│  ├── 不纳入版本控制                                               │
│  └── 优先级: ⭐⭐⭐                                              │
│                                                                 │
│  Layer 4: 环境配置 (config/{env}.yaml)                            │
│  ├── development.yaml / production.yaml                           │
│  ├── 环境差异化参数                                               │
│  └── 优先级: ⭐⭐                                               │
│                                                                 │
│  Layer 5: 默认配置 (config/default.yaml)                          │
│  ├── 内置默认值                                                   │
│  ├── 纳入版本控制                                                 │
│  └── 优先级: ⭐ 最低                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 核心配置类: Settings (`app/core/config.py`, 178 行)

Settings 类基于 **Pydantic BaseSettings**，所有配置项均从环境变量读取，支持默认值和类型校验。

#### 7.2.1 基础应用配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `APP_NAME` | - | 基于多模态融合的小麦病害诊断系统 | 应用名称 |
| `APP_VERSION` | - | 1.0.0 | 应用版本号 |
| `DEBUG` | DEBUG | False | 调试模式开关 |
| `API_PREFIX` | API_PREFIX | /api/v1 | API 路由前缀 |

#### 7.2.2 数据库配置 (MySQL)

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `DATABASE_HOST` | DATABASE_HOST | localhost | MySQL 主机地址 |
| `DATABASE_PORT` | DATABASE_PORT | 3306 | MySQL 端口 |
| `DATABASE_NAME` | DATABASE_NAME | wheat_agent_db | 数据库名称 |
| `DATABASE_USER` | DATABASE_USER | root | 数据库用户 |
| `DATABASE_PASSWORD` | DATABASE_PASSWORD | "" | 数据库密码 |
| `DB_POOL_SIZE` | DB_POOL_SIZE | 10 | 连接池大小 |
| `DB_MAX_OVERFLOW` | DB_MAX_OVERFLOW | 20 | 溢出连接数 |
| `DB_POOL_TIMEOUT` | DB_POOL_TIMEOUT | 30 | 获取连接超时(s) |
| `DB_POOL_RECYCLE` | DB_POOL_RECYCLE | 3600 | 连接回收时间(s) |

**数据库 URL 自动构建** (属性方法):
```python
# 输出格式: mysql+aiomysql://user:pass@host:port/db?charset=utf8mb4
@property
def DATABASE_URL(self) -> str:
    return f"mysql+aiomysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}" \
           f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
```

#### 7.2.3 Redis 缓存配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `REDIS_HOST` | REDIS_HOST | localhost | Redis 主机 |
| `REDIS_PORT` | REDIS_PORT | 6379 | Redis 端口 |
| `REDIS_DB` | REDIS_DB | 0 | 数据库编号 |
| `REDIS_PASSWORD` | REDIS_PASSWORD | "" | 密码 |

#### 7.2.4 Neo4j 图数据库配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `NEO4J_URI` | NEO4J_URI | bolt://localhost:7687 | Bolt 协议地址 |
| `NEO4J_USER` | NEO4J_USER | neo4j | 用户名 |
| `NEO4J_PASSWORD` | NEO4J_PASSWORD | "" | 密码 |
| `NEO4J_DATABASE` | NEO4J_DATABASE | neo4j | 数据库名 |
| `NEO4J_MAX_CONNECTION_POOL_SIZE` | NEO4J_MAX_CONNECTION_POOL_SIZE | 50 | 最大连接池 |
| `NEO4J_CONNECTION_TIMEOUT` | NEO4J_CONNECTION_TIMEOUT | 30 | 连接超时(s) |

#### 7.2.5 JWT 安全配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `JWT_ALGORITHM` | - | HS256 | 签名算法 |
| `JWT_SECRET_KEY` | JWT_SECRET_KEY | *(自动生成/必填)* | 签名密钥 |
| `JWT_EXPIRE_HOURS` | JWT_EXPIRE_HOURS | 24 | Access Token 有效期(h) |

**安全机制**: 
- 开发环境未配置时自动生成临时密钥并输出警告
- 生产环境未配置时抛出 ValueError 异常，阻止启动
- 密钥缓存机制保证生命周期内一致性

#### 7.2.6 CORS 跨域配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `CORS_ORIGINS` | CORS_ORIGINS | localhost:3000,5173,8080 | 允许的源列表 |
| `CORS_ALLOW_CREDENTIALS` | CORS_ALLOW_CREDENTIALS | true | 允许凭证 |
| `CORS_MAX_AGE` | CORS_MAX_AGE | 600 | 预检缓存(s) |

**安全特性**: 通配符 `*` 自动过滤并报警告；空列表时回退到 localhost 默认值。

#### 7.2.7 本地文件存储配置（MinIO已弃用）

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `UPLOAD_DIR` | UPLOAD_DIR | ./uploads | 文件上传目录 |

**说明**: MinIO对象存储已弃用，系统使用本地文件存储。

#### 7.2.8 AI 融合引擎配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `FUSION_DEGRADATION_FACTOR` | FUSION_DEGRADATION_FACTOR | 0.9 | 降级因子 |
| `FUSION_VISUAL_WEIGHT` | FUSION_VISUAL_WEIGHT | 0.4 | 视觉权重 |
| `FUSION_TEXTUAL_WEIGHT` | FUSION_TEXTUAL_WEIGHT | 0.35 | 文本权重 |
| `FUSION_KNOWLEDGE_WEIGHT` | FUSION_KNOWLEDGE_WEIGHT | 0.25 | 知识权重 |

> **注**: ai_config.py 中的融合权重 (vision=0.6, text=0.4, knowledge=0.3) 为 V2.0 DeepStack 版本，Settings 中为 V1.0 基础版本。

#### 7.2.9 推理缓存配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `INFERENCE_CACHE_TTL` | INFERENCE_CACHE_TTL | 86400 (30min) | 缓存过期时间(s) |
| `INFERENCE_CACHE_ENABLED` | INFERENCE_CACHE_ENABLED | true | 缓存开关 |
| `INFERENCE_CACHE_ENABLE_SIMILAR_SEARCH` | INFERENCE_CACHE_ENABLE_SIMILAR_SEARCH | true | 相似图像搜索 |
| `INFERENCE_CACHE_SIMILARITY_THRESHOLD` | INFERENCE_CACHE_SIMILARITY_THRESHOLD | 5 | 相似度阈值 |

#### 7.2.10 SSE 流式响应配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `SSE_TIMEOUT_SECONDS` | SSE_TIMEOUT_SECONDS | 120 | 总超时时间(s) |
| `SSE_HEARTBEAT_INTERVAL` | SSE_HEARTBEAT_INTERVAL | 15 | 心跳间隔(s) |
| `SSE_BACKPRESSURE_QUEUE_SIZE` | SSE_BACKPRESSURE_QUEUE_SIZE | 100 | 背压队列容量 |

#### 7.2.11 并发控制与 GPU 监控配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `MAX_CONCURRENT_DIAGNOSIS` | MAX_CONCURRENT_DIAGNOSIS | 3 | 最大并发诊断数 |
| `MAX_DIAGNOSIS_QUEUE_SIZE` | MAX_DIAGNOSIS_QUEUE_SIZE | 10 | 诊断队列容量 |
| `DIAGNOSIS_QUEUE_TIMEOUT` | DIAGNOSIS_QUEUE_TIMEOUT | 300 | 队列超时(s) |
| `GPU_MEMORY_THRESHOLD` | GPU_MEMORY_THRESHOLD | 0.90 | 显存警告阈值 |

#### 7.2.12 速率限制配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|-------|------|
| `RATE_LIMIT_ENABLED` | RATE_LIMIT_ENABLED | true | 全局限流开关 |
| `RATE_LIMIT_DEFAULT` | RATE_LIMIT_DEFAULT | 60/minute | 默认限流 |
| `RATE_LIMIT_DIAGNOSIS` | RATE_LIMIT_DIAGNOSIS | 10/minute | 诊断接口限流 |
| `RATE_LIMIT_UPLOAD` | RATE_LIMIT_UPLOAD | 20/minute | 上传接口限流 |

### 7.3 ConfigManager 分层配置器 (`src/utils/config_manager.py`, 517 行)

除 Settings 外，项目还提供更强大的 `ConfigManager` 单例类：

```
ConfigManager 核心能力:
├── 四层配置覆盖: runtime > user > environment > default
├── YAML/JSON 文件格式支持
├── 配置热更新 (文件变更监听线程)
├── 配置验证 (Schema 校验 + 自定义 Validator)
├── 配置变更监听器 (Listener 模式)
├── 点号路径访问 (如 model.vision.confidence_threshold)
└── 线程安全 (双重检查锁单例)
```

**典型用途**: AI 模型参数、推理配置、训练超参等需要动态调整的场景。

### 7.4 .env 文件模板

```bash
# ===== 应用基础配置 =====
DEBUG=False
API_PREFIX=/api/v1

# ===== MySQL 数据库 =====
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=wheat_agent_db
DATABASE_USER=root
DATABASE_PASSWORD=your_password_here
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ===== Redis 缓存 =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ===== Neo4j 图数据库 =====
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ===== JWT 安全 (生产环境必须配置!) =====
JWT_SECRET_KEY=your_production_secret_key_here
JWT_EXPIRE_MINUTES=30

# ===== 本地文件存储（MinIO已弃用）=====
UPLOAD_DIR=./uploads

# ===== CORS 跨域 =====
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ===== GPU 与并发控制 =====
MAX_CONCURRENT_DIAGNOSIS=3
GPU_MEMORY_THRESHOLD=0.90

# ===== SSE 流式响应 =====
SSE_TIMEOUT_SECONDS=120
SSE_HEARTBEAT_INTERVAL=15
```

---

## 第8章: 性能与优化

### 8.1 性能基准指标矩阵

```
┌─────────────────────────────────────────────────────────────────┐
│                    WheatAgent 性能基准矩阵                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┬──────────┬──────────┬────────┬─────────┐ │
│  │ 性能指标           │ 目标值    │ 实测值    │ 达标率 │ 优化方向 │ │
│  ├──────────────────┼──────────┼──────────┼────────┼─────────┤ │
│  │ SSE首事件延迟      │ <500ms   │ 0.01ms   │ 50000× │ ✅ 已达标│ │
│  │ YOLO推理(GPU)     │ <100ms   │ <50ms    │ 200%   │ ✅ 已达标│ │
│  │ YOLO推理(CPU)     │ <300ms   │ ~187ms   │ 160%   │ ✅ 已达标│ │
│  │ Qwen首次推理       │ <40s     │ <35s     │ 114%   │ ✅ 已达标│ │
│  │ Qwen后续推理       │ <35s     │ <25-30s  │ 117%   │ ✅ 已达标│ │
│  │ KAD-Former融合     │ <5ms     │ <1ms     │ 500%   │ ✅ 已达标│ │
│  │ GraphRAG检索       │ <100ms   │ ~50ms    │ 200%   │ ✅ 已达标│ │
│  │ 数据库写入         │ <50ms    │ ~10ms    │ 500%   │ ✅ 已达标│ │
│  │ SSE事件格式化       │ <10ms    │ 6.19μs   │ 1615× │ ✅ 已达标│ │
│  │ 心跳事件格式化      │ <10ms    │ 4.28μs   │ 2336× │ ✅ 已达标│ │
│  └──────────────────┴──────────┴──────────┴────────┴─────────┘ │
│                                                                 │
│  综合评价: 🟢 全部指标超标达成                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.1.1 PipelineTimer 流水线计时器

**位置**: [fusion_service.py:54-120](../src/web/backend/app/services/fusion_service.py#L54-L120)

**设计目的**: 精确测量融合诊断流水线各阶段的耗时,支持性能分析和瓶颈定位

**核心能力**:
- 上下文管理器模式: `with timer.stage("阶段名"):`
- 手动计时模式: `timer.start("阶段名")` / `timer.stop()`
- 自动汇总: `timer.summary()` 输出各阶段耗时报告
- 嵌套计时: 支持子阶段嵌套测量

**使用示例**:
```python
from app.services.fusion_service import PipelineTimer

def diagnose_async(self, ...):
    timer = PipelineTimer()

    with timer.stage("初始化"):
        self.initialize()

    with timer.stage("特征提取"):
        features = self._feature_extractor.extract_features(...)

    with timer.stage("KAD-Former融合"):
        fused = self._fusion_engine.fuse_features(...)

    with timer.stage("结果标注"):
        result = self._result_annotator.annotate(fused)

    logger.info(timer.summary())
    # 输出:
    # [PipelineTimer] 总耗时: 1234.56ms
    #   - 初始化: 5.23ms (0.4%)
    #   - 特征提取: 890.12ms (72.1%) ← 瓶颈
    #   - KAD-Former融合: 45.67ms (3.7%)
    #   - 结果标注: 293.54ms (23.8%)
```

**各阶段名称与典型耗时**:

| 阶段名称 | 说明 | CPU环境典型耗时 | GPU环境典型耗时 | 占比 |
|---------|------|----------------|----------------|------|
| `请求验证` | 文件校验/限流/Mock检查 | <1ms | <1ms | <0.1% |
| `图像预处理` | Letterbox/Normalize/格式转换 | ~0.9ms | <0.5ms | <0.1% |
| `YOLO推理` | 视觉目标检测(16类病害) | ~187ms | <50ms | 15-25% |
| `Qwen推理` | 多模态语义理解 | ~25-30s | ~5-8s | 60-80% |
| `GraphRAG检索` | 知识图谱子图查询 | ~50ms | ~50ms | 1-5% |
| `KAD-Former融合` | 跨模态注意力融合 | <1ms | <1ms | <0.1% |
| `结果标注` | ROI框绘制/Base64编码/缓存 | ~293ms | ~200ms | 10-20% |

**输出格式**: `timer.summary()` 返回结构化日志,包含:
- 总耗时 (毫秒)
- 各阶段绝对耗时和百分比
- 自动标记瓶颈阶段 (占比>50% 标记为 ⚠️)
- 支持 JSON 格式导出 (`timer.to_json()`)

**集成位置**: 在 `diagnose_async()` 方法中自动启用,结果写入日志和返回给客户端的 `performance.inference_time_ms`

### 8.2 各阶段耗时分布 (CPU 环境)

```
完整诊断流程耗时分布 (不含模型懒加载):

Step 1 请求验证     ████░░░░░░░░░░░░  <1ms     (~0.5%)
Step 2 图像预处理   ██████░░░░░░░░░░  ~0.9ms   (~0.5%)
Step 3 YOLOv8检测   ████████████████  ~187ms   (~85%)  ← 最大瓶颈
Step 4 Qwen3-VL分析  ████████████████████████████  N/A (GPU专用)
Step 5 KAD融合       ██░░░░░░░░░░░░░  <1ms     (~0.3%)
Step 6 GraphRAG      █████░░░░░░░░░░  ~50ms    (~12%)
Step 7 结果组装       ░░░░░░░░░░░░░░  <1ms     (<0.1%)
Step 8 持久化写入     ████░░░░░░░░░░░  ~10ms    (~4.5%)
Step 9 资源清理       ░░░░░░░░░░░░░░  <1ms     (<0.1%)
Step 10 SSE输出       ░░░░░░░░░░░░░░  0.01ms*  (首事件)
                      ─────────────────────────
                      总计 (CPU):     ~250ms   (不含Qwen)
```

> * SSE 首事件延迟，非总耗时

### 8.3 优化策略详解

#### 8.3.1 推理层优化

| 优化技术 | 应用位置 | 效果 | 实现状态 |
|---------|---------|------|---------|
| **FP16 半精度推理** | YOLOv8 GPU 模式 | 显存减半，速度提升 ~2x | ✅ 已启用 |
| **INT4 量化** | Qwen3-VL-2B | 显存 9.8GB → 2.6GB (-73.5%) | ✅ 已启用 |
| **Flash Attention 2** | Qwen3-VL | 注意力计算加速 ~2x | ✅ 已启用 (需Ampere+) |
| **KV Cache 量化** | Qwen3-VL | KV Cache 4bit 压缩 | ✅ 已启用 |
| **Torch Compile** | Qwen3-VL | 图优化 reduce-overhead | ✅ 已启用 |
| **CPU Offload** | Qwen3-VL | 显存不足时卸载至内存 | ✅ 已启用 |
| **LRU 缓存** | YOLOv8 检测结果 | 相同图像复用 (maxsize=64) | ✅ 已启用 |
| **动态批处理** | 批量诊断请求 | 吞吐量提升 | ✅ 已启用 (max_size=16) |

#### 8.3.2 网络层优化

| 优化技术 | 应用位置 | 效果 | 实现状态 |
|---------|---------|------|---------|
| **GZip 压缩** | Response Middleware | 带宽减少 ~70% | ✅ 已启用 (min_size=1KB) |
| **SSE 流式传输** | 诊断结果推送 | 首屏时间 <1ms | ✅ 已启用 |
| **背压控制** | SSE asyncio.Queue | 内存溢出保护 | ✅ 已启用 (maxsize=100) |
| **心跳保活** | SSE Heartbeat | 防代理超时断开 | ✅ 已启用 (15s间隔) |
| **连接池复用** | MySQL/Redis/Neo4j | 连接建立开销归零 | ✅ 已启用 |

#### 8.3.3 数据层优化

| 优化技术 | 应用位置 | 效果 | 实现状态 |
|---------|---------|------|---------|
| **Async SQLAlchemy** | ORM 层 | 非阻塞数据库 IO | ✅ 已启用 (aiomysql) |
| **连接池** | MySQL (10+20) | 连接复用 | ✅ 已启用 |
| **Redis 缓存** | 推理结果 | 相同查询命中 <1ms | ✅ 已启用 (TTL=24h) |
| **复合索引** | MySQL 8 个 | 查询加速 10-100x | ✅ 已启用 |
| **SHA256 去重** | image_metadata | 避免重复存储/推理 | ✅ 已启用 |
| **批量插入** | diagnosis_confidences | 子表批量写优化 | ✅ 已启用 |

#### 8.3.4 并发控制优化

| 优化技术 | 应用位置 | 效果 | 实现状态 |
|---------|---------|------|---------|
| **令牌桶限流** | RateLimiter | 并发 ≤3 诊断 | ✅ 已启用 |
| **推理队列** | InferenceQueue | 请求排队 FIFO | ✅ 已启用 (capacity=10) |
| **GPU 显存监控** | GPUMonitor | 使用率 >90% 时拒绝 | ✅ 已启用 |
| **SlowAPI 限流** | API 层 | 全局 60/min | ✅ 已启用 |

### 8.4 瓶颈分析与优化方向

```
当前瓶颈排名 (按影响程度):
┌──────────────────────────────────────────────────────────────┐
│ #1  Qwen3-VL 推理 (~25-30s)                                  │
│     占比: >90% 的端到端耗时                                    │
│     优化方向:                                                 │
│     ├── 模型蒸馏 (Teacher→Student, 目标 500M 参数)            │
│     ├── INT8 进一步量化 (当前 INT4 已接近极限)                  │
│     ├── 推理并行化 (TensorRT/vLLM 加速)                        │
│     └── 结果缓存命中率提升 (相似问题复用)                       │
│                                                              │
│ #2  YOLOv8 CPU 推理 (~187ms)                                 │
│     占比: CPU 模式下 ~75%                                     │
│     优化方向:                                                 │
│     ├── ONNX Runtime 推理 (比 PyTorch 快 2-3x)                │
│     ├── OpenVINO 加速 (Intel CPU 优化)                        │
│     └── TensorRT 加速 (NVIDIA GPU)                            │
│                                                              │
│ #3  GraphRAG 检索 (~50ms)                                    │
│     占比: ~12%                                                │
│     优化方向:                                                 │
│     ├── Neo4j 查询计划缓存                                     │
│     ├── TransE 嵌入预计算                                      │
│     └── 结果缓存层 (知识上下文缓存)                             │
│                                                              │
│ #4  数据库写入 (~10ms)                                       │
│     占比: ~4.5%                                               │
│     当前状态: 已较优                                          │
│     优化方向: 批量写入合并 + 异步刷盘                           │
└──────────────────────────────────────────────────────────────┘
```

### 8.5 代码质量评分

| 维度 | 得分 | 说明 |
|------|------|------|
| **代码规范** | 93.6/100 | V7_PROJECT_ANALYSIS.md 综合评分 |
| **类型标注覆盖率** | >90% | Python type hints + Pydantic |
| **测试用例数** | 1113+ | 包含单元/集成/E2E 测试 |
| **文档覆盖** | 28/28 文件 | docs/ 目录全部完成 |
| **安全评分** | 90.9% | OWASP Top 10 覆盖率 |

---

## 第9章: 部署与运维

### 9.1 部署架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WheatAgent 部署拓扑图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐   │
│  │   用户浏览器   │────│   Nginx     │────│   Vue3 前端 (静态资源)       │   │
│  │  (Chrome等)  │    │  反向代理    │    │   dist/ (npm run build)     │   │
│  └─────────────┘     └──────┬──────┘     └─────────────────────────────┘   │
│                             │  :80/:443                                       │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI 后端服务                                   │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Gunicorn (4 Workers) × Uvicorn (ASGI)                         │  │   │
│  │  │  Port: 8000 | Timeout: 120s (SSE长连接)                       │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│           ┌───────────────────────┼───────────────────────┐                 │
│           ▼                       ▼                       ▼                 │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │   MySQL 8.0    │    │    Redis 7.2   │    │   Neo4j 5.x    │            │
│  │   :3306        │    │    :6379       │    │   :7687(Bolt)  │            │
│  │  业务数据(12表) │    │  缓存/会话/队列 │    │  知识图谱(106实体)│           │
│  └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                   │         │
│  ┌─────────────────────────────────────────────────────────────┐ │         │
│  │                    本地文件存储                                │ │         │
│  │                    :9000 (API) / :9001 (Console)             │ │         │
│  │                    图像文件 / 模型权重                        │ │         │
│  └─────────────────────────────────────────────────────────────┘ │         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    可选: 监控栈 (monitoring profile)                 │   │
│  │  Prometheus (:9090) ←── metrics scrape ──→ Grafana (:3000)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 硬件需求

| 场景 | CPU | 内存 | GPU | 存储 | 网络 |
|------|-----|------|-----|------|------|
| **最低开发** | 4核 | 16GB | 无 (CPU模式) | 50GB SSD | - |
| **推荐开发** | 8核 | 32GB | GTX 1660+ (6GB) | 100GB SSD | - |
| **生产部署** | 16核 | 64GB | T4 ×1 (16GB) | 500GB NVMe | 1Gbps |
| **高性能部署** | 32核 | 128GB | T4 ×4 (16GB) | 2TB NVMe | 10Gbps |

### 9.3 软件依赖版本

| 组件 | 最低版本 | 推荐版本 | 用途 |
|------|---------|---------|------|
| **Python** | 3.10 | 3.10.12 | 后端运行时 |
| **MySQL** | 8.0 | 8.0.36 | 主数据库 |
| **Redis** | 7.0 | 7.2.4 | 缓存/会话/队列 |
| **Node.js** | 18 | 20 LTS | 前端构建 |
| **Neo4j** | 5.x | 5.12+ | 知识图谱 |
| **MinIO** | - | - | ~~已弃用，使用本地文件存储~~ |
| **Docker** | 20.10+ | 24.x+ | 容器化部署 |
| **CUDA** | 12.0 | 12.1+ | GPU 计算 (可选) |

### 9.4 Docker Compose 一键部署

项目提供完整的 `deploy/docker-compose.yml` (253 行)，包含 6 个核心服务 + 2 个可选监控服务：

**核心服务**:

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `api` | iwdda/api:latest | 8000 | FastAPI 后端 (含 GPU 支持) |
| `web` | iwdda/web:latest | 5173 | Vue 3 前端 |
| `neo4j` | neo4j:5.12 | 7474/7687 | 知识图谱数据库 |
| `redis` | redis:7-alpine | 6379 | 缓存/任务队列 |
| `minio` | minio/minio | 9000/9001 | 对象存储 |
| `training` | iwdda/training:latest | - | 模型训练 (profile: training) |

**可选服务 (profiles)**:

| Profile | 服务 | 端口 | 说明 |
|---------|------|------|------|
| `monitoring` | prometheus | 9090 | 指标采集 |
| `monitoring` | grafana | 3000 | 可视化面板 |
| `training` | training | - | 模型训练 |

**快速启动命令**:
```bash
# 克隆项目后进入部署目录
cd deploy

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 填入实际密码和密钥

# 启动核心服务
docker-compose up -d

# 启动含监控的全量服务
docker-compose --profile monitoring up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 9.5 开发模式启动

适用于本地开发和调试，无需 Docker：

```bash
# ===== 终端 1: 启动后端 =====
cd D:\Project\WheatAgent\src\web\backend
conda activate wheatagent-py310
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ===== 终端 2: 启动前端 =====
cd D:\Project\WheatAgent\src\web\frontend
npm run dev
```

**访问地址**:
| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:5173 | Vite 开发服务器 |
| API 文档 (Swagger) | http://localhost:8000/docs | 交互式 API 文档 |
| ReDoc 文档 | http://localhost:8000/redoc | 美化 API 文档 |
| 健康检查 | http://localhost:8000/api/v1/health | 系统健康状态 |
| Prometheus 指标 | http://localhost:8000/metrics | 监控指标 |

### 9.6 生产模式启动 (Gunicorn + Uvicorn)

```bash
cd D:\Project\WheatAgent\src\web\backend
conda activate wheatagent-py310

gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile -
```

**Worker 数建议**: `CPU 核数 × 2 + 1`（如 8 核 → 17 workers）
**Timeout 设置**: 120s（适配 SSE 长连接和 Qwen 推理耗时）

### 9.7 健康检查端点

| 端点 | 方法 | 说明 | 预期响应 |
|------|------|------|---------|
| `/api/v1/health` | GET | 基础健康检查 | `{"status": "healthy"}` |
| `/api/v1/health/database` | GET | 数据库连通性 | `{"mysql": "connected", ...}` |
| `/api/v1/health/startup` | GET | 启动阶段状态 | 4 阶段进度 |
| `/api/v1/health/ready` | GET | 就绪探针 (K8s) | `{"ready": true}` |
| `/api/v1/health/components` | GET | 各组件详情 | MySQL/Redis/Neo4j/AI 状态 |
| `/api/v1/health/ai` | GET | AI 模型状态 | YOLO/Qwen/KAD 就绪情况 |

### 9.8 监控体系

```
┌─────────────────────────────────────────────────────────────────┐
│                    三层监控体系                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L1: 应用内监控 (app/monitoring/)                                │
│  ├── MetricsCollector (576行) — 指标采集                        │
│  │   ├── 请求计数/延迟/P99                                      │
│  │   ├── 诊断成功率/失败率                                       │
│  │   ├── 模型推理耗时分布                                        │
│  │   └── GPU 显存/利用率                                        │
│  ├── AlertManager (651行) — 告警管理                            │
│  │   ├── 阈值规则引擎                                           │
│  │   ├── 多通道通知 (Webhook/邮件)                               │
│  │   └── 告警抑制/聚合                                          │
│  └── MonitoringAPI (526行) — 指标暴露                            │
│      └── /metrics 端点 (Prometheus 格式)                        │
│                                                                 │
│  L2: 基础设施监控 (Prometheus + Grafana)                         │
│  ├── 指标采集间隔: 15s                                          │
│  ├── 数据保留: 15天                                             │
│  └── Dashboard: 系统概况/诊断流量/错误率/GPU状态                  │
│                                                                 │
│  L3: 日志集中 (结构化 JSON 日志)                                 │
│  ├── 日志级别: DEBUG/INFO/WARNING/ERROR/CRITICAL                │
│  ├── Request-ID 全链路追踪                                      │
│  └── ELK Stack 可选集成                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.9 运维操作手册

#### 日常运维

| 操作 | 命令/方法 | 频率 |
|------|----------|------|
| 健康检查 | `GET /api/v1/health` | 每 5 分钟 (自动) |
| 日志轮转 | logrotate / Docker driver | 每天 |
| 数据库备份 | `mysqldump` + 定时任务 | 每天 02:00 |
| Redis 持久化 | AOF + RDB | 自动 |
| 磁盘清理 | 临时文件 + 过期缓存 | 每周 |
| 证书更新 | Let's Encrypt / 手动 | 每 90 天 |

#### 故障排查 Top 10

| # | 故障现象 | 可能原因 | 解决方案 |
|---|---------|---------|---------|
| 1 | API 无法启动 | 端口占用/依赖未启动 | `lsof -i :8000`; 检查 docker-compose 依赖 |
| 2 | 数据库连接失败 | MySQL 未启动/密码错误 | 检查 `.env` 中 DATABASE_* 配置 |
| 3 | Redis 连接失败 | Redis 未运行 | `redis-server --daemonize yes` |
| 4 | Neo4j 连接失败 | Bolt 端口不通 | 检查 7687 端口防火墙 |
| 5 | Qwen 模型加载失败 | 显存不足/CUDA 错误 | 降低 batch size; 检查 nvidia-smi |
| 6 | YOLO 推理 OOM | 图像过大/并发过多 | 调整 MAX_CONCURRENT_DIAGNOSIS |
| 7 | SSE 连接断开 | 超时/代理限制 | 检查 SSE_TIMEOUT_SECONDS; 心跳间隔 |
| 8 | 上传文件失败 | 存储空间不足/权限错误 | 检查磁盘空间; 检查上传目录权限 |
| 9 | JWT 验证失败 | Secret Key 不一致 | 确保前后端使用相同密钥 |
| 10 | 前端无法连接 API | CORS 配置错误 | 检查 CORS_ORIGINS 环境变量 |

#### 备份与恢复策略

```
备份策略:
├── MySQL: mysqldump --single-transaction --routines (每日全量 + binlog 增量)
├── Neo4j: neo4j-admin dump (每周全量)
├── Redis: AOF 持久化 + RDB 快照 (自动)
├── 本地文件: 定期备份上传目录 (每日增量)
└── 配置文件: .env + config/*.yaml (Git 管理 + 加密存储)

恢复目标:
├── RPO (Recovery Point Objective): < 1 小时
├── RTO (Recovery Time Objective): < 30 分钟
└── 数据完整性: ACID 事务保证
```

### 9.10 扩展性规划

| 方向 | 当前状态 | 规划 | 优先级 |
|------|---------|------|--------|
| **水平扩展** | 单实例 | Kubernetes Deployment + HPA | 中 |
| **模型服务化** | 内嵌进程 | 独立 Model Service (Triton) | 高 |
| **前端 CDN** | 本地 Nginx | CloudFlare/OSS CDN | 低 |
| **读写分离** | 单 MySQL | Master-Slave 架构 | 中 |
| **消息队列** | Redis 简单队列 | RabbitMQ/Kafka | 低 |
| **多区域部署** | 单节点 | 多可用区容灾 | 低 |

---

> **文档结束**
>
> 本白皮书基于 WheatAgent V12.0 代码库实际编写，所有技术数据来源于源码分析。
> 最后更新: 2026-04-05 | 综合评分: 93.6/100