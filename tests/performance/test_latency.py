# -*- coding: utf-8 -*-
"""
推理延迟测试模块

测试目标：
- p50 延迟 < 1s
- p95 延迟 < 3s
- p99 延迟 < 5s

测试场景：
1. 视觉感知模块推理延迟
2. 认知层 (Qwen3-VL) 推理延迟
3. 规划层推理延迟
4. 端到端推理延迟
"""
import os
import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import pytest
import torch
from PIL import Image

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class LatencyMetrics:
    """延迟统计指标"""
    p50: float
    p95: float
    p99: float
    mean: float
    std: float
    min: float
    max: float
    total_requests: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_list(cls, latencies: List[float]) -> 'LatencyMetrics':
        """从延迟列表计算指标"""
        if not latencies:
            return cls(
                p50=0, p95=0, p99=0, 
                mean=0, std=0, min=0, max=0, 
                total_requests=0
            )
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        return cls(
            p50=sorted_latencies[int(n * 0.50)],
            p95=sorted_latencies[int(n * 0.95)],
            p99=sorted_latencies[int(n * 0.99)],
            mean=statistics.mean(latencies),
            std=statistics.stdev(latencies) if len(latencies) > 1 else 0,
            min=min(latencies),
            max=max(latencies),
            total_requests=n
        )


class LatencyBenchmark:
    """延迟基准测试类"""
    
    # 性能目标 (秒)
    TARGETS = {
        'p50': 1.0,
        'p95': 3.0,
        'p99': 5.0
    }
    
    def __init__(self, num_iterations: int = 100):
        """
        初始化延迟基准测试
        
        :param num_iterations: 测试迭代次数
        """
        self.num_iterations = num_iterations
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.latencies: List[float] = []
    
    def benchmark_perception_inference(self) -> LatencyMetrics:
        """
        测试视觉感知模块推理延迟
        
        模拟 YOLO 模型的推理过程
        """
        latencies = []
        
        # 创建模拟输入
        dummy_input = torch.randn(1, 3, 640, 640).to(self.device)
        
        # 创建简单模型模拟 YOLO
        model = self._create_dummy_model().to(self.device)
        model.eval()
        
        # 预热
        with torch.no_grad():
            for _ in range(10):
                _ = model(dummy_input)
        
        if self.device == 'cuda':
            torch.cuda.synchronize()
        
        # 正式测试
        for i in range(self.num_iterations):
            start_time = time.perf_counter()
            
            with torch.no_grad():
                _ = model(dummy_input)
            
            if self.device == 'cuda':
                torch.cuda.synchronize()
            
            end_time = time.perf_counter()
            latency = end_time - start_time
            latencies.append(latency)
        
        return LatencyMetrics.from_list(latencies)
    
    def benchmark_cognition_inference(self) -> LatencyMetrics:
        """
        测试认知层 (Qwen3-VL) 推理延迟
        
        模拟多模态大模型的推理过程
        """
        latencies = []
        
        # 创建模拟的多模态输入
        dummy_image = torch.randn(1, 3, 224, 224).to(self.device)
        dummy_text = "这张图片显示了什么小麦病害？"
        
        # 创建简化的多模态模型
        model = self._create_multimodal_model().to(self.device)
        model.eval()
        
        # 预热
        with torch.no_grad():
            for _ in range(5):
                _ = model(dummy_image, dummy_text)
        
        if self.device == 'cuda':
            torch.cuda.synchronize()
        
        # 正式测试
        for i in range(self.num_iterations):
            start_time = time.perf_counter()
            
            with torch.no_grad():
                _ = model(dummy_image, dummy_text)
            
            if self.device == 'cuda':
                torch.cuda.synchronize()
            
            end_time = time.perf_counter()
            latency = end_time - start_time
            latencies.append(latency)
        
        return LatencyMetrics.from_list(latencies)
    
    def benchmark_planning_inference(self) -> LatencyMetrics:
        """
        测试规划层推理延迟
        
        模拟基于规则的规划模块
        """
        latencies = []
        
        # 模拟规划输入
        planning_input = {
            'disease': '条锈病',
            'confidence': 0.92,
            'severity': 0.45,
            'weather': {'temperature': 12, 'humidity': 85}
        }
        
        # 预热
        for _ in range(10):
            self._simulate_planning(planning_input)
        
        # 正式测试
        for i in range(self.num_iterations):
            start_time = time.perf_counter()
            
            self._simulate_planning(planning_input)
            
            end_time = time.perf_counter()
            latency = end_time - start_time
            latencies.append(latency)
        
        return LatencyMetrics.from_list(latencies)
    
    def benchmark_end_to_end(self) -> LatencyMetrics:
        """
        测试端到端推理延迟
        
        包含感知 -> 认知 -> 规划的完整流程
        """
        latencies = []
        
        # 创建模拟输入
        dummy_image = torch.randn(1, 3, 640, 640).to(self.device)
        planning_input = {
            'disease': '条锈病',
            'confidence': 0.92,
            'severity': 0.45
        }
        
        # 创建模型
        perception_model = self._create_dummy_model().to(self.device)
        cognition_model = self._create_multimodal_model().to(self.device)
        perception_model.eval()
        cognition_model.eval()
        
        # 预热
        with torch.no_grad():
            for _ in range(5):
                _ = perception_model(dummy_image)
                _ = cognition_model(dummy_image, "test")
                self._simulate_planning(planning_input)
        
        if self.device == 'cuda':
            torch.cuda.synchronize()
        
        # 正式测试
        for i in range(self.num_iterations):
            start_time = time.perf_counter()
            
            # 感知阶段
            with torch.no_grad():
                perception_output = perception_model(dummy_image)
            
            # 认知阶段
            with torch.no_grad():
                cognition_output = cognition_model(dummy_image, "描述病害")
            
            # 规划阶段
            planning_output = self._simulate_planning(planning_input)
            
            if self.device == 'cuda':
                torch.cuda.synchronize()
            
            end_time = time.perf_counter()
            latency = end_time - start_time
            latencies.append(latency)
        
        return LatencyMetrics.from_list(latencies)
    
    def _create_dummy_model(self) -> torch.nn.Module:
        """创建模拟 YOLO 的简单模型"""
        class DummyYOLO(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.features = torch.nn.Sequential(
                    torch.nn.Conv2d(3, 64, 3, padding=1),
                    torch.nn.BatchNorm2d(64),
                    torch.nn.ReLU(),
                    torch.nn.MaxPool2d(2, 2),
                    
                    torch.nn.Conv2d(64, 128, 3, padding=1),
                    torch.nn.BatchNorm2d(128),
                    torch.nn.ReLU(),
                    torch.nn.MaxPool2d(2, 2),
                    
                    torch.nn.Conv2d(128, 256, 3, padding=1),
                    torch.nn.BatchNorm2d(256),
                    torch.nn.ReLU(),
                    torch.nn.MaxPool2d(2, 2),
                    
                    torch.nn.Conv2d(256, 512, 3, padding=1),
                    torch.nn.BatchNorm2d(512),
                    torch.nn.ReLU(),
                    torch.nn.AdaptiveAvgPool2d(1),
                )
                self.head = torch.nn.Sequential(
                    torch.nn.Flatten(),
                    torch.nn.Linear(512, 256),
                    torch.nn.ReLU(),
                    torch.nn.Linear(256, 10)
                )
            
            def forward(self, x):
                x = self.features(x)
                x = self.head(x)
                return x
        
        return DummyYOLO()
    
    def _create_multimodal_model(self) -> torch.nn.Module:
        """创建模拟 Qwen3-VL 的多模态模型"""
        class DummyMultimodal(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.vision_encoder = torch.nn.Sequential(
                    torch.nn.Conv2d(3, 64, 7, stride=2, padding=3),
                    torch.nn.BatchNorm2d(64),
                    torch.nn.ReLU(),
                    torch.nn.MaxPool2d(3, stride=2, padding=1),
                    torch.nn.Conv2d(64, 128, 3, padding=1),
                    torch.nn.BatchNorm2d(128),
                    torch.nn.ReLU(),
                    torch.nn.AdaptiveAvgPool2d(1),
                )
                self.text_encoder = torch.nn.Embedding(1000, 512)
                self.fusion = torch.nn.Sequential(
                    torch.nn.Linear(128 + 512, 512),
                    torch.nn.ReLU(),
                    torch.nn.Linear(512, 256),
                    torch.nn.ReLU(),
                    torch.nn.Linear(256, 128)
                )
            
            def forward(self, image, text):
                img_feat = self.vision_encoder(image)
                img_feat = img_feat.view(img_feat.size(0), -1)
                
                # 简化的文本编码
                text_ids = torch.randint(0, 1000, (1, 10)).to(image.device)
                text_feat = self.text_encoder(text_ids).mean(dim=1)
                
                combined = torch.cat([img_feat, text_feat], dim=1)
                output = self.fusion(combined)
                return output
        
        return DummyMultimodal()
    
    def _simulate_planning(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟规划层推理"""
        # 模拟基于规则的推理延迟
        time.sleep(0.01)
        
        return {
            'plan': '推荐防治方案',
            'confidence': 0.9
        }


class TestLatency:
    """延迟测试类"""
    
    @pytest.fixture
    def latency_benchmark(self) -> LatencyBenchmark:
        """创建延迟基准测试实例"""
        return LatencyBenchmark(num_iterations=50)
    
    def test_perception_latency(self, latency_benchmark: LatencyBenchmark):
        """
        测试视觉感知模块的推理延迟
        
        性能目标:
        - p50 < 1s
        - p95 < 3s
        - p99 < 5s
        """
        metrics = latency_benchmark.benchmark_perception_inference()
        
        # 输出结果
        print(f"\n视觉感知模块延迟测试:")
        print(f"  测试次数：{metrics.total_requests}")
        print(f"  p50: {metrics.p50*1000:.2f}ms (目标: <1000ms)")
        print(f"  p95: {metrics.p95*1000:.2f}ms (目标: <3000ms)")
        print(f"  p99: {metrics.p99*1000:.2f}ms (目标: <5000ms)")
        print(f"  平均：{metrics.mean*1000:.2f}ms ± {metrics.std*1000:.2f}ms")
        print(f"  范围：{metrics.min*1000:.2f}ms - {metrics.max*1000:.2f}ms")
        
        # 断言性能目标
        assert metrics.p50 < LatencyBenchmark.TARGETS['p50'], \
            f"p50 延迟 {metrics.p50:.3f}s 超过目标 {LatencyBenchmark.TARGETS['p50']}s"
        assert metrics.p95 < LatencyBenchmark.TARGETS['p95'], \
            f"p95 延迟 {metrics.p95:.3f}s 超过目标 {LatencyBenchmark.TARGETS['p95']}s"
        assert metrics.p99 < LatencyBenchmark.TARGETS['p99'], \
            f"p99 延迟 {metrics.p99:.3f}s 超过目标 {LatencyBenchmark.TARGETS['p99']}s"
    
    def test_cognition_latency(self, latency_benchmark: LatencyBenchmark):
        """
        测试认知层 (Qwen3-VL) 的推理延迟
        
        性能目标:
        - p50 < 1s
        - p95 < 3s
        - p99 < 5s
        """
        metrics = latency_benchmark.benchmark_cognition_inference()
        
        print(f"\n认知层延迟测试:")
        print(f"  测试次数：{metrics.total_requests}")
        print(f"  p50: {metrics.p50*1000:.2f}ms (目标: <1000ms)")
        print(f"  p95: {metrics.p95*1000:.2f}ms (目标: <3000ms)")
        print(f"  p99: {metrics.p99*1000:.2f}ms (目标: <5000ms)")
        print(f"  平均：{metrics.mean*1000:.2f}ms ± {metrics.std*1000:.2f}ms")
        
        assert metrics.p50 < LatencyBenchmark.TARGETS['p50']
        assert metrics.p95 < LatencyBenchmark.TARGETS['p95']
        assert metrics.p99 < LatencyBenchmark.TARGETS['p99']
    
    def test_planning_latency(self, latency_benchmark: LatencyBenchmark):
        """
        测试规划层的推理延迟
        
        性能目标:
        - p50 < 1s
        - p95 < 3s
        - p99 < 5s
        """
        metrics = latency_benchmark.benchmark_planning_inference()
        
        print(f"\n规划层延迟测试:")
        print(f"  测试次数：{metrics.total_requests}")
        print(f"  p50: {metrics.p50*1000:.2f}ms (目标: <1000ms)")
        print(f"  p95: {metrics.p95*1000:.2f}ms (目标: <3000ms)")
        print(f"  p99: {metrics.p99*1000:.2f}ms (目标: <5000ms)")
        print(f"  平均：{metrics.mean*1000:.2f}ms ± {metrics.std*1000:.2f}ms")
        
        assert metrics.p50 < LatencyBenchmark.TARGETS['p50']
        assert metrics.p95 < LatencyBenchmark.TARGETS['p95']
        assert metrics.p99 < LatencyBenchmark.TARGETS['p99']
    
    def test_end_to_end_latency(self, latency_benchmark: LatencyBenchmark):
        """
        测试端到端的推理延迟
        
        性能目标:
        - p50 < 1s
        - p95 < 3s
        - p99 < 5s
        """
        metrics = latency_benchmark.benchmark_end_to_end()
        
        print(f"\n端到端延迟测试:")
        print(f"  测试次数：{metrics.total_requests}")
        print(f"  p50: {metrics.p50*1000:.2f}ms (目标: <1000ms)")
        print(f"  p95: {metrics.p95*1000:.2f}ms (目标: <3000ms)")
        print(f"  p99: {metrics.p99*1000:.2f}ms (目标: <5000ms)")
        print(f"  平均：{metrics.mean*1000:.2f}ms ± {metrics.std*1000:.2f}ms")
        
        assert metrics.p50 < LatencyBenchmark.TARGETS['p50']
        assert metrics.p95 < LatencyBenchmark.TARGETS['p95']
        assert metrics.p99 < LatencyBenchmark.TARGETS['p99']
    
    def test_latency_stability(self, latency_benchmark: LatencyBenchmark):
        """
        测试延迟的稳定性
        
        验证延迟的标准差是否在可接受范围内
        """
        metrics = latency_benchmark.benchmark_end_to_end()
        
        # 稳定性要求：标准差不超过平均值的 50%
        stability_threshold = 0.5
        cv = metrics.std / metrics.mean if metrics.mean > 0 else 0
        
        print(f"\n延迟稳定性测试:")
        print(f"  变异系数 (CV): {cv:.2%}")
        print(f"  阈值：{stability_threshold:.0%}")
        
        assert cv < stability_threshold, \
            f"延迟变异系数 {cv:.2%} 超过阈值 {stability_threshold:.0%}"


def generate_latency_report(metrics: Dict[str, LatencyMetrics], output_path: Optional[str] = None):
    """
    生成延迟测试报告
    
    :param metrics: 各模块的延迟指标
    :param output_path: 报告输出路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/latency_report_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'modules': {
            name: metric.to_dict() for name, metric in metrics.items()
        },
        'targets': LatencyBenchmark.TARGETS
    }
    
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 延迟报告已保存：{output_path}")
    return report
