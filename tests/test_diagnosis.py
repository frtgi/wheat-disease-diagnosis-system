# -*- coding: utf-8 -*-
"""
诊断模块测试

测试诊断引擎和报告生成器
"""
import os
import sys
import json
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
    ReportTemplate,
    create_report_generator
)


class TestDiagnosisResult:
    """诊断结果测试"""
    
    def test_diagnosis_result_creation(self):
        """测试诊断结果创建"""
        result = DiagnosisResult(
            disease_name="Yellow Rust",
            confidence=0.92,
            symptoms=["黄色条状孢子堆", "沿叶脉排列"],
            pathogen="条形柄锈菌",
            severity="中度"
        )
        
        assert result.disease_name == "Yellow Rust"
        assert result.confidence == 0.92
        assert len(result.symptoms) == 2
        assert result.pathogen == "条形柄锈菌"
        assert result.severity == "中度"
    
    def test_diagnosis_result_to_dict(self):
        """测试转换为字典"""
        result = DiagnosisResult(
            disease_name="Brown Rust",
            confidence=0.85
        )
        
        result_dict = result.to_dict()
        
        assert "diagnosis" in result_dict
        assert result_dict["diagnosis"]["disease_name"] == "Brown Rust"
        assert result_dict["diagnosis"]["confidence"] == 0.85
    
    def test_diagnosis_result_to_json(self):
        """测试转换为JSON"""
        result = DiagnosisResult(
            disease_name="Mildew",
            confidence=0.78
        )
        
        json_str = result.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["diagnosis"]["disease_name"] == "Mildew"


class TestDiagnosisEngine:
    """诊断引擎测试"""
    
    def test_engine_creation(self):
        """测试引擎创建"""
        engine = DiagnosisEngine()
        
        assert engine is not None
        assert engine.diagnosis_history == []
    
    def test_disease_info_exists(self):
        """测试病害信息存在"""
        engine = DiagnosisEngine()
        
        assert "Yellow Rust" in engine.DISEASE_INFO
        assert "Brown Rust" in engine.DISEASE_INFO
        assert "Mildew" in engine.DISEASE_INFO
        assert "Aphid" in engine.DISEASE_INFO
    
    def test_disease_info_content(self):
        """测试病害信息内容"""
        engine = DiagnosisEngine()
        
        yellow_rust = engine.DISEASE_INFO["Yellow Rust"]
        
        assert "chinese_name" in yellow_rust
        assert "pathogen" in yellow_rust
        assert "symptoms" in yellow_rust
        assert "treatment" in yellow_rust
        assert "prevention" in yellow_rust
    
    def test_severity_levels(self):
        """测试严重程度级别"""
        engine = DiagnosisEngine()
        
        assert "轻度" in engine.SEVERITY_LEVELS
        assert "中度" in engine.SEVERITY_LEVELS
        assert "重度" in engine.SEVERITY_LEVELS
    
    def test_knowledge_retrieval(self):
        """测试知识检索"""
        engine = DiagnosisEngine()
        
        result = engine._knowledge_retrieval("Yellow Rust")
        
        assert "disease_info" in result
        assert result["disease_info"]["chinese_name"] == "条锈病"
    
    def test_get_history(self):
        """测试获取历史"""
        engine = DiagnosisEngine()
        
        history = engine.get_history()
        
        assert isinstance(history, list)


class TestReportGenerator:
    """报告生成器测试"""
    
    def test_generator_creation(self):
        """测试生成器创建"""
        generator = ReportGenerator()
        
        assert generator is not None
        assert generator.template is not None
    
    def test_generate_json(self):
        """测试生成JSON报告"""
        generator = ReportGenerator()
        
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
            "reasoning_log": ["测试日志"]
        }
        
        json_report = generator.generate_json(diagnosis_result)
        parsed = json.loads(json_report)
        
        assert "report_info" in parsed
        assert parsed["diagnosis"]["disease_name"] == "Yellow Rust"
    
    def test_generate_markdown(self):
        """测试生成Markdown报告"""
        generator = ReportGenerator()
        
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
        
        md_report = generator.generate_markdown(diagnosis_result)
        
        assert "# 小麦病害诊断报告" in md_report
        assert "Brown Rust" in md_report
        assert "85.00%" in md_report
    
    def test_generate_html(self):
        """测试生成HTML报告"""
        generator = ReportGenerator()
        
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
        
        html_report = generator.generate_html(diagnosis_result)
        
        assert "<!DOCTYPE html>" in html_report
        assert "Mildew" in html_report
        assert "78.00%" in html_report


class TestFactoryFunctions:
    """工厂函数测试"""
    
    def test_create_diagnosis_engine(self):
        """测试创建诊断引擎"""
        engine = create_diagnosis_engine({"load_vision": False, "load_knowledge": False})
        
        assert engine is not None
        assert isinstance(engine, DiagnosisEngine)
    
    def test_create_report_generator(self):
        """测试创建报告生成器"""
        generator = create_report_generator({
            "title": "测试报告",
            "version": "1.0.0"
        })
        
        assert generator is not None
        assert generator.template.title == "测试报告"
        assert generator.template.version == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
