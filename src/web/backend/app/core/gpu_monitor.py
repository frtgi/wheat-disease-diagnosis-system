"""
GPU 显存监控模块
提供 GPU 显存使用率监控和告警功能
"""
import logging
import subprocess
import json
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GPUStatus:
    """GPU 状态数据类"""

    gpu_id: int
    name: str
    memory_total_mb: int  # 总显存（MB）
    memory_used_mb: int   # 已用显存（MB）
    memory_free_mb: int   # 可用显存（MB）
    utilization_gpu: float    # GPU 利用率 (%)
    utilization_memory: float # 显存利用率 (%)
    timestamp: datetime


# 默认配置（已迁移至 Settings，保留向后兼容的模块级引用）
GPU_MEMORY_THRESHOLD = 0.90
MAX_CONCURRENT_DIAGNOSIS = 3

def get_gpu_memory_threshold() -> float:
    """获取 GPU 显存告警阈值（从配置中心读取）"""
    return settings.GPU_MEMORY_THRESHOLD

def get_max_concurrent_diagnosis() -> int:
    """获取最大并发诊断数（从配置中心读取）"""
    return settings.MAX_CONCURRENT_DIAGNOSIS

# nvidia-smi 是否可用的缓存标志
_nvidia_smi_available: Optional[bool] = None


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
    获取当前 GPU 状态信息
    
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


def check_gpu_memory_available(required_mb: int = 500) -> tuple[bool, str]:
    """
    检查 GPU 显存是否足够
    
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
    获取显存使用率百分比
    
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
    获取 GPU 信息字典（用于 API 响应或日志）
    
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
