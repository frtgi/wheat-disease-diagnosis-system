"""
性能监控模块

提供全面的系统性能监控、告警和报告功能

模块组成:
- metrics_collector: 监控指标收集器
- alert_manager: 告警管理器
- monitoring_api: 监控 API 接口

功能特性:
1. API 响应时间监控
2. 缓存命中率监控
3. 系统资源监控 (CPU、内存、GPU)
4. 性能阈值检测
5. 告警通知
6. 性能报告生成
"""

from .metrics_collector import (
    MetricsCollector,
    CacheMetrics,
    APIMetrics,
    SystemMetrics,
    get_metrics_collector
)

from .alert_manager import (
    AlertManager,
    AlertLevel,
    AlertRule,
    get_alert_manager
)

__all__ = [
    "MetricsCollector",
    "CacheMetrics",
    "APIMetrics",
    "SystemMetrics",
    "get_metrics_collector",
    "AlertManager",
    "AlertLevel",
    "AlertRule",
    "get_alert_manager"
]

__version__ = "1.0.0"
