"""
端到端测试脚本

测试所有功能：
1. API 功能测试（单图像、批量、缓存）
2. 性能测试（延迟、吞吐量）
3. 缓存命中率测试
4. 监控和日志测试
"""

import asyncio
import time
import hashlib
import aiohttp
import statistics
from typing import List, Dict, Any
from pathlib import Path


class EndToEndTester:
    """端到端测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化测试器
        
        Args:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.results = {
            "api_tests": [],
            "performance_tests": [],
            "cache_tests": [],
            "monitoring_tests": []
        }
    
    def _generate_test_image(self) -> bytes:
        """生成测试图像（简化版，实际应使用真实图像）"""
        # 这里使用占位符，实际测试应该使用真实的小麦病害图像
        return b"test_image_data"
    
    async def test_single_diagnosis(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """测试单图像诊断"""
        url = f"{self.base_url}/api/v1/diagnosis/multimodal"
        
        # 准备测试数据
        data = aiohttp.FormData()
        data.add_field("symptoms", "小麦叶片出现黄色条纹")
        data.add_field("thinking_mode", "true")
        data.add_field("use_graph_rag", "true")
        data.add_field("use_cache", "true")
        
        # 添加图像（如果有）
        test_image_path = Path("tests/test_image.jpg")
        if test_image_path.exists():
            data.add_field(
                "image",
                test_image_path.open("rb"),
                filename="test_image.jpg",
                content_type="image/jpeg"
            )
        
        start_time = time.time()
        try:
            async with session.post(url, data=data) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                return {
                    "test": "single_diagnosis",
                    "success": response.status == 200,
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "result": result,
                    "cache_hit": result.get("cache_info", {}).get("hit", False) if result.get("success") else False
                }
        except Exception as e:
            return {
                "test": "single_diagnosis",
                "success": False,
                "error": str(e)
            }
    
    async def test_batch_diagnosis(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """测试批量诊断"""
        url = f"{self.base_url}/api/v1/diagnosis/batch"
        
        # 准备测试数据
        data = aiohttp.FormData()
        data.add_field("symptoms", "小麦叶片病斑")
        data.add_field("thinking_mode", "false")
        data.add_field("use_cache", "true")
        
        # 添加多张图像（如果有）
        test_image_path = Path("tests/test_image.jpg")
        if test_image_path.exists():
            for i in range(3):  # 3 张图像
                data.add_field(
                    f"images",
                    test_image_path.open("rb"),
                    filename=f"test_image_{i}.jpg",
                    content_type="image/jpeg"
                )
        
        start_time = time.time()
        try:
            async with session.post(url, data=data) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                return {
                    "test": "batch_diagnosis",
                    "success": response.status == 200,
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "result": result,
                    "cache_hit_rate": result.get("summary", {}).get("cache_hit_rate", 0)
                }
        except Exception as e:
            return {
                "test": "batch_diagnosis",
                "success": False,
                "error": str(e)
            }
    
    async def test_cache_stats(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """测试缓存统计"""
        url = f"{self.base_url}/api/v1/diagnosis/cache/stats"
        
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                return {
                    "test": "cache_stats",
                    "success": response.status == 200,
                    "result": result
                }
        except Exception as e:
            return {
                "test": "cache_stats",
                "success": False,
                "error": str(e)
            }
    
    async def test_metrics(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """测试性能指标"""
        url = f"{self.base_url}/api/v1/metrics/"
        
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                return {
                    "test": "metrics",
                    "success": response.status == 200,
                    "result": result
                }
        except Exception as e:
            return {
                "test": "metrics",
                "success": False,
                "error": str(e)
            }
    
    async def test_logs(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """测试日志 API"""
        url = f"{self.base_url}/api/v1/logs/statistics"
        
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                return {
                    "test": "logs",
                    "success": response.status == 200,
                    "result": result
                }
        except Exception as e:
            return {
                "test": "logs",
                "success": False,
                "error": str(e)
            }
    
    async def test_alerts(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """测试告警 API"""
        url = f"{self.base_url}/api/v1/metrics/alerts"
        
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                return {
                    "test": "alerts",
                    "success": response.status == 200,
                    "result": result
                }
        except Exception as e:
            return {
                "test": "alerts",
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self, num_requests: int = 10) -> Dict[str, Any]:
        """
        运行所有测试
        
        Args:
            num_requests: 测试请求数量
        
        Returns:
            测试结果汇总
        """
        print(f"开始端到端测试...")
        print(f"API 地址：{self.base_url}")
        print(f"测试请求数：{num_requests}")
        
        async with aiohttp.ClientSession() as session:
            # 1. 功能测试
            print("\n=== 功能测试 ===")
            
            # 单次诊断测试
            single_result = await self.test_single_diagnosis(session)
            print(f"单图像诊断：{'✓' if single_result['success'] else '✗'} "
                  f"延迟：{single_result.get('latency_ms', 'N/A')}ms")
            
            # 批量诊断测试
            batch_result = await self.test_batch_diagnosis(session)
            print(f"批量诊断：{'✓' if batch_result['success'] else '✗'} "
                  f"延迟：{batch_result.get('latency_ms', 'N/A')}ms")
            
            # 缓存统计测试
            cache_result = await self.test_cache_stats(session)
            print(f"缓存统计：{'✓' if cache_result['success'] else '✗'}")
            
            # 性能指标测试
            metrics_result = await self.test_metrics(session)
            print(f"性能指标：{'✓' if metrics_result['success'] else '✗'}")
            
            # 日志 API 测试
            logs_result = await self.test_logs(session)
            print(f"日志统计：{'✓' if logs_result['success'] else '✗'}")
            
            # 告警 API 测试
            alerts_result = await self.test_alerts(session)
            print(f"告警系统：{'✓' if alerts_result['success'] else '✗'}")
            
            # 2. 性能测试（多次请求）
            print(f"\n=== 性能测试 ({num_requests} 次请求) ===")
            latencies = []
            cache_hits = 0
            
            for i in range(num_requests):
                result = await self.test_single_diagnosis(session)
                if result.get("success"):
                    latencies.append(result.get("latency_ms", 0))
                    if result.get("cache_hit"):
                        cache_hits += 1
                
                if (i + 1) % 5 == 0:
                    print(f"  进度：{i + 1}/{num_requests}")
            
            # 计算性能指标
            if latencies:
                avg_latency = statistics.mean(latencies)
                p50_latency = statistics.median(latencies)
                p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies)
                cache_hit_rate = cache_hits / num_requests * 100
                
                print(f"\n平均延迟：{avg_latency:.2f}ms")
                print(f"P50 延迟：{p50_latency:.2f}ms")
                print(f"P95 延迟：{p95_latency:.2f}ms")
                print(f"缓存命中率：{cache_hit_rate:.2f}%")
            
            # 3. 汇总结果
            all_tests_passed = all([
                single_result.get("success", False),
                batch_result.get("success", False),
                cache_result.get("success", False),
                metrics_result.get("success", False),
                logs_result.get("success", False),
                alerts_result.get("success", False)
            ])
            
            summary = {
                "all_tests_passed": all_tests_passed,
                "api_tests": {
                    "single_diagnosis": single_result,
                    "batch_diagnosis": batch_result,
                    "cache_stats": cache_result,
                    "metrics": metrics_result,
                    "logs": logs_result,
                    "alerts": alerts_result
                },
                "performance": {
                    "total_requests": num_requests,
                    "successful_requests": len(latencies),
                    "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
                    "p50_latency_ms": round(p50_latency, 2) if latencies else 0,
                    "p95_latency_ms": round(p95_latency, 2) if latencies else 0,
                    "cache_hit_rate": round(cache_hit_rate, 2) if latencies else 0
                },
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            print(f"\n=== 测试总结 ===")
            print(f"所有 API 测试：{'✓ 通过' if all_tests_passed else '✗ 失败'}")
            print(f"性能测试完成：{len(latencies)}/{num_requests} 成功")
            
            return summary


async def main():
    """主函数"""
    tester = EndToEndTester(base_url="http://localhost:8000")
    results = await tester.run_all_tests(num_requests=10)
    
    # 保存结果
    import json
    from pathlib import Path
    
    output_file = Path("tests/e2e_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n测试结果已保存到：{output_file}")
    
    # 返回退出码
    return 0 if results["all_tests_passed"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
