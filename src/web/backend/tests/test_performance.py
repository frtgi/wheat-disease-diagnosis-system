"""
全面性能测试脚本
测试系统的各项性能指标
"""
import asyncio
import time
import aiohttp
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import json

# 性能测试配置
TEST_CONFIG = {
    "base_url": "http://localhost:8000/api/v1",
    "concurrent_users": 50,  # 并发用户数
    "test_duration": 60,     # 测试持续时间（秒）
    "warmup_requests": 10,   # 预热请求次数
}

# 测试结果统计
test_results = {
    "requests_sent": 0,
    "requests_completed": 0,
    "requests_failed": 0,
    "response_times": [],
    "throughput": 0,  # 每秒请求数
    "avg_response_time": 0,
    "p95_response_time": 0,
    "p99_response_time": 0,
    "error_rate": 0,
    "status_codes": defaultdict(int),
}

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def warmup_api():
    """API 预热"""
    print_info("开始 API 预热...")
    
    for i in range(TEST_CONFIG["warmup_requests"]):
        try:
            response = requests.get(f"{TEST_CONFIG['base_url']}/health", timeout=5)
            if response.status_code == 200:
                print_success(f"预热请求 {i+1}/{TEST_CONFIG['warmup_requests']}: {response.status_code}")
            else:
                print_error(f"预热请求 {i+1}/{TEST_CONFIG['warmup_requests']}: {response.status_code}")
        except Exception as e:
            print_error(f"预热请求 {i+1}/{TEST_CONFIG['warmup_requests']}: {e}")
    
    print_info("API 预热完成")

def test_health_endpoint():
    """测试健康检查端点"""
    print_header("测试 1: 健康检查端点")
    
    start_time = time.time()
    try:
        response = requests.get(f"{TEST_CONFIG['base_url']}/health", timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            health_data = response.json()
            print_success(f"健康检查: {response.status_code}")
            print_info(f"  响应时间: {elapsed*1000:.2f}ms")
            print_info(f"  服务状态: {health_data}")
        else:
            print_error(f"健康检查失败: {response.status_code}")
    except Exception as e:
        print_error(f"健康检查异常: {e}")

def test_database_performance():
    """测试数据库查询性能"""
    print_header("测试 2: 数据库查询性能")
    
    # 模拟用户登录获取 token
    try:
        login_resp = requests.post(
            f"{TEST_CONFIG['base_url']}/auth/login",
            json={"username": "farmer_zhang", "password": "123456"},
            timeout=10
        )
        
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试诊断记录查询
            start_time = time.time()
            records_resp = requests.get(
                f"{TEST_CONFIG['base_url']}/diagnosis/records",
                headers=headers,
                params={"skip": 0, "limit": 10},
                timeout=10
            )
            elapsed = time.time() - start_time
            
            if records_resp.status_code == 200:
                records = records_resp.json()
                print_success(f"诊断记录查询: {records_resp.status_code}")
                print_info(f"  响应时间: {elapsed*1000:.2f}ms")
                print_info(f"  记录数量: {len(records)}")
            else:
                print_error(f"诊断记录查询失败: {records_resp.status_code}")
        else:
            print_error(f"登录失败: {login_resp.status_code}")
    except Exception as e:
        print_error(f"数据库性能测试异常: {e}")

def test_cache_performance():
    """测试缓存性能"""
    print_header("测试 3: 缓存性能")
    
    try:
        # 首次请求
        start_time1 = time.time()
        resp1 = requests.get(f"{TEST_CONFIG['base_url']}/health", timeout=10)
        elapsed1 = time.time() - start_time1
        
        # 第二次请求（可能命中缓存）
        start_time2 = time.time()
        resp2 = requests.get(f"{TEST_CONFIG['base_url']}/health", timeout=10)
        elapsed2 = time.time() - start_time2
        
        print_success(f"缓存测试完成")
        print_info(f"  首次请求: {elapsed1*1000:.2f}ms")
        print_info(f"  第二次请求: {elapsed2*1000:.2f}ms")
        print_info(f"  性能提升: {((elapsed1 - elapsed2) / elapsed1 * 100):.1f}%" if elapsed1 > elapsed2 else "无明显提升")
    except Exception as e:
        print_error(f"缓存性能测试异常: {e}")

def concurrent_test_worker(session, endpoint, headers=None, payload=None):
    """并发测试工作函数"""
    global test_results
    
    try:
        start_time = time.time()
        
        if payload:
            response = session.post(endpoint, headers=headers, json=payload, timeout=30)
        else:
            response = session.get(endpoint, headers=headers, timeout=30)
        
        elapsed = time.time() - start_time
        
        test_results["requests_completed"] += 1
        test_results["response_times"].append(elapsed)
        test_results["status_codes"][response.status_code] += 1
        
        if response.status_code >= 400:
            test_results["requests_failed"] += 1
            
        return elapsed, response.status_code
    except Exception as e:
        test_results["requests_failed"] += 1
        test_results["requests_completed"] += 1
        test_results["response_times"].append(30.0)  # 超时时间
        return 30.0, 0

def test_concurrent_performance():
    """测试并发性能"""
    print_header("测试 4: 并发性能测试")
    
    print_info(f"并发用户数: {TEST_CONFIG['concurrent_users']}")
    print_info(f"测试持续时间: {TEST_CONFIG['test_duration']}秒")
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建会话
    with requests.Session() as session:
        # 首先登录获取 token
        try:
            login_resp = session.post(
                f"{TEST_CONFIG['base_url']}/auth/login",
                json={"username": "farmer_zhang", "password": "123456"},
                timeout=10
            )
            if login_resp.status_code == 200:
                token = login_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
            else:
                print_error("登录失败，使用无认证请求")
                headers = {}
        except Exception as e:
            print_error(f"登录异常: {e}")
            headers = {}
        
        # 并发执行测试
        with ThreadPoolExecutor(max_workers=TEST_CONFIG['concurrent_users']) as executor:
            futures = []
            
            # 在测试持续时间内持续发送请求
            while time.time() - start_time < TEST_CONFIG['test_duration']:
                # 发送健康检查请求
                future = executor.submit(
                    concurrent_test_worker,
                    session,
                    f"{TEST_CONFIG['base_url']}/health",
                    headers
                )
                futures.append(future)
                
                # 控制请求频率
                time.sleep(0.1)
                
                # 限制并发请求数量
                if len(futures) >= TEST_CONFIG['concurrent_users']:
                    break
            
            # 等待所有请求完成
            for future in futures:
                try:
                    elapsed, status = future.result(timeout=35)
                except Exception as e:
                    test_results["requests_failed"] += 1
                    test_results["requests_completed"] += 1
                    test_results["response_times"].append(30.0)
    
    # 计算统计结果
    total_time = time.time() - start_time
    total_requests = len(test_results["response_times"])
    
    if total_requests > 0:
        test_results["throughput"] = total_requests / total_time
        test_results["avg_response_time"] = sum(test_results["response_times"]) / total_requests
        test_results["error_rate"] = test_results["requests_failed"] / total_requests
        
        # 计算百分位数
        sorted_times = sorted(test_results["response_times"])
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        
        if p95_idx < len(sorted_times):
            test_results["p95_response_time"] = sorted_times[p95_idx]
        if p99_idx < len(sorted_times):
            test_results["p99_response_time"] = sorted_times[p99_idx]
    
    print_success(f"并发测试完成")
    print_info(f"  总请求数: {total_requests}")
    print_info(f"  成功请求数: {total_requests - test_results['requests_failed']}")
    print_info(f"  失败请求数: {test_results['requests_failed']}")
    print_info(f"  吞吐量: {test_results['throughput']:.2f} req/s")
    print_info(f"  平均响应时间: {test_results['avg_response_time']*1000:.2f}ms")
    print_info(f"  P95 响应时间: {test_results['p95_response_time']*1000:.2f}ms")
    print_info(f"  P99 响应时间: {test_results['p99_response_time']*1000:.2f}ms")
    print_info(f"  错误率: {test_results['error_rate']*100:.2f}%")
    print_info(f"  状态码分布: {dict(test_results['status_codes'])}")

def test_api_endpoints():
    """测试各 API 端点性能"""
    print_header("测试 5: API 端点性能")
    
    endpoints = [
        ("/health", "GET", None),
        ("/users/me", "GET", None),  # 需要认证
        ("/diagnosis/records?skip=0&limit=5", "GET", None),  # 需要认证
        ("/knowledge/search?keyword=白粉病", "GET", None),
    ]
    
    # 获取认证 token
    try:
        login_resp = requests.post(
            f"{TEST_CONFIG['base_url']}/auth/login",
            json={"username": "farmer_zhang", "password": "123456"},
            timeout=10
        )
        token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
    except Exception:
        print_warning("无法获取认证 token，跳过需要认证的测试")
        auth_headers = {}
    
    for endpoint, method, payload in endpoints:
        try:
            start_time = time.time()
            
            if method == "GET":
                if "users/me" in endpoint or "diagnosis/records" in endpoint:
                    # 需要认证
                    response = requests.get(f"{TEST_CONFIG['base_url']}{endpoint}", headers=auth_headers, timeout=10)
                else:
                    response = requests.get(f"{TEST_CONFIG['base_url']}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{TEST_CONFIG['base_url']}{endpoint}", json=payload, headers=auth_headers, timeout=10)
            
            elapsed = time.time() - start_time
            
            status = "✓" if response.status_code < 400 else "✗"
            print(f"  {status} {method} {endpoint}: {response.status_code} ({elapsed*1000:.2f}ms)")
            
        except Exception as e:
            print(f"  ✗ {method} {endpoint}: Error - {e}")

def generate_performance_report():
    """生成性能测试报告"""
    print_header("性能测试报告")
    
    print_info("性能指标:")
    print_info(f"  吞吐量: {test_results['throughput']:.2f} req/s")
    print_info(f"  平均响应时间: {test_results['avg_response_time']*1000:.2f}ms")
    print_info(f"  P95 响应时间: {test_results['p95_response_time']*1000:.2f}ms")
    print_info(f"  P99 响应时间: {test_results['p99_response_time']*1000:.2f}ms")
    print_info(f"  错误率: {test_results['error_rate']*100:.2f}%")
    print_info(f"  总请求数: {test_results['requests_completed']}")
    print_info(f"  成功率: {((test_results['requests_completed'] - test_results['requests_failed']) / max(test_results['requests_completed'], 1) * 100):.2f}%")
    
    print_info("\n状态码分布:")
    for code, count in test_results['status_codes'].items():
        print_info(f"  {code}: {count}")
    
    # 性能评级
    print_info("\n性能评级:")
    avg_ms = test_results['avg_response_time'] * 1000
    throughput = test_results['throughput']
    error_rate = test_results['error_rate'] * 100
    
    if avg_ms < 500 and error_rate < 1 and throughput > 10:
        rating = "优秀 ⭐⭐⭐⭐⭐"
    elif avg_ms < 1000 and error_rate < 5 and throughput > 5:
        rating = "良好 ⭐⭐⭐⭐"
    elif avg_ms < 2000 and error_rate < 10 and throughput > 2:
        rating = "一般 ⭐⭐⭐"
    elif avg_ms < 5000 and error_rate < 20:
        rating = "较差 ⭐⭐"
    else:
        rating = "很差 ⭐"
    
    print_info(f"  整体性能: {rating}")
    
    # 性能建议
    print_info("\n性能建议:")
    if avg_ms > 2000:
        print_info("  • 响应时间较长，考虑优化数据库查询或添加缓存")
    if error_rate > 5:
        print_info("  • 错误率较高，检查服务稳定性")
    if throughput < 5:
        print_info("  • 吞吐量较低，考虑增加服务实例或优化代码")

def main():
    """主测试函数"""
    print_header("WheatAgent Web 系统性能测试")
    
    try:
        # 1. 预热 API
        warmup_api()
        
        # 2. 单项测试
        test_health_endpoint()
        test_database_performance()
        test_cache_performance()
        test_api_endpoints()
        
        # 3. 并发性能测试
        test_concurrent_performance()
        
        # 4. 生成报告
        generate_performance_report()
        
        print_header("性能测试完成")
        
    except KeyboardInterrupt:
        print_error("\n测试被用户中断")
    except Exception as e:
        print_error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()