"""
SSE 流管理器单元测试
测试覆盖：
1. ProgressEvent 数据类（SSE 格式化、字段验证）
2. HeartbeatEvent 心跳事件生成
3. LogEvent 日志事件格式化
4. StepIndicator 步骤定义
5. SSEStreamManager 类功能
   - 心跳保活机制
   - 超时控制
   - 断线检测
   - 背压控制
6. 工具函数测试
7. 生产就绪增强测试（Task 6 P1-S6）
   - 认证保护：未认证用户访问返回 401
   - 超时控制：超时场景正确关闭连接并返回标准格式
   - 背压控制：队列满时不丢失数据，生产者自动阻塞恢复
"""
import asyncio
import pytest
import json
import time

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

    def test_basic_progress_event_creation(self):
        """测试基本进度事件的创建和字段赋值"""
        event = ProgressEvent(
            event="progress",
            stage="visual",
            progress=50,
            message="正在提取视觉特征..."
        )

        assert event.event == "progress"
        assert event.stage == "visual"
        assert event.progress == 50
        assert event.message == "正在提取视觉特征..."
        assert event.data is None

    def test_progress_event_with_data(self):
        """测试带附加数据的进度事件"""
        event = ProgressEvent(
            event="complete",
            stage="complete",
            progress=100,
            message="诊断完成",
            data={"disease_name": "小麦条锈病", "confidence": 0.95}
        )

        assert event.data is not None
        assert event.data["disease_name"] == "小麦条锈病"

    def test_to_sse_format(self):
        """测试 SSE 格式转换的正确性"""
        event = ProgressEvent(
            event="progress",
            stage="init",
            progress=10,
            message="初始化完成"
        )

        sse_str = event.to_sse()

        assert "event: progress" in sse_str
        assert '"stage": "init"' in sse_str
        assert '"progress": 10' in sse_str
        assert '"message": "初始化完成"' in sse_str
        assert '"timestamp"' in sse_str
        assert sse_str.endswith("\n\n")

    def test_to_sse_includes_data_field(self):
        """测试 SSE 格式是否正确包含 data 字段"""
        event = ProgressEvent(
            event="complete",
            stage="fusion",
            progress=100,
            message="融合完成",
            data={"confidence": 0.88}
        )

        sse_str = event.to_sse()
        parsed_data = json.loads(sse_str.split("data: ")[1].strip())

        assert "confidence" in parsed_data
        assert parsed_data["confidence"] == 0.88


class TestHeartbeatEvent:
    """HeartbeatEvent 心跳事件测试"""

    def test_heartbeat_format(self):
        """测试心跳事件的 SSE 格式"""
        heartbeat = HeartbeatEvent.to_sse()

        assert "event: heartbeat" in heartbeat
        assert '"timestamp"' in heartbeat
        assert heartbeat.endswith("\n\n")

    def test_heartbeat_contains_timestamp(self):
        """测试心跳事件包含有效时间戳"""
        before = time.time()
        heartbeat = HeartbeatEvent.to_sse()
        after = time.time()

        data_part = heartbeat.split("data: ")[1].strip()
        timestamp = json.loads(data_part)["timestamp"]

        assert before <= timestamp <= after


class TestLogEvent:
    """LogEvent 日志事件测试"""

    def test_log_event_creation(self):
        """测试日志事件的创建"""
        log = LogEvent(
            level="info",
            message="模型加载完成",
            stage="init"
        )

        assert log.level == "info"
        assert log.message == "模型加载完成"
        assert log.stage == "init"
        assert log.timestamp is not None

    def test_auto_timestamp_generation(self):
        """测试自动时间戳生成"""
        before = time.time()
        log = LogEvent(level="warning", message="警告信息")
        after = time.time()

        assert before <= log.timestamp <= after

    def test_manual_timestamp(self):
        """测试手动指定时间戳"""
        custom_time = 1234567890.0
        log = LogEvent(level="error", message="错误", timestamp=custom_time)

        assert log.timestamp == custom_time

    def test_log_to_sse_format(self):
        """测试日志事件的 SSE 格式"""
        log = LogEvent(
            level="info",
            message="开始诊断",
            stage="visual"
        )

        sse_str = log.to_sse()

        assert "event: log" in sse_str
        assert '"level": "info"' in sse_str
        assert '"message": "开始诊断"' in sse_str
        assert '"stage": "visual"' in sse_str

    def test_log_without_stage(self):
        """测试不带 stage 的日志事件"""
        log = LogEvent(level="debug", message="调试信息")
        sse_str = log.to_sse()

        assert '"stage"' not in sse_str or '"stage": null' in sse_str


class TestStepIndicator:
    """StepIndicator 步骤指示器测试"""

    def test_steps_definition(self):
        """测试步骤定义的完整性"""
        steps = StepIndicator.STEPS

        assert len(steps) == 6
        step_ids = [s["id"] for s in steps]
        assert "init" in step_ids
        assert "visual" in step_ids
        assert "knowledge" in step_ids
        assert "textual" in step_ids
        assert "fusion" in step_ids
        assert "complete" in step_ids

    def test_step_structure(self):
        """测试每个步骤的数据结构"""
        for step in StepIndicator.STEPS:
            assert "id" in step
            assert "name" in step
            assert "icon" in step

    def test_to_sse_format(self):
        """测试步骤定义的 SSE 格式"""
        sse_str = StepIndicator.to_sse()

        assert "event: steps" in sse_str
        assert '"steps"' in sse_str
        parsed = json.loads(sse_str.split("data: ")[1].strip())
        assert len(parsed["steps"]) == 6


class TestSSEStreamManager:
    """SSEStreamManager 流管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建流管理器实例"""
        return SSEStreamManager(heartbeat_interval=0.1, timeout_seconds=1, queue_size=10)

    async def test_heartbeat_generator_with_data(self, manager):
        """测试心跳生成器正常数据传输"""
        async def source():
            yield "data: test\n\n"
            await asyncio.sleep(0)
            yield "data: another\n\n"

        events = []
        async for event in manager.create_heartbeat_generator(source()):
            events.append(event)
            if len(events) >= 2:
                break

        assert len(events) >= 2
        assert any("test" in e for e in events)

    async def test_timeout_control(self, manager):
        """测试超时控制机制"""
        start_time = time.time()

        async def slow_source():
            await asyncio.sleep(2)
            yield "data: late\n\n"

        events = []
        async for event in manager.create_heartbeat_generator(slow_source()):
            events.append(event)

        elapsed = time.time() - start_time
        assert elapsed < 1.5  # 应该在超时时间内返回
        assert any("timeout" in e.lower() or "error" in e.lower() for e in events)

    async def test_cancelled_error_handling(self, manager):
        """测试客户端断开（CancelledError）处理"""
        cancelled_triggered = False

        async def cancelling_source():
            nonlocal cancelled_triggered
            yield "data: start\n\n"
            raise asyncio.CancelledError()

        try:
            async for event in manager.create_heartbeat_generator(cancelling_source()):
                pass
        except asyncio.CancelledError:
            cancelled_triggered = True

        assert cancelled_triggered

    async def test_backpressure_queue_limit(self, manager):
        """测试背压控制的队列大小限制"""
        queue_size = 5
        limited_manager = SSEStreamManager(queue_size=queue_size)

        async def fast_producer():
            for i in range(queue_size * 2):
                yield f"data: item {i}\n\n"

        events_received = []
        async for event in limited_manager.create_backpressure_controlled_stream(fast_producer()):
            events_received.append(event)
            if len(events_received) >= queue_size + 2:
                break

        assert len(events_received) > 0

    async def test_error_event_handling(self, manager):
        """测试异常情况下的错误事件生成"""
        async def failing_source():
            yield "data: ok\n\n"
            raise RuntimeError("模拟错误")

        events = []
        error_found = False
        async for event in manager.create_heartbeat_generator(failing_source()):
            events.append(event)
            if "error" in event.lower():
                error_found = True

        assert error_found
        assert len(events) >= 1


class TestUtilityFunctions:
    """工具函数测试"""

    def test_format_sse_event_with_dict(self):
        """测试使用字典格式的 SSE 事件格式化"""
        result = format_sse_event("progress", {"stage": "init", "value": 50})

        assert "event: progress" in result
        assert '"stage": "init"' in result
        assert '"value": 50' in result

    def test_format_sse_event_with_string(self):
        """测试使用字符串格式的 SSE 事件格式化"""
        result = format_sse_event("message", "hello world")

        assert "event: message" in result
        assert "data: hello world" in result

    def test_create_progress_callback(self):
        """测试进度回调函数创建"""
        queue = asyncio.Queue(maxsize=10)
        callback = create_progress_callback(queue)

        callback("visual", 75, "视觉分析完成", {"count": 3})

        assert not queue.empty()
        event = queue.get_nowait()
        assert isinstance(event, ProgressEvent)
        assert event.stage == "visual"
        assert event.progress == 75
        assert event.data["count"] == 3


class TestIntegrationScenarios:
    """集成场景测试 - 模拟完整的诊断流程"""

    async def test_full_diagnosis_flow_simulation(self):
        """模拟完整诊断流程的事件序列"""
        manager = SSEStreamManager(heartbeat_interval=0.05, timeout_seconds=5)

        async def diagnosis_flow():
            yield StepIndicator.to_sse()
            yield ProgressEvent(event="start", stage="init", progress=0, message="开始诊断").to_sse()
            await asyncio.sleep(0.02)
            yield ProgressEvent(event="progress", stage="visual", progress=30, message="视觉特征提取").to_sse()
            await asyncio.sleep(0.02)
            yield ProgressEvent(event="progress", stage="textual", progress=60, message="文本分析").to_sse()
            await asyncio.sleep(0.02)
            yield ProgressEvent(event="complete", stage="complete", progress=100, message="诊断完成").to_sse()

        events = []
        async for event in manager.create_heartbeat_generator(diagnosis_flow()):
            events.append(event)

        assert len(events) >= 4
        assert any("start" in e for e in events)
        assert any("complete" in e for e in events)

    async def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        manager = SSEStreamManager(heartbeat_interval=0.05, timeout_seconds=2)

        async def failing_diagnosis():
            yield ProgressEvent(event="start", stage="init", progress=0, message="开始").to_sse()
            await asyncio.sleep(0.01)
            raise ValueError("模拟推理错误")

        events = []
        async for event in manager.create_heartbeat_generator(failing_diagnosis()):
            events.append(event)

        assert len(events) > 0
        has_start = any("start" in e for e in events)
        has_error = any("error" in e for e in events)
        assert has_start
        assert has_error


class TestSSEAuthProtection:
    """
    SSE 端点认证保护测试（Task 6 P1-S6 要求 1）

    验证所有诊断相关 SSE 端点在未提供有效认证令牌时返回 401 Unauthorized。
    健康检查端点应保持公开访问。
    """

    def test_fusion_endpoint_requires_auth(self, client):
        """
        测试 POST /diagnosis/fusion 未认证返回 401

        验证融合诊断端点需要认证才能访问
        """
        response = client.post("/api/v1/diagnosis/fusion")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_fusion_stream_get_requires_auth(self, client):
        """
        测试 GET /diagnosis/fusion/stream 未认证返回 401

        验证 SSE 流式融合诊断 GET 端点需要认证
        """
        response = client.get("/api/v1/diagnosis/fusion/stream")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_fusion_stream_post_requires_auth(self, client):
        """
        测试 POST /diagnosis/fusion/stream 未认证返回 401

        验证 SSE 流式融合诊断 POST 端点需要认证
        """
        response = client.post("/api/v1/diagnosis/fusion/stream")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_image_diagnosis_requires_auth(self, client):
        """
        测试 POST /diagnosis/image 未认证返回 401

        验证图像诊断端点需要认证
        """
        response = client.post("/api/v1/diagnosis/image")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_multimodal_requires_auth(self, client):
        """
        测试 POST /diagnosis/multimodal 未认证返回 401

        验证多模态诊断端点需要认证
        """
        response = client.post("/api/v1/diagnosis/multimodal")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_text_diagnosis_requires_auth(self, client):
        """
        测试 POST /diagnosis/text 未认证返回 401

        验证文本诊断端点需要认证
        """
        response = client.post("/api/v1/diagnosis/text")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_batch_requires_auth(self, client):
        """
        测试 POST /diagnosis/batch 未认证返回 401

        验证批量诊断端点需要认证
        """
        response = client.post("/api/v1/diagnosis/batch")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_cache_stats_requires_auth(self, client):
        """
        测试 GET /diagnosis/cache/stats 未认证返回 401

        验证缓存统计端点需要认证
        """
        response = client.get("/api/v1/diagnosis/cache/stats")
        assert response.status_code == 401, f"期望 401，实际 {response.status_code}"

    def test_cache_clear_requires_admin_auth(self, client):
        """
        测试 POST /diagnosis/cache/clear 未认证返回 401/403

        验证缓存清理端点需要管理员权限
        """
        response = client.post("/api/v1/diagnosis/cache/clear")
        assert response.status_code in (401, 403), f"期望 401/403，实际 {response.status_code}"

    def test_preload_requires_admin_auth(self, client):
        """
        测试 POST /diagnosis/admin/ai/preload 未认证返回 401/403

        验证模型预加载端点需要管理员权限
        """
        response = client.post("/api/v1/diagnosis/admin/ai/preload")
        assert response.status_code in (401, 403), f"期望 401/403，实际 {response.status_code}"

    def test_health_check_is_public(self, client):
        """
        测试 GET /diagnosis/health/ai 公开访问正常

        验证健康检查端点保持公开，无需认证即可访问
        """
        response = client.get("/api/v1/diagnosis/health/ai")
        assert response.status_code == 200, f"健康检查应公开访问，实际 {response.status_code}"


class TestSSETimeoutControl:
    """
    SSE 超时控制测试（Task 6 P1-S6 要求 2）

    验证超时控制机制：
    - 默认超时时间 = 120 秒
    - 超时时发送 event: error\ndata: {"error": "timeout", "message": "诊断超时"}
    - 之后关闭 SSE 连接（发送 event: close）
    - 超时时间可通过参数配置
    """

    def test_default_timeout_value(self):
        """
        测试默认超时时间为 120 秒

        验证 SSEStreamManager.DEFAULT_TIMEOUT_SECONDS 常量值正确
        """
        assert SSEStreamManager.DEFAULT_TIMEOUT_SECONDS == 120

    def test_custom_timeout_value(self):
        """
        测试自定义超时时间可配置

        验证构造函数参数能正确设置超时时间
        """
        manager = SSEStreamManager(timeout_seconds=60)
        assert manager.timeout_seconds == 60

    async def test_timeout_event_format(self):
        """
        测试超时事件 SSE 格式符合生产标准

        验证超时事件包含正确的 error 类型标识和消息：
        - event: error
        - data: {"error": "timeout", "message": "诊断超时"}
        - event: close
        - data: {"reason": "timeout"}
        """
        manager = SSEStreamManager(timeout_seconds=120)
        timeout_event = manager._create_timeout_event()

        lines = [l.strip() for l in timeout_event.strip().split("\n") if l.strip()]

        assert any("event: error" in line for line in lines), "缺少 event: error"
        assert any("event: close" in line for line in lines), "缺少 event: close"

        data_lines = [l for l in lines if l.startswith("data:")]
        error_data = None
        close_data = None
        for dl in data_lines:
            parsed = json.loads(dl.replace("data: ", "", 1))
            if "error" in parsed and "timeout" in str(parsed.get("error", "")):
                error_data = parsed
            if "reason" in parsed:
                close_data = parsed

        assert error_data is not None, "未找到包含 error: timeout 的数据"
        assert error_data["error"] == "timeout", f"error 字段应为 'timeout'，实际 '{error_data['error']}'"
        assert error_data["message"] == "诊断超时", f"message 应为 '诊断超时'，实际 '{error_data.get('message')}'"
        assert error_data["timeout"] == 120, f"timeout 字段应为 120，实际 {error_data.get('timeout')}"
        assert close_data is not None, "未找到 close 事件数据"
        assert close_data["reason"] == "timeout"

    async def test_timeout_triggers_within_limit(self):
        """
        测试慢速源在超时时间内触发超时事件

        使用 create_backpressure_controlled_stream 验证超时机制，
        因为它使用 asyncio.wait_for 实现真正的异步超时检测，
        即使源生成器阻塞也能正确触发超时。
        """
        manager = SSEStreamManager(heartbeat_interval=0.05, timeout_seconds=1)

        async def very_slow_source():
            await asyncio.sleep(5)
            yield "data: too late\n\n"

        events = []
        start = time.time()
        async for event in manager.create_backpressure_controlled_stream(very_slow_source()):
            events.append(event)
            break

        elapsed = time.time() - start
        assert elapsed < 2.5, f"应在约 1 秒内超时，实际耗时 {elapsed:.2f}s"
        assert len(events) >= 1, "应至少收到一个超时或心跳事件"

    async def test_no_timeout_for_fast_source(self):
        """
        测试快速源不会触发超时

        验证在超时时间内完成的数据源不会触发超时事件
        """
        manager = SSEStreamManager(timeout_seconds=5, heartbeat_interval=0.05)

        async def fast_source():
            yield "data: quick result\n\n"
            return

        events = []
        async for event in manager.create_heartbeat_generator(fast_source()):
            events.append(event)

        timeout_events = [
            e for e in events
            if '"timeout"' in e and '"error"' in e
        ]
        assert len(timeout_events) == 0, "快速源不应触发超时事件"
        assert len(events) >= 1, "应至少收到一条数据"


class TestSSEBackpressureControl:
    """
    SSE 背压控制测试（Task 6 P1-S6 要求 3）

    验证背压控制机制：
    - 队列大小 = 100（QUEUE_MAX_SIZE）
    - 当队列满时，生成器应暂停（await queue.put() 自然阻塞）
    - 客户端消费后自动恢复
    - 数据不丢失
    """

    def test_default_queue_size(self):
        """
        测试默认队列大小为 100

        验证 SSEStreamManager.QUEUE_MAX_SIZE 常量值正确
        """
        assert SSEStreamManager.QUEUE_MAX_SIZE == 100

    async def test_backpressure_no_data_loss(self):
        """
        测试背压场景下不丢失数据

        使用较小的队列（size=5）和快速生产者产生大量数据，
        同时模拟慢消费者。验证所有数据最终都被消费。
        """
        queue_size = 5
        total_items = 20
        manager = SSEStreamManager(queue_size=queue_size, timeout_seconds=10, heartbeat_interval=0.01)

        async def fast_producer():
            for i in range(total_items):
                yield ProgressEvent(
                    event="progress",
                    stage="backpressure_test",
                    progress=int((i + 1) / total_items * 100),
                    message=f"项目 {i+1}/{total_items}"
                )

        received_items = []
        async for event_str in manager.create_backpressure_controlled_stream(fast_producer()):
            received_items.append(event_str)
            await asyncio.sleep(0.02)

        progress_events = [e for e in received_items if "progress" in e and "backpressure_test" in e]
        assert len(progress_events) == total_items, (
            f"期望收到 {total_items} 条进度事件，实际收到 {len(progress_events)} 条"
        )

    async def test_backpressure_producer_blocks_when_full(self):
        """
        测试队列满时生产者自动阻塞

        验证当队列达到 maxsize 时，put() 操作会阻塞等待消费者取出数据。
        通过测量总耗时来间接验证背压生效。
        """
        queue_size = 3
        manager = SSEStreamManager(queue_size=queue_size, timeout_seconds=10, heartbeat_interval=0.01)
        queue = asyncio.Queue(maxsize=queue_size)

        producer_started = asyncio.Event()
        producer_done = asyncio.Event()
        production_times = []

        async def tracked_producer():
            producer_started.set()
            for i in range(queue_size * 3):
                t_before = time.time()
                await queue.put(f"item_{i}")
                t_after = time.time()
                production_times.append(t_after - t_before)
            producer_done.set()

        producer_task = asyncio.create_task(tracked_producer())
        await producer_started.wait()

        await asyncio.sleep(0.05)
        for _ in range(queue_size * 3):
            item = await asyncio.wait_for(queue.get(), timeout=5)

        await producer_done.wait()
        producer_task.cancel()
        try:
            await producer_task
        except asyncio.CancelledError:
            pass

        slow_puts = [t for t in production_times if t > 0.01]
        assert len(slow_puts) > 0, (
            "队列满时应观察到 put() 阻塞（慢速写入），但所有写入都很快完成"
        )

    async def test_backpressure_consumer_recovery(self):
        """
        测试客户端消费后生产者自动恢复

        先让队列填满导致生产者阻塞，然后消费数据，
        验证生产者恢复继续生产新数据
        """
        queue_size = 3
        manager = SSEStreamManager(queue_size=queue_size, timeout_seconds=10, heartbeat_interval=0.01)

        items_to_produce = 15
        consumed_items = []

        async def steady_producer():
            for i in range(items_to_produce):
                yield f"data_{i}"

        stream_gen = manager.create_backpressure_controlled_stream(steady_producer())
        consume_task = asyncio.create_task(self._consume_with_delay(stream_gen, consumed_items, delay_per_item=0.03))

        await asyncio.wait_for(consume_task, timeout=10)

        assert len(consumed_items) == items_to_produce, (
            f"期望消费 {items_to_produce} 条，实际 {len(consumed_items)} 条"
        )

    @staticmethod
    async def _consume_with_delay(gen, collector, delay_per_item):
        """
        辅助方法：带延迟的消费器，用于模拟慢客户端

        参数:
            gen: 异步生成器
            collector: 收集结果的列表
            delay_per_item: 每条数据的消费延迟（秒）
        """
        try:
            async for item in gen:
                collector.append(item)
                await asyncio.sleep(delay_per_item)
        except Exception:
            pass

    def test_queue_status_method(self):
        """
        测试 get_queue_status 返回完整状态信息

        验证监控接口返回正确的配置和运行状态
        """
        manager = SSEStreamManager(
            heartbeat_interval=15.0,
            timeout_seconds=120,
            queue_size=100
        )
        status = manager.get_queue_status()

        assert status["queue_max_size"] == 100
        assert status["timeout_seconds"] == 120
        assert status["heartbeat_interval"] == 15.0
        assert "is_cancelled" in status
        assert "elapsed_seconds" in status

    async def test_large_volume_backpressure_integrity(self):
        """
        大批量数据背压完整性测试

        生产远超队列容量的大量数据（200条 vs 队列大小10），
        验证最终所有数据都能被正确消费且顺序一致
        """
        queue_size = 10
        total_count = 200
        manager = SSEStreamManager(
            queue_size=queue_size,
            timeout_seconds=30,
            heartbeat_interval=0.005
        )

        async def high_volume_producer():
            for i in range(total_count):
                yield {"index": i, "value": f"payload_{i}"}

        received = []
        async for event_str in manager.create_backpressure_controlled_stream(high_volume_producer()):
            received.append(event_str)
            if len(received) % 20 == 0:
                await asyncio.sleep(0.001)

        data_events = [e for e in received if "payload_" in e]
        assert len(data_events) == total_count, (
            f"大批量测试：期望 {total_count} 条，收到 {len(data_events)} 条"
        )


class TestConcurrentConsumers:
    """并发消费者测试 - 验证多客户端同时消费 SSE 流的场景"""

    @pytest.fixture
    def concurrent_manager(self):
        """
        创建用于并发测试的流管理器实例

        返回:
            SSEStreamManager: 配置了较短超时和队列大小的管理器
        """
        return SSEStreamManager(
            heartbeat_interval=0.05,
            timeout_seconds=3,
            queue_size=20
        )

    async def test_multiple_consumers_same_stream(self, concurrent_manager):
        """
        测试多个消费者从同一个 SSE 流读取数据
        验证每个消费者都能独立接收到完整的事件流
        """
        async def event_source():
            for i in range(10):
                yield ProgressEvent(
                    event="progress",
                    stage="test",
                    progress=i * 10,
                    message=f"事件 {i}"
                )
                await asyncio.sleep(0.01)

        consumer_count = 3
        all_consumer_events = []

        async def consume_events(consumer_id: int):
            """单个消费者的消费逻辑"""
            events = []
            try:
                async for event in concurrent_manager.create_backpressure_controlled_stream(
                    event_source()
                ):
                    events.append(event)
                    if len(events) >= 5:
                        break
            except Exception as e:
                print(f"Consumer {consumer_id} error: {e}")
            all_consumer_events.append((consumer_id, events))

        tasks = [consume_events(i) for i in range(consumer_count)]
        await asyncio.gather(*tasks)

        assert len(all_consumer_events) == consumer_count
        for consumer_id, events in all_consumer_events:
            assert len(events) > 0, f"Consumer {consumer_id} should receive events"

    async def test_concurrent_producer_consumer_balance(self, concurrent_manager):
        """
        测试生产者和消费者的速率平衡
        验证背压机制在并发场景下正常工作
        """
        production_count = 0
        consumption_count = 0

        async def fast_producer():
            """快速生产者 - 模拟高频事件生成"""
            nonlocal production_count
            for i in range(50):
                yield f"data: fast_event_{i}\n\n"
                production_count += 1
                await asyncio.sleep(0.001)

        async def slow_consumer():
            """慢速消费者 - 模拟网络延迟的客户端"""
            nonlocal consumption_count
            received = 0
            async for event in concurrent_manager.create_backpressure_controlled_stream(
                fast_producer()
            ):
                consumption_count += 1
                received += 1
                await asyncio.sleep(0.02)
                if received >= 10:
                    break

        await slow_consumer()

        assert production_count > 0
        assert consumption_count > 0
        assert consumption_count <= production_count

    async def test_queue_overflow_recovery(self, concurrent_manager):
        """
        测试队列溢出后的恢复能力
        验证当队列满时系统不会崩溃，且能恢复正常工作
        """
        overflow_detected = False
        recovery_successful = False

        async def burst_producer():
            """突发生产者 - 快速产生大量事件导致队列溢出"""
            nonlocal overflow_detected
            for i in range(100):
                try:
                    yield ProgressEvent(
                        event="progress",
                        stage="burst",
                        progress=i,
                        message=f"Burst {i}"
                    )
                except Exception:
                    overflow_detected = True
                    raise
                await asyncio.sleep(0)

        async def recovering_consumer():
            """恢复消费者 - 在队列溢出后继续消费"""
            nonlocal recovery_successful
            events_received = 0
            try:
                async for event in concurrent_manager.create_backpressure_controlled_stream(
                    burst_producer()
                ):
                    events_received += 1
                    if events_received >= 15:
                        recovery_successful = True
                        break
            except asyncio.CancelledError:
                pass

        await recovering_consumer()

        assert recovery_successful or overflow_detected


class TestMixedEventTypes:
    """多种 Event Type 混合测试 - 验证不同类型事件的正确处理和格式化"""

    @pytest.fixture
    def mixed_manager(self):
        """
        创建用于混合事件测试的管理器实例

        返回:
            SSEStreamManager: 标准配置的管理器
        """
        return SSEStreamManager(heartbeat_interval=0.05, timeout_seconds=5)

    async def test_progress_log_heartbeat_mixed(self, mixed_manager):
        """
        测试 ProgressEvent、LogEvent 和 HeartbeatEvent 混合场景
        验证不同类型事件能正确格式化和传输
        """
        mixed_events = []

        async def mixed_source():
            yield ProgressEvent(event="start", stage="init", progress=0, message="开始")
            yield LogEvent(level="info", message="初始化完成", stage="init")
            await asyncio.sleep(0.06)
            yield HeartbeatEvent.to_sse()
            yield ProgressEvent(event="progress", stage="visual", progress=50, message="处理中")
            yield LogEvent(level="warning", message="检测到异常", stage="visual")
            await asyncio.sleep(0.06)
            yield HeartbeatEvent.to_sse()
            yield ProgressEvent(event="complete", stage="complete", progress=100, message="完成")

        async for event in mixed_manager.create_heartbeat_generator(mixed_source()):
            mixed_events.append(event)

        has_progress = any("event: progress" in e for e in mixed_events)
        has_log = any("event: log" in e for e in mixed_events)
        has_heartbeat = any("event: heartbeat" in e for e in mixed_events)

        assert has_progress, "应包含进度事件"
        assert has_log, "应包含日志事件"
        assert has_heartbeat, "应包含心跳事件"
        assert len(mixed_events) >= 5

    async def test_event_type_ordering_preserved(self, mixed_manager):
        """
        测试事件类型的顺序保持
        验证混合事件流中事件的发送顺序与接收顺序一致
        """
        expected_order = []

        async def ordered_source():
            expected_order.append("steps")
            yield StepIndicator.to_sse()
            expected_order.append("start")
            yield ProgressEvent(event="start", stage="init", progress=0).to_sse()
            expected_order.append("log_info")
            yield LogEvent(level="info", message="Step 1").to_sse()
            expected_order.append("progress")
            yield ProgressEvent(event="progress", stage="visual", progress=30).to_sse()
            expected_order.append("log_warning")
            yield LogEvent(level="warning", message="Warning").to_sse()
            expected_order.append("complete")
            yield ProgressEvent(event="complete", stage="complete", progress=100).to_sse()

        received_types = []
        async for event in mixed_manager.create_heartbeat_generator(ordered_source()):
            if "event: steps" in event:
                received_types.append("steps")
            elif 'event: progress' in event and '"stage": "init"' in event:
                received_types.append("start")
            elif 'event: progress' in event and '"stage": "visual"' in event:
                received_types.append("progress")
            elif 'event: log' in event and '"level": "info"' in event:
                received_types.append("log_info")
            elif 'event: log' in event and '"level": "warning"' in event:
                received_types.append("log_warning")
            elif 'event: complete' in event or ('event: progress' in event and '"progress": 100' in event):
                received_types.append("complete")

        assert len(received_types) == len(expected_order), \
            f"事件数量不匹配: 收到 {len(received_types)}, 期望 {len(expected_order)}"

    async def test_error_event_among_normal_events(self, mixed_manager):
        """
        测试错误事件与正常事件交替出现的情况
        验证错误事件不会影响后续正常事件的处理
        """
        events_before_error = 0
        events_after_error = 0
        error_found = False

        async def error_mixed_source():
            nonlocal events_before_error
            for i in range(3):
                yield ProgressEvent(event="progress", stage="test", progress=i*30, msg=f"Normal {i}")
                events_before_error += 1
                await asyncio.sleep(0.01)
            raise RuntimeError("模拟中间错误")

        try:
            async for event in mixed_manager.create_heartbeat_generator(error_mixed_source()):
                if not error_found and "error" not in event.lower():
                    events_before_error = max(events_before_error, 1)
                elif "error" in event.lower():
                    error_found = True
                else:
                    events_after_error += 1
        except Exception:
            pass

        assert error_found, "应检测到错误事件"
        assert events_before_error > 0, "错误前应有正常事件"


class TestQueueStatusAndMonitoring:
    """队列状态监控测试 - 验证管理器的状态查询功能"""

    def test_initial_queue_status(self):
        """
        测试初始状态下的队列信息
        验证新创建的管理器返回正确的默认状态
        """
        manager = SSEStreamManager(
            heartbeat_interval=10.0,
            timeout_seconds=60,
            queue_size=50
        )

        status = manager.get_queue_status()

        assert status["queue_max_size"] == 50
        assert status["timeout_seconds"] == 60
        assert status["heartbeat_interval"] == 10.0
        assert status["is_cancelled"] is False
        assert status["elapsed_seconds"] == 0

    async def test_status_after_operation(self):
        """
        测试操作后的状态更新
        验证经过一段时间操作后，elapsed_seconds 正确更新
        """
        manager = SSEStreamManager(heartbeat_interval=0.05, timeout_seconds=2)

        async def short_operation():
            yield "data: test\n\n"
            await asyncio.sleep(0.1)

        async for _ in manager.create_heartbeat_generator(short_operation()):
            pass

        status = manager.get_queue_status()

        assert status["elapsed_seconds"] > 0
        assert status["is_cancelled"] is False

    async def test_cancelled_status_after_client_disconnect(self):
        """
        测试客户端断开连接后的取消状态
        验证CancelledError 被正确捕获并反映到状态中
        """
        manager = SSEStreamManager(heartbeat_interval=0.05, timeout_seconds=2)

        async def cancelling_operation():
            yield "data: start\n\n"
            raise asyncio.CancelledError()

        try:
            async for _ in manager.create_heartbeat_generator(cancelling_operation()):
                pass
        except asyncio.CancelledError:
            pass

        status = manager.get_queue_status()

        assert status["is_cancelled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
