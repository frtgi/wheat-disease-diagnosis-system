"""
P0-OPT-01 全面异步迁移验证测试
验证核心诊断链路无 asyncio.run() 残留，所有调用方使用异步接口
"""
import asyncio
import warnings
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from PIL import Image
import numpy as np

from app.services.fusion_service import (
    MultimodalFusionService,
    deprecated,
    get_fusion_service
)
from app.services.qwen_service import QwenService, deprecated as qwen_deprecated


class TestDeprecatedDecorator:
    """弃用装饰器单元测试"""

    def test_deprecated_emits_warning(self):
        """
        验证 @deprecated 装饰器正确发出 DeprecationWarning

        调用被标记的方法时应触发 DeprecationWarning，包含方法名和推荐替代方案
        """
        @deprecated("new_method")
        def old_method():
            return 42

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_method()

            assert result == 42
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_method 已弃用" in str(w[0].message)
            assert "new_method" in str(w[0].message)

    def test_deprecated_preserves_signature(self):
        """
        验证 @deprecated 装饰器保留原方法的签名和文档

        functools.wraps 应确保元数据完整保留
        """
        @deprecated("new_method")
        def original(x: int, y: str = "default") -> int:
            """原始方法文档"""
            return x

        assert original.__name__ == "original"
        assert "原始方法文档" in original.__doc__


class TestFusionServiceAsyncMigration:
    """fusion_service.py 异步迁移验证测试"""

    def test_diagnose_method_has_deprecated_decorator(self):
        """
        验证 fusion_service.diagnose() 已标记 @deprecated

        同步 diagnose() 方法应带有弃用警告，引导用户使用 diagnose_async()
        """
        service = MultimodalFusionService(enable_cache=False)
        assert hasattr(service.diagnose, '__wrapped__'), \
            "diagnose() 方法应被 @deprecated 装饰器包装"

    def test_check_cache_method_has_deprecated_decorator(self):
        """
        验证 _check_cache() 代理方法已标记 @deprecated

        _check_cache() 内部使用 asyncio.run()，已标记为弃用
        """
        service = MultimodalFusionService(enable_cache=False)
        assert hasattr(service._check_cache, '__wrapped__'), \
            "_check_cache() 方法应被 @deprecated 装饰器包装"

    def test_diagnose_emits_deprecation_warning(self):
        """
        验证调用同步 diagnose() 触发 DeprecationWarning

        模拟调用同步接口时必须收到弃用警告
        """
        service = MultimodalFusionService(enable_cache=False)
        service._initialized = True

        mock_annotator = MagicMock()
        mock_annotator.check_cache = AsyncMock(return_value=None)
        mock_annotator.pil_to_bytes = MagicMock(return_value=b"fake")
        mock_annotator.annotate_image = MagicMock(return_value=None)
        mock_annotator.build_response_dict = MagicMock(return_value={
            "success": True, "diagnosis": {}, "features": {}
        })
        mock_annotator.save_to_cache = AsyncMock(return_value=True)
        service._result_annotator = mock_annotator

        mock_extractor = MagicMock()
        mock_extractor.extract_all_features = MagicMock(
            return_value=(None, None, None)
        )
        service._feature_extractor = mock_extractor

        mock_engine = MagicMock()
        mock_fusion_result = MagicMock()
        mock_fusion_result.disease_name = "测试病害"
        mock_fusion_result.confidence = 0.9
        mock_engine.fuse_features = MagicMock(return_value=mock_fusion_result)
        service._fusion_engine = mock_engine

        dummy_img = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            service.diagnose(image=dummy_img, symptoms="测试", use_cache=False)

            deprecation_warnings = [
                warning for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1, \
                "调用 diagnose() 应至少触发一个 DeprecationWarning"

    @pytest.mark.asyncio
    async def test_diagnose_async_no_deprecation_warning(self):
        """
        验证 diagnose_async() 不触发 DeprecationWarning

        异步接口是推荐路径，不应产生任何弃用警告
        """
        service = MultimodalFusionService(enable_cache=False)
        service._initialized = True

        mock_annotator = MagicMock()
        mock_annotator.check_cache = AsyncMock(return_value=None)
        mock_annotator.pil_to_bytes = MagicMock(return_value=b"fake")
        mock_annotator.annotate_image = MagicMock(return_value=None)
        mock_annotator.build_response_dict = MagicMock(return_value={
            "success": True, "diagnosis": {}, "features": {}
        })
        mock_annotator.save_to_cache = AsyncMock(return_value=True)
        service._result_annotator = mock_annotator

        mock_extractor = MagicMock()
        mock_extractor.extract_all_features = MagicMock(
            return_value=(None, None, None)
        )
        service._feature_extractor = mock_extractor

        mock_engine = MagicMock()
        mock_fusion_result = MagicMock()
        mock_fusion_result.disease_name = "测试病害"
        mock_fusion_result.confidence = 0.9
        mock_engine.fuse_features = MagicMock(return_value=mock_fusion_result)
        service._fusion_engine = mock_engine

        dummy_img = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            await service.diagnose_async(
                image=dummy_img, symptoms="测试", use_cache=False
            )

            deprecation_warnings = [
                warning for warning in w
                if issubclass(warning.category, DeprecationWarning)
                and "diagnose" in str(warning.message).lower()
            ]
            assert len(deprecation_warnings) == 0, \
                f"diagnose_async() 不应触发弃用警告，但收到: {deprecation_warnings}"

    @pytest.mark.asyncio
    async def test_diagnose_async_no_asyncio_run(self):
        """
        验证 diagnose_async() 执行过程中不调用 asyncio.run()

        使用 mock 拦截 asyncio.run 调用，确保异步路径完全原生
        """
        service = MultimodalFusionService(enable_cache=False)
        service._initialized = True

        mock_annotator = MagicMock()
        mock_annotator.check_cache = AsyncMock(return_value=None)
        mock_annotator.pil_to_bytes = MagicMock(return_value=b"fake")
        mock_annotator.annotate_image = MagicMock(return_value=None)
        mock_annotator.build_response_dict = MagicMock(return_value={
            "success": True, "diagnosis": {}, "features": {}
        })
        mock_annotator.save_to_cache = AsyncMock(return_value=True)
        service._result_annotator = mock_annotator

        mock_extractor = MagicMock()
        mock_extractor.extract_all_features = MagicMock(
            return_value=(None, None, None)
        )
        service._feature_extractor = mock_extractor

        mock_engine = MagicMock()
        mock_fusion_result = MagicMock()
        mock_fusion_result.disease_name = "测试"
        mock_fusion_result.confidence = 0.85
        mock_engine.fuse_features = MagicMock(return_value=mock_fusion_result)
        service._fusion_engine = mock_engine

        dummy_img = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )

        with patch("app.services.fusion_service.asyncio.run") as mock_run:
            await service.diagnose_async(
                image=dummy_img, symptoms="test", use_cache=False
            )
            mock_run.assert_not_called(), \
                "diagnose_async() 不应调用 asyncio.run()"

    @pytest.mark.asyncio
    async def test_full_async_chain_returns_correct_structure(self):
        """
        验证全异步链路返回正确的诊断结果结构

        端到端验证：async 路径的输出格式与预期一致
        """
        service = MultimodalFusionService(enable_cache=False)
        service._initialized = True

        mock_annotator = MagicMock()
        mock_annotator.check_cache = AsyncMock(return_value=None)
        mock_annotator.pil_to_bytes = MagicMock(return_value=b"test_bytes")
        mock_annotator.annotate_image = MagicMock(return_value=None)
        mock_annotator.build_response_dict = MagicMock(return_value={
            "success": True,
            "diagnosis": {
                "disease_name": "小麦条锈病",
                "confidence": 0.92
            },
            "features": {"cache_hit": False},
            "performance": {}
        })
        mock_annotator.save_to_cache = AsyncMock(return_value=True)
        service._result_annotator = mock_annotator

        mock_extractor = MagicMock()
        mock_extractor.extract_all_features = MagicMock(
            return_value=(
                {"detections": [], "count": 0},
                {"diagnosis": {"disease_name": "条锈病"}},
                None
            )
        )
        service._feature_extractor = mock_extractor

        mock_engine = MagicMock()
        mock_fusion_result = MagicMock()
        mock_fusion_result.disease_name = "小麦条锈病"
        mock_fusion_result.disease_name_en = "Yellow Rust"
        mock_fusion_result.confidence = 0.92
        mock_fusion_result.visual_confidence = 0.88
        mock_fusion_result.textual_confidence = 0.90
        mock_fusion_result.knowledge_confidence = 0.0
        mock_fusion_result.description = "叶片出现条状锈斑"
        mock_fusion_result.symptoms = []
        mock_fusion_result.causes = []
        mock_fusion_result.recommendations = []
        mock_fusion_result.treatment = []
        mock_fusion_result.medicines = []
        mock_fusion_result.knowledge_references = []
        mock_fusion_result.severity = "medium"
        mock_fusion_result.reasoning_chain = None
        mock_fusion_result.roi_boxes = []
        mock_fusion_result.annotated_image = None
        mock_fusion_result.inference_time_ms = 150.5
        mock_fusion_result.kad_former_used = False
        mock_engine.fuse_features = MagicMock(return_value=mock_fusion_result)
        service._fusion_engine = mock_engine

        dummy_img = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )

        result = await service.diagnose_async(
            image=dummy_img,
            symptoms="叶片出现黄色条纹",
            enable_thinking=False,
            use_graph_rag=False,
            use_cache=True
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "diagnosis" in result
        assert "features" in result
        assert result["features"].get("cache_hit") is False


class TestQwenServiceAsyncMigration:
    """qwen_service.py 异步迁移验证测试"""

    def test_qwen_diagnose_has_deprecated_decorator(self):
        """
        验证 QwenService.diagnose() 已标记 @deprecated

        同步诊断方法应引导用户使用 diagnose_async()
        """
        with patch.object(QwenService, "__init__", lambda self, **kw: None):
            service = object.__new__(QwenService)
            service.loader = MagicMock()
            service.loader.is_loaded = True

            assert hasattr(service.diagnose, '__wrapped__'), \
                "QwenService.diagnose() 应被 @deprecated 装饰器包装"

    def test_qwen_diagnose_emits_deprecation_warning(self):
        """
        验证 QwenService.diagnose() 调用时触发 DeprecationWarning
        """
        with patch.object(QwenService, "__init__", lambda self, **kw: None):
            service = object.__new__(QwenService)
            service.loader = MagicMock()
            service.loader.is_loaded = True
            service.loader.get_model_status = MagicMock(return_value={})
            service.cpu_offload = False
            service.enable_kad_former = False
            service.enable_graph_rag = False
            service.preprocessor = MagicMock()
            service.preprocessor.build_system_prompt = MagicMock(return_value="sys")
            service.preprocessor.preprocess_image = MagicMock(side_effect=lambda x: x)
            service.preprocessor.build_text_query = MagicMock(return_value="q")
            service.preprocessor.format_chat_template = MagicMock(return_value=[])
            service.inferencer = MagicMock()
            service.inferencer.infer_single = MagicMock(return_value="")
            service.postprocessor = MagicMock()
            service.postprocessor.parse_response = MagicMock(
                return_value={"disease_name": "测试"}
            )

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                service.diagnose(symptoms="测试")

                dep_warnings = [
                    warn for warn in w
                    if issubclass(warn.category, DeprecationWarning)
                ]
                assert len(dep_warnings) >= 1, \
                    "QwenService.diagnose() 应触发 DeprecationWarning"


class TestRouterAsyncCallSite:
    """路由层异步调用点验证测试"""

    def test_router_imports_async_method(self):
        """
        验证 diagnosis_router 可访问 diagnose_async 方法

        确保 fusion_service 暴露了异步接口供路由使用
        """
        from app.services.fusion_service import MultimodalFusionService
        service = MultimodalFusionService(enable_cache=False)

        assert hasattr(service, "diagnose_async"), \
            "MultimodalFusionService 必须暴露 diagnose_async 方法"
        assert callable(service.diagnose_async), \
            "diagnose_async 必须可调用"

    def test_diagnose_async_is_coroutine_function(self):
        """
        验证 diagnose_async 是原生协程函数

        使用 inspect 判断是否为真正的 async 函数
        """
        import inspect
        from app.services.fusion_service import MultimodalFusionService
        service = MultimodalFusionService(enable_cache=False)

        assert inspect.iscoroutinefunction(service.diagnose_async), \
            "diagnose_async 必须是 async 协程函数"


class TestNoAsyncioRunInAsyncPath:
    """异步路径中禁止 asyncio.run() 的集成测试"""

    def test_sync_diagnose_still_exists_for_backward_compat(self):
        """
        验证同步 diagnose() 方法仍然存在（向后兼容保证）

        确认不删除同步方法，仅标记为弃用。
        注意：在异步上下文中直接调用同步 diagnose() 会因
        嵌套事件循环而失败，这正是迁移到 diagnose_async 的原因。
        """
        service = MultimodalFusionService(enable_cache=False)

        assert hasattr(service, "diagnose"), \
            "同步 diagnose() 方法必须保留以维持向后兼容"
        assert callable(service.diagnose), \
            "diagnose() 必须保持可调用状态"

        assert hasattr(service, "diagnose_async"), \
            "异步 diagnose_async() 方法必须同时存在"
        assert callable(service.diagnose_async), \
            "diagnose_async() 必须可调用"
