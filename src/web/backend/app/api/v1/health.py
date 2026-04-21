"""
数据库健康检查端点
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.core.database import SyncSessionLocal
from app.core.startup_manager import get_startup_manager
from app.services.yolo_service import get_yolo_service
from app.services.qwen_service import get_qwen_service
from app.services.cache_manager import get_cache_manager
import time

router = APIRouter(prefix="/health", tags=["健康检查"])

_components_cache = {"data": None, "timestamp": 0}
COMPONENTS_CACHE_TTL = 5

@router.get("/database")
async def database_health():
    """
    数据库健康检查
    返回数据库连接状态和基本信息
    """
    try:
        db = SyncSessionLocal()

        # 测试连接
        start_time = time.time()
        db.execute(text("SELECT 1"))
        query_time = round((time.time() - start_time) * 1000, 2)

        # 获取数据库信息
        result = db.execute(text("SELECT DATABASE()")).fetchone()
        database_name = result[0] if result else "unknown"

        # 获取表数量
        result = db.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
        """)).fetchone()
        table_count = result[0] if result else 0

        db.close()

        return {
            "status": "healthy",
            "database": database_name,
            "connection_time_ms": query_time,
            "table_count": table_count,
            "pool_status": "active"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"数据库连接失败：{str(e)}")


@router.get("/startup")
async def startup_status():
    """
    启动状态检查
    返回应用启动进度和状态
    """
    try:
        startup_mgr = get_startup_manager()
        status = startup_mgr.get_status()

        return {
            "status": status["status"],
            "progress": status["progress"]["overall_progress"],
            "phase": status["progress"]["phase"],
            "components": {
                name: info.to_dict()
                for name, info in startup_mgr.progress.components.items()
            },
            "elapsed_time": status["progress"]["elapsed_time"],
            "estimated_remaining_time": status["progress"]["estimated_remaining_time"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check():
    """
    就绪状态检查
    返回应用是否已就绪可以接受请求
    """
    try:
        startup_mgr = get_startup_manager()

        is_ready = startup_mgr.is_ready()
        is_degraded = startup_mgr.is_degraded()
        is_failed = startup_mgr.is_failed()

        # 检查关键组件
        critical_components = {
            "database": False,
            "yolo": False,
            "qwen": False
        }

        for name, component in startup_mgr.progress.components.items():
            if name in critical_components:
                critical_components[name] = (
                    component.status.value in ["ready", "degraded"]
                )

        return {
            "ready": is_ready,
            "degraded": is_degraded,
            "failed": is_failed,
            "status": "ready" if is_ready else ("degraded" if is_degraded else "starting"),
            "critical_components": critical_components,
            "all_components_ready": all(critical_components.values()),
            "message": "服务已就绪" if is_ready else (
                "服务降级运行" if is_degraded else
                "服务正在启动" if not is_failed else
                "服务启动失败"
            )
        }
    except Exception as e:
        return {
            "ready": False,
            "status": "error",
            "error": str(e)
        }


@router.get("/components")
async def components_status():
    """
    组件状态检查
    返回所有组件的详细状态（带 TTL 缓存）
    """
    current_time = time.time()
    if _components_cache["data"] and (current_time - _components_cache["timestamp"]) < COMPONENTS_CACHE_TTL:
        return _components_cache["data"]

    try:
        get_startup_manager()

        components = {}

        # 数据库状态
        try:
            db = SyncSessionLocal()
            start_time = time.time()
            db.execute(text("SELECT 1"))
            query_time = round((time.time() - start_time) * 1000, 2)
            result = db.execute(text("SELECT DATABASE()")).fetchone()
            database_name = result[0] if result else "unknown"
            db.close()

            components["database"] = {
                "status": "ready",
                "name": database_name,
                "connection_time_ms": query_time
            }
        except Exception as e:
            components["database"] = {
                "status": "failed",
                "error": str(e)
            }

        # YOLO 服务状态
        try:
            yolo_service = get_yolo_service()
            components["yolo"] = {
                "status": "ready" if yolo_service.is_loaded else "failed",
                "model_path": str(yolo_service.model_path) if yolo_service.model_path else "pretrained",
                "confidence_threshold": yolo_service.confidence_threshold
            }
        except Exception as e:
            components["yolo"] = {
                "status": "failed",
                "error": str(e)
            }

        # Qwen 服务状态
        try:
            qwen_service = get_qwen_service()
            components["qwen"] = {
                "status": "ready" if qwen_service.is_loaded else "failed",
                "model_path": str(qwen_service.model_path),
                "device": qwen_service.device,
                "int4_quantization": qwen_service.load_in_4bit,
                "features": {
                    "kad_former": qwen_service.enable_kad_former,
                    "graph_rag": qwen_service.enable_graph_rag
                }
            }
        except Exception as e:
            components["qwen"] = {
                "status": "failed",
                "error": str(e)
            }

        # 缓存状态
        try:
            cache_mgr = get_cache_manager()
            components["cache"] = {
                "status": "ready",
                "cache_size": len(cache_mgr.cache) if hasattr(cache_mgr, 'cache') else 0
            }
        except Exception as e:
            components["cache"] = {
                "status": "failed",
                "error": str(e)
            }

        result = {
            "status": "healthy",
            "components": components,
            "summary": {
                "total": len(components),
                "ready": sum(1 for c in components.values() if c["status"] == "ready"),
                "failed": sum(1 for c in components.values() if c["status"] == "failed"),
                "degraded": sum(1 for c in components.values() if c["status"] == "degraded")
            }
        }

        _components_cache["data"] = result
        _components_cache["timestamp"] = current_time

        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"组件状态检查失败：{str(e)}")
