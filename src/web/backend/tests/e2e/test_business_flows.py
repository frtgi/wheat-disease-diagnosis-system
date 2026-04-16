"""
业务流程端到端测试脚本

测试完整的业务流程，包括：
1. 用户注册 -> 登录 -> 诊断 -> 查看历史记录
2. 批量图像诊断流程
3. 缓存命中率测试流程
4. 性能压力测试流程
"""
import os
import sys
import time
import json
import asyncio
import statistics
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

import httpx
from httpx import AsyncClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.e2e.test_utils import (
    TestConfig,
    TestDataGenerator,
    AuthHelper,
    PerformanceMonitor,
    TestReport,
    create_e2e_client,
    setup_mock_environment,
    teardown_mock_environment
)


class BusinessFlowTester:
    """
    业务流程测试器
    
    用于测试完整的业务流程，模拟真实用户操作
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_prefix: str = "/api/v1"
    ):
        """
        初始化业务流程测试器
        
        参数:
            base_url: API 基础 URL
            api_prefix: API 前缀
        """
        self.base_url = base_url
        self.api_prefix = api_prefix
        self.config = TestConfig(base_url=base_url, api_prefix=api_prefix)
        self.monitor = PerformanceMonitor()
        self.report = TestReport("WheatAgent E2E Business Flows")
    
    async def run_all_flows(self) -> Dict[str, Any]:
        """
        运行所有业务流程测试
        
        返回:
            测试结果汇总
        """
        setup_mock_environment()
        
        try:
            print("=" * 60)
            print("WheatAgent 端到端业务流程测试")
            print("=" * 60)
            print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"API 地址: {self.base_url}")
            print()
            
            async with create_e2e_client(self.base_url, timeout=60.0) as client:
                await self._test_user_journey_flow(client)
                
                await self._test_diagnosis_flow(client)
                
                await self._test_batch_diagnosis_flow(client)
                
                await self._test_cache_flow(client)
                
                await self._test_performance_flow(client)
            
            return self._generate_summary()
            
        finally:
            teardown_mock_environment()
    
    async def _test_user_journey_flow(self, client: AsyncClient) -> None:
        """
        测试用户旅程流程
        
        完整流程：注册 -> 登录 -> 获取用户信息 -> 登出
        
        参数:
            client: 异步 HTTP 客户端
        """
        print("\n[流程 1] 用户旅程测试")
        print("-" * 40)
        
        auth_helper = AuthHelper(client, self.config)
        
        print("  步骤 1: 用户注册...")
        self.monitor.start("user_journey_register")
        register_result = await auth_helper.register_user()
        register_time = self.monitor.stop(
            success=register_result["status_code"] in [200, 201, 409]
        )
        print(f"    状态码: {register_result['status_code']}, 耗时: {register_time['duration_ms']:.2f}ms")
        
        print("  步骤 2: 用户登录...")
        self.monitor.start("user_journey_login")
        login_result = await auth_helper.login()
        login_time = self.monitor.stop(
            success=login_result["status_code"] == 200
        )
        print(f"    状态码: {login_result['status_code']}, 耗时: {login_time['duration_ms']:.2f}ms")
        
        if login_result["status_code"] == 200:
            print("  步骤 3: 获取用户信息...")
            self.monitor.start("user_journey_get_user")
            response = await client.get(
                f"{self.api_prefix}/users/me",
                headers=auth_helper.get_auth_headers()
            )
            get_user_time = self.monitor.stop(
                success=response.status_code == 200
            )
            print(f"    状态码: {response.status_code}, 耗时: {get_user_time['duration_ms']:.2f}ms")
            
            print("  步骤 4: 用户登出...")
            self.monitor.start("user_journey_logout")
            logout_result = await auth_helper.logout()
            logout_time = self.monitor.stop(
                success=logout_result["status_code"] == 200
            )
            print(f"    状态码: {logout_result['status_code']}, 耗时: {logout_time['duration_ms']:.2f}ms")
        
        self.report.record_test(
            test_name="user_journey_flow",
            success=login_result["status_code"] == 200,
            duration_ms=register_time["duration_ms"] + login_time["duration_ms"]
        )
        
        print("  ✓ 用户旅程测试完成")
    
    async def _test_diagnosis_flow(self, client: AsyncClient) -> None:
        """
        测试诊断流程
        
        完整流程：图像诊断 -> 文本诊断 -> 融合诊断
        
        参数:
            client: 异步 HTTP 客户端
        """
        print("\n[流程 2] 诊断流程测试")
        print("-" * 40)
        
        auth_helper = AuthHelper(client, self.config)
        await auth_helper.ensure_authenticated()
        headers = auth_helper.get_auth_headers()
        
        print("  步骤 1: 图像诊断...")
        image_bytes = TestDataGenerator.generate_test_image()
        self.monitor.start("diagnosis_flow_image")
        
        files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
        data = {"symptoms": "叶片出现黄色斑点"}
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/image",
            files=files,
            data=data,
            headers=headers
        )
        image_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {image_time['duration_ms']:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print(f"    诊断结果: {result.get('disease_name', 'N/A')}")
        
        print("  步骤 2: 文本诊断...")
        symptoms = TestDataGenerator.generate_symptoms_text("条锈病")
        self.monitor.start("diagnosis_flow_text")
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/text",
            data={"symptoms": symptoms},
            headers=headers
        )
        text_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {text_time['duration_ms']:.2f}ms")
        
        print("  步骤 3: 多模态融合诊断...")
        self.monitor.start("diagnosis_flow_fusion")
        
        files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
        data = {
            "symptoms": symptoms,
            "enable_thinking": "true",
            "use_graph_rag": "true"
        }
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/fusion",
            files=files,
            data=data
        )
        fusion_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {fusion_time['duration_ms']:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            diagnosis = result.get("diagnosis", {})
            print(f"    诊断结果: {diagnosis.get('disease_name', 'N/A')}")
            print(f"    置信度: {diagnosis.get('confidence', 0):.2%}")
        
        print("  步骤 4: 查询诊断记录...")
        self.monitor.start("diagnosis_flow_records")
        
        response = await client.get(
            f"{self.api_prefix}/diagnosis/records",
            headers=headers
        )
        records_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {records_time['duration_ms']:.2f}ms")
        
        if response.status_code == 200:
            records = response.json()
            print(f"    记录数: {records.get('total', 0)}")
        
        self.report.record_test(
            test_name="diagnosis_flow",
            success=True,
            duration_ms=image_time["duration_ms"] + text_time["duration_ms"] + fusion_time["duration_ms"]
        )
        
        print("  ✓ 诊断流程测试完成")
    
    async def _test_batch_diagnosis_flow(self, client: AsyncClient) -> None:
        """
        测试批量诊断流程
        
        参数:
            client: 异步 HTTP 客户端
        """
        print("\n[流程 3] 批量诊断测试")
        print("-" * 40)
        
        num_images = 3
        print(f"  批量上传 {num_images} 张图像进行诊断...")
        
        self.monitor.start("batch_diagnosis")
        
        files = []
        for i in range(num_images):
            image_bytes = TestDataGenerator.generate_test_image()
            files.append(("images", (f"test_wheat_{i}.jpg", image_bytes, "image/jpeg")))
        
        data = {
            "symptoms": "小麦叶片出现病斑",
            "thinking_mode": "false",
            "use_cache": "true"
        }
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/batch",
            files=files,
            data=data
        )
        
        batch_time = self.monitor.stop(
            success=response.status_code == 200
        )
        
        print(f"    状态码: {response.status_code}, 耗时: {batch_time['duration_ms']:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get("summary", {})
            print(f"    总图像数: {summary.get('total_images', 0)}")
            print(f"    成功数: {summary.get('success_count', 0)}")
            print(f"    缓存命中: {summary.get('cache_hits', 0)}")
            print(f"    成功率: {summary.get('success_rate', 0):.1f}%")
        
        self.report.record_test(
            test_name="batch_diagnosis_flow",
            success=response.status_code == 200,
            duration_ms=batch_time["duration_ms"]
        )
        
        print("  ✓ 批量诊断测试完成")
    
    async def _test_cache_flow(self, client: AsyncClient) -> None:
        """
        测试缓存流程
        
        参数:
            client: 异步 HTTP 客户端
        """
        print("\n[流程 4] 缓存功能测试")
        print("-" * 40)
        
        print("  步骤 1: 清空缓存...")
        self.monitor.start("cache_clear")
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/cache/clear"
        )
        clear_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {clear_time['duration_ms']:.2f}ms")
        
        print("  步骤 2: 第一次诊断（缓存未命中）...")
        image_bytes = TestDataGenerator.generate_test_image()
        symptoms = "测试缓存功能的症状描述"
        
        self.monitor.start("cache_first_diagnosis")
        
        files = {"image": ("cache_test.jpg", image_bytes, "image/jpeg")}
        data = {"symptoms": symptoms, "use_cache": "true"}
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/multimodal",
            files=files,
            data=data
        )
        first_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {first_time['duration_ms']:.2f}ms")
        
        print("  步骤 3: 第二次诊断（相同输入，应命中缓存）...")
        self.monitor.start("cache_second_diagnosis")
        
        files = {"image": ("cache_test.jpg", image_bytes, "image/jpeg")}
        data = {"symptoms": symptoms, "use_cache": "true"}
        
        response = await client.post(
            f"{self.api_prefix}/diagnosis/multimodal",
            files=files,
            data=data
        )
        second_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {second_time['duration_ms']:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            cache_info = result.get("cache_info", {})
            if cache_info.get("hit"):
                print(f"    ✓ 缓存命中！来源: {cache_info.get('source', 'N/A')}")
            else:
                print("    ⚠ 缓存未命中")
        
        print("  步骤 4: 获取缓存统计...")
        self.monitor.start("cache_stats")
        
        response = await client.get(
            f"{self.api_prefix}/diagnosis/cache/stats"
        )
        stats_time = self.monitor.stop(
            success=response.status_code == 200
        )
        print(f"    状态码: {response.status_code}, 耗时: {stats_time['duration_ms']:.2f}ms")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"    缓存统计: {json.dumps(stats.get('data', {}), ensure_ascii=False)[:100]}...")
        
        self.report.record_test(
            test_name="cache_flow",
            success=True,
            duration_ms=first_time["duration_ms"] + second_time["duration_ms"]
        )
        
        print("  ✓ 缓存功能测试完成")
    
    async def _test_performance_flow(self, client: AsyncClient) -> None:
        """
        测试性能流程
        
        参数:
            client: 异步 HTTP 客户端
        """
        print("\n[流程 5] 性能压力测试")
        print("-" * 40)
        
        num_requests = 10
        print(f"  发送 {num_requests} 次诊断请求...")
        
        latencies = []
        success_count = 0
        
        for i in range(num_requests):
            self.monitor.start(f"perf_test_{i}")
            
            symptoms = TestDataGenerator.generate_symptoms_text()
            
            response = await client.post(
                f"{self.api_prefix}/diagnosis/text",
                data={"symptoms": symptoms}
            )
            
            result = self.monitor.stop(
                success=response.status_code == 200
            )
            
            latencies.append(result["duration_ms"])
            if response.status_code == 200:
                success_count += 1
            
            if (i + 1) % 5 == 0:
                print(f"    进度: {i + 1}/{num_requests}")
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            p50_latency = statistics.median(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 5 else max(latencies)
            
            print(f"\n  性能统计:")
            print(f"    平均延迟: {avg_latency:.2f}ms")
            print(f"    P50 延迟: {p50_latency:.2f}ms")
            print(f"    P95 延迟: {p95_latency:.2f}ms")
            print(f"    成功率: {success_count}/{num_requests} ({success_count/num_requests*100:.1f}%)")
        
        self.report.record_test(
            test_name="performance_flow",
            success=success_count == num_requests,
            duration_ms=sum(latencies)
        )
        
        print("  ✓ 性能压力测试完成")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """
        生成测试汇总
        
        返回:
            测试汇总字典
        """
        report = self.report.finalize()
        stats = self.monitor.get_statistics()
        
        print("\n" + "=" * 60)
        print("测试汇总")
        print("=" * 60)
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过: {report['summary']['passed']}")
        print(f"失败: {report['summary']['failed']}")
        print(f"通过率: {report['summary']['pass_rate']:.1f}%")
        print(f"\n性能统计:")
        print(f"  总操作数: {stats['total_operations']}")
        print(f"  平均耗时: {stats['avg_duration_ms']:.2f}ms")
        print(f"  最小耗时: {stats['min_duration_ms']:.2f}ms")
        print(f"  最大耗时: {stats['max_duration_ms']:.2f}ms")
        
        slow_ops = self.monitor.get_slow_operation(threshold_ms=1000.0)
        if slow_ops:
            print(f"\n慢操作 (>1000ms):")
            for op in slow_ops:
                print(f"  - {op['operation']}: {op['duration_ms']:.2f}ms")
        
        report_dir = Path(__file__).parent / "reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"business_flows_{timestamp}.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "report": report,
                "performance": stats
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试报告已保存到: {report_path}")
        
        return {
            "report": report,
            "performance": stats
        }


class ConcurrentTester:
    """
    并发测试器
    
    用于测试系统在高并发场景下的表现
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_prefix: str = "/api/v1"
    ):
        """
        初始化并发测试器
        
        参数:
            base_url: API 基础 URL
            api_prefix: API 前缀
        """
        self.base_url = base_url
        self.api_prefix = api_prefix
    
    async def run_concurrent_diagnosis(
        self,
        num_concurrent: int = 5,
        total_requests: int = 20
    ) -> Dict[str, Any]:
        """
        运行并发诊断测试
        
        参数:
            num_concurrent: 并发数
            total_requests: 总请求数
        
        返回:
            测试结果
        """
        setup_mock_environment()
        
        try:
            print(f"\n并发测试: {num_concurrent} 并发, {total_requests} 总请求")
            print("-" * 40)
            
            semaphore = asyncio.Semaphore(num_concurrent)
            results = []
            start_time = time.time()
            
            async def single_request(request_id: int) -> Dict[str, Any]:
                """
                单个请求
                
                参数:
                    request_id: 请求 ID
                
                返回:
                    请求结果
                """
                async with semaphore:
                    request_start = time.time()
                    
                    async with AsyncClient(base_url=self.base_url, timeout=30.0) as client:
                        symptoms = TestDataGenerator.generate_symptoms_text()
                        
                        try:
                            response = await client.post(
                                f"{self.api_prefix}/diagnosis/text",
                                data={"symptoms": symptoms}
                            )
                            
                            return {
                                "request_id": request_id,
                                "status_code": response.status_code,
                                "duration_ms": (time.time() - request_start) * 1000,
                                "success": response.status_code == 200
                            }
                        except Exception as e:
                            return {
                                "request_id": request_id,
                                "status_code": 0,
                                "duration_ms": (time.time() - request_start) * 1000,
                                "success": False,
                                "error": str(e)
                            }
            
            tasks = [single_request(i) for i in range(total_requests)]
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            
            success_count = sum(1 for r in results if r["success"])
            durations = [r["duration_ms"] for r in results]
            
            summary = {
                "total_requests": total_requests,
                "concurrent_limit": num_concurrent,
                "success_count": success_count,
                "failed_count": total_requests - success_count,
                "success_rate": round(success_count / total_requests * 100, 2),
                "total_time_ms": round(total_time * 1000, 2),
                "avg_latency_ms": round(statistics.mean(durations), 2) if durations else 0,
                "p50_latency_ms": round(statistics.median(durations), 2) if durations else 0,
                "p95_latency_ms": round(sorted(durations)[int(len(durations) * 0.95)], 2) if len(durations) > 5 else 0,
                "throughput_rps": round(total_requests / total_time, 2)
            }
            
            print(f"  成功率: {summary['success_rate']}%")
            print(f"  平均延迟: {summary['avg_latency_ms']:.2f}ms")
            print(f"  P95 延迟: {summary['p95_latency_ms']:.2f}ms")
            print(f"  吞吐量: {summary['throughput_rps']} req/s")
            
            return summary
            
        finally:
            teardown_mock_environment()


async def main():
    """
    主函数
    
    运行所有业务流程测试
    """
    base_url = os.getenv("TEST_BASE_URL", "http://localhost:8000")
    
    tester = BusinessFlowTester(base_url=base_url)
    results = await tester.run_all_flows()
    
    concurrent_tester = ConcurrentTester(base_url=base_url)
    concurrent_results = await concurrent_tester.run_concurrent_diagnosis(
        num_concurrent=5,
        total_requests=10
    )
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
    
    return 0 if results["report"]["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
