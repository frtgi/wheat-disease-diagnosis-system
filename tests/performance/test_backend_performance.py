# -*- coding: utf-8 -*-
"""
WheatAgent 后端服务性能测试脚本

测试场景：
1. API 响应时间测试
   - GET /health (目标 < 50ms)
   - GET /api/v1/diagnosis/health/ai (目标 < 100ms)
   - GET /api/v1/knowledge/search (目标 < 100ms)
   - GET /api/v1/stats/overview (目标 < 100ms)
   - POST /api/v1/diagnosis/text (目标 < 3000ms)

2. 并发测试
   - 10 并发用户测试
   - 50 并发用户测试
   - 统计成功率和平均响应时间

3. 资源占用检查
   - 检查当前显存占用
   - 检查模型加载状态
"""
import os
import sys
import time
import json
import asyncio
import threading
import statistics
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.exceptions import RequestException

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class PerformanceMetrics:
    """
    性能指标数据类
    
    存储响应时间的各项统计指标
    """
    endpoint: str
    method: str
    total_requests: int
    success_count: int
    fail_count: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    std_ms: float
    target_ms: float
    passed: bool
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        返回:
            Dict[str, Any]: 包含所有指标的字典
        """
        return asdict(self)


@dataclass
class ConcurrencyResult:
    """
    并发测试结果数据类
    
    存储并发测试的各项统计指标
    """
    concurrent_users: int
    total_requests: int
    success_count: int
    fail_count: int
    success_rate: float
    avg_response_ms: float
    p95_response_ms: float
    p99_response_ms: float
    throughput_rps: float
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        返回:
            Dict[str, Any]: 包含所有指标的字典
        """
        return asdict(self)


class BackendPerformanceTester:
    """
    后端性能测试器
    
    执行 API 响应时间测试、并发测试和资源占用检查
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化性能测试器
        
        参数:
            base_url: 后端服务基础 URL
        """
        self.base_url = base_url
        self.results: Dict[str, PerformanceMetrics] = {}
        self.concurrency_results: List[ConcurrencyResult] = []
        self.test_data = {
            "symptoms": "小麦叶片出现黄色条纹，叶面有白色霉层，穗部漂白",
            "keyword": "锈病"
        }
        
    def check_service_available(self) -> bool:
        """
        检查后端服务是否可用
        
        返回:
            bool: 服务是否可用
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except RequestException:
            return False
    
    def measure_response_time(
        self, 
        endpoint: str, 
        method: str = "GET",
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Tuple[float, bool, str]:
        """
        测量单个请求的响应时间
        
        参数:
            endpoint: API 端点路径
            method: HTTP 方法
            data: 请求数据
            files: 上传文件
            headers: 请求头
            
        返回:
            Tuple[float, bool, str]: (响应时间ms, 是否成功, 错误信息)
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.perf_counter()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=30, headers=headers)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, files=files, timeout=60, headers=headers)
                elif data:
                    response = requests.post(url, data=data, timeout=60, headers=headers)
                else:
                    response = requests.post(url, timeout=60, headers=headers)
            else:
                return 0, False, f"不支持的 HTTP 方法: {method}"
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            if response.status_code >= 200 and response.status_code < 300:
                return elapsed_ms, True, ""
            else:
                return elapsed_ms, False, f"HTTP {response.status_code}: {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return elapsed_ms, False, "请求超时"
        except RequestException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return elapsed_ms, False, str(e)
    
    def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        target_ms: float = 100.0,
        iterations: int = 20,
        data: Optional[Dict] = None,
        warmup: int = 3
    ) -> PerformanceMetrics:
        """
        测试单个 API 端点的响应时间
        
        参数:
            endpoint: API 端点路径
            method: HTTP 方法
            target_ms: 目标响应时间（毫秒）
            iterations: 测试迭代次数
            data: 请求数据
            warmup: 预热次数
            
        返回:
            PerformanceMetrics: 性能指标
        """
        print(f"\n{'='*60}")
        print(f"测试端点: {method} {endpoint}")
        print(f"目标: < {target_ms}ms")
        print(f"迭代次数: {iterations} (预热: {warmup})")
        print(f"{'='*60}")
        
        latencies: List[float] = []
        errors: List[str] = []
        success_count = 0
        fail_count = 0
        
        for i in range(warmup):
            _, _, _ = self.measure_response_time(endpoint, method, data)
            print(f"  预热 {i+1}/{warmup} 完成")
        
        print(f"\n开始正式测试...")
        
        for i in range(iterations):
            latency_ms, success, error = self.measure_response_time(endpoint, method, data)
            
            if success:
                latencies.append(latency_ms)
                success_count += 1
                status = "✅"
            else:
                fail_count += 1
                errors.append(f"请求 {i+1}: {error}")
                status = "❌"
            
            print(f"  请求 {i+1}/{iterations}: {latency_ms:.2f}ms {status}")
        
        if not latencies:
            return PerformanceMetrics(
                endpoint=endpoint,
                method=method,
                total_requests=iterations,
                success_count=success_count,
                fail_count=fail_count,
                avg_ms=0,
                min_ms=0,
                max_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
                std_ms=0,
                target_ms=target_ms,
                passed=False,
                errors=errors
            )
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        metrics = PerformanceMetrics(
            endpoint=endpoint,
            method=method,
            total_requests=iterations,
            success_count=success_count,
            fail_count=fail_count,
            avg_ms=statistics.mean(latencies),
            min_ms=min(latencies),
            max_ms=max(latencies),
            p50_ms=sorted_latencies[int(n * 0.50)],
            p95_ms=sorted_latencies[int(n * 0.95)] if n >= 20 else sorted_latencies[-1],
            p99_ms=sorted_latencies[int(n * 0.99)] if n >= 100 else sorted_latencies[-1],
            std_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0,
            target_ms=target_ms,
            passed=statistics.mean(latencies) < target_ms,
            errors=errors
        )
        
        print(f"\n结果统计:")
        print(f"  成功: {success_count}/{iterations}")
        print(f"  平均: {metrics.avg_ms:.2f}ms")
        print(f"  P50:  {metrics.p50_ms:.2f}ms")
        print(f"  P95:  {metrics.p95_ms:.2f}ms")
        print(f"  P99:  {metrics.p99_ms:.2f}ms")
        print(f"  范围: {metrics.min_ms:.2f}ms - {metrics.max_ms:.2f}ms")
        print(f"  标准差: {metrics.std_ms:.2f}ms")
        print(f"  状态: {'✅ 通过' if metrics.passed else '❌ 未达标'}")
        
        return metrics
    
    def run_api_response_tests(self) -> Dict[str, PerformanceMetrics]:
        """
        执行所有 API 响应时间测试
        
        返回:
            Dict[str, PerformanceMetrics]: 各端点的性能指标
        """
        print("\n" + "="*70)
        print("📊 API 响应时间测试")
        print("="*70)
        
        test_cases = [
            {
                "name": "health",
                "endpoint": "/health",
                "method": "GET",
                "target_ms": 50,
                "iterations": 30
            },
            {
                "name": "ai_health",
                "endpoint": "/api/v1/diagnosis/health/ai",
                "method": "GET",
                "target_ms": 100,
                "iterations": 20
            },
            {
                "name": "knowledge_search",
                "endpoint": "/api/v1/knowledge/search",
                "method": "GET",
                "target_ms": 100,
                "iterations": 20,
                "data": {"keyword": self.test_data["keyword"]}
            },
            {
                "name": "stats_overview",
                "endpoint": "/api/v1/stats/overview",
                "method": "GET",
                "target_ms": 100,
                "iterations": 20
            },
            {
                "name": "diagnosis_text",
                "endpoint": "/api/v1/diagnosis/text",
                "method": "POST",
                "target_ms": 3000,
                "iterations": 10,
                "data": {"symptoms": self.test_data["symptoms"]}
            }
        ]
        
        for case in test_cases:
            name = case["name"]
            print(f"\n{'─'*60}")
            print(f"测试用例: {name}")
            
            metrics = self.test_endpoint(
                endpoint=case["endpoint"],
                method=case["method"],
                target_ms=case["target_ms"],
                iterations=case["iterations"],
                data=case.get("data")
            )
            
            self.results[name] = metrics
        
        return self.results
    
    def run_concurrent_test(
        self,
        concurrent_users: int,
        requests_per_user: int = 5,
        endpoint: str = "/health"
    ) -> ConcurrencyResult:
        """
        执行并发测试
        
        参数:
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数
            endpoint: 测试端点
            
        返回:
            ConcurrencyResult: 并发测试结果
        """
        print(f"\n{'='*60}")
        print(f"并发测试: {concurrent_users} 用户")
        print(f"每用户请求数: {requests_per_user}")
        print(f"总请求数: {concurrent_users * requests_per_user}")
        print(f"测试端点: {endpoint}")
        print(f"{'='*60}")
        
        total_requests = concurrent_users * requests_per_user
        latencies: List[float] = []
        errors: List[str] = []
        success_count = 0
        fail_count = 0
        
        start_time = time.time()
        
        def worker(user_id: int) -> List[Tuple[float, bool, str]]:
            """
            并发工作线程
            
            参数:
                user_id: 用户标识
                
            返回:
                List[Tuple[float, bool, str]]: 请求结果列表
            """
            results = []
            for i in range(requests_per_user):
                latency_ms, success, error = self.measure_response_time(endpoint)
                results.append((latency_ms, success, error))
            return results
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = {
                executor.submit(worker, user_id): user_id 
                for user_id in range(concurrent_users)
            }
            
            completed = 0
            for future in as_completed(futures):
                user_id = futures[future]
                try:
                    results = future.result()
                    for latency_ms, success, error in results:
                        if success:
                            latencies.append(latency_ms)
                            success_count += 1
                        else:
                            fail_count += 1
                            errors.append(f"用户 {user_id}: {error}")
                    
                    completed += 1
                    print(f"  进度: {completed}/{concurrent_users} 用户完成")
                    
                except Exception as e:
                    fail_count += requests_per_user
                    errors.append(f"用户 {user_id} 异常: {str(e)}")
        
        total_time = time.time() - start_time
        
        if not latencies:
            return ConcurrencyResult(
                concurrent_users=concurrent_users,
                total_requests=total_requests,
                success_count=success_count,
                fail_count=fail_count,
                success_rate=0,
                avg_response_ms=0,
                p95_response_ms=0,
                p99_response_ms=0,
                throughput_rps=0,
                errors=errors
            )
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        result = ConcurrencyResult(
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            success_count=success_count,
            fail_count=fail_count,
            success_rate=round(success_count / total_requests * 100, 2),
            avg_response_ms=statistics.mean(latencies),
            p95_response_ms=sorted_latencies[int(n * 0.95)] if n >= 20 else sorted_latencies[-1],
            p99_response_ms=sorted_latencies[int(n * 0.99)] if n >= 100 else sorted_latencies[-1],
            throughput_rps=round(success_count / total_time, 2),
            errors=errors[:10]
        )
        
        print(f"\n并发测试结果:")
        print(f"  总请求: {total_requests}")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  成功率: {result.success_rate}%")
        print(f"  平均响应时间: {result.avg_response_ms:.2f}ms")
        print(f"  P95 响应时间: {result.p95_response_ms:.2f}ms")
        print(f"  P99 响应时间: {result.p99_response_ms:.2f}ms")
        print(f"  吞吐量: {result.throughput_rps} req/s")
        print(f"  总耗时: {total_time:.2f}s")
        
        return result
    
    def run_all_concurrency_tests(self) -> List[ConcurrencyResult]:
        """
        执行所有并发测试
        
        返回:
            List[ConcurrencyResult]: 并发测试结果列表
        """
        print("\n" + "="*70)
        print("📊 并发测试")
        print("="*70)
        
        test_configs = [
            {"users": 10, "requests_per_user": 5},
            {"users": 50, "requests_per_user": 3}
        ]
        
        for config in test_configs:
            result = self.run_concurrent_test(
                concurrent_users=config["users"],
                requests_per_user=config["requests_per_user"]
            )
            self.concurrency_results.append(result)
        
        return self.concurrency_results
    
    def check_gpu_memory(self) -> Dict[str, Any]:
        """
        检查 GPU 显存占用
        
        返回:
            Dict[str, Any]: GPU 信息
        """
        print("\n" + "="*60)
        print("🖥️  GPU 显存检查")
        print("="*60)
        
        gpu_info = {
            "available": False,
            "device_name": "",
            "total_memory_mb": 0,
            "used_memory_mb": 0,
            "free_memory_mb": 0,
            "utilization_percent": 0
        }
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["available"] = True
                gpu_info["device_name"] = torch.cuda.get_device_name(0)
                gpu_info["total_memory_mb"] = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                
                torch.cuda.synchronize()
                gpu_info["used_memory_mb"] = torch.cuda.memory_allocated(0) / (1024 * 1024)
                gpu_info["free_memory_mb"] = gpu_info["total_memory_mb"] - gpu_info["used_memory_mb"]
                gpu_info["utilization_percent"] = round(
                    gpu_info["used_memory_mb"] / gpu_info["total_memory_mb"] * 100, 2
                )
                
                print(f"  GPU 设备: {gpu_info['device_name']}")
                print(f"  总显存: {gpu_info['total_memory_mb']:.2f} MB")
                print(f"  已使用: {gpu_info['used_memory_mb']:.2f} MB")
                print(f"  空闲: {gpu_info['free_memory_mb']:.2f} MB")
                print(f"  使用率: {gpu_info['utilization_percent']}%")
            else:
                print("  CUDA 不可用")
        except ImportError:
            print("  PyTorch 未安装")
        except Exception as e:
            print(f"  检查失败: {e}")
        
        return gpu_info
    
    def check_model_status(self) -> Dict[str, Any]:
        """
        检查模型加载状态
        
        返回:
            Dict[str, Any]: 模型状态信息
        """
        print("\n" + "="*60)
        print("🤖 模型状态检查")
        print("="*60)
        
        model_status = {
            "yolo": {"loaded": False, "info": ""},
            "qwen": {"loaded": False, "info": ""}
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/diagnosis/health/ai", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                services = data.get("services", {})
                
                if "yolov8" in services:
                    yolo_info = services["yolov8"]
                    model_status["yolo"]["loaded"] = yolo_info.get("is_loaded", False)
                    model_status["yolo"]["info"] = f"Model: {yolo_info.get('model_type', 'unknown')}"
                
                if "qwen3vl" in services:
                    qwen_info = services["qwen3vl"]
                    model_status["qwen"]["loaded"] = qwen_info.get("is_loaded", False)
                    model_status["qwen"]["info"] = f"Device: {qwen_info.get('device', 'unknown')}, INT4: {qwen_info.get('int4_quantization', False)}"
                
                print(f"  YOLO 模型: {'✅ 已加载' if model_status['yolo']['loaded'] else '❌ 未加载'}")
                print(f"    {model_status['yolo']['info']}")
                print(f"  Qwen 模型: {'✅ 已加载' if model_status['qwen']['loaded'] else '❌ 未加载'}")
                print(f"    {model_status['qwen']['info']}")
                print(f"  整体状态: {data.get('status', 'unknown')}")
            else:
                print(f"  获取状态失败: HTTP {response.status_code}")
                
        except RequestException as e:
            print(f"  请求失败: {e}")
        
        return model_status
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        
        返回:
            Dict[str, Any]: 完整测试报告
        """
        print("\n" + "="*70)
        print("📋 性能测试报告")
        print("="*70)
        
        api_summary = []
        for name, metrics in self.results.items():
            api_summary.append({
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "avg_ms": round(metrics.avg_ms, 2),
                "p95_ms": round(metrics.p95_ms, 2),
                "p99_ms": round(metrics.p99_ms, 2),
                "target_ms": metrics.target_ms,
                "passed": metrics.passed,
                "success_rate": round(metrics.success_count / metrics.total_requests * 100, 2) if metrics.total_requests > 0 else 0
            })
        
        print("\n📊 API 响应时间测试结果:")
        print(f"{'端点':<40} {'平均(ms)':<12} {'P95(ms)':<12} {'目标(ms)':<12} {'状态':<8}")
        print("-" * 90)
        for item in api_summary:
            status = "✅ 通过" if item["passed"] else "❌ 未达标"
            print(f"{item['endpoint']:<40} {item['avg_ms']:<12.2f} {item['p95_ms']:<12.2f} {item['target_ms']:<12.0f} {status:<8}")
        
        print("\n📊 并发测试结果:")
        print(f"{'并发用户':<12} {'总请求':<12} {'成功率':<12} {'平均响应(ms)':<16} {'吞吐量(req/s)':<16}")
        print("-" * 70)
        for result in self.concurrency_results:
            print(f"{result.concurrent_users:<12} {result.total_requests:<12} {result.success_rate}%{'':<8} {result.avg_response_ms:<16.2f} {result.throughput_rps:<16.2f}")
        
        passed_count = sum(1 for m in self.results.values() if m.passed)
        total_count = len(self.results)
        
        print(f"\n📊 总体评估:")
        print(f"  API 测试通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
        
        bottleneck_analysis = self._analyze_bottlenecks()
        print(f"\n📊 瓶颈分析:")
        for analysis in bottleneck_analysis:
            print(f"  • {analysis}")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "api_tests": {
                "summary": api_summary,
                "details": {name: metrics.to_dict() for name, metrics in self.results.items()}
            },
            "concurrency_tests": [r.to_dict() for r in self.concurrency_results],
            "overall": {
                "api_pass_rate": round(passed_count / total_count * 100, 2) if total_count > 0 else 0,
                "total_api_tests": total_count,
                "passed_api_tests": passed_count
            },
            "bottleneck_analysis": bottleneck_analysis
        }
        
        return report
    
    def _analyze_bottlenecks(self) -> List[str]:
        """
        分析性能瓶颈
        
        返回:
            List[str]: 瓶颈分析结果列表
        """
        bottlenecks = []
        
        for name, metrics in self.results.items():
            if not metrics.passed:
                if metrics.avg_ms > metrics.target_ms * 2:
                    bottlenecks.append(
                        f"{name} 响应时间严重超标 ({metrics.avg_ms:.0f}ms > {metrics.target_ms}ms)，"
                        f"建议检查数据库查询或模型推理性能"
                    )
                else:
                    bottlenecks.append(
                        f"{name} 响应时间略超目标 ({metrics.avg_ms:.0f}ms > {metrics.target_ms}ms)，"
                        f"建议优化网络或服务配置"
                    )
            
            if metrics.std_ms > metrics.avg_ms * 0.5:
                bottlenecks.append(
                    f"{name} 响应时间波动较大 (标准差: {metrics.std_ms:.0f}ms)，"
                    f"可能存在资源竞争或冷启动问题"
                )
        
        for result in self.concurrency_results:
            if result.success_rate < 95:
                bottlenecks.append(
                    f"{result.concurrent_users} 并发用户测试成功率较低 ({result.success_rate}%)，"
                    f"建议检查服务并发处理能力或增加资源"
                )
            
            if result.avg_response_ms > 1000:
                bottlenecks.append(
                    f"{result.concurrent_users} 并发用户平均响应时间过长 ({result.avg_response_ms:.0f}ms)，"
                    f"建议优化服务性能或限制并发数"
                )
        
        if not bottlenecks:
            bottlenecks.append("所有性能指标均达标，系统运行良好")
        
        return bottlenecks
    
    def save_report(self, report: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        保存测试报告到文件
        
        参数:
            report: 测试报告数据
            output_path: 输出文件路径
            
        返回:
            str: 保存的文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(__file__).parent / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"performance_report_{timestamp}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {output_path}")
        return output_path
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        执行所有性能测试
        
        返回:
            Dict[str, Any]: 完整测试报告
        """
        print("\n" + "="*70)
        print("🚀 WheatAgent 后端服务性能测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        print("="*70)
        
        if not self.check_service_available():
            print("\n❌ 后端服务不可用，请先启动服务")
            return {"error": "服务不可用"}
        
        print("\n✅ 后端服务可用，开始测试...")
        
        self.run_api_response_tests()
        self.run_all_concurrency_tests()
        self.check_gpu_memory()
        self.check_model_status()
        
        report = self.generate_report()
        self.save_report(report)
        
        return report


def main():
    """
    主函数
    
    执行性能测试并输出结果
    """
    tester = BackendPerformanceTester(base_url="http://localhost:8000")
    report = tester.run_all_tests()
    
    print("\n" + "="*70)
    print("✅ 性能测试完成")
    print("="*70)


if __name__ == "__main__":
    main()
