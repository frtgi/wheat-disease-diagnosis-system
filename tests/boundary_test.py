# -*- coding: utf-8 -*-
"""
WheatAgent 后端服务边界条件测试脚本

测试场景:
1. 输入边界测试 - 空症状、超长文本、特殊字符
2. 用户输入边界 - 空用户名、无效邮箱、短密码
3. 数值边界 - 无效分页、超大分页
"""
import requests
import json
import time
from typing import Dict, Any, Tuple

BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/v1"

class BoundaryTestResult:
    """测试结果类"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.status_code = None
        self.response_body = None
        self.passed = False
        self.error_message = ""
        self.security_issue = False
    
    def to_dict(self) -> Dict:
        return {
            "test_name": self.test_name,
            "status_code": self.status_code,
            "passed": self.passed,
            "error_message": self.error_message,
            "security_issue": self.security_issue,
            "response_preview": str(self.response_body)[:500] if self.response_body else None
        }


def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Tuple[int, Any]:
    """
    发送 HTTP 请求
    
    :param method: HTTP 方法
    :param endpoint: API 端点
    :param data: 请求数据
    :param headers: 请求头
    :return: (状态码, 响应体)
    """
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data, headers=default_headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers, timeout=30)
        else:
            response = requests.request(method, url, json=data, headers=default_headers, timeout=30)
        
        try:
            body = response.json()
        except:
            body = response.text
        
        return response.status_code, body
    except requests.exceptions.ConnectionError:
        return None, "连接失败: 服务未启动"
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except Exception as e:
        return None, f"请求异常: {str(e)}"


def test_empty_symptoms() -> BoundaryTestResult:
    """
    测试空症状描述
    
    预期: 应该返回 422 验证错误
    """
    result = BoundaryTestResult("空症状描述测试")
    
    status_code, response = make_request("POST", "/diagnosis/text", {"symptoms": ""})
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了空症状描述"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 401:
        result.passed = True
        result.error_message = "需要认证，验证正确"
    else:
        result.passed = False
        result.error_message = f"预期 422/400/401，实际 {status_code}"
    
    return result


def test_long_text() -> BoundaryTestResult:
    """
    测试超长文本输入
    
    预期: 应该返回 422 或正确处理
    """
    result = BoundaryTestResult("超长文本测试")
    
    long_text = "很长的文本..." + "x" * 10000
    status_code, response = make_request("POST", "/diagnosis/text", {"symptoms": long_text})
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了超长文本"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 401:
        result.passed = True
        result.error_message = "需要认证，验证正确"
    elif status_code == 500:
        result.passed = False
        result.error_message = "服务器内部错误，可能存在资源耗尽风险"
        result.security_issue = True
    elif status_code == 200:
        result.passed = False
        result.error_message = "接受了超长文本，可能存在资源耗尽风险"
        result.security_issue = True
    else:
        result.passed = False
        result.error_message = f"未预期的状态码: {status_code}"
    
    return result


def test_xss_injection() -> BoundaryTestResult:
    """
    测试 XSS 注入
    
    预期: 应该正确转义或拒绝
    """
    result = BoundaryTestResult("XSS 注入测试")
    
    xss_payload = "<script>alert('xss')</script>"
    status_code, response = make_request("POST", "/diagnosis/text", {"symptoms": xss_payload})
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了特殊字符"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 401:
        result.passed = True
        result.error_message = "需要认证，验证正确"
    elif status_code == 200:
        response_str = str(response)
        if "<script>" in response_str and not response_str.startswith("<!DOCTYPE"):
            result.passed = False
            result.error_message = "XSS payload 未被转义，存在安全风险"
            result.security_issue = True
        else:
            result.passed = True
            result.error_message = "响应中未包含原始 XSS payload"
    else:
        result.passed = False
        result.error_message = f"未预期的状态码: {status_code}"
    
    return result


def test_empty_username() -> BoundaryTestResult:
    """
    测试空用户名注册
    
    预期: 应该返回 422 验证错误
    """
    result = BoundaryTestResult("空用户名注册测试")
    
    status_code, response = make_request("POST", "/users/register", {
        "username": "",
        "email": "test@test.com",
        "password": "123456"
    })
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了空用户名"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    else:
        result.passed = False
        result.error_message = f"预期 422/400，实际 {status_code}"
    
    return result


def test_invalid_email() -> BoundaryTestResult:
    """
    测试无效邮箱格式
    
    预期: 应该返回 422 验证错误
    """
    result = BoundaryTestResult("无效邮箱格式测试")
    
    status_code, response = make_request("POST", "/users/register", {
        "username": "testuser",
        "email": "invalid-email",
        "password": "123456"
    })
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了无效邮箱格式"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    else:
        result.passed = False
        result.error_message = f"预期 422/400，实际 {status_code}"
        if status_code == 200 or status_code == 201:
            result.security_issue = True
    
    return result


def test_short_password() -> BoundaryTestResult:
    """
    测试短密码
    
    预期: 应该返回 422 验证错误（密码至少 6 位）
    """
    result = BoundaryTestResult("短密码测试")
    
    status_code, response = make_request("POST", "/users/register", {
        "username": "testuser",
        "email": "test@test.com",
        "password": "1"
    })
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了短密码"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    else:
        result.passed = False
        result.error_message = f"预期 422/400，实际 {status_code}"
        if status_code == 200 or status_code == 201:
            result.security_issue = True
    
    return result


def test_invalid_pagination() -> BoundaryTestResult:
    """
    测试无效分页参数
    
    预期: 应该返回 422 或使用默认值
    """
    result = BoundaryTestResult("无效分页参数测试")
    
    status_code, response = make_request("GET", "/knowledge/search", {"page": -1, "page_size": 0})
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了无效分页参数"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 401:
        result.passed = True
        result.error_message = "需要认证，验证正确"
    elif status_code == 200:
        result.passed = True
        result.error_message = "使用了默认分页参数"
    else:
        result.passed = False
        result.error_message = f"未预期的状态码: {status_code}"
    
    return result


def test_large_pagination() -> BoundaryTestResult:
    """
    测试超大分页参数
    
    预期: 应该限制最大值或返回 422
    """
    result = BoundaryTestResult("超大分页参数测试")
    
    status_code, response = make_request("GET", "/knowledge/search", {"page": 999999, "page_size": 1000})
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了超大分页参数"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 401:
        result.passed = True
        result.error_message = "需要认证，验证正确"
    elif status_code == 200:
        if isinstance(response, list) and len(response) <= 100:
            result.passed = True
            result.error_message = "正确限制了返回数量"
        else:
            result.passed = False
            result.error_message = "可能存在资源耗尽风险"
            result.security_issue = True
    elif status_code == 500:
        result.passed = False
        result.error_message = "服务器内部错误"
        result.security_issue = True
    else:
        result.passed = False
        result.error_message = f"未预期的状态码: {status_code}"
    
    return result


def test_sql_injection() -> BoundaryTestResult:
    """
    测试 SQL 注入
    
    预期: 应该正确处理，不执行 SQL
    """
    result = BoundaryTestResult("SQL 注入测试")
    
    sql_payload = "'; DROP TABLE users; --"
    status_code, response = make_request("POST", "/users/register", {
        "username": sql_payload,
        "email": "test@test.com",
        "password": "123456"
    })
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了 SQL 注入 payload"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 409:
        result.passed = True
        result.error_message = "用户名冲突，但 SQL 未执行"
    elif status_code == 500:
        result.passed = False
        result.error_message = "服务器错误，可能存在 SQL 注入风险"
        result.security_issue = True
    elif status_code == 200 or status_code == 201:
        result.passed = False
        result.error_message = "可能存在 SQL 注入风险"
        result.security_issue = True
    else:
        result.passed = False
        result.error_message = f"未预期的状态码: {status_code}"
    
    return result


def test_path_traversal() -> BoundaryTestResult:
    """
    测试路径遍历攻击
    
    预期: 应该正确拒绝
    """
    result = BoundaryTestResult("路径遍历测试")
    
    path_payload = "../../../etc/passwd"
    status_code, response = make_request("GET", f"/knowledge/{path_payload}")
    result.status_code = status_code
    result.response_body = response
    
    if status_code == 404:
        result.passed = True
        result.error_message = "正确返回 404"
    elif status_code == 400:
        result.passed = True
        result.error_message = "正确返回 400 错误"
    elif status_code == 422:
        result.passed = True
        result.error_message = "正确拒绝了路径遍历"
    elif status_code == 500:
        result.passed = False
        result.error_message = "服务器错误，可能存在路径遍历风险"
        result.security_issue = True
    else:
        result.passed = False
        result.error_message = f"未预期的状态码: {status_code}"
    
    return result


def check_server_health() -> bool:
    """检查服务器是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def run_all_tests():
    """运行所有边界条件测试"""
    print("=" * 70)
    print("WheatAgent 后端服务边界条件测试")
    print("=" * 70)
    print()
    
    if not check_server_health():
        print("⚠️  服务器未运行，尝试连接中...")
        print(f"   目标地址: {BASE_URL}")
        print()
    
    tests = [
        ("输入边界测试", [
            test_empty_symptoms,
            test_long_text,
            test_xss_injection,
        ]),
        ("用户输入边界测试", [
            test_empty_username,
            test_invalid_email,
            test_short_password,
        ]),
        ("数值边界测试", [
            test_invalid_pagination,
            test_large_pagination,
        ]),
        ("安全测试", [
            test_sql_injection,
            test_path_traversal,
        ])
    ]
    
    all_results = []
    passed_count = 0
    failed_count = 0
    security_issues = []
    
    for category, test_funcs in tests:
        print(f"\n{'='*70}")
        print(f"📋 {category}")
        print("=" * 70)
        
        for test_func in test_funcs:
            print(f"\n🔍 执行: {test_func.__doc__.strip().split(chr(10))[0]}")
            result = test_func()
            all_results.append(result)
            
            status_icon = "✅" if result.passed else "❌"
            print(f"   状态码: {result.status_code}")
            print(f"   结果: {status_icon} {result.error_message}")
            
            if result.passed:
                passed_count += 1
            else:
                failed_count += 1
            
            if result.security_issue:
                security_issues.append(result.test_name)
                print(f"   ⚠️  安全警告: 存在潜在安全风险!")
    
    print("\n" + "=" * 70)
    print("📊 测试汇总")
    print("=" * 70)
    print(f"   总测试数: {len(all_results)}")
    print(f"   ✅ 通过: {passed_count}")
    print(f"   ❌ 失败: {failed_count}")
    print(f"   ⚠️  安全问题: {len(security_issues)}")
    
    if security_issues:
        print("\n⚠️  发现的安全问题:")
        for issue in security_issues:
            print(f"   - {issue}")
    
    print("\n" + "=" * 70)
    print("详细测试结果")
    print("=" * 70)
    
    for result in all_results:
        status = "✅ 通过" if result.passed else "❌ 失败"
        security = " ⚠️ 安全风险" if result.security_issue else ""
        print(f"\n{result.test_name}: {status}{security}")
        print(f"   状态码: {result.status_code}")
        print(f"   说明: {result.error_message}")
    
    return {
        "total": len(all_results),
        "passed": passed_count,
        "failed": failed_count,
        "security_issues": security_issues,
        "results": [r.to_dict() for r in all_results]
    }


if __name__ == "__main__":
    results = run_all_tests()
    
    with open("boundary_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试结果已保存到: boundary_test_results.json")
