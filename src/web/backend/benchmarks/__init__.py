# -*- coding: utf-8 -*-
"""
WheatAgent 性能基准测试套件

提供关键路径的性能基线测量，用于：
- 建立性能基线数据
- 对比优化前后效果
- 检测性能退化

模块组成:
- benchmark_yolo_inference: YOLOv8 推理延迟
- benchmark_qwen_inference: Qwen3-VL 推理延迟
- benchmark_full_diagnosis: 完整诊断流程
- benchmark_sse_latency: SSE 流延迟
"""

from .benchmark_yolo_inference import benchmark_yolo_inference, YOLO_TARGET_MS
from .benchmark_qwen_inference import (
    benchmark_qwen_first_inference,
    benchmark_qwen_subsequent_inference,
    QWEN_FIRST_TARGET_S,
    QWEN_SUBSEQUENT_TARGET_S,
)
from .benchmark_full_diagnosis import benchmark_full_diagnosis, FULL_DIAGNOSIS_TARGET_S
from .benchmark_sse_latency import (
    benchmark_sse_manager_creation,
    benchmark_sse_first_event,
    benchmark_sse_heartbeat,
    SSE_FIRST_EVENT_TARGET_MS,
)

__all__ = [
    "benchmark_yolo_inference",
    "YOLO_TARGET_MS",
    "benchmark_qwen_first_inference",
    "benchmark_qwen_subsequent_inference",
    "QWEN_FIRST_TARGET_S",
    "QWEN_SUBSEQUENT_TARGET_S",
    "benchmark_full_diagnosis",
    "FULL_DIAGNOSIS_TARGET_S",
    "benchmark_sse_manager_creation",
    "benchmark_sse_first_event",
    "benchmark_sse_heartbeat",
    "SSE_FIRST_EVENT_TARGET_MS",
]
