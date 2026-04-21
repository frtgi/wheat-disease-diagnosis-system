"""
监控 API 接口模块

提供监控数据查询和性能报告的 REST API:
1. 获取监控数据接口
2. 获取性能报告接口
3. 健康检查接口
4. 告警管理接口
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .metrics_collector import get_metrics_collector
from .alert_manager import get_alert_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["性能监控"])


class HealthCheckResponse(BaseModel):
    """
    健康检查响应模型
    """
    status: str = Field(..., description="健康状态: healthy, warning, error, critical")
    message: str = Field(..., description="状态消息")
    timestamp: str = Field(..., description="时间戳")
    uptime_seconds: float = Field(..., description="运行时间（秒）")
    active_alerts_count: int = Field(..., description="活跃告警数量")
    checks: Dict[str, Any] = Field(default_factory=dict, description="检查项详情")


class MetricsResponse(BaseModel):
    """
    监控指标响应模型
    """
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="指标数据")
    timestamp: str = Field(..., description="时间戳")


class AlertResponse(BaseModel):
    """
    告警响应模型
    """
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="告警数据")
    timestamp: str = Field(..., description="时间戳")


class PerformanceReportResponse(BaseModel):
    """
    性能报告响应模型
    """
    success: bool = Field(..., description="是否成功")
    report: Dict[str, Any] = Field(..., description="性能报告")
    generated_at: str = Field(..., description="生成时间")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    健康检查接口
    
    返回系统健康状态，包括:
    - 系统运行时间
    - 活跃告警数量
    - 各项检查状态
    
    返回:
        HealthCheckResponse: 健康检查结果
    """
    try:
        collector = get_metrics_collector()
        alert_manager = get_alert_manager()
        
        all_metrics = collector.get_all_metrics()
        health_status = alert_manager.get_health_status()
        
        checks = {}
        
        system_metrics = all_metrics.get("system_metrics", {})
        
        checks["cpu"] = {
            "status": "ok" if system_metrics.get("cpu_percent", 0) < 80 else "warning",
            "value": system_metrics.get("cpu_percent", 0),
            "threshold": 80
        }
        
        checks["memory"] = {
            "status": "ok" if system_metrics.get("memory_percent", 0) < 85 else "warning",
            "value": system_metrics.get("memory_percent", 0),
            "threshold": 85
        }
        
        if system_metrics.get("gpu_available", False):
            gpu_memory_percent = (
                system_metrics.get("gpu_memory_used_mb", 0) / 
                max(system_metrics.get("gpu_memory_total_mb", 1), 1) * 100
            )
            checks["gpu_memory"] = {
                "status": "ok" if gpu_memory_percent < 85 else "warning",
                "value": round(gpu_memory_percent, 2),
                "threshold": 85
            }
        
        api_metrics = all_metrics.get("api_metrics", {})
        if api_metrics:
            total_requests = sum(m.get("count", 0) for m in api_metrics.values())
            total_errors = sum(m.get("error_count", 0) for m in api_metrics.values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            checks["api_error_rate"] = {
                "status": "ok" if error_rate < 5 else "warning",
                "value": round(error_rate, 2),
                "threshold": 5
            }
        
        cache_metrics = all_metrics.get("cache_metrics", {})
        if cache_metrics:
            avg_hit_rate = sum(m.get("hit_rate", 0) for m in cache_metrics.values()) / len(cache_metrics)
            checks["cache_hit_rate"] = {
                "status": "ok" if avg_hit_rate > 50 else "warning",
                "value": round(avg_hit_rate, 2),
                "threshold": 50
            }
        
        return HealthCheckResponse(
            status=health_status["status"],
            message=health_status["message"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=all_metrics.get("uptime_seconds", 0),
            active_alerts_count=health_status["active_alerts_count"],
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    metric_type: str = Query(
        default="all",
        description="指标类型: all, api, cache, system"
    )
):
    """
    获取监控数据接口
    
    参数:
        metric_type: 指标类型，可选值: all, api, cache, system
    
    返回:
        MetricsResponse: 监控指标数据
    """
    try:
        collector = get_metrics_collector()
        
        if metric_type == "all":
            data = collector.get_all_metrics()
        elif metric_type == "api":
            data = {
                "api_metrics": collector.get_api_metrics(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        elif metric_type == "cache":
            data = {
                "cache_metrics": collector.get_cache_metrics(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        elif metric_type == "system":
            data = {
                "system_metrics": collector.get_system_metrics(),
                "system_metrics_history": collector.get_system_metrics_history(limit=10),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的指标类型: {metric_type}"
            )
        
        return MetricsResponse(
            success=True,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监控数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取监控数据失败: {str(e)}")


@router.get("/metrics/api/{endpoint:path}", response_model=MetricsResponse)
async def get_api_metrics_by_endpoint(endpoint: str):
    """
    获取特定 API 端点的监控数据
    
    参数:
        endpoint: API 端点路径
    
    返回:
        MetricsResponse: API 指标数据
    """
    try:
        collector = get_metrics_collector()
        
        data = collector.get_api_metrics(endpoint=endpoint)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到端点 {endpoint} 的监控数据"
            )
        
        return MetricsResponse(
            success=True,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 API 指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取 API 指标失败: {str(e)}")


@router.get("/metrics/cache/{cache_name}", response_model=MetricsResponse)
async def get_cache_metrics_by_name(cache_name: str):
    """
    获取特定缓存的监控数据
    
    参数:
        cache_name: 缓存名称
    
    返回:
        MetricsResponse: 缓存指标数据
    """
    try:
        collector = get_metrics_collector()
        
        data = collector.get_cache_metrics(cache_name=cache_name)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到缓存 {cache_name} 的监控数据"
            )
        
        return MetricsResponse(
            success=True,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存指标失败: {str(e)}")


@router.get("/report", response_model=PerformanceReportResponse)
async def get_performance_report():
    """
    获取性能报告接口
    
    返回综合性能报告，包括:
    - API 性能摘要
    - 缓存性能摘要
    - 系统资源使用情况
    - 性能建议
    
    返回:
        PerformanceReportResponse: 性能报告
    """
    try:
        collector = get_metrics_collector()
        alert_manager = get_alert_manager()
        
        summary = collector.get_performance_summary()
        health_status = alert_manager.get_health_status()
        active_alerts = alert_manager.get_active_alerts()
        
        recommendations = []
        
        api_metrics = summary.get("api", {})
        if api_metrics.get("avg_error_rate", 0) > 5:
            recommendations.append({
                "priority": "high",
                "category": "api",
                "issue": "API 错误率过高",
                "suggestion": "检查 API 错误日志，修复常见错误",
                "current_value": f"{api_metrics['avg_error_rate']}%"
            })
        
        slowest = api_metrics.get("slowest_endpoints", [])
        if slowest and slowest[0].get("p95_latency_ms", 0) > 3000:
            recommendations.append({
                "priority": "high",
                "category": "performance",
                "issue": "API 响应时间过长",
                "suggestion": "优化慢查询、增加缓存、使用异步处理",
                "current_value": f"{slowest[0]['p95_latency_ms']}ms"
            })
        
        cache_metrics = summary.get("cache", {})
        if cache_metrics.get("avg_hit_rate", 100) < 50:
            recommendations.append({
                "priority": "medium",
                "category": "cache",
                "issue": "缓存命中率过低",
                "suggestion": "增加缓存大小、优化缓存策略、预热常用数据",
                "current_value": f"{cache_metrics['avg_hit_rate']}%"
            })
        
        system_metrics = summary.get("system", {})
        if system_metrics.get("cpu_percent", 0) > 80:
            recommendations.append({
                "priority": "high",
                "category": "system",
                "issue": "CPU 使用率过高",
                "suggestion": "优化计算密集型任务、增加服务器资源",
                "current_value": f"{system_metrics['cpu_percent']}%"
            })
        
        if system_metrics.get("memory_percent", 0) > 85:
            recommendations.append({
                "priority": "high",
                "category": "system",
                "issue": "内存使用率过高",
                "suggestion": "检查内存泄漏、优化数据结构、增加内存",
                "current_value": f"{system_metrics['memory_percent']}%"
            })
        
        if system_metrics.get("gpu_available", False):
            gpu_memory_percent = (
                system_metrics.get("gpu_memory_used_mb", 0) /
                max(system_metrics.get("gpu_memory_total_mb", 1), 1) * 100
            )
            if gpu_memory_percent > 85:
                recommendations.append({
                    "priority": "high",
                    "category": "gpu",
                    "issue": "GPU 显存使用率过高",
                    "suggestion": "减小批处理大小、使用模型量化、清理显存缓存",
                    "current_value": f"{round(gpu_memory_percent, 2)}%"
                })
        
        report = {
            "summary": summary,
            "health_status": health_status,
            "active_alerts": active_alerts,
            "recommendations": recommendations,
            "report_metadata": {
                "generated_by": "WheatAgent Monitoring System",
                "version": "1.0.0"
            }
        }
        
        return PerformanceReportResponse(
            success=True,
            report=report,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"生成性能报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成性能报告失败: {str(e)}")


@router.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    include_history: bool = Query(
        default=False,
        description="是否包含历史告警"
    ),
    history_limit: int = Query(
        default=100,
        description="历史告警数量限制"
    )
):
    """
    获取告警信息接口
    
    参数:
        include_history: 是否包含历史告警
        history_limit: 历史告警数量限制
    
    返回:
        AlertResponse: 告警信息
    """
    try:
        alert_manager = get_alert_manager()
        
        data = {
            "active_alerts": alert_manager.get_active_alerts(),
            "health_status": alert_manager.get_health_status(),
            "rules": alert_manager.get_rules()
        }
        
        if include_history:
            data["history"] = alert_manager.get_alert_history(limit=history_limit)
        
        return AlertResponse(
            success=True,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取告警信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警信息失败: {str(e)}")


@router.post("/alerts/{rule_name}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(rule_name: str):
    """
    确认告警接口
    
    参数:
        rule_name: 告警规则名称
    
    返回:
        AlertResponse: 操作结果
    """
    try:
        alert_manager = get_alert_manager()
        
        success = alert_manager.acknowledge_alert(rule_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"未找到活跃告警: {rule_name}"
            )
        
        return AlertResponse(
            success=True,
            data={
                "message": f"告警 {rule_name} 已确认",
                "rule_name": rule_name
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


@router.post("/alerts/clear", response_model=AlertResponse)
async def clear_alerts():
    """
    清除所有活跃告警接口
    
    返回:
        AlertResponse: 操作结果
    """
    try:
        alert_manager = get_alert_manager()
        alert_manager.clear_alerts()
        
        return AlertResponse(
            success=True,
            data={
                "message": "所有活跃告警已清除"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"清除告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除告警失败: {str(e)}")


@router.get("/alerts/rules", response_model=AlertResponse)
async def get_alert_rules():
    """
    获取告警规则接口
    
    返回:
        AlertResponse: 告警规则列表
    """
    try:
        alert_manager = get_alert_manager()
        
        return AlertResponse(
            success=True,
            data={
                "rules": alert_manager.get_rules()
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警规则失败: {str(e)}")


@router.post("/collect", response_model=MetricsResponse)
async def collect_system_metrics():
    """
    手动触发系统指标收集接口
    
    返回:
        MetricsResponse: 收集到的系统指标
    """
    try:
        collector = get_metrics_collector()
        
        metrics = collector.collect_system_metrics()
        
        return MetricsResponse(
            success=True,
            data=metrics.to_dict(),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"收集系统指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"收集系统指标失败: {str(e)}")


@router.post("/reset", response_model=MetricsResponse)
async def reset_metrics():
    """
    重置所有监控指标接口
    
    返回:
        MetricsResponse: 操作结果
    """
    try:
        collector = get_metrics_collector()
        alert_manager = get_alert_manager()
        
        collector.reset()
        alert_manager.reset()
        
        return MetricsResponse(
            success=True,
            data={
                "message": "所有监控指标和告警已重置"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"重置监控指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置监控指标失败: {str(e)}")


def include_router(app):
    """
    将监控路由注册到 FastAPI 应用
    
    参数:
        app: FastAPI 应用实例
    """
    app.include_router(router)
    logger.info("监控 API 路由已注册")
