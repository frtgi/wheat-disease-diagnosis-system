# -*- coding: utf-8 -*-
"""
IWDDA Agent 单元测试套件
测试配置和全局 fixture
"""
import pytest
import sys
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "mock: marks tests that use mock services"
    )


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root_fixture():
    """项目根目录 fixture"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root_fixture):
    """测试数据目录"""
    data_dir = project_root_fixture / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_dir():
    """临时目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env():
    """Mock 环境变量"""
    env_vars = {
        "WHEATAGENT_MOCK_AI": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15",
        "LOG_LEVEL": "DEBUG"
    }
    original = {}
    for key, value in env_vars.items():
        original[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env_vars
    
    for key, value in original.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def sample_cognition_output():
    """模拟认知层输出"""
    return {
        "disease_name": "条锈病",
        "confidence": 0.92,
        "severity_score": 0.45,
        "visual_features": [
            "叶片出现黄色条状孢子堆",
            "沿叶脉排列",
            "叶片褪绿"
        ],
        "environmental_conditions": {
            "temperature": "12°C",
            "humidity": "高湿"
        },
        "userDescription": "叶片有黄色条纹，最近下雨"
    }


@pytest.fixture
def sample_diagnosis_plan():
    """模拟诊断计划"""
    return {
        "病害诊断": {
            "病害名称": "条锈病",
            "置信度": 0.92,
            "主要特征": ["黄色条状孢子堆", "沿叶脉排列"]
        },
        "严重度评估": {
            "严重度等级": "中度",
            "严重度评分": 0.45,
            "影响评估": "病斑中等，对产量有一定影响"
        },
        "风险等级": {
            "风险等级": "中风险",
            "风险评分": 0.55,
            "传播速度": "较快"
        },
        "防治措施": {
            "推荐药剂": [
                {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"}
            ],
            "防治步骤": [
                "立即喷施治疗性杀菌剂",
                "7-10 天后复查并补喷",
                "清除严重病株，减少菌源"
            ]
        },
        "复查计划": {
            "复查时间": "2026-03-16",
            "复查间隔": "7 天",
            "紧急程度": "重要",
            "复查内容": [
                "拍摄田间照片",
                "描述病情变化",
                "记录防治措施"
            ]
        }
    }


@pytest.fixture
def sample_image_data(test_data_dir):
    """创建测试图像"""
    import numpy as np
    image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    image_path = test_data_dir / "test_image.jpg"
    import cv2
    cv2.imwrite(str(image_path), image)
    return str(image_path)


@pytest.fixture
def sample_text_description():
    """模拟文本描述"""
    return "小麦叶片出现黄色条状病斑，沿叶脉排列，最近气温 12 度，湿度较高，有降雨"


@pytest.fixture
def sample_weather_data():
    """模拟天气数据"""
    return {
        "temperature": 12.5,
        "humidity": 85.0,
        "precipitation": 5.2,
        "weather_condition": "小雨"
    }


@pytest.fixture
def mock_diagnosis_service():
    """Mock 诊断服务实例"""
    from tests.mocks.diagnosis_mock import MockDiagnosisService
    return MockDiagnosisService()


@pytest.fixture
def mock_qwen_service():
    """Mock Qwen 服务"""
    mock = MagicMock()
    mock.is_loaded = False
    mock.diagnose.return_value = {
        "success": True,
        "diagnosis": {
            "disease_name": "条锈病",
            "confidence": 0.92,
            "symptoms": "叶片出现黄色条状孢子堆",
            "prevention_methods": "选用抗病品种",
            "treatment_methods": "喷洒三唑酮",
            "severity": "中等"
        },
        "model": "mock_qwen"
    }
    mock.get_model_info.return_value = {
        "model_type": "mock_qwen",
        "is_loaded": False
    }
    return mock


@pytest.fixture
def mock_yolo_service():
    """Mock YOLO 服务"""
    mock = MagicMock()
    mock.detect.return_value = {
        "success": True,
        "detections": [
            {
                "class_name": "条锈病",
                "confidence": 0.92,
                "box": [100, 100, 200, 200]
            }
        ],
        "count": 1
    }
    mock.get_model_info.return_value = {
        "model_type": "mock_yolo",
        "is_loaded": False
    }
    return mock


@pytest.fixture
def mock_cache_manager():
    """Mock 缓存管理器"""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.get_stats.return_value = {
        "hits": 0,
        "misses": 0,
        "size": 0
    }
    return mock


@pytest.fixture
def sample_fusion_request():
    """融合诊断请求样例"""
    return {
        "symptoms": "叶片出现黄色条状病斑",
        "weather": "阴雨",
        "growth_stage": "拔节期",
        "affected_part": "叶片",
        "enable_thinking": True,
        "use_graph_rag": True,
        "use_cache": False
    }


@pytest.fixture
def sample_fusion_response():
    """融合诊断响应样例"""
    return {
        "success": True,
        "diagnosis": {
            "disease_name": "条锈病",
            "confidence": 0.92,
            "visual_confidence": 0.90,
            "textual_confidence": 0.88,
            "knowledge_confidence": 0.95,
            "description": "小麦条锈病是由条形柄锈菌引起的真菌病害",
            "recommendations": [
                "喷洒 15% 三唑酮可湿性粉剂 1000 倍液",
                "加强田间管理，及时排水"
            ]
        },
        "model": "fusion_engine",
        "performance": {
            "inference_time_ms": 150.5
        }
    }


@pytest.fixture
def api_client():
    """FastAPI 测试客户端"""
    from fastapi.testclient import TestClient
    try:
        from app.main import app
        with TestClient(app) as client:
            yield client
    except ImportError:
        yield None


@pytest.fixture
async def async_api_client():
    """异步 API 测试客户端"""
    from httpx import AsyncClient
    try:
        from app.main import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    except ImportError:
        yield None


@pytest.fixture
def health_check_response():
    """健康检查响应样例"""
    return {
        "status": "healthy",
        "mock_mode": False,
        "services": {
            "yolov8": {
                "model_type": "yolov8",
                "is_loaded": True
            },
            "qwen3vl": {
                "model_type": "Qwen3-VL-4B-Instruct",
                "is_loaded": True
            }
        }
    }


@pytest.fixture
def mock_health_check_response():
    """Mock 模式健康检查响应样例"""
    return {
        "status": "mock",
        "mock_mode": True,
        "message": "AI 服务不可用，使用 Mock 模式",
        "services": {
            "mock": {
                "status": "active",
                "model": "mock_service",
                "capabilities": ["text_diagnosis", "image_diagnosis"]
            }
        }
    }
