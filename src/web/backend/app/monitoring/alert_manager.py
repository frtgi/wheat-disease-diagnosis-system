"""
告警管理器模块

提供性能阈值检测和告警通知功能:
1. 性能阈值配置
2. 阈值检测逻辑
3. 告警通知功能（日志记录）
"""
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """
    告警级别枚举

    定义不同严重程度的告警级别
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def __lt__(self, other):
        """
        比较告警级别

        参数:
            other: 另一个告警级别

        返回:
            是否小于另一个级别
        """
        levels = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }
        return levels[self] < levels[other]

    def __le__(self, other):
        """
        比较告警级别

        参数:
            other: 另一个告警级别

        返回:
            是否小于等于另一个级别
        """
        levels = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }
        return levels[self] <= levels[other]


@dataclass
class AlertRule:
    """
    告警规则数据类

    定义单个告警规则的配置
    """
    name: str
    metric_name: str
    threshold: float
    comparison: str  # "gt", "lt", "gte", "lte", "eq"
    level: AlertLevel
    message_template: str
    enabled: bool = True
    cooldown_seconds: int = 300  # 告警冷却时间
    tags: Dict[str, str] = field(default_factory=dict)

    def check(self, value: float) -> bool:
        """
        检查值是否触发告警

        参数:
            value: 当前值

        返回:
            是否触发告警
        """
        if not self.enabled:
            return False

        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "gte":
            return value >= self.threshold
        elif self.comparison == "lte":
            return value <= self.threshold
        elif self.comparison == "eq":
            return value == self.threshold

        return False

    def format_message(self, value: float) -> str:
        """
        格式化告警消息

        参数:
            value: 当前值

        返回:
            格式化的消息
        """
        return self.message_template.format(
            metric_name=self.metric_name,
            value=round(value, 2),
            threshold=self.threshold
        )


@dataclass
class Alert:
    """
    告警数据类

    记录单个告警事件
    """
    rule_name: str
    metric_name: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        返回:
            字典格式的告警
        """
        return {
            "rule_name": self.rule_name,
            "metric_name": self.metric_name,
            "level": self.level.value,
            "message": self.message,
            "value": round(self.value, 2),
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "timestamp_human": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "tags": self.tags
        }

    def resolve(self) -> None:
        """
        标记告警为已解决
        """
        self.resolved = True
        self.resolved_at = time.time()


class AlertManager:
    """
    告警管理器

    管理告警规则、检测阈值、发送告警通知

    功能:
    1. 配置和管理告警规则
    2. 定期检测性能指标
    3. 发送告警通知（日志记录）
    4. 管理告警状态（确认、解决）

    采用单例模式确保全局唯一实例
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        单例模式实现

        返回:
            AlertManager 实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_alerts: int = 1000):
        """
        初始化告警管理器

        参数:
            max_alerts: 最大告警记录数
        """
        if self._initialized:
            return

        self._initialized = True
        self.max_alerts = max_alerts

        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=max_alerts)
        self._last_alert_time: Dict[str, float] = {}

        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._alert_lock = threading.Lock()

        self._init_default_rules()

        logger.info("告警管理器已初始化")

    def _init_default_rules(self) -> None:
        """
        初始化默认告警规则
        """
        default_rules = [
            AlertRule(
                name="high_api_latency",
                metric_name="api_latency_p95",
                threshold=3000.0,
                comparison="gt",
                level=AlertLevel.WARNING,
                message_template="API P95 延迟过高: {value}ms (阈值: {threshold}ms)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="critical_api_latency",
                metric_name="api_latency_p95",
                threshold=5000.0,
                comparison="gt",
                level=AlertLevel.CRITICAL,
                message_template="API P95 延迟严重过高: {value}ms (阈值: {threshold}ms)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="api_error_rate",
                threshold=5.0,
                comparison="gt",
                level=AlertLevel.WARNING,
                message_template="API 错误率过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="critical_error_rate",
                metric_name="api_error_rate",
                threshold=10.0,
                comparison="gt",
                level=AlertLevel.CRITICAL,
                message_template="API 错误率严重过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="low_cache_hit_rate",
                metric_name="cache_hit_rate",
                threshold=50.0,
                comparison="lt",
                level=AlertLevel.WARNING,
                message_template="缓存命中率过低: {value}% (阈值: {threshold}%)",
                cooldown_seconds=600
            ),
            AlertRule(
                name="high_cpu_usage",
                metric_name="cpu_percent",
                threshold=80.0,
                comparison="gt",
                level=AlertLevel.WARNING,
                message_template="CPU 使用率过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="critical_cpu_usage",
                metric_name="cpu_percent",
                threshold=95.0,
                comparison="gt",
                level=AlertLevel.CRITICAL,
                message_template="CPU 使用率严重过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="memory_percent",
                threshold=85.0,
                comparison="gt",
                level=AlertLevel.WARNING,
                message_template="内存使用率过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="critical_memory_usage",
                metric_name="memory_percent",
                threshold=95.0,
                comparison="gt",
                level=AlertLevel.CRITICAL,
                message_template="内存使用率严重过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="high_gpu_memory_usage",
                metric_name="gpu_memory_percent",
                threshold=85.0,
                comparison="gt",
                level=AlertLevel.WARNING,
                message_template="GPU 显存使用率过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="critical_gpu_memory_usage",
                metric_name="gpu_memory_percent",
                threshold=95.0,
                comparison="gt",
                level=AlertLevel.CRITICAL,
                message_template="GPU 显存使用率严重过高: {value}% (阈值: {threshold}%)",
                cooldown_seconds=300
            ),
            AlertRule(
                name="high_gpu_temperature",
                metric_name="gpu_temperature",
                threshold=85,
                comparison="gt",
                level=AlertLevel.WARNING,
                message_template="GPU 温度过高: {value}°C (阈值: {threshold}°C)",
                cooldown_seconds=300
            )
        ]

        for rule in default_rules:
            self._rules[rule.name] = rule

    def add_rule(self, rule: AlertRule) -> None:
        """
        添加告警规则

        参数:
            rule: 告警规则
        """
        with self._alert_lock:
            self._rules[rule.name] = rule
            logger.info(f"已添加告警规则: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """
        移除告警规则

        参数:
            rule_name: 规则名称

        返回:
            是否成功移除
        """
        with self._alert_lock:
            if rule_name in self._rules:
                del self._rules[rule_name]
                logger.info(f"已移除告警规则: {rule_name}")
                return True
            return False

    def enable_rule(self, rule_name: str) -> bool:
        """
        启用告警规则

        参数:
            rule_name: 规则名称

        返回:
            是否成功启用
        """
        with self._alert_lock:
            if rule_name in self._rules:
                self._rules[rule_name].enabled = True
                logger.info(f"已启用告警规则: {rule_name}")
                return True
            return False

    def disable_rule(self, rule_name: str) -> bool:
        """
        禁用告警规则

        参数:
            rule_name: 规则名称

        返回:
            是否成功禁用
        """
        with self._alert_lock:
            if rule_name in self._rules:
                self._rules[rule_name].enabled = False
                logger.info(f"已禁用告警规则: {rule_name}")
                return True
            return False

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        添加告警处理器

        参数:
            handler: 告警处理函数
        """
        with self._alert_lock:
            self._alert_handlers.append(handler)
            logger.info("已添加告警处理器")

    def check_metric(self, metric_name: str, value: float) -> List[Alert]:
        """
        检查指标是否触发告警

        参数:
            metric_name: 指标名称
            value: 指标值

        返回:
            触发的告警列表
        """
        triggered_alerts = []

        with self._alert_lock:
            for rule in self._rules.values():
                if rule.metric_name != metric_name:
                    continue

                if not rule.enabled:
                    continue

                if not rule.check(value):
                    if rule.name in self._active_alerts:
                        self._resolve_alert(rule.name)
                    continue

                last_alert = self._last_alert_time.get(rule.name, 0)
                if time.time() - last_alert < rule.cooldown_seconds:
                    continue

                alert = Alert(
                    rule_name=rule.name,
                    metric_name=metric_name,
                    level=rule.level,
                    message=rule.format_message(value),
                    value=value,
                    threshold=rule.threshold,
                    tags=rule.tags
                )

                self._active_alerts[rule.name] = alert
                self._alert_history.append(alert)
                self._last_alert_time[rule.name] = time.time()

                triggered_alerts.append(alert)

                self._notify_handlers(alert)

        return triggered_alerts

    def check_metrics(self, metrics: Dict[str, float]) -> List[Alert]:
        """
        批量检查指标

        参数:
            metrics: 指标字典 {metric_name: value}

        返回:
            触发的告警列表
        """
        all_alerts = []

        for metric_name, value in metrics.items():
            alerts = self.check_metric(metric_name, value)
            all_alerts.extend(alerts)

        return all_alerts

    def _notify_handlers(self, alert: Alert) -> None:
        """
        通知所有告警处理器

        参数:
            alert: 告警对象
        """
        self._log_alert(alert)

        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")

    def _log_alert(self, alert: Alert) -> None:
        """
        记录告警日志

        参数:
            alert: 告警对象
        """
        log_msg = f"[{alert.level.value.upper()}] {alert.message}"

        if alert.level == AlertLevel.CRITICAL:
            logger.critical(log_msg)
        elif alert.level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif alert.level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def _resolve_alert(self, rule_name: str) -> None:
        """
        解决告警

        参数:
            rule_name: 规则名称
        """
        if rule_name in self._active_alerts:
            alert = self._active_alerts[rule_name]
            alert.resolve()

            resolved_alert = Alert(
                rule_name=rule_name,
                metric_name=alert.metric_name,
                level=AlertLevel.INFO,
                message=f"告警已解决: {alert.message}",
                value=alert.value,
                threshold=alert.threshold
            )

            self._alert_history.append(resolved_alert)
            del self._active_alerts[rule_name]

            logger.info(f"告警已解决: {rule_name}")

    def acknowledge_alert(self, rule_name: str) -> bool:
        """
        确认告警

        参数:
            rule_name: 规则名称

        返回:
            是否成功确认
        """
        with self._alert_lock:
            if rule_name in self._active_alerts:
                self._active_alerts[rule_name].acknowledged = True
                logger.info(f"告警已确认: {rule_name}")
                return True
            return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        获取活跃告警

        返回:
            活跃告警列表
        """
        with self._alert_lock:
            return [alert.to_dict() for alert in self._active_alerts.values()]

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取告警历史

        参数:
            limit: 返回记录数量限制

        返回:
            告警历史列表
        """
        with self._alert_lock:
            history = list(self._alert_history)[-limit:]
            return [alert.to_dict() for alert in history]

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        获取所有告警规则

        返回:
            告警规则列表
        """
        with self._alert_lock:
            return [
                {
                    "name": rule.name,
                    "metric_name": rule.metric_name,
                    "threshold": rule.threshold,
                    "comparison": rule.comparison,
                    "level": rule.level.value,
                    "enabled": rule.enabled,
                    "cooldown_seconds": rule.cooldown_seconds,
                    "message_template": rule.message_template
                }
                for rule in self._rules.values()
            ]

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取系统健康状态

        返回:
            健康状态字典
        """
        with self._alert_lock:
            active_alerts = list(self._active_alerts.values())

            if not active_alerts:
                return {
                    "status": "healthy",
                    "message": "系统运行正常",
                    "active_alerts_count": 0,
                    "highest_level": None
                }

            highest_level = max(alert.level for alert in active_alerts)

            if highest_level == AlertLevel.CRITICAL:
                status = "critical"
                message = "系统存在严重问题"
            elif highest_level == AlertLevel.ERROR:
                status = "error"
                message = "系统存在错误"
            elif highest_level == AlertLevel.WARNING:
                status = "warning"
                message = "系统存在警告"
            else:
                status = "info"
                message = "系统运行正常，存在信息提示"

            return {
                "status": status,
                "message": message,
                "active_alerts_count": len(active_alerts),
                "highest_level": highest_level.value,
                "alerts_by_level": {
                    level.value: sum(1 for a in active_alerts if a.level == level)
                    for level in AlertLevel
                }
            }

    def clear_alerts(self) -> None:
        """
        清除所有活跃告警
        """
        with self._alert_lock:
            for rule_name in list(self._active_alerts.keys()):
                self._resolve_alert(rule_name)

        logger.info("已清除所有活跃告警")

    def reset(self) -> None:
        """
        重置告警管理器
        """
        with self._alert_lock:
            self._active_alerts.clear()
            self._alert_history.clear()
            self._last_alert_time.clear()

        logger.info("告警管理器已重置")


_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    获取全局告警管理器实例

    返回:
        AlertManager 实例
    """
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager
