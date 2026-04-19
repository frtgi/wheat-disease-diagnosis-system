# 基于多模态融合的小麦病害诊断系统 — 变更日志

> 所有版本变更记录集中管理

---

## [V41.0] - 2026-04-20 📝 文档全面对齐更新

### 📝 文档更新
- **README.md**: 完全重写，移除过时的 Gradio/BERT 引用，更新为 Vue3+FastAPI+Qwen3-VL 技术栈
- **WEB_ARCHITECTURE.md**: V12.0 → V41.0，新增安全设计（XSS防护/开放重定向/账户锁定/SHA-256令牌哈希）、管理员路由、导航状态持久化、遗留组件说明
- **API_REFERENCE.md**: V12.0 → V41.0，更新认证要求（知识库/统计端点需认证）、新增知识图谱/统计/显存端点、补充 SHA-256 密码重置令牌说明
- **DEPLOYMENT.md**: V12.0 → V41.0，版本号对齐
- **TEST_GUIDE.md**: V12.0 → V41.0，修正 Node.js 版本矛盾（v16→v18+）

### 🔒 安全特性记录（V29-V41 累积）
- XSS 防护：html.escape 转义 + sanitize_response 装饰器 + CSP 安全头
- 开放重定向防护：Login.vue redirect 参数验证
- 密码重置令牌：SHA-256 哈希存储 + 1 小时有效期 + 一次性使用
- 授权检查：get_user/update_user 本人或管理员模式
- 知识库/统计端点认证升级：knowledge.graph/stats、stats.overview/diagnoses/cache 需认证
- 账户锁定：连续 5 次失败锁定 30 分钟
- Cookie 安全：httpOnly + secure + samesite=lax
- 错误信息脱敏：非 DEBUG 模式隐藏 traceback

### ✅ 验收测试结果（V40）
- 后端 API 测试：46/46 PASS (100%)
- 前端 E2E 测试：14/14 PASS (100%)
- 总计：60/60 PASS (100%)

### 🐛 Bug 修复（V40）
- Login.vue 登录导航：`router.push('/')` → `router.replace('/dashboard')`，修复路由守卫竞态
- router/index.ts：移除重复 `isAuthenticated` 声明，修复 Vite 编译错误

---

## [V13.0] - 2026-04-16 ✅ 前后端系统验收测试

### 🧪 验收测试执行
- **测试类型**: 端到端系统验收测试（启动真实服务）
- **测试结果**: 19项测试, 18通过, 1失败, **94.7%通过率**
- **验收结论**: ✅ **有条件通过**

### ✅ 通过项 (18/19)
- 服务启动: 后端FastAPI(8000) + 前端Vite(5173) 均正常启动
- 认证流程: 注册→登录→Token验证→无效Token拒绝 全部通过
- 诊断流程: SSE流式诊断(降级模式)返回完整结果(小麦条锈病, confidence=0.805)
- 数据交互: 知识库查询、诊断记录分页、统计接口 全部正常
- 安全防护: XSS(AUTH_005)、未认证(401)、无效方法(405)、不存在端点(404) 全部正确

### ❌ 失败项 (1/19) — P2级别
- **BUG-001**: 诊断记录查询接口响应时间6120ms > 5s阈值
  - 原因: 多表JOIN + SQLAlchemy lazy loading开销
  - 建议: 添加eager loading和复合索引优化

### ⚠️ 环境问题
- Redis不可用(未安装) → JWT黑名单和缓存功能降级
- Qwen3-VL INT4量化加载失败 → 多模态诊断降级为纯文本模式

### 📊 性能数据
| 端点 | 响应时间 | 目标 |
|------|---------|------|
| GET /api/v1/health | 2042ms | <5s ✅ |
| GET /api/v1/knowledge/search | 2051ms | <5s ✅ |
| GET /api/v1/diagnosis/records | 6120ms | <5s ❌ |

### 📄 产出物
- V13_ACCEPTANCE_TEST_REPORT.md — `.trae/specs/v13-system-acceptance-testing/`

---

## [V12.0] - 2026-04-16 🏗️ 架构深度分析 + 文档V12对齐重写

### 📊 架构深度分析
- **架构成熟度评分**: 3.7/5 (Level 3 Defined — 良好)
- **5种设计模式识别**: Facade / Singleton / State / Strategy / Observer
- **诊断核心链路**: 10个关键环节完整追踪
- **技术债务清单**: 19项 (P1:4, P2:12, P3:3), 修复成本~50h
- **V12架构分析报告**: `.trae/specs/v12-architecture-deep-analysis/V12_ARCHITECTURE_ANALYSIS_REPORT.md`

### 🗑️ 删除 (7个过时文档)
- `architecture/ARCHITECTURE_ANALYSIS_REPORT.md` — V7.0, 被V12报告取代
- `reports/DOCUMENT_MODIFICATION_REPORT.md` — V7.0, 文档标准化元文档
- `reports/MODIFICATION_MANUAL.md` — V7.0, 历史修改日志(引用Gradio等已弃用技术)
- `reports/PROJECT_PROGRESS.md` — V7.0, 停留在V6(引用不存在的目录)
- `reports/NEXT_STEPS.md` — V7.0, 描述不存在的功能(DeepStack/SE/LoRA)
- `reports/MULTIMODAL_FUSION_UPGRADE_REPORT.md` — V7.0, 描述理论/计划功能
- `reports/INTEGRATION_TEST_REPORT.md` — V7.0, 88测试用例(V10已有1102+)

### ✏️ 重写 (3个架构文档)
- `architecture/AGENT_ARCHITECTURE.md` — V7.0→V12.0: 移除EnvironmentAgent/SelfEvolution/LoRA/EventBus/UncertaintyLoss等不存在的功能, 新增诊断核心链路/5种设计模式/安全能力状态/技术债务
- `architecture/WEB_ARCHITECTURE.md` — V7.0→V12.0: 修正前端目录结构(store/→stores/)、移除ResNet/Celery/MinIO/WebSocket、修正JWT时间(24h→30min)、新增diagnosis_confidences/image_metadata/audit_logs表
- `reference/INFRASTRUCTURE_COMPONENTS.md` — V9.0→V12.0: 移除Celery/MinIO章节, 新增SSE流式响应/Redis缓存/GPU监控章节

### 📝 更新 (2个核心文档)
- `README.md` — 版本V9.0→V12.0, 测试数1113→1448, 移除MinIO/Celery引用, 更新项目历程V7-V12
- `CHANGELOG.md` — 新增V11.0和V12.0条目

### 📊 文档整理效果
| 指标 | V9整理后 | V12整理后 | 变化 |
|------|----------|----------|------|
| 文件总数 | **22** | **15** | ↓ **32%** |
| 架构文档准确性 | 多处描述不存在的功能 | 与V12代码库完全对齐 | ✅ |
| 技术栈描述 | 含Celery/MinIO/ResNet | 仅含实际使用的技术 | ✅ |

---

## [V11.0] - 2026-04-15 🧪 Web前端综合测试

### 🧪 测试执行
- **前端全量测试**: 346 用例, 通过率 **98.8%**
- **新增测试**: 257 个前端测试用例
- **覆盖模块**: 登录/注册/诊断/记录/知识库/用户管理/路由守卫

### 📊 测试报告
- V11_WEB_TEST_REPORT.md — `.trae/specs/v11-web-comprehensive-testing/`

---

## [V10.0] - 2026-04-15 🧪 前后端全系统完整测试

### 🧪 测试执行
- **后端全量测试**: 1102 用例, 通过率 **~99.4%** (3个P1级失败)
- **核心模块覆盖**: fusion_service / yolo_service / qwen_loader / security / rate_limiter / image_preprocessor — 全部通过 ✅
- **SSE 流式测试**: 27 用例, 24 通过 / 3 失败 (async generator 清理问题)

### 🐛 发现缺陷 (3个P1)
- BUG-001: SSE StreamManager 超时控制 — async generator 未处理 GeneratorExit
- BUG-002: SSE StreamManager 取消处理 — 同根因
- BUG-003: SSE 进度回调 — 主线程无 event loop

### 📊 测试报告
- V10_TEST_REPORT.md (9章节完整报告) — `.trae/specs/v10-full-system-testing/`

---

## [V9.0] - 2026-04-05 📁 文档目录系统性整理与冗余清理

### 🗑️ 删除 (9 个文件)
- **预先删除 (6个)**: TECHNICAL_AUDIT_OPTIMIZATION_REPORT / GRAPH_RAG_SPEC(归档) / ARCHITECTURE_TECHNICAL_AUDIT / ARCHITECTURE_DEVIATION_OPTIMIZATION / TEST_ENVIRONMENT / API_TEST_GUIDE
- **合并删除 (3个)**: CELERY_GUIDE + MINIO_GUIDE + SLOWAPI_GUIDE → 合并为 INFRASTRUCTURE_COMPONENTS.md

### 🔀 合并 (1 组执行)
- 组件三合一: `reference/INFRASTRUCTURE_COMPONENTS.md` (~620行)
  - 新增组件总览架构图 + 端口分配表
  - 新增组件间协作模式（完整诊断流程/Redis规划/Docker编排/故障排查速查）

### 📁 目录重组
```
docs/
├── README.md + CHANGELOG.md           # 根目录 (2个) ← 原扁平28文件
├── core/                              # 核心文档 (4个)
├── architecture/                      # 架构设计 (3个)
├── guides/                            # 操作指南 (4个)
├── reports/                           # 历史报告 (8个)
└── reference/                         # 参考资料 (1个, 合并产物)
```

### 📝 导航更新
- README.md 文档导航全面重写为子目录分类结构
- 所有内部链接路径更新为新相对路径 (`core/`, `architecture/` 等)
- 项目统计信息更新: 30→22 文件, V7.0→V9.0 版本

### 📊 整理效果
| 指标 | 整理前 | 整理后 | 变化 |
|------|--------|--------|------|
| 文件总数 | **30** | **22** | ↓ **27%** |
| 目录深度 | 1 (全扁平) | **3** (树形结构) | 结构化 |
| 零引用文件 | 13 个 | **5 个** | ↓ **62%** |
| S+A级占比 | 53% | **77%** | ↑ **24%** |

### 📋 备份记录
- DELETION_LOG.md 完整记录所有处置操作 (`.trae/specs/v9-docs-cleanup-reorganization/`)
- 可通过 Git 历史恢复任何被处置文件

---

## [V8.0] - 2026-04-05 🔍 架构审计与文档精炼

### 🆕 新增
- ARCHITECTURE_BASELINE_V8.md — 权威代码级架构基线（1537行，9章节+5附录）
- V8_DOCUMENT_AUDIT_MATRIX.md — 29文档×10维度完整审计矩阵
- V8_AUDIT_REPORT.md — 最终审计报告（本版本核心产出）

### 🔧 修正 (P0: 3项, P1: 7项)
- GRAPH_RAG_SPEC.md 版本升级 v1.0→V7.0 + 名称统一 + 归档标记
- 3个测试文档添加版本号标注 (TEST_GUIDE/TEST_ENVIRONMENT/API_TEST_GUIDE)
- 技术栈版本更新 (Vue^3.5.25/Element Plus^2.13.5/TypeScript~5.9.3/Vite^7.3.1)
- Node.js 版本要求 16.x+ → 18.x+
- 多模态融合报告/集成测试报告格式规范化
- Docker 24+/Kubernetes 1.28+/Nginx ≥1.24 版本补充
- NEXT_STEPS 新增维护阶段规划章节
- AGENT_ARCHITECTURE 新增认证与鉴权状态总览表

### 📚 内容补充 (~445行)
- ModelState 状态机完整详解 (+35行) → PROJECT_DOCUMENTATION.md
- PipelineTimer 性能计时器说明 (+60行) → PROJECT_DOCUMENTATION.md
- Facade 内部组件交互细节 (+95行) → AGENT_ARCHITECTURE.md
- SSE 事件时间序列与客户端解析指南 (+130行) → API_REFERENCE.md
- DiagnosisRequestValidator 验证流程增强 (+30行) → API_REFERENCE.md
- @deprecated 迁移策略完整指南 (+95行) → PROJECT_DOCUMENTATION.md

### 📦 归档 (1项)
- GRAPH_RAG_SPEC.md → 添加归档标记（保留原文，Cypher查询示例有技术参考价值）

### 📊 审计结果
- 审计范围: 29文档 × 10维度 = 290项检查 (100%覆盖率)
- 初始评级: A=12(41.4%) / B=11(37.9%) / C=5(17.2%) / D=1(3.5%)
- 修正后一致性: 名称100% / 版本≥89.7% / 技术≥93.1% / 综合≥96.5%
- 抽样复验: 5/5 = 100% 通过
- 评分变化: **93.8 → 94.0** (+0.2) 🎉

---

## [V7.0] - 2026-04-05 🎉 文档质量大提升

### 📝 新增
- README.md 重写为专业项目门户（徽章/架构图/5类导航）
- API_REFERENCE.md 重构为开发者友好文档（55端点/9功能域/速查表）
- PROJECT_DOCUMENTATION.md 升级为技术白皮书（9章/ER图/Facade详解）
- USER_GUIDE.md 重写为用户操作手册（5场景/20 FAQ/50术语对照）
- DEPLOYMENT.md 升级为生产部署指南（环境矩阵/30项检查清单/15故障排查）
- CHANGELOG.md 本文件（版本变更集中管理）

### 🔧 改进
- 28 个文档统一项目名称格式
- 17 个辅助文档头部格式标准化
- 6 个架构文档内容增强（决策流程图/序列图/查询示例）
- API 文档源码路径引用更新为 V6 实际结构

#### 架构文档增强详情
| 文档 | 增强内容 |
|------|---------|
| **AGENT_ARCHITECTURE.md** | 完整决策循环流程图 + SSEStreamManager位置标注 |
| **WEB_ARCHITECTURE.md** | 前后端交互时序图(14步) + SSE流数据流图 |
| **MULTIMODAL_FUSION_UPGRADE_REPORT.md** | V6 Facade重构/V7文档质量提升 追加记录 |
| **KAD_FORMER_GRAPHRAG_ARCHITECTURE_EXPLANATION.md** | 公式审查通过(LaTeX正确) + 版本至V7.0 |
| **GRAPH_RAG_SPEC.md** | 4个实际查询示例附录(Cypher+Python) |
| **ARCHITECTURE_ANALYSIS_REPORT.md** | 附录E: V7文档质量量化分析 |

### 🐛 修复
- 修正文档中的过时端点路径（缓存 API 统一为 /api/v1/cache/*）
- 修正部分端点的认证状态标注
- 清理文档间的交叉引用死链接

---

## [V6.0] - 2026-04-04 🔧 深度优化 + 文档同步

### 🆕 新增
- P0: QwenModelLoader.__new__() API 兼容性修复 (+8 测试)
- P1: 核心模块测试补充 (+107 测试用例，总计 1113+)
- P2: 代码质量审计报告 (@deprecated 清单/死代码报告)
- BASELINE_PERFORMANCE.md V6 更新记录

### 📝 文档同步 (28/28 文件)
- 核心 6 文件全面更新 (README/API_REF/PROJECT_DOC/AGENT_ARCH/WEB_ARCH/PROGRESS)
- 架构 8 文件同步 (含 DEPLOYMENT 新增 7 环境变量)
- 测试/运维 4 文件更新 (TEST_GUIDE 基准测试章节/MODIFICATION_MANUAL V4-V6 记录)
- 其余 11 文件审查修正 (100% 已更新)

### 📊 评分变化: 92.3 → **93.6** (+1.3)

---

## [V5.0] - 2026-04-04 🚀 深度优化

### 🆕 新增
- 异步迁移: @deprecated ×3 + diagnose_async() 全链路
- 类型注解: 12 模块 158 函数 = **100% 覆盖**
- 配置外部化: 7 配置项替换 9 处硬编码
- 测试基建: SQLAlchemy Index bug 修复 + 1006 测试基线
- 性能基准: benchmarks/ 目录 8 文件 + 9 项基线指标
- API 安全: 认证覆盖率 72.7% → **90.9%**

### 📊 评分变化: 89.8 → **92.3** (+2.5)

---

## [V4.0] - 2026-04-04 ⚡ 分析驱动优化

### 🆕 新增
- God File 消除: ai_diagnosis.py 2202行 → **54行** (-97.5%)
- Facade 重构: fusion_service.py 1268行 → **692行** (拆分 4 子模块)
- SSE 独立模块: sse_stream_manager.py (~450行)
- 诊断验证器: diagnosis_validator.py (~400行)
- 安全修复: 2 处认证缺失 + 认证去重

### 📊 评分变化: 86.5 → **89.8** (+3.3)

---

## [V3.0] - 2026-03-xx 🌾 初始版本

### 初始功能
- 基础 AI 诊断能力 (YOLOv8 + Qwen3-VL)
- 用户认证系统 (JWT)
- 诊断记录管理
- 知识库基础功能

### 📊 初始评分: **86.5**

---

*CHANGELOG 格式遵循 [Keep a Changelog](https://keepachangelog.com/) 规范*
*维护者: WheatAgent 文档工作组*
