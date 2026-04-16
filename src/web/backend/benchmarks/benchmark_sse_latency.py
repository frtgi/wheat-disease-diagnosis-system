# -*- coding: utf-8 -*-
"""
性能基准测试：SSE 流管理器延迟

测量 SSE (Server-Sent Events) 流相关操作的响应时间，用于：
- 建立 SSE 性能基线
- 评估心跳保活机制效率
- 检测事件生成延迟问题

测试项目:
- SSEStreamManager 创建延迟
- ProgressEvent 生成延迟
- 心跳事件生成延迟
- 首个事件到达延迟（通过模拟流）

目标值: SSE 首个事件 < 500ms

使用 time.perf_counter() 高精度计时。
"""
import time
import statistics
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

SSE_FIRST_EVENT_TARGET_MS = 500.0


def benchmark_sse_manager_creation(iterations: int = 100) -> Dict[str, Any]:
    """
    执行 SSEStreamManager 实例化基准测试

    测量 SSE 流管理器对象的创建耗时，
    包括初始化内部状态（队列、定时器配置等）。

    Args:
        iterations: 创建迭代次数（默认 100 次，轻量操作）

    Returns:
        Dict[str, Any]: 创建延迟的统计结果
    """
    print("=" * 60)
    print("📊 SSEStreamManager 创建延迟基准测试")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    results = []
    details = []

    try:
        from app.api.v1.sse_stream_manager import SSEStreamManager

        for i in range(iterations):
            start = time.perf_counter()
            manager = SSEStreamManager(
                heartbeat_interval=15.0,
                timeout_seconds=120,
                queue_size=100,
            )
            elapsed = time.perf_counter() - start
            elapsed_us = elapsed * 1_000_000

            results.append(elapsed)
            details.append({
                "iteration": i + 1,
                "elapsed_us": round(elapsed_us, 2),
                "heartbeat_interval": manager.heartbeat_interval,
                "timeout_seconds": manager.timeout_seconds,
                "queue_size": manager.queue_size,
            })

            if (i + 1) % 20 == 0 or i == 0:
                print(f"  进度: {i+1}/{iterations} (最新 {elapsed_us:.2f}μs)")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "status": "skipped", "details": [], "note": f"N/A ({e})",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": statistics.mean(results) if results else float("nan"),
            "median": statistics.median(results) if results else float("nan"),
            "min": min(results) if results else float("nan"),
            "max": max(results) if results else float("nan"),
            "stdev": statistics.stdev(results) if len(results) > 1 else 0.0,
            "iterations": len(results), "status": "error",
            "details": details, "error": str(e),
        }

    if not results:
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "status": "skipped", "details": [],
        }

    mean_us = statistics.mean(results) * 1_000_000

    print(f"\n{'='*60}")
    print(f"📈 Manager 创建结果汇总:")
    print(f"   平均值: {mean_us:.2f}μs")
    print(f"   中位数: {statistics.median(results)*1_000_000:.2f}μs")
    print(f"   最小值: {min(results)*1_000_000:.2f}μs")
    print(f"   最大值: {max(results)*1_000_000:.2f}μs")
    print(f"{'='*60}\n")

    return {
        "mean": round(statistics.mean(results), 8),
        "median": round(statistics.median(results), 8),
        "min": round(min(results), 8),
        "max": round(max(results), 8),
        "stdev": round(statistics.stdev(results) if len(results) > 1 else 0, 8),
        "unit": "seconds",
        "mean_us": round(mean_us, 2),
        "iterations": iterations,
        "status": "passed",
        "details": details[:10],
    }


def benchmark_sse_progress_event(iterations: int = 1000) -> Dict[str, Any]:
    """
    执行 ProgressEvent SSE 格式化基准测试

    测量 ProgressEvent.to_sse() 的序列化和格式化耗时。

    Args:
        iterations: 事件生成迭代次数（默认 1000 次）

    Returns:
        Dict[str, Any]: 格式化延迟的统计结果
    """
    print("=" * 60)
    print("📊 ProgressEvent 格式化延迟基准测试")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    results = []
    details = []

    try:
        from app.api.v1.sse_stream_manager import ProgressEvent

        for i in range(iterations):
            event = ProgressEvent(
                event="progress",
                stage="visual_analysis",
                progress=i % 101,
                message=f"处理中... {i}",
                data={"iteration": i},
            )

            start = time.perf_counter()
            sse_str = event.to_sse()
            elapsed = time.perf_counter() - start
            elapsed_us = elapsed * 1_000_000

            results.append(elapsed)
            if i < 5 or i == iterations - 1:
                details.append({
                    "iteration": i + 1,
                    "elapsed_us": round(elapsed_us, 2),
                    "output_len": len(sse_str),
                })

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "status": "skipped", "details": [],
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": statistics.mean(results) if results else float("nan"),
            "median": statistics.median(results) if results else float("nan"),
            "stdev": statistics.stdev(results) if len(results) > 1 else 0.0,
            "iterations": len(results), "status": "error",
            "details": details, "error": str(e),
        }

    mean_us = statistics.mean(results) * 1_000_000
    print(f"\n📈 ProgressEvent 格式化结果: 平均 {mean_us:.2f}μs/次\n")

    return {
        "mean": round(statistics.mean(results), 8),
        "median": round(statistics.median(results), 8),
        "min": round(min(results), 8),
        "max": round(max(results), 8),
        "stdev": round(statistics.stdev(results) if len(results) > 1 else 0, 8),
        "unit": "seconds",
        "mean_us": round(mean_us, 2),
        "iterations": iterations,
        "status": "passed",
        "details": details,
    }


def benchmark_sse_heartbeat(iterations: int = 1000) -> Dict[str, Any]:
    """
    执行 HeartbeatEvent 生成基准测试

    测量心跳事件的生成和序列化耗时。

    Args:
        iterations: 心跳事件生成迭代次数

    Returns:
        Dict[str, Any]: 心跳事件生成的统计结果
    """
    print("=" * 60)
    print("📊 HeartbeatEvent 生成延迟基准测试")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    results = []

    try:
        from app.api.v1.sse_stream_manager import HeartbeatEvent

        for _ in range(iterations):
            start = time.perf_counter()
            sse_str = HeartbeatEvent.to_sse()
            elapsed = time.perf_counter() - start
            results.append(elapsed)

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"), "iterations": 0, "status": "skipped",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {"mean": float("nan"), "iterations": len(results), "status": "error", "error": str(e)}

    mean_us = statistics.mean(results) * 1_000_000
    print(f"\n📈 HeartbeatEvent 生成结果: 平均 {mean_us:.2f}μs/次\n")

    return {
        "mean": round(statistics.mean(results), 8),
        "median": round(statistics.median(results), 8),
        "min": round(min(results), 8),
        "max": round(max(results), 8),
        "stdev": round(statistics.stdev(results) if len(results) > 1 else 0, 8),
        "mean_us": round(mean_us, 2),
        "iterations": iterations,
        "status": "passed",
    }


async def benchmark_sse_first_event_async() -> Dict[str, Any]:
    """
    异步执行 SSE 首个事件到达延迟测试

    模拟完整的 SSE 流创建 → 首个事件输出流程，
    测量从流启动到客户端收到第一个事件的时间。

    Returns:
        Dict[str, Any]: 首个事件延迟的统计结果
    """
    print("=" * 60)
    print("📊 SSE 首个事件到达延迟基准测试 (异步)")
    print(f"   目标值: < {SSE_FIRST_EVENT_TARGET_MS}ms")
    print("=" * 60)

    results = []
    iterations = 50

    try:
        from app.api.v1.sse_stream_manager import (
            SSEStreamManager,
            ProgressEvent,
            HeartbeatEvent,
        )

        for i in range(iterations):
            manager = SSEStreamManager(
                heartbeat_interval=15.0,
                timeout_seconds=120,
                queue_size=100,
            )

            async def mock_source():
                yield ProgressEvent(
                    event="start",
                    stage="init",
                    progress=0,
                    message="诊断开始",
                ).to_sse()

            start = time.perf_counter()
            first_event_arrived = False
            first_event_time = None

            async for event_str in manager.create_heartbeat_generator(mock_source()):
                if not first_event_arrived:
                    first_event_time = time.perf_counter() - start
                    first_event_arrived = True
                    results.append(first_event_time)
                break

            if not first_event_arrived:
                results.append(float("nan"))

            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{iterations}")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"), "iterations": 0,
            "target_ms": SSE_FIRST_EVENT_TARGET_MS, "status": "skipped",
            "note": f"N/A ({e})",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": float("nan"), "iterations": len(results),
            "target_ms": SSE_FIRST_EVENT_TARGET_S, "status": "error",
            "error": str(e),
        }

    valid_results = [r for r in results if not (r != r)]
    if not valid_results:
        return {
            "mean": float("nan"), "iterations": iterations,
            "target_ms": SSE_FIRST_EVENT_TARGET_MS, "status": "skipped",
        }

    mean_s = statistics.mean(valid_results)
    mean_ms = mean_s * 1000
    status = "passed" if mean_ms < SSE_FIRST_EVENT_TARGET_MS else "warning"

    print(f"\n{'='*60}")
    print(f"📈 SSE 首个事件延迟结果:")
    print(f"   平均值: {mean_ms:.2f}ms")
    print(f"   中位数: {statistics.median(valid_results)*1000:.2f}ms")
    print(f"   最小值: {min(valid_results)*1000:.2f}ms")
    print(f"   最大值: {max(valid_results)*1000:.2f}ms")
    print(f"   状态: {'✅ 达标' if status=='passed' else '⚠️ 未达标'} (目标 <{SSE_FIRST_EVENT_TARGET_MS}ms)")
    print(f"{'='*60}\n")

    return {
        "mean": round(mean_s, 6),
        "median": round(statistics.median(valid_results), 6),
        "min": round(min(valid_results), 6),
        "max": round(max(valid_results), 6),
        "stdev": round(statistics.stdev(valid_results) if len(valid_results) > 1 else 0, 6),
        "unit": "seconds",
        "mean_ms": round(mean_ms, 2),
        "iterations": iterations,
        "valid_iterations": len(valid_results),
        "target_ms": SSE_FIRST_EVENT_TARGET_MS,
        "status": status,
    }


def benchmark_sse_first_event(iterations: int = 50) -> Dict[str, Any]:
    """
    同步包装函数：执行 SSE 首个事件到达延迟测试

    Args:
        iterations: 测试迭代次数

    Returns:
        Dict[str, Any]: 首个事件延迟统计结果
    """
    return asyncio.run(benchmark_sse_first_event_async())


if __name__ == "__main__":
    import json

    print("\n" + "#" * 70)
    print("# SSE 流延迟基准测试套件")
    print("#" * 70 + "\n")

    r1 = benchmark_sse_manager_creation(iterations=100)
    print(json.dumps(r1, indent=2, ensure_ascii=False, default=str))

    r2 = benchmark_sse_progress_event(iterations=1000)
    print(json.dumps(r2, indent=2, ensure_ascii=False, default=str))

    r3 = benchmark_sse_heartbeat(iterations=1000)
    print(json.dumps(r3, indent=2, ensure_ascii=False, default=str))

    r4 = benchmark_sse_first_event(iterations=50)
    print(json.dumps(r4, indent=2, ensure_ascii=False, default=str))
