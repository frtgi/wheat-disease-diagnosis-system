# -*- coding: utf-8 -*-
"""
视觉模块完整测试

测试所有视觉模块功能
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision.postprocessing import (
    NMSProcessor,
    BoxRefiner,
    ConfidenceCalibrator,
    DetectionPostprocessor,
    create_postprocessor
)
from src.vision.analysis import (
    LesionAnalyzer,
    DetectionStatistics,
    AnalysisResult,
    create_lesion_analyzer,
    create_detection_statistics
)


class TestNMSProcessor:
    """NMS处理器测试"""
    
    def test_nms_processor_creation(self):
        """测试NMS处理器创建"""
        processor = NMSProcessor()
        
        assert processor is not None
    
    def test_standard_nms(self):
        """测试标准NMS"""
        processor = NMSProcessor()
        
        boxes = np.array([
            [10, 10, 50, 50],
            [12, 12, 52, 52],
            [100, 100, 150, 150]
        ])
        scores = np.array([0.9, 0.8, 0.7])
        
        keep = processor.nms(boxes, scores)
        
        assert len(keep) == 2
        assert 0 in keep or 1 in keep
        assert 2 in keep
    
    def test_soft_nms(self):
        """测试Soft-NMS"""
        processor = NMSProcessor()
        
        boxes = np.array([
            [10, 10, 50, 50],
            [100, 100, 150, 150]
        ])
        scores = np.array([0.9, 0.8])
        
        keep, new_scores = processor.soft_nms(boxes, scores)
        
        assert len(keep) == 2
    
    def test_class_aware_nms(self):
        """测试类别感知NMS"""
        processor = NMSProcessor()
        
        boxes = np.array([
            [10, 10, 50, 50],
            [12, 12, 52, 52],
            [100, 100, 150, 150]
        ])
        scores = np.array([0.9, 0.8, 0.7])
        classes = np.array([0, 0, 1])
        
        keep = processor.class_aware_nms(boxes, scores, classes)
        
        assert len(keep) == 2


class TestBoxRefiner:
    """边界框精炼器测试"""
    
    def test_box_refiner_creation(self):
        """测试边界框精炼器创建"""
        refiner = BoxRefiner()
        
        assert refiner is not None
    
    def test_refine_boxes(self):
        """测试边界框精炼"""
        refiner = BoxRefiner()
        
        boxes = np.array([
            [-10, -10, 50, 50],
            [100, 100, 300, 300]
        ])
        scores = np.array([0.9, 0.8])
        image_shape = (200, 200)
        
        refined = refiner.refine_boxes(boxes, scores, image_shape)
        
        assert refined[0, 0] == 0
        assert refined[0, 1] == 0
        assert refined[1, 2] == 199
    
    def test_expand_boxes(self):
        """测试边界框扩展"""
        refiner = BoxRefiner()
        
        boxes = np.array([
            [10, 10, 50, 50]
        ])
        
        expanded = refiner.expand_boxes(boxes, scale=1.5)
        
        assert expanded[0, 2] - expanded[0, 0] > 40


class TestConfidenceCalibrator:
    """置信度校准器测试"""
    
    def test_calibrator_creation(self):
        """测试校准器创建"""
        calibrator = ConfidenceCalibrator()
        
        assert calibrator is not None
    
    def test_temperature_scaling(self):
        """测试温度缩放"""
        calibrator = ConfidenceCalibrator(temperature=1.0)
        
        scores = np.array([0.1, 0.5, 0.9])
        
        calibrated = calibrator.calibrate(scores, method="temperature")
        
        assert len(calibrated) == 3
        assert np.all(calibrated >= 0)
        assert np.all(calibrated <= 1)


class TestDetectionPostprocessor:
    """检测后处理器测试"""
    
    def test_postprocessor_creation(self):
        """测试后处理器创建"""
        processor = create_postprocessor()
        
        assert processor is not None
    
    def test_process_detections(self):
        """测试检测结果处理"""
        processor = create_postprocessor()
        
        detections = [
            {"bbox": [10, 10, 50, 50], "confidence": 0.9, "name": "Yellow Rust", "class_id": 0},
            {"bbox": [100, 100, 150, 150], "confidence": 0.8, "name": "Brown Rust", "class_id": 1}
        ]
        image_shape = (200, 200)
        
        results = processor.process(detections, image_shape)
        
        assert len(results) == 2


class TestLesionAnalyzer:
    """病斑分析器测试"""
    
    def test_analyzer_creation(self):
        """测试分析器创建"""
        analyzer = create_lesion_analyzer()
        
        assert analyzer is not None
    
    def test_analyze_empty_detections(self):
        """测试空检测结果分析"""
        analyzer = LesionAnalyzer()
        
        result = analyzer.analyze([], (200, 200))
        
        assert result.total_detections == 0
        assert result.severity == "健康"
    
    def test_analyze_detections(self):
        """测试检测结果分析"""
        analyzer = LesionAnalyzer()
        
        detections = [
            {"bbox": [10, 10, 50, 50], "confidence": 0.9, "name": "Yellow Rust"},
            {"bbox": [100, 100, 150, 150], "confidence": 0.8, "name": "Brown Rust"}
        ]
        image_shape = (200, 200)
        
        result = analyzer.analyze(detections, image_shape)
        
        assert result.total_detections == 2
        assert "Yellow Rust" in result.disease_distribution
        assert len(result.recommendations) > 0
    
    def test_severity_determination(self):
        """测试严重程度确定"""
        analyzer = LesionAnalyzer()
        
        high_coverage_detections = [
            {"bbox": [0, 0, 150, 150], "confidence": 0.9, "name": "Yellow Rust"}
        ]
        
        result = analyzer.analyze(high_coverage_detections, (200, 200))
        
        assert result.severity in ["轻度", "中度", "重度", "严重"]


class TestDetectionStatistics:
    """检测统计器测试"""
    
    def test_statistics_creation(self):
        """测试统计器创建"""
        stats = create_detection_statistics()
        
        assert stats is not None
    
    def test_add_result(self):
        """测试添加结果"""
        stats = DetectionStatistics()
        
        result = AnalysisResult(
            total_detections=2,
            severity="轻度"
        )
        
        stats.add_result(result)
        
        assert len(stats.history) == 1
    
    def test_get_summary(self):
        """测试获取摘要"""
        stats = DetectionStatistics()
        
        result = AnalysisResult(
            total_detections=2,
            coverage_ratio=0.1,
            severity="轻度",
            disease_distribution={"Yellow Rust": 2}
        )
        
        stats.add_result(result)
        
        summary = stats.get_summary()
        
        assert summary["total_images"] == 1
        assert summary["total_detections"] == 2


class TestAnalysisResult:
    """分析结果测试"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = AnalysisResult(
            total_detections=5,
            coverage_ratio=0.15,
            severity="中度"
        )
        
        assert result.total_detections == 5
        assert result.coverage_ratio == 0.15
        assert result.severity == "中度"
    
    def test_result_to_dict(self):
        """测试结果转字典"""
        result = AnalysisResult(
            total_detections=3,
            coverage_ratio=0.1,
            severity="轻度",
            disease_distribution={"Yellow Rust": 2, "Brown Rust": 1}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["total_detections"] == 3
        assert result_dict["severity"] == "轻度"
        assert "Yellow Rust" in result_dict["disease_distribution"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
