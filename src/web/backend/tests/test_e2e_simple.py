"""
端到端测试脚本（简化版 - 使用 requests 库）

测试所有功能：
1. API 功能测试（单图像、批量、缓存）
2. 性能测试（延迟、吞吐量）
3. 缓存命中率测试
4. 监控和日志测试
"""

import time
import hashlib
import requests
import statistics
import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime


class EndToEndTester:
    """端到端测试器（同步版本）"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化测试器
        
        Args:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            "api_tests": [],
            "performance_tests": [],
            "cache_tests": [],
            "monitoring_tests": []
        }
    
    def test_health(self) -> Dict[str, Any]:
        """测试健康检查端点"""
        try:
            # 根健康检查
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            root_health = response.status_code == 200
            
            # AI 健康检查
            response = self.session.get(f"{self.base_url}/api/v1/health/ai", timeout=5)
            ai_health = response.status_code == 200
            
            return {
                "test": "health_check",
                "success": root_health and ai_health,
                "root_health": root_health,
                "ai_health": ai_health
            }
        except Exception as e:
            return {
                "test": "health_check",
                "success": False,
                "error": str(e)
            }
    
    def test_single_diagnosis(self) -> Dict[str, Any]:
        """测试单图像诊断（无图像，仅文本）"""
        url = f"{self.base_url}/api/v1/diagnosis/multimodal"
        
        try:
            # 准备测试数据（仅文本，不上传图像）
            data = {
                "symptoms": "小麦叶片出现黄色条纹",
                "thinking_mode": "true",
                "use_graph_rag": "true",
                "use_cache": "true"
            }
            
            start_time = time.time()
            response = self.session.post(url, data=data, timeout=30)
            latency = (time.time() - start_time) * 1000
            
            result = response.json() if response.status_code == 200 else None
            
            return {
                "test": "single_diagnosis",
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "latency_ms": round(latency, 2),
                "result": result,
                "cache_hit": result.get("cache_info", {}).get("hit", False) if result and result.get("success") else False
            }
        except Exception as e:
            return {
                "test": "single_diagnosis",
                "success": False,
                "error": str(e)
            }
    
    def test_cache_stats(self) -> Dict[str, Any]:
        """测试缓存统计"""
        url = f"{self.base_url}/api/v1/diagnosis/cache/stats"
        
        try:
            response = self.session.get(url, timeout=5)
            result = response.json() if response.status_code == 200 else None
            
            return {
                "test": "cache_stats",
                "success": response.status_code == 200,
                "result": result
            }
        except Exception as e:
            return {
                "test": "cache_stats",
                "success": False,
                "error": str(e)
            }
    
    def test_metrics(self) -> Dict[str, Any]:
        """测试性能指标"""
        url = f"{self.base_url}/api/v1/metrics/"
        
        try:
            response = self.session.get(url, timeout=5)
            result = response.json() if response.status_code == 200 else None
            
            return {
                "test": "metrics",
                "success": response.status_code == 200,
                "result": result
            }
        except Exception as e:
            return {
                "test": "metrics",
                "success": False,
                "error": str(e)
            }
    
    def test_logs(self) -> Dict[str, Any]:
        """测试日志 API"""
        url = f"{self.base_url}/api/v1/logs/statistics"
        
        try:
            response = self.session.get(url, timeout=5)
            result = response.json() if response.status_code == 200 else None
            
            return {
                "test": "logs",
                "success": response.status_code == 200,
                "result": result
            }
        except Exception as e:
            return {
                "test": "logs",
                "success": False,
                "error": str(e)
            }
    
    def test_alerts(self) -> Dict[str, Any]:
        """测试告警 API"""
        url = f"{self.base_url}/api/v1/metrics/alerts"
        
        try:
            response = self.session.get(url, timeout=5)
            result = response.json() if response.status_code == 200 else None
            
            return {
                "test": "alerts",
                "success": response.status_code == 200,
                "result": result
            }
        except Exception as e:
            return {
                "test": "alerts",
                "success": False,
                "error": str(e)
            }
    
    def run_all_tests(self, num_requests: int = 10) -> Dict[str, Any]:
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
        print(f"测试时间：{datetime.now().isoformat()}")
        print("=" * 60)
        
        # 1. 健康检查
        print("\n=== 健康检查 ===")
        health_result = self.test_health()
        print(f"根健康检查：{'✓' if health_result.get('root_health') else '✗'}")
        print(f"AI 健康检查：{'✓' if health_result.get('ai_health') else '✗'}")
        
        # 2. 功能测试
        print("\n=== API 功能测试 ===")
        
        # 单次诊断测试
        single_result = self.test_single_diagnosis()
        print(f"单图像诊断：{'✓' if single_result['success'] else '✗'} "
              f"延迟：{single_result.get('latency_ms', 'N/A')}ms "
              f"缓存命中：{'✓' if single_result.get('cache_hit') else '✗'}")
        
        # 缓存统计测试
        cache_result = self.test_cache_stats()
        print(f"缓存统计：{'✓' if cache_result['success'] else '✗'}")
        
        # 性能指标测试
        metrics_result = self.test_metrics()
        print(f"性能指标：{'✓' if metrics_result['success'] else '✗'}")
        
        # 日志 API 测试
        logs_result = self.test_logs()
        print(f"日志统计：{'✓' if logs_result['success'] else '✗'}")
        
        # 告警 API 测试
        alerts_result = self.test_alerts()
        print(f"告警系统：{'✓' if alerts_result['success'] else '✗'}")
        
        # 3. 性能测试（多次请求）
        print(f"\n=== 性能测试 ({num_requests} 次请求) ===")
        latencies = []
        cache_hits = 0
        
        for i in range(num_requests):
            result = self.test_single_diagnosis()
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
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)
            p95_latency = sorted(latencies)[p95_idx] if len(latencies) > 20 else max(latencies)
            p99_latency = sorted(latencies)[p99_idx] if len(latencies) > 100 else max(latencies)
            cache_hit_rate = cache_hits / num_requests * 100
            
            print(f"\n性能统计:")
            print(f"  平均延迟：{avg_latency:.2f}ms")
            print(f"  P50 延迟：{p50_latency:.2f}ms")
            print(f"  P95 延迟：{p95_latency:.2f}ms")
            print(f"  P99 延迟：{p99_latency:.2f}ms")
            print(f"  缓存命中率：{cache_hit_rate:.2f}%")
        
        # 4. 汇总结果
        all_tests_passed = all([
            health_result.get("success", False) or (health_result.get("root_health") and health_result.get("ai_health")),
            single_result.get("success", False),
            cache_result.get("success", False),
            metrics_result.get("success", False),
            logs_result.get("success", False),
            alerts_result.get("success", False)
        ])
        
        summary = {
            "all_tests_passed": all_tests_passed,
            "api_tests": {
                "health_check": health_result,
                "single_diagnosis": single_result,
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
                "p99_latency_ms": round(p99_latency, 2) if latencies else 0,
                "cache_hit_rate": round(cache_hit_rate, 2) if latencies else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n{'=' * 60}")
        print(f"=== 测试总结 ===")
        print(f"所有 API 测试：{'✓ 通过' if all_tests_passed else '✗ 失败'}")
        print(f"性能测试完成：{len(latencies)}/{num_requests} 成功")
        print(f"测试报告已保存：tests/e2e_test_results.json")
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_file: str = "tests/e2e_test_results.json") -> None:
        """保存测试结果到文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"测试结果已保存到：{output_path}")


def main():
    """主函数"""
    tester = EndToEndTester(base_url="http://localhost:8000")
    results = tester.run_all_tests(num_requests=10)
    
    # 保存结果
    tester.save_results(results)
    
    # 返回退出码
    return 0 if results["all_tests_passed"] else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
