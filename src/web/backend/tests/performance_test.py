"""
API 性能测试脚本
测试优化后的 API 响应时间和缓存命中率
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import json
from datetime import datetime


class PerformanceTester:
    """
    API 性能测试器
    
    功能：
    1. 测试 API 响应时间
    2. 测试缓存命中率
    3. 生成性能报告
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化性能测试器
        
        Args:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        self.access_token = None
    
    async def login(self, username: str, password: str) -> bool:
        """
        登录获取访问令牌
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            是否登录成功
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/users/login",
                    json={"username": username, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["data"]["access_token"]
                    print(f"[OK] Login successful: {username}")
                    return True
                else:
                    print(f"[ERROR] Login failed: {response.text}")
                    return False
            except Exception as e:
                print(f"[ERROR] Login exception: {e}")
                return False
    
    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        测试单个端点的响应时间
        
        Args:
            endpoint: API 端点
            method: HTTP 方法
            params: 查询参数
            data: 请求体数据
            headers: 请求头
        
        Returns:
            测试结果
        """
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=data, headers=headers)
                else:
                    raise ValueError(f"不支持的 HTTP 方法：{method}")
                
                duration = (time.time() - start_time) * 1000
                
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "duration_ms": round(duration, 2),
                    "success": response.status_code < 400,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": None,
                    "duration_ms": round(duration, 2),
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    async def test_endpoint_multiple_times(
        self,
        endpoint: str,
        times: int = 10,
        method: str = "GET",
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        多次测试同一端点
        
        Args:
            endpoint: API 端点
            times: 测试次数
            method: HTTP 方法
            params: 查询参数
        
        Returns:
            统计结果
        """
        durations = []
        success_count = 0
        
        for i in range(times):
            result = await self.test_endpoint(endpoint, method, params)
            durations.append(result["duration_ms"])
            
            if result["success"]:
                success_count += 1
            
            await asyncio.sleep(0.1)
        
        return {
            "endpoint": endpoint,
            "times": times,
            "success_count": success_count,
            "success_rate": round(success_count / times * 100, 2),
            "avg_duration_ms": round(statistics.mean(durations), 2),
            "min_duration_ms": round(min(durations), 2),
            "max_duration_ms": round(max(durations), 2),
            "median_duration_ms": round(statistics.median(durations), 2),
            "std_dev_ms": round(statistics.stdev(durations), 2) if len(durations) > 1 else 0
        }
    
    async def test_cache_effectiveness(
        self,
        endpoint: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        测试缓存效果
        
        Args:
            endpoint: API 端点
            params: 查询参数
        
        Returns:
            缓存效果测试结果
        """
        first_call = await self.test_endpoint(endpoint, params=params)
        await asyncio.sleep(0.5)
        second_call = await self.test_endpoint(endpoint, params=params)
        
        improvement = 0
        if first_call["success"] and second_call["success"]:
            improvement = round(
                (first_call["duration_ms"] - second_call["duration_ms"]) 
                / first_call["duration_ms"] * 100, 2
            )
        
        return {
            "endpoint": endpoint,
            "first_call_ms": first_call["duration_ms"],
            "second_call_ms": second_call["duration_ms"],
            "improvement_percent": improvement,
            "cache_effective": second_call["duration_ms"] < first_call["duration_ms"]
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        运行综合性能测试
        
        Returns:
            综合测试结果
        """
        print("\n" + "="*60)
        print("[START] API Performance Test")
        print("="*60 + "\n")
        
        test_endpoints = [
            {"endpoint": "/api/v1/users/me", "name": "获取当前用户信息"},
            {"endpoint": "/api/v1/diagnosis/records", "name": "查询诊断记录"},
            {"endpoint": "/api/v1/knowledge/search", "name": "搜索病害知识", "params": {"keyword": "锈病"}},
        ]
        
        results = {
            "test_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "endpoints": []
        }
        
        for test in test_endpoints:
            print(f"\n[TEST] Endpoint: {test['name']}")
            print(f"   Endpoint: {test['endpoint']}")
            
            print("   1. Response time test (10 times)...")
            time_test = await self.test_endpoint_multiple_times(
                endpoint=test["endpoint"],
                times=10,
                params=test.get("params")
            )
            
            print(f"   [OK] Average response time: {time_test['avg_duration_ms']} ms")
            print(f"   [OK] Min response time: {time_test['min_duration_ms']} ms")
            print(f"   [OK] Max response time: {time_test['max_duration_ms']} ms")
            
            print("   2. Cache effectiveness test...")
            cache_test = await self.test_cache_effectiveness(
                endpoint=test["endpoint"],
                params=test.get("params")
            )
            
            if cache_test["cache_effective"]:
                print(f"   [OK] Cache effective, improvement: {cache_test['improvement_percent']}%")
            else:
                print(f"   [WARN] Cache not effective or improvement not obvious")
            
            results["endpoints"].append({
                "name": test["name"],
                "endpoint": test["endpoint"],
                "time_test": time_test,
                "cache_test": cache_test
            })
        
        print("\n" + "="*60)
        print("[SUMMARY] Test Summary")
        print("="*60)
        
        all_durations = []
        for endpoint_result in results["endpoints"]:
            all_durations.append(endpoint_result["time_test"]["avg_duration_ms"])
        
        overall_avg = statistics.mean(all_durations)
        
        print(f"\n[OK] Overall average response time: {round(overall_avg, 2)} ms")
        
        if overall_avg < 500:
            print("[OK] Performance target achieved: average response time < 500ms")
        else:
            print("[FAIL] Performance target not achieved: average response time >= 500ms")
        
        results["overall_avg_ms"] = round(overall_avg, 2)
        results["target_achieved"] = overall_avg < 500
        
        return results
    
    def save_report(self, results: Dict[str, Any], filename: str = "performance_report.json"):
        """
        保存性能报告
        
        Args:
            results: 测试结果
            filename: 文件名
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n[REPORT] Performance report saved: {filename}")


async def main():
    """主函数"""
    tester = PerformanceTester(base_url="http://localhost:8000")
    
    success = await tester.login("test_admin", "test123")
    
    if not success:
        print("[ERROR] Login failed, please check username and password")
        return
    
    results = await tester.run_comprehensive_test()
    
    tester.save_report(results)


if __name__ == "__main__":
    asyncio.run(main())
