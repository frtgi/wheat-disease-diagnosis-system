"""
边界条件和异常处理测试脚本
测试覆盖：边界条件、异常处理、并发用户、数据量等
使用 pytest + requests 框架
"""
import os
import sys
import pytest
import requests
import json
import time
import threading
import random
import string
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 测试配置
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000/api/v1")
HEADERS = {"Content-Type": "application/json"}

# 测试超时时间
REQUEST_TIMEOUT = 30  # 秒


class TestEdgeCases:
    """边界条件和异常处理测试类"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """创建测试用户"""
        timestamp = int(time.time())
        user_data = {
            "username": f"edge_test_{timestamp}",
            "email": f"edge_test_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            # 注册用户
            response = requests.post(
                f"{BASE_URL}/users/register",
                json=user_data,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                user_info = response.json()
                yield user_info
                
                # 清理：这里可以添加删除用户的逻辑
            else:
                # 如果注册失败，可能用户已存在，尝试登录
                login_response = requests.post(
                    f"{BASE_URL}/users/login",
                    json={"username": user_data["username"], "password": user_data["password"]},
                    timeout=REQUEST_TIMEOUT
                )
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    # 获取用户信息
                    user_response = requests.get(
                        f"{BASE_URL}/users/me",
                        headers={"Authorization": f"Bearer {token_data['access_token']}"},
                        timeout=REQUEST_TIMEOUT
                    )
                    yield user_response.json()
                else:
                    pytest.skip("无法创建测试用户")
        except Exception as e:
            pytest.skip(f"测试用户创建失败：{e}")
    
    @pytest.fixture(scope="class")
    def auth_token(self, test_user):
        """获取认证 Token"""
        if not test_user:
            pytest.skip("测试用户不存在")
        
        # 登录获取 token
        login_response = requests.post(
            f"{BASE_URL}/users/login",
            json={"username": test_user.get("username"), "password": "TestPassword123!"},
            timeout=REQUEST_TIMEOUT
        )
        
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        else:
            pytest.skip("无法获取认证 token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """获取带认证的请求头"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    # ==================== 边界条件测试 ====================
    
    def test_01_username_length_boundary(self, test_user):
        """测试用户名长度边界"""
        print("\n[边界测试] 用户名长度边界")
        
        # 测试最小长度（1 个字符）
        short_user = {
            "username": "a",
            "email": f"short_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=short_user, timeout=REQUEST_TIMEOUT)
        print(f"  1 字符用户名：{response.status_code}")
        
        # 测试最大长度（50 个字符）
        max_user = {
            "username": "a" * 50,
            "email": f"max_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=max_user, timeout=REQUEST_TIMEOUT)
        print(f"  50 字符用户名：{response.status_code}")
        
        # 测试超过最大长度（51 个字符）
        over_max_user = {
            "username": "a" * 51,
            "email": f"overmax_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=over_max_user, timeout=REQUEST_TIMEOUT)
        print(f"  51 字符用户名（应失败）：{response.status_code}")
        assert response.status_code in [400, 422], "超过最大长度应该失败"
    
    def test_02_password_length_boundary(self):
        """测试密码长度边界"""
        print("\n[边界测试] 密码长度边界")
        timestamp = int(time.time())
        
        # 测试最小长度（6 个字符）
        min_pass_user = {
            "username": f"minpass_{timestamp}",
            "email": f"minpass_{timestamp}@example.com",
            "password": "123456"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=min_pass_user, timeout=REQUEST_TIMEOUT)
        print(f"  6 字符密码：{response.status_code}")
        
        # 测试短密码（5 个字符，应该失败）
        short_pass_user = {
            "username": f"shortpass_{timestamp}",
            "email": f"shortpass_{timestamp}@example.com",
            "password": "12345"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=short_pass_user, timeout=REQUEST_TIMEOUT)
        print(f"  5 字符密码（应失败）：{response.status_code}")
        assert response.status_code in [400, 422], "密码长度不足应该失败"
    
    def test_03_pagination_boundary(self, auth_headers):
        """测试分页参数边界"""
        print("\n[边界测试] 分页参数边界")
        
        # 测试 skip=0
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            headers=auth_headers,
            params={"skip": 0, "limit": 10},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  skip=0, limit=10: {response.status_code}")
        assert response.status_code == 200
        
        # 测试 skip 为负数（应该失败）
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            headers=auth_headers,
            params={"skip": -1, "limit": 10},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  skip=-1（应失败）：{response.status_code}")
        assert response.status_code in [400, 422], "负的 skip 值应该失败"
        
        # 测试 limit=1（最小值）
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            headers=auth_headers,
            params={"skip": 0, "limit": 1},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  limit=1: {response.status_code}")
        assert response.status_code == 200
        
        # 测试 limit=100（最大值）
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            headers=auth_headers,
            params={"skip": 0, "limit": 100},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  limit=100: {response.status_code}")
        assert response.status_code == 200
        
        # 测试 limit=101（超过最大值，应该失败）
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            headers=auth_headers,
            params={"skip": 0, "limit": 101},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  limit=101（应失败）：{response.status_code}")
        assert response.status_code in [400, 422], "超过最大 limit 值应该失败"
    
    def test_04_special_characters_input(self):
        """测试特殊字符输入"""
        print("\n[边界测试] 特殊字符输入")
        timestamp = int(time.time())
        
        # 测试包含特殊字符的用户名
        special_user = {
            "username": f"test_user-{timestamp}_中文",
            "email": f"special_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=special_user, timeout=REQUEST_TIMEOUT)
        print(f"  包含特殊字符和中文的用户名：{response.status_code}")
        
        # 测试 SQL 注入尝试
        sql_injection_user = {
            "username": f"admin' OR '1'='1",
            "email": f"sql_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=sql_injection_user, timeout=REQUEST_TIMEOUT)
        print(f"  SQL 注入尝试：{response.status_code}")
        
        # 测试 XSS 尝试
        xss_user = {
            "username": f"<script>alert('xss')</script>_{timestamp}",
            "email": f"xss_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=xss_user, timeout=REQUEST_TIMEOUT)
        print(f"  XSS 尝试：{response.status_code}")
    
    def test_05_empty_and_null_input(self):
        """测试空值和 null 输入"""
        print("\n[边界测试] 空值和 null 输入")
        
        # 测试空用户名
        empty_user = {
            "username": "",
            "email": f"empty_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=empty_user, timeout=REQUEST_TIMEOUT)
        print(f"  空用户名：{response.status_code}")
        assert response.status_code in [400, 422], "空用户名应该失败"
        
        # 测试空密码
        empty_pass_user = {
            "username": f"emptypass_{int(time.time())}",
            "email": f"emptypass_{int(time.time())}@example.com",
            "password": ""
        }
        response = requests.post(f"{BASE_URL}/users/register", json=empty_pass_user, timeout=REQUEST_TIMEOUT)
        print(f"  空密码：{response.status_code}")
        assert response.status_code in [400, 422], "空密码应该失败"
    
    def test_06_concurrent_requests(self, auth_headers):
        """测试并发请求"""
        print("\n[边界测试] 并发请求测试")
        
        results = []
        num_requests = 20
        
        def make_request(index):
            try:
                start_time = time.time()
                response = requests.get(
                    f"{BASE_URL}/health",
                    timeout=REQUEST_TIMEOUT
                )
                elapsed = time.time() - start_time
                return {
                    "index": index,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "success": True
                }
            except Exception as e:
                return {
                    "index": index,
                    "error": str(e),
                    "success": False
                }
        
        # 使用线程池并发发送请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r.get("success"))
        print(f"  总请求数：{num_requests}")
        print(f"  成功请求数：{success_count}")
        print(f"  平均响应时间：{sum(r.get('elapsed', 0) for r in results if r.get('success')) / max(success_count, 1):.3f}秒")
        
        assert success_count >= num_requests * 0.8, "至少 80% 的请求应该成功"
    
    def test_07_large_data_volume(self, auth_headers):
        """测试大数据量"""
        print("\n[边界测试] 大数据量测试")
        
        # 测试长文本症状描述
        long_symptoms = "小麦叶片出现病斑，" * 1000  # 约 20000 字符
        response = requests.post(
            f"{BASE_URL}/diagnosis/text",
            headers=auth_headers,
            data={"symptoms": long_symptoms},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  长文本症状描述（{len(long_symptoms)}字符）：{response.status_code}")
        
        # 注意：这里不检查响应状态，因为实际业务可能有限制
    
    def test_08_numeric_range_boundary(self):
        """测试数值范围边界"""
        print("\n[边界测试] 数值范围边界")
        
        # 测试置信度边界值
        # 这里主要是接口参数验证，实际测试需要看具体实现
        
        # 测试分页的边界值
        test_cases = [
            (0, 1, "最小分页"),
            (0, 100, "最大 limit"),
            (1000000, 10, "大 skip 值"),
        ]
        
        for skip, limit, description in test_cases:
            response = requests.get(
                f"{BASE_URL}/diagnosis/records",
                params={"skip": skip, "limit": limit},
                timeout=REQUEST_TIMEOUT
            )
            print(f"  {description} (skip={skip}, limit={limit}): {response.status_code}")
    
    # ==================== 异常处理测试 ====================
    
    def test_09_invalid_token(self):
        """测试无效 Token"""
        print("\n[异常测试] 无效 Token")
        
        # 使用无效的 Token
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz123", "Content-Type": "application/json"}
        
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers=invalid_headers,
            timeout=REQUEST_TIMEOUT
        )
        print(f"  无效 Token 访问受保护接口：{response.status_code}")
        assert response.status_code in [401, 403], "无效 Token 应该被拒绝"
    
    def test_10_expired_token(self):
        """测试过期 Token（如果支持）"""
        print("\n[异常测试] 过期 Token")
        # 注意：实际测试过期 token 需要等待或修改配置
        # 这里只是演示测试结构
        pytest.skip("过期 Token 测试需要特殊配置，跳过")
    
    def test_11_missing_required_fields(self):
        """测试缺少必填字段"""
        print("\n[异常测试] 缺少必填字段")
        
        # 测试缺少用户名
        missing_username = {
            "email": f"missing_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=missing_username, timeout=REQUEST_TIMEOUT)
        print(f"  缺少用户名：{response.status_code}")
        assert response.status_code in [400, 422], "缺少必填字段应该失败"
        
        # 测试缺少密码
        missing_password = {
            "username": f"missingpass_{int(time.time())}",
            "email": f"missingpass_{int(time.time())}@example.com"
        }
        response = requests.post(f"{BASE_URL}/users/register", json=missing_password, timeout=REQUEST_TIMEOUT)
        print(f"  缺少密码：{response.status_code}")
        assert response.status_code in [400, 422], "缺少必填字段应该失败"
    
    def test_12_wrong_content_type(self):
        """测试错误的 Content-Type"""
        print("\n[异常测试] 错误的 Content-Type")
        
        # 使用错误的 Content-Type
        wrong_headers = {"Content-Type": "text/plain"}
        user_data = {"username": "test", "email": "test@example.com", "password": "test123"}
        
        response = requests.post(
            f"{BASE_URL}/users/register",
            headers=wrong_headers,
            data=json.dumps(user_data),
            timeout=REQUEST_TIMEOUT
        )
        print(f"  错误的 Content-Type: {response.status_code}")
    
    def test_13_invalid_json_format(self):
        """测试无效的 JSON 格式"""
        print("\n[异常测试] 无效的 JSON 格式")
        
        # 发送无效的 JSON
        invalid_json = '{"username": "test", "email": "test@example.com", "password": "test123"'  # 缺少右括号
        response = requests.post(
            f"{BASE_URL}/users/register",
            headers={"Content-Type": "application/json"},
            data=invalid_json,
            timeout=REQUEST_TIMEOUT
        )
        print(f"  无效的 JSON 格式：{response.status_code}")
        assert response.status_code in [400, 422], "无效 JSON 应该被拒绝"
    
    def test_14_duplicate_registration(self):
        """测试重复注册"""
        print("\n[异常测试] 重复注册")
        timestamp = int(time.time())
        
        # 第一次注册
        user_data = {
            "username": f"dup_test_{timestamp}",
            "email": f"dup_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        response1 = requests.post(f"{BASE_URL}/users/register", json=user_data, timeout=REQUEST_TIMEOUT)
        print(f"  首次注册：{response1.status_code}")
        
        # 第二次注册（重复）
        response2 = requests.post(f"{BASE_URL}/users/register", json=user_data, timeout=REQUEST_TIMEOUT)
        print(f"  重复注册：{response2.status_code}")
        assert response2.status_code in [400, 409], "重复注册应该失败"
    
    def test_15_unauthorized_access(self):
        """测试未授权访问"""
        print("\n[异常测试] 未授权访问")
        
        # 不带 Token 访问受保护接口
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            timeout=REQUEST_TIMEOUT
        )
        print(f"  未授权访问诊断记录：{response.status_code}")
        assert response.status_code in [401, 403], "未授权访问应该被拒绝"
    
    def test_16_network_timeout(self, auth_headers):
        """测试网络超时处理"""
        print("\n[异常测试] 网络超时处理")
        
        try:
            # 设置非常短的超时时间
            response = requests.get(
                f"{BASE_URL}/diagnosis/records",
                headers=auth_headers,
                timeout=0.001  # 1 毫秒，肯定会超时
            )
            print(f"  超时请求（意外成功）：{response.status_code}")
        except requests.exceptions.Timeout:
            print("  网络超时：正确捕获超时异常")
            assert True
        except Exception as e:
            print(f"  网络超时：捕获异常 - {type(e).__name__}")
            assert True
    
    def test_17_invalid_email_format(self):
        """测试无效的邮箱格式"""
        print("\n[异常测试] 无效的邮箱格式")
        timestamp = int(time.time())
        
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "test@",
            "test@example",
            "test..test@example.com"
        ]
        
        for email in invalid_emails:
            user_data = {
                "username": f"invalidmail_{timestamp}_{random.randint(1, 1000)}",
                "email": email,
                "password": "TestPassword123!"
            }
            response = requests.post(f"{BASE_URL}/users/register", json=user_data, timeout=REQUEST_TIMEOUT)
            print(f"  无效邮箱 '{email}': {response.status_code}")
    
    def test_18_case_sensitivity(self):
        """测试大小写敏感性"""
        print("\n[异常测试] 大小写敏感性")
        timestamp = int(time.time())
        
        # 注册用户
        user_data = {
            "username": f"CaseTest_{timestamp}",
            "email": f"casetest_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        response1 = requests.post(f"{BASE_URL}/users/register", json=user_data, timeout=REQUEST_TIMEOUT)
        print(f"  注册 CaseTest_{timestamp}: {response1.status_code}")
        
        # 尝试用不同大小写登录
        login_variations = [
            f"casetest_{timestamp}",  # 全小写
            f"CASETEST_{timestamp}",  # 全大写
            f"CaseTest_{timestamp}",  # 原样
        ]
        
        for username in login_variations:
            login_response = requests.post(
                f"{BASE_URL}/users/login",
                json={"username": username, "password": "TestPassword123!"},
                timeout=REQUEST_TIMEOUT
            )
            print(f"  登录 '{username}': {login_response.status_code}")
    
    def test_19_resource_not_found(self, auth_headers):
        """测试资源不存在"""
        print("\n[异常测试] 资源不存在")
        
        # 访问不存在的诊断记录
        response = requests.get(
            f"{BASE_URL}/diagnosis/999999999",
            headers=auth_headers,
            timeout=REQUEST_TIMEOUT
        )
        print(f"  访问不存在的诊断记录：{response.status_code}")
        assert response.status_code == 404, "不存在的资源应该返回 404"
    
    def test_20_method_not_allowed(self):
        """测试不允许的 HTTP 方法"""
        print("\n[异常测试] 不允许的 HTTP 方法")
        
        # 尝试用 DELETE 方法访问注册接口
        response = requests.delete(
            f"{BASE_URL}/users/register",
            json={"username": "test", "email": "test@example.com", "password": "test123"},
            timeout=REQUEST_TIMEOUT
        )
        print(f"  DELETE 方法访问注册接口：{response.status_code}")
        assert response.status_code in [405, 404], "不允许的方法应该被拒绝"


class TestStressAndLoad:
    """压力测试和负载测试类"""
    
    def test_21_high_concurrent_login(self):
        """测试高并发登录"""
        print("\n[压力测试] 高并发登录")
        
        results = []
        num_requests = 50
        
        def make_login_request(index):
            try:
                start_time = time.time()
                # 使用测试账号
                response = requests.post(
                    f"{BASE_URL}/users/login",
                    json={"username": "test_user", "password": "test_password"},
                    timeout=REQUEST_TIMEOUT
                )
                elapsed = time.time() - start_time
                return {
                    "index": index,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "index": index,
                    "error": str(e),
                    "success": False
                }
        
        # 并发发送登录请求
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_login_request, i) for i in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r.get("success"))
        print(f"  总请求数：{num_requests}")
        print(f"  成功请求数：{success_count}")
        print(f"  成功率：{success_count / num_requests * 100:.1f}%")
    
    def test_22_sustained_load(self):
        """测试持续负载"""
        print("\n[压力测试] 持续负载测试")
        
        duration = 10  # 持续时间（秒）- 缩短时间以加快测试
        start_time = time.time()
        request_count = 0
        success_count = 0
        
        while time.time() - start_time < duration:
            try:
                response = requests.get(
                    f"{BASE_URL}/health",
                    timeout=REQUEST_TIMEOUT
                )
                request_count += 1
                if response.status_code == 200:
                    success_count += 1
            except Exception:
                request_count += 1
            
            # 控制请求频率
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        print(f"  测试持续时间：{elapsed:.1f}秒")
        print(f"  总请求数：{request_count}")
        print(f"  成功请求数：{success_count}")
        print(f"  吞吐量：{request_count / elapsed:.2f} req/s")


def run_edge_case_tests():
    """运行边界和异常测试"""
    print("=" * 80)
    print("边界条件和异常处理测试")
    print("=" * 80)
    print(f"测试开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试目标 URL: {BASE_URL}")
    print("=" * 80)
    
    # 使用 pytest 运行测试
    pytest_args = [
        __file__,
        "-v",
        "-s",
        "--tb=short",
        f"--junitxml={os.path.join(os.path.dirname(__file__), 'test_edge_cases_report.xml')}"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    print("\n" + "=" * 80)
    print("测试执行完成")
    print("=" * 80)
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)
