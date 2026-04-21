"""
SSE 流式响应管理器
提供 Server-Sent Events 的完整生命周期管理，包括：
- 心跳保活机制（15s 间隔）
- 断线检测与优雅关闭
- 背压控制（asyncio.Queue 缓冲区，队列大小 100）
- 超时控制（默认 120s）
- ProgressEvent/LogEvent 数据类标准化
- SSE event 格式化工具函数
"""
import logging
import time
import json
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, AsyncGenerator, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ProgressEvent:
    """
    SSE 进度事件数据结构

    属性:
        event: 事件类型 (start, progress, heartbeat, complete, error)
        stage: 当前阶段名称
        progress: 进度百分比 (0-100)
        message: 进度描述消息
        data: 附加数据（可选）
    """
    event: str
    stage: str
    progress: int
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_sse(self) -> str:
        """
        将进度事件转换为 SSE 格式字符串

        SSE 标准格式：
        - event: 事件类型（如 progress, complete, error）
        - data: JSON 格式的负载数据

        返回:
            str: SSE 格式的事件字符串，格式为 "event: {type}\\ndata: {json}\\n\\n"
        """
        event_data = {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "timestamp": time.time()
        }
        if self.data:
            event_data.update(self.data)

        return f"event: {self.event}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"


class HeartbeatEvent:
    """
    SSE 心跳事件类
    用于保持连接活跃，防止超时断开
    """

    @staticmethod
    def to_sse() -> str:
        """
        生成心跳事件的 SSE 字符串

        返回:
            str: SSE 格式的心跳字符串
        """
        return f"event: heartbeat\ndata: {json.dumps({'timestamp': time.time()}, ensure_ascii=False)}\n\n"


@dataclass
class LogEvent:
    """
    SSE 日志事件数据类
    用于实时推送推理过程中的日志信息

    属性:
        level: 日志级别 (info, warning, error, debug)
        message: 日志消息内容
        stage: 当前阶段名称（可选）
        timestamp: 时间戳（自动生成）
    """
    level: str
    message: str
    stage: Optional[str] = None
    timestamp: float = field(default=None)

    def __post_init__(self) -> None:
        """初始化后处理：如果未提供时间戳则自动生成"""
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_sse(self) -> str:
        """
        生成日志事件的 SSE 字符串

        返回:
            str: SSE 格式的日志字符串
        """
        data = {
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp
        }
        if self.stage:
            data["stage"] = self.stage
        return f"event: log\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class StepIndicator:
    """
    推理步骤指示器类
    定义诊断推理的各个阶段及其图标
    """
    STEPS = [
        {"id": "init", "name": "初始化", "icon": "Loading"},
        {"id": "visual", "name": "视觉分析", "icon": "View"},
        {"id": "knowledge", "name": "知识检索", "icon": "Search"},
        {"id": "textual", "name": "语义分析", "icon": "Document"},
        {"id": "fusion", "name": "特征融合", "icon": "Connection"},
        {"id": "complete", "name": "完成", "icon": "CircleCheck"}
    ]

    @staticmethod
    def to_sse() -> str:
        """
        生成步骤定义的 SSE 事件字符串

        返回:
            str: SSE 格式的步骤定义字符串
        """
        return f"event: steps\ndata: {json.dumps({'steps': StepIndicator.STEPS}, ensure_ascii=False)}\n\n"


class SSEStreamManager:
    """
    SSE 流管理器类
    封装完整的 SSE 流生命周期管理功能

    功能特性:
    - 心跳保活机制（可配置间隔时间）
    - 断线检测与优雅关闭
    - 背压控制（基于 asyncio.Queue）
    - 超时控制（默认 120 秒）
    - 错误处理与日志记录
    """

    DEFAULT_HEARTBEAT_INTERVAL = 15.0
    DEFAULT_TIMEOUT_SECONDS = 120
    QUEUE_MAX_SIZE = 100

    def __init__(
        self,
        heartbeat_interval: float = None,
        timeout_seconds: int = None,
        queue_size: int = None
    ) -> None:
        """
        初始化 SSE 流管理器

        参数:
            heartbeat_interval: 心跳发送间隔（秒），默认从配置读取 (SSE_HEARTBEAT_INTERVAL)
            timeout_seconds: 超时时间（秒），默认从配置读取 (SSE_TIMEOUT_SECONDS)
            queue_size: 背压控制队列大小，默认从配置读取 (SSE_BACKPRESSURE_QUEUE_SIZE)
        """
        self.heartbeat_interval = heartbeat_interval if heartbeat_interval is not None else settings.SSE_HEARTBEAT_INTERVAL
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.SSE_TIMEOUT_SECONDS
        self.queue_size = queue_size if queue_size is not None else settings.SSE_BACKPRESSURE_QUEUE_SIZE
        self._start_time: float = 0
        self._last_heartbeat_time: float = 0
        self._is_cancelled: bool = False

    async def create_heartbeat_generator(
        self,
        source_generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        创建带心跳保活的异步 SSE 流生成器

        在源数据生成器的基础上添加心跳机制和超时控制。
        当源数据长时间未产生输出时，自动发送心跳保持连接活跃。

        参数:
            source_generator: 原始异步数据生成器

        生成:
            str: SSE 格式的事件字符串或心跳事件
        """
        self._start_time = time.time()
        self._last_heartbeat_time = self._start_time
        self._is_cancelled = False

        try:
            async for data in source_generator:
                current_time = time.time()

                if current_time - self._start_time > self.timeout_seconds:
                    logger.warning(f"SSE 流超时（{self.timeout_seconds}秒）")
                    yield self._create_timeout_event()
                    return

                self._last_heartbeat_time = current_time

                if isinstance(data, str):
                    yield data
                else:
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                if current_time - self._last_heartbeat_time > self.heartbeat_interval:
                    yield HeartbeatEvent.to_sse()
                    self._last_heartbeat_time = current_time

        except asyncio.CancelledError:
            self._is_cancelled = True
            logger.info("SSE 流被客户端取消，优雅关闭")
            yield self._create_cancel_event()
        except Exception as e:
            logger.error(f"SSE 流异常: {e}")
            yield self._create_error_event(str(e))

    async def create_backpressure_controlled_stream(
        self,
        source_generator: AsyncGenerator[Any, None],
        queue: Optional[asyncio.Queue] = None
    ) -> AsyncGenerator[str, None]:
        """
        创建带背压控制的 SSE 流

        使用 asyncio.Queue 作为缓冲区实现背压控制，
        防止生产者速度过快导致内存溢出。

        参数:
            source_generator: 源数据生成器
            queue: 外部提供的队列（可选），如不提供则内部创建

        生成:
            str: SSE 格式的事件字符串
        """
        if queue is None:
            queue = asyncio.Queue(maxsize=self.queue_size)

        self._start_time = time.time()
        producer_task = asyncio.create_task(
            self._produce_to_queue(source_generator, queue)
        )

        try:
            while True:
                try:
                    item = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.heartbeat_interval
                    )

                    current_time = time.time()
                    if current_time - self._start_time > self.timeout_seconds:
                        yield self._create_timeout_event()
                        break

                    if isinstance(item, (ProgressEvent, LogEvent)):
                        yield item.to_sse()
                    elif isinstance(item, str):
                        yield item
                    else:
                        yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

                except asyncio.TimeoutError:
                    yield HeartbeatEvent.to_sse()

                except asyncio.CancelledError:
                    self._is_cancelled = True
                    yield self._create_cancel_event()
                    break

        finally:
            producer_task.cancel()
            try:
                await producer_task
            except asyncio.CancelledError:
                pass

    async def _produce_to_queue(
        self,
        generator: AsyncGenerator[Any, None],
        queue: asyncio.Queue
    ) -> None:
        """
        生产者协程：将源数据放入队列，实现背压控制

        当队列满时（达到 queue_size 限制），await queue.put() 会自动阻塞，
        等待消费者取出数据后继续生产，从而实现自然的背压流量控制。

        参数:
            generator: 源数据生成器
            queue: 目标队列（maxsize 决定背压阈值）
        """
        total_produced = 0
        try:
            async for item in generator:
                await queue.put(item)
                total_produced += 1
                if total_produced % 50 == 0:
                    logger.debug(f"背压生产者已产出 {total_produced} 条事件，队列深度: {queue.qsize()}/{queue.maxsize}")
        except asyncio.CancelledError:
            logger.info(f"背压生产者被取消，已产出 {total_produced} 条事件")
        except Exception as e:
            logger.error(f"背压生产者异常（已产出 {total_produced} 条）: {e}")
            try:
                await queue.put(ProgressEvent(
                    event="error",
                    stage="producer",
                    progress=0,
                    message=f"生产者错误: {str(e)}"
                ))
            except Exception:
                pass

    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取当前队列状态信息（用于监控和调试）

        返回:
            Dict[str, Any]: 包含队列大小配置、超时设置等状态信息
        """
        return {
            "queue_max_size": self.queue_size,
            "timeout_seconds": self.timeout_seconds,
            "heartbeat_interval": self.heartbeat_interval,
            "is_cancelled": self._is_cancelled,
            "elapsed_seconds": time.time() - self._start_time if self._start_time > 0 else 0
        }

    def _create_timeout_event(self) -> str:
        """
        创建超时事件的 SSE 字符串

        按照生产环境标准格式发送超时错误事件，
        包含 error 类型标识和诊断超时消息。

        返回:
            str: 超时事件的 SSE 格式字符串，格式为
                 event: error\ndata: {"error": "timeout", "message": "诊断超时", ...}\n\n
                 event: close\ndata: {"reason": "timeout"}\n\n
        """
        return (
            f"event: error\ndata: "
            f"{json.dumps({'error': 'timeout', 'message': '诊断超时', 'timeout': self.timeout_seconds, 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
            f"event: close\ndata: {json.dumps({'reason': 'timeout'}, ensure_ascii=False)}\n\n"
        )

    def _create_cancel_event(self) -> str:
        """
        创建取消事件的 SSE 字符串

        返回:
            str: 取消事件的 SSE 格式字符串
        """
        return (
            f"event: error\ndata: "
            f"{json.dumps({'error': '连接已关闭', 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
        )

    @staticmethod
    def _create_error_event(error_msg: str) -> str:
        """
        创建错误事件的 SSE 字符串

        参数:
            error_msg: 错误消息

        返回:
            str: 错误事件的 SSE 格式字符串
        """
        return (
            f"event: error\ndata: "
            f"{json.dumps({'error': error_msg, 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
        )


def create_progress_callback(queue: asyncio.Queue) -> Callable:
    """
    创建进度回调函数

    用于将同步的进度更新转换为异步队列中的事件，
    适用于需要从同步代码向 SSE 流发送进度的场景。

    参数:
        queue: 异步队列，用于传递进度事件

    返回:
        Callable: 进度回调函数，签名为 (stage, progress, message, data=None)
    """
    def callback(stage: str, progress: int, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        进度回调函数

        将进度信息封装为 ProgressEvent 并放入异步队列。

        参数:
            stage: 当前阶段名称
            progress: 进度百分比 (0-100)
            message: 进度描述消息
            data: 附加数据（可选）
        """
        event = ProgressEvent(
            event="progress",
            stage=stage,
            progress=progress,
            message=message,
            data=data
        )
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(queue.put(event))
            else:
                loop.run_until_complete(queue.put(event))
        except Exception as e:
            logger.warning(f"进度回调失败: {e}")

    return callback


def format_sse_event(event_type: str, data: Any) -> str:
    """
    格式化通用的 SSE 事件字符串

    工具函数，用于快速构建符合 SSE 标准的事件格式。

    参数:
        event_type: 事件类型（如 start, progress, complete, error）
        data: 事件负载数据（将自动 JSON 序列化）

    返回:
        str: SSE 格式的事件字符串
    """
    if isinstance(data, str):
        payload = data
    else:
        payload = json.dumps(data, ensure_ascii=False)

    return f"event: {event_type}\ndata: {payload}\n\n"
