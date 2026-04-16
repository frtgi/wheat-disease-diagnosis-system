# -*- coding: utf-8 -*-
"""
WheatAgent 后端服务性能测试脚本

测试场景：
1. API 响应时间测试
2. 并发测试（10并发用户）

使用方法：
    python scripts/performance_test.py
"""
import requests
import time
import statistics
import concurrent.futures
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import os
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """测试结果数据类"""
    endpoint: str
    success: bool
    response_time_ms: float
    status_code: int
    error: str = ""


@dataclass
class EndpointConfig:
    """端点配置数据类"""
    name: str
    path: str
    target_ms: float
    method: str = "GET"
    params: Dict = None


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化性能测试器
        
        :param base_url: 基础URL
        """
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
    
    def test_endpoint(self, config: EndpointConfig) -> TestResult:
        """
        测试单个端点
        
        :param config: 端点配置
        :return: 测试结果
        """
        url = f"{self.base_url}{config.path}"
        
        try:
            start_time = time.time()
            
            if config.method == "GET":
                response = self.session.get(url, params=config.params, timeout=10)
            elif config.method == "POST":
                response = self.session.post(url, json=config.params, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {config.method}")
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                endpoint=config.name,
                success=response.status_code == 200,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                error="" if response.status_code == 200 else f"HTTP {response.status_code}"
            )
            
        except requests.exceptions.Timeout:
            return TestResult(
                endpoint=config.name,
                success=False,
                response_time_ms=10000,
                status_code=0,
                error="请求超时"
            )
        except requests.exceptions.ConnectionError:
            return TestResult(
                endpoint=config.name,
                success=False,
                response_time_ms=0,
                status_code=0,
                error="连接失败"
            )
        except Exception as e:
            return TestResult(
                endpoint=config.name,
                success=False,
                response_time_ms=0,
                status_code=0,
                error=str(e)
            )
    
    def run_response_time_test(
        self, 
        configs: List[EndpointConfig], 
        iterations: int = 10
    ) -> Dict[str, Dict[str, Any]]:
        """
        运行响应时间测试
        
        :param configs: 端点配置列表
        :param iterations: 每个端点测试次数
        :return: 测试结果统计
        """
        print("\n" + "=" * 70)
        print("📊 API 响应时间测试")
        print("=" * 70)
        print(f"测试次数: {iterations} 次/端点")
        print(f"目标响应时间: 见下表")
        print("-" * 70)
        
        results = {}
        
        for config in configs:
            print(f"\n🔍 测试端点: {config.name}")
            print(f"   路径: {config.path}")
            print(f"   目标: < {config.target_ms}ms")
            
            test_results: List[TestResult] = []
            
            for i in range(iterations):
                result = self.test_endpoint(config)
                test_results.append(result)
                
                status = "✅" if result.success else "❌"
                print(f"   [{i+1:2d}/{iterations}] {status} {result.response_time_ms:7.2f}ms", end="")
                if result.error:
                    print(f" - {result.error}")
                else:
                    print()
                
                time.sleep(0.1)
            
            response_times = [r.response_time_ms for r in test_results if r.success]
            success_count = sum(1 for r in test_results if r.success)
            
            if response_times:
                stats = {
                    "min_ms": min(response_times),
                    "max_ms": max(response_times),
                    "avg_ms": statistics.mean(response_times),
                    "median_ms": statistics.median(response_times),
                    "p95_ms": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0],
                    "success_rate": success_count / iterations * 100,
                    "target_ms": config.target_ms,
                    "passed": statistics.mean(response_times) < config.target_ms
                }
            else:
                stats = {
                    "min_ms": 0,
                    "max_ms": 0,
                    "avg_ms": 0,
                    "median_ms": 0,
                    "p95_ms": 0,
                    "success_rate": 0,
                    "target_ms": config.target_ms,
                    "passed": False
                }
            
            results[config.name] = stats
            
            print(f"\n   📈 统计结果:")
            print(f"      最小值: {stats['min_ms']:.2f}ms")
            print(f"      最大值: {stats['max_ms']:.2f}ms")
            print(f"      平均值: {stats['avg_ms']:.2f}ms")
            print(f"      中位数: {stats['median_ms']:.2f}ms")
            print(f"      P95:    {stats['p95_ms']:.2f}ms")
            print(f"      成功率: {stats['success_rate']:.1f}%")
            
            if stats['passed']:
                print(f"   ✅ 性能达标 (目标: < {config.target_ms}ms)")
            else:
                print(f"   ❌ 性能未达标 (目标: < {config.target_ms}ms)")
        
        return results
    
    def run_concurrent_test(
        self, 
        config: EndpointConfig, 
        concurrent_users: int = 10,
        requests_per_user: int = 5
    ) -> Dict[str, Any]:
        """
        运行并发测试
        
        :param config: 端点配置
        :param concurrent_users: 并发用户数
        :param requests_per_user: 每个用户请求数
        :return: 测试结果统计
        """
        print("\n" + "=" * 70)
        print("🚀 并发测试")
        print("=" * 70)
        print(f"端点: {config.name}")
        print(f"路径: {config.path}")
        print(f"并发用户数: {concurrent_users}")
        print(f"每用户请求数: {requests_per_user}")
        print(f"总请求数: {concurrent_users * requests_per_user}")
        print("-" * 70)
        
        all_results: List[TestResult] = []
        
        def user_task(user_id: int) -> List[TestResult]:
            """用户任务"""
            user_results = []
            for i in range(requests_per_user):
                result = self.test_endpoint(config)
                user_results.append(result)
                time.sleep(0.05)
            return user_results
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_task, i) for i in range(concurrent_users)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    print(f"   ❌ 用户任务异常: {e}")
        
        total_time = time.time() - start_time
        
        response_times = [r.response_time_ms for r in all_results if r.success]
        success_count = sum(1 for r in all_results if r.success)
        total_requests = len(all_results)
        
        if response_times:
            stats = {
                "total_requests": total_requests,
                "success_count": success_count,
                "failed_count": total_requests - success_count,
                "success_rate": success_count / total_requests * 100,
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "avg_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "p95_ms": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0],
                "total_time_s": total_time,
                "requests_per_second": total_requests / total_time
            }
        else:
            stats = {
                "total_requests": total_requests,
                "success_count": 0,
                "failed_count": total_requests,
                "success_rate": 0,
                "min_ms": 0,
                "max_ms": 0,
                "avg_ms": 0,
                "median_ms": 0,
                "p95_ms": 0,
                "total_time_s": total_time,
                "requests_per_second": 0
            }
        
        print(f"\n📊 并发测试结果:")
        print(f"   总请求数:   {stats['total_requests']}")
        print(f"   成功请求:   {stats['success_count']}")
        print(f"   失败请求:   {stats['failed_count']}")
        print(f"   成功率:     {stats['success_rate']:.1f}%")
        print(f"   最小响应:   {stats['min_ms']:.2f}ms")
        print(f"   最大响应:   {stats['max_ms']:.2f}ms")
        print(f"   平均响应:   {stats['avg_ms']:.2f}ms")
        print(f"   中位数:     {stats['median_ms']:.2f}ms")
        print(f"   P95:        {stats['p95_ms']:.2f}ms")
        print(f"   总耗时:     {stats['total_time_s']:.2f}s")
        print(f"   吞吐量:     {stats['requests_per_second']:.2f} req/s")
        
        return stats
    
    def check_server_health(self) -> bool:
        """
        检查服务器健康状态
        
        :return: 服务器是否健康
        """
        print("\n🔍 检查服务器状态...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ 服务器运行正常: {self.base_url}")
                return True
            else:
                print(f"   ❌ 服务器响应异常: HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 无法连接到服务器: {self.base_url}")
            print(f"   请确保后端服务已启动:")
            print(f"   - 方式1: cd {project_root} && python -m uvicorn src.web.backend.app.main:app --host 0.0.0.0 --port 8000")
            print(f"   - 方式2: cd {project_root} && python run_api.py")
            return False
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            return False


def generate_report(
    response_time_results: Dict[str, Dict],
    concurrent_results: Dict[str, Dict]
) -> str:
    """
    生成测试报告
    
    :param response_time_results: 响应时间测试结果
    :param concurrent_results: 并发测试结果
    :return: 报告文本
    """
    report = []
    report.append("\n" + "=" * 70)
    report.append("📋 WheatAgent 后端服务性能测试报告")
    report.append("=" * 70)
    report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    report.append("-" * 70)
    report.append("一、API 响应时间测试结果")
    report.append("-" * 70)
    
    all_passed = True
    for name, stats in response_time_results.items():
        status = "✅ 达标" if stats['passed'] else "❌ 未达标"
        report.append(f"\n{name}:")
        report.append(f"   平均响应时间: {stats['avg_ms']:.2f}ms (目标: < {stats['target_ms']}ms)")
        report.append(f"   P95响应时间:  {stats['p95_ms']:.2f}ms")
        report.append(f"   成功率:       {stats['success_rate']:.1f}%")
        report.append(f"   状态:         {status}")
        if not stats['passed']:
            all_passed = False
    
    report.append("\n" + "-" * 70)
    report.append("二、并发测试结果")
    report.append("-" * 70)
    
    for name, stats in concurrent_results.items():
        report.append(f"\n{name}:")
        report.append(f"   成功率:     {stats['success_rate']:.1f}%")
        report.append(f"   平均响应:   {stats['avg_ms']:.2f}ms")
        report.append(f"   吞吐量:     {stats['requests_per_second']:.2f} req/s")
    
    report.append("\n" + "-" * 70)
    report.append("三、测试结论")
    report.append("-" * 70)
    
    if all_passed:
        report.append("\n✅ 所有端点性能达标!")
    else:
        report.append("\n⚠️ 部分端点性能未达标，请优化!")
    
    report.append("\n" + "=" * 70)
    
    return "\n".join(report)


def main():
    """主函数"""
    print("=" * 70)
    print("🌾 WheatAgent 后端服务性能测试")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = os.getenv("WHEATAGENT_API_URL", "http://localhost:8000")
    print(f"服务地址: {base_url}")
    
    tester = PerformanceTester(base_url)
    
    if not tester.check_server_health():
        print("\n❌ 服务器不可用，测试终止")
        return
    
    endpoint_configs = [
        EndpointConfig(
            name="健康检查",
            path="/health",
            target_ms=50,
            method="GET"
        ),
        EndpointConfig(
            name="AI服务健康检查",
            path="/api/v1/diagnosis/health/ai",
            target_ms=100,
            method="GET"
        ),
        EndpointConfig(
            name="知识库搜索",
            path="/api/v1/knowledge/search",
            target_ms=100,
            method="GET",
            params={"keyword": "锈病", "page": 1, "page_size": 10}
        ),
        EndpointConfig(
            name="统计概览",
            path="/api/v1/stats/overview",
            target_ms=100,
            method="GET"
        ),
    ]
    
    response_time_results = tester.run_response_time_test(
        endpoint_configs, 
        iterations=10
    )
    
    concurrent_configs = [
        EndpointConfig(
            name="健康检查并发测试",
            path="/health",
            target_ms=100,
            method="GET"
        ),
        EndpointConfig(
            name="AI健康检查并发测试",
            path="/api/v1/diagnosis/health/ai",
            target_ms=200,
            method="GET"
        ),
    ]
    
    concurrent_results = {}
    
    for config in concurrent_configs:
        result = tester.run_concurrent_test(
            config,
            concurrent_users=10,
            requests_per_user=5
        )
        concurrent_results[config.name] = result
    
    report = generate_report(response_time_results, concurrent_results)
    print(report)
    
    report_dir = Path("test_results")
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / f"performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    full_results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "response_time_tests": response_time_results,
        "concurrent_tests": concurrent_results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试结果已保存至: {report_file}")


if __name__ == "__main__":
    main()
