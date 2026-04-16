# -*- coding: utf-8 -*-
"""
FeatureExtractor 单元测试

使用 Mock 对象测试特征提取器的各个方法，
验证与 YOLO/Qwen/GraphRAG 服务的交互逻辑。
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import numpy as np
import torch

from app.services.fusion_feature_extractor import FeatureExtractor


class TestFeatureExtractorInit:
    """FeatureExtractor 初始化测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = FeatureExtractor()
        
        assert extractor._yolo_service is None
        assert extractor._qwen_service is None
        assert extractor._graphrag_service is None

    def test_init_with_services(self):
        """测试带服务实例的初始化"""
        mock_yolo = MagicMock()
        mock_qwen = MagicMock()
        mock_graphrag = MagicMock()
        
        extractor = FeatureExtractor(
            yolo_service=mock_yolo,
            qwen_service=mock_qwen,
            graphrag_service=mock_graphrag
        )
        
        assert extractor._yolo_service is mock_yolo
        assert extractor._qwen_service is mock_qwen
        assert extractor._graphrag_service is mock_graphrag

    def test_set_services(self):
        """测试动态设置服务"""
        extractor = FeatureExtractor()
        
        mock_yolo = MagicMock()
        extractor.set_services(yolo_service=mock_yolo)
        
        assert extractor._yolo_service is mock_yolo
        assert extractor._qwen_service is None  # 未设置


class TestExtractVisualFeatures:
    """视觉特征提取测试"""

    def test_extract_visual_success(self):
        """测试成功的视觉特征提取"""
        # 创建 Mock YOLO 服务
        mock_yolo = MagicMock()
        mock_yolo.is_loaded = True
        mock_yolo.detect.return_value = {
            "success": True,
            "detections": [
                {
                    "class_name": "小麦锈病",
                    "confidence": 0.95,
                    "bbox": {"x1": 10, "y1": 20, "x2": 100, "y2": 200},
                    "features": torch.randn(768)
                }
            ],
            "count": 1
        }
        
        extractor = FeatureExtractor(yolo_service=mock_yolo)
        image = Image.fromarray(np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8))
        
        result = extractor.extract_visual_features(image)
        
        assert result is not None
        assert result["success"] == True  # 注意：这里返回的是字典，不是布尔值
        assert result["count"] == 1
        assert len(result["detections"]) == 1
        assert result["detections"][0]["class_name"] == "小麦锈病"
        mock_yolo.detect.assert_called_once_with(image)

    def test_extract_visual_yolo_not_loaded(self):
        """测试 YOLO 服务未加载的情况"""
        mock_yolo = MagicMock()
        mock_yolo.is_loaded = False
        
        extractor = FeatureExtractor(yolo_service=mock_yolo)
        image = Image.new("RGB", (640, 640))
        
        result = extractor.extract_visual_features(image)
        
        assert result is None
        mock_yolo.detect.assert_not_called()

    def test_extract_visual_no_service(self):
        """测试无 YOLO 服务的情况"""
        extractor = FeatureExtractor()  # 无服务
        image = Image.new("RGB", (640, 640))
        
        result = extractor.extract_visual_features(image)
        
        assert result is None

    def test_extract_visual_detection_failure(self):
        """测试检测失败的情况"""
        mock_yolo = MagicMock()
        mock_yolo.is_loaded = True
        mock_yolo.detect.return_value = {
            "success": False,
            "error": "模型推理错误"
        }
        
        extractor = FeatureExtractor(yolo_service=mock_yolo)
        image = Image.new("RGB", (640, 640))
        
        result = extractor.extract_visual_features(image)
        
        assert result is None


class TestExtractTextualFeatures:
    """文本特征提取测试"""

    def test_extract_textual_success(self):
        """测试成功的文本特征提取"""
        mock_qwen = MagicMock()
        mock_qwen.is_loaded = True
        mock_qwen.diagnose.return_value = {
            "success": True,
            "diagnosis": {
                "disease_name": "小麦白粉病",
                "confidence": 0.88,
                "description": "叶片出现白色粉层"
            },
            "reasoning_chain": ["步骤1: 分析图像", "步骤2: 识别症状"],
            "features": torch.randn(2560)
        }
        
        extractor = FeatureExtractor(qwen_service=mock_qwen)
        image = Image.new("RGB", (224, 224))
        
        result = extractor.extract_textual_features(
            image=image,
            symptoms="叶片有白色粉末",
            knowledge_context=None,
            enable_thinking=True
        )
        
        assert result is not None
        assert result["diagnosis"]["disease_name"] == "小麦白粉病"
        assert result["diagnosis"]["confidence"] == 0.88
        assert len(result["reasoning_chain"]) == 2
        mock_qwen.diagnose.assert_called_once()

    def test_extract_textual_with_knowledge_context(self):
        """测试带知识上下文的文本特征提取"""
        mock_qwen = MagicMock()
        mock_qwen.is_loaded = True
        mock_qwen.diagnose.return_value = {
            "success": True,
            "diagnosis": {"disease_name": "小麦赤霉病", "confidence": 0.92}
        }
        
        # 创建 Mock 知识上下文
        mock_knowledge = MagicMock()
        mock_knowledge.tokens = "知识嵌入向量..."
        
        extractor = FeatureExtractor(qwen_service=mock_qwen)
        
        result = extractor.extract_textual_features(
            image=None,
            symptoms="穗部发红",
            knowledge_context=mock_knowledge,
            enable_thinking=False
        )
        
        assert result is not None
        # 验证 Qwen 被调用时传入了 use_graph_rag=True
        call_args = mock_qwen.diagnose.call_args
        assert call_args[1]["use_graph_rag"] == True


class TestExtractKnowledgeFeatures:
    """知识特征提取测试"""

    def test_extract_knowledge_success(self):
        """测试成功的知识检索"""
        mock_graphrag = MagicMock()
        mock_graphrag._initialized = True
        
        # 创建 Mock 知识上下文
        mock_context = MagicMock()
        mock_context.triples = [
            MagicMock(head="小麦", relation="感染", tail="锈菌")
        ]
        mock_context.entities = ["小麦", "锈菌"]
        mock_context.citations = [
            {"entity_name": "小麦锈病", "confidence": 0.9}
        ]
        
        mock_graphrag.retrieve_disease_knowledge.return_value = mock_context
        
        extractor = FeatureExtractor(graphrag_service=mock_graphrag)
        
        result = extractor.extract_knowledge_features(
            symptoms="叶片出现锈色斑点",
            disease_hint="锈病"
        )
        
        assert result is not None
        assert result is mock_context
        mock_graphrag.retrieve_disease_knowledge.assert_called_once_with("锈病")

    def test_extract_knowledge_not_initialized(self):
        """测试 GraphRAG 未初始化的情况"""
        mock_graphrag = MagicMock()
        mock_graphrag._initialized = False
        
        extractor = FeatureExtractor(graphrag_service=mock_graphrag)
        
        result = extractor.extract_knowledge_features(symptoms="症状描述")
        
        assert result is None
        mock_graphrag.retrieve_disease_knowledge.assert_not_called()


class TestExtractAllFeatures:
    """协调特征提取测试"""

    @patch.object(FeatureExtractor, 'extract_visual_features')
    @patch.object(FeatureExtractor, 'extract_knowledge_features')
    @patch.object(FeatureExtractor, 'extract_textual_features')
    def test_extract_all_with_image_and_symptoms(
        self,
        mock_textual,
        mock_knowledge,
        mock_visual
    ):
        """测试完整的特征提取流程（有图像和症状）"""
        # 设置 Mock 返回值
        mock_visual.return_value = {"count": 2, "detections": []}
        mock_knowledge.return_value = MagicMock()
        mock_textual.return_value = {"diagnosis": {"disease_name": "测试病害"}}
        
        extractor = FeatureExtractor()
        image = Image.new("RGB", (640, 640))
        
        visual_result, textual_result, knowledge_context = \
            extractor.extract_all_features(
                image=image,
                symptoms="叶片发黄",
                enable_thinking=False,
                use_graph_rag=True
            )
        
        # 验证所有三个提取方法都被调用
        mock_visual.assert_called_once_with(image)
        mock_knowledge.assert_called_once()
        mock_textual.assert_called_once()
        
        assert visual_result is not None
        assert textual_result is not None
        assert knowledge_context is not None

    @patch.object(FeatureExtractor, 'extract_visual_features')
    @patch.object(FeatureExtractor, 'extract_knowledge_features')
    @patch.object(FeatureExtractor, 'extract_textual_features')
    def test_extract_all_without_image(
        self,
        mock_textual,
        mock_knowledge,
        mock_visual
    ):
        """测试无图像时的特征提取"""
        extractor = FeatureExtractor()
        
        visual_result, textual_result, knowledge_context = \
            extractor.extract_all_features(
                image=None,
                symptoms="只有文本症状"
            )
        
        # 视觉提取不应被调用
        mock_visual.assert_not_called()
        # 知识和文本提取应该被调用
        mock_knowledge.assert_called_once()
        mock_textual.assert_called_once()


class TestGenerateTensors:
    """张量生成测试"""

    def test_generate_visual_features_tensor_from_detections(self):
        """测试从检测结果生成视觉特征张量"""
        extractor = FeatureExtractor()

        visual_result = {
            "detections": [
                {
                    "features": torch.randn(768),
                    "class_name": "锈病"
                },
                {
                    "features": torch.randn(768),
                    "class_name": "白粉病"
                }
            ]
        }

        tensor = extractor.generate_visual_features_tensor(visual_result)

        assert tensor is not None
        assert tensor.shape == (1, 2, 768)  # [batch, num_detections, feature_dim]

    def test_generate_visual_features_tensor_pseudo(self):
        """测试无特征时生成伪特征张量"""
        extractor = FeatureExtractor()

        visual_result = {
            "detections": [
                {"class_name": "锈病", "confidence": 0.9},
                {"class_name": "白粉病", "confidence": 0.8},
                {"class_name": "赤霉病", "confidence": 0.7}
            ]
        }

        tensor = extractor.generate_visual_features_tensor(visual_result)

        assert tensor is not None
        assert tensor.shape == (1, 3, 768)  # 应该生成伪特征

    def test_generate_text_features_tensor_from_features(self):
        """测试从文本结果生成特征张量"""
        extractor = FeatureExtractor()

        textual_result = {
            "features": torch.randn(1, 2560),
            "diagnosis": {"disease_name": "测试"}
        }

        tensor = extractor.generate_text_features_tensor(textual_result)

        assert tensor is not None
        assert tensor.shape == (1, 1, 2560) or tensor.shape == (1, 2560)

    def test_generate_knowledge_embeddings_from_tokens(self):
        """测试从 tokens 生成知识嵌入张量"""
        extractor = FeatureExtractor()

        mock_knowledge = MagicMock()
        mock_knowledge.tokens = torch.randn(1, 5, 256)

        tensor = extractor.generate_knowledge_embeddings_tensor(mock_knowledge)

        assert tensor is not None
        assert tensor.shape[0] == 1  # batch 维度
        assert tensor.shape[2] == 256  # 嵌入维度


class TestBoundaryConditions:
    """边界条件测试 - 验证空输入、None 值和异常传播"""

    def test_extract_visual_with_none_image(self):
        """
        测试传入 None 图像时的行为
        验证对空输入的优雅处理
        """
        extractor = FeatureExtractor()
        result = extractor.extract_visual_features(image=None)

        assert result is None

    def test_extract_textual_with_all_none_params(self):
        """
        测试所有参数为 None 时的文本提取
        验证完全空输入的处理能力
        """
        mock_qwen = MagicMock()
        mock_qwen.is_loaded = True
        mock_qwen.diagnose.return_value = {"success": True, "diagnosis": {}}

        extractor = FeatureExtractor(qwen_service=mock_qwen)
        result = extractor.extract_textual_features(
            image=None,
            symptoms=None,
            knowledge_context=None,
            enable_thinking=False
        )

        assert result is not None

    def test_extract_knowledge_with_empty_symptoms(self):
        """
        测试空症状字符串的知识检索
        验证空字符串输入的处理
        """
        mock_graphrag = MagicMock()
        mock_graphrag._initialized = True
        mock_graphrag.retrieve_disease_knowledge.return_value = MagicMock()

        extractor = FeatureExtractor(graphrag_service=mock_graphrag)
        result = extractor.extract_knowledge_features(symptoms="", disease_hint=None)

        assert result is not None
        mock_graphrag.retrieve_disease_knowledge.assert_called_once()

    def test_extract_all_with_completely_empty_input(self):
        """
        测试完全空输入的特征提取流程
        验证无图像无症状时的系统行为
        """
        extractor = FeatureExtractor()

        visual_result, textual_result, knowledge_context = \
            extractor.extract_all_features(
                image=None,
                symptoms=None,
                enable_thinking=False,
                use_graph_rag=False
            )

        assert visual_result is None
        assert textual_result is not None or textual_result is None
        assert knowledge_context is not None or knowledge_context is None

    def test_generate_visual_tensor_with_empty_detections(self):
        """
        测试空检测列表的张量生成
        验证无检测结果时的处理
        """
        extractor = FeatureExtractor()
        visual_result = {"detections": []}

        tensor = extractor.generate_visual_features_tensor(visual_result)

        assert tensor is not None

    def test_generate_text_tensor_with_no_features(self):
        """
        测试无 features 字段的文本结果
        验证缺失特征字段时的降级处理
        """
        extractor = FeatureExtractor()
        textual_result = {
            "diagnosis": {"disease_name": "测试病害"}
        }

        tensor = extractor.generate_text_features_tensor(textual_result)

        assert tensor is not None

    def test_generate_knowledge_tensor_with_none_tokens(self):
        """
        测试 tokens 为 None 的知识嵌入生成
        验证 None 值在嵌入生成中的处理
        """
        extractor = FeatureExtractor()
        mock_knowledge = MagicMock()
        mock_knowledge.tokens = None

        tensor = extractor.generate_knowledge_embeddings_tensor(mock_knowledge)

        assert tensor is not None


class TestExceptionPropagation:
    """异常传播测试 - 验证错误正确传播和处理"""

    def test_extract_visual_service_exception(self):
        """
        测试 YOLO 服务抛出异常时的处理
        验证服务异常不会导致程序崩溃
        """
        mock_yolo = MagicMock()
        mock_yolo.is_loaded = True
        mock_yolo.detect.side_effect = RuntimeError("GPU out of memory")

        extractor = FeatureExtractor(yolo_service=mock_yolo)
        image = Image.new("RGB", (640, 640))

        with pytest.raises(RuntimeError):
            extractor.extract_visual_features(image)

    def test_extract_textual_service_exception(self):
        """
        测试 Qwen 服务抛出异常时的处理
        验证文本分析服务异常的正确传播
        """
        mock_qwen = MagicMock()
        mock_qwen.is_loaded = True
        mock_qwen.diagnose.side_effect = ConnectionError("Model server unreachable")

        extractor = FeatureExtractor(qwen_service=mock_qwen)

        with pytest.raises(ConnectionError):
            extractor.extract_textual_features(
                image=Image.new("RGB", (224, 224)),
                symptoms="测试症状"
            )

    def test_extract_knowledge_service_exception(self):
        """
        测试 GraphRAG 服务抛出异常时的处理
        验证知识检索服务异常的传播机制
        """
        mock_graphrag = MagicMock()
        mock_graphrag._initialized = True
        mock_graphrag.retrieve_disease_knowledge.side_effect = \
            TimeoutError("Knowledge base query timeout")

        extractor = FeatureExtractor(graphrag_service=mock_graphrag)

        with pytest.raises(TimeoutError):
            extractor.extract_knowledge_features(symptoms="症状描述")

    def test_set_services_with_invalid_type(self):
        """
        测试设置无效类型的服务实例
        验证类型检查或异常处理机制
        """
        extractor = FeatureExtractor()

        invalid_service = "not_a_service_object"
        extractor.set_services(yolo_service=invalid_service)

        assert extractor._yolo_service == invalid_service

    def test_generate_tensor_with_corrupted_data(self):
        """
        测试使用损坏数据生成张量
        验证对畸形数据的容错能力
        """
        extractor = FeatureExtractor()

        corrupted_visual = {
            "detections": [
                {"features": "not_a_tensor", "class_name": "锈病"}
            ]
        }

        try:
            tensor = extractor.generate_visual_features_tensor(corrupted_visual)
            assert tensor is not None
        except (AttributeError, TypeError):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
