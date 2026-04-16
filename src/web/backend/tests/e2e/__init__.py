"""
端到端测试模块

包含以下测试组件：
- test_utils.py: 测试辅助工具
- test_user_scenarios.py: 用户场景测试用例
- test_business_flows.py: 业务流程测试脚本

测试场景：
1. 用户登录认证流程
2. 图像上传诊断流程
3. 文本诊断流程
4. 多模态融合诊断流程
5. SSE 实时进度推送流程
"""
from tests.e2e.test_utils import (
    TestConfig,
    TestDataGenerator,
    AuthHelper,
    SSEClient,
    PerformanceMonitor,
    TestReport,
    create_e2e_client,
    setup_mock_environment,
    teardown_mock_environment,
    assert_response_success,
    assert_diagnosis_result
)

__all__ = [
    "TestConfig",
    "TestDataGenerator",
    "AuthHelper",
    "SSEClient",
    "PerformanceMonitor",
    "TestReport",
    "create_e2e_client",
    "setup_mock_environment",
    "teardown_mock_environment",
    "assert_response_success",
    "assert_diagnosis_result"
]
