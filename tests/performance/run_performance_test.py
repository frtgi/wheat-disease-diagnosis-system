# -*- coding: utf-8 -*-
"""
WheatAgent 后端服务性能测试脚本 - 精简版

直接测试 API 响应时间，排除沙箱环境影响
"""
import os
import sys
import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

import requests

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_endpoint_performance(
    base_url: str,
    endpoint: str,
    method: str = "GET",
    data: Dict = None,
    iterations: int = 10,
    target_ms: float = 100.0
) -> Dict[str, Any]:
    """
    测试单个 API 端点的响应时间
    
    参数:
        base_url: 服务基础 URL
        endpoint: API 端点路径
        method: HTTP 方法
        data: 请求数据
        iterations: 测试迭代次数
        target_ms: 目标响应时间（毫秒）
        
    返回:
        Dict[str, Any]: 测试结果
    """
    url = f"{base_url}{endpoint}"
    latencies = []
    errors = []
    
    for i in range(iterations):
        try:
            start = time.perf_counter()
            
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, data=data, timeout=60)
            else:
                continue
                
            elapsed = (time.perf_counter() - start) * 1000
            
            if response.status_code >= 200 and response.status_code < 300:
                latencies.append(elapsed)
            else:
                errors.append(f"HTTP {response.status_code}")
                
        except Exception as e:
            errors.append(str(e))
    
    if not latencies:
        return {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "success_count": 0,
            "fail_count": len(errors),
            "avg_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0,
            "target_ms": target_ms,
            "passed": False,
            "errors": errors
        }
    
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    return {
        "endpoint": endpoint,
        "method": method,
        "iterations": iterations,
        "success_count": len(latencies),
        "fail_count": len(errors),
        "avg_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "p50_ms": round(sorted_latencies[int(n * 0.50)], 2),
        "p95_ms": round(sorted_latencies[int(n * 0.95)], 2) if n >= 20 else round(sorted_latencies[-1], 2),
        "p99_ms": round(sorted_latencies[int(n * 0.99)], 2) if n >= 100 else round(sorted_latencies[-1], 2),
        "target_ms": target_ms,
        "passed": statistics.mean(latencies) < target_ms,
        "errors": errors[:5]
    }


def check_gpu_status() -> Dict[str, Any]:
    """
    检查 GPU 状态
    
    返回:
        Dict[str, Any]: GPU 状态信息
    """
    gpu_info = {
        "available": False,
        "device_name": "",
        "total_memory_gb": 0,
        "allocated_gb": 0,
        "reserved_gb": 0
    }
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            gpu_info["total_memory_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
            )
            gpu_info["allocated_gb"] = round(
                torch.cuda.memory_allocated(0) / (1024**3), 2
            )
            gpu_info["reserved_gb"] = round(
                torch.cuda.memory_reserved(0) / (1024**3), 2
            )
    except ImportError:
        pass
    
    return gpu_info


def check_model_status(base_url: str) -> Dict[str, Any]:
    """
    检查模型加载状态
    
    参数:
        base_url: 服务基础 URL
        
    返回:
        Dict[str, Any]: 模型状态信息
    """
    try:
        response = requests.get(f"{base_url}/api/v1/diagnosis/health/ai", timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def run_concurrency_test(
    base_url: str,
    concurrent_users: int,
    requests_per_user: int,
    endpoint: str = "/health"
) -> Dict[str, Any]:
    """
    执行并发测试
    
    参数:
        base_url: 服务基础 URL
        concurrent_users: 并发用户数
        requests_per_user: 每用户请求数
        endpoint: 测试端点
        
    返回:
        Dict[str, Any]: 并发测试结果
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    total_requests = concurrent_users * requests_per_user
    latencies = []
    errors = []
    success_count = 0
    fail_count = 0
    
    def worker(user_id: int) -> List[float]:
        results = []
        for _ in range(requests_per_user):
            try:
                start = time.perf_counter()
                response = requests.get(f"{base_url}{endpoint}", timeout=30)
                elapsed = (time.perf_counter() - start) * 1000
                if response.status_code >= 200 and response.status_code < 300:
                    results.append(elapsed)
                else:
                    results.append(-1)
            except Exception:
                results.append(-1)
        return results
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = {executor.submit(worker, i): i for i in range(concurrent_users)}
        
        for future in as_completed(futures):
            try:
                results = future.result()
                for r in results:
                    if r > 0:
                        latencies.append(r)
                        success_count += 1
                    else:
                        fail_count += 1
            except Exception as e:
                fail_count += requests_per_user
                errors.append(str(e))
    
    total_time = time.time() - start_time
    
    if not latencies:
        return {
            "concurrent_users": concurrent_users,
            "total_requests": total_requests,
            "success_count": success_count,
            "fail_count": fail_count,
            "success_rate": 0,
            "avg_response_ms": 0,
            "throughput_rps": 0,
            "errors": errors
        }
    
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    return {
        "concurrent_users": concurrent_users,
        "total_requests": total_requests,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": round(success_count / total_requests * 100, 2),
        "avg_response_ms": round(statistics.mean(latencies), 2),
        "p95_response_ms": round(sorted_latencies[int(n * 0.95)], 2) if n >= 20 else round(sorted_latencies[-1], 2),
        "throughput_rps": round(success_count / total_time, 2),
        "errors": errors[:5]
    }


def run_performance_tests(base_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
    """
    执行所有性能测试
    
    参数:
        base_url: 服务基础 URL
        
    返回:
        Dict[str, Any]: 测试结果
    """
    print("=" * 70)
    print("🚀 WheatAgent 后端服务性能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标服务: {base_url}")
    print("=" * 70)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "api_tests": {},
        "concurrency_tests": [],
        "gpu_status": {},
        "model_status": {},
        "summary": {}
    }
    
    test_cases = [
        {"name": "health", "endpoint": "/health", "method": "GET", "target_ms": 50, "iterations": 10},
        {"name": "ai_health", "endpoint": "/api/v1/diagnosis/health/ai", "method": "GET", "target_ms": 100, "iterations": 10},
        {"name": "knowledge_search", "endpoint": "/api/v1/knowledge/search", "method": "GET", "target_ms": 100, "iterations": 10},
        {"name": "stats_overview", "endpoint": "/api/v1/stats/overview", "method": "GET", "target_ms": 100, "iterations": 10},
    ]
    
    print("\n📊 API 响应时间测试")
    print("-" * 70)
    
    for case in test_cases:
        name = case["name"]
        print(f"\n测试: {name} ({case['method']} {case['endpoint']})")
        print(f"  目标: < {case['target_ms']}ms")
        
        result = test_endpoint_performance(
            base_url=base_url,
            endpoint=case["endpoint"],
            method=case["method"],
            iterations=case["iterations"],
            target_ms=case["target_ms"]
        )
        
        results["api_tests"][name] = result
        
        status = "✅ 通过" if result["passed"] else "❌ 未达标"
        print(f"  平均: {result['avg_ms']}ms")
        print(f"  P95: {result['p95_ms']}ms")
        print(f"  状态: {status}")
    
    print("\n" + "=" * 70)
    print("📊 并发测试")
    print("-" * 70)
    
    concurrency_configs = [
        {"users": 10, "requests_per_user": 5},
        {"users": 50, "requests_per_user": 3}
    ]
    
    for config in concurrency_configs:
        print(f"\n并发测试: {config['users']} 用户, 每用户 {config['requests_per_user']} 请求")
        
        result = run_concurrency_test(
            base_url=base_url,
            concurrent_users=config["users"],
            requests_per_user=config["requests_per_user"]
        )
        
        results["concurrency_tests"].append(result)
        
        print(f"  成功率: {result['success_rate']}%")
        print(f"  平均响应: {result['avg_response_ms']}ms")
        print(f"  吞吐量: {result['throughput_rps']} req/s")
    
    print("\n" + "=" * 70)
    print("🖥️  GPU 状态检查")
    print("-" * 70)
    
    gpu_status = check_gpu_status()
    results["gpu_status"] = gpu_status
    
    if gpu_status["available"]:
        print(f"  GPU 设备: {gpu_status['device_name']}")
        print(f"  总显存: {gpu_status['total_memory_gb']} GB")
        print(f"  已分配: {gpu_status['allocated_gb']} GB")
        print(f"  已预留: {gpu_status['reserved_gb']} GB")
    else:
        print("  CUDA 不可用")
    
    print("\n" + "=" * 70)
    print("🤖 模型状态检查")
    print("-" * 70)
    
    model_status = check_model_status(base_url)
    results["model_status"] = model_status
    
    if "services" in model_status:
        services = model_status["services"]
        
        if "yolov8" in services:
            yolo = services["yolov8"]
            status = "✅ 已加载" if yolo.get("is_loaded") else "❌ 未加载"
            print(f"  YOLO 模型: {status}")
            print(f"    类型: {yolo.get('model_type', 'unknown')}")
        
        if "qwen3vl" in services:
            qwen = services["qwen3vl"]
            status = "✅ 已加载" if qwen.get("is_loaded") else "❌ 未加载"
            print(f"  Qwen 模型: {status}")
            print(f"    类型: {qwen.get('model_type', 'unknown')}")
            print(f"    设备: {qwen.get('device', 'unknown')}")
            print(f"    INT4: {qwen.get('features', {}).get('int4_quantization', False)}")
        
        print(f"  整体状态: {model_status.get('status', 'unknown')}")
    else:
        print(f"  获取模型状态失败: {model_status.get('error', 'unknown')}")
    
    passed_count = sum(1 for r in results["api_tests"].values() if r.get("passed", False))
    total_count = len(results["api_tests"])
    
    results["summary"] = {
        "api_pass_rate": round(passed_count / total_count * 100, 2) if total_count > 0 else 0,
        "passed_tests": passed_count,
        "total_tests": total_count
    }
    
    print("\n" + "=" * 70)
    print("📋 测试摘要")
    print("-" * 70)
    print(f"  API 测试通过率: {passed_count}/{total_count}")
    
    for name, result in results["api_tests"].items():
        status = "✅" if result.get("passed", False) else "❌"
        print(f"  {status} {name}: {result.get('avg_ms', 0):.2f}ms (目标: < {result.get('target_ms', 0)}ms)")
    
    print("\n" + "=" * 70)
    print("✅ 性能测试完成")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    results = run_performance_tests()
    
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存: {output_file}")
