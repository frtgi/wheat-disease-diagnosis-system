"""
异步推理队列服务
实现请求队列、并发控制、结果缓存

功能特性：
1. 异步请求队列管理
2. 并发控制（限制同时运行的推理任务数）
3. 结果缓存（避免重复计算）
4. 优先级队列支持
5. 超时处理
6. 统计监控
"""
import asyncio
import time
import logging
import hashlib
import threading
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from collections import OrderedDict
from enum import Enum
from datetime import datetime
import gc

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """请求状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Priority(Enum):
    """优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class InferenceRequest:
    """
    推理请求数据类
    
    Attributes:
        request_id: 请求唯一标识
        image: 图像数据（字节或 PIL Image）
        symptoms: 症状描述文本
        callback: 回调函数（可选）
        priority: 请求优先级
        created_at: 创建时间戳
        status: 请求状态
        result: 推理结果
        error: 错误信息
        metadata: 额外元数据
    """
    request_id: str
    image: Optional[bytes] = None
    symptoms: str = ""
    callback: Optional[Callable] = None
    priority: Priority = Priority.NORMAL
    created_at: float = field(default_factory=time.time)
    status: RequestStatus = RequestStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_cache_key(self) -> str:
        """
        生成缓存键
        
        基于图像哈希和症状描述生成唯一缓存键
        
        Returns:
            str: 缓存键
        """
        parts = []
        
        if self.image is not None:
            image_hash = hashlib.md5(self.image).hexdigest()[:16]
            parts.append(f"img_{image_hash}")
        
        if self.symptoms:
            symptoms_hash = hashlib.md5(self.symptoms.encode()).hexdigest()[:8]
            parts.append(f"sym_{symptoms_hash}")
        
        return "_".join(parts) if parts else f"req_{self.request_id}"


@dataclass
class InferenceResult:
    """
    推理结果数据类
    
    Attributes:
        request_id: 请求唯一标识
        success: 是否成功
        result: 推理结果数据
        error: 错误信息
        processing_time_ms: 处理时间（毫秒）
        queue_time_ms: 排队时间（毫秒）
        cache_hit: 是否命中缓存
    """
    request_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0
    queue_time_ms: float = 0.0
    cache_hit: bool = False


class ResultCache:
    """
    结果缓存类
    
    实现 LRU 缓存策略，支持 TTL 过期
    """
    
    def __init__(self, capacity: int = 1000, ttl: int = 1800):
        """
        初始化结果缓存
        
        Args:
            capacity: 缓存容量
            ttl: 缓存过期时间（秒）
        """
        self.capacity = capacity
        self.ttl = ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Dict[str, Any]]: 缓存结果，不存在或已过期返回 None
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            if time.time() - entry["created_at"] > self.ttl:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            return entry["result"]
    
    def set(self, key: str, result: Dict[str, Any]) -> None:
        """
        设置缓存结果
        
        Args:
            key: 缓存键
            result: 缓存结果
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            
            while len(self._cache) >= self.capacity:
                self._cache.popitem(last=False)
            
            self._cache[key] = {
                "result": result,
                "created_at": time.time()
            }
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        return {
            "capacity": self.capacity,
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2)
        }


class AsyncInferenceQueue:
    """
    异步推理队列类
    
    实现异步请求队列、并发控制、结果缓存
    
    Features:
    - 请求队列管理
    - 并发控制
    - 结果缓存
    - 优先级队列
    - 超时处理
    - 统计监控
    """
    
    def __init__(
        self,
        max_concurrent: int = 2,
        max_queue_size: int = 100,
        timeout: int = 120,
        enable_cache: bool = True,
        cache_ttl: int = 1800,
        process_interval_ms: int = 50,
        enable_priority: bool = True
    ):
        """
        初始化异步推理队列
        
        Args:
            max_concurrent: 最大并发推理数
            max_queue_size: 队列最大长度
            timeout: 请求超时时间（秒）
            enable_cache: 是否启用结果缓存
            cache_ttl: 缓存过期时间（秒）
            process_interval_ms: 队列处理间隔（毫秒）
            enable_priority: 是否启用优先级队列
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.timeout = timeout
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.process_interval_ms = process_interval_ms
        self.enable_priority = enable_priority
        
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._pending_requests: Dict[str, InferenceRequest] = {}
        self._results: Dict[str, InferenceResult] = {}
        self._futures: Dict[str, asyncio.Future] = {}
        
        self._cache = ResultCache(
            capacity=500,
            ttl=cache_ttl
        ) if enable_cache else None
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        self._stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "cache_hits": 0,
            "avg_processing_time_ms": 0.0,
            "avg_queue_time_ms": 0.0
        }
        
        self._processing_times: list = []
        self._queue_times: list = []
    
    async def submit(
        self,
        request: InferenceRequest
    ) -> str:
        """
        提交推理请求
        
        Args:
            request: 推理请求对象
            
        Returns:
            str: 请求 ID
            
        Raises:
            RuntimeError: 队列已满或服务未启动
        """
        if not self._running:
            raise RuntimeError("推理队列未启动，请先调用 start() 方法")
        
        if len(self._pending_requests) >= self.max_queue_size:
            raise RuntimeError(f"队列已满，最大容量: {self.max_queue_size}")
        
        async with self._lock:
            self._pending_requests[request.request_id] = request
            self._stats["total_requests"] += 1
            
            priority_value = request.priority.value if self.enable_priority else 0
            queue_item = (priority_value, time.time(), request)
            await self._queue.put(queue_item)
            
            loop = asyncio.get_event_loop()
            self._futures[request.request_id] = loop.create_future()
        
        logger.info(f"推理请求已提交: {request.request_id}, 优先级: {request.priority.name}")
        
        return request.request_id
    
    async def get_result(
        self,
        request_id: str,
        timeout: Optional[float] = None
    ) -> Optional[InferenceResult]:
        """
        获取推理结果
        
        Args:
            request_id: 请求 ID
            timeout: 超时时间（秒），None 使用默认超时
            
        Returns:
            Optional[InferenceResult]: 推理结果，超时返回 None
        """
        if request_id not in self._futures:
            return None
        
        future = self._futures[request_id]
        actual_timeout = timeout or self.timeout
        
        try:
            await asyncio.wait_for(future, timeout=actual_timeout)
            return self._results.get(request_id)
        except asyncio.TimeoutError:
            logger.warning(f"请求超时: {request_id}")
            async with self._lock:
                if request_id in self._pending_requests:
                    self._pending_requests[request_id].status = RequestStatus.TIMEOUT
                    self._stats["timeout_requests"] += 1
            return InferenceResult(
                request_id=request_id,
                success=False,
                error="请求超时"
            )
    
    async def _process_queue(
        self,
        inference_fn: Callable[[InferenceRequest], Awaitable[Dict[str, Any]]]
    ) -> None:
        """
        处理队列中的请求
        
        Args:
            inference_fn: 推理函数
        """
        while self._running:
            try:
                try:
                    priority, timestamp, request = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=self.process_interval_ms / 1000.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                asyncio.create_task(
                    self._process_request(request, inference_fn)
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"队列处理错误: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_request(
        self,
        request: InferenceRequest,
        inference_fn: Callable[[InferenceRequest], Awaitable[Dict[str, Any]]]
    ) -> None:
        """
        处理单个请求
        
        Args:
            request: 推理请求
            inference_fn: 推理函数
        """
        async with self._semaphore:
            start_time = time.time()
            queue_time_ms = (start_time - request.created_at) * 1000
            
            try:
                request.status = RequestStatus.PROCESSING
                
                cache_key = request.get_cache_key()
                cached_result = None
                
                if self._cache and self.enable_cache:
                    cached_result = self._cache.get(cache_key)
                
                if cached_result is not None:
                    result = cached_result
                    cache_hit = True
                    self._stats["cache_hits"] += 1
                    logger.info(f"缓存命中: {request.request_id}")
                else:
                    result = await inference_fn(request)
                    cache_hit = False
                    
                    if self._cache and self.enable_cache:
                        self._cache.set(cache_key, result)
                
                processing_time_ms = (time.time() - start_time) * 1000
                
                inference_result = InferenceResult(
                    request_id=request.request_id,
                    success=True,
                    result=result,
                    processing_time_ms=processing_time_ms,
                    queue_time_ms=queue_time_ms,
                    cache_hit=cache_hit
                )
                
                request.status = RequestStatus.COMPLETED
                request.result = result
                
                async with self._lock:
                    self._results[request.request_id] = inference_result
                    self._stats["completed_requests"] += 1
                    self._update_avg_times(processing_time_ms, queue_time_ms)
                    
                    if request.request_id in self._pending_requests:
                        del self._pending_requests[request.request_id]
                    
                    if request.request_id in self._futures:
                        future = self._futures[request.request_id]
                        if not future.done():
                            future.set_result(inference_result)
                
                logger.info(
                    f"推理完成: {request.request_id}, "
                    f"处理时间: {processing_time_ms:.2f}ms, "
                    f"排队时间: {queue_time_ms:.2f}ms"
                )
                
                if request.callback:
                    try:
                        if asyncio.iscoroutinefunction(request.callback):
                            await request.callback(inference_result)
                        else:
                            request.callback(inference_result)
                    except Exception as e:
                        logger.warning(f"回调执行失败: {e}")
                
            except Exception as e:
                logger.error(f"推理失败: {request.request_id}, 错误: {e}")
                
                inference_result = InferenceResult(
                    request_id=request.request_id,
                    success=False,
                    error=str(e),
                    queue_time_ms=queue_time_ms
                )
                
                request.status = RequestStatus.FAILED
                request.error = str(e)
                
                async with self._lock:
                    self._results[request.request_id] = inference_result
                    self._stats["failed_requests"] += 1
                    
                    if request.request_id in self._pending_requests:
                        del self._pending_requests[request.request_id]
                    
                    if request.request_id in self._futures:
                        future = self._futures[request.request_id]
                        if not future.done():
                            future.set_result(inference_result)
    
    def _update_avg_times(
        self,
        processing_time_ms: float,
        queue_time_ms: float
    ) -> None:
        """
        更新平均时间统计
        
        Args:
            processing_time_ms: 处理时间（毫秒）
            queue_time_ms: 排队时间（毫秒）
        """
        self._processing_times.append(processing_time_ms)
        self._queue_times.append(queue_time_ms)
        
        window_size = 100
        if len(self._processing_times) > window_size:
            self._processing_times = self._processing_times[-window_size:]
            self._queue_times = self._queue_times[-window_size:]
        
        if self._processing_times:
            self._stats["avg_processing_time_ms"] = sum(self._processing_times) / len(self._processing_times)
        
        if self._queue_times:
            self._stats["avg_queue_time_ms"] = sum(self._queue_times) / len(self._queue_times)
    
    def start(
        self,
        inference_fn: Optional[Callable[[InferenceRequest], Awaitable[Dict[str, Any]]]] = None
    ) -> None:
        """
        启动队列处理
        
        Args:
            inference_fn: 推理函数（可选，后续可通过 run 方法传入）
        """
        if self._running:
            logger.warning("推理队列已在运行中")
            return
        
        self._running = True
        
        if inference_fn:
            loop = asyncio.get_event_loop()
            self._worker_task = loop.create_task(self._process_queue(inference_fn))
        
        self._init_cuda_memory()
        
        logger.info(
            f"推理队列已启动: "
            f"最大并发={self.max_concurrent}, "
            f"队列容量={self.max_queue_size}, "
            f"超时={self.timeout}s"
        )
    
    def stop(self) -> None:
        """停止队列处理"""
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
        
        for request_id, future in self._futures.items():
            if not future.done():
                future.cancel()
        
        self._futures.clear()
        self._pending_requests.clear()
        
        self._cleanup_cuda_memory()
        
        logger.info("推理队列已停止")
    
    def _init_cuda_memory(self) -> None:
        """
        初始化 CUDA 内存分配策略
        
        配置 PyTorch CUDA 内存分配器以优化显存使用
        """
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return
        
        try:
            torch.cuda.set_per_process_memory_fraction(0.8, 0)
            
            torch.cuda.empty_cache()
            
            if TORCH_AVAILABLE:
                gc.collect()
            
            logger.info("CUDA 内存分配策略已初始化")
            
        except Exception as e:
            logger.warning(f"CUDA 内存初始化失败: {e}")
    
    def _cleanup_cuda_memory(self) -> None:
        """清理 CUDA 内存"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return
        
        try:
            torch.cuda.empty_cache()
            gc.collect()
            logger.info("CUDA 内存已清理")
        except Exception as e:
            logger.warning(f"CUDA 内存清理失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取队列统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            **self._stats,
            "queue_size": len(self._pending_requests),
            "max_concurrent": self.max_concurrent,
            "running": self._running
        }
        
        if self._cache:
            stats["cache"] = self._cache.get_stats()
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            stats["gpu_memory"] = {
                "allocated_mb": torch.cuda.memory_allocated() / 1024**2,
                "reserved_mb": torch.cuda.memory_reserved() / 1024**2,
                "available_mb": (torch.cuda.get_device_properties(0).total_memory - 
                                torch.cuda.memory_allocated()) / 1024**2
            }
        
        return stats
    
    def clear_cache(self) -> None:
        """清空结果缓存"""
        if self._cache:
            self._cache.clear()
            logger.info("结果缓存已清空")
    
    async def cancel(self, request_id: str) -> bool:
        """
        取消请求
        
        Args:
            request_id: 请求 ID
            
        Returns:
            bool: 是否成功取消
        """
        async with self._lock:
            if request_id in self._pending_requests:
                self._pending_requests[request_id].status = RequestStatus.CANCELLED
                del self._pending_requests[request_id]
                
                if request_id in self._futures:
                    future = self._futures[request_id]
                    if not future.done():
                        future.cancel()
                    del self._futures[request_id]
                
                logger.info(f"请求已取消: {request_id}")
                return True
            
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态
        
        Returns:
            Dict[str, Any]: 队列状态信息
        """
        pending_by_priority = {}
        for req in self._pending_requests.values():
            priority_name = req.priority.name
            pending_by_priority[priority_name] = pending_by_priority.get(priority_name, 0) + 1
        
        return {
            "running": self._running,
            "total_pending": len(self._pending_requests),
            "pending_by_priority": pending_by_priority,
            "max_queue_size": self.max_queue_size,
            "max_concurrent": self.max_concurrent
        }


_inference_queue: Optional[AsyncInferenceQueue] = None


def get_inference_queue() -> AsyncInferenceQueue:
    """
    获取推理队列单例
    
    Returns:
        AsyncInferenceQueue: 推理队列实例
    """
    global _inference_queue
    
    if _inference_queue is None:
        try:
            from app.core.ai_config import ai_config
            _inference_queue = AsyncInferenceQueue(
                max_concurrent=ai_config.INFERENCE_QUEUE_MAX_CONCURRENT,
                max_queue_size=ai_config.INFERENCE_QUEUE_MAX_SIZE,
                timeout=ai_config.INFERENCE_QUEUE_TIMEOUT,
                enable_cache=ai_config.INFERENCE_QUEUE_ENABLE_CACHE,
                cache_ttl=ai_config.INFERENCE_QUEUE_CACHE_TTL,
                process_interval_ms=ai_config.INFERENCE_QUEUE_PROCESS_INTERVAL_MS,
                enable_priority=ai_config.INFERENCE_QUEUE_ENABLE_PRIORITY
            )
        except Exception as e:
            logger.error(f"初始化推理队列失败: {e}")
            _inference_queue = AsyncInferenceQueue()
    
    return _inference_queue


def initialize_inference_queue(
    max_concurrent: int = 2,
    max_queue_size: int = 100,
    timeout: int = 120,
    enable_cache: bool = True,
    cache_ttl: int = 1800
) -> AsyncInferenceQueue:
    """
    初始化推理队列
    
    Args:
        max_concurrent: 最大并发推理数
        max_queue_size: 队列最大长度
        timeout: 请求超时时间（秒）
        enable_cache: 是否启用结果缓存
        cache_ttl: 缓存过期时间（秒）
        
    Returns:
        AsyncInferenceQueue: 推理队列实例
    """
    global _inference_queue
    
    _inference_queue = AsyncInferenceQueue(
        max_concurrent=max_concurrent,
        max_queue_size=max_queue_size,
        timeout=timeout,
        enable_cache=enable_cache,
        cache_ttl=cache_ttl
    )
    
    logger.info(
        f"推理队列已初始化: "
        f"max_concurrent={max_concurrent}, "
        f"max_queue_size={max_queue_size}"
    )
    
    return _inference_queue
