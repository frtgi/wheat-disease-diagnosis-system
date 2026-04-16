# -*- coding: utf-8 -*-
"""
用户输入层单元测试
测试 InputParser, InputValidator 和 EnvironmentEncoder 的核心功能
"""
import pytest
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.input.input_parser import InputParser
from src.input.input_validator import InputValidator
from src.input.environment_encoder import EnvironmentEncoder


class TestInputParser:
    """InputParser 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.parser = InputParser(image_size=(224, 224))
    
    def test_input_parser_initialization(self):
        """测试输入解析器初始化"""
        # Arrange & Act
        parser = InputParser()
        
        # Assert
        assert parser is not None
        assert parser.image_size == (224, 224)
    
    def test_parse_image_success(self, tmp_path):
        """测试成功解析图像"""
        # Arrange
        import cv2
        image_path = tmp_path / "test_image.jpg"
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(image_path), test_image)
        
        # Act
        result = self.parser.parse_image(str(image_path))
        
        # Assert
        assert result is not None
        assert "image" in result
        assert "metadata" in result
        assert result["type"] == "image"
    
    def test_parse_image_not_found(self):
        """测试图像文件不存在"""
        # Arrange
        invalid_path = "non_existent_image.jpg"
        
        # Act & Assert
        with pytest.raises(ValueError):
            self.parser.parse_image(invalid_path)
    
    def test_parse_text_success(self):
        """测试成功解析文本"""
        # Arrange
        text = "小麦叶片出现黄色病斑，最近温度 15 度，湿度较高"
        
        # Act
        result = self.parser.parse_text(text)
        
        # Assert
        assert result is not None
        assert "symptoms" in result
        assert "disease_parts" in result
        assert result["type"] == "text"
    
    def test_extract_symptoms(self):
        """测试症状提取"""
        # Arrange
        text = "叶片出现病斑和霉层，有黄色变色现象"
        
        # Act
        symptoms = self.parser._extract_symptoms(text)
        
        # Assert
        assert len(symptoms) > 0
        symptom_categories = [s["category"] for s in symptoms]
        assert "病斑" in symptom_categories or "霉层" in symptom_categories
    
    def test_extract_disease_parts(self):
        """测试发病部位提取"""
        # Arrange
        text = "叶片和叶鞘都有发病症状"
        
        # Act
        parts = self.parser._extract_disease_parts(text)
        
        # Assert
        assert len(parts) > 0
        assert "叶片" in parts
    
    def test_extract_growth_stage(self):
        """测试生长阶段提取"""
        # Arrange
        text = "小麦正处于拔节期"
        
        # Act
        stage = self.parser._extract_growth_stage(text)
        
        # Assert
        assert stage == "拔节期"
    
    def test_extract_severity(self):
        """测试严重程度提取"""
        # Arrange
        severe_text = "病情严重，大面积发病"
        mild_text = "病情轻微，只有几株"
        
        # Act
        severe_result = self.parser._extract_severity(severe_text)
        mild_result = self.parser._extract_severity(mild_text)
        
        # Assert
        assert severe_result == "严重"
        assert mild_result == "轻微"
    
    def test_parse_structured_data(self):
        """测试解析结构化数据"""
        # Arrange
        data = {
            "location": "河南郑州",
            "time": "2026-03-09",
            "weather": {
                "temperature": 15.5,
                "humidity": 75.0
            }
        }
        
        # Act
        result = self.parser.parse_structured_data(data)
        
        # Assert
        assert result is not None
        assert "data" in result
        assert result["type"] == "structured"
    
    def test_parse_multimodal_input(self, tmp_path):
        """测试多模态输入解析"""
        # Arrange
        import cv2
        image_path = tmp_path / "test.jpg"
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(image_path), test_image)
        
        text = "叶片出现病斑"
        structured_data = {"location": "河南", "weather": {"temperature": 15}}
        
        # Act
        result = self.parser.parse_multimodal_input(
            image_path=str(image_path),
            text=text,
            structured_data=structured_data
        )
        
        # Assert
        assert result is not None
        assert "image" in result
        assert "text" in result
        assert "structured" in result
        assert "fused" in result
    
    def test_generate_json_schema(self):
        """测试生成 JSON Schema"""
        # Act
        schema = self.parser.generate_json_schema()
        
        # Assert
        assert schema is not None
        assert "$schema" in schema
        assert "properties" in schema
    
    def test_validate_against_schema(self):
        """测试 Schema 验证"""
        # Arrange
        valid_data = {
            "image": "test.jpg",
            "text": "测试描述"
        }
        invalid_data = {
            "image": 123,  # 应该是字符串
            "text": ""  # 不能为空
        }
        
        # Act
        valid_result, valid_errors = self.parser.validate_against_schema(valid_data)
        invalid_result, invalid_errors = self.parser.validate_against_schema(invalid_data)
        
        # Assert
        assert valid_result is True
        assert invalid_result is False
        assert len(invalid_errors) > 0


class TestInputValidator:
    """InputValidator 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.validator = InputValidator()
    
    def test_input_validator_initialization(self):
        """测试输入验证器初始化"""
        # Arrange & Act
        validator = InputValidator()
        
        # Assert
        assert validator is not None
    
    def test_validate_image_success(self, tmp_path):
        """测试成功验证图像"""
        # Arrange
        import cv2
        image_path = tmp_path / "valid_image.jpg"
        test_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        cv2.imwrite(str(image_path), test_image)
        
        # Act
        result = self.validator.validate_image(str(image_path))
        
        # Assert
        assert result is not None
        assert "valid" in result
        assert "checks" in result
        assert result["valid"] is True
    
    def test_validate_image_not_found(self):
        """测试图像文件不存在"""
        # Arrange
        invalid_path = "non_existent.jpg"
        
        # Act
        result = self.validator.validate_image(invalid_path)
        
        # Assert
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_image_low_resolution(self, tmp_path):
        """测试低分辨率图像"""
        # Arrange
        import cv2
        image_path = tmp_path / "low_res.jpg"
        test_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        cv2.imwrite(str(image_path), test_image)
        
        # Act
        result = self.validator.validate_image(str(image_path))
        
        # Assert
        assert result["checks"]["resolution"]["passed"] is False
    
    def test_check_brightness(self):
        """测试亮度检查"""
        # Arrange
        dark_image = np.ones((100, 100, 3), dtype=np.uint8) * 10  # 很暗
        normal_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # 正常
        
        # Act
        dark_result = self.validator._check_brightness(dark_image)
        normal_result = self.validator._check_brightness(normal_image)
        
        # Assert
        assert bool(dark_result["passed"]) is False
        assert bool(normal_result["passed"]) is True
    
    def test_check_blur(self):
        """测试模糊度检查"""
        # Arrange
        sharp_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Act
        result = self.validator._check_blur(sharp_image)
        
        # Assert
        assert result is not None
        assert "value" in result
        assert "passed" in result
    
    def test_validate_data_completeness(self):
        """测试数据完整性验证"""
        # Arrange
        complete_data = {
            "image_path": "test.jpg",
            "description": "测试描述",
            "location": "河南",
            "time": "2026-03-09"
        }
        incomplete_data = {}
        
        # Act
        complete_result = self.validator.validate_data_completeness(complete_data)
        incomplete_result = self.validator.validate_data_completeness(incomplete_data)
        
        # Assert
        assert complete_result["valid"] is True
        assert incomplete_result["valid"] is False
        assert len(incomplete_result["missing_fields"]) > 0
    
    def test_validate_text(self):
        """测试文本验证"""
        # Arrange
        valid_text = "小麦叶片出现黄色病斑，沿叶脉排列"
        short_text = "病"
        
        # Act
        valid_result = self.validator.validate_text(valid_text)
        short_result = self.validator.validate_text(short_text)
        
        # Assert
        assert valid_result["valid"] is True
        assert valid_result["quality_score"] > 50
        assert short_result["valid"] is False
    
    def test_validate_structured_data(self):
        """测试结构化数据验证"""
        # Arrange
        valid_data = {
            "location": "河南郑州",
            "time": "2026-03-09",
            "weather": {
                "temperature": 15.5,
                "humidity": 75.0
            },
            "growth_stage": "拔节期"
        }
        
        # Act
        result = self.validator.validate_structured_data(valid_data)
        
        # Assert
        assert result["valid"] is True
        assert result["completeness_score"] > 0
    
    def test_get_recovery_suggestions(self):
        """测试获取恢复建议"""
        # Arrange
        validation_result = {
            "components": {
                "image": {
                    "valid": False,
                    "errors": ["文件不存在"]
                }
            },
            "errors": ["图像文件不存在"]
        }
        
        # Act
        recovery = self.validator.get_recovery_suggestions(validation_result)
        
        # Assert
        assert "can_recover" in recovery
        assert "actions" in recovery


class TestEnvironmentEncoder:
    """EnvironmentEncoder 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        self.encoder = EnvironmentEncoder()
    
    def test_environment_encoder_initialization(self):
        """测试环境编码器初始化"""
        # Arrange & Act
        encoder = EnvironmentEncoder()
        
        # Assert
        assert encoder is not None
        assert len(encoder.GROWTH_STAGES) > 0
        assert len(encoder.DISEASE_PARTS) > 0
    
    def test_encode_weather_success(self):
        """测试成功编码天气数据"""
        # Arrange
        weather_data = {
            "temperature": 15.5,
            "humidity": 75.0,
            "precipitation": 5.2,
            "weather_condition": "小雨"
        }
        
        # Act
        result = self.encoder.encode_weather(weather_data)
        
        # Assert
        assert result is not None
        assert "temperature" in result
        assert "humidity" in result
        assert "risk_score" in result
        assert 0 <= result["risk_score"] <= 1
    
    def test_encode_temperature(self):
        """测试温度编码"""
        # Arrange
        test_cases = [
            (5.0, "较低温"),
            (20.0, "适宜"),
            (35.0, "高温")
        ]
        
        # Act & Assert
        for temp, expected_category in test_cases:
            result = self.encoder._encode_temperature(temp)
            assert result["category"] == expected_category
            assert 0 <= result["encoded"] <= 1
    
    def test_encode_humidity(self):
        """测试湿度编码"""
        # Arrange
        test_cases = [
            (30.0, "干燥"),
            (70.0, "适宜"),
            (95.0, "高湿")
        ]
        
        # Act & Assert
        for humidity, expected_category in test_cases:
            result = self.encoder._encode_humidity(humidity)
            assert result["category"] == expected_category
    
    def test_calculate_weather_risk_score(self):
        """测试天气风险评分计算"""
        # Arrange
        encoded_weather = {
            "temperature": {"risk_level": 0.7},
            "humidity": {"risk_level": 0.9},
            "precipitation": {"risk_level": 0.6},
            "weather_condition": {"risk_level": 0.7}
        }
        
        # Act
        risk_score = self.encoder._calculate_weather_risk_score(encoded_weather)
        
        # Assert
        assert 0 <= risk_score <= 1
    
    def test_encode_growth_stage(self):
        """测试生长阶段编码"""
        # Arrange
        stage = "拔节期"
        
        # Act
        result = self.encoder.encode_growth_stage(stage)
        
        # Assert
        assert result["value"] == stage
        assert result["susceptibility"] > 0
        assert len(result["one_hot"]) == len(self.encoder.GROWTH_STAGES)
    
    def test_encode_disease_part(self):
        """测试发病部位编码"""
        # Arrange
        part = "叶片"
        
        # Act
        result = self.encoder.encode_disease_part(part)
        
        # Assert
        assert result["value"] == part
        assert result["weight"] > 0
    
    def test_encode_multiple_disease_parts(self):
        """测试多个发病部位编码"""
        # Arrange
        parts = ["叶片", "叶鞘", "茎秆"]
        
        # Act
        result = self.encoder.encode_multiple_disease_parts(parts)
        
        # Assert
        assert len(result["values"]) == len(parts)
        assert "multi_hot" in result
    
    def test_calculate_environment_risk_score(self):
        """测试综合环境风险评分计算"""
        # Arrange
        weather_data = {
            "temperature": 20.0,
            "humidity": 85.0,
            "precipitation": 10.0,
            "weather_condition": "中雨"
        }
        growth_stage = "抽穗期"
        disease_parts = ["叶片", "叶鞘"]
        
        # Act
        result = self.encoder.calculate_environment_risk_score(
            weather_data, growth_stage, disease_parts
        )
        
        # Assert
        assert "comprehensive_risk" in result
        assert "risk_level" in result
        assert 0 <= result["comprehensive_risk"] <= 1
    
    def test_create_environment_feature_vector(self):
        """测试创建环境特征向量"""
        # Arrange
        weather_data = {
            "temperature": 15.0,
            "humidity": 70.0,
            "precipitation": 0.0,
            "weather_condition": "晴"
        }
        growth_stage = "拔节期"
        disease_parts = ["叶片"]
        
        # Act
        vector = self.encoder.create_environment_feature_vector(
            weather_data, growth_stage, disease_parts
        )
        
        # Assert
        assert isinstance(vector, np.ndarray)
        assert len(vector.shape) == 1
    
    def test_parse_weather_from_text(self):
        """测试从文本解析天气"""
        # Arrange
        text = "温度 15 度，湿度 80%，有小雨"
        
        # Act
        result = self.encoder.parse_weather_from_text(text)
        
        # Assert
        assert "temperature" in result
        assert "humidity" in result
        assert result["temperature"] == 15.0
        assert result["humidity"] == 80.0
    
    def test_get_seasonal_risk_factors(self):
        """测试获取季节性风险因子"""
        # Arrange
        test_months = [
            (1, "冬季"),
            (5, "春季"),
            (8, "夏季"),
            (11, "秋季")
        ]
        
        # Act & Assert
        for month, expected_season in test_months:
            result = self.encoder.get_seasonal_risk_factors(month)
            assert result["name"] == expected_season
            assert "base_risk" in result
            assert "common_diseases" in result
    
    def test_generate_environment_report(self):
        """测试生成环境报告"""
        # Arrange
        weather_data = {
            "temperature": 20.0,
            "humidity": 85.0,
            "precipitation": 5.0,
            "weather_condition": "小雨"
        }
        growth_stage = "抽穗期"
        disease_parts = ["叶片"]
        
        # Act
        report = self.encoder.generate_environment_report(
            weather_data, growth_stage, disease_parts
        )
        
        # Assert
        assert isinstance(report, str)
        assert "环境因素分析报告" in report
        assert "风险评估" in report


def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
