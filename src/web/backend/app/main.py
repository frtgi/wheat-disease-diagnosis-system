import os
import sys

if sys.platform == 'win32':
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

"""
FastAPI 应用主入口
创建并配置 FastAPI 应用实例
优化版：集成 GPU 监控、错误摘要和融合诊断验证
"""
import asyncio
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from pathlib import Path as FilePath
from .core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from .rate_limiter import limiter, add_rate_limit_middleware
from .core.database import init_db_async
from .core.startup_manager import initialize_startup_manager, get_startup_manager, StartupPhase, ComponentStatus
from .core.exceptions import register_exception_handlers
from .services.ai_preloader import preload_ai_services
from .services.cache_manager import get_cache_manager
from .api.v1 import user, knowledge, stats, health, ai_diagnosis, metrics, logs, reports, upload
from .monitoring.monitoring_api import router as monitoring_router
from .utils.gpu_monitor import log_gpu_memory, get_device_info, check_gpu_available

from .core.logging_config import setup_logging

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    import asyncio
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
    except ImportError:
        try:
            from asyncio.windows_events import _ProactorBasePipeTransport
        except ImportError:
            _ProactorBasePipeTransport = None

    if _ProactorBasePipeTransport is not None:
        _original_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _silent_call_connection_lost(self, exc):
            if isinstance(exc, ConnectionResetError):
                return
            _original_call_connection_lost(self, exc)

        _ProactorBasePipeTransport._call_connection_lost = _silent_call_connection_lost

setup_logging(
    level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO",
    json_format=settings.JSON_LOG_FORMAT if hasattr(settings, 'JSON_LOG_FORMAT') else False
)
for handler in logging.root.handlers:
    if hasattr(handler.stream, 'reconfigure'):
        handler.stream.reconfigure(encoding='utf-8', errors='replace')
logger = logging.getLogger(__name__)


def _print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ██╗    ██╗██╗███╗   ██╗    ████████╗███████╗██████╗ ███╗   ███╗    ║
║   ██║    ██║██║████╗  ██║    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║    ║
║   ██║ █╗ ██║██║██╔██╗ ██║       ██║   █████╗  ██████╔╝██╔████╔██║    ║
║   ██║███╗██║██║██║╚██╗██║       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║    ║
║   ╚███╔███╔╝██║██║ ╚████║       ██║   ███████╗██║  ██║██║ ╚═╝ ██║    ║
║    ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝    ║
║                                                                       ║
║              Wheat Agent - 小麦病害智能诊断系统                        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"版本: {settings.APP_VERSION}")
    print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 71)


def _print_startup_phase(phase_num: int, total_phases: int, phase_name: str, progress_range: str):
    """打印启动阶段信息"""
    print("\n" + "-" * 71)
    print(f"[阶段 {phase_num}/{total_phases}] {phase_name} (进度 {progress_range})")
    print("-" * 71)


async def _verify_fusion_diagnosis() -> dict:
    """
    验证融合诊断模块
    
    Returns:
        验证结果字典
    """
    result = {
        "yolo_available": False,
        "qwen_available": False,
        "graphrag_available": False,
        "fusion_available": False,
        "errors": []
    }
    
    try:
        from .services import yolo_service
        result["yolo_available"] = yolo_service._yolo_service is not None and yolo_service._yolo_service.is_loaded
        if result["yolo_available"]:
            logger.info("✅ YOLO 服务验证通过")
        else:
            result["errors"].append("YOLO 服务未加载")
            logger.warning("⚠️ YOLO 服务未加载")
    except Exception as e:
        result["errors"].append(f"YOLO 服务验证失败: {e}")
        logger.error(f"❌ YOLO 服务验证失败: {e}")
    
    try:
        from .services import qwen_service
        result["qwen_available"] = qwen_service._qwen_service is not None and qwen_service._qwen_service.is_loaded
        if result["qwen_available"]:
            logger.info("✅ Qwen 服务验证通过")
        else:
            result["errors"].append("Qwen 服务未加载")
            logger.warning("⚠️ Qwen 服务未加载")
    except Exception as e:
        result["errors"].append(f"Qwen 服务验证失败: {e}")
        logger.error(f"❌ Qwen 服务验证失败: {e}")
    
    try:
        from .services.graphrag_service import get_graphrag_service
        graphrag = get_graphrag_service()
        result["graphrag_available"] = graphrag is not None
        if result["graphrag_available"]:
            logger.info("✅ GraphRAG 服务验证通过")
        else:
            result["errors"].append("GraphRAG 服务未连接")
            logger.warning("⚠️ GraphRAG 服务未连接")
    except Exception as e:
        result["errors"].append(f"GraphRAG 服务验证失败: {e}")
        logger.warning(f"⚠️ GraphRAG 服务验证失败: {e}")
    
    result["fusion_available"] = result["yolo_available"] and result["qwen_available"]
    
    return result


def create_application() -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    返回:
        配置好的 FastAPI 应用
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="WheatAgent 小麦病害智能诊断系统后端服务",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    register_exception_handlers(app)
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept", "Origin"],
        expose_headers=["X-Request-ID"],
        max_age=settings.CORS_MAX_AGE,
    )
    
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """
        请求 ID 追踪中间件
        为每个请求生成唯一 ID，便于日志追踪和问题定位
        """
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """
        安全头中间件（增强版）

        添加以下 HTTP 安全响应头：
        - X-Content-Type-Options: 防止 MIME 类型嗅探
        - X-Frame-Options: 防止点击劫持
        - X-XSS-Protection: 启用 XSS 过滤器
        - Strict-Transport-Security: 强制 HTTPS（仅生产环境）
        - Content-Security-Policy: 内容安全策略，防止 XSS 和数据注入攻击
        - Referrer-Policy: 控制引用头信息泄露
        - Permissions-Policy: 限制浏览器功能
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: blob: https:",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response
    
    @app.middleware("http")
    async def retry_middleware(request: Request, call_next):
        """
        请求重试中间件
        处理连接重置等临时错误，增强服务稳定性
        """
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = await call_next(request)
                return response
            except (ConnectionResetError, OSError, IOError) as e:
                last_exception = e
                logger.warning(f"请求失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"重试失败，放弃请求：{e}")
                    raise
                await asyncio.sleep(0.1 * (2 ** attempt))
        
        if last_exception:
            raise last_exception
    
    app.include_router(user.router, prefix=settings.API_PREFIX)
    app.include_router(knowledge.router, prefix=settings.API_PREFIX)
    app.include_router(stats.router, prefix=settings.API_PREFIX)
    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(ai_diagnosis.router, prefix=settings.API_PREFIX)
    app.include_router(metrics.router, prefix=settings.API_PREFIX)
    app.include_router(logs.router, prefix=settings.API_PREFIX)
    app.include_router(reports.router, prefix=settings.API_PREFIX)
    app.include_router(upload.router, prefix=settings.API_PREFIX)
    app.include_router(monitoring_router, prefix=settings.API_PREFIX)
    
    uploads_dir = FilePath(__file__).parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行分阶段初始化（优化版）"""
        total_start = time.time()
        
        _print_banner()
        
        startup_mgr = initialize_startup_manager(timeout=120.0)
        startup_mgr.update_phase(StartupPhase.INIT, "开始初始化基础服务")
        
        device_info = get_device_info()
        startup_mgr.set_gpu_info(device_info)
        
        if device_info.get("cuda_available"):
            print(f"\n[GPU 检测]:")
            for device in device_info.get("devices", []):
                print(f"   GPU {device['id']}: {device['name']} ({device['total_memory_mb']:.0f}MB)")
        else:
            print(f"\n[警告] GPU 不可用: {device_info.get('message', '未知原因')}")
            print("   AI 模型将无法加载，请检查 GPU 驱动和 CUDA 安装")
        
        _print_startup_phase(1, 4, "基础服务初始化", "0-20%")
        startup_mgr.progress.overall_progress = 0
        logger.info("初始化基础配置...")
        await asyncio.sleep(0.1)
        startup_mgr.progress.overall_progress = 20
        logger.info("基础服务初始化完成")
        
        _print_startup_phase(2, 4, "数据库初始化", "20-40%")
        startup_mgr.update_phase(StartupPhase.DATABASE, "初始化数据库连接")
        startup_mgr.progress.overall_progress = 20
        
        startup_mgr.register_component("database")
        startup_mgr.update_component_status("database", ComponentStatus.LOADING, 0, "连接数据库")
        
        try:
            await init_db_async()
            startup_mgr.update_component_status("database", ComponentStatus.READY, 100, "数据库就绪")
            logger.info("✅ 数据库初始化完成")
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败：{e}")
            startup_mgr.update_component_status("database", ComponentStatus.FAILED, 0, "数据库失败", str(e))
            startup_mgr.add_error("database", str(e), "检查数据库服务是否启动，连接参数是否正确")
            print(f"⚠️ 数据库初始化失败: {e}")
            print("   应用仍可启动，但数据库相关功能将不可用")
        
        startup_mgr.progress.overall_progress = 40
        
        _print_startup_phase(3, 4, "AI 模型加载", "40-90%")
        startup_mgr.update_phase(StartupPhase.AI_LOADING, "预加载 AI 模型")
        
        try:
            ai_results = await preload_ai_services()
            
            if ai_results["success_count"] == 2:
                logger.info(f"✅ AI 模型加载成功：2/2 ({ai_results['total_time']:.2f}秒)")
            elif ai_results["success_count"] == 1:
                logger.warning(f"⚠️ AI 模型部分加载：1/2 ({ai_results['total_time']:.2f}秒)，降级模式")
            else:
                logger.error(f"❌ AI 模型加载失败：0/2 ({ai_results['total_time']:.2f}秒)")
            
            if ai_results.get("final_gpu_memory"):
                gpu_mem = ai_results["final_gpu_memory"]
                print(f"\n📊 最终显存状态:")
                print(f"   已用: {gpu_mem['used_mb']:.0f}MB")
                print(f"   可用: {gpu_mem['free_mb']:.0f}MB")
                print(f"   利用率: {gpu_mem['utilization_percent']:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ AI 模型加载异常：{e}")
            startup_mgr.add_error("ai_models", str(e), "检查模型路径、GPU 显存是否充足")
        
        startup_mgr.progress.overall_progress = 90
        
        _print_startup_phase(4, 4, "服务组件初始化", "90-100%")
        startup_mgr.update_phase(StartupPhase.SERVICES, "初始化服务组件")
        
        try:
            cache_mgr = get_cache_manager()
            startup_mgr.register_component("cache")
            startup_mgr.update_component_status("cache", ComponentStatus.READY, 100, "缓存就绪")
            logger.info("✅ 缓存管理器初始化完成")
        except Exception as e:
            logger.error(f"❌ 缓存管理器初始化失败：{e}")
            startup_mgr.register_component("cache")
            startup_mgr.update_component_status("cache", ComponentStatus.FAILED, 0, "缓存失败", str(e))
        
        logger.info("验证融合诊断模块...")
        fusion_result = await _verify_fusion_diagnosis()
        startup_mgr.register_component("fusion_diagnosis")
        
        if fusion_result["fusion_available"]:
            startup_mgr.update_component_status("fusion_diagnosis", ComponentStatus.READY, 100, "融合诊断就绪")
            logger.info("✅ 融合诊断模块验证通过")
        else:
            startup_mgr.update_component_status("fusion_diagnosis", ComponentStatus.DEGRADED, 50, "部分可用")
            logger.warning("⚠️ 融合诊断模块部分可用")
            for error in fusion_result["errors"]:
                logger.warning(f"   - {error}")
        
        startup_mgr.update_phase(StartupPhase.READY, "服务就绪")
        startup_mgr.progress.overall_progress = 100
        
        total_time = time.time() - total_start
        
        print("\n" + "=" * 71)
        print("🚀 启动完成！")
        print("=" * 71)
        print(f"总耗时: {total_time:.2f}秒")
        
        status = "就绪" if startup_mgr.is_ready() else "降级" if startup_mgr.is_degraded() else "失败"
        status_icon = "✅" if startup_mgr.is_ready() else "⚠️" if startup_mgr.is_degraded() else "❌"
        print(f"状态: {status_icon} {status}")
        
        print("\n📋 组件状态:")
        for name, component in startup_mgr.progress.components.items():
            icon = {
                ComponentStatus.READY: "✅",
                ComponentStatus.FAILED: "❌",
                ComponentStatus.DEGRADED: "⚠️",
                ComponentStatus.LOADING: "⏳",
                ComponentStatus.PENDING: "⏸️"
            }.get(component.status, "❓")
            print(f"   {icon} {name}: {component.message}")
        
        if startup_mgr.get_errors():
            print("\n❌ 错误摘要:")
            for error in startup_mgr.get_errors():
                print(f"   [{error.component}] {error.error_message}")
                if error.suggestion:
                    print(f"      建议: {error.suggestion}")
        
        print("\n🌐 服务地址:")
        print(f"   API 文档: http://localhost:8000/docs")
        print(f"   健康检查: http://localhost:8000/api/v1/health")
        print("=" * 71)

        asyncio.create_task(_system_metrics_collector_loop())

    async def _system_metrics_collector_loop():
        """后台定时采集系统指标"""
        await asyncio.sleep(10)
        while True:
            try:
                from app.monitoring.metrics_collector import get_metrics_collector
                collector = get_metrics_collector()
                collector.collect_system_metrics()
            except Exception:
                pass
            await asyncio.sleep(10)
    
    @app.get("/", tags=["根路径"])
    async def root():
        """根路径，返回应用信息"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }
    
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """
        健康检查接口
        返回服务基本健康状态
        """
        return {"status": "healthy"}
    
    @app.get("/api/v1/health", tags=["健康检查"])
    async def api_health_check():
        """
        API健康检查接口
        返回详细的服务健康状态信息
        """
        try:
            startup_mgr = get_startup_manager()
            is_ready = startup_mgr.is_ready()
            is_degraded = startup_mgr.is_degraded()
            
            return {
                "status": "healthy" if is_ready else ("degraded" if is_degraded else "unhealthy"),
                "version": settings.APP_VERSION,
                "ready": is_ready,
                "degraded": is_degraded,
                "components": {k: v.to_dict() for k, v in startup_mgr.progress.components.items()}
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1,
        timeout_keep_alive=30,
        limit_concurrency=100,
        limit_max_requests=1000,
        log_level="info"
    )
