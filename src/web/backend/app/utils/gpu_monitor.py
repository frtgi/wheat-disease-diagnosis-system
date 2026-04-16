"""
GPU 显存监控工具模块

提供 GPU 显存状态监控、日志记录和可用性检查功能
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPUMemoryInfo:
    """GPU 显存信息数据类"""
    total_memory_mb: float
    used_memory_mb: float
    free_memory_mb: float
    utilization_percent: float
    is_available: bool
    device_name: str = "Unknown"
    device_count: int = 0


def check_gpu_available() -> bool:
    """
    检查 GPU 是否可用
    
    返回:
        bool: GPU 是否可用
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        logger.warning("PyTorch 未安装，无法检测 GPU")
        return False
    except Exception as e:
        logger.warning(f"检测 GPU 时发生错误: {e}")
        return False


def get_gpu_memory_info(device_id: int = 0) -> GPUMemoryInfo:
    """
    获取 GPU 显存信息
    
    参数:
        device_id: GPU 设备 ID，默认为 0
    
    返回:
        GPUMemoryInfo: GPU 显存信息对象
    """
    try:
        import torch
        
        if not torch.cuda.is_available():
            return GPUMemoryInfo(
                total_memory_mb=0,
                used_memory_mb=0,
                free_memory_mb=0,
                utilization_percent=0,
                is_available=False,
                device_name="CPU",
                device_count=0
            )
        
        device_count = torch.cuda.device_count()
        
        if device_id >= device_count:
            logger.warning(f"GPU 设备 {device_id} 不存在，使用设备 0")
            device_id = 0
        
        torch.cuda.set_device(device_id)
        
        total_memory = torch.cuda.get_device_properties(device_id).total_memory
        reserved_memory = torch.cuda.memory_reserved(device_id)
        allocated_memory = torch.cuda.memory_allocated(device_id)
        
        used_memory = min(reserved_memory, total_memory)
        free_memory = total_memory - used_memory
        
        total_mb = total_memory / (1024 ** 2)
        reserved_mb = reserved_memory / (1024 ** 2)
        allocated_mb = allocated_memory / (1024 ** 2)
        used_mb = used_memory / (1024 ** 2)
        free_mb = free_memory / (1024 ** 2)
        
        utilization = (used_memory / total_memory) * 100 if total_memory > 0 else 0
        
        device_name = torch.cuda.get_device_name(device_id)
        
        return GPUMemoryInfo(
            total_memory_mb=round(total_mb, 2),
            used_memory_mb=round(used_mb, 2),
            free_memory_mb=round(free_mb, 2),
            utilization_percent=round(utilization, 2),
            is_available=True,
            device_name=device_name,
            device_count=device_count
        )
        
    except ImportError:
        logger.warning("PyTorch 未安装，无法获取 GPU 显存信息")
        return GPUMemoryInfo(
            total_memory_mb=0,
            used_memory_mb=0,
            free_memory_mb=0,
            utilization_percent=0,
            is_available=False
        )
    except Exception as e:
        logger.error(f"获取 GPU 显存信息失败: {e}")
        return GPUMemoryInfo(
            total_memory_mb=0,
            used_memory_mb=0,
            free_memory_mb=0,
            utilization_percent=0,
            is_available=False
        )


def log_gpu_memory(prefix: str = "", device_id: int = 0) -> GPUMemoryInfo:
    """
    记录 GPU 显存状态到日志
    
    参数:
        prefix: 日志前缀，用于标识记录点
        device_id: GPU 设备 ID，默认为 0
    
    返回:
        GPUMemoryInfo: GPU 显存信息对象
    """
    info = get_gpu_memory_info(device_id)
    
    if info.is_available:
        log_message = (
            f"{prefix} GPU 显存状态: "
            f"设备={info.device_name}, "
            f"总计={info.total_memory_mb:.0f}MB, "
            f"已用={info.used_memory_mb:.0f}MB, "
            f"可用={info.free_memory_mb:.0f}MB, "
            f"利用率={info.utilization_percent:.1f}%"
        )
        logger.info(log_message)
    else:
        logger.info(f"{prefix} GPU 不可用，将使用 CPU 模式")
    
    return info


def check_memory_sufficient(required_memory_mb: float, device_id: int = 0) -> Dict[str, Any]:
    """
    检查 GPU 显存是否足够
    
    参数:
        required_memory_mb: 所需显存大小（MB）
        device_id: GPU 设备 ID，默认为 0
    
    返回:
        Dict: 包含检查结果的字典
            - sufficient: 是否足够
            - available_memory_mb: 可用显存
            - required_memory_mb: 所需显存
            - message: 状态消息
    """
    info = get_gpu_memory_info(device_id)
    
    if not info.is_available:
        return {
            "sufficient": False,
            "available_memory_mb": 0,
            "required_memory_mb": required_memory_mb,
            "message": "GPU 不可用"
        }
    
    sufficient = info.free_memory_mb >= required_memory_mb
    
    if sufficient:
        message = f"显存充足: 可用 {info.free_memory_mb:.0f}MB >= 所需 {required_memory_mb:.0f}MB"
    else:
        message = f"显存不足: 可用 {info.free_memory_mb:.0f}MB < 所需 {required_memory_mb:.0f}MB"
    
    return {
        "sufficient": sufficient,
        "available_memory_mb": info.free_memory_mb,
        "required_memory_mb": required_memory_mb,
        "message": message
    }


def get_memory_usage_delta(start_info: GPUMemoryInfo, end_info: GPUMemoryInfo) -> Dict[str, float]:
    """
    计算显存使用变化量
    
    参数:
        start_info: 起始显存信息
        end_info: 结束显存信息
    
    返回:
        Dict: 显存变化量信息
    """
    delta_used = end_info.used_memory_mb - start_info.used_memory_mb
    delta_free = end_info.free_memory_mb - start_info.free_memory_mb
    
    return {
        "delta_used_mb": round(delta_used, 2),
        "delta_free_mb": round(delta_free, 2),
        "start_used_mb": start_info.used_memory_mb,
        "end_used_mb": end_info.used_memory_mb
    }


def clear_gpu_cache() -> bool:
    """
    清理 GPU 缓存
    
    返回:
        bool: 是否成功清理
    """
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU 缓存已清理")
            return True
        return False
    except ImportError:
        return False
    except Exception as e:
        logger.warning(f"清理 GPU 缓存失败: {e}")
        return False


def get_device_info() -> Dict[str, Any]:
    """
    获取所有 GPU 设备信息
    
    返回:
        Dict: 包含所有设备信息的字典
    """
    try:
        import torch
        
        if not torch.cuda.is_available():
            return {
                "cuda_available": False,
                "device_count": 0,
                "devices": [],
                "message": "CUDA 不可用"
            }
        
        device_count = torch.cuda.device_count()
        devices = []
        
        for i in range(device_count):
            props = torch.cuda.get_device_properties(i)
            devices.append({
                "id": i,
                "name": props.name,
                "total_memory_mb": round(props.total_memory / (1024 ** 2), 2),
                "multi_processor_count": props.multi_processor_count,
                "compute_capability": f"{props.major}.{props.minor}"
            })
        
        return {
            "cuda_available": True,
            "device_count": device_count,
            "devices": devices,
            "current_device": torch.cuda.current_device()
        }
        
    except ImportError:
        return {
            "cuda_available": False,
            "device_count": 0,
            "devices": [],
            "message": "PyTorch 未安装"
        }
    except Exception as e:
        return {
            "cuda_available": False,
            "device_count": 0,
            "devices": [],
            "message": str(e)
        }
