"""
GPU 显存监控核心模块

此模块已合并至 app.utils.gpu_monitor，所有功能从该模块重新导出以保持向后兼容。
新代码请直接使用: from app.utils.gpu_monitor import ...
"""
from app.utils.gpu_monitor import (
    GPUMemoryInfo,
    GPUStatus,
    check_gpu_available,
    get_gpu_memory_info,
    log_gpu_memory,
    check_memory_sufficient,
    get_memory_usage_delta,
    clear_gpu_cache,
    get_device_info,
    get_gpu_memory_threshold,
    get_max_concurrent_diagnosis,
    get_gpu_status,
    check_gpu_memory_available,
    get_memory_usage_percent,
    get_memory_usage_percent_from_status,
    get_gpu_info_dict,
    GPU_MEMORY_THRESHOLD,
    MAX_CONCURRENT_DIAGNOSIS,
)

__all__ = [
    "GPUMemoryInfo",
    "GPUStatus",
    "check_gpu_available",
    "get_gpu_memory_info",
    "log_gpu_memory",
    "check_memory_sufficient",
    "get_memory_usage_delta",
    "clear_gpu_cache",
    "get_device_info",
    "get_gpu_memory_threshold",
    "get_max_concurrent_diagnosis",
    "get_gpu_status",
    "check_gpu_memory_available",
    "get_memory_usage_percent",
    "get_memory_usage_percent_from_status",
    "get_gpu_info_dict",
    "GPU_MEMORY_THRESHOLD",
    "MAX_CONCURRENT_DIAGNOSIS",
]
