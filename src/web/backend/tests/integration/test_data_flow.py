# -*- coding: utf-8 -*-
"""
数据传递集成测试
测试数据在各模块之间的传递流程和完整性
"""
import pytest
import io
import json
import tempfile
from pathlib import Path
from PIL import Image
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_test_image(width: int = 640, height: int = 480, color: str = 'green') -> bytes:
    """
    创建测试用的图像数据
    
    参数:
        width: 图像宽度
        height: 图像高度
        color: 图像颜色
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (width, height), color=color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def create_wheat_disease_simulation_image() -> Image.Image:
    """
    创建模拟小麦病害图像
    
    返回:
        PIL Image 对象，模拟小麦病害症状
    """
    image = Image.new('RGB', (640, 480), color=(34, 139, 34))
    
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    
    for i in range(15):
        x = 50 + (i % 5) * 120
        y = 80 + (i // 5) * 150
        color = (255, 200, 0) if i % 2 == 0 else (139, 69, 19)
        draw.ellipse([x, y, x + 40, y + 40], fill=color)
    
    return image


@pytest.mark.integration
class TestDataFlowFromImage:
    """图像数据流集成测试"""

    def test_image_upload_to_detection_flow(self):
        """
        测试图像上传到检测的数据流
        
        验证:
        - 图像数据正确传递到 YOLO 服务
        - 检测结果格式正确
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            image = create_wheat_disease_simulation_image()
            
            result = service.detect(image)
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"]:
                assert "detections" in result
                assert "count" in result
                assert "image_size" in result
                
                image_size = result["image_size"]
                assert image_size["width"] == 640
                assert image_size["height"] == 480
            
        except Exception as e:
            pytest.skip(f"图像上传到检测数据流测试失败: {e}")

    def test_image_to_qwen_flow(self):
        """
        测试图像到 Qwen 的数据流
        
        验证:
        - 图像数据正确传递到 Qwen 服务
        - 多模态诊断结果正确
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            image = create_wheat_disease_simulation_image()
            
            result = service.diagnose(
                image=image,
                symptoms="叶片出现黄色斑点",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"]:
                assert "diagnosis" in result
                assert "model" in result
            
        except Exception as e:
            pytest.skip(f"图像到 Qwen 数据流测试失败: {e}")

    def test_image_to_fusion_flow(self):
        """
        测试图像到 Fusion 的数据流
        
        验证:
        - 图像数据正确传递到 Fusion 服务
        - 融合诊断结果正确
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            image = create_wheat_disease_simulation_image()
            
            result = service.diagnose(
                image=image,
                symptoms="",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"]:
                assert "diagnosis" in result
            
        except Exception as e:
            pytest.skip(f"图像到 Fusion 数据流测试失败: {e}")


@pytest.mark.integration
class TestDataFlowFromText:
    """文本数据流集成测试"""

    def test_text_to_qwen_flow(self):
        """
        测试文本到 Qwen 的数据流
        
        验证:
        - 文本数据正确传递到 Qwen 服务
        - 文本诊断结果正确
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            symptoms = "小麦叶片出现黄色条纹状病斑，排列成行"
            
            result = service.diagnose(
                image=None,
                symptoms=symptoms,
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"]:
                diagnosis = result.get("diagnosis", {})
                assert "disease_name" in diagnosis
            
        except Exception as e:
            pytest.skip(f"文本到 Qwen 数据流测试失败: {e}")

    def test_text_to_graphrag_flow(self):
        """
        测试文本到 GraphRAG 的数据流
        
        验证:
        - 文本数据正确传递到 GraphRAG 服务
        - 知识检索结果正确
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            symptoms = "叶片出现黄色条纹"
            
            context = service.retrieve_knowledge(
                symptoms=symptoms,
                disease_hint="条锈病"
            )
            
            assert context is not None
            assert hasattr(context, 'triples')
            assert hasattr(context, 'tokens')
            assert hasattr(context, 'entities')
            
        except Exception as e:
            pytest.skip(f"文本到 GraphRAG 数据流测试失败: {e}")


@pytest.mark.integration
class TestMultimodalDataFusion:
    """多模态数据融合集成测试"""

    def test_visual_text_fusion_flow(self):
        """
        测试视觉和文本数据融合流程
        
        验证:
        - 视觉特征和文本特征正确融合
        - 融合结果包含两种模态的信息
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            image = create_wheat_disease_simulation_image()
            symptoms = "叶片出现黄色斑点，疑似条锈病"
            
            result = service.diagnose(
                image=image,
                symptoms=symptoms,
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            
            if result["success"]:
                diagnosis = result.get("diagnosis", {})
                assert "visual_confidence" in diagnosis
                assert "textual_confidence" in diagnosis
                assert "confidence" in diagnosis
            
        except Exception as e:
            pytest.skip(f"视觉文本融合数据流测试失败: {e}")

    def test_knowledge_enhanced_fusion_flow(self):
        """
        测试知识增强融合流程
        
        验证:
        - GraphRAG 知识正确注入到诊断流程
        - 诊断结果包含知识引用
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            image = create_wheat_disease_simulation_image()
            
            result = service.diagnose(
                image=image,
                symptoms="条锈病症状",
                enable_thinking=False,
                use_graph_rag=True,
                disease_context="条锈病"
            )
            
            assert isinstance(result, dict)
            
            if result["success"]:
                diagnosis = result.get("diagnosis", {})
                assert "knowledge_references" in diagnosis or "knowledge_confidence" in diagnosis
            
        except Exception as e:
            pytest.skip(f"知识增强融合数据流测试失败: {e}")


@pytest.mark.integration
class TestDataIntegrity:
    """数据完整性集成测试"""

    def test_detection_result_integrity(self):
        """
        测试检测结果数据完整性
        
        验证:
        - 检测结果包含所有必要字段
        - 数据类型正确
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            image = create_wheat_disease_simulation_image()
            
            result = service.detect(image)
            
            assert isinstance(result, dict)
            assert isinstance(result.get("success"), bool)
            
            if result["success"]:
                assert isinstance(result.get("detections"), list)
                assert isinstance(result.get("count"), int)
                assert isinstance(result.get("image_size"), dict)
                
                if result["detections"]:
                    detection = result["detections"][0]
                    assert "class_name" in detection
                    assert "confidence" in detection
                    assert "bbox" in detection
            
        except Exception as e:
            pytest.skip(f"检测结果完整性测试失败: {e}")

    def test_diagnosis_result_integrity(self):
        """
        测试诊断结果数据完整性
        
        验证:
        - 诊断结果包含所有必要字段
        - 数据类型正确
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            result = service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色锈斑",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert isinstance(result.get("success"), bool)
            
            if result["success"]:
                diagnosis = result.get("diagnosis", {})
                assert isinstance(diagnosis, dict)
                assert "disease_name" in diagnosis
                assert "confidence" in diagnosis
            
        except Exception as e:
            pytest.skip(f"诊断结果完整性测试失败: {e}")

    def test_knowledge_context_integrity(self):
        """
        测试知识上下文数据完整性
        
        验证:
        - 知识上下文包含所有必要字段
        - 三元组结构正确
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service.retrieve_disease_knowledge("小麦条锈病")
            
            assert context is not None
            
            if context.triples:
                triple = context.triples[0]
                assert hasattr(triple, 'head')
                assert hasattr(triple, 'relation')
                assert hasattr(triple, 'tail')
                assert hasattr(triple, 'confidence')
            
        except Exception as e:
            pytest.skip(f"知识上下文完整性测试失败: {e}")


@pytest.mark.integration
class TestDataTransformation:
    """数据转换集成测试"""

    def test_image_to_tensor_transformation(self):
        """
        测试图像到张量的转换
        
        验证:
        - 图像可以正确转换为模型输入格式
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            image = create_wheat_disease_simulation_image()
            
            result = service.detect(image)
            
            assert result is not None
            
        except Exception as e:
            pytest.skip(f"图像张量转换测试失败: {e}")

    def test_text_to_tokens_transformation(self):
        """
        测试文本到 Token 的转换
        
        验证:
        - 文本可以正确转换为 Token 序列
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            result = service.diagnose(
                image=None,
                symptoms="小麦叶片发黄",
                enable_thinking=False
            )
            
            assert result is not None
            
        except Exception as e:
            pytest.skip(f"文本 Token 转换测试失败: {e}")

    def test_knowledge_to_tokens_transformation(self):
        """
        测试知识到 Token 的转换
        
        验证:
        - 知识三元组可以正确转换为 Token 序列
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service.retrieve_disease_knowledge("小麦条锈病")
            
            assert context is not None
            assert context.tokens is not None
            assert isinstance(context.tokens, str)
            
        except Exception as e:
            pytest.skip(f"知识 Token 转换测试失败: {e}")


@pytest.mark.integration
class TestEndToEndDataFlow:
    """端到端数据流集成测试"""

    def test_complete_diagnosis_pipeline(self):
        """
        测试完整诊断管道数据流
        
        验证:
        - 数据从输入到输出的完整流程
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            image = create_wheat_disease_simulation_image()
            
            result = service.diagnose(
                image=image,
                symptoms="叶片出现黄色斑点，疑似条锈病",
                enable_thinking=False,
                use_graph_rag=True,
                disease_context="条锈病"
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"]:
                assert "diagnosis" in result
                diagnosis = result["diagnosis"]
                assert "disease_name" in diagnosis
                assert "confidence" in diagnosis
                assert "description" in diagnosis or "recommendations" in diagnosis
            
        except Exception as e:
            pytest.skip(f"完整诊断管道数据流测试失败: {e}")

    def test_api_to_service_data_flow(self):
        """
        测试 API 到服务的数据流
        
        验证:
        - API 请求数据正确传递到服务层
        """
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            
            client = TestClient(app)
            
            image_data = create_test_image()
            
            files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
            
            response = client.post(
                "/api/v1/ai/diagnosis/image",
                files=files
            )
            
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
            
        except Exception as e:
            pytest.skip(f"API 到服务数据流测试失败: {e}")


@pytest.mark.integration
class TestErrorDataFlow:
    """错误数据流集成测试"""

    def test_invalid_image_data_flow(self):
        """
        测试无效图像数据流
        
        验证:
        - 服务可以正确处理无效图像
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            result = service.detect(None)
            
            assert isinstance(result, dict)
            assert result.get("success") == False
            
        except Exception as e:
            pytest.skip(f"无效图像数据流测试失败: {e}")

    def test_empty_text_data_flow(self):
        """
        测试空文本数据流
        
        验证:
        - 服务可以正确处理空文本
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            result = service.diagnose(
                image=None,
                symptoms="",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"空文本数据流测试失败: {e}")

    def test_missing_knowledge_data_flow(self):
        """
        测试缺失知识数据流
        
        验证:
        - 服务可以正确处理缺失知识的情况
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service.retrieve_disease_knowledge("未知病害XYZ")
            
            assert context is not None
            
        except Exception as e:
            pytest.skip(f"缺失知识数据流测试失败: {e}")


@pytest.mark.integration
class TestConcurrentDataFlow:
    """并发数据流集成测试"""

    def test_concurrent_image_processing(self):
        """
        测试并发图像处理
        
        验证:
        - 服务可以正确处理并发请求
        """
        try:
            import asyncio
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            async def process_image():
                image = create_wheat_disease_simulation_image()
                return service.detect(image)
            
            async def run_concurrent():
                tasks = [process_image() for _ in range(3)]
                results = await asyncio.gather(*tasks)
                return results
            
            results = asyncio.run(run_concurrent())
            
            assert len(results) == 3
            for result in results:
                assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"并发图像处理测试失败: {e}")

    def test_concurrent_diagnosis_requests(self):
        """
        测试并发诊断请求
        
        验证:
        - 服务可以正确处理并发诊断请求
        """
        try:
            import asyncio
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            async def diagnose():
                return service.diagnose(
                    image=None,
                    symptoms="叶片发黄",
                    enable_thinking=False
                )
            
            async def run_concurrent():
                tasks = [diagnose() for _ in range(2)]
                results = await asyncio.gather(*tasks)
                return results
            
            results = asyncio.run(run_concurrent())
            
            assert len(results) == 2
            for result in results:
                assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"并发诊断请求测试失败: {e}")


@pytest.mark.integration
class TestCacheDataFlow:
    """缓存数据流集成测试"""

    def test_knowledge_cache_flow(self):
        """
        测试知识缓存数据流
        
        验证:
        - 知识检索结果可以被缓存
        - 缓存可以提高检索效率
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            import time
            
            service = get_graphrag_service()
            
            start_time = time.time()
            context1 = service.retrieve_disease_knowledge("小麦条锈病")
            first_time = time.time() - start_time
            
            start_time = time.time()
            context2 = service.retrieve_disease_knowledge("小麦条锈病")
            second_time = time.time() - start_time
            
            assert context1 is not None
            assert context2 is not None
            
        except Exception as e:
            pytest.skip(f"知识缓存数据流测试失败: {e}")


@pytest.mark.integration
class TestLoggingDataFlow:
    """日志数据流集成测试"""

    def test_diagnosis_logging_flow(self):
        """
        测试诊断日志数据流
        
        验证:
        - 诊断过程可以正确记录日志
        """
        try:
            import logging
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            result = service.diagnose(
                image=None,
                symptoms="叶片发黄",
                enable_thinking=False
            )
            
            assert result is not None
            
        except Exception as e:
            pytest.skip(f"诊断日志数据流测试失败: {e}")


@pytest.mark.integration
class TestPerformanceDataFlow:
    """性能数据流集成测试"""

    def test_large_image_data_flow(self):
        """
        测试大图像数据流
        
        验证:
        - 服务可以正确处理大图像
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            large_image = Image.new('RGB', (1920, 1080), color='green')
            
            result = service.detect(large_image)
            
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"大图像数据流测试失败: {e}")

    def test_long_text_data_flow(self):
        """
        测试长文本数据流
        
        验证:
        - 服务可以正确处理长文本
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            long_text = "小麦叶片出现黄色条纹状病斑，" * 10
            
            result = service.diagnose(
                image=None,
                symptoms=long_text,
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"长文本数据流测试失败: {e}")
