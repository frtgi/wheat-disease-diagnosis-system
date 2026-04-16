"""
统计 API 路由
提供数据统计和仪表盘功能
包含缓存统计功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from ...core.database import get_db
from ...core.security import get_current_user, require_admin
from ...models.diagnosis import Diagnosis
from ...models.disease import Disease
from ...models.user import User

router = APIRouter(prefix="/stats", tags=["统计信息"])


@router.get("/overview", summary="获取概览统计")
def get_overview_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取系统概览统计数据
    
    返回用户总数、诊断记录总数、疾病知识总数等
    """
    user_count = db.query(func.count(User.id)).scalar()
    diagnosis_count = db.query(func.count(Diagnosis.id)).scalar()
    disease_count = db.query(func.count(Disease.id)).scalar()
    
    return {
        "total_users": user_count,
        "total_diagnoses": diagnosis_count,
        "total_diseases": disease_count
    }


@router.get("/diagnoses", summary="获取诊断统计")
def get_diagnosis_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取诊断相关统计
    
    返回诊断状态分布、热门疾病等
    """
    # 按状态统计诊断数量
    status_stats = db.query(
        Diagnosis.status,
        func.count(Diagnosis.id)
    ).group_by(Diagnosis.status).all()
    
    # 统计热门疾病（被诊断次数最多的）
    top_diseases = db.query(
        Diagnosis.disease_id,
        func.count(Diagnosis.id).label("count")
    ).filter(
        Diagnosis.disease_id.isnot(None)
    ).group_by(Diagnosis.disease_id).order_by(
        func.count(Diagnosis.id).desc()
    ).limit(10).all()
    
    return {
        "by_status": {status: count for status, count in status_stats},
        "top_diseases": [{"disease_id": d_id, "count": cnt} for d_id, cnt in top_diseases]
    }


@router.get("/users", summary="获取用户统计")
def get_user_stats(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    获取用户相关统计
    
    返回活跃用户数、角色分布等
    """
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # 按角色统计
    role_stats = db.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "by_role": {role: count for role, count in role_stats}
    }


@router.get("/cache", summary="获取缓存统计")
async def get_cache_stats(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    获取推理缓存统计信息
    
    返回缓存命中率、键数量、节省时间等统计
    """
    try:
        from ...services.inference_cache_service import get_inference_cache
        
        cache_service = get_inference_cache()
        stats = await cache_service.get_stats()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@router.delete("/cache", summary="清空推理缓存")
async def clear_inference_cache(current_user: User = Depends(require_admin)) -> Dict[str, Any]:
    """
    清空所有推理缓存
    
    需要管理员权限
    """
    try:
        from ...services.inference_cache_service import get_inference_cache
        
        cache_service = get_inference_cache()
        deleted_count = await cache_service.clear_all()
        
        return {
            "success": True,
            "message": f"已清空 {deleted_count} 个缓存键",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空缓存失败: {str(e)}"
        )


@router.get("/cache/info", summary="获取缓存配置信息")
async def get_cache_config(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    获取缓存配置信息
    
    返回 TTL、相似搜索配置等
    """
    try:
        from ...services.inference_cache_service import get_inference_cache
        
        cache_service = get_inference_cache()
        
        return {
            "success": True,
            "data": {
                "ttl_seconds": cache_service.ttl,
                "similar_search_enabled": cache_service.enable_similar_search,
                "similarity_threshold": cache_service.similarity_threshold,
                "cache_prefix": cache_service.CACHE_PREFIX,
                "phash_index_prefix": cache_service.PHASH_INDEX_PREFIX
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存配置失败: {str(e)}"
        )


@router.get("/vram", summary="获取 GPU 显存状态")
async def get_vram_status(current_user: User = Depends(require_admin)) -> Dict[str, Any]:
    """
    获取 GPU 显存使用状态（需管理员权限）

    返回显存使用量、空闲量、使用率等信息，
    用于管理后台监控 4GB 显存限制下的资源使用情况。

    权限:
        仅 admin 角色可访问
    """
    try:
        from ...services.vram_manager import get_vram_manager

        vram_mgr = get_vram_manager()
        usage = vram_mgr.get_vram_usage()

        return {
            "success": True,
            "data": {
                "used_mb": usage["used_mb"],
                "free_mb": usage["free_mb"],
                "total_mb": usage["total_mb"],
                "reserved_mb": usage.get("reserved_mb", 0),
                "usage_ratio": usage["usage_ratio"],
                "warning_threshold": vram_mgr.warning_threshold,
                "critical_threshold": vram_mgr.critical_threshold,
                "is_critical": usage["usage_ratio"] >= vram_mgr.critical_threshold,
                "is_warning": usage["usage_ratio"] >= vram_mgr.warning_threshold
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取显存状态失败: {str(e)}"
        )


@router.post("/vram/cleanup", summary="清理 GPU 显存")
async def cleanup_vram(current_user: User = Depends(require_admin)) -> Dict[str, Any]:
    """
    手动触发 GPU 显存清理（需管理员权限）

    执行激进的显存清理操作，包括 Python GC 和 CUDA 缓存释放。

    权限:
        仅 admin 角色可访问
    """
    try:
        from ...services.vram_manager import get_vram_manager

        vram_mgr = get_vram_manager()
        result = vram_mgr.cleanup(aggressive=True)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"显存清理失败: {str(e)}"
        )
