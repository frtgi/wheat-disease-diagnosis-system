# 基础设施组件指南

> **版本**: V12.0
> **更新日期**: 2026-04-16
> **基于**: V12 架构深度分析报告
> **适用项目**: 基于多模态融合的小麦病害诊断系统

---

## 一、组件总览与依赖关系

本项目使用以下关键基础设施组件支撑诊断系统的流式响应、缓存、限流和GPU管理：

```
┌─────────────────────────────────────────────────────────────┐
│                    WheatAgent 诊断系统                        │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  FastAPI  │◄──►│  Redis   │    │  Neo4j   │              │
│  │  (API层)  │    │(缓存/限流)│    │(知识图谱) │              │
│  └────┬─────┘    └──────────┘    └──────────┘              │
│       │                                                    │
│       ▼                                                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  SSE流式  │    │ SlowAPI  │    │ GPU监控  │              │
│  │ (响应推送)│    │ (限流保护)│    │(显存管理) │              │
│  └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### 组件依赖关系

| 组件 | 作用 | 依赖 | 被依赖方 |
|------|------|------|---------|
| **Redis** | 缓存/黑名单/限流计数 | 无 | SlowAPI, JWT黑名单, DiagnosisRateLimiter |
| **Neo4j** | 知识图谱存储 | 无 | GraphRAGService |
| **SSE** | 流式响应推送 | FastAPI | ai_diagnosis.py |
| **SlowAPI** | API频率限流 | Redis(可选) | 所有API端点 |
| **DiagnosisRateLimiter** | 诊断并发限流 | Redis | ai_diagnosis.py |
| **GPUMonitor** | GPU显存监控 | nvidia-smi | ai_diagnosis.py |

### 端口分配

| 组件 | 端口 | 用途 |
|------|------|------|
| FastAPI | 8000 | 后端API服务 |
| Redis | 6379 | 缓存/黑名单/限流计数 |
| MySQL | 3306 | 业务数据存储 |
| Neo4j HTTP | 7474 | 知识图谱管理界面 |
| Neo4j Bolt | 7687 | 知识图谱Cypher查询 |

---

## 二、SSE 流式响应

### 2.1 概述

本项目使用 **Server-Sent Events (SSE)** 实现诊断过程的实时进度推送，替代传统轮询模式。SSE基于HTTP长连接，服务端可单向推送事件到客户端。

### 2.2 架构说明

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │ ──→ │  SSE Event      │ ──→ │  Vue3 前端      │
│  diagnose_async │     │  Generator      │     │  EventSource    │
│  (AsyncGenerator)│    │  (text/event-   │     │  (事件监听)      │
│                 │     │   stream)       │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 2.3 事件类型体系

| 事件类型 | 触发时机 | 数据内容 | 前端处理 |
|----------|---------|---------|---------|
| `start` | 诊断开始 | diagnosis_id | 初始化进度条 |
| `progress` | 各阶段完成 | step, progress%, message | 更新进度条 |
| `heartbeat` | 每15秒 | 空 | 重置超时计时器 |
| `log` | 关键日志 | level, message | 显示日志面板 |
| `step_indicator` | 阶段切换 | current_step, total_steps | 更新步骤指示器 |
| `complete` | 诊断完成 | 完整诊断结果 | 渲染融合结果 |
| `error` | 发生错误 | error_code, message | 显示错误提示 |

### 2.4 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 心跳间隔 | 15秒 | 防止代理/CDN超时断连 |
| 诊断超时 | 120秒 | 整体诊断时间上限 |
| 背压队列 | 100 | 事件缓冲区大小 |
| Content-Type | text/event-stream | SSE标准MIME类型 |

### 2.5 使用示例

```python
@router.post("/diagnosis/multimodal")
async def diagnose_multimodal_stream(request: Request, ...):
    """SSE流式诊断端点"""
    async def event_generator():
        async for event in fusion_service.diagnose_async(image, symptoms):
            yield f"event: {event.type}\ndata: {event.json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

### 2.6 最佳实践

1. **心跳保活**: 每15秒发送heartbeat事件，防止中间代理超时
2. **背压控制**: 使用asyncio.Queue(100)缓冲事件，防止消费者慢导致内存溢出
3. **超时处理**: 设置120秒整体超时，避免无限等待
4. **错误恢复**: 客户端EventSource自动重连，最多3次

---

## 三、Redis 缓存

### 3.1 概述

Redis在本项目中承担多种角色：JWT Token黑名单、诊断结果缓存、知识图谱缓存、限流计数器和并发信号量。

### 3.2 数据规划

| 数据类型 | 用途 | Key模式 | TTL |
|---------|------|---------|-----|
| Set | JWT Token黑名单 | `blacklist:token:{jti}` | 30分钟 |
| String | 诊断结果缓存 | `diagnosis:{image_hash}` | 7天 |
| String | 病害知识缓存 | `knowledge:disease:{id}` | 30天 |
| String | 限流计数器 | `rate-limit:{ip}:{endpoint}` | 60秒 |
| String | 并发诊断计数 | `concurrent:diagnosis` | 5分钟 |

### 3.3 配置说明

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
```

### 3.4 使用示例

#### JWT Token黑名单

```python
async def revoke_token(jti: str, exp: int):
    """将Token加入黑名单"""
    ttl = exp - int(time.time())
    if ttl > 0:
        await redis.setex(f"blacklist:token:{jti}", ttl, "1")

async def is_token_revoked(jti: str) -> bool:
    """检查Token是否已被撤销"""
    return await redis.exists(f"blacklist:token:{jti}")
```

#### 诊断结果缓存

```python
async def cache_diagnosis_result(image_hash: str, result: dict):
    """缓存诊断结果"""
    await redis.setex(
        f"diagnosis:{image_hash}",
        7 * 24 * 3600,
        json.dumps(result)
    )
```

### 3.5 最佳实践

1. **Key命名规范**: 使用冒号分隔的层级命名空间
2. **TTL设置**: 所有Key必须设置过期时间，防止内存泄漏
3. **连接池**: 使用连接池管理Redis连接
4. **序列化**: 统一使用JSON序列化

---

## 四、SlowAPI 限流

### 4.1 概述

SlowAPI是基于令牌桶算法的API限流库，用于保护API免受滥用。本项目使用SlowAPI进行频率限流，配合DiagnosisRateLimiter进行并发限流。

### 4.2 双层限流架构

```
客户端请求 → SlowAPI(频率限流) → FastAPI(业务处理)
                                        ↓
                              DiagnosisRateLimiter(并发≤3)
                                        ↓
                                   等待队列(≤10)
                                        ↓
                                      Redis(计数存储)
```

### 4.3 限流策略

| 端点类型 | 频率限流 | 并发限流 | 说明 |
|---------|---------|---------|------|
| 用户注册 | 3次/分钟 | - | 防止恶意批量注册 |
| 用户登录 | 5次/分钟 | - | 防止暴力破解 |
| 文件上传 | 10次/分钟 | - | 控制存储压力 |
| 诊断接口 | 20次/分钟 | ≤3并发 | GPU资源保护 |
| 一般查询 | 60次/分钟 | - | 默认限流 |

### 4.4 配置说明

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_DIAGNOSIS=20/minute
RATE_LIMIT_UPLOAD=10/minute
MAX_CONCURRENT_DIAGNOSIS=3
MAX_DIAGNOSIS_QUEUE_SIZE=10
GPU_MEMORY_THRESHOLD=0.9
```

### 4.5 使用示例

#### 频率限流

```python
@router.post("/diagnosis/multimodal")
@limiter.limit("20/minute")
async def diagnose(request: Request, ...):
    pass
```

#### 并发限流

```python
from app.core.rate_limiter import get_diagnosis_rate_limiter

rate_limiter = get_diagnosis_rate_limiter()

acquired = await rate_limiter.acquire(
    DiagnosisRequest(request_id=uuid4(), user_id=user.id)
)
if not acquired:
    raise HTTPException(status_code=429, detail="诊断服务繁忙")
try:
    result = await fusion_service.diagnose_async(...)
finally:
    await rate_limiter.release(request_id)
```

### 4.6 GPU降级策略

```
GPU显存使用率 < 90% → 正常接受诊断请求
GPU显存使用率 ≥ 90% → 返回 503 "计算资源繁忙"
nvidia-smi 不可用   → 仅做并发限流（跳过显存检查）
并发数已达上限(3)    → 返回 429 "服务器繁忙，已加入队列"
队列已满(10)        → 返回 429 "服务器繁忙，请稍后重试"
```

### 4.7 最佳实践

1. **区分用户类型**: 认证用户和匿名用户使用不同限流规则
2. **区分接口类型**: 读接口和写接口使用不同限流规则
3. **GPU保护**: 显存过载时自动降级，保护系统稳定
4. **生产环境必须启用限流**
5. **监控限流触发频率，识别异常行为**

---

## 五、GPU 监控

### 5.1 概述

GPU监控模块通过nvidia-smi获取GPU显存使用情况，在显存过载时拒绝新的诊断请求，防止OOM崩溃。

### 5.2 核心功能

```python
class GPUMonitor:
    async def get_memory_usage(self) -> Optional[float]:
        """获取GPU显存使用率(0.0-1.0)"""

    async def is_overloaded(self, threshold: float = 0.9) -> bool:
        """检查GPU是否过载"""

    async def get_gpu_info(self) -> Dict:
        """获取GPU详细信息"""
```

### 5.3 使用方式

```python
gpu_monitor = GPUMonitor()

if await gpu_monitor.is_overloaded(threshold=0.9):
    raise HTTPException(status_code=503, detail="计算资源繁忙，请稍后重试")
```

---

## 六、组件间协作模式

### 6.1 典型诊断请求流程

```
用户上传图像
    ↓
[SlowAPI] 频率限制检查 (20次/分钟) ✅ 通过
    ↓
[FastAPI] JWT认证 + 请求校验
    ↓
[GPUMonitor] GPU显存检查 (<90%) ✅ 通过
    ↓
[DiagnosisRateLimiter] 并发许可获取 (≤3) ✅ 获取成功
    ↓
[SSE] 创建流式连接 → 返回 text/event-stream
    ↓
[FusionService] 执行诊断:
    ├── SSE: progress {step: "visual", progress: 100}
    ├── SSE: progress {step: "cognition", progress: 100}
    ├── SSE: progress {step: "knowledge", progress: 100}
    ├── SSE: progress {step: "fusion", progress: 100}
    └── SSE: complete {data: {诊断结果}}
    ↓
[DiagnosisRateLimiter] 释放许可
    ↓
[MySQL] 持久化诊断记录
    ↓
[Redis] 缓存诊断结果(可选)
```

### 6.2 Docker Compose 完整编排参考

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: ["redis_data:/data"]

  mysql:
    image: mysql:8.0
    ports: ["3306:3306"]
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: wheat_agent
    volumes: ["mysql_data:/var/lib/mysql"]

  neo4j:
    image: neo4j:5.x
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/password
    volumes: ["neo4j_data:/data"]

  backend:
    build: ./src/web/backend
    ports: ["8000:8000"]
    depends_on: [redis, mysql, neo4j]
    environment:
      DATABASE_URL: mysql+pymysql://root:rootpassword@mysql:3306/wheat_agent
      REDIS_URL: redis://redis:6379/0
      NEO4J_URI: bolt://neo4j:7687
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]

  frontend:
    build: ./src/web/frontend
    ports: ["5173:5173"]
    depends_on: [backend]

volumes:
  redis_data:
  mysql_data:
  neo4j_data:
```

### 6.3 故障排查速查

| 症状 | 可能原因 | 检查方式 | 解决方案 |
|------|---------|---------|---------|
| SSE断连 | 心跳超时 | 检查heartbeat间隔 | 确保每15秒发送心跳 |
| 429错误过多 | 限流阈值过低 | 查看X-RateLimit响应头 | 调整RATE_LIMIT_*配置 |
| 503错误 | GPU显存过载 | nvidia-smi检查显存 | 等待释放或降低并发上限 |
| Redis连接失败 | Redis未启动 | redis-cli ping | 启动Redis服务 |
| Neo4j查询慢 | 索引缺失 | Neo4j Browser检查 | 添加节点/关系索引 |
| Token验证失败 | 黑名单误判 | 检查Redis黑名单Key | 确认TTL设置正确 |

---

*文档更新时间：2026-04-16*
*版本：V12.0 (基于V12架构深度分析报告重写，移除Celery/MinIO)*
