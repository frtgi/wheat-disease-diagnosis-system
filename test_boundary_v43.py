# -*- coding: utf-8 -*-
"""
WheatAgent 后端边界条件与安全测试脚本
测试认证、权限、XSS/SQL注入防护、文件上传安全、Token黑名单等场景
"""
import requests
import sys
import time

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

results = []

_cached_admin_token = None
_cached_admin_refresh = None


def record(test_name, passed, detail=""):
    """记录测试结果"""
    status = "PASS" if passed else "FAIL"
    results.append({"test": test_name, "status": status, "detail": detail})
    print(f"  [{status}] {test_name}: {detail}")


def login(username, password):
    """登录并返回 (access_token, refresh_token, 响应)"""
    resp = requests.post(
        f"{BASE_URL}{API_PREFIX}/users/login",
        json={"username": username, "password": password}
    )
    data = resp.json()
    access_token = data.get("data", {}).get("access_token") if resp.status_code == 200 else None
    refresh_token = data.get("data", {}).get("refresh_token") if resp.status_code == 200 else None
    return access_token, refresh_token, resp


def get_admin_token():
    """获取管理员Token（带缓存，避免重复登录触发限流）"""
    global _cached_admin_token, _cached_admin_refresh
    if _cached_admin_token:
        return _cached_admin_token, _cached_admin_refresh
    access_token, refresh_token, resp = login("v21test_admin", "Test1234!")
    if access_token:
        _cached_admin_token = access_token
        _cached_admin_refresh = refresh_token
    return access_token, refresh_token


def test_1_invalid_token():
    """测试1: 无效Token请求"""
    print("\n=== 测试1: 无效Token请求 ===")
    try:
        resp = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        passed = resp.status_code == 401
        record("无效Token请求返回401", passed,
               f"状态码={resp.status_code}, 响应={resp.text[:200]}")
    except Exception as e:
        record("无效Token请求返回401", False, f"请求异常: {e}")


def test_2_token_type_confusion():
    """测试2: Refresh Token当作Access Token使用"""
    print("\n=== 测试2: Refresh Token类型混淆 ===")
    try:
        access_token, refresh_token = get_admin_token()
        if not refresh_token:
            record("Refresh Token类型混淆", False,
                   "登录失败，无法获取refresh_token")
            return

        resp = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        passed = resp.status_code == 401
        record("Refresh Token作为Access Token被拒绝(401)", passed,
               f"状态码={resp.status_code}, 响应={resp.text[:200]}")
    except Exception as e:
        record("Refresh Token类型混淆", False, f"请求异常: {e}")


def test_3_admin_endpoints():
    """测试3: 管理员端点权限控制"""
    print("\n=== 测试3: 管理员端点权限控制 ===")
    try:
        access_token, _ = get_admin_token()
        if not access_token:
            record("管理员端点权限控制", False, "管理员登录失败")
            return

        headers = {"Authorization": f"Bearer {access_token}"}

        resp_vram = requests.get(f"{BASE_URL}{API_PREFIX}/stats/vram", headers=headers)
        vram_ok = resp_vram.status_code in [200, 500]
        record("管理员访问 GET /stats/vram", vram_ok,
               f"状态码={resp_vram.status_code}, 响应={resp_vram.text[:200]}")

        resp_logs = requests.get(f"{BASE_URL}{API_PREFIX}/logs/statistics", headers=headers)
        logs_ok = resp_logs.status_code in [200, 500]
        record("管理员访问 GET /logs/statistics", logs_ok,
               f"状态码={resp_logs.status_code}, 响应={resp_logs.text[:200]}")

        resp_cleanup = requests.post(f"{BASE_URL}{API_PREFIX}/stats/vram/cleanup", headers=headers)
        cleanup_ok = resp_cleanup.status_code in [200, 500]
        record("管理员访问 POST /stats/vram/cleanup", cleanup_ok,
               f"状态码={resp_cleanup.status_code}, 响应={resp_cleanup.text[:200]}")

        resp_no_token = requests.get(f"{BASE_URL}{API_PREFIX}/stats/vram")
        no_token_ok = resp_no_token.status_code in [401, 403]
        record("无Token访问 /stats/vram 被拒绝(401/403)", no_token_ok,
               f"状态码={resp_no_token.status_code}, 响应={resp_no_token.text[:200]}")

    except Exception as e:
        record("管理员端点权限控制", False, f"请求异常: {e}")


def test_4_xss_protection():
    """测试4: XSS输入防护"""
    print("\n=== 测试4: XSS输入防护 ===")
    try:
        xss_username = "<script>alert(1)</script>"
        resp = requests.post(
            f"{BASE_URL}{API_PREFIX}/users/register",
            json={
                "username": xss_username,
                "email": "xss_test@example.com",
                "password": "Test1234!"
            }
        )
        passed = resp.status_code in [400, 422, 409]
        record("XSS用户名注册被拒绝(400/422)", passed,
               f"状态码={resp.status_code}, 响应={resp.text[:200]}")
    except Exception as e:
        record("XSS输入防护", False, f"请求异常: {e}")


def test_5_sql_injection():
    """测试5: SQL注入防护"""
    print("\n=== 测试5: SQL注入防护 ===")
    try:
        sql_username = "' OR '1'='1"
        resp = requests.post(
            f"{BASE_URL}{API_PREFIX}/users/login",
            json={
                "username": sql_username,
                "password": "anything"
            }
        )
        not_server_error = resp.status_code < 500
        not_success_login = not (resp.status_code == 200 and
                                 resp.json().get("success") is True)
        passed = not_server_error and not_success_login
        record("SQL注入登录被拒绝(非500且非成功)", passed,
               f"状态码={resp.status_code}, 响应={resp.text[:200]}")
    except Exception as e:
        record("SQL注入防护", False, f"请求异常: {e}")


def test_6_large_file_upload():
    """测试6: 大文件上传防护"""
    print("\n=== 测试6: 大文件上传防护(50MB) ===")
    try:
        access_token, _ = get_admin_token()
        if not access_token:
            record("大文件上传防护", False, "登录失败")
            return

        large_content = b"\x00" * (50 * 1024 * 1024)
        resp = requests.post(
            f"{BASE_URL}{API_PREFIX}/upload/image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("large_test.jpg", large_content, "image/jpeg")}
        )
        passed = resp.status_code in [400, 413, 422]
        record("50MB文件上传被拒绝(400/413/422)", passed,
               f"状态码={resp.status_code}, 响应={resp.text[:300]}")
    except Exception as e:
        record("大文件上传防护", False, f"请求异常: {e}")


def test_7_invalid_image_upload():
    """测试7: 非图像文件上传"""
    print("\n=== 测试7: 非图像文件上传 ===")
    try:
        access_token, _ = get_admin_token()
        if not access_token:
            record("非图像文件上传", False, "登录失败")
            return

        text_content = b"This is not an image, just plain text content."
        resp = requests.post(
            f"{BASE_URL}{API_PREFIX}/diagnosis/image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("test.txt", text_content, "text/plain")}
        )
        passed = resp.status_code in [400, 415, 422]
        record("非图像文件上传被拒绝(400/415/422)", passed,
               f"状态码={resp.status_code}, 响应={resp.text[:200]}")
    except Exception as e:
        record("非图像文件上传", False, f"请求异常: {e}")


def test_8_token_blacklist_after_logout():
    """测试8: 登出后Token黑名单"""
    print("\n=== 测试8: 登出后Token黑名单 ===")
    try:
        # 等待限流窗口重置后重新登录获取独立Token
        print("  等待限流窗口重置...")
        time.sleep(65)

        # 清除缓存，强制重新登录获取独立Token
        global _cached_admin_token, _cached_admin_refresh
        _cached_admin_token = None
        _cached_admin_refresh = None

        access_token, _, login_resp = login("v21test_admin", "Test1234!")
        if not access_token:
            record("登出后Token黑名单", False,
                   f"登录失败, 响应={login_resp.text[:200]}")
            return

        headers = {"Authorization": f"Bearer {access_token}"}

        resp_before = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=headers)
        before_ok = resp_before.status_code == 200
        record("登出前 /users/me 返回200", before_ok,
               f"状态码={resp_before.status_code}, 响应={resp_before.text[:200]}")

        resp_logout = requests.post(f"{BASE_URL}{API_PREFIX}/users/logout", headers=headers)
        logout_ok = resp_logout.status_code == 200
        record("登出请求返回200", logout_ok,
               f"状态码={resp_logout.status_code}, 响应={resp_logout.text[:200]}")

        resp_after = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=headers)
        after_ok = resp_after.status_code == 401
        record("登出后 /users/me 返回401", after_ok,
               f"状态码={resp_after.status_code}, 响应={resp_after.text[:200]}")

    except Exception as e:
        record("登出后Token黑名单", False, f"请求异常: {e}")


def test_9_knowledge_graph_integrity():
    """测试9: 知识图谱数据完整性"""
    print("\n=== 测试9: 知识图谱数据完整性 ===")
    try:
        # 等待限流窗口重置后重新登录
        print("  等待限流窗口重置...")
        time.sleep(65)

        access_token, _, login_resp = login("v21test_admin", "Test1234!")
        if not access_token:
            record("知识图谱数据完整性", False,
                   f"登录失败, 响应={login_resp.text[:200]}")
            return

        # 更新缓存供后续测试使用
        global _cached_admin_token, _cached_admin_refresh
        _cached_admin_token = access_token

        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(f"{BASE_URL}{API_PREFIX}/knowledge/graph", headers=headers)

        if resp.status_code != 200:
            record("知识图谱数据完整性", False,
                   f"请求失败, 状态码={resp.status_code}, 响应={resp.text[:200]}")
            return

        data = resp.json()
        nodes = data.get("nodes", [])
        relations = data.get("relations", [])

        has_nodes = len(nodes) > 0
        has_relations = len(relations) > 0

        record("知识图谱包含节点", has_nodes,
               f"节点数={len(nodes)}")
        record("知识图谱包含关系(relations>0)", has_relations,
               f"关系数={len(relations)}")

    except Exception as e:
        record("知识图谱数据完整性", False, f"请求异常: {e}")


def test_10_health_check():
    """测试10: 健康检查"""
    print("\n=== 测试10: 健康检查 ===")
    try:
        resp_health = requests.get(f"{BASE_URL}/health")
        health_ok = resp_health.status_code == 200
        record("GET /health 返回200", health_ok,
               f"状态码={resp_health.status_code}, 响应={resp_health.text[:200]}")

        resp_components = requests.get(f"{BASE_URL}{API_PREFIX}/health/components")
        components_ok = resp_components.status_code == 200
        detail = f"状态码={resp_components.status_code}"
        if components_ok:
            comp_data = resp_components.json()
            components_info = comp_data.get("components", {})
            summary = comp_data.get("summary", {})
            detail += (f", 组件={list(components_info.keys())}, "
                       f"摘要={summary}")
        else:
            detail += f", 响应={resp_components.text[:200]}"
        record("GET /api/v1/health/components 返回200", components_ok, detail)

    except Exception as e:
        record("健康检查", False, f"请求异常: {e}")


def print_summary():
    """打印测试结果汇总"""
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    for r in results:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {icon} [{r['status']}] {r['test']}: {r['detail']}")

    print("-" * 70)
    print(f"  总计: {total} | 通过: {passed} | 失败: {failed}")
    print("=" * 70)

    if failed > 0:
        print("\n失败项详情:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['test']}: {r['detail']}")

    return failed == 0


if __name__ == "__main__":
    print("=" * 70)
    print("WheatAgent 后端边界条件与安全测试")
    print(f"目标: {BASE_URL}")
    print("=" * 70)

    test_1_invalid_token()
    test_2_token_type_confusion()
    test_3_admin_endpoints()
    test_4_xss_protection()
    test_5_sql_injection()
    test_6_large_file_upload()
    test_7_invalid_image_upload()
    test_8_token_blacklist_after_logout()
    test_9_knowledge_graph_integrity()
    test_10_health_check()

    all_passed = print_summary()
    sys.exit(0 if all_passed else 1)
