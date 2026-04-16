# -*- coding: utf-8 -*-
"""
感知诊断层单元测试
测试 YOLOv8Engine, QwenVLEngine 和 FusionEngine 的核心功能
"""
import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.perception.yolo_engine import YOLOEngine
from src.perception.qwen_vl_engine import QwenVLEngine
from src.perception.fusion_engine import DualEngineFusion


class TestYOLOEngine:
    """YOLOEngine 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        with patch('src.perception.yolo_engine.YOLO'):
            self.engine = YOLOEngine(model_path="mock_model.pt")
    
    def test_yolo_engine_initialization(self):
        """测试 YOLO 引擎初始化"""
        # Arrange & Act
        with patch('src.perception.yolo_engine.YOLO'):
            engine = YOLOEngine()
        
        # Assert
        assert engine is not None
        assert hasattr(engine, 'model')
    
    def test_detect_disease_success(self):
        """测试成功检测病害"""
        # Arrange
        mock_result = Mock()
        mock_result.boxes = Mock()
        mock_result.boxes.conf = np.array([0.95])
        mock_result.boxes.cls = np.array([0])
        mock_result.boxes.xyxy = np.array([[10, 10, 100, 100]])
        self.engine.model.predict = Mock(return_value=[mock_result])
        
        # Act
        result = self.engine.detect_disease("test_image.jpg")
        
        # Assert
        assert result is not None
        assert "detections" in result
        assert "confidence" in result
    
    def test_detect_disease_no_detections(self):
        """测试无检测结果"""
        # Arrange
        mock_result = Mock()
        mock_result.boxes = None
        self.engine.model.predict = Mock(return_value=[mock_result])
        
        # Act
        result = self.engine.detect_disease("test_image.jpg")
        
        # Assert
        assert result is not None
        assert len(result.get("detections", [])) == 0
    
    def test_extract_features_success(self):
        """测试成功提取特征"""
        # Arrange
        detection_result = {
            "detections": [
                {
                    "bbox": [10, 10, 100, 100],
                    "confidence": 0.95,
                    "class": "条锈病"
                }
            ]
        }
        
        # Act
        features = self.engine.extract_features(detection_result)
        
        # Assert
        assert features is not None
        assert "visual_features" in features
    
    def test_calculate_severity_score(self):
        """测试计算严重度评分"""
        # Arrange
        detection_result = {
            "detections": [
                {"bbox": [10, 10, 50, 50], "confidence": 0.9},
                {"bbox": [60, 60, 100, 100], "confidence": 0.8}
            ],
            "image_size": [224, 224]
        }
        
        # Act
        severity = self.engine.calculate_severity_score(detection_result)
        
        # Assert
        assert 0 <= severity <= 1
    
    def test_get_disease_class_name(self):
        """测试获取病害类别名称"""
        # Arrange
        class_id = 0
        
        # Act
        class_name = self.engine.get_disease_class_name(class_id)
        
        # Assert
        assert class_name is not None
    
    def test_batch_detect(self):
        """测试批量检测"""
        # Arrange
        image_paths = ["image1.jpg", "image2.jpg", "image3.jpg"]
        self.engine.model.predict = Mock(return_value=[Mock(boxes=None)])
        
        # Act
        results = self.engine.batch_detect(image_paths)
        
        # Assert
        assert len(results) == len(image_paths)


class TestQwenVLEngine:
    """QwenVLEngine 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        with patch('src.perception.qwen_vl_engine.AutoModelForCausalLM'):
            with patch('src.perception.qwen_vl_engine.AutoTokenizer'):
                self.engine = QwenVLEngine(model_path="mock_model")
    
    def test_qwen_vl_engine_initialization(self):
        """测试 QwenVL 引擎初始化"""
        # Arrange & Act
        with patch('src.perception.qwen_vl_engine.AutoModelForCausalLM'):
            with patch('src.perception.qwen_vl_engine.AutoTokenizer'):
                engine = QwenVLEngine()
        
        # Assert
        assert engine is not None
    
    def test_describe_image_success(self):
        """测试成功描述图像"""
        # Arrange
        mock_response = Mock()
        mock_response = "图像显示小麦叶片出现黄色条状病斑"
        self.engine.generate = Mock(return_value=mock_response)
        
        # Act
        result = self.engine.describe_image("test_image.jpg")
        
        # Assert
        assert result is not None
        assert "description" in result
    
    def test_analyze_disease_features(self):
        """测试分析病害特征"""
        # Arrange
        image_features = {"feature1": "黄色病斑"}
        text_prompt = "请分析病害特征"
        self.engine.generate = Mock(return_value="条锈病特征：黄色条状孢子堆")
        
        # Act
        result = self.engine.analyze_disease_features(image_features, text_prompt)
        
        # Assert
        assert result is not None
        assert "features" in result
    
    def test_generate_diagnosis_reasoning(self):
        """测试生成诊断推理"""
        # Arrange
        context = {
            "disease_candidate": "条锈病",
            "visual_features": ["黄色病斑"],
            "environmental_conditions": {"temperature": "15°C"}
        }
        self.engine.generate = Mock(return_value="推理：符合条锈病特征")
        
        # Act
        result = self.engine.generate_diagnosis_reasoning(context)
        
        # Assert
        assert result is not None
        assert "reasoning" in result


class TestFusionEngine:
    """FusionEngine 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.fusion_engine = DualEngineFusion()
    
    def test_fusion_engine_initialization(self):
        """测试融合引擎初始化"""
        # Arrange & Act
        engine = DualEngineFusion()
        
        # Assert
        assert engine is not None
    
    def test_fuse_multi_modal_features(self):
        """测试融合多模态特征"""
        # Arrange
        visual_features = ["黄色病斑", "沿叶脉排列"]
        text_features = {"symptoms": "叶片发黄"}
        environmental_features = {"temperature": 15.0, "humidity": 80.0}
        
        # Act
        fused = self.fusion_engine.fuse_multi_modal_features(
            visual_features, text_features, environmental_features
        )
        
        # Assert
        assert fused is not None
        assert "visual" in fused
        assert "text" in fused
        assert "environmental" in fused
    
    def test_cross_attention_fusion(self):
        """测试交叉注意力融合"""
        # Arrange
        features = [
            np.random.rand(1, 128).astype(np.float32),
            np.random.rand(1, 128).astype(np.float32)
        ]
        
        # Act
        fused = self.fusion_engine.cross_attention_fusion(features)
        
        # Assert
        assert fused is not None
        assert isinstance(fused, np.ndarray)
    
    def test_confidence_weighted_fusion(self):
        """测试置信度加权融合"""
        # Arrange
        predictions = [
            {"disease": "条锈病", "confidence": 0.9},
            {"disease": "条锈病", "confidence": 0.8}
        ]
        
        # Act
        fused = self.fusion_engine.confidence_weighted_fusion(predictions)
        
        # Assert
        assert fused is not None
        assert "disease" in fused
        assert "confidence" in fused
        assert fused["confidence"] > 0.9  # 加权后应该更高
    
    def test_generate_unified_representation(self):
        """测试生成统一表示"""
        # Arrange
        multi_modal_data = {
            "visual": ["特征 1", "特征 2"],
            "text": {"description": "测试"},
            "environmental": {"temp": 15}
        }
        
        # Act
        representation = self.fusion_engine.generate_unified_representation(multi_modal_data)
        
        # Assert
        assert representation is not None
        assert "feature_vector" in representation
    
    def test_attention_weight_calculation(self):
        """测试注意力权重计算"""
        # Arrange
        features = np.random.rand(5, 128).astype(np.float32)
        
        # Act
        weights = self.fusion_engine.attention_weight_calculation(features)
        
        # Assert
        assert weights is not None
        assert len(weights) == len(features)
        # 权重应该归一化
        assert np.isclose(np.sum(weights), 1.0)
    
    def test_feature_alignment(self):
        """测试特征对齐"""
        # Arrange
        features = [
            np.random.rand(10, 64).astype(np.float32),
            np.random.rand(10, 128).astype(np.float32)
        ]
        
        # Act
        aligned = self.fusion_engine.feature_alignment(features)
        
        # Assert
        assert aligned is not None
        assert len(aligned) == len(features)
    
    def test_multi_scale_fusion(self):
        """测试多尺度融合"""
        # Arrange
        scale_features = {
            "fine": np.random.rand(64, 64, 128).astype(np.float32),
            "medium": np.random.rand(32, 32, 256).astype(np.float32),
            "coarse": np.random.rand(16, 16, 512).astype(np.float32)
        }
        
        # Act
        fused = self.fusion_engine.multi_scale_fusion(scale_features)
        
        # Assert
        assert fused is not None
        assert isinstance(fused, np.ndarray)
    
    def test_temporal_fusion(self):
        """测试时序融合"""
        # Arrange
        temporal_features = [
            np.random.rand(128).astype(np.float32) for _ in range(5)
        ]
        
        # Act
        fused = self.fusion_engine.temporal_fusion(temporal_features)
        
        # Assert
        assert fused is not None
        assert isinstance(fused, np.ndarray)
    
    def test_decision_level_fusion(self):
        """测试决策层融合"""
        # Arrange
        decisions = [
            {"disease": "条锈病", "confidence": 0.9, "source": "YOLO"},
            {"disease": "条锈病", "confidence": 0.85, "source": "QwenVL"}
        ]
        
        # Act
        fused_decision = self.fusion_engine.decision_level_fusion(decisions)
        
        # Assert
        assert fused_decision is not None
        assert fused_decision["disease"] == "条锈病"
        assert fused_decision["confidence"] > 0.85
    
    def test_quality_assessment(self):
        """测试质量评估"""
        # Arrange
        features = np.random.rand(128).astype(np.float32)
        
        # Act
        quality = self.fusion_engine.quality_assessment(features)
        
        # Assert
        assert quality is not None
        assert isinstance(quality, float)
        assert 0 <= quality <= 1


class TestPerceptionIntegration:
    """感知层集成测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        with patch('src.perception.yolo_engine.YOLO'):
            self.yolo_engine = YOLOEngine()
        with patch('src.perception.qwen_vl_engine.AutoModelForCausalLM'):
            with patch('src.perception.qwen_vl_engine.AutoTokenizer'):
                self.qwen_engine = QwenVLEngine()
        self.fusion_engine = DualEngineFusion()
    
    def test_end_to_end_perception(self, tmp_path):
        """测试端到端感知流程"""
        # Arrange
        import cv2
        image_path = tmp_path / "test_image.jpg"
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        cv2.imwrite(str(image_path), test_image)
        
        # Mock YOLO detection
        mock_result = Mock()
        mock_result.boxes = Mock()
        mock_result.boxes.conf = np.array([0.95])
        mock_result.boxes.cls = np.array([0])
        mock_result.boxes.xyxy = np.array([[10, 10, 100, 100]])
        self.yolo_engine.model.predict = Mock(return_value=[mock_result])
        
        # Mock Qwen description
        self.qwen_engine.generate = Mock(return_value="图像显示小麦病害")
        
        # Act
        # 1. YOLO 检测
        yolo_result = self.yolo_engine.detect_disease(str(image_path))
        
        # 2. QwenVL 描述
        qwen_result = self.qwen_engine.describe_image(str(image_path))
        
        # 3. 融合结果
        fused = self.fusion_engine.fuse_multi_modal_features(
            yolo_result.get("detections", []),
            {"description": qwen_result.get("description", "")},
            {}
        )
        
        # Assert
        assert yolo_result is not None
        assert qwen_result is not None
        assert fused is not None


def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
