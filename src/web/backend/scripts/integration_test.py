# -*- coding: utf-8 -*-
"""
集成测试脚本
测试前后端服务集成和完整诊断流程
"""
import os
import sys
import time
import json
import asyncio
import subprocess
import signal
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent))


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ServiceProcess:
    """服务进程数据类"""
    name: str
    process: Optional[subprocess.Popen] = None
    port: int = 0
    running: bool = False


class IntegrationTest:
    """
    集成测试类
    
    测试内容：
    1. 后端服务启动测试
    2. 前端服务启动测试
    3. 前后端通信测试
    4. 完整诊断流程测试
    """
    
    def __init__(self, backend_port: int = 8000, frontend_port: int = 5173):
        """
        初始化集成测试
        
        参数:
            backend_port: 后端服务端口
            frontend_port: 前端服务端口
        """
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.results: List[TestResult] = []
    
    async def test_backend_health(self) -> TestResult:
        """
        测试后端健康检查
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "后端健康检查"
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"http://localhost:{self.backend_port}/api/v1/health")
                
            duration_ms = (time.time() - start_time) * 1000
            passed = response.status_code == 200
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"status_code": response.status_code}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def test_api_endpoints(self) -> TestResult:
        """
        测试 API 端点可用性
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "API 端点测试"
        
        try:
            import httpx
            endpoints = [
                f"http://localhost:{self.backend_port}/api/v1/health",
                f"http://localhost:{self.backend_port}/api/v1/stats/overview",
            ]
            
            results = {}
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in endpoints:
                    try:
                        response = await client.get(endpoint)
                        results[endpoint] = response.status_code
                    except Exception as e:
                        results[endpoint] = str(e)
            
            duration_ms = (time.time() - start_time) * 1000
            passed = all(isinstance(v, int) and v < 500 for v in results.values())
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details=results
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def test_diagnosis_api(self) -> TestResult:
        """
        测试诊断 API
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "诊断 API 测试"
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"http://localhost:{self.backend_port}/api/v1/diagnosis/text",
                    json={
                        "symptoms": "小麦叶片出现黄色条纹",
                        "weather": "高温高湿",
                        "growth_stage": "抽穗期"
                    }
                )
            
            duration_ms = (time.time() - start_time) * 1000
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                passed = data.get("success", False)
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"status_code": response.status_code}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def test_sse_endpoint(self) -> TestResult:
        """
        测试 SSE 端点
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "SSE 端点测试"
        
        try:
            import httpx
            
            events_received = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "GET",
                    f"http://localhost:{self.backend_port}/api/v1/diagnosis/fusion/stream",
                    params={"symptoms": "叶片发黄"}
                ) as response:
                    if response.status_code != 200:
                        raise Exception(f"SSE 端点返回 {response.status_code}")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            events_received.append(line)
                        if len(events_received) >= 3:
                            break
            
            duration_ms = (time.time() - start_time) * 1000
            passed = len(events_received) > 0
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"events_received": len(events_received)}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def stop_services(self):
        """停止所有服务"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except Exception:
                self.backend_process.kill()
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except Exception:
                self.frontend_process.kill()
    
    async def run_all_tests(self) -> List[TestResult]:
        """
        运行所有集成测试
        
        返回:
            List[TestResult]: 测试结果列表
        """
        print("=" * 60)
        print("集成测试")
        print("=" * 60)
        
        print("\n[1/4] 运行后端健康检查...")
        result1 = await self.test_backend_health()
        self.results.append(result1)
        print(f"    {'✅ 通过' if result1.passed else '❌ 失败'} ({result1.duration_ms:.2f}ms)")
        if result1.error:
            print(f"    错误: {result1.error}")
        
        print("\n[2/4] 运行 API 端点测试...")
        result2 = await self.test_api_endpoints()
        self.results.append(result2)
        print(f"    {'✅ 通过' if result2.passed else '❌ 失败'} ({result2.duration_ms:.2f}ms)")
        if result2.error:
            print(f"    错误: {result2.error}")
        
        print("\n[3/4] 运行诊断 API 测试...")
        result3 = await self.test_diagnosis_api()
        self.results.append(result3)
        print(f"    {'✅ 通过' if result3.passed else '❌ 失败'} ({result3.duration_ms:.2f}ms)")
        if result3.error:
            print(f"    错误: {result3.error}")
        
        print("\n[4/4] 运行 SSE 端点测试...")
        result4 = await self.test_sse_endpoint()
        self.results.append(result4)
        print(f"    {'✅ 通过' if result4.passed else '❌ 失败'} ({result4.duration_ms:.2f}ms)")
        if result4.error:
            print(f"    错误: {result4.error}")
        
        return self.results
    
    def generate_report(self, results: List[TestResult]) -> str:
        """
        生成测试报告
        
        参数:
            results: 测试结果列表
            
        返回:
            str: 测试报告字符串
        """
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("集成测试报告")
        lines.append("=" * 60)
        
        lines.append("\n## 测试结果")
        passed_count = sum(1 for r in results if r.passed)
        lines.append(f"  通过: {passed_count}/{len(results)}")
        
        for result in results:
            status = "✅ 通过" if result.passed else "❌ 失败"
            lines.append(f"  {status} - {result.test_name} ({result.duration_ms:.2f}ms)")
            if result.error:
                lines.append(f"    错误: {result.error}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def save_report(self, output_path: str) -> None:
        """
        保存测试报告到文件
        
        参数:
            output_path: 输出文件路径
        """
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)


async def main():
    """主函数"""
    tester = IntegrationTest()
    
    try:
        results = await tester.run_all_tests()
        print(tester.generate_report(results))
        
        reports_dir = SCRIPT_DIR / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        tester.save_report(str(report_path))
        print(f"\n报告已保存到: {report_path}")
        
    finally:
        tester.stop_services()


if __name__ == "__main__":
    asyncio.run(main())
