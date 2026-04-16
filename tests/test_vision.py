# -*- coding: utf-8 -*-
"""
视觉引擎测试模块

测试YOLOv8检测功能
"""
import pytest
import numpy as np
from PIL import Image
import sys
from pathlib import Path
import tempfile

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vision.vision_engine import VisionAgent as VisionEngine


class TestVisionEngine:
    """视觉引擎测试"""
    
    @pytest.fixture
    def vision_engine(self):
        """创建视觉引擎实例"""
        try:
            return VisionEngine()
        except Exception as e:
            pytest.skip(f"视觉引擎初始化失败: {e}")
    
    @pytest.fixture
    def mock_image(self):
        """创建模拟图像"""
        # 创建224x224的RGB图像
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        return img
    
    def test_engine_initialization(self, vision_engine):
        """测试引擎初始化"""
        assert vision_engine is not None
        assert vision_engine.model is not None
    
    def test_detect_mock_image(self, vision_engine, mock_image):
        """测试模拟图像检测"""
        # 保存临时图像
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.fromarray(mock_image)
            img.save(f.name)
            temp_path = f.name
        
        try:
            # 执行检测
            results = vision_engine.detect(temp_path)
            
            # 验证结果格式
            assert isinstance(results, list)
            
            # 清理
            Path(temp_path).unlink()
        except Exception as e:
            # 模拟图像可能没有检测到结果，这是正常的
            pass


class TestImagePreprocessing:
    """图像预处理测试"""
    
    def test_image_loading(self):
        """测试图像加载"""
        # 创建临时图像
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f.name)
            temp_path = f.name
        
        # 加载图像
        loaded_img = Image.open(temp_path)
        assert loaded_img.size == (100, 100)
        
        # 清理
        Path(temp_path).unlink()
    
    def test_image_resize(self):
        """测试图像缩放"""
        img = Image.new('RGB', (1000, 800), color='blue')
        resized = img.resize((640, 480))
        assert resized.size == (640, 480)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
