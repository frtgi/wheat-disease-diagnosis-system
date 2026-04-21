"""
AI 服务预加载模块

负责在应用启动时预加载 AI 模型，包括 YOLOv8 和 Qwen3-VL
集成 GPU 显存监控，优化启动流程
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable

from ..core.ai_config import AIConfig
from ..core.startup_manager import get_startup_manager, ComponentStatus, StartupPhase
from ..utils.gpu_monitor import (
    log_gpu_memory,
    check_memory_sufficient,
    get_memory_usage_delta
)

logger = logging.getLogger(__name__)

ai_config = AIConfig()
QWEN_MODEL_PATH = ai_config.QWEN_MODEL_PATH
YOLO_MODEL_PATH = ai_config.YOLO_MODEL_PATH

YOLO_ESTIMATED_VRAM_MB = 500
QWEN_INT4_ESTIMATED_VRAM_MB = 3000
QWEN_BF16_ESTIMATED_VRAM_MB = 10000


async def preload_yolo_service(progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    预加载 YOLO 服务（集成 GPU 显存监控）
    
    Args:
        progress_callback: 进度回调函数，接收 (progress: int, message: str)
    
    Returns:
        加载结果字典
    """
    start_time = time.time()
    result = {
        "success": False,
        "model": "YOLOv8",
        "path": str(YOLO_MODEL_PATH),
        "load_time": 0.0,
        "error": None,
        "gpu_memory": {}
    }
    
    startup_mgr = get_startup_manager()
    
    try:
        logger.info("=" * 50)
        logger.info("开始加载 YOLOv8 模型...")
        logger.info("=" * 50)
        
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.LOADING,
            progress=0,
            message="开始加载 YOLOv8 模型"
        )
        
        if progress_callback:
            progress_callback(0, "开始加载 YOLOv8")
        
        gpu_before = log_gpu_memory("[YOLO 加载前]")
        result["gpu_memory"]["before"] = {
            "used_mb": gpu_before.used_memory_mb,
            "free_mb": gpu_before.free_memory_mb
        }
        
        if gpu_before.is_available:
            mem_check = check_memory_sufficient(YOLO_ESTIMATED_VRAM_MB)
            if not mem_check["sufficient"]:
                logger.warning(f"显存警告: {mem_check['message']}")
                logger.info("尝试清理 GPU 缓存...")
                from ..utils.gpu_monitor import clear_gpu_cache
                clear_gpu_cache()
        
        if YOLO_MODEL_PATH is None or not YOLO_MODEL_PATH.exists():
            error_msg = f"YOLO 模型文件不存在：{YOLO_MODEL_PATH}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if progress_callback:
            progress_callback(20, "初始化 YOLO 服务")
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.LOADING,
            progress=20,
            message="初始化 YOLO 服务"
        )
        
        from ..services.yolo_service import YOLOv8Service
        
        if progress_callback:
            progress_callback(40, "加载模型权重")
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.LOADING,
            progress=40,
            message="加载模型权重"
        )
        
        yolo_service = YOLOv8Service(model_path=YOLO_MODEL_PATH, auto_load=False)
        yolo_service._load_model()
        
        if progress_callback:
            progress_callback(60, "验证模型")
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.LOADING,
            progress=60,
            message="验证模型"
        )
        
        if not yolo_service.is_loaded:
            raise RuntimeError("YOLO 模型加载失败")
        
        validation_result = yolo_service.validate_disease_classes()
        if validation_result["is_valid"]:
            logger.info(f"YOLO 病害类别校验通过: {len(validation_result['matched_classes'])} 个类别")
        else:
            logger.warning(f"YOLO 病害类别校验未通过，匹配率: {validation_result['match_rate']*100:.1f}%")
        
        if progress_callback:
            progress_callback(80, "初始化推理引擎")
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.LOADING,
            progress=80,
            message="初始化推理引擎"
        )
        
        yolo_service._warmup()
        
        from ..services import yolo_service as yolo_module
        yolo_module._yolo_service = yolo_service
        
        gpu_after = log_gpu_memory("[YOLO 加载后]")
        result["gpu_memory"]["after"] = {
            "used_mb": gpu_after.used_memory_mb,
            "free_mb": gpu_after.free_memory_mb
        }
        
        memory_delta = get_memory_usage_delta(gpu_before, gpu_after)
        result["gpu_memory"]["delta_mb"] = memory_delta["delta_used_mb"]
        
        if progress_callback:
            progress_callback(100, "YOLO 模型加载完成")
        
        load_time = time.time() - start_time
        result["success"] = True
        result["load_time"] = load_time
        result["message"] = f"YOLO 模型加载成功，耗时 {load_time:.2f}秒"
        result["classes_count"] = len(validation_result["matched_classes"])
        
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.READY,
            progress=100,
            message=f"加载成功 ({load_time:.2f}s)"
        )
        
        logger.info(f"YOLO 模型加载完成，耗时 {load_time:.2f}秒")
        logger.info(f"显存变化: +{memory_delta['delta_used_mb']:.0f}MB")
        logger.info("=" * 50)
        
    except Exception as e:
        error_msg = f"YOLO 模型加载失败：{e}"
        logger.error(error_msg)
        result["error"] = str(e)
        
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.FAILED,
            progress=0,
            message="加载失败",
            error=str(e)
        )
        
        startup_mgr.add_error("yolo", str(e), "检查模型路径是否正确，或尝试重新下载模型")
        
        logger.warning("YOLO 服务将使用降级模式...")
        startup_mgr.update_component_status(
            "yolo",
            ComponentStatus.DEGRADED,
            progress=0,
            message="降级模式：模型不可用"
        )
    
    return result


async def preload_qwen_service(progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    预加载 Qwen 服务（集成 GPU 显存监控）
    
    Args:
        progress_callback: 进度回调函数，接收 (progress: int, message: str)
    
    Returns:
        加载结果字典
    """
    start_time = time.time()
    result = {
        "success": False,
        "model": "Qwen3-VL-2B-Instruct",
        "path": str(QWEN_MODEL_PATH),
        "load_time": 0.0,
        "error": None,
        "gpu_memory": {},
        "quantization": "BF16"
    }
    
    startup_mgr = get_startup_manager()
    
    try:
        logger.info("=" * 50)
        logger.info("开始加载 Qwen3-VL-2B-Instruct 模型...")
        logger.info("=" * 50)
        
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.LOADING,
            progress=0,
            message="开始加载 Qwen3-VL 模型"
        )
        
        if progress_callback:
            progress_callback(0, "开始加载 Qwen3-VL")
        
        gpu_before = log_gpu_memory("[Qwen 加载前]")
        result["gpu_memory"]["before"] = {
            "used_mb": gpu_before.used_memory_mb,
            "free_mb": gpu_before.free_memory_mb
        }
        
        cpu_offload_mode = False
        if gpu_before.is_available:
            required_memory = QWEN_INT4_ESTIMATED_VRAM_MB
            mem_check = check_memory_sufficient(required_memory)
            if not mem_check["sufficient"]:
                logger.warning(f"显存警告: {mem_check['message']}")
                logger.info("尝试清理 GPU 缓存...")
                from ..utils.gpu_monitor import clear_gpu_cache
                clear_gpu_cache()
                
                gpu_before = log_gpu_memory("[Qwen 加载前-重试]")
                result["gpu_memory"]["before"] = {
                    "used_mb": gpu_before.used_memory_mb,
                    "free_mb": gpu_before.free_memory_mb
                }
        else:
            logger.warning("GPU 不可用，将使用 CPU Offload 模式加载 Qwen 模型")
            cpu_offload_mode = True
        
        if not QWEN_MODEL_PATH.exists():
            error_msg = f"Qwen 模型目录不存在：{QWEN_MODEL_PATH}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if progress_callback:
            progress_callback(10, "初始化 Qwen 服务")
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.LOADING,
            progress=10,
            message="初始化 Qwen 服务"
        )
        
        from ..services.qwen_service import QwenService
        
        stages = [
            (20, "加载处理器"),
            (30, "配置量化参数"),
            (40, "加载视觉编码器"),
            (60, "加载语言模型"),
            (80, "初始化推理引擎")
        ]
        
        for progress, message in stages:
            if progress_callback:
                progress_callback(progress, message)
            startup_mgr.update_component_status(
                "qwen",
                ComponentStatus.LOADING,
                progress=progress,
                message=message
            )
            await asyncio.sleep(0.3)
        
        if cpu_offload_mode:
            logger.info("正在加载 Qwen 模型权重（CPU Offload 模式）...")
        else:
            logger.info("正在加载 Qwen 模型权重（INT4 量化 + GPU 模式）...")
        qwen_service = QwenService(
            model_path=QWEN_MODEL_PATH,
            load_in_4bit=not cpu_offload_mode,
            enable_graph_rag=True,
            auto_load=True,
            cpu_offload=cpu_offload_mode,
            lazy_load=False
        )
        
        if progress_callback:
            progress_callback(85, "验证模型")
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.LOADING,
            progress=85,
            message="验证模型"
        )
        
        if not qwen_service.is_loaded:
            raise RuntimeError("Qwen 模型加载失败")
        
        if progress_callback:
            progress_callback(90, "预热模型")
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.LOADING,
            progress=90,
            message="预热模型"
        )
        
        qwen_service._warmup()
        
        from ..services import qwen_service as qwen_module
        qwen_module._qwen_service = qwen_service
        
        gpu_after = log_gpu_memory("[Qwen 加载后]")
        result["gpu_memory"]["after"] = {
            "used_mb": gpu_after.used_memory_mb,
            "free_mb": gpu_after.free_memory_mb
        }
        
        memory_delta = get_memory_usage_delta(gpu_before, gpu_after)
        result["gpu_memory"]["delta_mb"] = memory_delta["delta_used_mb"]
        
        if progress_callback:
            progress_callback(100, "Qwen 模型加载完成")
        
        load_time = time.time() - start_time
        result["success"] = True
        result["load_time"] = load_time
        result["message"] = f"Qwen 模型加载成功，耗时 {load_time:.2f}秒"
        
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.READY,
            progress=100,
            message=f"加载成功 ({load_time:.2f}s)"
        )
        
        logger.info(f"Qwen 模型加载完成，耗时 {load_time:.2f}秒")
        logger.info(f"显存变化: +{memory_delta['delta_used_mb']:.0f}MB")
        logger.info("量化模式: INT4 (显存占用约 2.6GB)")
        logger.info("=" * 50)
        
    except Exception as e:
        error_msg = f"Qwen 模型加载失败：{e}"
        logger.error(error_msg)
        result["error"] = str(e)
        
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.FAILED,
            progress=0,
            message="加载失败",
            error=str(e)
        )
        
        startup_mgr.add_error("qwen", str(e), "检查模型路径、GPU 显存是否充足，或尝试使用 CPU 模式")
        
        logger.warning("Qwen 服务将使用降级模式...")
        startup_mgr.update_component_status(
            "qwen",
            ComponentStatus.DEGRADED,
            progress=0,
            message="降级模式：模型不可用"
        )
    
    return result


async def preload_ai_services() -> Dict[str, Any]:
    """
    预加载所有 AI 服务（优化版）
    
    Returns:
        加载结果汇总
    """
    logger.info("=" * 70)
    logger.info("开始预加载 AI 服务")
    logger.info("=" * 70)
    
    startup_mgr = get_startup_manager()
    startup_mgr.update_phase(StartupPhase.AI_LOADING, "开始预加载 AI 服务")
    
    results = {
        "yolo": None,
        "qwen": None,
        "total_time": 0.0,
        "success_count": 0,
        "failed_count": 0,
        "gpu_info": {}
    }
    
    total_start = time.time()
    
    device_info = startup_mgr.get_device_info()
    results["gpu_info"] = device_info
    
    if device_info.get("cuda_available"):
        logger.info(f"检测到 GPU: {device_info.get('devices', [])}")
    else:
        logger.warning("未检测到可用 GPU，AI 模型可能无法正常加载")
    
    def yolo_progress(progress: int, message: str):
        overall = 40 + int(progress * 0.2)
        startup_mgr.progress.overall_progress = overall
        logger.info(f"[AI 加载] YOLO: {progress}% - {message} (总体进度：{overall}%)")
    
    def qwen_progress(progress: int, message: str):
        overall = 60 + int(progress * 0.3)
        startup_mgr.progress.overall_progress = overall
        logger.info(f"[AI 加载] Qwen: {progress}% - {message} (总体进度：{overall}%)")
    
    logger.info("-" * 50)
    logger.info("阶段 1/2: 加载 YOLOv8 模型 (总体进度 40-60%)")
    logger.info("-" * 50)
    results["yolo"] = await preload_yolo_service(yolo_progress)
    
    if results["yolo"]["success"]:
        results["success_count"] += 1
    else:
        results["failed_count"] += 1
    
    logger.info("-" * 50)
    logger.info("阶段 2/2: 加载 Qwen3-VL 模型 (总体进度 60-90%)")
    logger.info("-" * 50)
    results["qwen"] = await preload_qwen_service(qwen_progress)
    
    if results["qwen"]["success"]:
        results["success_count"] += 1
    else:
        results["failed_count"] += 1
    
    results["total_time"] = time.time() - total_start
    
    final_gpu = log_gpu_memory("[AI 服务加载完成]")
    results["final_gpu_memory"] = {
        "used_mb": final_gpu.used_memory_mb,
        "free_mb": final_gpu.free_memory_mb,
        "utilization_percent": final_gpu.utilization_percent
    }
    
    logger.info("=" * 70)
    logger.info("AI 服务预加载完成")
    logger.info(f"总耗时：{results['total_time']:.2f}秒")
    logger.info(f"成功：{results['success_count']}/2")
    logger.info(f"失败：{results['failed_count']}/2")
    logger.info(f"最终显存占用：{final_gpu.used_memory_mb:.0f}MB / {final_gpu.total_memory_mb:.0f}MB ({final_gpu.utilization_percent:.1f}%)")
    logger.info("=" * 70)
    
    startup_mgr.progress.overall_progress = 90
    
    return results
