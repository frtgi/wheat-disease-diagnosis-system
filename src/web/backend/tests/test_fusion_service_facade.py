# -*- coding: utf-8 -*-
"""
多模态融合服务 Facade 测试模块

覆盖范围:
- deprecated 装饰器功能验证
- PipelineTimer 计时器类
- MultimodalFusionService 门面类初始化与组合关系
- diagnose_async 异步入口存在性
- @deprecated 标记验证 (diagnose / _check_cache)
- Facade 子模块组合关系验证（FeatureExtractor + FusionEngine + ResultAnnotator）
"""

import time
import warnings
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

import pytest

# 导入被测模块
from app.services.fusion_service import (
    deprecated,
    PipelineTimer,
    MultimodalFusionService,
    FusionResult,
    get_fusion_service,
)


class TestDeprecatedDecorator:
    """deprecated 装饰器测试"""

    def test_deprecated_emits_warning(self):
        """
        测试弃用装饰器发出 DeprecationWarning

        验证调用标记为弃用的方法时会触发警告
        """
        @deprecated("new_method")
        def old_method():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_method()

            assert result == "result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "已弃用" in str(w[0].message)
            assert "new_method" in str(w[0].message)

    def test_deprecated_preserves_function_name(self):
        """
        测试弃用装饰器保留原始函数名和文档

        验证 functools.wraps 正确工作
        """
        @deprecated("replacement")
        def original_function(x, y):
            """原始函数文档"""
            return x + y

        assert original_function.__name__ == "original_function"
        assert "原始函数文档" in original_function.__doc__
        assert original_function(2, 3) == 5


class TestPipelineTimer:
    """PipelineTimer 流水线计时器测试"""

    def test_timer_initialization(self):
        """
        测试计时器初始化状态

        验证初始属性正确设置
        """
        timer = PipelineTimer()

        assert timer._stages == {}
        assert timer._start is None
        assert timer._current_stage is None

    def test_manual_start_and_end(self):
        """
        测试手动开始和结束计时

        验证 start()/end() 返回合理的耗时值
        """
        timer = PipelineTimer()
        timer.start("test_stage")

        time.sleep(0.05)  # 50ms 延迟
        elapsed = timer.end("test_stage")

        assert elapsed >= 40  # 至少 40ms（允许误差）
        assert elapsed < 200  # 不超过 200ms
        assert "test_stage" in timer._stages

    def test_context_manager_timing(self):
        """
        测试上下文管理器模式计时

        验证 with 语句正确记录阶段耗时
        """
        timer = PipelineTimer()

        with timer.stage("context_test"):
            time.sleep(0.05)

        assert "context_test" in timer._stages
        assert timer._stages["context_test"] >= 40

    def test_multiple_stages(self):
        """
        测试多个阶段的计时

        验证计时器能跟踪多个独立阶段
        """
        timer = PipelineTimer()

        with timer.stage("stage1"):
            time.sleep(0.02)

        with timer.stage("stage2"):
            time.sleep(0.03)

        summary = timer.summary()
        assert summary["stage_count"] == 2
        assert "stage1" in summary["stages"]
        assert "stage2" in summary["stages"]

    def test_summary_structure(self):
        """
        测试摘要输出结构

        验证 summary() 返回包含所有必需字段
        """
        timer = PipelineTimer()

        with timer.stage("sample"):
            pass

        info = timer.summary()

        assert "stages" in info
        assert "total_stages_ms" in info
        assert "stage_count" in info
        assert "pipeline_total_ms" in info
        assert "overhead_ms" in info
        assert info["stage_count"] == 1

    def test_end_without_start_returns_zero(self):
        """
        测试在未调用 start() 时调用 end()

        验证边界情况返回 0 而不抛异常
        """
        timer = PipelineTimer()
        elapsed = timer.end("nonexistent")

        assert elapsed == 0.0

    def test_reset_clears_state(self):
        """
        测试重置计时器

        验证 reset() 清除所有记录并重新开始
        """
        timer = PipelineTimer()

        with timer.stage("to_be_cleared"):
            time.sleep(0.01)

        assert len(timer._stages) > 0

        timer.reset()
        assert timer._stages == {}
        assert timer._start is None


class TestMultimodalFusionServiceInit:
    """MultimodalFusionService 初始化与配置测试"""

    def test_facade_initialization_default(self):
        """
        测试门面类默认初始化

        验证创建实例时正确初始化子模块占位符
        """
        service = MultimodalFusionService()

        assert service._initialized is False
        assert service._warmed_up is False
        assert service._enable_cache is True
        assert hasattr(service, '_feature_extractor')
        assert hasattr(service, '_fusion_engine')
        assert hasattr(service, '_result_annotator')

    def test_facade_initialization_with_cache_disabled(self):
        """
        测试禁用缓存的初始化

        验证 enable_cache 参数生效
        """
        service = MultimodalFusionService(enable_cache=False)

        assert service._enable_cache is False

    def test_submodule_composition(self):
        """
        测试 Facade 组合关系：子模块类型验证

        验证三个核心子模块被正确实例化
        """
        from app.services.fusion_feature_extractor import FeatureExtractor
        from app.services.fusion_engine import FusionEngine
        from app.services.fusion_annotator import ResultAnnotator

        service = MultimodalFusionService()

        assert isinstance(service._feature_extractor, FeatureExtractor)
        assert isinstance(service._fusion_engine, FusionEngine)
        assert isinstance(service._result_annotator, ResultAnnotator)


class TestMultimodalFusionServiceDeprecatedMethods:
    """MultimodalFusionService 弃用方法测试"""

    def test_diagnose_deprecated_warning(self):
        """
        测试同步 diagnose() 方法的弃用标记

        验证调用时发出 DeprecationWarning 并推荐使用 diagnose_async
        """
        service = MultimodalFusionService()

        with patch.object(service, 'initialize'):
            with patch.object(service, '_result_annotator') as mock_annotator:
                mock_annotator.pil_to_bytes.return_value = b''
                mock_annotator.check_cache.return_value = None

                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")

                    try:
                        result = service.diagnose(symptoms="test")
                    except Exception:
                        result = {"error": "mocked"}

                    deprecation_warnings = [
                        warning for warning in w
                        if issubclass(warning.category, DeprecationWarning)
                    ]
                    assert len(deprecation_warnings) > 0
                    assert "diagnose_async" in str(deprecation_warnings[0].message)

    def test_check_cache_deprecated_warning(self):
        """
        测试 _check_cache() 方法的弃用标记

        验证调用时发出警告并推荐内联 await 调用
        """
        service = MultimodalFusionService()

        with patch.object(service, '_result_annotator') as mock_annotator:
            mock_annotator.check_cache.return_value = None

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                try:
                    result = service._check_cache(b'test_data', "symptoms")
                except Exception:
                    result = None

                deprecation_warnings = [
                    warning for warning in w
                    if issubclass(warning.category, DeprecationWarning)
                ]
                assert len(deprecation_warnings) > 0
                assert "check_cache" in str(deprecation_warnings[0].message).lower()


class TestMultimodalFusionServiceAsyncInterface:
    """MultimodalFusionService 异步接口测试"""

    @pytest.mark.asyncio
    async def test_diagnose_async_exists_and_callable(self):
        """
        测试 diagnose_async 方法存在且可调用

        验证异步入口点可用且签名正确
        """
        service = MultimodalFusionService()

        assert hasattr(service, 'diagnose_async')
        assert callable(service.diagnose_async)

    @pytest.mark.asyncio
    async def test_diagnose_async_basic_call(self):
        """
        测试 diagnose_async 基本调用流程

        验证异步方法能正常执行并返回结果字典
        """
        service = MultimodalFusionService()

        with patch.object(service, 'initialize'):
            with patch.object(service._feature_extractor, 'extract_all_features') as mock_extract:
                mock_extract.return_value = (None, None, None)

                with patch.object(service._fusion_engine, 'fuse_features') as mock_fuse:
                    mock_result = MagicMock(spec=FusionResult)
                    mock_result.disease_name = "锈病"
                    mock_result.confidence = 0.85
                    mock_fuse.return_value = mock_result

                    with patch.object(service._result_annotator, 'build_response_dict') as mock_build:
                        mock_build.return_value = {
                            "success": True,
                            "diagnosis": {"disease": "锈病"},
                            "model": "fusion_engine",
                            "features": {},
                            "cache_hit": False
                        }

                        result = await service.diagnose_async(
                            symptoms="叶片出现橙色斑点"
                        )

                        assert isinstance(result, dict)
                        assert "success" in result
                        assert "features" in result

    @pytest.mark.asyncio
    async def test_diagnose_async_triggers_initialize(self):
        """
        测试未初始化时 diagnose_async 自动触发 initialize

        验证懒初始化机制工作正常
        """
        service = MultimodalFusionService()
        assert service._initialized is False

        with patch.object(service, 'initialize') as mock_init:
            with patch.object(service._feature_extractor, 'extract_all_features', return_value=(None, None, None)):
                with patch.object(service._fusion_engine, 'fuse_features') as mock_fuse:
                    mock_result = MagicMock(spec=FusionResult)
                    mock_fuse.return_value = mock_result

                    with patch.object(service._result_annotator, 'build_response_dict', return_value={}):
                        with patch.object(service._result_annotator, 'pil_to_bytes', return_value=None):
                            try:
                                await service.diagnose_async(symptoms="test")
                            except Exception:
                                pass

                            mock_init.assert_called_once()


class TestMultimodalFusionServiceProxyMethods:
    """MultimodalFusionService 代理方法测试"""

    def test_extract_visual_features_proxy(self):
        """
        测试 _extract_visual_features 代理方法

        验证委托给 FeatureExtractor.extract_visual_features
        """
        service = MultimodalFusionService()
        mock_image = MagicMock()

        with patch.object(service._feature_extractor, 'extract_visual_features', return_value={"detections": []}) as mock_method:
            result = service._extract_visual_features(mock_image)

            mock_method.assert_called_once_with(mock_image)
            assert result == {"detections": []}

    def test_extract_textual_features_proxy(self):
        """
        测试 _extract_textual_features 代理方法

        验证委托给 FeatureExtractor.extract_textual_features
        """
        service = MultimodalFusionService()

        with patch.object(service._feature_extractor, 'extract_textual_features', return_value={"text": "analysis"}) as mock_method:
            result = service._extract_textual_features(
                image=None,
                symptoms="症状描述",
                knowledge_context=None,
                enable_thinking=False
            )

            mock_method.assert_called_once()
            assert result == {"text": "analysis"}

    def test_retrieve_knowledge_proxy(self):
        """
        测试 _retrieve_knowledge 代理方法

        验证委托给 FeatureExtractor.extract_knowledge_features
        """
        service = MultimodalFusionService()

        with patch.object(service._feature_extractor, 'extract_knowledge_features', return_value={"knowledge": []}) as mock_method:
            result = service._retrieve_knowledge(symptoms="小麦病害", disease_hint="锈病")

            mock_method.assert_called_once_with(symptoms="小麦病害", disease_hint="锈病")
            assert result == {"knowledge": []}

    def test_fuse_features_proxy(self):
        """
        测试 _fuse_features 代理方法

        验证委托给 FusionEngine.fuse_features
        """
        service = MultimodalFusionService()
        mock_visual = {"detections": []}  # 空列表，不会触发 annotate_image
        mock_fusion_result = MagicMock(spec=FusionResult)

        with patch.object(service._fusion_engine, 'fuse_features', return_value=mock_fusion_result) as mock_fuse:
            result = service._fuse_features(
                visual_result=mock_visual,
                textual_result=None,
                knowledge_context=None
            )

            mock_fuse.assert_called_once()
            assert result == mock_fusion_result


class TestGetFusionServiceSingleton:
    """get_fusion_service 单例工厂函数测试"""

    def test_singleton_pattern(self):
        """
        测试单例模式：多次调用返回同一实例

        验证全局共享同一个融合服务实例
        """
        instance1 = get_fusion_service()
        instance2 = get_fusion_service()

        assert instance1 is instance2
        assert isinstance(instance1, MultimodalFusionService)

    def test_get_fusion_service_returns_instance(self):
        """
        测试获取融合服务实例

        验证工厂函数返回有效实例
        """
        from app.services.fusion_service import _fusion_service_instance

        instance = get_fusion_service()
        assert instance is not None
        assert isinstance(instance, MultimodalFusionService)
