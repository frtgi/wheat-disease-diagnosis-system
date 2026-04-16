# 性能监控模块文档

## 概述

性能监控模块提供全面的系统性能监控、告警和报告功能，帮助开发者实时了解系统运行状态，及时发现和解决性能问题。

## 模块组成

### 1. 监控指标收集器 (metrics_collector.py)

负责收集和管理各类性能指标，包括：

#### API 响应时间监控

- 记录每个 API 请求的响应时间
- 计算延迟统计指标（P50、P95、P99）
- 跟踪错误率和请求计数

```python
from app.monitoring import get_metrics_collector

collector = get_metrics_collector()

# 记录 API 请求
collector.record_api_request(
    endpoint="/api/v1/diagnosis",
    method="POST",
    status_code=200,
    latency_ms=150.5
)

# 获取 API 指标
api_metrics = collector.get_api_metrics()
```

#### 缓存命中率监控

- 跟踪缓存命中和未命中次数
- 计算缓存命中率
- 监控缓存驱逐和大小

```python
# 记录缓存操作
collector.record_cache_operation(
    cache_name="diagnosis_cache",
    hit=True
)

# 更新缓存大小
collector.update_cache_size(
    cache_name="diagnosis_cache",
    size=500,
    max_size=1000
)

# 获取缓存指标
cache_metrics = collector.get_cache_metrics()
```

#### 系统资源监控

- CPU 使用率
- 内存使用率
- GPU 显存使用情况
- GPU 利用率和温度

```python
# 收集系统指标
system_metrics = collector.collect_system_metrics()

# 获取系统指标历史
history = collector.get_system_metrics_history(limit=100)
```

### 2. 告警管理器 (alert_manager.py)

提供性能阈值检测和告警通知功能：

#### 默认告警规则

| 规则名称 | 指标 | 阈值 | 级别 |
|---------|------|------|------|
| high_api_latency | API P95 延迟 | > 3000ms | WARNING |
| critical_api_latency | API P95 延迟 | > 5000ms | CRITICAL |
| high_error_rate | API 错误率 | > 5% | WARNING |
| critical_error_rate | API 错误率 | > 10% | CRITICAL |
| low_cache_hit_rate | 缓存命中率 | < 50% | WARNING |
| high_cpu_usage | CPU 使用率 | > 80% | WARNING |
| critical_cpu_usage | CPU 使用率 | > 95% | CRITICAL |
| high_memory_usage | 内存使用率 | > 85% | WARNING |
| critical_memory_usage | 内存使用率 | > 95% | CRITICAL |
| high_gpu_memory_usage | GPU 显存使用率 | > 85% | WARNING |
| critical_gpu_memory_usage | GPU 显存使用率 | > 95% | CRITICAL |
| high_gpu_temperature | GPU 温度 | > 85°C | WARNING |

#### 使用示例

```python
from app.monitoring import get_alert_manager, AlertRule, AlertLevel

alert_manager = get_alert_manager()

# 添加自定义告警规则
custom_rule = AlertRule(
    name="custom_latency_alert",
    metric_name="api_latency_p95",
    threshold=2000.0,
    comparison="gt",
    level=AlertLevel.WARNING,
    message_template="自定义延迟告警: {value}ms"
)
alert_manager.add_rule(custom_rule)

# 检查指标
alerts = alert_manager.check_metric("api_latency_p95", 2500.0)

# 获取活跃告警
active_alerts = alert_manager.get_active_alerts()

# 获取健康状态
health = alert_manager.get_health_status()
```

### 3. 监控 API 接口 (monitoring_api.py)

提供 REST API 接口用于查询监控数据和性能报告：

#### API 端点

##### 健康检查

```
GET /monitoring/health
```

返回系统健康状态，包括运行时间、活跃告警数量和各项检查状态。

##### 获取监控数据

```
GET /monitoring/metrics?metric_type=all
```

参数：
- `metric_type`: 指标类型（all, api, cache, system）

##### 获取特定 API 端点指标

```
GET /monitoring/metrics/api/{endpoint}
```

##### 获取特定缓存指标

```
GET /monitoring/metrics/cache/{cache_name}
```

##### 获取性能报告

```
GET /monitoring/report
```

返回综合性能报告，包括性能摘要、健康状态、活跃告警和优化建议。

##### 获取告警信息

```
GET /monitoring/alerts?include_history=false&history_limit=100
```

参数：
- `include_history`: 是否包含历史告警
- `history_limit`: 历史告警数量限制

##### 确认告警

```
POST /monitoring/alerts/{rule_name}/acknowledge
```

##### 清除所有告警

```
POST /monitoring/alerts/clear
```

##### 获取告警规则

```
GET /monitoring/alerts/rules
```

##### 手动收集系统指标

```
POST /monitoring/collect
```

##### 重置所有监控指标

```
POST /monitoring/reset
```

## 集成指南

### 1. 在 FastAPI 应用中注册监控路由

```python
from fastapi import FastAPI
from app.monitoring.monitoring_api import include_router

app = FastAPI()

# 注册监控路由
include_router(app)
```

### 2. 在中间件中记录 API 指标

```python
from fastapi import Request
from app.monitoring import get_metrics_collector
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    collector = get_metrics_collector()
    
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000
    
    collector.record_api_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        latency_ms=latency_ms
    )
    
    return response
```

### 3. 在缓存操作中记录指标

```python
from app.monitoring import get_metrics_collector

class CacheService:
    def __init__(self):
        self.collector = get_metrics_collector()
        self.cache_name = "my_cache"
    
    def get(self, key):
        value = self._get_from_cache(key)
        hit = value is not None
        self.collector.record_cache_operation(
            cache_name=self.cache_name,
            hit=hit
        )
        return value
```

### 4. 定期收集系统指标

```python
import asyncio
from app.monitoring import get_metrics_collector, get_alert_manager

async def collect_system_metrics_periodically():
    collector = get_metrics_collector()
    alert_manager = get_alert_manager()
    
    while True:
        # 收集系统指标
        metrics = collector.collect_system_metrics()
        
        # 检查告警
        alert_manager.check_metrics({
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "gpu_memory_percent": (
                metrics.gpu_memory_used_mb / 
                max(metrics.gpu_memory_total_mb, 1) * 100
            ),
            "gpu_temperature": metrics.gpu_temperature
        })
        
        # 每 60 秒收集一次
        await asyncio.sleep(60)

# 在应用启动时运行
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(collect_system_metrics_periodically())
```

## 性能指标说明

### API 指标

- **count**: 请求总数
- **avg_latency_ms**: 平均延迟（毫秒）
- **min_latency_ms**: 最小延迟
- **max_latency_ms**: 最大延迟
- **p50_latency_ms**: P50 延迟（50% 的请求延迟低于此值）
- **p95_latency_ms**: P95 延迟（95% 的请求延迟低于此值）
- **p99_latency_ms**: P99 延迟（99% 的请求延迟低于此值）
- **error_count**: 错误请求数
- **error_rate**: 错误率（%）

### 缓存指标

- **hits**: 缓存命中次数
- **misses**: 缓存未命中次数
- **total_requests**: 总请求次数
- **hit_rate**: 命中率（%）
- **miss_rate**: 未命中率（%）
- **evictions**: 驱逐次数
- **size**: 当前缓存大小
- **max_size**: 最大缓存大小
- **utilization**: 缓存利用率（%）

### 系统指标

- **cpu_percent**: CPU 使用率（%）
- **memory_percent**: 内存使用率（%）
- **memory_used_mb**: 已用内存（MB）
- **memory_total_mb**: 总内存（MB）
- **gpu_available**: GPU 是否可用
- **gpu_memory_used_mb**: GPU 已用显存（MB）
- **gpu_memory_total_mb**: GPU 总显存（MB）
- **gpu_utilization**: GPU 利用率（%）
- **gpu_temperature**: GPU 温度（°C）
- **gpu_power_draw**: GPU 功耗（W）

## 最佳实践

### 1. 合理设置告警阈值

根据业务需求和系统容量设置合理的告警阈值：
- 避免阈值过低导致频繁告警
- 避免阈值过高导致错过重要问题
- 为不同环境（开发、测试、生产）设置不同阈值

### 2. 定期审查告警规则

- 定期检查告警规则的有效性
- 移除不再适用的规则
- 根据系统变化调整阈值

### 3. 监控数据保留策略

- 设置合理的历史数据保留期限
- 定期清理过期的监控数据
- 对重要指标进行持久化存储

### 4. 性能优化建议

- 关注 P95 和 P99 延迟，而非仅关注平均值
- 监控缓存命中率，优化缓存策略
- 关注系统资源使用趋势，提前规划扩容

## 故障排查

### 监控数据不准确

1. 检查是否正确调用了记录方法
2. 确认指标收集器已正确初始化
3. 查看日志中是否有错误信息

### 告警未触发

1. 检查告警规则是否启用
2. 确认指标值是否达到阈值
3. 检查告警冷却时间是否已过

### 性能影响

1. 监控模块使用单例模式，避免重复初始化
2. 指标收集使用异步方式，不影响主业务性能
3. 历史数据使用 deque 限制大小，避免内存泄漏

## 版本历史

### v1.0.0 (2026-04-02)

- 初始版本发布
- 实现 API 响应时间监控
- 实现缓存性能监控
- 实现系统资源监控
- 实现告警机制
- 实现监控 API 接口
