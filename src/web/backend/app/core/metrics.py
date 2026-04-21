"""
性能指标收集模块
提供请求性能监控和指标收集功能
"""
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timezone
from collections import defaultdict
import threading

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestMetricsCollector:
    """
    请求性能指标收集器
    
    收集和存储应用请求性能指标
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化指标收集器
        """
        if self._initialized:
            return
        
        self._initialized = True
        self._request_count: Dict[str, int] = defaultdict(int)
        self._request_latency: Dict[str, list] = defaultdict(list)
        self._error_count: Dict[str, int] = defaultdict(int)
        self._diagnosis_count: Dict[str, int] = defaultdict(int)
        self._active_requests = 0
        self._max_active_requests = 0
        self._start_time = datetime.now(timezone.utc)
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        latency: float
    ) -> None:
        """
        记录请求指标
        
        Args:
            method: HTTP 方法
            endpoint: 端点路径
            status_code: HTTP 状态码
            latency: 响应延迟（秒）
        """
        key = f"{method}:{endpoint}"
        self._request_count[key] += 1
        self._request_latency[key].append(latency)
        
        if len(self._request_latency[key]) > 1000:
            self._request_latency[key] = self._request_latency[key][-500:]
        
        if status_code >= 400:
            self._error_count[key] += 1
    
    def record_diagnosis(self, disease_name: str, success: bool) -> None:
        """
        记录诊断指标
        
        Args:
            disease_name: 病害名称
            success: 是否成功
        """
        key = f"diagnosis:{disease_name}"
        self._diagnosis_count[key] += 1
    
    def increment_active_requests(self) -> None:
        """增加活跃请求数"""
        self._active_requests += 1
        self._max_active_requests = max(
            self._max_active_requests,
            self._active_requests
        )
    
    def decrement_active_requests(self) -> None:
        """减少活跃请求数"""
        self._active_requests = max(0, self._active_requests - 1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标
        
        Returns:
            指标字典
        """
        total_requests = sum(self._request_count.values())
        total_errors = sum(self._error_count.values())
        
        avg_latencies = {}
        for key, latencies in self._request_latency.items():
            if latencies:
                avg_latencies[key] = {
                    "avg": sum(latencies) / len(latencies),
                    "min": min(latencies),
                    "max": max(latencies),
                    "count": len(latencies)
                }
        
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "active_requests": self._active_requests,
            "max_active_requests": self._max_active_requests,
            "request_count": dict(self._request_count),
            "error_count": dict(self._error_count),
            "diagnosis_count": dict(self._diagnosis_count),
            "latency_stats": avg_latencies
        }
    
    def reset(self) -> None:
        """重置所有指标"""
        self._request_count.clear()
        self._request_latency.clear()
        self._error_count.clear()
        self._diagnosis_count.clear()
        self._active_requests = 0
        self._max_active_requests = 0
        self._start_time = datetime.now(timezone.utc)


metrics_collector = RequestMetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    性能指标中间件
    
    自动收集每个请求的性能指标
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并收集指标
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        metrics_collector.increment_active_requests()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            latency = time.time() - start_time
            
            endpoint = request.url.path
            if request.url.path.startswith("/api/v1/"):
                endpoint = request.url.path[7:]
            
            metrics_collector.record_request(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
                latency=latency
            )
            
            response.headers["X-Response-Time"] = f"{latency:.3f}s"
            
            return response
            
        except Exception as e:
            latency = time.time() - start_time
            
            metrics_collector.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                latency=latency
            )
            
            raise
            
        finally:
            metrics_collector.decrement_active_requests()


def track_performance(func_name: Optional[str] = None):
    """
    性能追踪装饰器
    
    用于追踪函数执行时间
    
    Args:
        func_name: 函数名称（可选）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start_time
                logger.debug(f"{name} 执行完成，耗时：{latency:.3f}s")
                return result
            except Exception as e:
                latency = time.time() - start_time
                logger.error(f"{name} 执行失败，耗时：{latency:.3f}s，错误：{e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                logger.debug(f"{name} 执行完成，耗时：{latency:.3f}s")
                return result
            except Exception as e:
                latency = time.time() - start_time
                logger.error(f"{name} 执行失败，耗时：{latency:.3f}s，错误：{e}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
