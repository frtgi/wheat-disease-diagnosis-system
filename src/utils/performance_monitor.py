# -*- coding: utf-8 -*-
"""
性能监控模块

实现推理延迟监控、准确率追踪、资源监控和自动报告生成

文档参考: 8.3 性能评估指标
- 视觉检测 mAP@0.5 > 95%
- 语义生成 BLEU-4, ROUGE-L > 0.45
- 知识一致性 Consistency@k > 85%
- 推理效率 FPS > 30
"""
import os
import time
import json
import datetime
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class MetricType(Enum):
    """指标类型"""
    LATENCY = "latency"
    ACCURACY = "accuracy"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    GPU = "gpu"
    CUSTOM = "custom"


@dataclass
class MetricRecord:
    """指标记录"""
    timestamp: float
    value: float
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LatencyStats:
    """延迟统计"""
    count: int = 0
    total: float = 0.0
    min: float = float('inf')
    max: float = 0.0
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    @property
    def mean(self) -> float:
        """平均值"""
        if self.count == 0:
            return 0.0
        return self.total / self.count
    
    @property
    def p50(self) -> float:
        """P50延迟"""
        return self._percentile(50)
    
    @property
    def p95(self) -> float:
        """P95延迟"""
        return self._percentile(95)
    
    @property
    def p99(self) -> float:
        """P99延迟"""
        return self._percentile(99)
    
    def _percentile(self, p: int) -> float:
        """计算百分位数"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        idx = int(len(sorted_values) * p / 100)
        idx = min(idx, len(sorted_values) - 1)
        return sorted_values[idx]


class PerformanceMonitor:
    """
    性能监控器
    
    文档参考: 8.3 性能评估指标
    
    功能:
    1. 推理延迟监控 (P50/P95/P99)
    2. 准确率趋势追踪
    3. 资源使用监控 (CPU/GPU/内存)
    4. 自动性能报告生成
    """
    
    def __init__(
        self,
        name: str = "IWDDA",
        history_size: int = 1000,
        report_dir: str = "logs/performance"
    ):
        """
        初始化性能监控器
        
        :param name: 监控器名称
        :param history_size: 历史记录大小
        :param report_dir: 报告输出目录
        """
        self.name = name
        self.history_size = history_size
        self.report_dir = report_dir
        
        # 创建报告目录
        os.makedirs(report_dir, exist_ok=True)
        
        # 延迟统计
        self.latency_stats: Dict[str, LatencyStats] = {}
        
        # 准确率追踪
        self.accuracy_history: Dict[str, deque] = {}
        
        # 资源使用历史
        self.resource_history: Dict[str, deque] = {
            "cpu": deque(maxlen=history_size),
            "memory": deque(maxlen=history_size),
            "gpu_memory": deque(maxlen=history_size),
            "gpu_util": deque(maxlen=history_size)
        }
        
        # 自定义指标
        self.custom_metrics: Dict[str, List[MetricRecord]] = {}
        
        # 锁
        self._lock = threading.Lock()
        
        # 开始时间
        self.start_time = time.time()
        
        # FPS追踪
        self._frame_times: deque = deque(maxlen=100)
        self._last_frame_time = None
        
        print(f"📊 [PerformanceMonitor] 性能监控器已启动: {name}")
    
    def start_timer(self, operation: str) -> float:
        """
        开始计时
        
        :param operation: 操作名称
        :return: 开始时间戳
        """
        return time.time()
    
    def stop_timer(self, operation: str, start_time: float, tags: Dict[str, str] = None):
        """
        停止计时并记录延迟
        
        :param operation: 操作名称
        :param start_time: 开始时间戳
        :param tags: 标签
        """
        elapsed = (time.time() - start_time) * 1000  # 毫秒
        
        with self._lock:
            if operation not in self.latency_stats:
                self.latency_stats[operation] = LatencyStats()
            
            stats = self.latency_stats[operation]
            stats.count += 1
            stats.total += elapsed
            stats.min = min(stats.min, elapsed)
            stats.max = max(stats.max, elapsed)
            stats.values.append(elapsed)
    
    def record_latency(self, operation: str, latency_ms: float):
        """
        记录延迟
        
        :param operation: 操作名称
        :param latency_ms: 延迟(毫秒)
        """
        with self._lock:
            if operation not in self.latency_stats:
                self.latency_stats[operation] = LatencyStats()
            
            stats = self.latency_stats[operation]
            stats.count += 1
            stats.total += latency_ms
            stats.min = min(stats.min, latency_ms)
            stats.max = max(stats.max, latency_ms)
            stats.values.append(latency_ms)
    
    def record_accuracy(self, metric_name: str, value: float):
        """
        记录准确率
        
        :param metric_name: 指标名称
        :param value: 准确率值
        """
        with self._lock:
            if metric_name not in self.accuracy_history:
                self.accuracy_history[metric_name] = deque(maxlen=self.history_size)
            
            self.accuracy_history[metric_name].append({
                "timestamp": time.time(),
                "value": value
            })
    
    def record_fps(self):
        """记录帧率"""
        current_time = time.time()
        
        if self._last_frame_time is not None:
            self._frame_times.append(current_time - self._last_frame_time)
        
        self._last_frame_time = current_time
    
    def get_fps(self) -> float:
        """
        获取当前FPS
        
        :return: FPS值
        """
        if not self._frame_times:
            return 0.0
        
        avg_frame_time = statistics.mean(self._frame_times)
        if avg_frame_time == 0:
            return 0.0
        
        return 1.0 / avg_frame_time
    
    def record_resource_usage(self):
        """记录资源使用情况"""
        record = {
            "timestamp": time.time(),
            "cpu": 0.0,
            "memory": 0.0,
            "gpu_memory": 0.0,
            "gpu_util": 0.0
        }
        
        # CPU和内存
        if PSUTIL_AVAILABLE:
            record["cpu"] = psutil.cpu_percent()
            record["memory"] = psutil.virtual_memory().percent
        
        # GPU
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                record["gpu_memory"] = torch.cuda.memory_allocated() / 1024**3 * 100  # GB转百分比
                record["gpu_util"] = torch.cuda.utilization()
            except Exception:
                pass
        
        with self._lock:
            self.resource_history["cpu"].append(record["cpu"])
            self.resource_history["memory"].append(record["memory"])
            self.resource_history["gpu_memory"].append(record["gpu_memory"])
            self.resource_history["gpu_util"].append(record["gpu_util"])
        
        return record
    
    def record_custom_metric(
        self,
        metric_name: str,
        value: float,
        tags: Dict[str, str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        记录自定义指标
        
        :param metric_name: 指标名称
        :param value: 指标值
        :param tags: 标签
        :param metadata: 元数据
        """
        record = MetricRecord(
            timestamp=time.time(),
            value=value,
            metric_type=MetricType.CUSTOM,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            if metric_name not in self.custom_metrics:
                self.custom_metrics[metric_name] = []
            
            self.custom_metrics[metric_name].append(record)
            
            # 限制历史大小
            if len(self.custom_metrics[metric_name]) > self.history_size:
                self.custom_metrics[metric_name] = \
                    self.custom_metrics[metric_name][-self.history_size:]
    
    def get_latency_summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取延迟摘要
        
        :param operation: 操作名称(可选，None表示所有操作)
        :return: 延迟摘要
        """
        with self._lock:
            if operation:
                if operation not in self.latency_stats:
                    return {}
                
                stats = self.latency_stats[operation]
                return {
                    "operation": operation,
                    "count": stats.count,
                    "mean_ms": round(stats.mean, 2),
                    "min_ms": round(stats.min, 2) if stats.min != float('inf') else 0,
                    "max_ms": round(stats.max, 2),
                    "p50_ms": round(stats.p50, 2),
                    "p95_ms": round(stats.p95, 2),
                    "p99_ms": round(stats.p99, 2)
                }
            else:
                summary = {}
                for op, stats in self.latency_stats.items():
                    summary[op] = {
                        "count": stats.count,
                        "mean_ms": round(stats.mean, 2),
                        "p95_ms": round(stats.p95, 2),
                        "p99_ms": round(stats.p99, 2)
                    }
                return summary
    
    def get_accuracy_trend(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取准确率趋势
        
        :param metric_name: 指标名称(可选)
        :return: 准确率趋势
        """
        with self._lock:
            if metric_name:
                if metric_name not in self.accuracy_history:
                    return {}
                
                history = list(self.accuracy_history[metric_name])
                if not history:
                    return {}
                
                values = [h["value"] for h in history]
                return {
                    "metric_name": metric_name,
                    "count": len(values),
                    "current": values[-1],
                    "mean": round(statistics.mean(values), 4),
                    "trend": "up" if len(values) > 1 and values[-1] > values[-2] else "down"
                }
            else:
                trends = {}
                for name, history in self.accuracy_history.items():
                    values = [h["value"] for h in history]
                    if values:
                        trends[name] = {
                            "current": values[-1],
                            "mean": round(statistics.mean(values), 4)
                        }
                return trends
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        获取资源使用摘要
        
        :return: 资源摘要
        """
        with self._lock:
            summary = {}
            
            for resource_type, history in self.resource_history.items():
                if history:
                    values = list(history)
                    summary[resource_type] = {
                        "current": round(values[-1], 2),
                        "mean": round(statistics.mean(values), 2),
                        "max": round(max(values), 2)
                    }
            
            return summary
    
    def check_performance_targets(self) -> Dict[str, Any]:
        """
        检查性能目标
        
        文档参考: 8.3 性能评估指标
        
        :return: 性能检查结果
        """
        results = {
            "passed": True,
            "checks": []
        }
        
        # 检查FPS (目标 > 30)
        fps = self.get_fps()
        fps_check = {
            "name": "FPS",
            "target": "> 30",
            "current": round(fps, 2),
            "passed": fps > 30
        }
        results["checks"].append(fps_check)
        if not fps_check["passed"]:
            results["passed"] = False
        
        # 检查推理延迟 (目标 < 100ms)
        if "inference" in self.latency_stats:
            latency = self.latency_stats["inference"].mean
            latency_check = {
                "name": "推理延迟",
                "target": "< 100ms",
                "current": round(latency, 2),
                "passed": latency < 100
            }
            results["checks"].append(latency_check)
            if not latency_check["passed"]:
                results["passed"] = False
        
        # 检查准确率 (目标 > 85%)
        for metric_name, history in self.accuracy_history.items():
            if history:
                current = list(history)[-1]["value"]
                acc_check = {
                    "name": f"准确率({metric_name})",
                    "target": "> 85%",
                    "current": round(current * 100, 2),
                    "passed": current > 0.85
                }
                results["checks"].append(acc_check)
                if not acc_check["passed"]:
                    results["passed"] = False
        
        return results
    
    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成性能报告
        
        :param output_path: 输出路径(可选)
        :return: 报告数据
        """
        report = {
            "monitor_name": self.name,
            "generated_at": datetime.datetime.now().isoformat(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "latency": self.get_latency_summary(),
            "accuracy": self.get_accuracy_trend(),
            "resources": self.get_resource_summary(),
            "fps": round(self.get_fps(), 2),
            "performance_targets": self.check_performance_targets()
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 [性能报告] 已保存到: {output_path}")
        
        return report
    
    def print_summary(self):
        """打印性能摘要"""
        print(f"\n{'='*60}")
        print(f"📊 性能监控摘要 - {self.name}")
        print(f"{'='*60}")
        
        # FPS
        print(f"\n🚀 帧率 (FPS): {self.get_fps():.2f}")
        
        # 延迟
        print(f"\n⏱️ 延迟统计:")
        latency_summary = self.get_latency_summary()
        for op, stats in latency_summary.items():
            print(f"   {op}:")
            print(f"      平均: {stats['mean_ms']:.2f}ms")
            print(f"      P95: {stats['p95_ms']:.2f}ms")
            print(f"      P99: {stats['p99_ms']:.2f}ms")
        
        # 准确率
        print(f"\n📈 准确率趋势:")
        accuracy_trends = self.get_accuracy_trend()
        for name, trend in accuracy_trends.items():
            print(f"   {name}: {trend['current']*100:.2f}% (趋势: {trend['trend']})")
        
        # 资源
        print(f"\n💻 资源使用:")
        resources = self.get_resource_summary()
        for resource, stats in resources.items():
            print(f"   {resource}: {stats['current']:.1f}% (平均: {stats['mean']:.1f}%)")
        
        # 性能目标
        print(f"\n🎯 性能目标检查:")
        target_results = self.check_performance_targets()
        for check in target_results["checks"]:
            status = "✅" if check["passed"] else "❌"
            print(f"   {status} {check['name']}: {check['current']} (目标: {check['target']})")
        
        print(f"{'='*60}")
    
    def reset(self):
        """重置所有统计数据"""
        with self._lock:
            self.latency_stats.clear()
            self.accuracy_history.clear()
            for key in self.resource_history:
                self.resource_history[key].clear()
            self.custom_metrics.clear()
            self._frame_times.clear()
            self._last_frame_time = None
            self.start_time = time.time()
        
        print(f"📊 [PerformanceMonitor] 统计数据已重置")


# 装饰器：自动计时
def timed(monitor: PerformanceMonitor, operation: str):
    """
    计时装饰器
    
    :param monitor: 性能监控器
    :param operation: 操作名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = monitor.start_timer(operation)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.stop_timer(operation, start_time)
        return wrapper
    return decorator


# 全局监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor
