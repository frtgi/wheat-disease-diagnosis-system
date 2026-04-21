"""
监控指标收集器模块

提供全面的性能指标收集功能:
1. API 响应时间监控
2. 缓存命中率监控
3. 系统资源监控 (CPU、内存、GPU)
"""
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
import statistics

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil 未安装，系统资源监控功能受限")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class APIMetrics:
    """
    API 性能指标数据类

    记录 API 请求的响应时间、状态码等信息
    """
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    request_size: int = 0
    response_size: int = 0
    error_message: Optional[str] = None


@dataclass
class CacheMetrics:
    """
    缓存性能指标数据类

    记录缓存命中率、访问次数等信息
    """
    cache_name: str
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def hit_rate(self) -> float:
        """
        计算缓存命中率

        返回:
            命中率 (0.0 - 1.0)
        """
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """
        计算缓存未命中率

        返回:
            未命中率 (0.0 - 1.0)
        """
        return 1.0 - self.hit_rate

    @property
    def utilization(self) -> float:
        """
        计算缓存利用率

        返回:
            利用率 (0.0 - 1.0)
        """
        if self.max_size == 0:
            return 0.0
        return self.size / self.max_size


@dataclass
class SystemMetrics:
    """
    系统资源指标数据类

    记录 CPU、内存、GPU 等系统资源使用情况
    """
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    gpu_available: bool = False
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    gpu_utilization: float = 0.0
    gpu_temperature: int = 0
    gpu_power_draw: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        返回:
            字典格式的系统指标
        """
        return {
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_percent": round(self.memory_percent, 2),
            "memory_used_mb": round(self.memory_used_mb, 2),
            "memory_total_mb": round(self.memory_total_mb, 2),
            "gpu_available": self.gpu_available,
            "gpu_memory_used_mb": round(self.gpu_memory_used_mb, 2),
            "gpu_memory_total_mb": round(self.gpu_memory_total_mb, 2),
            "gpu_utilization": round(self.gpu_utilization, 2),
            "gpu_temperature": self.gpu_temperature,
            "gpu_power_draw": round(self.gpu_power_draw, 2),
            "timestamp": self.timestamp
        }


class MetricsCollector:
    """
    监控指标收集器

    收集和管理各类性能指标，包括:
    - API 响应时间
    - 缓存命中率
    - 系统资源使用情况

    采用单例模式确保全局唯一实例
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        单例模式实现

        返回:
            MetricsCollector 实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, history_size: int = 1000):
        """
        初始化指标收集器

        参数:
            history_size: 历史记录大小
        """
        if self._initialized:
            return

        self._initialized = True
        self.history_size = history_size

        self._api_metrics: Dict[str, deque] = {}
        self._cache_metrics: Dict[str, CacheMetrics] = {}
        self._system_metrics_history: deque = deque(maxlen=history_size)

        self._api_latency_stats: Dict[str, Dict[str, Any]] = {}

        self._start_time = datetime.now(timezone.utc)
        self._metrics_lock = threading.Lock()

        logger.info("监控指标收集器已初始化")

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        request_size: int = 0,
        response_size: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """
        记录 API 请求指标

        参数:
            endpoint: API 端点路径
            method: HTTP 方法
            status_code: HTTP 状态码
            latency_ms: 响应延迟（毫秒）
            request_size: 请求大小（字节）
            response_size: 响应大小（字节）
            error_message: 错误信息（可选）
        """
        metric = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            request_size=request_size,
            response_size=response_size,
            error_message=error_message
        )

        key = f"{method}:{endpoint}"

        with self._metrics_lock:
            if key not in self._api_metrics:
                self._api_metrics[key] = deque(maxlen=self.history_size)

            self._api_metrics[key].append(metric)

            if key not in self._api_latency_stats:
                self._api_latency_stats[key] = {
                    "count": 0,
                    "total_latency": 0.0,
                    "min_latency": float('inf'),
                    "max_latency": 0.0,
                    "error_count": 0,
                    "latencies": deque(maxlen=self.history_size)
                }

            stats = self._api_latency_stats[key]
            stats["count"] += 1
            stats["total_latency"] += latency_ms
            stats["min_latency"] = min(stats["min_latency"], latency_ms)
            stats["max_latency"] = max(stats["max_latency"], latency_ms)
            stats["latencies"].append(latency_ms)

            if status_code >= 400:
                stats["error_count"] += 1

    def record_cache_operation(
        self,
        cache_name: str,
        hit: bool,
        eviction: bool = False
    ) -> None:
        """
        记录缓存操作

        参数:
            cache_name: 缓存名称
            hit: 是否命中
            eviction: 是否发生驱逐
        """
        with self._metrics_lock:
            if cache_name not in self._cache_metrics:
                self._cache_metrics[cache_name] = CacheMetrics(cache_name=cache_name)

            metrics = self._cache_metrics[cache_name]
            metrics.total_requests += 1

            if hit:
                metrics.hits += 1
            else:
                metrics.misses += 1

            if eviction:
                metrics.evictions += 1

    def update_cache_size(
        self,
        cache_name: str,
        size: int,
        max_size: int
    ) -> None:
        """
        更新缓存大小信息

        参数:
            cache_name: 缓存名称
            size: 当前大小
            max_size: 最大大小
        """
        with self._metrics_lock:
            if cache_name not in self._cache_metrics:
                self._cache_metrics[cache_name] = CacheMetrics(cache_name=cache_name)

            self._cache_metrics[cache_name].size = size
            self._cache_metrics[cache_name].max_size = max_size

    def collect_system_metrics(self) -> SystemMetrics:
        """
        收集系统资源指标

        返回:
            SystemMetrics 实例
        """
        metrics = SystemMetrics()

        if PSUTIL_AVAILABLE:
            try:
                metrics.cpu_percent = psutil.cpu_percent(interval=0.1)

                mem = psutil.virtual_memory()
                metrics.memory_percent = mem.percent
                metrics.memory_used_mb = mem.used / (1024 ** 2)
                metrics.memory_total_mb = mem.total / (1024 ** 2)
            except Exception as e:
                logger.debug(f"收集系统指标失败: {e}")

        if TORCH_AVAILABLE:
            try:
                if torch.cuda.is_available():
                    metrics.gpu_available = True

                    device = torch.cuda.current_device()
                    metrics.gpu_memory_used_mb = torch.cuda.memory_allocated(device) / (1024 ** 2)
                    metrics.gpu_memory_total_mb = torch.cuda.get_device_properties(device).total_memory / (1024 ** 2)

                    try:
                        import pynvml
                        pynvml.nvmlInit()
                        handle = pynvml.nvmlDeviceGetHandleByIndex(device)

                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        metrics.gpu_utilization = util.gpu

                        metrics.gpu_temperature = pynvml.nvmlDeviceGetTemperature(
                            handle, pynvml.NVML_TEMPERATURE_GPU
                        )

                        metrics.gpu_power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0

                        pynvml.nvmlShutdown()
                    except ImportError:
                        logger.debug("pynvml 未安装，GPU 详细指标不可用")
                    except Exception as e:
                        logger.debug(f"获取 GPU 详细指标失败: {e}")
            except Exception as e:
                logger.debug(f"收集 GPU 指标失败: {e}")

        with self._metrics_lock:
            self._system_metrics_history.append(metrics)

        return metrics

    def get_api_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 API 指标统计

        参数:
            endpoint: 特定端点（可选），None 表示所有端点

        返回:
            API 指标统计字典
        """
        with self._metrics_lock:
            if endpoint:
                stats = self._api_latency_stats.get(endpoint, {})
                if not stats:
                    return {}

                latencies = list(stats.get("latencies", []))
                if not latencies:
                    return {
                        "endpoint": endpoint,
                        "count": stats["count"],
                        "error_count": stats["error_count"],
                        "error_rate": 0.0
                    }

                sorted_latencies = sorted(latencies)
                count = len(sorted_latencies)

                return {
                    "endpoint": endpoint,
                    "count": stats["count"],
                    "avg_latency_ms": round(stats["total_latency"] / stats["count"], 2),
                    "min_latency_ms": round(stats["min_latency"], 2),
                    "max_latency_ms": round(stats["max_latency"], 2),
                    "p50_latency_ms": round(sorted_latencies[int(count * 0.5)], 2),
                    "p95_latency_ms": round(sorted_latencies[int(count * 0.95)], 2),
                    "p99_latency_ms": round(sorted_latencies[int(count * 0.99)], 2),
                    "error_count": stats["error_count"],
                    "error_rate": round(stats["error_count"] / stats["count"] * 100, 2)
                }
            else:
                result = {}
                for key, stats in self._api_latency_stats.items():
                    latencies = list(stats.get("latencies", []))
                    if not latencies:
                        continue

                    sorted_latencies = sorted(latencies)
                    count = len(sorted_latencies)

                    result[key] = {
                        "count": stats["count"],
                        "avg_latency_ms": round(stats["total_latency"] / stats["count"], 2),
                        "p50_latency_ms": round(sorted_latencies[int(count * 0.5)], 2),
                        "p95_latency_ms": round(sorted_latencies[int(count * 0.95)], 2),
                        "p99_latency_ms": round(sorted_latencies[int(count * 0.99)], 2),
                        "error_rate": round(stats["error_count"] / stats["count"] * 100, 2)
                    }

                return result

    def get_cache_metrics(self, cache_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取缓存指标

        参数:
            cache_name: 特定缓存名称（可选），None 表示所有缓存

        返回:
            缓存指标字典
        """
        with self._metrics_lock:
            if cache_name:
                metrics = self._cache_metrics.get(cache_name)
                if not metrics:
                    return {}

                return {
                    "cache_name": metrics.cache_name,
                    "hits": metrics.hits,
                    "misses": metrics.misses,
                    "total_requests": metrics.total_requests,
                    "hit_rate": round(metrics.hit_rate * 100, 2),
                    "miss_rate": round(metrics.miss_rate * 100, 2),
                    "evictions": metrics.evictions,
                    "size": metrics.size,
                    "max_size": metrics.max_size,
                    "utilization": round(metrics.utilization * 100, 2)
                }
            else:
                result = {}
                for name, metrics in self._cache_metrics.items():
                    result[name] = {
                        "hits": metrics.hits,
                        "misses": metrics.misses,
                        "total_requests": metrics.total_requests,
                        "hit_rate": round(metrics.hit_rate * 100, 2),
                        "miss_rate": round(metrics.miss_rate * 100, 2),
                        "evictions": metrics.evictions,
                        "size": metrics.size,
                        "max_size": metrics.max_size,
                        "utilization": round(metrics.utilization * 100, 2)
                    }

                return result

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        获取最新的系统指标

        返回:
            系统指标字典
        """
        with self._metrics_lock:
            if not self._system_metrics_history:
                return SystemMetrics().to_dict()

            latest = self._system_metrics_history[-1]
            return latest.to_dict()

    def get_system_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取系统指标历史记录

        参数:
            limit: 返回记录数量限制

        返回:
            系统指标历史列表
        """
        with self._metrics_lock:
            history = list(self._system_metrics_history)[-limit:]
            return [m.to_dict() for m in history]

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标的综合报告

        返回:
            包含所有指标的综合字典
        """
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_human": self._format_uptime(uptime),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_metrics": self.get_api_metrics(),
            "cache_metrics": self.get_cache_metrics(),
            "system_metrics": self.get_system_metrics()
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        返回:
            性能摘要字典
        """
        api_metrics = self.get_api_metrics()
        cache_metrics = self.get_cache_metrics()
        system_metrics = self.get_system_metrics()

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api": {
                "total_endpoints": len(api_metrics),
                "total_requests": sum(m.get("count", 0) for m in api_metrics.values()),
                "avg_error_rate": 0.0,
                "slowest_endpoints": []
            },
            "cache": {
                "total_caches": len(cache_metrics),
                "avg_hit_rate": 0.0,
                "total_requests": 0
            },
            "system": system_metrics
        }

        if api_metrics:
            error_rates = [m.get("error_rate", 0) for m in api_metrics.values()]
            summary["api"]["avg_error_rate"] = round(statistics.mean(error_rates), 2)

            sorted_by_latency = sorted(
                api_metrics.items(),
                key=lambda x: x[1].get("p95_latency_ms", 0),
                reverse=True
            )
            summary["api"]["slowest_endpoints"] = [
                {"endpoint": k, "p95_latency_ms": v.get("p95_latency_ms", 0)}
                for k, v in sorted_by_latency[:5]
            ]

        if cache_metrics:
            hit_rates = [m.get("hit_rate", 0) for m in cache_metrics.values()]
            summary["cache"]["avg_hit_rate"] = round(statistics.mean(hit_rates), 2)
            summary["cache"]["total_requests"] = sum(
                m.get("total_requests", 0) for m in cache_metrics.values()
            )

        return summary

    def reset(self) -> None:
        """
        重置所有指标
        """
        with self._metrics_lock:
            self._api_metrics.clear()
            self._cache_metrics.clear()
            self._system_metrics_history.clear()
            self._api_latency_stats.clear()
            self._start_time = datetime.now(timezone.utc)

        logger.info("所有监控指标已重置")

    def _format_uptime(self, seconds: float) -> str:
        """
        格式化运行时间

        参数:
            seconds: 秒数

        返回:
            格式化的时间字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    获取全局指标收集器实例

    返回:
        MetricsCollector 实例
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
