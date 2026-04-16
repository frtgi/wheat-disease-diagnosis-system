# -*- coding: utf-8 -*-
"""
诊断引擎集成测试

测试诊断引擎与视觉模块、知识图谱的完整集成
"""
import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.diagnosis.diagnosis_engine import (
    DiagnosisEngine,
    DiagnosisResult,
    create_diagnosis_engine
)
from src.diagnosis.report_generator import (
    ReportGenerator,
    create_report_generator
)


class TestDiagnosisIntegration:
    """诊断引擎集成测试"""
    
    @pytest.fixture
    def diagnosis_engine(self):
        """创建诊断引擎实例"""
        return create_diagnosis_engine({
            "load_vision": True,
            "load_knowledge": True
        })
    
    @pytest.fixture
    def report_generator(self):
        """创建报告生成器实例"""
        return create_report_generator({
            "title": "小麦病害诊断报告",
            "version": "2.0.0"
        })
    
    @pytest.fixture
    def test_image_path(self):
        """测试图像路径"""
        test_dir = Path(__file__).parent.parent / "datasets" / "wheat_data_unified" / "images" / "val"
        if test_dir.exists():
            images = list(test_dir.glob("*.jpg"))
            if images:
                return str(images[0])
        return None
    
    def test_engine_initialization(self, diagnosis_engine):
        """测试引擎初始化"""
        assert diagnosis_engine is not None
        assert diagnosis_engine.vision_agent is not None
    
    def test_disease_info_completeness(self, diagnosis_engine):
        """测试病害信息完整性"""
        expected_diseases = [
            "Yellow Rust", "Brown Rust", "Black Rust",
            "Mildew", "Fusarium Head Blight", "Aphid", "Mite", "Healthy"
        ]
        
        for disease in expected_diseases:
            assert disease in diagnosis_engine.DISEASE_INFO, f"缺少病害信息: {disease}"
            info = diagnosis_engine.DISEASE_INFO[disease]
            assert "chinese_name" in info
            assert "pathogen" in info
            assert "symptoms" in info
            assert "treatment" in info
    
    def test_vision_perception(self, diagnosis_engine, test_image_path):
        """测试视觉感知"""
        if test_image_path is None:
            pytest.skip("测试图像不存在")
        
        result = diagnosis_engine._vision_perception(test_image_path, 0.25)
        
        assert "label" in result
        assert "confidence" in result
        assert "detections" in result
    
    def test_knowledge_retrieval(self, diagnosis_engine):
        """测试知识检索"""
        result = diagnosis_engine._knowledge_retrieval("Yellow Rust")
        
        assert "disease_info" in result
        assert result["disease_info"]["chinese_name"] == "条锈病"
    
    def test_multimodal_fusion(self, diagnosis_engine):
        """测试多模态融合"""
        vision_result = {
            "label": "Yellow Rust",
            "confidence": 0.85,
            "detections": [{"name": "Yellow Rust", "confidence": 0.85}]
        }
        knowledge_result = {
            "disease_info": diagnosis_engine.DISEASE_INFO["Yellow Rust"],
            "related_entities": [],
            "treatments": []
        }
        
        result = diagnosis_engine._multimodal_fusion(
            vision_result, knowledge_result, "叶片上有黄色条纹"
        )
        
        assert "final_diagnosis" in result
        assert "final_confidence" in result
    
    def test_full_diagnosis(self, diagnosis_engine, test_image_path):
        """测试完整诊断流程"""
        if test_image_path is None:
            pytest.skip("测试图像不存在")
        
        result = diagnosis_engine.diagnose(
            image_path=test_image_path,
            user_description="测试诊断",
            environment_info={"temperature": "15°C"}
        )
        
        assert result is not None
        assert result.disease_name != ""
        assert result.confidence >= 0
        assert len(result.reasoning_log) > 0
    
    def test_report_generation_json(self, report_generator):
        """测试JSON报告生成"""
        diagnosis_result = {
            "diagnosis": {
                "disease_name": "Yellow Rust",
                "confidence": 0.92,
                "severity": "中度",
                "pathogen": "条形柄锈菌",
                "symptoms": ["黄色条状孢子堆"]
            },
            "treatment": {
                "chemical": ["三唑酮"],
                "biological": [],
                "cultural": ["清除病残体"]
            },
            "prevention": ["选用抗病品种"],
            "reasoning_log": []
        }
        
        json_report = report_generator.generate_json(diagnosis_result)
        
        assert "report_info" in json_report
        assert "Yellow Rust" in json_report
    
    def test_report_generation_markdown(self, report_generator):
        """测试Markdown报告生成"""
        diagnosis_result = {
            "diagnosis": {
                "disease_name": "Brown Rust",
                "confidence": 0.85,
                "severity": "轻度",
                "pathogen": "小麦叶锈菌",
                "symptoms": ["橙褐色圆形孢子堆"]
            },
            "treatment": {
                "chemical": ["三唑酮"],
                "biological": [],
                "cultural": ["清除病残体"]
            },
            "prevention": ["选用抗病品种"],
            "reasoning_log": []
        }
        
        md_report = report_generator.generate_markdown(diagnosis_result)
        
        assert "# 小麦病害诊断报告" in md_report
        assert "Brown Rust" in md_report
    
    def test_report_generation_html(self, report_generator):
        """测试HTML报告生成"""
        diagnosis_result = {
            "diagnosis": {
                "disease_name": "Mildew",
                "confidence": 0.78,
                "severity": "中度",
                "pathogen": "禾布氏白粉菌",
                "symptoms": ["白色粉状霉层"]
            },
            "treatment": {
                "chemical": ["三唑酮"],
                "biological": [],
                "cultural": ["合理密植"]
            },
            "prevention": ["选用抗病品种"],
            "reasoning_log": []
        }
        
        html_report = report_generator.generate_html(diagnosis_result)
        
        assert "<!DOCTYPE html>" in html_report
        assert "Mildew" in html_report
    
    def test_diagnosis_history(self, diagnosis_engine):
        """测试诊断历史记录"""
        history = diagnosis_engine.get_history()
        
        assert isinstance(history, list)


class TestEndToEndDiagnosis:
    """端到端诊断测试"""
    
    def test_diagnosis_workflow(self):
        """测试完整诊断工作流"""
        engine = create_diagnosis_engine({
            "load_vision": True,
            "load_knowledge": False
        })
        
        generator = create_report_generator()
        
        test_dir = Path(__file__).parent.parent / "datasets" / "wheat_data_unified" / "images" / "val"
        if not test_dir.exists():
            pytest.skip("测试图像目录不存在")
        
        images = list(test_dir.glob("*.jpg"))
        if not images:
            pytest.skip("没有测试图像")
        
        test_image = str(images[0])
        
        result = engine.diagnose(
            image_path=test_image,
            user_description="端到端测试",
            environment_info={"temperature": "20°C", "humidity": "70%"}
        )
        
        assert result.disease_name != ""
        
        json_report = generator.generate_json(result.to_dict())
        assert "diagnosis" in json_report
        
        md_report = generator.generate_markdown(result.to_dict())
        assert "# 小麦病害诊断报告" in md_report


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
