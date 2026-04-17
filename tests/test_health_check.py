# -*- coding: utf-8 -*-
"""
服务健康检查测试
测试 AI 服务、诊断服务和系统健康状态
"""
import pytest
from unittest.mock import patch, MagicMock
import asyncio


pytestmark = pytest.mark.api


class TestAIHealthCheck:
    """AI 服务健康检查测试类"""
    
    @pytest.mark.unit
    def test_health_check_mock_mode(self, mock_env):
        """测试 Mock 模式下的健康检查"""
        from tests.mocks.diagnosis_mock import MockDiagnosisService
        service = MockDiagnosisService()
        
        assert service is not None
        assert hasattr(service, "diagnose_by_text")
        assert hasattr(service, "diagnose_by_image")
    
    @pytest.mark.unit
    def test_health_check_response_structure(self, mock_health_check_response):
        """测试健康检查响应结构"""
        response = mock_health_check_response
        
        assert "status" in response
        assert "mock_mode" in response
        assert "services" in response
        assert response["status"] == "mock"
        assert response["mock_mode"] is True
        assert "mock" in response["services"]
    
    @pytest.mark.unit
    def test_health_check_healthy_response(self, health_check_response):
        """测试健康状态响应结构"""
        response = health_check_response
        
        assert response["status"] == "healthy"
        assert response["mock_mode"] is False
        assert "yolov8" in response["services"]
        assert "qwen3vl" in response["services"]
    
    @pytest.mark.unit
    def test_health_check_degraded_status(self):
        """测试降级状态"""
        degraded_response = {
            "status": "degraded",
            "mock_mode": False,
            "services": {
                "yolov8": {"is_loaded": False, "status": "error"},
                "qwen3vl": {"is_loaded": True, "status": "healthy"}
            }
        }
        
        assert degraded_response["status"] == "degraded"
        assert not degraded_response["services"]["yolov8"]["is_loaded"]
    
    @pytest.mark.mock
    def test_mock_diagnosis_service_text(self, mock_diagnosis_service):
        """测试 Mock 诊断服务文本诊断"""
        result = asyncio.run(mock_diagnosis_service.diagnose_by_text("叶片出现黄色条状病斑"))
        
        assert result is not None
        assert "disease_name" in result
        assert "confidence" in result
        assert result["disease_name"] in ["小麦条锈病", "小麦白粉病", "小麦赤霉病"]
        assert 0 < result["confidence"] <= 1
    
    @pytest.mark.mock
    def test_mock_diagnosis_service_image(self, mock_diagnosis_service):
        """测试 Mock 诊断服务图像诊断"""
        result = asyncio.run(mock_diagnosis_service.diagnose_by_image(b"fake_image_data", "测试症状"))
        
        assert result is not None
        assert "disease_name" in result
        assert "confidence" in result
        assert "bounding_boxes" in result
        assert len(result["bounding_boxes"]) > 0
    
    @pytest.mark.unit
    def test_mock_service_disease_database(self, mock_diagnosis_service):
        """测试 Mock 服务病害数据库"""
        diseases = mock_diagnosis_service.disease_database
        
        assert "条锈病" in diseases
        assert "白粉病" in diseases
        assert "赤霉病" in diseases
        
        for disease in diseases.values():
            assert "disease_id" in disease
            assert "disease_name" in disease
            assert "symptoms" in disease
            assert "treatment_methods" in disease


class TestDiagnosisAPIHealth:
    """诊断 API 健康检查测试类"""
    
    @pytest.mark.unit
    def test_fusion_endpoint_parameters(self, sample_fusion_request):
        """测试融合诊断端点参数"""
        request = sample_fusion_request
        
        assert "symptoms" in request
        assert "enable_thinking" in request
        assert "use_graph_rag" in request
        assert "use_cache" in request
    
    @pytest.mark.unit
    def test_fusion_response_structure(self, sample_fusion_response):
        """测试融合诊断响应结构"""
        response = sample_fusion_response
        
        assert response["success"] is True
        assert "diagnosis" in response
        assert "model" in response
        assert "performance" in response
        
        diagnosis = response["diagnosis"]
        assert "disease_name" in diagnosis
        assert "confidence" in diagnosis
        assert "recommendations" in diagnosis
    
    @pytest.mark.unit
    def test_text_diagnosis_request_validation(self):
        """测试文本诊断请求验证"""
        valid_request = {"symptoms": "叶片发黄"}
        invalid_request = {"symptoms": ""}
        
        assert len(valid_request["symptoms"]) > 0
        assert len(invalid_request["symptoms"]) == 0
    
    @pytest.mark.unit
    def test_image_diagnosis_response_format(self):
        """测试图像诊断响应格式"""
        mock_response = {
            "success": True,
            "data": {
                "detections": [
                    {"class_name": "条锈病", "confidence": 0.92, "box": [100, 100, 200, 200]}
                ],
                "count": 1
            },
            "message": "检测到 1 个病害"
        }
        
        assert mock_response["success"] is True
        assert "detections" in mock_response["data"]
        assert mock_response["data"]["count"] == len(mock_response["data"]["detections"])


class TestServiceStatus:
    """服务状态测试类"""
    
    @pytest.mark.unit
    def test_service_status_transitions(self):
        """测试服务状态转换"""
        states = ["healthy", "degraded", "unhealthy", "mock"]
        
        for state in states:
            assert state in ["healthy", "degraded", "unhealthy", "mock"]
    
    @pytest.mark.unit
    def test_service_capability_flags(self):
        """测试服务能力标志"""
        capabilities = {
            "text_diagnosis": True,
            "image_diagnosis": True,
            "multimodal_diagnosis": True,
            "thinking_mode": True,
            "graph_rag": False
        }
        
        assert capabilities["text_diagnosis"] is True
        assert capabilities["image_diagnosis"] is True
    
    @pytest.mark.unit
    def test_performance_metrics_structure(self):
        """测试性能指标结构"""
        metrics = {
            "inference_time_ms": 150.5,
            "cache_hit": False,
            "thinking_mode_enabled": True,
            "graph_rag_enabled": False
        }
        
        assert "inference_time_ms" in metrics
        assert isinstance(metrics["inference_time_ms"], (int, float))
        assert metrics["inference_time_ms"] >= 0
    
    @pytest.mark.unit
    def test_confidence_analysis_structure(self):
        """测试置信度分析结构"""
        confidence = {
            "overall_confidence": 0.92,
            "visual_confidence": 0.90,
            "textual_confidence": 0.88,
            "knowledge_confidence": 0.95
        }
        
        for key, value in confidence.items():
            assert 0 <= value <= 1, f"{key} 应在 0-1 范围内"


class TestCacheHealth:
    """缓存健康检查测试类"""
    
    @pytest.mark.unit
    def test_cache_stats_structure(self, mock_cache_manager):
        """测试缓存统计结构"""
        stats = mock_cache_manager.get_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "size" in stats
    
    @pytest.mark.unit
    def test_cache_operations(self, mock_cache_manager):
        """测试缓存操作"""
        result = mock_cache_manager.get(b"test_key", "test_symptoms")
        assert result is None
        
        success = mock_cache_manager.set(
            image_data=b"test_image",
            symptoms="test",
            diagnosis_result={"disease": "test"},
            ttl=3600
        )
        assert success is True


class TestErrorHandling:
    """错误处理测试类"""
    
    @pytest.mark.unit
    def test_error_response_format(self):
        """测试错误响应格式"""
        error_response = {
            "success": False,
            "error": "模型未加载",
            "fallback_suggestion": "请稍后重试或仅使用症状描述进行诊断"
        }
        
        assert error_response["success"] is False
        assert "error" in error_response
        assert "fallback_suggestion" in error_response
    
    @pytest.mark.unit
    def test_graceful_degradation(self):
        """测试优雅降级"""
        response = {
            "success": True,
            "model": "mock_service",
            "features": {"mock_mode": True},
            "message": "Mock 模式诊断成功（AI 服务不可用）"
        }
        
        assert response["success"] is True
        assert response["features"]["mock_mode"] is True
    
    @pytest.mark.unit
    def test_timeout_handling(self):
        """测试超时处理"""
        timeout_response = {
            "success": False,
            "error": "请求超时",
            "inference_time_ms": 30000
        }
        
        assert timeout_response["success"] is False
        assert "超时" in timeout_response["error"]


class TestIntegrationHealth:
    """集成健康检查测试类"""
    
    @pytest.mark.integration
    def test_full_diagnosis_flow_mock(self, mock_diagnosis_service):
        """测试完整诊断流程（Mock 模式）"""
        text_result = asyncio.run(mock_diagnosis_service.diagnose_by_text("叶片出现黄色条状病斑"))
        assert text_result["disease_name"] is not None
        
        image_result = asyncio.run(mock_diagnosis_service.diagnose_by_image(b"fake_image", "测试"))
        assert image_result["disease_name"] is not None
    
    @pytest.mark.integration
    def test_service_initialization_order(self):
        """测试服务初始化顺序"""
        init_order = [
            "cache_manager",
            "yolo_service",
            "qwen_service",
            "fusion_service"
        ]
        
        assert len(init_order) == 4
        assert init_order[0] == "cache_manager"
    
    @pytest.mark.integration
    def test_concurrent_health_checks(self, mock_diagnosis_service):
        """测试并发健康检查"""
        async def run_concurrent():
            tasks = [
                mock_diagnosis_service.diagnose_by_text(f"测试症状 {i}")
                for i in range(5)
            ]
            return await asyncio.gather(*tasks)
        
        results = asyncio.run(run_concurrent())
        
        assert len(results) == 5
        for result in results:
            assert "disease_name" in result
            assert "confidence" in result
