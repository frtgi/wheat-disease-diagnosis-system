"""
监控模块功能测试脚本

测试监控模块的核心功能
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.monitoring import (
    get_metrics_collector,
    get_alert_manager,
    AlertLevel,
    AlertRule
)


def test_metrics_collector():
    """
    测试指标收集器功能
    """
    print("=" * 60)
    print("测试指标收集器")
    print("=" * 60)
    
    collector = get_metrics_collector()
    
    print("\n1. 测试 API 指标记录")
    collector.record_api_request(
        endpoint="/api/v1/diagnosis",
        method="POST",
        status_code=200,
        latency_ms=150.5
    )
    collector.record_api_request(
        endpoint="/api/v1/diagnosis",
        method="POST",
        status_code=200,
        latency_ms=200.3
    )
    collector.record_api_request(
        endpoint="/api/v1/diagnosis",
        method="POST",
        status_code=500,
        latency_ms=300.0
    )
    
    api_metrics = collector.get_api_metrics()
    print(f"   API 指标: {api_metrics}")
    
    print("\n2. 测试缓存指标记录")
    collector.record_cache_operation("diagnosis_cache", hit=True)
    collector.record_cache_operation("diagnosis_cache", hit=True)
    collector.record_cache_operation("diagnosis_cache", hit=False)
    collector.update_cache_size("diagnosis_cache", size=500, max_size=1000)
    
    cache_metrics = collector.get_cache_metrics()
    print(f"   缓存指标: {cache_metrics}")
    
    print("\n3. 测试系统指标收集")
    system_metrics = collector.collect_system_metrics()
    print(f"   CPU 使用率: {system_metrics.cpu_percent}%")
    print(f"   内存使用率: {system_metrics.memory_percent}%")
    print(f"   GPU 可用: {system_metrics.gpu_available}")
    
    print("\n4. 测试综合指标获取")
    all_metrics = collector.get_all_metrics()
    print(f"   运行时间: {all_metrics['uptime_human']}")
    print(f"   API 端点数: {len(all_metrics['api_metrics'])}")
    print(f"   缓存数: {len(all_metrics['cache_metrics'])}")
    
    print("\n5. 测试性能摘要")
    summary = collector.get_performance_summary()
    print(f"   API 总请求数: {summary['api']['total_requests']}")
    print(f"   缓存平均命中率: {summary['cache']['avg_hit_rate']}%")
    
    print("\n✅ 指标收集器测试通过")


def test_alert_manager():
    """
    测试告警管理器功能
    """
    print("\n" + "=" * 60)
    print("测试告警管理器")
    print("=" * 60)
    
    alert_manager = get_alert_manager()
    
    print("\n1. 测试默认告警规则")
    rules = alert_manager.get_rules()
    print(f"   默认规则数量: {len(rules)}")
    for rule in rules[:3]:
        print(f"   - {rule['name']}: {rule['metric_name']} {rule['comparison']} {rule['threshold']}")
    
    print("\n2. 测试添加自定义规则")
    custom_rule = AlertRule(
        name="test_custom_alert",
        metric_name="test_metric",
        threshold=100.0,
        comparison="gt",
        level=AlertLevel.WARNING,
        message_template="测试告警: {value} > {threshold}"
    )
    alert_manager.add_rule(custom_rule)
    print(f"   已添加自定义规则: {custom_rule.name}")
    
    print("\n3. 测试告警触发")
    alerts = alert_manager.check_metric("test_metric", 150.0)
    if alerts:
        print(f"   触发告警: {alerts[0].message}")
        print(f"   告警级别: {alerts[0].level.value}")
    
    print("\n4. 测试活跃告警")
    active_alerts = alert_manager.get_active_alerts()
    print(f"   活跃告警数量: {len(active_alerts)}")
    
    print("\n5. 测试健康状态")
    health = alert_manager.get_health_status()
    print(f"   健康状态: {health['status']}")
    print(f"   状态消息: {health['message']}")
    print(f"   活跃告警数: {health['active_alerts_count']}")
    
    print("\n6. 测试告警确认")
    if active_alerts:
        alert_manager.acknowledge_alert(active_alerts[0]["rule_name"])
        print(f"   已确认告警: {active_alerts[0]['rule_name']}")
    
    print("\n7. 测试清除告警")
    alert_manager.clear_alerts()
    active_alerts_after = alert_manager.get_active_alerts()
    print(f"   清除后活跃告警数量: {len(active_alerts_after)}")
    
    print("\n✅ 告警管理器测试通过")


def test_integration():
    """
    测试指标收集器和告警管理器的集成
    """
    print("\n" + "=" * 60)
    print("测试集成功能")
    print("=" * 60)
    
    collector = get_metrics_collector()
    alert_manager = get_alert_manager()
    
    print("\n1. 收集系统指标并检查告警")
    system_metrics = collector.collect_system_metrics()
    
    alerts = alert_manager.check_metrics({
        "cpu_percent": system_metrics.cpu_percent,
        "memory_percent": system_metrics.memory_percent,
        "gpu_memory_percent": (
            system_metrics.gpu_memory_used_mb / 
            max(system_metrics.gpu_memory_total_mb, 1) * 100
        ) if system_metrics.gpu_available else 0,
        "gpu_temperature": system_metrics.gpu_temperature
    })
    
    print(f"   触发的告警数: {len(alerts)}")
    for alert in alerts:
        print(f"   - [{alert.level.value}] {alert.message}")
    
    print("\n2. 获取综合报告")
    all_metrics = collector.get_all_metrics()
    health_status = alert_manager.get_health_status()
    
    print(f"   系统运行时间: {all_metrics['uptime_human']}")
    print(f"   系统健康状态: {health_status['status']}")
    print(f"   CPU 使用率: {all_metrics['system_metrics']['cpu_percent']}%")
    print(f"   内存使用率: {all_metrics['system_metrics']['memory_percent']}%")
    
    print("\n✅ 集成测试通过")


def main():
    """
    主测试函数
    """
    print("\n" + "=" * 60)
    print("监控模块功能测试")
    print("=" * 60)
    
    try:
        test_metrics_collector()
        test_alert_manager()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
