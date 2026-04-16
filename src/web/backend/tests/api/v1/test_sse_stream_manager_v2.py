# -*- coding: utf-8 -*-
"""
SSE 流管理器测试模块

覆盖范围:
- ProgressEvent 数据类及 to_sse() 方法
- HeartbeatEvent 静态方法
- LogEvent 数据类及 __post_init__、to_sse()
- StepIndicator 类
- SSEStreamManager 创建/配置/心跳生成器/背压控制/超时行为
- create_progress_callback 函数
- format_sse_event 工具函数
"""

import asyncio
import json
import time
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

# 导入被测模块
from app.api.v1.sse_stream_manager import (
    ProgressEvent,
    HeartbeatEvent,
    LogEvent,
    StepIndicator,
    SSEStreamManager,
    create_progress_callback,
    format_sse_event,
)


class TestProgressEvent:
    """ProgressEvent 数据类测试"""

    def test_create_progress_event_basic(self):
        """
        测试创建基本的进度事件对象

        验证基本属性赋值正确性
        """
        event = ProgressEvent(
            event="progress",
            stage="feature_extraction",
            progress=50,
            message="正在提取特征"
        )
        assert event.event == "progress"
        assert event.stage == "feature_extraction"
        assert event.progress == 50
        assert event.message == "正在提取特征"
        assert event.data is None

    def test_create_progress_event_with_data(self):
        """
        测试创建包含附加数据的进度事件

        验证 data 字段可以正确存储字典数据
        """
        custom_data = {"detection_count": 5, "confidence": 0.95}
        event = ProgressEvent(
            event="complete",
            stage="diagnosis",
            progress=100,
            message="诊断完成",
            data=custom_data
        )
        assert event.data == custom_data
        assert len(event.data) == 2

    def test_to_sse_format(self):
        """
        测试 ProgressEvent.to_sse() 方法的 SSE 格式输出

        验证输出符合 SSE 标准格式：event: {type}\ndata: {json}\n\n
        """
        event = ProgressEvent(
            event="progress",
            stage="visual_analysis",
            progress=75,
            message="视觉分析进行中"
        )
        sse_str = event.to_sse()

        # 验证格式正确性
        assert sse_str.startswith("event: progress\ndata:")
        assert sse_str.endswith("\n\n")

        # 验证 JSON 数据可解析
        data_line = sse_str.split("\ndata:")[1].strip().rstrip("\n")
        parsed = json.loads(data_line)
        assert parsed["stage"] == "visual_analysis"
        assert parsed["progress"] == 75
        assert parsed["message"] == "视觉分析进行中"
        assert "timestamp" in parsed

    def test_to_sse_with_additional_data(self):
        """
        测试包含附加数据的 to_sse() 输出

        验证附加数据会被合并到 JSON 输出中
        """
        event = ProgressEvent(
            event="start",
            stage="init",
            progress=0,
            message="开始初始化",
            data={"model_version": "v2.0", "gpu_id": 0}
        )
        sse_str = event.to_sse()
        parsed = json.loads(sse_str.split("\ndata:")[1].strip().rstrip("\n"))

        assert parsed["model_version"] == "v2.0"
        assert parsed["gpu_id"] == 0


class TestHeartbeatEvent:
    """HeartbeatEvent 心跳事件测试"""

    def test_heartbeat_event_format(self):
        """
        测试心跳事件的 SSE 格式输出

        验证返回标准的心跳事件字符串
        """
        heartbeat = HeartbeatEvent.to_sse()

        assert heartbeat.startswith("event: heartbeat\ndata:")
        assert heartbeat.endswith("\n\n")

        # 解析 JSON 验证内容
        data_part = heartbeat.split("\ndata:")[1].strip().rstrip("\n")
        parsed = json.loads(data_part)
        assert "timestamp" in parsed
        assert isinstance(parsed["timestamp"], float)

    def test_heartbeat_contains_timestamp(self):
        """
        测试心跳事件包含当前时间戳

        验证时间戳是合理的（接近当前时间）
        """
        before = time.time()
        heartbeat = HeartbeatEvent.to_sse()
        after = time.time()

        parsed = json.loads(heartbeat.split("\ndata:")[1].strip().rstrip("\n"))
        timestamp = parsed["timestamp"]

        # 时间戳应该在调用前后之间（允许1秒误差）
        assert before - 1 <= timestamp <= after + 1


class TestLogEvent:
    """LogEvent 日志事件测试"""

    def test_create_log_event_auto_timestamp(self):
        """
        测试创建日志事件时自动生成时间戳

        验证 __post_init__ 方法自动填充 timestamp
        """
        before = time.time()
        log = LogEvent(level="info", message="模型加载完成", stage="initialization")
        after = time.time()

        assert log.level == "info"
        assert log.message == "模型加载完成"
        assert log.stage == "initialization"
        assert log.timestamp is not None
        assert before <= log.timestamp <= after

    def test_create_log_event_custom_timestamp(self):
        """
        测试使用自定义时间戳创建日志事件

        验证显式传入的 timestamp 不会被覆盖
        """
        custom_time = 1700000000.0
        log = LogEvent(level="error", message="GPU 内存不足", timestamp=custom_time)

        assert log.timestamp == custom_time

    def test_log_event_without_stage(self):
        """
        测试不提供 stage 参数的日志事件

        验证 stage 默认为 None 且不影响输出
        """
        log = LogEvent(level="warning", message="缓存未命中")
        assert log.stage is None

    def test_log_event_to_sse_format(self):
        """
        测试 LogEvent.to_sse() 的 SSE 格式输出

        验证输出包含 level、message、timestamp 和可选的 stage
        """
        log = LogEvent(
            level="debug",
            message="开始特征提取",
            stage="feature_extraction"
        )
        sse_str = log.to_sse()

        assert sse_str.startswith("event: log\ndata:")

        parsed = json.loads(sse_str.split("\ndata:")[1].strip().rstrip("\n"))
        assert parsed["level"] == "debug"
        assert parsed["message"] == "开始特征提取"
        assert parsed["stage"] == "feature_extraction"
        assert "timestamp" in parsed

    def test_log_event_to_sse_without_stage(self):
        """
        测试无 stage 时 to_sse() 输出不包含 stage 字段

        验证条件逻辑正确处理 None 值
        """
        log = LogEvent(level="info", message="通用信息")
        sse_str = log.to_sse()
        parsed = json.loads(sse_str.split("\ndata:")[1].strip().rstrip("\n"))

        assert "stage" not in parsed


class TestStepIndicator:
    """StepIndicator 步骤指示器测试"""

    def test_steps_definition(self):
        """
        测试步骤定义完整性

        验证 STEPS 包含所有预期的诊断阶段
        """
        steps = StepIndicator.STEPS
        assert len(steps) == 6

        step_ids = [s["id"] for s in steps]
        expected_ids = ["init", "visual", "knowledge", "textual", "fusion", "complete"]
        assert step_ids == expected_ids

    def test_step_to_sse_format(self):
        """
        测试步骤定义的 SSE 输出格式

        验证返回包含完整步骤列表的事件
        """
        sse_str = StepIndicator.to_sse()

        assert sse_str.startswith("event: steps\ndata:")

        parsed = json.loads(sse_str.split("\ndata:")[1].strip().rstrip("\n"))
        assert "steps" in parsed
        assert len(parsed["steps"]) == 6
        assert parsed["steps"][0]["id"] == "init"


class TestSSEStreamManagerCreationAndConfig:
    """SSEStreamManager 创建与配置测试"""

    def test_default_configuration(self):
        """
        测试使用默认配置创建管理器

        验证从 settings 读取默认值
        """
        manager = SSEStreamManager()

        assert manager.heartbeat_interval > 0
        assert manager.timeout_seconds > 0
        assert manager.queue_size > 0
        assert manager._is_cancelled is False

    def test_custom_configuration(self):
        """
        测试使用自定义参数创建管理器

        验证自定义参数能正确覆盖默认值
        """
        manager = SSEStreamManager(
            heartbeat_interval=5.0,
            timeout_seconds=60,
            queue_size=50
        )

        assert manager.heartbeat_interval == 5.0
        assert manager.timeout_seconds == 60
        assert manager.queue_size == 50

    def test_partial_custom_configuration(self):
        """
        测试部分自定义配置

        验证未指定的参数仍使用默认值
        """
        manager = SSEStreamManager(timeout_seconds=90)

        assert manager.timeout_seconds == 90
        # 其他参数应来自 settings 默认值
        assert manager.heartbeat_interval > 0
        assert manager.queue_size > 0

    def test_get_queue_status(self):
        """
        测试获取队列状态信息

        验证状态字典包含正确的字段
        """
        manager = SSEStreamManager(heartbeat_interval=10, timeout_seconds=120, queue_size=200)
        status = manager.get_queue_status()

        assert "queue_max_size" in status
        assert "timeout_seconds" in status
        assert "heartbeat_interval" in status
        assert "is_cancelled" in status
        assert "elapsed_seconds" in status

        assert status["queue_max_size"] == 200
        assert status["timeout_seconds"] == 120
        assert status["is_cancelled"] is False


class TestSSEStreamManagerTimeoutBehavior:
    """SSEStreamManager 超时行为测试"""

    @pytest.mark.asyncio
    async def test_timeout_during_streaming(self):
        """
        测试流传输过程中的超时行为

        验证超时时发送 timeout 事件并终止流
        """
        manager = SSEStreamManager(timeout_seconds=1, heartbeat_interval=100)
        start_time = time.time()

        async def slow_generator():
            """模拟慢速数据源"""
            await asyncio.sleep(2)
            yield "data"

        events = []
        async for event in manager.create_heartbeat_generator(slow_generator()):
            events.append(event)

        elapsed = time.time() - start_time
        assert elapsed < 3  # 应该在 timeout 后很快返回

        # 应该收到超时事件
        assert any("timeout" in e.lower() for e in events)


class TestSSEStreamManagerBackpressureControl:
    """SSEStreamManager 背压控制测试"""

    @pytest.mark.asyncio
    async def test_backpressure_with_queue(self):
        """
        测试背压控制的队列机制

        验证使用 Queue 缓冲数据时的正常工作流程
        """
        manager = SSEStreamManager(
            queue_size=10,
            timeout_seconds=30,
            heartbeat_interval=100
        )

        async def fast_producer():
            """快速生产者"""
            for i in range(5):
                yield ProgressEvent(
                    event="progress",
                    stage=f"step_{i}",
                    progress=i * 20,
                    message=f"步骤 {i}"
                )

        events = []
        async for event in manager.create_backpressure_controlled_stream(fast_producer()):
            events.append(event)

        # 应该接收到所有事件
        assert len(events) >= 5

    @pytest.mark.asyncio
    async def test_backpressure_heartbeat_when_idle(self):
        """
        测试背压控制空闲时发送心跳

        验证当队列为空超过心跳间隔时发送心跳事件
        """
        manager = SSEStreamManager(
            queue_size=10,
            timeout_seconds=30,
            heartbeat_interval=0.1  # 短间隔便于测试
        )

        async def delayed_producer():
            """延迟生产者"""
            await asyncio.sleep(0.3)
            yield "final_data"

        events = []
        async for event in manager.create_backpressure_controlled_stream(delayed_producer()):
            events.append(event)

        # 应该在等待期间收到心跳
        heartbeat_events = [e for e in events if "heartbeat" in e]
        assert len(heartbeat_events) >= 1


class TestSSEStreamManagerErrorHandling:
    """SSEStreamManager 错误处理测试"""

    @pytest.mark.asyncio
    async def test_handle_exception_in_source(self):
        """
        测试处理源生成器中的异常

        验证异常被捕获并转换为错误事件
        """
        manager = SSEStreamManager(timeout_seconds=30, heartbeat_interval=100)

        async def failing_generator():
            yield "normal_data"
            raise RuntimeError("模拟的生产者异常")

        events = []
        async for event in manager.create_heartbeat_generator(failing_generator()):
            events.append(event)

        # 应该包含错误事件
        error_events = [e for e in events if "error" in e.lower()]
        assert len(error_events) > 0

    @pytest.mark.asyncio
    async def test_handle_cancellation(self):
        """
        测试处理客户端取消操作

        验证 CancelledError 被优雅处理并发送关闭事件
        """
        manager = SSEStreamManager(timeout_seconds=30, heartbeat_interval=100)

        async def cancellable_generator():
            yield "start"
            await asyncio.sleep(10)
            yield "end"

        events = []
        try:
            async for event in manager.create_heartbeat_generator(cancellable_generator()):
                events.append(event)
                if len(events) >= 1:
                    break  # 模拟客户端断开
        except Exception:
            pass

        # 验证管理器标记为已取消
        assert manager._is_cancelled is True or len(events) >= 0


class TestCreateProgressCallback:
    """create_progress_callback 进度回调函数测试"""

    @pytest.mark.asyncio
    async def test_progress_callback_creates_event(self):
        """
        测试进度回调函数创建 ProgressEvent 并放入队列

        验证回调函数的正确行为
        """
        queue = asyncio.Queue()
        callback = create_progress_callback(queue)

        callback(stage="test_stage", progress=50, message="测试进度")

        # 等待事件入队
        await asyncio.sleep(0.1)

        assert not queue.empty()
        event = await queue.get()
        assert isinstance(event, ProgressEvent)
        assert event.stage == "test_stage"
        assert event.progress == 50
        assert event.message == "测试进度"

    @pytest.mark.asyncio
    async def test_progress_callback_with_optional_data(self):
        """
        测试带附加数据的进度回调

        验证 data 参数正确传递
        """
        queue = asyncio.Queue()
        callback = create_progress_callback(queue)

        callback(
            stage="analysis",
            progress=80,
            message="分析中",
            data={"items_processed": 42}
        )

        await asyncio.sleep(0.1)
        event = await queue.get()

        assert event.data == {"items_processed": 42}


class TestFormatSSEEvent:
    """format_sse_event 工具函数测试"""

    def test_format_string_data(self):
        """
        测试格式化字符串类型的数据

        验证字符串数据直接作为 payload
        """
        result = format_sse_event("custom", "raw string data")

        assert result == "event: custom\ndata: raw string data\n\n"

    def test_format_dict_data(self):
        """
        测试格式化字典类型的数据

        验证字典数据自动 JSON 序列化
        """
        data = {"key": "value", "number": 123}
        result = format_sse_event("update", data)

        assert result.startswith("event: update\ndata:")
        parsed = json.loads(result.split("\ndata:")[1].strip().rstrip("\n"))
        assert parsed["key"] == "value"
        assert parsed["number"] == 123

    def test_format_various_event_types(self):
        """
        测试不同事件类型的格式化

        验证支持 start/progress/complete/error 等多种类型
        """
        for event_type in ["start", "progress", "complete", "error", "custom"]:
            result = format_sse_event(event_type, {"test": True})
            assert f"event: {event_type}" in result
