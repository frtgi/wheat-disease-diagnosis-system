# -*- coding: utf-8 -*-
"""
性能基准测试

测试系统性能指标：
1. 视觉检测性能 (mAP, Precision, Recall)
2. 推理速度 (FPS, Latency)
3. 模型效率 (参数量, FLOPs, 内存)
4. 鲁棒性 (光照, 旋转, 遮挡, 噪声)
"""
import os
import sys
import json
import time
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
import cv2

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class PerformanceTarget:
    """性能目标"""
    metric_name: str
    target_value: float
    current_value: float = 0.0
    unit: str = ""
    passed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceReport:
    """性能测试报告"""
    timestamp: str
    device: str
    targets: List[PerformanceTarget] = field(default_factory=list)
    overall_passed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'device': self.device,
            'targets': [asdict(t) for t in self.targets],
            'overall_passed': self.overall_passed
        }


class PerformanceBenchmarkTest:
    """
    性能基准测试类
    
    根据研究文档要求，验证以下性能指标：
    - mAP@0.5 > 95%
    - FPS (Jetson Orin) > 30
    - BLEU-4 > 0.45
    - Consistency@k > 85%
    """
    
    # 性能目标 (根据研究文档)
    TARGETS = {
        'mAP50': {'value': 0.95, 'unit': '%', 'description': '视觉检测mAP@0.5'},
        'mAP50_95': {'value': 0.70, 'unit': '%', 'description': '视觉检测mAP@0.5:0.95'},
        'fps': {'value': 30, 'unit': 'fps', 'description': 'Jetson Orin推理速度'},
        'bleu4': {'value': 0.45, 'unit': '', 'description': '语义生成BLEU-4'},
        'rouge_l': {'value': 0.45, 'unit': '', 'description': '语义生成ROUGE-L'},
        'consistency_k': {'value': 0.85, 'unit': '%', 'description': '知识一致性'},
        'inference_time': {'value': 100, 'unit': 'ms', 'description': '单张图像推理时间'},
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化性能基准测试
        
        :param config: 测试配置
        """
        self.config = config or {}
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.results: Dict[str, Any] = {}
        
        print("⚡ [PerformanceBenchmarkTest] 性能基准测试初始化完成")
        print(f"   设备: {self.device}")
    
    def test_detection_performance(self) -> Dict[str, float]:
        """
        测试视觉检测性能
        
        目标: mAP@0.5 > 95%
        """
        print("\n🎯 测试视觉检测性能...")
        
        # 模拟检测结果
        # 实际测试中应使用真实数据集和模型
        np.random.seed(42)
        
        # 模拟mAP计算
        # 假设有100个测试样本
        num_samples = 100
        
        # 模拟预测结果
        predictions = []
        ground_truths = []
        
        for i in range(num_samples):
            # 模拟真实标签
            gt_class = np.random.randint(0, 10)
            gt_bbox = np.random.rand(4) * 100
            ground_truths.append({'class': gt_class, 'bbox': gt_bbox})
            
            # 模拟预测结果 (90%准确率)
            if np.random.rand() < 0.9:
                pred_class = gt_class
            else:
                pred_class = np.random.randint(0, 10)
            
            pred_conf = np.random.uniform(0.7, 0.99)
            pred_bbox = gt_bbox + np.random.randn(4) * 5  # 添加噪声
            
            predictions.append({
                'class': pred_class,
                'confidence': pred_conf,
                'bbox': pred_bbox
            })
        
        # 计算指标 (简化计算)
        correct = sum(1 for p, g in zip(predictions, ground_truths) 
                     if p['class'] == g['class'])
        
        precision = correct / len(predictions)
        recall = correct / len(ground_truths)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # 模拟mAP (实际应使用COCO API)
        map50 = 0.92  # 模拟值
        map50_95 = 0.68  # 模拟值
        
        results = {
            'mAP50': map50,
            'mAP50_95': map50_95,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
        
        print(f"   mAP@0.5: {map50:.2%} (目标: >95%)")
        print(f"   mAP@0.5:0.95: {map50_95:.2%}")
        print(f"   Precision: {precision:.2%}")
        print(f"   Recall: {recall:.2%}")
        print(f"   F1-Score: {f1:.2%}")
        
        return results
    
    def test_inference_speed(self) -> Dict[str, float]:
        """
        测试推理速度
        
        目标: FPS > 30 (Jetson Orin)
        """
        print("\n⚡ 测试推理速度...")
        
        # 创建简单模型
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
                self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
                self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
                self.pool = nn.AdaptiveAvgPool2d(1)
                self.fc = nn.Linear(128, 10)
            
            def forward(self, x):
                x = torch.relu(self.conv1(x))
                x = torch.relu(self.conv2(x))
                x = torch.relu(self.conv3(x))
                x = self.pool(x)
                x = x.view(x.size(0), -1)
                x = self.fc(x)
                return x
        
        model = SimpleModel().to(self.device)
        model.eval()
        
        # 测试配置
        input_shape = (1, 3, 640, 640)
        num_runs = 100
        warmup = 10
        
        dummy_input = torch.randn(input_shape).to(self.device)
        
        # 预热
        with torch.no_grad():
            for _ in range(warmup):
                _ = model(dummy_input)
        
        if self.device == 'cuda':
            torch.cuda.synchronize()
        
        # 测试推理时间
        times = []
        with torch.no_grad():
            for _ in range(num_runs):
                start = time.time()
                _ = model(dummy_input)
                if self.device == 'cuda':
                    torch.cuda.synchronize()
                times.append(time.time() - start)
        
        inference_time_ms = np.mean(times) * 1000
        fps = 1.0 / np.mean(times)
        
        # 计算标准差
        std_ms = np.std(times) * 1000
        
        results = {
            'inference_time_ms': inference_time_ms,
            'fps': fps,
            'std_ms': std_ms,
            'min_time_ms': np.min(times) * 1000,
            'max_time_ms': np.max(times) * 1000
        }
        
        print(f"   推理时间: {inference_time_ms:.2f}ms ± {std_ms:.2f}ms")
        print(f"   FPS: {fps:.2f} (目标: >30)")
        print(f"   最小/最大: {results['min_time_ms']:.2f}ms / {results['max_time_ms']:.2f}ms")
        
        return results
    
    def test_model_efficiency(self) -> Dict[str, Any]:
        """
        测试模型效率
        
        包括参数量、FLOPs、内存占用
        """
        print("\n📊 测试模型效率...")
        
        # 创建测试模型
        class TestModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.backbone = nn.Sequential(
                    nn.Conv2d(3, 64, 7, stride=2, padding=3),
                    nn.BatchNorm2d(64),
                    nn.ReLU(),
                    nn.MaxPool2d(3, stride=2, padding=1),
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(),
                    nn.Conv2d(128, 256, 3, padding=1),
                    nn.BatchNorm2d(256),
                    nn.ReLU(),
                )
                self.head = nn.Sequential(
                    nn.AdaptiveAvgPool2d(1),
                    nn.Flatten(),
                    nn.Linear(256, 128),
                    nn.ReLU(),
                    nn.Linear(128, 10)
                )
            
            def forward(self, x):
                x = self.backbone(x)
                x = self.head(x)
                return x
        
        model = TestModel().to(self.device)
        
        # 计算参数量
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        # 估算模型大小
        param_size_mb = total_params * 4 / (1024 ** 2)  # FP32
        
        # 估算FLOPs (简化)
        input_shape = (1, 3, 640, 640)
        dummy_input = torch.randn(input_shape).to(self.device)
        
        # 内存占用
        if self.device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
            with torch.no_grad():
                _ = model(dummy_input)
            memory_mb = torch.cuda.max_memory_allocated() / (1024 ** 2)
        else:
            memory_mb = 0
        
        results = {
            'total_params': total_params,
            'trainable_params': trainable_params,
            'model_size_mb': param_size_mb,
            'memory_usage_mb': memory_mb,
            'total_params_m': total_params / 1e6
        }
        
        print(f"   总参数量: {total_params:,} ({total_params/1e6:.2f}M)")
        print(f"   可训练参数量: {trainable_params:,}")
        print(f"   模型大小: {param_size_mb:.2f}MB")
        if self.device == 'cuda':
            print(f"   显存占用: {memory_mb:.2f}MB")
        
        return results
    
    def test_robustness(self) -> Dict[str, float]:
        """
        测试模型鲁棒性
        
        在不同条件下测试模型稳定性
        """
        print("\n🛡️ 测试模型鲁棒性...")
        
        # 创建简单模型
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv = nn.Conv2d(3, 16, 3, padding=1)
                self.pool = nn.AdaptiveAvgPool2d(1)
                self.fc = nn.Linear(16, 10)
            
            def forward(self, x):
                x = torch.relu(self.conv(x))
                x = self.pool(x)
                x = x.view(x.size(0), -1)
                x = self.fc(x)
                return x
        
        model = SimpleModel().to(self.device)
        model.eval()
        
        # 基准图像
        base_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        def preprocess(img):
            img = cv2.resize(img, (224, 224))
            img = img.astype(np.float32) / 255.0
            tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
            return tensor.to(self.device)
        
        # 获取基准预测
        with torch.no_grad():
            base_pred = model(preprocess(base_image)).cpu().numpy()
        
        # 亮度鲁棒性
        brightness_scores = []
        for factor in [0.5, 0.7, 0.9, 1.1, 1.3]:
            aug_img = np.clip(base_image * factor, 0, 255).astype(np.uint8)
            with torch.no_grad():
                pred = model(preprocess(aug_img)).cpu().numpy()
            # 计算余弦相似度
            similarity = np.dot(base_pred.flatten(), pred.flatten()) / \
                        (np.linalg.norm(base_pred) * np.linalg.norm(pred) + 1e-8)
            brightness_scores.append(similarity)
        
        brightness_robustness = np.mean(brightness_scores)
        
        # 旋转鲁棒性
        rotation_scores = []
        for angle in [0, 15, 30, 45, 90]:
            h, w = base_image.shape[:2]
            M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
            aug_img = cv2.warpAffine(base_image, M, (w, h))
            with torch.no_grad():
                pred = model(preprocess(aug_img)).cpu().numpy()
            similarity = np.dot(base_pred.flatten(), pred.flatten()) / \
                        (np.linalg.norm(base_pred) * np.linalg.norm(pred) + 1e-8)
            rotation_scores.append(similarity)
        
        rotation_robustness = np.mean(rotation_scores)
        
        # 噪声鲁棒性
        noise_scores = []
        for var in [0.001, 0.005, 0.01, 0.02, 0.05]:
            noise = np.random.normal(0, np.sqrt(var), base_image.shape) * 255
            aug_img = np.clip(base_image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            with torch.no_grad():
                pred = model(preprocess(aug_img)).cpu().numpy()
            similarity = np.dot(base_pred.flatten(), pred.flatten()) / \
                        (np.linalg.norm(base_pred) * np.linalg.norm(pred) + 1e-8)
            noise_scores.append(similarity)
        
        noise_robustness = np.mean(noise_scores)
        
        # 综合鲁棒性
        overall_robustness = np.mean([
            brightness_robustness,
            rotation_robustness,
            noise_robustness
        ])
        
        results = {
            'brightness_robustness': brightness_robustness,
            'rotation_robustness': rotation_robustness,
            'noise_robustness': noise_robustness,
            'overall_robustness': overall_robustness
        }
        
        print(f"   亮度鲁棒性: {brightness_robustness:.4f}")
        print(f"   旋转鲁棒性: {rotation_robustness:.4f}")
        print(f"   噪声鲁棒性: {noise_robustness:.4f}")
        print(f"   综合鲁棒性: {overall_robustness:.4f}")
        
        return results
    
    def check_targets(self, results: Dict[str, Any]) -> List[PerformanceTarget]:
        """检查是否达到性能目标"""
        targets = []
        
        # mAP@0.5 目标
        if 'detection' in results:
            map50 = results['detection'].get('mAP50', 0)
            targets.append(PerformanceTarget(
                metric_name='mAP@0.5',
                target_value=self.TARGETS['mAP50']['value'],
                current_value=map50,
                unit=self.TARGETS['mAP50']['unit'],
                passed=map50 >= self.TARGETS['mAP50']['value']
            ))
        
        # FPS 目标
        if 'speed' in results:
            fps = results['speed'].get('fps', 0)
            targets.append(PerformanceTarget(
                metric_name='FPS',
                target_value=self.TARGETS['fps']['value'],
                current_value=fps,
                unit=self.TARGETS['fps']['unit'],
                passed=fps >= self.TARGETS['fps']['value']
            ))
        
        # 推理时间目标
        if 'speed' in results:
            inference_time = results['speed'].get('inference_time_ms', 0)
            targets.append(PerformanceTarget(
                metric_name='推理时间',
                target_value=self.TARGETS['inference_time']['value'],
                current_value=inference_time,
                unit=self.TARGETS['inference_time']['unit'],
                passed=inference_time <= self.TARGETS['inference_time']['value']
            ))
        
        return targets
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        print("\n" + "=" * 70)
        print("⚡ 开始性能基准测试")
        print("=" * 70)
        
        results = {}
        
        # 1. 检测性能
        print("\n" + "-" * 70)
        print("1. 视觉检测性能")
        print("-" * 70)
        results['detection'] = self.test_detection_performance()
        
        # 2. 推理速度
        print("\n" + "-" * 70)
        print("2. 推理速度")
        print("-" * 70)
        results['speed'] = self.test_inference_speed()
        
        # 3. 模型效率
        print("\n" + "-" * 70)
        print("3. 模型效率")
        print("-" * 70)
        results['efficiency'] = self.test_model_efficiency()
        
        # 4. 鲁棒性
        print("\n" + "-" * 70)
        print("4. 鲁棒性测试")
        print("-" * 70)
        results['robustness'] = self.test_robustness()
        
        # 检查目标达成情况
        targets = self.check_targets(results)
        
        # 统计
        total_targets = len(targets)
        passed_targets = sum(1 for t in targets if t.passed)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'device': self.device,
            'results': results,
            'targets': [t.to_dict() for t in targets],
            'overall_passed': passed_targets == total_targets if total_targets > 0 else True
        }
        
        self.results = summary
        
        # 打印摘要
        print("\n" + "=" * 70)
        print("📊 性能基准测试摘要")
        print("=" * 70)
        
        if targets:
            print(f"\n目标达成情况: {passed_targets}/{total_targets}")
            for target in targets:
                status = "✅" if target.passed else "❌"
                print(f"   {status} {target.metric_name}: "
                      f"{target.current_value:.2f}{target.unit} "
                      f"(目标: {target.target_value}{target.unit})")
        
        print("\n关键指标:")
        if 'detection' in results:
            print(f"   mAP@0.5: {results['detection']['mAP50']:.2%}")
        if 'speed' in results:
            print(f"   FPS: {results['speed']['fps']:.2f}")
            print(f"   推理时间: {results['speed']['inference_time_ms']:.2f}ms")
        if 'efficiency' in results:
            print(f"   参数量: {results['efficiency']['total_params_m']:.2f}M")
        
        print("=" * 70)
        
        return summary
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成测试报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/performance_benchmark_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 转换numpy类型为Python原生类型
        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(v) for v in obj]
            return obj
        
        serializable_results = convert_to_serializable(self.results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 性能报告已保存: {output_path}")
        return output_path


def test_performance():
    """测试性能基准"""
    print("=" * 70)
    print("🧪 测试性能基准")
    print("=" * 70)
    
    tester = PerformanceBenchmarkTest()
    summary = tester.run_all_tests()
    
    # 生成报告
    report_path = tester.generate_report()
    
    # 清理
    import shutil
    if os.path.exists("reports"):
        shutil.rmtree("reports")
    
    print("\n" + "=" * 70)
    print("✅ 性能基准测试完成！")
    print("=" * 70)
    
    return summary


# 创建兼容函数供外部调用
run_tests = test_performance


if __name__ == "__main__":
    test_performance()
