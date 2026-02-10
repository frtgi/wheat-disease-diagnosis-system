# -*- coding: utf-8 -*-
"""
集成测试模块

测试各模块之间的协同工作能力
"""

__all__ = [
    'IntegrationTestSuite',
    'EndToEndTestSuite',
    'ModuleIntegrationTest',
    'PerformanceBenchmarkTest',
    'SystemStabilityTest',
]


def __getattr__(name):
    """延迟导入测试类"""
    if name == 'IntegrationTestSuite':
        from .test_integration import IntegrationTestSuite
        return IntegrationTestSuite
    elif name == 'EndToEndTestSuite':
        from .test_end_to_end import EndToEndTestSuite
        return EndToEndTestSuite
    elif name == 'ModuleIntegrationTest':
        from .test_module_integration import ModuleIntegrationTest
        return ModuleIntegrationTest
    elif name == 'PerformanceBenchmarkTest':
        from .test_performance import PerformanceBenchmarkTest
        return PerformanceBenchmarkTest
    elif name == 'SystemStabilityTest':
        from .test_stability import SystemStabilityTest
        return SystemStabilityTest
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
