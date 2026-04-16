"""
GPU 显存管理工具模块

提供显存监控、自动清理和 VRAM 感知的资源管理功能，
确保在 4GB 显存限制下稳定运行。

核心功能：
1. 实时显存监控和阈值告警
2. 推理后自动清理 GPU 缓存
3. VRAM 感知的批处理大小调整
4. 显存碎片整理优化
"""
import logging
import gc
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class VRAMManager:
    """
    GPU 显存管理器

    监控 GPU 显存使用情况，在推理前后执行显存优化操作，
    确保应用在 4GB 显存限制下稳定运行。

    使用方式：
    - with vram_manager.inference_context(): 进行推理
    - vram_manager.get_optimal_batch_size() 获取建议批处理大小
    - vram_manager.cleanup() 手动触发清理
    """

    def __init__(
        self,
        max_vram_mb: int = 4096,
        warning_threshold: float = 0.80,
        critical_threshold: float = 0.92,
        cleanup_after_inference: bool = True
    ):
        """
        初始化显存管理器

        Args:
            max_vram_mb: 最大显存限制（MB），默认 4096 (4GB)
            warning_threshold: 显存使用率警告阈值（0-1）
            critical_threshold: 显存使用率临界阈值（0-1）
            cleanup_after_inference: 推理后是否自动清理
        """
        self.max_vram_mb = max_vram_mb
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.cleanup_after_inference = cleanup_after_inference
        self._cuda_available = self._check_cuda()

    def _check_cuda(self) -> bool:
        """
        检查 CUDA 是否可用

        Returns:
            bool: CUDA 是否可用
        """
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def get_vram_usage(self) -> Dict[str, float]:
        """
        获取当前显存使用情况

        Returns:
            Dict[str, float]: 显存使用信息，包含已用、空闲、总量（MB）和使用率
        """
        if not self._cuda_available:
            return {
                "used_mb": 0,
                "free_mb": self.max_vram_mb,
                "total_mb": self.max_vram_mb,
                "usage_ratio": 0.0
            }

        try:
            import torch
            used = torch.cuda.memory_allocated() / (1024 * 1024)
            reserved = torch.cuda.memory_reserved() / (1024 * 1024)
            total = torch.cuda.get_device_properties(0).total_mem / (1024 * 1024)
            free = total - reserved

            return {
                "used_mb": round(used, 2),
                "free_mb": round(free, 2),
                "total_mb": round(total, 2),
                "reserved_mb": round(reserved, 2),
                "usage_ratio": round(reserved / total, 4) if total > 0 else 0.0
            }
        except Exception as e:
            logger.warning(f"获取显存信息失败: {e}")
            return {
                "used_mb": 0,
                "free_mb": self.max_vram_mb,
                "total_mb": self.max_vram_mb,
                "usage_ratio": 0.0
            }

    def is_vram_sufficient(self, required_mb: int = 512) -> bool:
        """
        检查显存是否充足

        Args:
            required_mb: 所需显存（MB）

        Returns:
            bool: 显存是否充足
        """
        usage = self.get_vram_usage()
        return usage["free_mb"] >= required_mb

    def get_optimal_batch_size(self, base_batch_size: int = 1) -> int:
        """
        根据当前显存情况获取最优批处理大小

        在 4GB 显存限制下，INT4 量化的 Qwen3-VL-2B 模型约占用 1.5GB，
        推理时 KV Cache 和中间激活值需要额外显存。

        Args:
            base_batch_size: 基础批处理大小

        Returns:
            int: 建议的批处理大小
        """
        if not self._cuda_available:
            return base_batch_size

        usage = self.get_vram_usage()
        free_mb = usage["free_mb"]

        per_image_mb = 256

        if free_mb < 512:
            logger.warning(f"显存不足（空闲 {free_mb:.0f}MB），建议批处理大小为 1")
            return 1

        max_batch = max(1, int(free_mb / per_image_mb))
        optimal = min(base_batch_size, max_batch)

        if optimal < base_batch_size:
            logger.info(f"显存受限（空闲 {free_mb:.0f}MB），批处理大小从 {base_batch_size} 调整为 {optimal}")

        return optimal

    def cleanup(self, aggressive: bool = False) -> Dict[str, Any]:
        """
        执行显存清理操作

        Args:
            aggressive: 是否执行激进清理（包括 Python GC）

        Returns:
            Dict[str, Any]: 清理前后显存对比
        """
        before = self.get_vram_usage()

        if not self._cuda_available:
            return {"before": before, "after": before, "freed_mb": 0}

        try:
            import torch

            if aggressive:
                gc.collect()

            torch.cuda.empty_cache()

            if aggressive:
                torch.cuda.synchronize()
                gc.collect()

            after = self.get_vram_usage()
            freed_mb = before["reserved_mb"] - after["reserved_mb"]

            if freed_mb > 0:
                logger.info(f"显存清理完成，释放 {freed_mb:.1f}MB（{before['reserved_mb']:.0f}MB -> {after['reserved_mb']:.0f}MB）")

            return {
                "before": before,
                "after": after,
                "freed_mb": round(freed_mb, 2)
            }
        except Exception as e:
            logger.error(f"显存清理失败: {e}")
            return {"before": before, "after": before, "freed_mb": 0}

    def check_and_warn(self) -> bool:
        """
        检查显存使用率并发出警告

        Returns:
            bool: 是否超过临界阈值
        """
        usage = self.get_vram_usage()
        ratio = usage["usage_ratio"]

        if ratio >= self.critical_threshold:
            logger.critical(
                f"显存使用率 {ratio:.1%} 超过临界阈值 {self.critical_threshold:.0%}，"
                f"已用 {usage['reserved_mb']:.0f}MB / {usage['total_mb']:.0f}MB"
            )
            self.cleanup(aggressive=True)
            return True

        if ratio >= self.warning_threshold:
            logger.warning(
                f"显存使用率 {ratio:.1%} 超过警告阈值 {self.warning_threshold:.0%}，"
                f"已用 {usage['reserved_mb']:.0f}MB / {usage['total_mb']:.0f}MB"
            )
            self.cleanup(aggressive=False)

        return False

    @contextmanager
    def inference_context(self):
        """
        推理上下文管理器

        在推理前检查显存，推理后自动清理。
        确保每次推理后 GPU 缓存被及时释放。

        Yields:
            VRAMManager: 自身实例
        """
        self.check_and_warn()
        try:
            yield self
        finally:
            if self.cleanup_after_inference:
                self.cleanup(aggressive=False)


_vram_manager: Optional[VRAMManager] = None


def get_vram_manager() -> VRAMManager:
    """
    获取全局显存管理器实例

    Returns:
        VRAMManager: 显存管理器实例
    """
    global _vram_manager
    if _vram_manager is None:
        try:
            from app.core.ai_config import ai_config
            _vram_manager = VRAMManager(
                max_vram_mb=4096,
                warning_threshold=ai_config.CUDA_MEMORY_WARNING_THRESHOLD,
                critical_threshold=ai_config.CUDA_MEMORY_CRITICAL_THRESHOLD,
                cleanup_after_inference=True
            )
        except Exception:
            _vram_manager = VRAMManager()
    return _vram_manager
