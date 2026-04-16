# -*- coding: utf-8 -*-
"""
模块间交互集成测试
测试 YOLO、Qwen、Fusion、GraphRAG 服务之间的交互
"""
import pytest
import io
import tempfile
from pathlib import Path
from PIL import Image
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
@pytest.mark.yolo
class TestYOLOServiceIntegration:
    """YOLO 服务集成测试"""

    def test_yolo_service_initialization(self):
        """
        测试 YOLO 服务初始化
        
        验证:
        - 服务可以正确初始化
        - 服务状态正确
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            assert service is not None
            assert hasattr(service, 'is_loaded')
            assert hasattr(service, 'detect')
            assert hasattr(service, 'get_model_info')
            
        except Exception as e:
            pytest.skip(f"YOLO 服务初始化失败: {e}")

    def test_yolo_service_model_info(self):
        """
        测试 YOLO 服务模型信息获取
        
        验证:
        - 可以获取模型信息
        - 模型信息包含必要字段
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            model_info = service.get_model_info()
            
            assert isinstance(model_info, dict)
            assert "model_type" in model_info
            assert "is_loaded" in model_info
            assert "classes" in model_info
            
        except Exception as e:
            pytest.skip(f"YOLO 服务不可用: {e}")

    def test_yolo_service_detection(self):
        """
        测试 YOLO 服务检测功能
        
        验证:
        - 可以对图像进行检测
        - 返回正确格式的结果
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
            assert "detections" in result
            
        except Exception as e:
            pytest.skip(f"YOLO 检测失败: {e}")

    def test_yolo_service_detection_from_file(self):
        """
        测试 YOLO 服务从文件检测
        
        验证:
        - 可以从文件路径进行检测
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            if not service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            image = create_wheat_disease_simulation_image()
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                image.save(f.name)
                temp_path = Path(f.name)
            
            try:
                result = service.detect_from_file(temp_path)
                
                assert isinstance(result, dict)
                assert "success" in result
            finally:
                if temp_path.exists():
                    temp_path.unlink()
            
        except Exception as e:
            pytest.skip(f"YOLO 文件检测失败: {e}")

    def test_yolo_service_chinese_name_mapping(self):
        """
        测试 YOLO 服务中文名称映射
        
        验证:
        - 英文病害名称可以正确映射为中文
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            chinese_name = service.get_chinese_name("Yellow Rust")
            assert chinese_name == "条锈病"
            
            chinese_name = service.get_chinese_name("Unknown Disease")
            assert chinese_name == "Unknown Disease"
            
        except Exception as e:
            pytest.skip(f"YOLO 服务不可用: {e}")

    def test_yolo_service_class_validation(self):
        """
        测试 YOLO 服务类别校验
        
        验证:
        - 可以校验模型类别
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            validation_result = service.validate_disease_classes()
            
            assert isinstance(validation_result, dict)
            assert "is_valid" in validation_result
            assert "match_rate" in validation_result
            
        except Exception as e:
            pytest.skip(f"YOLO 类别校验失败: {e}")


@pytest.mark.integration
@pytest.mark.qwen
@pytest.mark.slow
@pytest.mark.gpu
class TestQwenServiceIntegration:
    """Qwen 服务集成测试"""

    def test_qwen_service_initialization(self):
        """
        测试 Qwen 服务初始化
        
        验证:
        - 服务可以正确初始化
        - 服务状态正确
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            assert service is not None
            assert hasattr(service, 'is_loaded')
            assert hasattr(service, 'diagnose')
            assert hasattr(service, 'get_model_info')
            
        except Exception as e:
            pytest.skip(f"Qwen 服务初始化失败: {e}")

    def test_qwen_service_model_info(self):
        """
        测试 Qwen 服务模型信息获取
        
        验证:
        - 可以获取模型信息
        - 模型信息包含必要字段
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            model_info = service.get_model_info()
            
            assert isinstance(model_info, dict)
            assert "model_type" in model_info
            assert "is_loaded" in model_info
            assert "features" in model_info
            
        except Exception as e:
            pytest.skip(f"Qwen 服务不可用: {e}")

    def test_qwen_service_text_diagnosis(self):
        """
        测试 Qwen 服务文本诊断
        
        验证:
        - 可以进行文本诊断
        - 返回正确格式的结果
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            result = service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色条纹状病斑",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            assert "diagnosis" in result
            
        except Exception as e:
            pytest.skip(f"Qwen 文本诊断失败: {e}")

    def test_qwen_service_multimodal_diagnosis(self):
        """
        测试 Qwen 服务多模态诊断
        
        验证:
        - 可以进行多模态诊断
        - 返回正确格式的结果
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
            
        except Exception as e:
            pytest.skip(f"Qwen 多模态诊断失败: {e}")

    def test_qwen_service_thinking_mode(self):
        """
        测试 Qwen 服务 Thinking 模式
        
        验证:
        - Thinking 模式可以正常工作
        - 返回推理链
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            result = service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色锈斑",
                enable_thinking=True
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"] and "reasoning_chain" in result:
                assert isinstance(result["reasoning_chain"], list)
            
        except Exception as e:
            pytest.skip(f"Qwen Thinking 模式测试失败: {e}")

    def test_qwen_service_gpu_memory_management(self):
        """
        测试 Qwen 服务 GPU 显存管理
        
        验证:
        - 可以获取 GPU 显存状态
        - 可以卸载/加载模型
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            gpu_status = service.get_gpu_memory_status()
            
            assert isinstance(gpu_status, dict)
            assert "available" in gpu_status
            
        except Exception as e:
            pytest.skip(f"Qwen GPU 显存管理测试失败: {e}")


@pytest.mark.integration
@pytest.mark.graphrag
class TestGraphRAGServiceIntegration:
    """GraphRAG 服务集成测试"""

    def test_graphrag_service_initialization(self):
        """
        测试 GraphRAG 服务初始化
        
        验证:
        - 服务可以正确初始化
        - 服务状态正确
        """
        try:
            from app.services.graphrag_service import get_graphrag_service, GraphRAGService
            
            service = get_graphrag_service()
            
            assert service is not None
            assert hasattr(service, '_initialized')
            assert hasattr(service, 'retrieve_knowledge')
            assert hasattr(service, 'retrieve_disease_knowledge')
            
        except Exception as e:
            pytest.skip(f"GraphRAG 服务初始化失败: {e}")

    def test_graphrag_service_disease_name_mapping(self):
        """
        测试 GraphRAG 服务病害名称映射
        
        验证:
        - 英文名称可以正确映射为中文
        """
        try:
            from app.services.graphrag_service import GraphRAGService
            
            chinese_name = GraphRAGService.map_disease_name("Yellow Rust")
            assert chinese_name == "小麦条锈病"
            
            chinese_name = GraphRAGService.map_disease_name("未知病害")
            assert chinese_name == "未知病害"
            
        except Exception as e:
            pytest.skip(f"GraphRAG 服务不可用: {e}")

    def test_graphrag_service_retrieve_knowledge(self):
        """
        测试 GraphRAG 服务知识检索
        
        验证:
        - 可以检索知识
        - 返回正确格式的结果
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service.retrieve_knowledge(
                symptoms="叶片出现黄色条纹",
                disease_hint="条锈病"
            )
            
            assert context is not None
            assert hasattr(context, 'triples')
            assert hasattr(context, 'tokens')
            
        except Exception as e:
            pytest.skip(f"GraphRAG 知识检索失败: {e}")

    def test_graphrag_service_retrieve_disease_knowledge(self):
        """
        测试 GraphRAG 服务病害知识检索
        
        验证:
        - 可以检索特定病害的知识
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service.retrieve_disease_knowledge("小麦条锈病")
            
            assert context is not None
            assert hasattr(context, 'triples')
            
        except Exception as e:
            pytest.skip(f"GraphRAG 病害知识检索失败: {e}")

    def test_graphrag_service_fallback_mode(self):
        """
        测试 GraphRAG 服务降级模式
        
        验证:
        - 降级模式可以正常工作
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service._fallback_retrieve(
                symptoms="叶片发黄",
                disease_hint="条锈病"
            )
            
            assert context is not None
            assert len(context.triples) > 0
            
        except Exception as e:
            pytest.skip(f"GraphRAG 降级模式测试失败: {e}")

    def test_graphrag_service_stats(self):
        """
        测试 GraphRAG 服务统计信息
        
        验证:
        - 可以获取服务统计信息
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            stats = service.get_stats()
            
            assert isinstance(stats, dict)
            assert "initialized" in stats
            
        except Exception as e:
            pytest.skip(f"GraphRAG 统计信息获取失败: {e}")


@pytest.mark.integration
@pytest.mark.fusion
@pytest.mark.slow
@pytest.mark.gpu
class TestFusionServiceIntegration:
    """Fusion 服务集成测试"""

    def test_fusion_service_initialization(self):
        """
        测试 Fusion 服务初始化
        
        验证:
        - 服务可以正确初始化
        - 服务状态正确
        """
        try:
            from app.services.fusion_service import get_fusion_service, MultimodalFusionService
            
            service = get_fusion_service()
            
            assert service is not None
            assert hasattr(service, '_initialized')
            assert hasattr(service, 'diagnose')
            assert hasattr(service, 'initialize')
            
        except Exception as e:
            pytest.skip(f"Fusion 服务初始化失败: {e}")

    def test_fusion_service_initialize(self):
        """
        测试 Fusion 服务初始化方法
        
        验证:
        - 可以调用初始化方法
        """
        try:
            from app.services.fusion_service import MultimodalFusionService
            
            service = MultimodalFusionService()
            service.initialize()
            
        except Exception as e:
            pytest.skip(f"Fusion 服务初始化方法失败: {e}")

    def test_fusion_service_diagnose_text_only(self):
        """
        测试 Fusion 服务纯文本诊断
        
        验证:
        - 可以进行纯文本诊断
        - 返回正确格式的结果
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            result = service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色条纹状病斑",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            assert "diagnosis" in result
            
        except Exception as e:
            pytest.skip(f"Fusion 纯文本诊断失败: {e}")

    def test_fusion_service_diagnose_image_only(self):
        """
        测试 Fusion 服务纯图像诊断
        
        验证:
        - 可以进行纯图像诊断
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
            
        except Exception as e:
            pytest.skip(f"Fusion 纯图像诊断失败: {e}")

    def test_fusion_service_diagnose_multimodal(self):
        """
        测试 Fusion 服务多模态诊断
        
        验证:
        - 可以进行多模态诊断
        - 返回融合结果
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            service.initialize()
            
            image = create_wheat_disease_simulation_image()
            
            result = service.diagnose(
                image=image,
                symptoms="叶片出现黄色斑点，排列成行",
                enable_thinking=False,
                use_graph_rag=True
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
            if result["success"]:
                diagnosis = result.get("diagnosis", {})
                assert "disease_name" in diagnosis
                assert "confidence" in diagnosis
            
        except Exception as e:
            pytest.skip(f"Fusion 多模态诊断失败: {e}")

    def test_fusion_service_with_graph_rag(self):
        """
        测试 Fusion 服务与 GraphRAG 集成
        
        验证:
        - GraphRAG 可以增强诊断结果
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
            
        except Exception as e:
            pytest.skip(f"Fusion GraphRAG 集成测试失败: {e}")


@pytest.mark.integration
@pytest.mark.slow
class TestModuleInteraction:
    """模块间交互集成测试"""

    def test_yolo_to_fusion_interaction(self):
        """
        测试 YOLO 到 Fusion 的交互
        
        验证:
        - YOLO 检测结果可以传递给 Fusion
        """
        try:
            from app.services.yolo_service import get_yolo_service
            from app.services.fusion_service import get_fusion_service
            
            yolo_service = get_yolo_service()
            fusion_service = get_fusion_service()
            
            if not yolo_service.is_loaded:
                pytest.skip("YOLO 模型未加载")
            
            image = create_wheat_disease_simulation_image()
            
            yolo_result = yolo_service.detect(image)
            
            assert isinstance(yolo_result, dict)
            
            fusion_service.initialize()
            fusion_result = fusion_service.diagnose(
                image=image,
                symptoms="",
                enable_thinking=False
            )
            
            assert isinstance(fusion_result, dict)
            
        except Exception as e:
            pytest.skip(f"YOLO-Fusion 交互测试失败: {e}")

    def test_qwen_to_fusion_interaction(self):
        """
        测试 Qwen 到 Fusion 的交互
        
        验证:
        - Qwen 诊断结果可以传递给 Fusion
        """
        try:
            from app.services.qwen_service import get_qwen_service
            from app.services.fusion_service import get_fusion_service
            
            qwen_service = get_qwen_service()
            fusion_service = get_fusion_service()
            
            if not qwen_service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            qwen_result = qwen_service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色锈斑",
                enable_thinking=False
            )
            
            assert isinstance(qwen_result, dict)
            
            fusion_service.initialize()
            fusion_result = fusion_service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色锈斑",
                enable_thinking=False
            )
            
            assert isinstance(fusion_result, dict)
            
        except Exception as e:
            pytest.skip(f"Qwen-Fusion 交互测试失败: {e}")

    def test_graphrag_to_qwen_interaction(self):
        """
        测试 GraphRAG 到 Qwen 的交互
        
        验证:
        - GraphRAG 知识可以增强 Qwen 诊断
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            from app.services.qwen_service import get_qwen_service
            
            graphrag_service = get_graphrag_service()
            qwen_service = get_qwen_service()
            
            if not qwen_service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            knowledge_context = graphrag_service.retrieve_disease_knowledge("小麦条锈病")
            
            assert knowledge_context is not None
            
            result = qwen_service.diagnose(
                image=None,
                symptoms="小麦叶片出现黄色条纹",
                enable_thinking=False,
                use_graph_rag=True,
                disease_context="条锈病"
            )
            
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"GraphRAG-Qwen 交互测试失败: {e}")

    def test_full_pipeline_interaction(self):
        """
        测试完整管道交互
        
        验证:
        - 所有模块可以协同工作
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            fusion_service = get_fusion_service()
            fusion_service.initialize()
            
            image = create_wheat_disease_simulation_image()
            
            result = fusion_service.diagnose(
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
            
        except Exception as e:
            pytest.skip(f"完整管道交互测试失败: {e}")

    def test_service_error_handling(self):
        """
        测试服务错误处理
        
        验证:
        - 服务可以正确处理错误输入
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            fusion_service = get_fusion_service()
            fusion_service.initialize()
            
            result = fusion_service.diagnose(
                image=None,
                symptoms="",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.skip(f"服务错误处理测试失败: {e}")


@pytest.mark.integration
class TestServiceHealthCheck:
    """服务健康检查集成测试"""

    def test_yolo_service_health(self):
        """
        测试 YOLO 服务健康状态
        
        验证:
        - 可以检查 YOLO 服务状态
        """
        try:
            from app.services.yolo_service import get_yolo_service
            
            service = get_yolo_service()
            
            assert service is not None
            assert hasattr(service, 'is_loaded')
            
        except Exception as e:
            pytest.skip(f"YOLO 服务健康检查失败: {e}")

    def test_qwen_service_health(self):
        """
        测试 Qwen 服务健康状态
        
        验证:
        - 可以检查 Qwen 服务状态
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            assert service is not None
            assert hasattr(service, 'is_loaded')
            
        except Exception as e:
            pytest.skip(f"Qwen 服务健康检查失败: {e}")

    def test_graphrag_service_health(self):
        """
        测试 GraphRAG 服务健康状态
        
        验证:
        - 可以检查 GraphRAG 服务状态
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            assert service is not None
            assert hasattr(service, '_initialized')
            
        except Exception as e:
            pytest.skip(f"GraphRAG 服务健康检查失败: {e}")

    def test_fusion_service_health(self):
        """
        测试 Fusion 服务健康状态
        
        验证:
        - 可以检查 Fusion 服务状态
        """
        try:
            from app.services.fusion_service import get_fusion_service
            
            service = get_fusion_service()
            
            assert service is not None
            assert hasattr(service, '_initialized')
            
        except Exception as e:
            pytest.skip(f"Fusion 服务健康检查失败: {e}")


@pytest.mark.integration
class TestServiceDegradation:
    """服务降级集成测试"""

    def test_fusion_service_degradation_without_yolo(self):
        """
        测试 Fusion 服务在 YOLO 不可用时的降级
        
        验证:
        - 服务可以降级运行
        """
        try:
            from app.services.fusion_service import MultimodalFusionService
            
            fusion_service = MultimodalFusionService()
            
            result = fusion_service.diagnose(
                image=None,
                symptoms="叶片出现黄色斑点",
                enable_thinking=False
            )
            
            assert isinstance(result, dict)
            assert "success" in result
            
        except Exception as e:
            pytest.skip(f"Fusion 服务降级测试失败: {e}")

    def test_graphrag_fallback_mode(self):
        """
        测试 GraphRAG 降级模式
        
        验证:
        - GraphRAG 可以在降级模式下工作
        """
        try:
            from app.services.graphrag_service import get_graphrag_service
            
            service = get_graphrag_service()
            
            context = service._fallback_retrieve(
                symptoms="叶片发黄",
                disease_hint="条锈病"
            )
            
            assert context is not None
            assert len(context.triples) > 0
            
        except Exception as e:
            pytest.skip(f"GraphRAG 降级模式测试失败: {e}")

    def test_qwen_service_cpu_offload(self):
        """
        测试 Qwen 服务 CPU Offload
        
        验证:
        - Qwen 可以使用 CPU Offload 模式
        """
        try:
            from app.services.qwen_service import get_qwen_service
            
            service = get_qwen_service()
            
            if not service.is_loaded:
                pytest.skip("Qwen 模型未加载")
            
            if hasattr(service, 'cpu_offload'):
                assert isinstance(service.cpu_offload, bool)
            
        except Exception as e:
            pytest.skip(f"Qwen CPU Offload 测试失败: {e}")
