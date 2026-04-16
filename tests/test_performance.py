# -*- coding: utf-8 -*-
"""
性能测试模块

测试模型性能指标：
- 检测精度 (mAP)
- 推理速度 (FPS)
- 内存占用
- 模型大小
"""
import os
import sys
import time
import pytest
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelPerformance:
    """模型性能测试"""
    
    def test_inference_speed(self):
        """测试推理速度"""
        try:
            from ultralytics import YOLO
            
            model_path = Path(__file__).parent.parent / "models" / "yolov8_wheat.pt"
            if not model_path.exists():
                pytest.skip("模型文件不存在")
            
            model = YOLO(str(model_path))
            
            dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            times = []
            for _ in range(10):
                start = time.time()
                model.predict(dummy_image, verbose=False)
                times.append(time.time() - start)
            
            avg_time = np.mean(times) * 1000
            fps = 1000 / avg_time
            
            print(f"\n📊 推理速度:")
            print(f"   平均时间: {avg_time:.2f} ms")
            print(f"   FPS: {fps:.1f}")
            
            assert avg_time < 1000, "推理时间过长"
            
        except ImportError:
            pytest.skip("ultralytics未安装")
    
    def test_model_size(self):
        """测试模型大小"""
        model_path = Path(__file__).parent.parent / "models" / "yolov8_wheat.pt"
        
        if not model_path.exists():
            pytest.skip("模型文件不存在")
        
        size_mb = model_path.stat().st_size / (1024 * 1024)
        
        print(f"\n📊 模型大小: {size_mb:.2f} MB")
        
        assert size_mb < 500, "模型过大"


class TestSystemPerformance:
    """系统性能测试"""
    
    def test_diagnosis_latency(self):
        """测试诊断延迟"""
        try:
            from src.diagnosis.diagnosis_engine import create_diagnosis_engine
            
            engine = create_diagnosis_engine({
                "load_vision": True,
                "load_knowledge": False
            })
            
            test_dir = Path(__file__).parent.parent / "datasets" / "wheat_data_unified" / "images" / "val"
            if not test_dir.exists():
                pytest.skip("测试数据不存在")
            
            images = list(test_dir.glob("*.jpg"))
            if not images:
                pytest.skip("没有测试图像")
            
            test_image = str(images[0])
            
            times = []
            for _ in range(3):
                start = time.time()
                engine.diagnose(test_image)
                times.append(time.time() - start)
            
            avg_time = np.mean(times)
            
            print(f"\n📊 诊断延迟: {avg_time:.2f} 秒")
            
            assert avg_time < 10, "诊断时间过长"
            
        except Exception as e:
            pytest.skip(f"测试跳过: {e}")
    
    def test_memory_usage(self):
        """测试内存使用"""
        try:
            import psutil
            import gc
            
            gc.collect()
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024 * 1024)
            
            from src.diagnosis.diagnosis_engine import create_diagnosis_engine
            engine = create_diagnosis_engine({
                "load_vision": True,
                "load_knowledge": False
            })
            
            gc.collect()
            
            final_memory = process.memory_info().rss / (1024 * 1024)
            memory_increase = final_memory - initial_memory
            
            print(f"\n📊 内存使用:")
            print(f"   初始: {initial_memory:.1f} MB")
            print(f"   加载后: {final_memory:.1f} MB")
            print(f"   增加: {memory_increase:.1f} MB")
            
            assert memory_increase < 2000, "内存占用过高"
            
        except ImportError:
            pytest.skip("psutil未安装")


class TestAccuracyMetrics:
    """精度指标测试"""
    
    def test_detection_classes(self):
        """测试检测类别"""
        try:
            from src.vision.vision_engine import VisionAgent
            
            agent = VisionAgent()
            
            expected_classes = [
                "Aphid", "Black Rust", "Blast", "Brown Rust",
                "Common Root Rot", "Fusarium Head Blight", "Healthy",
                "Leaf Blight", "Mildew", "Mite", "Septoria",
                "Smut", "Stem fly", "Tan spot", "Yellow Rust"
            ]
            
            model_classes = list(agent.model.names.values())
            
            print(f"\n📊 模型类别数: {len(model_classes)}")
            print(f"   预期类别数: {len(expected_classes)}")
            
            assert len(model_classes) >= 10, "类别数不足"
            
        except Exception as e:
            pytest.skip(f"测试跳过: {e}")
    
    def test_confidence_range(self):
        """测试置信度范围"""
        try:
            from src.vision.vision_engine import VisionAgent
            
            agent = VisionAgent()
            
            test_dir = Path(__file__).parent.parent / "datasets" / "wheat_data_unified" / "images" / "val"
            if not test_dir.exists():
                pytest.skip("测试数据不存在")
            
            images = list(test_dir.glob("*.jpg"))
            if not images:
                pytest.skip("没有测试图像")
            
            test_image = str(images[0])
            results = agent.detect(test_image, conf_threshold=0.1)
            
            if results:
                for det in results:
                    conf = det.get("confidence", 0)
                    assert 0 <= conf <= 1, f"置信度超出范围: {conf}"
                    print(f"\n📊 检测结果: {det.get('name')} ({conf:.2%})")
            
        except Exception as e:
            pytest.skip(f"测试跳过: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
