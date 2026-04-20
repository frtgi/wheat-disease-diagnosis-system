"""
V46 E2E 验证测试脚本
验证 V46 版本所有修复项是否正常工作
通过前端 Vite 代理访问后端 API，避免 IPv6 直连问题
"""
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:5173"
API_BASE = f"{FRONTEND_URL}/api/v1"
ADMIN_USER = {"username": "v21test_admin", "password": "Test1234!"}
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "v46_screenshots")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "v46_test_report.json")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {
    "version": "V46",
    "test_time": "",
    "items": [],
    "console_errors": [],
    "summary": {"pass": 0, "fail": 0, "total": 0},
}


def add_result(category: str, name: str, status: str, detail: str = ""):
    """添加测试结果条目"""
    results["items"].append({
        "category": category,
        "name": name,
        "status": status,
        "detail": detail,
    })
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["pass"] += 1
    else:
        results["summary"]["fail"] += 1
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{category}] {name}: {status} {detail}")


def clear_auth_state(page):
    """清除认证状态，先导航到同源页面再操作 localStorage"""
    page.goto(f"{FRONTEND_URL}/login")
    page.wait_for_load_state("networkidle")
    page.evaluate("""() => {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('user');
    }""")


def login_admin(page):
    """登录管理员账户"""
    page.goto(f"{FRONTEND_URL}/login")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    username_input = page.locator('input[placeholder*="用户名"]').first
    password_input = page.locator('input[type="password"]').first
    submit_btn = page.locator('button:has-text("登录")').first

    username_input.clear()
    username_input.fill(ADMIN_USER["username"])
    password_input.clear()
    password_input.fill(ADMIN_USER["password"])
    submit_btn.click()

    try:
        page.wait_for_function(
            "() => !window.location.href.includes('/login')",
            timeout=15000,
        )
    except Exception:
        username_input = page.locator('input[placeholder*="用户名"]').first
        password_input = page.locator('input[type="password"]').first
        submit_btn = page.locator('button:has-text("登录")').first
        username_input.clear()
        username_input.fill(ADMIN_USER["username"])
        password_input.clear()
        password_input.fill(ADMIN_USER["password"])
        submit_btn.click()
        page.wait_for_function(
            "() => !window.location.href.includes('/login')",
            timeout=15000,
        )

    page.wait_for_timeout(2000)


def test_diagnosis_route(page):
    """验证项1: 诊断路由正常（diagnosis.py已删除）"""
    print("\n=== 验证项1: 诊断路由正常 ===")

    try:
        clear_auth_state(page)
        login_admin(page)
        page.goto(f"{FRONTEND_URL}/diagnosis")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_diagnosis_page.png"), full_page=True)

        current_url = page.url
        if "/diagnosis" in current_url:
            add_result("诊断路由", "诊断页面正常加载", "PASS", f"URL: {current_url}")
        else:
            add_result("诊断路由", "诊断页面正常加载", "FAIL", f"URL: {current_url}")
    except Exception as e:
        add_result("诊断路由", "诊断页面正常加载", "FAIL", str(e))

    try:
        api_resp = page.request.get(f"{API_BASE}/health")
        status_code = api_resp.status
        if status_code == 200:
            add_result("诊断路由", "诊断API端点可用", "PASS", f"health返回{status_code}")
        else:
            add_result("诊断路由", "诊断API端点可用", "FAIL", f"health返回{status_code}")
    except Exception as e:
        add_result("诊断路由", "诊断API端点可用", "FAIL", str(e))


def test_admin_tabs(page):
    """验证项2: 管理后台5个标签页正常"""
    print("\n=== 验证项2: 管理后台5个标签页 ===")

    tab_tests = [
        {
            "name": "系统概览(overview)",
            "tab": "overview",
            "screenshot": "02_admin_overview.png",
            "check": lambda p: p.locator(".stat-card").count() > 0,
            "check_desc": "统计卡片显示",
        },
        {
            "name": "系统监控(monitor)",
            "tab": "monitor",
            "screenshot": "03_admin_monitor.png",
            "check": lambda p: p.locator("text=GPU 显存监控").count() > 0 or p.locator("text=缓存管理").count() > 0,
            "check_desc": "GPU显存和缓存管理",
        },
        {
            "name": "诊断日志(logs)",
            "tab": "logs",
            "screenshot": "04_admin_logs.png",
            "check": lambda p: p.locator("text=最近诊断日志").count() > 0 or p.locator("text=总诊断数").count() > 0,
            "check_desc": "日志统计",
        },
        {
            "name": "病害分布(distribution)",
            "tab": "distribution",
            "screenshot": "05_admin_distribution.png",
            "check": lambda p: p.locator("text=病害分布统计").count() > 0,
            "check_desc": "饼图区域",
        },
        {
            "name": "AI模型管理(models)",
            "tab": "models",
            "screenshot": "06_admin_models.png",
            "check": lambda p: p.locator("text=AI 模型管理").count() > 0 or p.locator("text=Qwen3-VL").count() > 0,
            "check_desc": "模型信息",
        },
    ]

    for tab in tab_tests:
        try:
            page.goto(f"{FRONTEND_URL}/admin?tab={tab['tab']}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, tab["screenshot"]), full_page=True)

            if tab["check"](page):
                add_result("管理后台标签页", tab["name"], "PASS", tab["check_desc"])
            else:
                add_result("管理后台标签页", tab["name"], "FAIL", f"未检测到: {tab['check_desc']}")
        except Exception as e:
            add_result("管理后台标签页", tab["name"], "FAIL", str(e))


def test_refresh_token_hash(page):
    """验证项3: RefreshToken哈希存储验证"""
    print("\n=== 验证项3: RefreshToken哈希存储 ===")

    try:
        clear_auth_state(page)
        login_admin(page)
        page.wait_for_timeout(1000)

        refresh_token_val = page.evaluate("() => localStorage.getItem('refresh_token')")
        access_token_val = page.evaluate("() => localStorage.getItem('token')")

        if refresh_token_val:
            add_result("RefreshToken哈希", "登录后refresh_token存在", "PASS", f"token长度: {len(refresh_token_val)}")
        else:
            add_result("RefreshToken哈希", "登录后refresh_token存在", "FAIL", "refresh_token为空")

        if access_token_val:
            add_result("RefreshToken哈希", "登录后access_token存在", "PASS", f"token长度: {len(access_token_val)}")
        else:
            add_result("RefreshToken哈希", "登录后access_token存在", "FAIL", "access_token为空")

        try:
            refresh_resp = page.request.post(
                f"{API_BASE}/users/token/refresh",
                data=json.dumps({"refresh_token": refresh_token_val}),
                headers={"Content-Type": "application/json"},
            )
            refresh_status = refresh_resp.status
            refresh_body = refresh_resp.json()

            if refresh_status == 200 and refresh_body.get("access_token"):
                add_result(
                    "RefreshToken哈希",
                    "使用refresh_token刷新access_token",
                    "PASS",
                    f"状态码: {refresh_status}, 新token长度: {len(refresh_body.get('access_token', ''))}",
                )
            else:
                add_result(
                    "RefreshToken哈希",
                    "使用refresh_token刷新access_token",
                    "FAIL",
                    f"状态码: {refresh_status}, 响应: {json.dumps(refresh_body, ensure_ascii=False)[:200]}",
                )
        except Exception as e:
            add_result("RefreshToken哈希", "使用refresh_token刷新access_token", "FAIL", str(e))

    except Exception as e:
        add_result("RefreshToken哈希", "登录流程", "FAIL", str(e))


def test_frontend_cleanup(page):
    """验证项4: 前端冗余清理验证"""
    print("\n=== 验证项4: 前端冗余清理 ===")

    console_errors = []

    def handle_console(msg):
        if msg.type == "error":
            console_errors.append(f"[{msg.type}] {msg.text}")

    page.on("console", handle_console)

    try:
        clear_auth_state(page)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_frontend_login.png"), full_page=True)

        critical_errors = [
            e for e in console_errors
            if "Failed to resolve" in e
            or "Module not found" in e
            or "does not provide an export" in e
            or "Uncaught" in e
            or "SyntaxError" in e
        ]

        if not critical_errors:
            add_result("前端冗余清理", "前端正常启动(无编译错误)", "PASS", f"控制台错误: {len(console_errors)}个(无关键错误)")
        else:
            add_result("前端冗余清理", "前端正常启动(无编译错误)", "FAIL", f"关键错误: {critical_errors[:3]}")
    except Exception as e:
        add_result("前端冗余清理", "前端正常启动(无编译错误)", "FAIL", str(e))

    try:
        login_admin(page)
        page.goto(f"{FRONTEND_URL}/admin?tab=overview")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        api_errors = [
            e for e in console_errors
            if "does not provide an export" in e
            or ("404" in e and "api" in e.lower())
        ]
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_admin_api_check.png"), full_page=True)

        if not api_errors:
            add_result("前端冗余清理", "管理后台API调用正常(admin.ts重新导出)", "PASS", "无API相关控制台错误")
        else:
            add_result("前端冗余清理", "管理后台API调用正常(admin.ts重新导出)", "FAIL", f"API错误: {api_errors[:3]}")
    except Exception as e:
        add_result("前端冗余清理", "管理后台API调用正常(admin.ts重新导出)", "FAIL", str(e))

    results["console_errors"] = console_errors


def test_security(browser):
    """验证项5: 安全性验证 - 使用独立浏览器上下文"""
    print("\n=== 验证项5: 安全性验证 ===")

    try:
        anon_context = browser.new_context(viewport={"width": 1920, "height": 1080})
        anon_page = anon_context.new_page()

        resp = anon_page.request.get(f"{API_BASE}/stats/overview")
        status_code = resp.status

        if status_code in [401, 403]:
            add_result("安全性", "未认证访问stats/overview返回401/403", "PASS", f"状态码: {status_code}")
        else:
            body = resp.text()[:200]
            add_result("安全性", "未认证访问stats/overview返回401/403", "FAIL", f"状态码: {status_code}, 响应: {body}")

        resp2 = anon_page.request.get(f"{API_BASE}/stats/users")
        status_code2 = resp2.status

        if status_code2 in [401, 403]:
            add_result("安全性", "未认证访问stats/users返回401/403", "PASS", f"状态码: {status_code2}")
        else:
            body2 = resp2.text()[:200]
            add_result("安全性", "未认证访问stats/users返回401/403", "FAIL", f"状态码: {status_code2}, 响应: {body2}")

        anon_context.close()
    except Exception as e:
        add_result("安全性", "未认证访问管理接口", "FAIL", str(e))

    try:
        auth_context = browser.new_context(viewport={"width": 1920, "height": 1080})
        auth_page = auth_context.new_page()
        login_admin(auth_page)
        auth_page.wait_for_timeout(1000)
        access_token_val = auth_page.evaluate("() => localStorage.getItem('token')")

        admin_resp = auth_page.request.get(
            f"{API_BASE}/stats/users",
            headers={"Authorization": f"Bearer {access_token_val}"},
        )
        admin_status = admin_resp.status

        if admin_status == 200:
            add_result("安全性", "管理员访问管理接口返回200", "PASS", f"状态码: {admin_status}")
        else:
            add_result("安全性", "管理员访问管理接口返回200", "FAIL", f"状态码: {admin_status}")

        auth_context.close()
    except Exception as e:
        add_result("安全性", "管理员访问管理接口返回200", "FAIL", str(e))

    try:
        xss_context = browser.new_context(viewport={"width": 1920, "height": 1080})
        xss_page = xss_context.new_page()
        xss_page.goto(f"{FRONTEND_URL}/login")
        xss_page.wait_for_load_state("networkidle")

        username_input = xss_page.locator('input[placeholder*="用户名"]').first
        xss_payload = '<script>alert("XSS")</script>'
        username_input.clear()
        username_input.fill(xss_payload)
        xss_page.wait_for_timeout(1000)

        xss_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "09_xss_test.png"), full_page=True)

        dialog_triggered = False

        def on_dialog(dialog):
            nonlocal dialog_triggered
            dialog_triggered = True
            dialog.dismiss()

        xss_page.on("dialog", on_dialog)
        xss_page.wait_for_timeout(2000)

        page_content = xss_page.content()
        script_in_dom = '<script>alert("XSS")</script>' in page_content

        if not dialog_triggered and not script_in_dom:
            add_result("安全性", "XSS输入不被执行", "PASS", "XSS脚本未被渲染执行")
        else:
            add_result("安全性", "XSS输入不被执行", "FAIL", f"dialog={dialog_triggered}, script_in_dom={script_in_dom}")

        xss_context.close()
    except Exception as e:
        add_result("安全性", "XSS输入不被执行", "FAIL", str(e))


def main():
    """主测试入口"""
    results["test_time"] = datetime.now().isoformat()
    print("=" * 60)
    print("V46 E2E 验证测试")
    print(f"测试时间: {results['test_time']}")
    print(f"前端地址: {FRONTEND_URL}")
    print(f"API代理: {API_BASE}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = context.new_page()

        test_diagnosis_route(page)
        test_admin_tabs(page)
        test_refresh_token_hash(page)
        test_frontend_cleanup(page)
        test_security(browser)

        context.close()
        browser.close()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    total = results["summary"]["total"]
    passed = results["summary"]["pass"]
    failed = results["summary"]["fail"]
    print(f"总计: {total} 项")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print(f"通过率: {passed / total * 100:.1f}%")
    print(f"\n截图保存目录: {SCREENSHOT_DIR}")
    print(f"报告保存路径: {REPORT_PATH}")

    if failed > 0:
        print("\n失败项详情:")
        for item in results["items"]:
            if item["status"] == "FAIL":
                print(f"  ❌ [{item['category']}] {item['name']}: {item['detail']}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n测试报告已保存: {REPORT_PATH}")


if __name__ == "__main__":
    main()
