"""
诊断请求限流器
控制同时进行的 AI 诊断请求数量，防止 GPU 过载
"""
import asyncio
from collections import deque
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisRequest:
    """诊断请求信息"""

    request_id: str
    user_id: int
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 0  # 优先级，数字越小越优先


class DiagnosisRateLimiter:
    """
    诊断请求并发限制器
    
    使用信号量模式控制并发诊断请求数量，
    超过并发上限的请求进入等待队列，
    队列满后拒绝新请求。
    """

    def __init__(self, max_concurrent: int = None, max_queue_size: int = None) -> None:
        """
        初始化限流器

        Args:
            max_concurrent: 最大并发诊断数，默认从配置读取 (MAX_CONCURRENT_DIAGNOSIS)
            max_queue_size: 最大排队长度，默认从配置读取 (MAX_DIAGNOSIS_QUEUE_SIZE)
        """
        self._max_concurrent = max_concurrent if max_concurrent is not None else settings.MAX_CONCURRENT_DIAGNOSIS
        self._max_queue_size = max_queue_size if max_queue_size is not None else settings.MAX_DIAGNOSIS_QUEUE_SIZE
        self._active_count = 0
        self._queue: deque[DiagnosisRequest] = deque()
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._waiters: dict[str, asyncio.Future] = {}

    async def acquire(self, request: DiagnosisRequest) -> bool:
        """
        获取诊断执行许可
        
        如果当前并发数未满，立即返回 True。
        否则加入队列等待（有超时机制）。
        
        Args:
            request: 诊断请求信息
            
        Returns:
            bool: 是否获得许可（False 表示队列已满被拒绝）
        """
        async with self._lock:
            if self._active_count < self._max_concurrent:
                self._active_count += 1
                logger.info(
                    f"诊断请求获准执行: request_id={request.request_id}, "
                    f"user_id={request.user_id}, 当前活跃={self._active_count}/{self._max_concurrent}"
                )
                return True

            if len(self._queue) >= self._max_queue_size:
                logger.warning(
                    f"诊断请求被拒绝 - 队列已满: request_id={request.request_id}, "
                    f"user_id={request.user_id}, 队列长度={len(self._queue)}/{self._max_queue_size}, "
                    f"当前活跃={self._active_count}/{self._max_concurrent}"
                )
                return False

            self._queue.append(request)
            logger.info(
                f"诊断请求进入等待队列: request_id={request.request_id}, "
                f"user_id={request.user_id}, 队列位置={len(self._queue)}, "
                f"当前活跃={self._active_count}/{self._max_concurrent}"
            )

            loop = asyncio.get_event_loop()
            future: asyncio.Future[bool] = loop.create_future()
            self._waiters[request.request_id] = future

        try:
            result = await asyncio.wait_for(future, timeout=settings.DIAGNOSIS_QUEUE_TIMEOUT)
            return result
        except asyncio.TimeoutError:
            async with self._lock:
                if request.request_id in self._waiters:
                    del self._waiters[request.request_id]
                try:
                    self._queue.remove(request)
                except ValueError:
                    pass
            logger.warning(
                f"诊断请求等待超时 ({settings.DIAGNOSIS_QUEUE_TIMEOUT}s): request_id={request.request_id}, "
                f"user_id={request.user_id}"
            )
            return False
        except Exception as e:
            async with self._lock:
                if request.request_id in self._waiters:
                    del self._waiters[request.request_id]
            logger.error(
                f"诊断请求等待异常: request_id={request.request_id}, error={e}"
            )
            return False

    async def release(self) -> None:
        """
        释放一个诊断许可
        
        释放后会唤醒队列中的下一个等待者（如果有）。
        """
        async with self._lock:
            if self._active_count > 0:
                self._active_count -= 1

            if self._queue:
                next_request = self._queue.popleft()
                waiter_future = self._waiters.pop(next_request.request_id, None)

                if waiter_future and not waiter_future.done():
                    self._active_count += 1
                    waiter_future.set_result(True)
                    logger.info(
                        f"从队列唤醒诊断请求: request_id={next_request.request_id}, "
                        f"user_id={next_request.user_id}, 当前活跃={self._active_count}/{self._max_concurrent}, "
                        f"剩余队列={len(self._queue)}"
                    )
                else:
                    logger.debug(f"队列中下一个请求的 Future 已完成或不存在，跳过")
            else:
                logger.debug(
                    f"释放诊断许可，当前活跃={self._active_count}/{self._max_concurrent}，队列为空"
                )

    @property
    def active_count(self) -> int:
        """当前活跃的诊断数"""
        return self._active_count

    @property
    def queue_length(self) -> int:
        """当前排队长度"""
        return len(self._queue)

    @property
    def max_concurrent(self) -> int:
        """最大并发数配置"""
        return self._max_concurrent

    def get_status(self) -> dict:
        """
        获取限流器状态信息
        
        Returns:
            dict: 包含活跃数、队列长度等信息的字典
        """
        return {
            "active_count": self._active_count,
            "max_concurrent": self._max_concurrent,
            "queue_length": len(self._queue),
            "max_queue_size": self._max_queue_size,
            "available_slots": max(0, self._max_concurrent - self._active_count),
            "waiting_request_ids": [r.request_id for r in list(self._queue)[:5]]
        }


# 全局诊断限流器单例
_diagnosis_rate_limiter: Optional[DiagnosisRateLimiter] = None


def get_diagnosis_rate_limiter() -> DiagnosisRateLimiter:
    """
    获取全局诊断请求限流器单例

    Returns:
        DiagnosisRateLimiter: 限流器实例
    """
    global _diagnosis_rate_limiter
    if _diagnosis_rate_limiter is None:
        _diagnosis_rate_limiter = DiagnosisRateLimiter()
        logger.info(
            f"诊断请求限流器初始化完成: 最大并发={settings.MAX_CONCURRENT_DIAGNOSIS}, "
            f"最大队列={settings.MAX_DIAGNOSIS_QUEUE_SIZE}"
        )
    return _diagnosis_rate_limiter
