"""
诊断日志分析 API 端点

提供日志查询和统计分析（需要管理员权限）：
1. 热门病害类型统计
2. 诊断成功率分析
3. 日志查询和过滤
4. 趋势分析

安全说明：
- 所有端点均需要 JWT 认证和管理员权限
- 所有限流设置为每分钟 60 次请求
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import func

from app.core.security import require_admin, verify_token
from app.core.dependencies import get_pagination_params
from app.schemas.common import PaginationParams
from app.rate_limiter import limiter
from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.core.database import SyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["诊断日志"])


def _get_db_session():
    """获取数据库会话"""
    db = SyncSessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def _build_stats_from_db(duration_hours: int) -> dict:
    """从数据库构建诊断统计信息"""
    db = SyncSessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=duration_hours)
        query = db.query(Diagnosis).filter(
            Diagnosis.created_at >= cutoff,
            Diagnosis.deleted_at.is_(None)
        )
        total = query.count()
        success_count = query.filter(Diagnosis.status == "completed").count()

        disease_counts = (
            db.query(Diagnosis.disease_name, func.count(Diagnosis.id))
            .filter(
                Diagnosis.created_at >= cutoff,
                Diagnosis.deleted_at.is_(None),
                Diagnosis.status == "completed"
            )
            .group_by(Diagnosis.disease_name)
            .order_by(func.count(Diagnosis.id).desc())
            .limit(10)
            .all()
        )

        avg_confidence_result = (
            db.query(func.avg(Diagnosis.confidence))
            .filter(
                Diagnosis.created_at >= cutoff,
                Diagnosis.deleted_at.is_(None),
                Diagnosis.status == "completed"
            )
            .scalar()
        )

        return {
            "duration_hours": duration_hours,
            "total_requests": total,
            "success_count": success_count,
            "error_count": total - success_count,
            "success_rate": round(success_count / total * 100, 2) if total > 0 else 0,
            "cache_hit_rate": 0,
            "top_diseases": [
                {"disease": name, "count": count}
                for name, count in disease_counts
            ],
            "avg_confidence": round(float(avg_confidence_result or 0), 3),
            "avg_processing_time_ms": 0,
            "error_types": []
        }
    finally:
        db.close()


def _build_distribution_from_db(duration_hours: int) -> list:
    """从数据库构建病害分布"""
    db = SyncSessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=duration_hours)
        disease_counts = (
            db.query(Diagnosis.disease_name, func.count(Diagnosis.id))
            .filter(
                Diagnosis.created_at >= cutoff,
                Diagnosis.deleted_at.is_(None),
                Diagnosis.status == "completed"
            )
            .group_by(Diagnosis.disease_name)
            .order_by(func.count(Diagnosis.id).desc())
            .all()
        )

        total = sum(count for _, count in disease_counts)
        return [
            {
                "disease_name": name,
                "count": count,
                "percentage": round(count / total * 100, 2) if total > 0 else 0
            }
            for name, count in disease_counts
        ]
    finally:
        db.close()


def _build_recent_logs_from_db(limit: int = 100) -> list:
    """从数据库构建最近日志"""
    db = SyncSessionLocal()
    try:
        records = (
            db.query(Diagnosis)
            .filter(Diagnosis.deleted_at.is_(None))
            .order_by(Diagnosis.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "timestamp": r.created_at.isoformat() if r.created_at else "",
                "request_id": f"diag_{r.id}",
                "image_hash": None,
                "symptoms": r.symptoms or "",
                "disease_detected": r.disease_name or "未知",
                "confidence": float(r.confidence) if r.confidence else 0.0,
                "processing_time_ms": 0,
                "success": r.status == "completed",
                "error": None,
                "cache_hit": False,
                "features": {}
            }
            for r in records
        ]
    finally:
        db.close()


@router.get("/statistics")
@limiter.limit("60/minute")
async def get_diagnosis_statistics(
    request: Request,
    duration_hours: int = Query(24, description="统计时长（小时）", ge=1, le=720),
    current_user: User = Depends(require_admin)
):
    """
    获取诊断统计信息（需管理员权限）

    参数:
        request: FastAPI 请求对象（用于限流）
        duration_hours: 统计时长（小时），默认 24 小时
        current_user: 当前认证用户（必须为管理员）

    返回:
        热门病害、成功率、平均置信度等统计

    权限:
        仅 admin 角色可访问
    """
    try:
        from app.services.diagnosis_logger import get_diagnosis_logger

        diagnosis_logger = get_diagnosis_logger()
        stats = diagnosis_logger.get_statistics(duration_hours=duration_hours)

        if stats.get("total_requests", 0) == 0:
            stats = _build_stats_from_db(duration_hours)

        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取诊断统计失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取诊断统计失败：{str(e)}")


@router.get("/disease-distribution")
@limiter.limit("60/minute")
async def get_disease_distribution(
    request: Request,
    duration_hours: int = Query(24, description="统计时长（小时）", ge=1, le=720),
    current_user: User = Depends(require_admin)
):
    """
    获取病害分布统计（需管理员权限）

    参数:
        request: FastAPI 请求对象（用于限流）
        duration_hours: 统计时长（小时）
        current_user: 当前认证用户（必须为管理员）

    返回:
        病害类型分布（数量和百分比）

    权限:
        仅 admin 角色可访问
    """
    try:
        from app.services.diagnosis_logger import get_diagnosis_logger

        diagnosis_logger = get_diagnosis_logger()
        distribution = diagnosis_logger.get_disease_distribution(duration_hours=duration_hours)

        if not distribution:
            distribution = _build_distribution_from_db(duration_hours)

        return {
            "success": True,
            "data": {
                "duration_hours": duration_hours,
                "distribution": distribution,
                "total_diseases": len(distribution)
            }
        }

    except Exception as e:
        logger.error(f"获取病害分布失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取病害分布失败：{str(e)}")


@router.get("/success-rate-trend")
@limiter.limit("60/minute")
async def get_success_rate_trend(
    request: Request,
    duration_hours: int = Query(24, description="统计时长（小时）", ge=1, le=720),
    current_user: User = Depends(require_admin)
):
    """
    获取成功率趋势（需管理员权限）

    参数:
        request: FastAPI 请求对象（用于限流）
        duration_hours: 统计时长（小时）
        current_user: 当前认证用户（必须为管理员）

    返回:
        按小时的成功率趋势

    权限:
        仅 admin 角色可访问
    """
    try:
        from app.services.diagnosis_logger import get_diagnosis_logger

        diagnosis_logger = get_diagnosis_logger()
        trend = diagnosis_logger.get_success_rate_trend(duration_hours=duration_hours)

        if not trend:
            db = SyncSessionLocal()
            try:
                cutoff = datetime.utcnow() - timedelta(hours=duration_hours)
                hourly = (
                    db.query(
                        func.date_format(Diagnosis.created_at, '%Y-%m-%d %H:00').label('hour'),
                        func.count(Diagnosis.id).label('total'),
                        func.sum(func.if_(Diagnosis.status == 'completed', 1, 0)).label('success')
                    )
                    .filter(Diagnosis.created_at >= cutoff, Diagnosis.deleted_at.is_(None))
                    .group_by('hour')
                    .order_by('hour')
                    .all()
                )
                trend = [
                    {
                        "hour": str(h.hour),
                        "total_requests": h.total,
                        "success_count": int(h.success or 0),
                        "success_rate": round(int(h.success or 0) / h.total * 100, 2) if h.total > 0 else 0
                    }
                    for h in hourly
                ]
            finally:
                db.close()

        return {
            "success": True,
            "data": {
                "duration_hours": duration_hours,
                "trend": trend,
                "data_points": len(trend)
            }
        }

    except Exception as e:
        logger.error(f"获取成功率趋势失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取成功率趋势失败：{str(e)}")


@router.get("/recent")
@limiter.limit("60/minute")
async def get_recent_logs(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination_params),
    success_only: bool = Query(False, description="仅返回成功日志"),
    disease_filter: Optional[str] = Query(None, description="病害类型过滤"),
    current_user: User = Depends(require_admin)
):
    """
    获取最近的诊断日志（需管理员权限）

    参数:
        request: FastAPI 请求对象（用于限流）
        pagination: 统一分页参数（page, page_size）
        success_only: 是否仅返回成功日志
        disease_filter: 病害类型过滤
        current_user: 当前认证用户（必须为管理员）

    返回:
        最近的诊断日志列表

    权限:
        仅 admin 角色可访问
    """
    try:
        from app.services.diagnosis_logger import get_diagnosis_logger

        diagnosis_logger = get_diagnosis_logger()
        logs = diagnosis_logger.get_recent_logs(limit=pagination.limit)

        if not logs:
            logs = _build_recent_logs_from_db(limit=pagination.limit)

        if success_only:
            logs = [log for log in logs if log["success"]]

        if disease_filter:
            logs = [
                log for log in logs
                if disease_filter.lower() in log.get("disease_detected", "").lower()
            ]

        return {
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs),
                "filters": {
                    "success_only": success_only,
                    "disease_filter": disease_filter
                }
            }
        }

    except Exception as e:
        logger.error(f"获取最近日志失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取最近日志失败：{str(e)}")


@router.get("/error-analysis")
@limiter.limit("60/minute")
async def get_error_analysis(
    request: Request,
    duration_hours: int = Query(24, description="统计时长（小时）", ge=1, le=720),
    current_user: User = Depends(require_admin)
):
    """
    获取错误分析（需管理员权限）

    参数:
        duration_hours: 统计时长（小时）
        current_user: 当前认证用户（必须为管理员）

    返回:
        错误类型统计和常见错误

    权限:
        仅 admin 角色可访问
    """
    try:
        from app.services.diagnosis_logger import get_diagnosis_logger

        diagnosis_logger = get_diagnosis_logger()
        stats = diagnosis_logger.get_statistics(duration_hours=duration_hours)

        if stats.get("total_requests", 0) == 0:
            stats = _build_stats_from_db(duration_hours)

        return {
            "success": True,
            "data": {
                "duration_hours": duration_hours,
                "total_errors": stats.get("error_count", 0),
                "error_rate": stats.get("error_rate", 0),
                "error_types": stats.get("error_types", [])
            }
        }

    except Exception as e:
        logger.error(f"获取错误分析失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取错误分析失败：{str(e)}")


@router.get("/cache-stats")
@limiter.limit("60/minute")
async def get_cache_statistics(
    request: Request,
    duration_hours: int = Query(24, description="统计时长（小时）", ge=1, le=720),
    current_user: User = Depends(require_admin)
):
    """
    获取缓存统计（需管理员权限）

    参数:
        duration_hours: 统计时长（小时）
        current_user: 当前认证用户（必须为管理员）

    返回:
        缓存命中率等统计

    权限:
        仅 admin 角色可访问
    """
    try:
        from app.services.diagnosis_logger import get_diagnosis_logger

        diagnosis_logger = get_diagnosis_logger()
        stats = diagnosis_logger.get_statistics(duration_hours=duration_hours)

        return {
            "success": True,
            "data": {
                "cache_hit_rate": stats.get("cache_hit_rate", 0),
                "duration_hours": duration_hours,
                "note": "缓存命中率基于诊断日志统计"
            }
        }

    except Exception as e:
        logger.error(f"获取缓存统计失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败：{str(e)}")
