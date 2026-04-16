"""
AI 诊断 API 端点（薄包装层）
本文件作为向后兼容的薄包装层，所有功能已拆分到以下模块：
- diagnosis_router.py: 路由注册层（API 端点定义）
- sse_stream_manager.py: SSE 流管理层（事件流管理）
- diagnosis_validator.py: 请求验证层（文件验证、Mock 切换等）

保持此文件以确保现有 import 语句的向后兼容性。
"""
from .diagnosis_router import router
from .sse_stream_manager import (
    ProgressEvent,
    HeartbeatEvent,
    LogEvent,
    StepIndicator,
    SSEStreamManager,
    create_progress_callback,
    format_sse_event,
)
from .diagnosis_validator import (
    validate_image,
    check_image_magic_number,
    is_mock_enabled,
    should_use_mock,
    get_mock_service,
    get_cache_manager_safe,
    check_gpu_memory,
    acquire_rate_limit,
    release_rate_limit,
    preprocess_image,
    DiagnosisRequestValidator,
)

__all__ = [
    'router',
    'ProgressEvent',
    'HeartbeatEvent',
    'LogEvent',
    'StepIndicator',
    'SSEStreamManager',
    'create_progress_callback',
    'format_sse_event',
    'validate_image',
    'check_image_magic_number',
    'is_mock_enabled',
    'should_use_mock',
    'get_mock_service',
    'get_cache_manager_safe',
    'check_gpu_memory',
    'acquire_rate_limit',
    'release_rate_limit',
    'preprocess_image',
    'DiagnosisRequestValidator',
]
