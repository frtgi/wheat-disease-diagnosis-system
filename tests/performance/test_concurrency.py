# -*- coding: utf-8 -*-
"""
并发性能测试模块

测试目标：
- 10 并发测试
- 50 并发测试
- 100 并发测试
- 吞吐量统计

性能指标：
- 每秒请求数 (RPS)
- 平均响应时间
- 错误率
- 并发成功率
"""
import os
import sys
import time
import threading
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pytest
import torch

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ConcurrencyMetrics:
    """并发性能指标"""
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    requests_per_second: float
    mean_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    min_latency: float
    max_latency: float
    throughput_mb_per_sec: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConcurrencyBenchmark:
    """并发基准测试类"""
    
    # 并发级别配置
    CONCURRENCY_LEVELS = [10, 50, 100]
    
    # 测试配置
    TEST_DURATION = 10  # 测试持续时间 (秒)
    WARMUP_REQUESTS = 10  # 预热请求数
    
    def __init__(self):
        """初始化并发基准测试"""
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.results: Dict[int, ConcurrencyMetrics] = {}
        
        # 创建模拟服务
        self.mock_service = self._create_mock_service()
    
    def run_concurrency_test(self, concurrent_users: int) -> ConcurrencyMetrics:
        """
        运行并发测试
        
        :param concurrent_users: 并发用户数
        :return: 并发性能指标
        """
        print(f"\n开始 {concurrent_users} 并发测试...")
        
        # 记录测试结果
        latencies = []
        successful = 0
        failed = 0
        total_bytes = 0
        
        # 同步信号
        start_event = threading.Event()
        stop_event = threading.Event()
        
        # 线程安全锁
        lock = threading.Lock()
        
        def worker():
            """工作线程函数"""
            nonlocal successful, failed, total_bytes
            
            # 等待开始信号
            start_event.wait()
            
            while not stop_event.is_set():
                try:
                    request_start = time.perf_counter()
                    
                    # 模拟请求
                    response_size, response_data = self.mock_service.process_request()
                    
                    request_end = time.perf_counter()
                    latency = request_end - request_start
                    
                    with lock:
                        latencies.append(latency)
                        successful += 1
                        total_bytes += response_size
                    
                except Exception as e:
                    with lock:
                        failed += 1
        
        # 预热
        print(f"  预热阶段：{self.WARMUP_REQUESTS} 次请求...")
        for _ in range(self.WARMUP_REQUESTS):
            self.mock_service.process_request()
        
        # 创建工作线程
        threads = []
        for _ in range(concurrent_users):
            thread = threading.Thread(target=worker)
            thread.daemon = True
            threads.append(thread)
        
        # 启动线程
        for thread in threads:
            thread.start()
        
        # 同时开始测试
        print(f"  测试进行中，持续 {self.TEST_DURATION} 秒...")
        start_event.set()
        time.sleep(self.TEST_DURATION)
        stop_event.set()
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=2.0)
        
        # 计算指标
        total_requests = successful + failed
        success_rate = successful / total_requests if total_requests > 0 else 0
        rps = successful / self.TEST_DURATION
        
        # 计算延迟百分位数
        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            p50 = sorted_latencies[int(n * 0.50)]
            p95 = sorted_latencies[int(n * 0.95)]
            p99 = sorted_latencies[int(n * 0.99)]
            mean_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            p50 = p95 = p99 = mean_latency = min_latency = max_latency = 0
        
        # 计算吞吐量 (MB/s)
        throughput_mb_per_sec = total_bytes / self.TEST_DURATION / (1024 * 1024)
        
        metrics = ConcurrencyMetrics(
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            success_rate=success_rate,
            requests_per_second=rps,
            mean_latency=mean_latency,
            p50_latency=p50,
            p95_latency=p95,
            p99_latency=p99,
            min_latency=min_latency,
            max_latency=max_latency,
            throughput_mb_per_sec=throughput_mb_per_sec
        )
        
        # 打印结果
        print(f"  总请求数：{total_requests}")
        print(f"  成功/失败：{successful}/{failed}")
        print(f"  成功率：{success_rate:.2%}")
        print(f"  吞吐量：{rps:.2f} RPS")
        print(f"  平均延迟：{mean_latency*1000:.2f}ms")
        print(f"  p50/p95/p99: {p50*1000:.2f}ms/{p95*1000:.2f}ms/{p99*1000:.2f}ms")
        print(f"  网络吞吐量：{throughput_mb_per_sec:.2f} MB/s")
        
        self.results[concurrent_users] = metrics
        return metrics
    
    def run_all_tests(self) -> Dict[int, ConcurrencyMetrics]:
        """运行所有并发级别的测试"""
        print("\n" + "=" * 70)
        print("⚡ 开始并发性能测试")
        print("=" * 70)
        
        for level in self.CONCURRENCY_LEVELS:
            self.run_concurrency_test(level)
        
        return self.results
    
    def _create_mock_service(self) -> 'MockService':
        """创建模拟服务"""
        return MockService(self.device)


class MockService:
    """模拟 IWDDA Agent 服务"""
    
    def __init__(self, device: str):
        """
        初始化模拟服务
        
        :param device: 计算设备 (cuda/cpu)
        """
        self.device = device
        self.model = self._create_mock_model()
        self.model.eval()
    
    def _create_mock_model(self) -> torch.nn.Module:
        """创建模拟模型"""
        class MockModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                # 模拟视觉感知模块
                self.perception = torch.nn.Sequential(
                    torch.nn.Conv2d(3, 64, 3, padding=1),
                    torch.nn.BatchNorm2d(64),
                    torch.nn.ReLU(),
                    torch.nn.MaxPool2d(2, 2),
                    torch.nn.Conv2d(64, 128, 3, padding=1),
                    torch.nn.BatchNorm2d(128),
                    torch.nn.ReLU(),
                    torch.nn.AdaptiveAvgPool2d(1),
                )
                # 模拟认知层
                self.cognition = torch.nn.Sequential(
                    torch.nn.Linear(128, 256),
                    torch.nn.ReLU(),
                    torch.nn.Linear(256, 128),
                    torch.nn.ReLU(),
                    torch.nn.Linear(128, 10)
                )
            
            def forward(self, x):
                x = self.perception(x)
                x = x.view(x.size(0), -1)
                x = self.cognition(x)
                return x
        
        return MockModel().to(self.device)
    
    def process_request(self) -> Tuple[int, Any]:
        """
        处理单个请求
        
        :return: (响应大小，响应数据)
        """
        # 模拟输入
        dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
        
        # 推理
        with torch.no_grad():
            output = self.model(dummy_input)
        
        if self.device == 'cuda':
            torch.cuda.synchronize()
        
        # 模拟响应数据
        response_data = {
            'prediction': output.cpu().numpy().tolist(),
            'confidence': 0.95
        }
        
        # 估算响应大小 (字节)
        response_size = len(str(response_data))
        
        return response_size, response_data


class TestConcurrency:
    """并发测试类"""
    
    @pytest.fixture
    def concurrency_benchmark(self) -> ConcurrencyBenchmark:
        """创建并发基准测试实例"""
        return ConcurrencyBenchmark()
    
    def test_10_concurrent_users(self, concurrency_benchmark: ConcurrencyBenchmark):
        """
        测试 10 并发性能
        
        验证在 10 个并发用户下的系统性能
        """
        metrics = concurrency_benchmark.run_concurrency_test(10)
        
        # 验证成功率
        assert metrics.success_rate > 0.95, \
            f"10 并发成功率 {metrics.success_rate:.2%} 低于 95%"
        
        # 验证吞吐量
        assert metrics.requests_per_second > 10, \
            f"10 并发吞吐量 {metrics.requests_per_second:.2f} RPS 低于预期"
    
    def test_50_concurrent_users(self, concurrency_benchmark: ConcurrencyBenchmark):
        """
        测试 50 并发性能
        
        验证在 50 个并发用户下的系统性能
        """
        metrics = concurrency_benchmark.run_concurrency_test(50)
        
        # 验证成功率
        assert metrics.success_rate > 0.90, \
            f"50 并发成功率 {metrics.success_rate:.2%} 低于 90%"
        
        # 验证吞吐量
        assert metrics.requests_per_second > 50, \
            f"50 并发吞吐量 {metrics.requests_per_second:.2f} RPS 低于预期"
    
    def test_100_concurrent_users(self, concurrency_benchmark: ConcurrencyBenchmark):
        """
        测试 100 并发性能
        
        验证在 100 个并发用户下的系统性能
        """
        metrics = concurrency_benchmark.run_concurrency_test(100)
        
        # 验证成功率
        assert metrics.success_rate > 0.85, \
            f"100 并发成功率 {metrics.success_rate:.2%} 低于 85%"
        
        # 验证系统稳定性
        assert metrics.failed_requests < metrics.total_requests * 0.15, \
            f"100 并发失败请求过多：{metrics.failed_requests}/{metrics.total_requests}"
    
    def test_throughput_scaling(self, concurrency_benchmark: ConcurrencyBenchmark):
        """
        测试吞吐量扩展性
        
        验证并发用户数增加时，系统仍能保持一定吞吐量
        """
        results = concurrency_benchmark.run_all_tests()
        
        # 获取各并发级别的吞吐量
        rps_10 = results[10].requests_per_second
        rps_50 = results[50].requests_per_second
        rps_100 = results[100].requests_per_second
        
        # 验证系统在高并发下仍能工作
        # 由于资源竞争，100 并发时吞吐量可能下降，但要求至少达到 10 并发的 50%
        min_rps_100 = rps_10 * 0.5
        scaling_efficiency = rps_100 / rps_10 if rps_10 > 0 else 0
        
        print(f"\n吞吐量扩展性测试:")
        print(f"  10 并发 RPS: {rps_10:.2f}")
        print(f"  50 并发 RPS: {rps_50:.2f}")
        print(f"  100 并发 RPS: {rps_100:.2f}")
        print(f"  扩展效率：{scaling_efficiency:.2f}x (目标：>0.5x)")
        
        assert rps_100 > min_rps_100, \
            f"100 并发吞吐量 {rps_100:.2f} RPS 低于最低要求 {min_rps_100:.2f} RPS"
    
    def test_latency_under_load(self, concurrency_benchmark: ConcurrencyBenchmark):
        """
        测试高负载下的延迟
        
        验证在高并发下延迟是否可控
        """
        results = concurrency_benchmark.run_all_tests()
        
        # 检查不同并发级别下的延迟
        for concurrent_users, metrics in results.items():
            max_allowed_latency = 2.0  # 最大允许延迟 (秒)
            
            print(f"\n{concurrent_users}并发延迟检查:")
            print(f"  p95 延迟：{metrics.p95_latency*1000:.2f}ms")
            print(f"  p99 延迟：{metrics.p99_latency*1000:.2f}ms")
            
            assert metrics.p95_latency < max_allowed_latency, \
                f"{concurrent_users}并发的 p95 延迟 {metrics.p95_latency:.3f}s 超过阈值"


def generate_concurrency_report(
    metrics: Dict[int, ConcurrencyMetrics], 
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成并发测试报告
    
    :param metrics: 各并发级别的性能指标
    :param output_path: 报告输出路径
    :return: 报告字典
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/concurrency_report_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_duration': ConcurrencyBenchmark.TEST_DURATION,
        'concurrency_levels': ConcurrencyBenchmark.CONCURRENCY_LEVELS,
        'results': {
            str(level): metric.to_dict() 
            for level, metric in metrics.items()
        },
        'summary': {
            'max_rps': max(m.requests_per_second for m in metrics.values()),
            'max_success_rate': max(m.success_rate for m in metrics.values()),
            'min_success_rate': min(m.success_rate for m in metrics.values()),
        }
    }
    
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 并发报告已保存：{output_path}")
    return report
