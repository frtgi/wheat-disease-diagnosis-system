# -*- coding: utf-8 -*-
"""
视觉模块测试

测试预处理、可视化和多尺度检测模块
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision.preprocessing import (
    ImagePreprocessor,
    PreprocessConfig,
    ImageQualityAssessor,
    DataAugmenter,
    create_preprocessor
)
from src.vision.visualization import (
    FeatureVisualizer,
    DetectionVisualizer,
    create_visualizer,
    create_detection_visualizer
)
from src.vision.multi_scale import (
    MultiScaleDetector,
    MultiScaleConfig,
    SmallObjectEnhancer,
    create_multiscale_detector,
    create_small_object_enhancer
)


class TestImagePreprocessor:
    """图像预处理器测试"""
    
    def test_preprocessor_creation(self):
        """测试预处理器创建"""
        preprocessor = create_preprocessor()
        
        assert preprocessor is not None
        assert preprocessor.config.target_size == (640, 640)
    
    def test_preprocess_config(self):
        """测试预处理配置"""
        config = PreprocessConfig(
            target_size=(416, 416),
            normalize=True
        )
        
        preprocessor = ImagePreprocessor(config)
        
        assert preprocessor.config.target_size == (416, 416)
    
    def test_preprocess_image(self):
        """测试图像预处理"""
        preprocessor = create_preprocessor(target_size=(224, 224))
        
        # 创建测试图像
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed, metadata = preprocessor.preprocess(image)
        
        assert processed.shape[:2] == (224, 224)
        assert "original_shape" in metadata
        assert "scale_info" in metadata
    
    def test_preprocess_batch(self):
        """测试批量预处理"""
        preprocessor = create_preprocessor(target_size=(224, 224))
        
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(3)
        ]
        
        processed, metadata_list = preprocessor.preprocess_batch(images)
        
        assert processed.shape[0] == 3
        assert len(metadata_list) == 3


class TestImageQualityAssessor:
    """图像质量评估器测试"""
    
    def test_assessor_creation(self):
        """测试评估器创建"""
        assessor = ImageQualityAssessor()
        
        assert assessor is not None
    
    def test_assess_good_image(self):
        """测试良好图像评估"""
        assessor = ImageQualityAssessor()
        
        # 创建清晰的测试图像
        image = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        
        result = assessor.assess(image)
        
        assert "is_valid" in result
        assert "scores" in result
    
    def test_assess_dark_image(self):
        """测试暗图像评估"""
        assessor = ImageQualityAssessor()
        
        # 创建暗图像
        image = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        
        result = assessor.assess(image)
        
        assert "brightness" in result["scores"]


class TestDataAugmenter:
    """数据增强器测试"""
    
    def test_augmenter_creation(self):
        """测试增强器创建"""
        augmenter = DataAugmenter()
        
        assert augmenter is not None
    
    def test_augment_image(self):
        """测试图像增强"""
        augmenter = DataAugmenter(augment_prob=1.0)
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        augmented = augmenter.augment(image)
        
        assert augmented.shape == image.shape


class TestFeatureVisualizer:
    """特征可视化器测试"""
    
    def test_visualizer_creation(self):
        """测试可视化器创建"""
        visualizer = create_visualizer()
        
        assert visualizer is not None
    
    def test_visualize_feature_maps(self):
        """测试特征图可视化"""
        visualizer = FeatureVisualizer(output_dir="test_outputs")
        
        # 创建测试特征图
        feature_maps = np.random.randn(64, 32, 32).astype(np.float32)
        
        result = visualizer.visualize_feature_maps(
            feature_maps, layer_name="test_layer"
        )
        
        assert result is not None
        assert len(result.shape) == 3


class TestDetectionVisualizer:
    """检测结果可视化器测试"""
    
    def test_detection_visualizer_creation(self):
        """测试检测可视化器创建"""
        visualizer = create_detection_visualizer()
        
        assert visualizer is not None
    
    def test_visualize_detections(self):
        """测试检测结果可视化"""
        visualizer = DetectionVisualizer(output_dir="test_outputs")
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        detections = [
            {
                "name": "Yellow Rust",
                "confidence": 0.85,
                "bbox": [100, 100, 200, 200]
            }
        ]
        
        result = visualizer.visualize_detections(image, detections)
        
        assert result is not None
        assert result.shape[:2] == image.shape[:2]
    
    def test_create_confidence_heatmap(self):
        """测试置信度热力图"""
        visualizer = DetectionVisualizer(output_dir="test_outputs")
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        detections = [
            {
                "name": "Yellow Rust",
                "confidence": 0.85,
                "bbox": [100, 100, 200, 200]
            }
        ]
        
        result = visualizer.create_confidence_heatmap(image, detections)
        
        assert result is not None


class TestMultiScaleDetector:
    """多尺度检测器测试"""
    
    def test_detector_creation(self):
        """测试检测器创建"""
        detector = create_multiscale_detector()
        
        assert detector is not None
        assert detector.config.scales == [0.75, 1.0, 1.25]
    
    def test_multiscale_config(self):
        """测试多尺度配置"""
        config = MultiScaleConfig(
            scales=[0.5, 1.0, 1.5],
            flip=False
        )
        
        detector = MultiScaleDetector(config)
        
        assert detector.config.scales == [0.5, 1.0, 1.5]
        assert detector.config.flip is False
    
    def test_scale_image(self):
        """测试图像缩放"""
        detector = MultiScaleDetector()
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        scaled = detector._scale_image(image, 0.5)
        
        assert scaled.shape[:2] == (240, 320)


class TestSmallObjectEnhancer:
    """小目标增强器测试"""
    
    def test_enhancer_creation(self):
        """测试增强器创建"""
        enhancer = create_small_object_enhancer()
        
        assert enhancer is not None
    
    def test_compute_iou(self):
        """测试IoU计算"""
        enhancer = SmallObjectEnhancer()
        
        box1 = [0, 0, 100, 100]
        box2 = [50, 50, 150, 150]
        
        iou = enhancer._compute_iou(box1, box2)
        
        assert 0 < iou < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
