"""
批处理优化服务模块

提供动态 batching 和 GPU 资源管理：
1. 请求队列管理
2. 自适应 batch size
3. GPU 显存监控
4. 防止 OOM 错误
"""

import asyncio
import time
import logging
import gc
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from collections import deque
import threading

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """批处理请求"""
    id: str
    image_data: Any
    symptoms: str
    future: asyncio.Future = field(default=None)
    created_at: float = field(default_factory=time.time)
    priority: int = 0  # 0 为普通优先级，数字越大优先级越高


@dataclass
class BatchResult:
    """批处理结果"""
    request_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0


class GPUMonitor:
    """GPU 显存监控"""
    
    def __init__(self, gpu_id: int = 0):
        """
        初始化 GPU 监控
        
        Args:
            gpu_id: GPU ID
        """
        self.gpu_id = gpu_id
        self._history: deque = deque(maxlen=100)
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取 GPU 显存信息"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return {
                "available": False,
                "message": "CUDA 不可用"
            }
        
        try:
            total_memory = torch.cuda.get_device_properties(self.gpu_id).total_memory
            allocated_memory = torch.cuda.memory_allocated(self.gpu_id)
            reserved_memory = torch.cuda.memory_reserved(self.gpu_id)
            free_memory = total_memory - allocated_memory
            
            info = {
                "available": True,
                "gpu_id": self.gpu_id,
                "total_memory_mb": round(total_memory / (1024 ** 2), 2),
                "allocated_memory_mb": round(allocated_memory / (1024 ** 2), 2),
                "reserved_memory_mb": round(reserved_memory / (1024 ** 2), 2),
                "free_memory_mb": round(free_memory / (1024 ** 2), 2),
                "utilization_percent": round(allocated_memory / total_memory * 100, 2)
            }
            
            self._history.append({
                "timestamp": time.time(),
                "allocated_mb": info["allocated_memory_mb"],
                "free_mb": info["free_memory_mb"]
            })
            
            return info
            
        except Exception as e:
            logger.error(f"获取 GPU 信息失败：{e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def is_memory_sufficient(self, required_mb: float = 512) -> bool:
        """检查是否有足够的显存"""
        info = self.get_memory_info()
        if not info.get("available"):
            return False
        
        return info.get("free_memory_mb", 0) >= required_mb
    
    def get_memory_pressure(self) -> str:
        """获取显存压力等级"""
        info = self.get_memory_info()
        if not info.get("available"):
            return "unknown"
        
        utilization = info.get("utilization_percent", 0)
        
        if utilization < 50:
            return "low"
        elif utilization < 75:
            return "medium"
        elif utilization < 90:
            return "high"
        else:
            return "critical"
    
    def clear_cache(self) -> None:
        """清理 GPU 缓存"""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                gc.collect()
                logger.info("GPU 缓存已清理")
            except Exception as e:
                logger.error(f"清理 GPU 缓存失败：{e}")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取显存使用历史"""
        return list(self._history)


class DynamicBatcher:
    """动态批处理器"""
    
    def __init__(
        self,
        max_batch_size: int = 16,
        min_batch_size: int = 1,
        max_wait_time: float = 0.5,
        gpu_monitor: Optional[GPUMonitor] = None
    ):
        """
        初始化动态批处理器
        
        Args:
            max_batch_size: 最大 batch size
            min_batch_size: 最小 batch size
            max_wait_time: 最大等待时间（秒）
            gpu_monitor: GPU 监控器
        """
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
        self.max_wait_time = max_wait_time
        self.gpu_monitor = gpu_monitor or GPUMonitor()
        
        self._queue: deque[BatchRequest] = deque()
        self._lock = threading.Lock()
        self._current_batch_size = max_batch_size
        self._stats = {
            "total_requests": 0,
            "total_batches": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time": 0.0,
            "avg_processing_time": 0.0
        }
    
    def add_request(
        self,
        request_id: str,
        image_data: Any,
        symptoms: str,
        priority: int = 0
    ) -> asyncio.Future:
        """
        添加请求到队列
        
        Args:
            request_id: 请求 ID
            image_data: 图像数据
            symptoms: 症状描述
            priority: 优先级
        
        Returns:
            Future 对象，用于获取结果
        """
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        request = BatchRequest(
            id=request_id,
            image_data=image_data,
            symptoms=symptoms,
            future=future,
            priority=priority
        )
        
        with self._lock:
            # 高优先级插入队首，普通优先级追加到队尾
            if priority > 0:
                self._queue.appendleft(request)
            else:
                self._queue.append(request)
            
            self._stats["total_requests"] += 1
        
        logger.debug(f"请求已添加：{request_id}, 队列长度：{len(self._queue)}")
        return future
    
    def _adjust_batch_size(self) -> int:
        """根据 GPU 显存调整 batch size"""
        pressure = self.gpu_monitor.get_memory_pressure()
        
        if pressure == "critical":
            # 显存严重不足，减小 batch size
            new_size = max(self.min_batch_size, self._current_batch_size // 2)
            logger.warning(f"显存压力严重，batch size 调整为：{new_size}")
        elif pressure == "high":
            # 显存压力高，适度减小
            new_size = max(self.min_batch_size, int(self._current_batch_size * 0.75))
            logger.info(f"显存压力高，batch size 调整为：{new_size}")
        elif pressure == "low":
            # 显存充足，增大 batch size
            new_size = min(self.max_batch_size, int(self._current_batch_size * 1.25))
            logger.info(f"显存充足，batch size 调整为：{new_size}")
        else:
            # 保持当前
            new_size = self._current_batch_size
        
        self._current_batch_size = new_size
        return new_size
    
    def _get_next_batch(self) -> List[BatchRequest]:
        """获取下一个批处理批次"""
        with self._lock:
            # 调整 batch size
            batch_size = self._adjust_batch_size()
            
            # 获取队列中的前 batch_size 个请求
            batch = []
            current_time = time.time()
            
            while self._queue and len(batch) < batch_size:
                request = self._queue[0]
                
                # 检查是否超时
                wait_time = current_time - request.created_at
                if wait_time > self.max_wait_time or len(batch) >= self.min_batch_size:
                    batch.append(self._queue.popleft())
                else:
                    break
            
            return batch
    
    async def process_batch(
        self,
        batch: List[BatchRequest],
        process_fn: Callable[[List[Any], str], Awaitable[List[Dict[str, Any]]]]
    ) -> None:
        """
        处理批次
        
        Args:
            batch: 批处理请求列表
            process_fn: 处理函数，接收图像列表和症状，返回结果列表
        """
        if not batch:
            return
        
        start_time = time.time()
        
        try:
            # 提取图像和症状
            images = [req.image_data for req in batch]
            symptoms = batch[0].symptoms  # 使用第一个请求的症状
            
            # 执行批处理
            results = await process_fn(images, symptoms)
            
            # 设置结果
            for req, result in zip(batch, results):
                if not req.future.done():
                    req.future.set_result(BatchResult(
                        request_id=req.id,
                        success=True,
                        result=result,
                        processing_time=time.time() - req.created_at
                    ))
            
            # 更新统计
            processing_time = time.time() - start_time
            self._update_stats(len(batch), processing_time, 
                             sum(time.time() - req.created_at for req in batch))
            
            logger.info(f"批处理完成：{len(batch)} 个请求，耗时 {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"批处理失败：{e}")
            # 设置错误
            for req in batch:
                if not req.future.done():
                    req.future.set_result(BatchResult(
                        request_id=req.id,
                        success=False,
                        error=str(e)
                    ))
    
    def _update_stats(self, batch_size: int, processing_time: float, 
                     total_wait_time: float) -> None:
        """更新统计信息"""
        self._stats["total_batches"]
        
        # 滑动平均
        alpha = 0.1  # 平滑系数
        
        self._stats["total_batches"] += 1
        self._stats["avg_batch_size"] = (
            (1 - alpha) * self._stats["avg_batch_size"] + 
            alpha * batch_size
        )
        self._stats["avg_wait_time"] = (
            (1 - alpha) * self._stats["avg_wait_time"] +
            alpha * (total_wait_time / batch_size if batch_size > 0 else 0)
        )
        self._stats["avg_processing_time"] = (
            (1 - alpha) * self._stats["avg_processing_time"] +
            alpha * processing_time
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取批处理统计"""
        return {
            **self._stats,
            "queue_length": len(self._queue),
            "current_batch_size": self._current_batch_size,
            "gpu_memory": self.gpu_monitor.get_memory_info()
        }
    
    async def run(self, process_fn: Callable[[List[Any], str], Awaitable[List[Dict[str, Any]]]]) -> None:
        """
        运行批处理循环
        
        Args:
            process_fn: 处理函数
        """
        logger.info("批处理循环已启动")
        
        while True:
            try:
                # 获取下一个批次
                batch = self._get_next_batch()
                
                if batch:
                    # 处理批次
                    await self.process_batch(batch, process_fn)
                else:
                    # 队列为空，等待
                    await asyncio.sleep(0.01)
                    
            except asyncio.CancelledError:
                logger.info("批处理循环已停止")
                break
            except Exception as e:
                logger.error(f"批处理循环错误：{e}")
                await asyncio.sleep(1)


class BatchProcessor:
    """批处理管理器（简化版，用于 API 集成）"""
    
    def __init__(self):
        """初始化批处理器"""
        self.gpu_monitor = GPUMonitor()
        self.batcher = DynamicBatcher(
            max_batch_size=10,
            min_batch_size=1,
            max_wait_time=0.3,
            gpu_monitor=self.gpu_monitor
        )
        self._request_counter = 0
    
    def _generate_request_id(self) -> str:
        """生成请求 ID"""
        self._request_counter += 1
        return f"req_{int(time.time())}_{self._request_counter}"
    
    async def process_single(
        self,
        image_data: Any,
        symptoms: str,
        process_fn: Callable[[Any, str], Awaitable[Dict[str, Any]]],
        use_batch: bool = False
    ) -> Dict[str, Any]:
        """
        处理单个请求
        
        Args:
            image_data: 图像数据
            symptoms: 症状描述
            process_fn: 处理函数
            use_batch: 是否使用批处理
        
        Returns:
            处理结果
        """
        start_time = time.time()
        
        if not use_batch:
            # 直接处理
            result = await process_fn(image_data, symptoms)
            return {
                **result,
                "processing_time": time.time() - start_time,
                "batch_mode": False
            }
        
        # 使用批处理
        future = self.batcher.add_request(
            request_id=self._generate_request_id(),
            image_data=image_data,
            symptoms=symptoms
        )
        
        # 等待结果
        batch_result: BatchResult = await future
        
        if batch_result.success:
            return {
                **batch_result.result,
                "processing_time": batch_result.processing_time,
                "batch_mode": True,
                "queue_time": batch_result.processing_time - (time.time() - start_time)
            }
        else:
            return {
                "success": False,
                "error": batch_result.error,
                "processing_time": time.time() - start_time,
                "batch_mode": True
            }
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """获取 GPU 信息"""
        return self.gpu_monitor.get_memory_info()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取批处理统计"""
        return self.batcher.get_stats()
    
    def clear_gpu_cache(self) -> None:
        """清理 GPU 缓存"""
        self.gpu_monitor.clear_cache()


# 全局批处理器实例
batch_processor: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    """获取批处理器实例"""
    global batch_processor
    if batch_processor is None:
        batch_processor = BatchProcessor()
    return batch_processor


def initialize_batch_processor() -> BatchProcessor:
    """初始化批处理器"""
    global batch_processor
    batch_processor = BatchProcessor()
    logger.info("批处理器已初始化")
    return batch_processor
