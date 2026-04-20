"""
GPU 显存监控工具模块

提供 GPU 显存状态监控、日志记录和可用性检查功能
支持两种后端：
1. PyTorch (torch.cuda) - 用于程序内 GPU 信息获取
2. nvidia-smi - 用于系统级 GPU 状态监控和告警
"""
import logging
import subprocess
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from app.core.config import settings
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False


@dataclass
class GPUMemoryInfo:
    """GPU 显存信息数据类（基于 PyTorch）"""
    total_memory_mb: float
    used_memory_mb: float
    free_memory_mb: float
    utilization_percent: float
    is_available: bool
    device_name: str = "Unknown"
    device_count: int = 0


@dataclass
class GPUStatus:
    """GPU 状态数据类（基于 nvidia-smi）"""
    gpu_id: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    memory_free_mb: int
    utilization_gpu: float
    utilization_memory: float
    timestamp: datetime


def check_gpu_available() -> bool:
    """
    检查 GPU 是否可用（基于 PyTorch）

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
    获取 GPU 显存信息（基于 PyTorch）

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
    检查 GPU 显存是否足够（基于 PyTorch）

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
    获取所有 GPU 设备信息（基于 PyTorch）

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


# ========== nvidia-smi 后端功能 ==========

_nvidia_smi_available: Optional[bool] = None

GPU_MEMORY_THRESHOLD = 0.90
MAX_CONCURRENT_DIAGNOSIS = 3


def get_gpu_memory_threshold() -> float:
    """获取 GPU 显存告警阈值（从配置中心读取）"""
    if _CONFIG_AVAILABLE:
        return settings.GPU_MEMORY_THRESHOLD
    return GPU_MEMORY_THRESHOLD


def get_max_concurrent_diagnosis() -> int:
    """获取最大并发诊断数（从配置中心读取）"""
    if _CONFIG_AVAILABLE:
        return settings.MAX_CONCURRENT_DIAGNOSIS
    return MAX_CONCURRENT_DIAGNOSIS


def _is_nvidia_smi_available() -> bool:
    """
    检测 nvidia-smi 命令是否可用

    通过尝试执行 nvidia-smi --version 来判断，
    结果会被缓存以避免重复检测。

    Returns:
        bool: nvidia-smi 是否可用
    """
    global _nvidia_smi_available
    if _nvidia_smi_available is not None:
        return _nvidia_smi_available
    try:
        result = subprocess.run(
            ["nvidia-smi", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if __import__("os").name == "nt" else 0
        )
        _nvidia_smi_available = result.returncode == 0
        if _nvidia_smi_available:
            logger.info("nvidia-smi 可用，GPU 监控功能已启用")
        else:
            logger.warning("nvidia-smi 返回非零退出码，GPU 监控功能将禁用")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        _nvidia_smi_available = False
        logger.warning(f"nvidia-smi 不可用 ({e})，GPU 监控功能将禁用，仅使用并发限流")
    return _nvidia_smi_available


def get_gpu_status() -> Optional[GPUStatus]:
    """
    获取当前 GPU 状态信息（基于 nvidia-smi）

    使用 nvidia-smi 命令查询 GPU 状态，
    如果 nvidia-smi 不可用或执行失败则返回 None。

    Returns:
        GPUStatus 对象，查询失败返回 None
    """
    if not _is_nvidia_smi_available():
        return None

    try:
        query = "index,name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory"
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=" + query,
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if __import__("os").name == "nt" else 0
        )
        if result.returncode != 0:
            logger.warning(f"nvidia-smi 查询失败 (exit code {result.returncode}): {result.stderr.strip()}")
            return None

        lines = result.stdout.strip().split("\n")
        if not lines or not lines[0].strip():
            logger.warning("nvidia-smi 返回空结果")
            return None

        parts = [p.strip() for p in lines[0].split(",")]
        if len(parts) < 7:
            logger.warning(f"nvidia-smi 输出格式异常，期望 7 列，实际 {len(parts)} 列: {lines[0]}")
            return None

        status = GPUStatus(
            gpu_id=int(parts[0]),
            name=parts[1],
            memory_total_mb=int(parts[2]),
            memory_used_mb=int(parts[3]),
            memory_free_mb=int(parts[4]),
            utilization_gpu=float(parts[5]),
            utilization_memory=float(parts[6]),
            timestamp=datetime.now()
        )

        usage_pct = get_memory_usage_percent_from_status(status)
        if usage_pct >= get_gpu_memory_threshold():
            logger.warning(
                f"GPU 显存使用率超过阈值: {usage_pct:.1%} "
                f"(已用 {status.memory_used_mb}MB / 总计 {status.memory_total_mb}MB)，"
                f"GPU 利用率 {status.utilization_gpu:.1f}%"
            )
        else:
            logger.debug(
                f"GPU 状态正常: 显存 {usage_pct:.1%} "
                f"({status.memory_used_mb}/{status.memory_total_mb}MB), "
                f"GPU 利用率 {status.utilization_gpu:.1f}%"
            )

        return status

    except subprocess.TimeoutExpired:
        logger.error("nvidia-smi 查询超时（10秒）")
        return None
    except ValueError as e:
        logger.warning(f"nvidia-smi 结果解析错误: {e}")
        return None
    except Exception as e:
        logger.error(f"获取 GPU 状态异常: {e}", exc_info=True)
        return None


def check_gpu_memory_available(required_mb: int = 500) -> Tuple[bool, str]:
    """
    检查 GPU 显存是否足够（基于 nvidia-smi）

    Args:
        required_mb: 所需显存（MB），默认 500MB

    Returns:
        tuple[bool, str]: (是否可用, 原因描述)
    """
    if not _is_nvidia_smi_available():
        return True, "nvidia-smi 不可用，跳过显存检查"

    status = get_gpu_status()
    if status is None:
        logger.warning("无法获取 GPU 状态，默认允许请求通过（仅依赖并发限流）")
        return True, "无法获取 GPU 状态，跳过显存检查"

    if status.memory_free_mb < required_mb:
        reason = (
            f"GPU 显存不足: 可用 {status.memory_free_mb}MB < 需要 {required_mb}MB "
            f"(总显存 {status.memory_total_mb}MB, 已用 {status.memory_used_mb}MB)"
        )
        logger.warning(reason)
        return False, reason

    return True, f"显存充足: 可用 {status.memory_free_mb}MB >= 需要 {required_mb}MB"


def get_memory_usage_percent() -> float:
    """
    获取显存使用率百分比（基于 nvidia-smi）

    Returns:
        float: 0.0-1.0 的浮点数，获取失败返回 -1.0
    """
    status = get_gpu_status()
    if status is None:
        return -1.0
    return get_memory_usage_percent_from_status(status)


def get_memory_usage_percent_from_status(status: GPUStatus) -> float:
    """
    从 GPUStatus 对象计算显存使用率

    Args:
        status: GPU 状态对象

    Returns:
        float: 0.0-1.0 的浮点数
    """
    if status.memory_total_mb <= 0:
        return 0.0
    return status.memory_used_mb / status.memory_total_mb


def get_gpu_info_dict() -> dict:
    """
    获取 GPU 信息字典（基于 nvidia-smi，用于 API 响应或日志）

    Returns:
        dict: 包含 GPU 状态信息的字典，不可用时返回空字典
    """
    status = get_gpu_status()
    if status is None:
        return {"available": False, "reason": "nvidia-smi 不可用或查询失败"}
    info = asdict(status)
    info["timestamp"] = status.timestamp.isoformat()
    info["memory_usage_percent"] = round(get_memory_usage_percent_from_status(status), 4)
    info["available"] = True
    return info
