# -*- coding: utf-8 -*-
"""
集成测试模块

测试各模块之间的协同工作能力
包含：
1. 六层架构端到端测试
2. 工具调用集成测试
3. 记忆引用集成测试
4. Graph-RAG 测试
"""

__all__ = [
    'IntegrationTestSuite',
    'EndToEndTestSuite',
    'ModuleIntegrationTest',
    'PerformanceBenchmarkTest',
    'SystemStabilityTest',
    # 新增测试函数
    'test_six_layer_architecture',
    'test_tool_integration',
    'test_memory_integration',
    'test_graphrag',
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
    # 新增测试函数
    elif name == 'test_six_layer_architecture':
        from .test_end_to_end import TestSixLayerArchitecture
        return TestSixLayerArchitecture
    elif name == 'test_tool_integration':
        from .test_tool_integration import TestToolManagerBasic
        return TestToolManagerBasic
    elif name == 'test_memory_integration':
        from .test_memory_integration import TestCaseMemoryBasic
        return TestCaseMemoryBasic
    elif name == 'test_graphrag':
        from .test_graphrag import TestGraphRAGSubgraphRetrieval
        return TestGraphRAGSubgraphRetrieval
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
