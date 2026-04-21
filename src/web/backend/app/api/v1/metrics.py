"""
性能监控 API 端点

提供系统性能指标收集和监控：
1. 推理延迟（p50, p95, p99）
2. 吞吐量（req/s）
3. 错误率
4. 显存占用
5. 告警机制
"""

import logging
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from collections import deque
import statistics

from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["性能监控"])


class InferenceMetricsCollector:
    """推理性能指标收集器"""
    
    def __init__(self, window_size: int = 1000):
        """
        初始化指标收集器
        
        Args:
            window_size: 滑动窗口大小
        """
        self.window_size = window_size
        self._latencies: deque = deque(maxlen=window_size)
        self._requests: deque = deque(maxlen=window_size)
        self._errors: deque = deque(maxlen=window_size)
        self._gpu_memory: deque = deque(maxlen=100)
        self._start_time = time.time()
    
    def record_latency(self, latency_ms: float) -> None:
        """记录延迟"""
        self._latencies.append({
            "timestamp": time.time(),
            "value": latency_ms
        })
    
    def record_request(self, success: bool = True) -> None:
        """记录请求"""
        self._requests.append({
            "timestamp": time.time(),
            "success": success
        })
    
    def record_error(self, error_type: str) -> None:
        """记录错误"""
        self._errors.append({
            "timestamp": time.time(),
            "type": error_type
        })
    
    def record_gpu_memory(self, memory_mb: float, utilization: float) -> None:
        """记录 GPU 显存"""
        self._gpu_memory.append({
            "timestamp": time.time(),
            "memory_mb": memory_mb,
            "utilization": utilization
        })
    
    def get_latency_stats(self) -> Dict[str, float]:
        """获取延迟统计"""
        if not self._latencies:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0
            }
        
        values = [x["value"] for x in self._latencies]
        values.sort()
        
        count = len(values)
        return {
            "count": count,
            "avg": round(statistics.mean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "p50": round(values[int(count * 0.5)], 2),
            "p95": round(values[int(count * 0.95)] if count > 20 else values[-1], 2),
            "p99": round(values[int(count * 0.99)] if count > 100 else values[-1], 2)
        }
    
    def get_throughput(self, window_seconds: float = 60) -> float:
        """获取吞吐量（req/s）"""
        if not self._requests:
            return 0.0
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # 计算窗口内的请求数
        requests_in_window = sum(
            1 for x in self._requests 
            if x["timestamp"] >= window_start
        )
        
        return round(requests_in_window / window_seconds, 2)
    
    def get_error_rate(self, window_seconds: float = 300) -> Dict[str, float]:
        """获取错误率"""
        if not self._requests:
            return {
                "total_requests": 0,
                "total_errors": 0,
                "error_rate": 0.0
            }
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # 计算窗口内的请求和错误
        requests_in_window = [
            x for x in self._requests 
            if x["timestamp"] >= window_start
        ]
        
        errors_in_window = [
            x for x in self._errors 
            if x["timestamp"] >= window_start
        ]
        
        total = len(requests_in_window)
        failed = sum(1 for x in requests_in_window if not x["success"])
        
        return {
            "total_requests": total,
            "total_errors": len(errors_in_window),
            "failed_requests": failed,
            "error_rate": round(failed / total * 100 if total > 0 else 0, 2)
        }
    
    def get_gpu_memory_stats(self) -> Dict[str, Any]:
        """获取 GPU 显存统计"""
        if not self._gpu_memory:
            return {
                "current": None,
                "avg_utilization": 0,
                "max_utilization": 0
            }
        
        values = [x["utilization"] for x in self._gpu_memory]
        latest = self._gpu_memory[-1]
        
        return {
            "current": {
                "memory_mb": latest["memory_mb"],
                "utilization": latest["utilization"]
            },
            "avg_utilization": round(statistics.mean(values), 2),
            "max_utilization": round(max(values), 2)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        uptime = time.time() - self._start_time
        
        return {
            "uptime_seconds": round(uptime, 2),
            "latency": self.get_latency_stats(),
            "throughput": self.get_throughput(),
            "error_rate": self.get_error_rate(),
            "gpu_memory": self.get_gpu_memory_stats(),
            "total_requests": len(self._requests),
            "total_errors": len(self._errors)
        }


# 全局指标收集器实例
metrics_collector = InferenceMetricsCollector()


@router.get("/")
async def get_current_metrics(current_user: User = Depends(get_current_user)):
    """
    获取当前性能指标
    
    返回:
        延迟、吞吐量、错误率、GPU 显存等指标
    """
    try:
        metrics = metrics_collector.get_all_metrics()
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取性能指标失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败：{str(e)}")


@router.get("/latency")
async def get_latency_metrics(current_user: User = Depends(get_current_user)):
    """
    获取延迟指标
    
    返回:
        p50, p95, p99 延迟
    """
    try:
        latency = metrics_collector.get_latency_stats()
        
        return {
            "success": True,
            "data": {
                "latency_ms": latency,
                "performance_grade": _get_latency_grade(latency["p95"])
            }
        }
        
    except Exception as e:
        logger.error(f"获取延迟指标失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取延迟指标失败：{str(e)}")


@router.get("/throughput")
async def get_throughput_metrics(current_user: User = Depends(get_current_user)):
    """
    获取吞吐量指标
    
    返回:
        请求/秒
    """
    try:
        throughput = metrics_collector.get_throughput()
        error_rate = metrics_collector.get_error_rate()
        
        return {
            "success": True,
            "data": {
                "requests_per_second": throughput,
                "error_rate_percent": error_rate["error_rate"],
                "total_requests": error_rate["total_requests"]
            }
        }
        
    except Exception as e:
        logger.error(f"获取吞吐量指标失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取吞吐量指标失败：{str(e)}")


@router.get("/gpu")
async def get_gpu_metrics(current_user: User = Depends(get_current_user)):
    """
    获取 GPU 指标
    
    返回:
        GPU 显存占用、利用率
    """
    try:
        from app.services.batch_processor import get_batch_processor
        
        batch_processor = get_batch_processor()
        gpu_info = batch_processor.get_gpu_info()
        gpu_stats = metrics_collector.get_gpu_memory_stats()
        
        return {
            "success": True,
            "data": {
                "current": gpu_info,
                "history": gpu_stats
            }
        }
        
    except Exception as e:
        logger.error(f"获取 GPU 指标失败：{e}")
        return {
            "success": False,
            "data": {
                "available": False,
                "message": str(e)
            }
        }


@router.get("/alerts")
async def get_alerts(current_user: User = Depends(get_current_user)):
    """
    获取当前告警
    
    返回:
        延迟、错误率、GPU 显存告警状态
    """
    try:
        metrics = metrics_collector.get_all_metrics()
        alerts = []
        
        # 延迟告警
        p95_latency = metrics["latency"]["p95"]
        if p95_latency > 5000:  # > 5s
            alerts.append({
                "type": "high_latency",
                "severity": "critical",
                "message": f"P95 延迟过高：{p95_latency}ms",
                "threshold": 5000
            })
        elif p95_latency > 3000:  # > 3s
            alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"P95 延迟偏高：{p95_latency}ms",
                "threshold": 3000
            })
        
        # 错误率告警
        error_rate = metrics["error_rate"]["error_rate"]
        if error_rate > 10:  # > 10%
            alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"错误率过高：{error_rate}%",
                "threshold": 10
            })
        elif error_rate > 5:  # > 5%
            alerts.append({
                "type": "high_error_rate",
                "severity": "warning",
                "message": f"错误率偏高：{error_rate}%",
                "threshold": 5
            })
        
        # GPU 显存告警
        gpu_util = metrics["gpu_memory"]["current"]
        if gpu_util and gpu_util.get("utilization", 0) > 95:
            alerts.append({
                "type": "high_gpu_memory",
                "severity": "critical",
                "message": f"GPU 显存占用过高：{gpu_util['utilization']}%",
                "threshold": 95
            })
        elif gpu_util and gpu_util.get("utilization", 0) > 85:
            alerts.append({
                "type": "high_gpu_memory",
                "severity": "warning",
                "message": f"GPU 显存占用偏高：{gpu_util['utilization']}%",
                "threshold": 85
            })
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "alert_count": len(alerts),
                "health_status": "healthy" if not alerts else "degraded"
            }
        }
        
    except Exception as e:
        logger.error(f"获取告警失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取告警失败：{str(e)}")


@router.get("/history")
async def get_metrics_history(
    metric_type: str = "all",
    duration_minutes: int = 60,
    current_user: User = Depends(get_current_user)
):
    """
    获取指标历史数据
    
    参数:
        metric_type: 指标类型 (latency/throughput/gpu/all)
        duration_minutes: 历史时长（分钟）
        
    返回:
        历史指标数据
    """
    try:
        current_time = time.time()
        window_start = current_time - duration_minutes * 60
        
        result = {}
        
        if metric_type in ("latency", "all"):
            latencies_in_window = [
                x for x in metrics_collector._latencies
                if x["timestamp"] >= window_start
            ]
            latency_series = _aggregate_by_minute(latencies_in_window, "value")
            result["latency"] = {
                "timestamps": [t for t, _ in latency_series],
                "values": [v for _, v in latency_series]
            }
        
        if metric_type in ("throughput", "all"):
            requests_in_window = [
                x for x in metrics_collector._requests
                if x["timestamp"] >= window_start
            ]
            throughput_series = _aggregate_requests_by_minute(requests_in_window)
            result["throughput"] = {
                "timestamps": [t for t, _ in throughput_series],
                "values": [v for _, v in throughput_series]
            }
        
        if metric_type in ("gpu", "all"):
            gpu_in_window = [
                x for x in metrics_collector._gpu_memory
                if x["timestamp"] >= window_start
            ]
            gpu_series = _aggregate_by_minute(gpu_in_window, "memory_mb")
            result["gpu"] = {
                "timestamps": [t for t, _ in gpu_series],
                "values": [v for _, v in gpu_series]
            }
        
        return {
            "success": True,
            "data": result,
            "duration_minutes": duration_minutes
        }
        
    except Exception as e:
        logger.error(f"获取历史数据失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败：{str(e)}")


def _get_latency_grade(p95_latency: float) -> str:
    """根据 P95 延迟获取性能等级"""
    if p95_latency < 1000:
        return "excellent"
    elif p95_latency < 2000:
        return "good"
    elif p95_latency < 3000:
        return "fair"
    elif p95_latency < 5000:
        return "poor"
    else:
        return "critical"


def _aggregate_by_minute(data_points: list, value_key: str) -> list:
    """按分钟聚合数据点，计算每分钟平均值
    
    Args:
        data_points: 包含 timestamp 和 value_key 的数据点列表
        value_key: 要聚合的值键名
        
    Returns:
        [(timestamp_iso, avg_value), ...] 列表
    """
    if not data_points:
        return []
    
    buckets: Dict[int, list] = {}
    for point in data_points:
        minute_key = int(point["timestamp"] // 60)
        buckets.setdefault(minute_key, []).append(point[value_key])
    
    result = []
    for minute_key in sorted(buckets.keys()):
        values = buckets[minute_key]
        avg_value = round(sum(values) / len(values), 2)
        ts = datetime.fromtimestamp(minute_key * 60).isoformat()
        result.append((ts, avg_value))
    
    return result


def _aggregate_requests_by_minute(data_points: list) -> list:
    """按分钟聚合请求数据，计算每分钟请求计数
    
    Args:
        data_points: 包含 timestamp 和 success 的请求数据点列表
        
    Returns:
        [(timestamp_iso, count), ...] 列表
    """
    if not data_points:
        return []
    
    buckets: Dict[int, int] = {}
    for point in data_points:
        minute_key = int(point["timestamp"] // 60)
        buckets[minute_key] = buckets.get(minute_key, 0) + 1
    
    result = []
    for minute_key in sorted(buckets.keys()):
        ts = datetime.fromtimestamp(minute_key * 60).isoformat()
        result.append((ts, buckets[minute_key]))
    
    return result


def record_inference(latency_ms: float, success: bool = True) -> None:
    """记录推理性能指标"""
    metrics_collector.record_latency(latency_ms)
    metrics_collector.record_request(success)


def record_error(error_type: str) -> None:
    """记录错误"""
    metrics_collector.record_error(error_type)


def record_gpu_usage(memory_mb: float, utilization: float) -> None:
    """记录 GPU 使用"""
    metrics_collector.record_gpu_memory(memory_mb, utilization)
