# -*- coding: utf-8 -*-
"""
WheatAgent API 响应时间性能测试脚本

测试内容：
1. 测试各 API 端点响应时间
   - GET /api/v1/health 健康检查
   - GET /api/v1/knowledge 知识查询
   - POST /api/v1/user/login 用户登录
   - GET /api/v1/diagnosis/records 诊断历史

2. 性能指标记录
   - 记录每个 API 的平均响应时间
   - 记录最大/最小响应时间
   - 验证是否满足 < 500ms 的要求

3. 性能分析
   - 识别响应时间较长的 API
   - 提供优化建议
"""
import os
import sys
import io
import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
from requests.exceptions import RequestException

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class APIMetrics:
    """
    API 性能指标数据类
    
    存储响应时间的各项统计指标
    """
    endpoint: str
    method: str
    description: str
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


class APIResponseTimeTester:
    """
    API 响应时间测试器
    
    执行 API 响应时间测试并生成性能报告
    """
    
    TARGET_RESPONSE_TIME_MS = 500
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化测试器
        
        参数:
            base_url: 后端服务基础 URL
        """
        self.base_url = base_url
        self.results: Dict[str, APIMetrics] = {}
        self.auth_token: Optional[str] = None
        self.test_user = {
            "username": "test_user",
            "password": "test123456"
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
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 30
    ) -> Tuple[float, bool, str, Optional[Dict]]:
        """
        测量单个请求的响应时间
        
        参数:
            endpoint: API 端点路径
            method: HTTP 方法
            data: 表单数据
            json_data: JSON 数据
            headers: 请求头
            timeout: 超时时间
            
        返回:
            Tuple[float, bool, str, Optional[Dict]]: (响应时间ms, 是否成功, 错误信息, 响应数据)
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.perf_counter()
        response_data = None
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout, headers=headers, params=data)
            elif method.upper() == "POST":
                if json_data:
                    response = requests.post(url, json=json_data, timeout=timeout, headers=headers)
                elif data:
                    response = requests.post(url, data=data, timeout=timeout, headers=headers)
                else:
                    response = requests.post(url, timeout=timeout, headers=headers)
            else:
                return 0, False, f"不支持的 HTTP 方法: {method}", None
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            try:
                response_data = response.json()
            except:
                pass
            
            if response.status_code >= 200 and response.status_code < 300:
                return elapsed_ms, True, "", response_data
            else:
                error_msg = f"HTTP {response.status_code}"
                if response_data and isinstance(response_data, dict):
                    if "detail" in response_data:
                        error_msg += f": {response_data['detail']}"
                    elif "error" in response_data:
                        error_msg += f": {response_data['error']}"
                return elapsed_ms, False, error_msg, response_data
                
        except requests.exceptions.Timeout:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return elapsed_ms, False, "请求超时", None
        except RequestException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return elapsed_ms, False, str(e), None
    
    def test_endpoint(
        self,
        name: str,
        endpoint: str,
        method: str = "GET",
        description: str = "",
        target_ms: float = 500.0,
        iterations: int = 20,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        warmup: int = 3,
        timeout: int = 30
    ) -> APIMetrics:
        """
        测试单个 API 端点的响应时间
        
        参数:
            name: 测试名称
            endpoint: API 端点路径
            method: HTTP 方法
            description: 端点描述
            target_ms: 目标响应时间（毫秒）
            iterations: 测试迭代次数
            data: 表单数据
            json_data: JSON 数据
            headers: 请求头
            warmup: 预热次数
            timeout: 超时时间
            
        返回:
            APIMetrics: 性能指标
        """
        print(f"\n{'='*60}")
        print(f"测试端点: {method} {endpoint}")
        print(f"描述: {description}")
        print(f"目标: < {target_ms}ms")
        print(f"迭代次数: {iterations} (预热: {warmup})")
        print(f"{'='*60}")
        
        latencies: List[float] = []
        errors: List[str] = []
        success_count = 0
        fail_count = 0
        
        for i in range(warmup):
            _, _, _, _ = self.measure_response_time(endpoint, method, data, json_data, headers, timeout)
            print(f"  预热 {i+1}/{warmup} 完成")
        
        print(f"\n开始正式测试...")
        
        for i in range(iterations):
            latency_ms, success, error, _ = self.measure_response_time(
                endpoint, method, data, json_data, headers, timeout
            )
            
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
            return APIMetrics(
                endpoint=endpoint,
                method=method,
                description=description,
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
        
        metrics = APIMetrics(
            endpoint=endpoint,
            method=method,
            description=description,
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
    
    def setup_test_user(self) -> bool:
        """
        设置测试用户（注册或登录）
        
        返回:
            bool: 是否成功获取认证令牌
        """
        print(f"\n{'='*60}")
        print("设置测试用户")
        print(f"{'='*60}")
        
        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        
        _, success, _, response_data = self.measure_response_time(
            "/api/v1/users/login",
            method="POST",
            json_data=login_data
        )
        
        if success and response_data:
            data = response_data.get("data", {})
            self.auth_token = data.get("access_token")
            if self.auth_token:
                print(f"  ✅ 登录成功，获取到认证令牌")
                return True
        
        print(f"  ⚠️ 登录失败，尝试注册新用户...")
        
        register_data = {
            "username": self.test_user["username"],
            "email": f"{self.test_user['username']}@test.com",
            "password": self.test_user["password"]
        }
        
        _, success, _, _ = self.measure_response_time(
            "/api/v1/users/register",
            method="POST",
            json_data=register_data
        )
        
        if success:
            print(f"  ✅ 注册成功，尝试登录...")
            
            _, success, _, response_data = self.measure_response_time(
                "/api/v1/users/login",
                method="POST",
                json_data=login_data
            )
            
            if success and response_data:
                data = response_data.get("data", {})
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    print(f"  ✅ 登录成功，获取到认证令牌")
                    return True
        
        print(f"  ❌ 无法获取认证令牌，部分测试将跳过")
        return False
    
    def run_all_tests(self) -> Dict[str, APIMetrics]:
        """
        执行所有 API 响应时间测试
        
        返回:
            Dict[str, APIMetrics]: 各端点的性能指标
        """
        print("\n" + "="*70)
        print("📊 API 响应时间性能测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        print(f"性能目标: < {self.TARGET_RESPONSE_TIME_MS}ms")
        print("="*70)
        
        if not self.check_service_available():
            print("\n❌ 后端服务不可用，请先启动服务")
            return {}
        
        print("\n✅ 后端服务可用，开始测试...")
        
        self.setup_test_user()
        
        auth_headers = {}
        if self.auth_token:
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_cases = [
            {
                "name": "health_check",
                "endpoint": "/api/v1/health",
                "method": "GET",
                "description": "健康检查 - 检查服务运行状态",
                "target_ms": 100,
                "iterations": 30,
                "headers": None
            },
            {
                "name": "knowledge_search",
                "endpoint": "/api/v1/knowledge/search",
                "method": "GET",
                "description": "知识查询 - 搜索病害知识库",
                "target_ms": self.TARGET_RESPONSE_TIME_MS,
                "iterations": 20,
                "data": {"keyword": "锈病"},
                "headers": None
            },
            {
                "name": "user_login",
                "endpoint": "/api/v1/users/login",
                "method": "POST",
                "description": "用户登录 - 用户认证获取令牌",
                "target_ms": self.TARGET_RESPONSE_TIME_MS,
                "iterations": 20,
                "json_data": {
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                },
                "headers": None
            },
            {
                "name": "diagnosis_history",
                "endpoint": "/api/v1/diagnosis/records",
                "method": "GET",
                "description": "诊断历史 - 查询用户诊断记录",
                "target_ms": self.TARGET_RESPONSE_TIME_MS,
                "iterations": 20,
                "data": {"skip": 0, "limit": 20},
                "headers": auth_headers if self.auth_token else None
            }
        ]
        
        for case in test_cases:
            name = case["name"]
            print(f"\n{'─'*60}")
            print(f"测试用例: {name}")
            
            if case.get("headers") is None and "headers" in case:
                if case["endpoint"] == "/api/v1/diagnosis/records" and not self.auth_token:
                    print(f"  ⚠️ 跳过测试：需要认证令牌")
                    continue
            
            metrics = self.test_endpoint(
                name=name,
                endpoint=case["endpoint"],
                method=case["method"],
                description=case["description"],
                target_ms=case["target_ms"],
                iterations=case["iterations"],
                data=case.get("data"),
                json_data=case.get("json_data"),
                headers=case.get("headers"),
                warmup=3
            )
            
            self.results[name] = metrics
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        
        返回:
            Dict[str, Any]: 完整测试报告
        """
        print("\n" + "="*70)
        print("📋 API 响应时间性能测试报告")
        print("="*70)
        
        if not self.results:
            print("\n❌ 没有测试结果")
            return {}
        
        summary = []
        for name, metrics in self.results.items():
            summary.append({
                "name": name,
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "description": metrics.description,
                "avg_ms": round(metrics.avg_ms, 2),
                "min_ms": round(metrics.min_ms, 2),
                "max_ms": round(metrics.max_ms, 2),
                "p50_ms": round(metrics.p50_ms, 2),
                "p95_ms": round(metrics.p95_ms, 2),
                "p99_ms": round(metrics.p99_ms, 2),
                "std_ms": round(metrics.std_ms, 2),
                "target_ms": metrics.target_ms,
                "passed": metrics.passed,
                "success_rate": round(metrics.success_count / metrics.total_requests * 100, 2) if metrics.total_requests > 0 else 0
            })
        
        print("\n📊 测试结果汇总:")
        print(f"{'端点':<35} {'平均(ms)':<12} {'P95(ms)':<12} {'目标(ms)':<12} {'状态':<10}")
        print("-" * 85)
        for item in summary:
            status = "✅ 通过" if item["passed"] else "❌ 未达标"
            print(f"{item['endpoint']:<35} {item['avg_ms']:<12.2f} {item['p95_ms']:<12.2f} {item['target_ms']:<12.0f} {status:<10}")
        
        print("\n📊 详细性能指标:")
        print(f"{'端点':<35} {'最小(ms)':<12} {'最大(ms)':<12} {'P50(ms)':<12} {'P99(ms)':<12}")
        print("-" * 85)
        for item in summary:
            print(f"{item['endpoint']:<35} {item['min_ms']:<12.2f} {item['max_ms']:<12.2f} {item['p50_ms']:<12.2f} {item['p99_ms']:<12.2f}")
        
        passed_count = sum(1 for m in self.results.values() if m.passed)
        total_count = len(self.results)
        
        print(f"\n📊 总体评估:")
        print(f"  测试通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
        print(f"  性能目标: < {self.TARGET_RESPONSE_TIME_MS}ms")
        
        optimization_suggestions = self._generate_optimization_suggestions()
        print(f"\n📊 优化建议:")
        for suggestion in optimization_suggestions:
            print(f"  • {suggestion}")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "target_response_time_ms": self.TARGET_RESPONSE_TIME_MS,
            "summary": summary,
            "details": {name: metrics.to_dict() for name, metrics in self.results.items()},
            "overall": {
                "pass_rate": round(passed_count / total_count * 100, 2) if total_count > 0 else 0,
                "total_tests": total_count,
                "passed_tests": passed_count
            },
            "optimization_suggestions": optimization_suggestions
        }
        
        return report
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """
        生成优化建议
        
        返回:
            List[str]: 优化建议列表
        """
        suggestions = []
        
        for name, metrics in self.results.items():
            if not metrics.passed:
                if metrics.avg_ms > metrics.target_ms * 2:
                    suggestions.append(
                        f"【高优先级】{metrics.description}({metrics.endpoint}) 响应时间严重超标 "
                        f"({metrics.avg_ms:.0f}ms > {metrics.target_ms}ms)，"
                        f"建议检查数据库查询优化、添加缓存或优化业务逻辑"
                    )
                else:
                    suggestions.append(
                        f"【中优先级】{metrics.description}({metrics.endpoint}) 响应时间略超目标 "
                        f"({metrics.avg_ms:.0f}ms > {metrics.target_ms}ms)，"
                        f"建议优化网络配置或增加服务器资源"
                    )
            
            if metrics.std_ms > metrics.avg_ms * 0.5 and metrics.avg_ms > 0:
                suggestions.append(
                    f"【稳定性】{metrics.description}({metrics.endpoint}) 响应时间波动较大 "
                    f"(标准差: {metrics.std_ms:.0f}ms)，可能存在资源竞争或冷启动问题，"
                    f"建议增加预热机制或检查资源竞争"
                )
            
            if metrics.fail_count > 0:
                suggestions.append(
                    f"【可靠性】{metrics.description}({metrics.endpoint}) 存在失败请求 "
                    f"({metrics.fail_count}/{metrics.total_requests})，"
                    f"建议检查错误日志并优化错误处理"
                )
        
        if all(m.passed for m in self.results.values()):
            suggestions.append("✅ 所有 API 响应时间均达标，系统性能良好")
            suggestions.append("建议：持续监控性能指标，定期进行性能测试")
        
        if not suggestions:
            suggestions.append("系统性能表现良好，暂无优化建议")
        
        return suggestions
    
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
            output_path = str(output_dir / f"api_response_time_report_{timestamp}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {output_path}")
        return output_path


def main():
    """
    主函数
    
    执行 API 响应时间性能测试并输出结果
    """
    tester = APIResponseTimeTester(base_url="http://localhost:8000")
    
    results = tester.run_all_tests()
    
    if results:
        report = tester.generate_report()
        tester.save_report(report)
    
    print("\n" + "="*70)
    print("✅ API 响应时间性能测试完成")
    print("="*70)


if __name__ == "__main__":
    main()
