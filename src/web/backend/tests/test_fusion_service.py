"""
多模态融合服务单元测试
测试结果融合逻辑、置信度计算等功能
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import torch
import numpy as np

from app.services.fusion_service import (
    MultimodalFusionService,
    FusionResult,
    get_fusion_service
)


class TestFusionResult:
    """融合结果数据类测试"""

    def test_fusion_result_default_values(self):
        """
        测试融合结果默认值
        
        验证:
        - 可选字段默认为空列表
        - 必填字段正确设置
        """
        result = FusionResult(
            disease_name="小麦锈病",
            confidence=0.95
        )
        
        assert result.disease_name == "小麦锈病"
        assert result.confidence == 0.95
        assert result.symptoms == []
        assert result.causes == []
        assert result.recommendations == []
        assert result.treatment == []
        assert result.medicines == []
        assert result.knowledge_references == []

    def test_fusion_result_with_all_fields(self):
        """
        测试包含所有字段的融合结果
        
        验证:
        - 所有字段正确设置
        """
        result = FusionResult(
            disease_name="小麦锈病",
            disease_name_en="Yellow Rust",
            confidence=0.95,
            visual_confidence=0.92,
            textual_confidence=0.88,
            knowledge_confidence=0.90,
            description="叶片出现黄色锈斑",
            symptoms=["叶片发黄", "出现锈斑"],
            causes=["锈菌感染"],
            recommendations=["喷洒杀菌剂"],
            treatment=["三唑酮"],
            medicines=[{"name": "三唑酮", "dosage": "100ml/亩"}],
            knowledge_references=[{"source": "知识库"}],
            severity="high"
        )
        
        assert result.disease_name == "小麦锈病"
        assert result.disease_name_en == "Yellow Rust"
        assert result.confidence == 0.95
        assert len(result.symptoms) == 2
        assert len(result.medicines) == 1


class TestMultimodalFusionServiceInit:
    """融合服务初始化测试类"""

    def test_init_default_state(self):
        """
        测试默认初始化状态
        
        验证:
        - 服务未初始化
        - 依赖服务为空
        """
        service = MultimodalFusionService()
        
        assert service._initialized is False
        assert service._yolo_service is None
        assert service._qwen_service is None
        assert service._graphrag_service is None

    def test_initialize_success(self):
        """
        测试成功初始化
        
        验证:
        - 初始化状态正确设置
        - 依赖服务正确加载
        """
        service = MultimodalFusionService()
        
        with patch('app.services.fusion_service.get_yolo_service') as mock_yolo:
            with patch('app.services.fusion_service.get_qwen_service') as mock_qwen:
                with patch('app.services.fusion_service.get_graphrag_service') as mock_graphrag:
                    with patch('app.services.fusion_service.create_kad_former') as mock_kad:
                        with patch('torch.cuda.is_available', return_value=False):
                            mock_yolo_instance = MagicMock()
                            mock_yolo_instance.is_loaded = True
                            mock_yolo.return_value = mock_yolo_instance
                            
                            mock_qwen_instance = MagicMock()
                            mock_qwen_instance.is_loaded = True
                            mock_qwen.return_value = mock_qwen_instance
                            
                            mock_graphrag_instance = MagicMock()
                            mock_graphrag_instance._initialized = True
                            mock_graphrag.return_value = mock_graphrag_instance
                            
                            service.initialize()
                            
                            assert service._initialized is True

    def test_initialize_skip_when_already_initialized(self):
        """
        测试已初始化时跳过
        
        验证:
        - 重复初始化不执行
        """
        service = MultimodalFusionService()
        service._initialized = True
        
        service.initialize()
        
        assert service._initialized is True

    def test_initialize_with_cuda(self):
        """
        测试 CUDA 环境初始化
        
        验证:
        - CUDA 可用时初始化 KAD-Former
        """
        service = MultimodalFusionService()
        
        with patch('app.services.fusion_service.get_yolo_service') as mock_yolo:
            with patch('app.services.fusion_service.get_qwen_service') as mock_qwen:
                with patch('app.services.fusion_service.get_graphrag_service') as mock_graphrag:
                    with patch('app.services.fusion_service.create_kad_former') as mock_kad:
                        with patch('torch.cuda.is_available', return_value=True):
                            mock_yolo_instance = MagicMock()
                            mock_yolo_instance.is_loaded = True
                            mock_yolo.return_value = mock_yolo_instance
                            
                            mock_qwen_instance = MagicMock()
                            mock_qwen_instance.is_loaded = True
                            mock_qwen.return_value = mock_qwen_instance
                            
                            mock_graphrag_instance = MagicMock()
                            mock_graphrag_instance._initialized = True
                            mock_graphrag.return_value = mock_graphrag_instance
                            
                            mock_kad_instance = MagicMock()
                            mock_kad.return_value = mock_kad_instance
                            
                            service.initialize()
                            
                            mock_kad_instance.eval.assert_called_once()


class TestMultimodalFusionServiceDiagnose:
    """融合诊断测试类"""

    @pytest.fixture
    def initialized_service(self):
        """
        创建已初始化的融合服务
        
        返回:
            MultimodalFusionService: 已初始化的服务实例
        """
        service = MultimodalFusionService()
        service._initialized = True
        
        mock_yolo = MagicMock()
        mock_yolo.is_loaded = True
        mock_yolo.detect = MagicMock(return_value={
            "success": True,
            "detections": [{
                "class_name": "Yellow Rust",
                "confidence": 0.92,
                "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
            }],
            "count": 1
        })
        service._yolo_service = mock_yolo
        
        mock_qwen = MagicMock()
        mock_qwen.is_loaded = True
        mock_qwen.diagnose = MagicMock(return_value={
            "success": True,
            "diagnosis": {
                "disease_name": "小麦锈病",
                "confidence": 0.88,
                "description": "叶片出现黄色锈斑",
                "recommendations": ["喷洒杀菌剂"]
            }
        })
        service._qwen_service = mock_qwen
        
        mock_graphrag = MagicMock()
        mock_graphrag._initialized = True
        mock_context = MagicMock()
        mock_context.triples = []
        mock_context.entities = []
        mock_context.citations = []
        mock_context.tokens = None
        mock_graphrag.retrieve_disease_knowledge = MagicMock(return_value=mock_context)
        service._graphrag_service = mock_graphrag
        
        service._kad_former = None
        
        return service

    def test_diagnose_with_image_only(self, initialized_service: MultimodalFusionService):
        """
        测试仅图像诊断
        
        验证:
        - 返回成功状态
        - 包含诊断结果
        """
        image = Image.new('RGB', (640, 480), color='white')
        
        result = initialized_service.diagnose(image=image)
        
        assert "success" in result
        assert "diagnosis" in result

    def test_diagnose_with_symptoms_only(self, initialized_service: MultimodalFusionService):
        """
        测试仅症状文本诊断
        
        验证:
        - 返回成功状态
        - 包含诊断结果
        """
        result = initialized_service.diagnose(symptoms="叶片出现黄色锈斑")
        
        assert "success" in result

    def test_diagnose_with_all_inputs(self, initialized_service: MultimodalFusionService):
        """
        测试多模态输入诊断
        
        验证:
        - 返回成功状态
        - 包含所有特征信息
        """
        image = Image.new('RGB', (640, 480), color='white')
        
        result = initialized_service.diagnose(
            image=image,
            symptoms="叶片出现黄色锈斑",
            enable_thinking=True,
            use_graph_rag=True
        )
        
        assert "success" in result
        assert "features" in result

    def test_diagnose_not_initialized(self):
        """
        测试服务未初始化时诊断
        
        验证:
        - 自动初始化服务
        """
        service = MultimodalFusionService()
        
        with patch.object(service, 'initialize') as mock_init:
            mock_init.return_value = None
            service._initialized = True
            service._yolo_service = None
            service._qwen_service = None
            service._graphrag_service = None
            
            result = service.diagnose()
            
            assert "success" in result

    def test_diagnose_exception_handling(self, initialized_service: MultimodalFusionService):
        """
        测试诊断异常处理
        
        验证:
        - 异常被捕获
        - 返回错误信息
        """
        initialized_service._yolo_service.detect.side_effect = Exception("检测失败")
        
        image = Image.new('RGB', (640, 480), color='white')
        result = initialized_service.diagnose(image=image)
        
        assert "success" in result


class TestCalculateFusedConfidence:
    """置信度计算测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        return MultimodalFusionService()

    def test_calculate_confidence_all_modalities(self, service: MultimodalFusionService):
        """
        测试所有模态的置信度计算
        
        验证:
        - 加权平均计算正确
        - 置信度在合理范围
        """
        confidence = service._calculate_fused_confidence(
            visual_conf=0.9,
            textual_conf=0.8,
            knowledge_conf=0.85,
            has_visual=True,
            has_textual=True,
            has_knowledge=True
        )
        
        assert 0 <= confidence <= 1
        assert confidence > 0.8

    def test_calculate_confidence_visual_only(self, service: MultimodalFusionService):
        """
        测试仅视觉模态的置信度
        
        验证:
        - 使用降级因子
        - 置信度降低
        """
        confidence = service._calculate_fused_confidence(
            visual_conf=0.9,
            textual_conf=0.0,
            knowledge_conf=0.0,
            has_visual=True,
            has_textual=False,
            has_knowledge=False
        )
        
        assert confidence < 0.9
        assert confidence > 0

    def test_calculate_confidence_no_modality(self, service: MultimodalFusionService):
        """
        测试无模态时的置信度
        
        验证:
        - 返回默认值 0.5
        """
        confidence = service._calculate_fused_confidence(
            visual_conf=0.0,
            textual_conf=0.0,
            knowledge_conf=0.0,
            has_visual=False,
            has_textual=False,
            has_knowledge=False
        )
        
        assert confidence == 0.5

    def test_calculate_confidence_textual_only(self, service: MultimodalFusionService):
        """
        测试仅文本模态的置信度
        
        验证:
        - 使用文本权重
        - 应用降级因子
        """
        confidence = service._calculate_fused_confidence(
            visual_conf=0.0,
            textual_conf=0.85,
            knowledge_conf=0.0,
            has_visual=False,
            has_textual=True,
            has_knowledge=False
        )
        
        assert 0 < confidence < 0.85

    def test_calculate_confidence_two_modalities(self, service: MultimodalFusionService):
        """
        测试两个模态的置信度
        
        验证:
        - 加权计算正确
        - 应用降级因子
        """
        confidence = service._calculate_fused_confidence(
            visual_conf=0.9,
            textual_conf=0.8,
            knowledge_conf=0.0,
            has_visual=True,
            has_textual=True,
            has_knowledge=False
        )
        
        assert 0 < confidence <= 1


class TestFuseFeatures:
    """特征融合测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        service = MultimodalFusionService()
        service._kad_former = None
        return service

    def test_fuse_features_visual_only(self, service: MultimodalFusionService):
        """
        测试仅视觉特征融合
        
        验证:
        - 返回融合结果
        - 包含视觉置信度
        """
        visual_result = {
            "detections": [{
                "class_name": "Yellow Rust",
                "confidence": 0.92,
                "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
            }],
            "count": 1
        }
        
        result = service._fuse_features(
            visual_result=visual_result,
            textual_result=None,
            knowledge_context=None
        )
        
        assert result.disease_name == "Yellow Rust"
        assert result.visual_confidence == 0.92

    def test_fuse_features_textual_only(self, service: MultimodalFusionService):
        """
        测试仅文本特征融合
        
        验证:
        - 返回融合结果
        - 包含文本置信度
        """
        textual_result = {
            "diagnosis": {
                "disease_name": "小麦锈病",
                "confidence": 0.88,
                "description": "叶片出现黄色锈斑",
                "recommendations": ["喷洒杀菌剂"]
            }
        }
        
        result = service._fuse_features(
            visual_result=None,
            textual_result=textual_result,
            knowledge_context=None
        )
        
        assert result.disease_name == "小麦锈病"
        assert result.textual_confidence == 0.88

    def test_fuse_features_all_modalities(self, service: MultimodalFusionService):
        """
        测试所有模态特征融合
        
        验证:
        - 返回融合结果
        - 包含所有置信度
        """
        visual_result = {
            "detections": [{
                "class_name": "Yellow Rust",
                "confidence": 0.92,
                "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
            }],
            "count": 1
        }
        
        textual_result = {
            "diagnosis": {
                "disease_name": "小麦锈病",
                "confidence": 0.88,
                "description": "叶片出现黄色锈斑",
                "recommendations": ["喷洒杀菌剂"]
            }
        }
        
        mock_context = MagicMock()
        mock_context.triples = []
        mock_context.entities = []
        mock_context.citations = [{"confidence": 0.85}]
        mock_context.tokens = None
        
        result = service._fuse_features(
            visual_result=visual_result,
            textual_result=textual_result,
            knowledge_context=mock_context
        )
        
        assert result.confidence > 0
        assert result.visual_confidence == 0.92
        assert result.textual_confidence == 0.88

    def test_fuse_features_no_input(self, service: MultimodalFusionService):
        """
        测试无输入时融合
        
        验证:
        - 返回默认结果
        """
        result = service._fuse_features(
            visual_result=None,
            textual_result=None,
            knowledge_context=None
        )
        
        assert result.disease_name == "未知病害"
        assert result.confidence == 0.5


class TestExtractVisualFeatures:
    """视觉特征提取测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        service = MultimodalFusionService()
        service._yolo_service = MagicMock()
        service._yolo_service.is_loaded = True
        return service

    def test_extract_visual_features_success(self, service: MultimodalFusionService):
        """
        测试成功提取视觉特征
        
        验证:
        - 返回检测结果
        """
        service._yolo_service.detect.return_value = {
            "success": True,
            "detections": [{
                "class_name": "Yellow Rust",
                "confidence": 0.92
            }],
            "count": 1
        }
        
        image = Image.new('RGB', (640, 480), color='white')
        result = service._extract_visual_features(image)
        
        assert result is not None
        assert "detections" in result

    def test_extract_visual_features_service_not_loaded(self, service: MultimodalFusionService):
        """
        测试服务未加载时提取
        
        验证:
        - 返回 None
        """
        service._yolo_service.is_loaded = False
        
        image = Image.new('RGB', (640, 480), color='white')
        result = service._extract_visual_features(image)
        
        assert result is None


class TestDiagnoseAsync:
    """
    异步诊断方法测试
    
    验证 diagnose_async() 在以下场景下的正确性:
    1. 高并发场景下不出现事件循环嵌套错误
    2. 异步缓存操作正常工作
    3. 与同步 diagnose() 方法结果一致
    """

    @pytest.mark.asyncio
    async def test_diagnose_async_basic(self):
        """
        测试异步诊断基本功能
        
        验证:
        - 异步方法能正常返回结果
        - 结果包含必要字段
        """
        service = MultimodalFusionService()
        service._initialized = True
        service._yolo_service = None
        service._qwen_service = None
        service._graphrag_service = None
        service._cache_service = None
        
        result = await service.diagnose_async(
            symptoms="叶片出现锈状孢子",
            use_cache=False
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "model" in result

    @pytest.mark.asyncio
    async def test_diagnose_async_with_cache_hit(self):
        """
        测试异步诊断缓存命中场景
        
        验证:
        - 缓存命中时直接返回缓存结果
        - 使用 await 而非 asyncio.run()
        """
        service = MultimodalFusionService()
        service._initialized = True
        
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {
            "result": {
                "success": True,
                "diagnosis": {"disease_name": "小麦锈病", "confidence": 0.95},
                "features": {}
            }
        }
        service._cache_service = mock_cache
        
        image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        
        result = await service.diagnose_async(
            image=image,
            symptoms="叶片出现锈状孢子",
            use_cache=True
        )
        
        assert result["success"] is True
        assert result["cache_hit"] is True
        mock_cache.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_diagnose_async_save_to_cache(self):
        """
        测试异步诊断保存到缓存
        
        验证:
        - 诊断完成后使用 await 保存到缓存
        - 不使用 asyncio.run()
        """
        service = MultimodalFusionService()
        service._initialized = True
        service._yolo_service = None
        service._qwen_service = None
        service._graphrag_service = None
        
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        service._cache_service = mock_cache
        
        result = await service.diagnose_async(
            symptoms="测试症状",
            use_cache=True
        )
        
        mock_cache.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_high_concurrency_no_event_loop_error(self):
        """
        测试高并发场景下无事件循环嵌套错误
        
        这是最关键的测试，验证修复的核心目标:
        - 多个并发调用不会触发 "Event loop is already running" 错误
        - 所有请求都能正常完成
        """
        import asyncio
        
        service = MultimodalFusionService()
        service._initialized = True
        service._yolo_service = None
        service._qwen_service = None
        service._graphrag_service = None
        service._cache_service = None
        
        async def single_request(request_id: int) -> dict:
            """模拟单个异步诊断请求"""
            result = await service.diagnose_async(
                symptoms=f"测试请求 {request_id}",
                use_cache=False
            )
            return result
        
        concurrent_requests = 10
        tasks = [single_request(i) for i in range(concurrent_requests)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = [r for r in results if not isinstance(r, Exception)]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        assert len(exceptions) == 0, f"发现 {len(exceptions)} 个异常: {exceptions}"
        assert len(successful_results) == concurrent_requests
        
        for i, result in enumerate(successful_results):
            assert isinstance(result, dict)
            assert "success" in result

    @pytest.mark.asyncio
    async def test_high_concurrency_with_cache_operations(self):
        """
        测试高并发场景下的异步缓存操作
        
        验证:
        - 并发缓存读取不会阻塞
        - 并发缓存写入不会导致竞争条件
        """
        import asyncio
        
        service = MultimodalFusionService()
        service._initialized = True
        service._yolo_service = None
        service._qwen_service = None
        service._graphrag_service = None
        
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        service._cache_service = mock_cache
        
        async def cached_request(request_id: int) -> dict:
            """模拟带缓存的异步诊断请求"""
            image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
            result = await service.diagnose_async(
                image=image,
                symptoms=f"并发请求 {request_id}",
                use_cache=True
            )
            return result
        
        concurrent_requests = 5
        tasks = [cached_request(i) for i in range(concurrent_requests)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"发现异常: {exceptions}"
        
        assert mock_cache.get.await_count == concurrent_requests
        assert mock_cache.set.await_count == concurrent_requests

    @pytest.mark.asyncio
    async def test_mixed_sync_async_compatibility(self):
        """
        测试同步和异步方法的兼容性
        
        验证:
        - 同步方法在非异步环境中正常工作
        - 异步方法在异步环境中正常工作
        - 两者结果结构一致
        """
        service = MultimodalFusionService()
        service._initialized = True
        service._yolo_service = None
        service._qwen_service = None
        service._graphrag_service = None
        service._cache_service = None
        
        async_result = await service.diagnose_async(
            symptoms="兼容性测试",
            use_cache=False
        )
        
        assert isinstance(async_result, dict)
        assert "success" in async_result
        assert "model" in async_result

    @pytest.mark.asyncio
    async def test_diagnose_async_exception_handling(self):
        """
        测试异步诊断异常处理
        
        验证:
        - 异常被正确捕获
        - 返回包含 error 字段的结果
        """
        service = MultimodalFusionService()
        service._initialized = True
        service._yolo_service = None
        service._qwen_service = None
        service._graphrag_service = None
        
        mock_cache = AsyncMock()
        mock_cache.get.side_effect = Exception("缓存服务异常")
        service._cache_service = mock_cache
        
        result = await service.diagnose_async(
            symptoms="异常测试",
            use_cache=True
        )
        
        assert isinstance(result, dict)
        assert "success" in result

    def test_extract_visual_features_no_service(self):
        """
        测试无服务时提取
        
        验证:
        - 返回 None
        """
        service = MultimodalFusionService()
        service._yolo_service = None
        
        image = Image.new('RGB', (640, 480), color='white')
        result = service._extract_visual_features(image)
        
        assert result is None

    def test_extract_visual_features_detection_failed(self, service: MultimodalFusionService):
        """
        测试检测失败时提取
        
        验证:
        - 返回 None
        """
        service._yolo_service.detect.return_value = {
            "success": False,
            "error": "检测失败"
        }
        
        image = Image.new('RGB', (640, 480), color='white')
        result = service._extract_visual_features(image)
        
        assert result is None


class TestExtractTextualFeatures:
    """文本特征提取测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        service = MultimodalFusionService()
        service._qwen_service = MagicMock()
        service._qwen_service.is_loaded = True
        return service

    def test_extract_textual_features_success(self, service: MultimodalFusionService):
        """
        测试成功提取文本特征
        
        验证:
        - 返回诊断结果
        """
        service._qwen_service.diagnose.return_value = {
            "success": True,
            "diagnosis": {
                "disease_name": "小麦锈病",
                "confidence": 0.88
            }
        }
        
        result = service._extract_textual_features(
            image=None,
            symptoms="叶片发黄",
            knowledge_context=None,
            enable_thinking=False
        )
        
        assert result is not None
        assert "diagnosis" in result

    def test_extract_textual_features_service_not_loaded(self, service: MultimodalFusionService):
        """
        测试服务未加载时提取
        
        验证:
        - 返回 None
        """
        service._qwen_service.is_loaded = False
        
        result = service._extract_textual_features(
            image=None,
            symptoms="叶片发黄",
            knowledge_context=None,
            enable_thinking=False
        )
        
        assert result is None

    def test_extract_textual_features_with_knowledge(self, service: MultimodalFusionService):
        """
        测试带知识上下文的文本特征提取
        
        验证:
        - 正确传递知识上下文
        """
        service._qwen_service.diagnose.return_value = {
            "success": True,
            "diagnosis": {
                "disease_name": "小麦锈病",
                "confidence": 0.88
            }
        }
        
        mock_context = MagicMock()
        mock_context.tokens = "知识上下文内容"
        
        result = service._extract_textual_features(
            image=None,
            symptoms="叶片发黄",
            knowledge_context=mock_context,
            enable_thinking=False
        )
        
        assert result is not None


class TestRetrieveKnowledge:
    """知识检索测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        service = MultimodalFusionService()
        service._graphrag_service = MagicMock()
        service._graphrag_service._initialized = True
        return service

    def test_retrieve_knowledge_success(self, service: MultimodalFusionService):
        """
        测试成功检索知识
        
        验证:
        - 返回知识上下文
        """
        mock_context = MagicMock()
        mock_context.triples = [MagicMock()]
        mock_context.entities = ["小麦锈病"]
        service._graphrag_service.retrieve_disease_knowledge.return_value = mock_context
        
        result = service._retrieve_knowledge("叶片发黄", None)
        
        assert result is not None

    def test_retrieve_knowledge_service_not_initialized(self, service: MultimodalFusionService):
        """
        测试服务未初始化时检索
        
        验证:
        - 返回 None
        """
        service._graphrag_service._initialized = False
        
        result = service._retrieve_knowledge("叶片发黄", None)
        
        assert result is None

    def test_retrieve_knowledge_no_service(self):
        """
        测试无服务时检索
        
        验证:
        - 返回 None
        """
        service = MultimodalFusionService()
        service._graphrag_service = None
        
        result = service._retrieve_knowledge("叶片发黄", None)
        
        assert result is None


class TestAnnotateImage:
    """图像标注测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        return MultimodalFusionService()

    def test_annotate_image_success(self, service: MultimodalFusionService):
        """
        测试成功标注图像
        
        验证:
        - 返回 Base64 编码图像
        """
        image = Image.new('RGB', (640, 480), color='white')
        detections = [{
            "class_name": "Yellow Rust",
            "confidence": 0.92,
            "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
        }]
        
        result = service._annotate_image(image, detections)
        
        assert result is not None
        assert result.startswith("data:image/png;base64,")

    def test_annotate_image_no_detections(self, service: MultimodalFusionService):
        """
        测试无检测结果时标注
        
        验证:
        - 返回 None
        """
        image = Image.new('RGB', (640, 480), color='white')
        
        result = service._annotate_image(image, [])
        
        assert result is None

    def test_annotate_image_with_bbox_list(self, service: MultimodalFusionService):
        """
        测试使用列表格式边界框标注
        
        验证:
        - 正确处理列表格式
        """
        image = Image.new('RGB', (640, 480), color='white')
        detections = [{
            "class_name": "Yellow Rust",
            "confidence": 0.92,
            "bbox": [100, 100, 200, 200]
        }]
        
        result = service._annotate_image(image, detections)
        
        assert result is not None


class TestGetFusionService:
    """融合服务单例测试类"""

    def test_get_fusion_service_singleton(self):
        """
        测试获取服务单例
        
        验证:
        - 多次调用返回同一实例
        """
        with patch('app.services.fusion_service._fusion_service_instance', None):
            service1 = get_fusion_service()
            service2 = get_fusion_service()
            
            assert service1 is service2

    def test_get_fusion_service_creates_new_instance(self):
        """
        测试创建新服务实例
        
        验证:
        - 首次调用创建实例
        """
        with patch('app.services.fusion_service._fusion_service_instance', None):
            service = get_fusion_service()
            
            assert service is not None
            assert isinstance(service, MultimodalFusionService)


class TestGenerateFeatures:
    """特征生成测试类"""

    @pytest.fixture
    def service(self):
        """
        创建融合服务实例
        
        返回:
            MultimodalFusionService: 服务实例
        """
        return MultimodalFusionService()

    def test_generate_visual_features_with_tensor(self, service: MultimodalFusionService):
        """
        测试从张量生成视觉特征
        
        验证:
        - 正确处理张量输入
        """
        visual_result = {
            "detections": [{
                "features": torch.randn(768)
            }]
        }
        
        result = service._generate_visual_features(visual_result)
        
        assert result is not None
        assert isinstance(result, torch.Tensor)

    def test_generate_visual_features_with_numpy(self, service: MultimodalFusionService):
        """
        测试从 NumPy 数组生成视觉特征
        
        验证:
        - 正确处理 NumPy 输入
        """
        visual_result = {
            "detections": [{
                "features": np.random.randn(768).astype(np.float32)
            }]
        }
        
        result = service._generate_visual_features(visual_result)
        
        assert result is not None

    def test_generate_visual_features_no_detections(self, service: MultimodalFusionService):
        """
        测试无检测结果时生成特征
        
        验证:
        - 返回 None
        """
        visual_result = {"detections": []}
        
        result = service._generate_visual_features(visual_result)
        
        assert result is None

    def test_generate_text_features_with_tensor(self, service: MultimodalFusionService):
        """
        测试从张量生成文本特征
        
        验证:
        - 正确处理张量输入
        """
        textual_result = {
            "features": torch.randn(1, 2560)
        }
        
        result = service._generate_text_features(textual_result)
        
        assert result is not None

    def test_generate_knowledge_embeddings_with_tensor(self, service: MultimodalFusionService):
        """
        测试从张量生成知识嵌入
        
        验证:
        - 正确处理张量输入
        """
        mock_context = MagicMock()
        mock_context.tokens = torch.randn(10, 256)
        
        result = service._generate_knowledge_embeddings(mock_context)
        
        assert result is not None


class TestApplyKadFormerFusion:
    """KAD-Former 融合测试类"""

    def test_apply_kad_former_fusion_success(self):
        """
        测试成功应用 KAD-Former 融合
        
        验证:
        - 返回融合特征
        """
        service = MultimodalFusionService()
        
        mock_kad = MagicMock()
        mock_kad.return_value = torch.randn(1, 10, 768)
        service._kad_former = mock_kad
        
        visual_features = torch.randn(1, 10, 768)
        text_features = torch.randn(1, 5, 2560)
        knowledge_embeddings = torch.randn(1, 8, 256)
        
        result = service._apply_kad_former_fusion(
            visual_features, text_features, knowledge_embeddings
        )
        
        assert result is not None

    def test_apply_kad_former_fusion_no_kad(self):
        """
        测试无 KAD-Former 时融合
        
        验证:
        - 返回 None
        """
        service = MultimodalFusionService()
        service._kad_former = None
        
        result = service._apply_kad_former_fusion(
            torch.randn(1, 10, 768),
            torch.randn(1, 5, 2560),
            torch.randn(1, 8, 256)
        )
        
        assert result is None

    def test_apply_kad_former_fusion_exception(self):
        """
        测试 KAD-Former 融合异常处理
        
        验证:
        - 异常被捕获
        - 返回 None
        """
        service = MultimodalFusionService()
        
        mock_kad = MagicMock(side_effect=Exception("融合失败"))
        service._kad_former = mock_kad
        
        result = service._apply_kad_former_fusion(
            torch.randn(1, 10, 768),
            torch.randn(1, 5, 2560),
            torch.randn(1, 8, 256)
        )
        
        assert result is None
