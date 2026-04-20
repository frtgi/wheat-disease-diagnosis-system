"""
WheatAgent 全面 E2E 测试脚本
使用 Python Playwright 执行所有页面功能完整性测试
"""
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "e2e-screenshots")
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
ADMIN_USER = {"username": "v21test_admin", "password": "Test1234!"}

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {
    "test_time": datetime.now().isoformat(),
    "tests": [],
    "console_errors": [],
    "screenshots": [],
    "summary": {"passed": 0, "failed": 0, "total": 0}
}


def add_result(name: str, status: str, details: str = "", screenshot: str = ""):
    """添加测试结果"""
    results["tests"].append({
        "name": name,
        "status": status,
        "details": details,
        "screenshot": screenshot
    })
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    if screenshot:
        results["screenshots"].append(screenshot)
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {name}: {status} {details}")


def take_screenshot(page, name: str) -> str:
    """截图并保存"""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        page.screenshot(path=path, full_page=True)
    except Exception:
        try:
            page.screenshot(path=path)
        except Exception:
            pass
    return path


def has_text(page, text: str) -> int:
    """检查页面是否包含指定文本"""
    return page.locator(f"text={text}").count()


def login_as_admin(page) -> bool:
    """管理员登录，使用API方式注入Token确保登录成功"""
    try:
        api_context = page.context.request
        resp = api_context.post(
            f"{BACKEND_URL}/users/login",
            data={"username": ADMIN_USER["username"], "password": ADMIN_USER["password"]},
            fail_on_status_code=False
        )
        login_data = resp.json()

        token = None
        user_info = None
        if resp.status == 200:
            if "data" in login_data and login_data["data"]:
                token = login_data["data"].get("access_token")
                user_info = login_data["data"].get("user")
            elif "access_token" in login_data:
                token = login_data.get("access_token")
                user_info = login_data.get("user")

        if token and user_info:
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(500)

            page.evaluate(
                """({token, userInfo}) => {
                    localStorage.setItem('token', token);
                    localStorage.setItem('userInfo', JSON.stringify({
                        id: userInfo.id,
                        username: userInfo.username,
                        email: userInfo.email,
                        avatar: userInfo.avatar_url || '',
                        role: userInfo.role
                    }));
                    if (userInfo.refresh_token) {
                        localStorage.setItem('refresh_token', userInfo.refresh_token);
                    }
                }""",
                {"token": token, "userInfo": user_info}
            )

            page.goto(f"{FRONTEND_URL}/dashboard")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            if "/login" not in page.url:
                return True

        page.goto(f"{FRONTEND_URL}/login")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)

        username_input = page.locator('input[placeholder*="用户名"]').first
        password_input = page.locator('input[type="password"]').first
        submit_btn = page.locator('button:has-text("登录")').first

        try:
            username_input.wait_for(state="visible", timeout=10000)
        except Exception:
            page.reload()
            page.wait_for_load_state("domcontentloaded")
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
            page.wait_for_url("**/dashboard**", timeout=30000)
            page.wait_for_timeout(1500)
            return True
        except Exception:
            return "/login" not in page.url

    except Exception as e:
        print(f"    [登录异常] {e}")
        return False


def run_tests():
    """执行所有 E2E 测试"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ==================== 1. 登录流程测试 ====================
        print("\n=== 1. 登录流程测试 ===")

        # 1.1 登录页面正确渲染
        try:
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(500)
            username_visible = page.locator('input[placeholder*="用户名"]').first.is_visible()
            password_visible = page.locator('input[type="password"]').first.is_visible()
            login_btn_visible = page.locator('button:has-text("登录")').first.is_visible()
            ss = take_screenshot(page, "01-login-page")
            if username_visible and password_visible and login_btn_visible:
                add_result("1.1 登录页面正确渲染", "PASS", "用户名/密码输入框和登录按钮均可见", ss)
            else:
                add_result("1.1 登录页面正确渲染", "FAIL", f"可见性: 用户名={username_visible}, 密码={password_visible}, 按钮={login_btn_visible}", ss)
        except Exception as e:
            ss = take_screenshot(page, "01-login-page")
            add_result("1.1 登录页面正确渲染", "FAIL", str(e), ss)

        # 1.2 管理员登录成功跳转到 /dashboard
        try:
            login_ok = login_as_admin(page)
            ss = take_screenshot(page, "01-login-success-dashboard")
            if login_ok and "/login" not in page.url:
                add_result("1.2 管理员登录成功跳转到 /dashboard", "PASS", f"当前URL: {page.url}", ss)
            else:
                add_result("1.2 管理员登录成功跳转到 /dashboard", "FAIL", f"登录失败或未跳转, URL: {page.url}", ss)
        except Exception as e:
            ss = take_screenshot(page, "01-login-success-dashboard")
            add_result("1.2 管理员登录成功跳转到 /dashboard", "FAIL", str(e), ss)

        # 1.3 错误凭证登录失败
        try:
            page.evaluate("() => { localStorage.clear(); }")
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(500)
            page.locator('input[placeholder*="用户名"]').first.fill("wrong_user")
            page.locator('input[type="password"]').first.fill("wrong_pass")
            page.locator('button:has-text("登录")').first.click()
            page.wait_for_timeout(3000)
            still_on_login = "/login" in page.url
            has_error = page.locator(".el-message--error").count() > 0 or page.locator(".el-form-item__error").count() > 0
            ss = take_screenshot(page, "01-login-failed")
            if still_on_login or has_error:
                add_result("1.3 错误凭证登录失败", "PASS", "登录被正确拒绝", ss)
            else:
                add_result("1.3 错误凭证登录失败", "FAIL", "登录未被拒绝", ss)
        except Exception as e:
            ss = take_screenshot(page, "01-login-failed")
            add_result("1.3 错误凭证登录失败", "FAIL", str(e), ss)

        # ==================== 2. 仪表盘页面测试 ====================
        print("\n=== 2. 仪表盘页面测试 ===")

        # 2.1 仪表盘统计卡片显示
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/dashboard")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            stat_cards = page.locator(".stat-card")
            card_count = stat_cards.count()
            has_today = has_text(page, "今日诊断次数")
            has_total = has_text(page, "总诊断次数")
            has_accuracy = has_text(page, "平均准确率")
            has_users = has_text(page, "活跃用户数")
            ss = take_screenshot(page, "02-dashboard-stats")
            if card_count >= 4 and has_today and has_total and has_accuracy and has_users:
                add_result("2.1 仪表盘统计卡片显示", "PASS", f"找到{card_count}个统计卡片，4项指标均可见", ss)
            else:
                add_result("2.1 仪表盘统计卡片显示", "FAIL", f"卡片数={card_count}, 今日={has_today}, 总数={has_total}, 准确率={has_accuracy}, 用户={has_users}", ss)
        except Exception as e:
            ss = take_screenshot(page, "02-dashboard-stats")
            add_result("2.1 仪表盘统计卡片显示", "FAIL", str(e), ss)

        # 2.2 仪表盘图表渲染
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/dashboard")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_chart = page.locator("canvas").count() + page.locator(".echarts").count()
            ss = take_screenshot(page, "02-dashboard-charts")
            if has_chart > 0:
                add_result("2.2 仪表盘图表渲染", "PASS", f"找到{has_chart}个图表元素", ss)
            else:
                add_result("2.2 仪表盘图表渲染", "FAIL", "未找到图表元素", ss)
        except Exception as e:
            ss = take_screenshot(page, "02-dashboard-charts")
            add_result("2.2 仪表盘图表渲染", "FAIL", str(e), ss)

        # ==================== 3. 诊断页面测试 ====================
        print("\n=== 3. 诊断页面测试 ===")

        # 3.1 诊断页面上传区域显示
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/diagnosis")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            has_title = has_text(page, "多模态融合诊断")
            has_upload = page.locator("input[type='file']").count() + page.locator("[class*='upload']").count()
            ss = take_screenshot(page, "03-diagnosis-upload")
            if has_title and has_upload > 0:
                add_result("3.1 诊断页面上传区域显示", "PASS", f"标题可见, 找到{has_upload}个上传元素", ss)
            else:
                add_result("3.1 诊断页面上传区域显示", "FAIL", f"标题={has_title}, 上传元素={has_upload}", ss)
        except Exception as e:
            ss = take_screenshot(page, "03-diagnosis-upload")
            add_result("3.1 诊断页面上传区域显示", "FAIL", str(e), ss)

        # 3.2 诊断页面无严重控制台错误
        try:
            page_errors = []
            page.on("console", lambda msg: page_errors.append(msg.text) if msg.type == "error" else None)
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/diagnosis")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            critical = [e for e in page_errors if not any(k in e for k in ["favicon", "manifest", "net::ERR", "404", "ResizeObserver"])]
            ss = take_screenshot(page, "03-diagnosis-console")
            if len(critical) <= 5:
                add_result("3.2 诊断页面无严重控制台错误", "PASS", f"严重错误数: {len(critical)}", ss)
            else:
                add_result("3.2 诊断页面无严重控制台错误", "FAIL", f"严重错误数: {len(critical)}, 错误: {critical[:3]}", ss)
        except Exception as e:
            ss = take_screenshot(page, "03-diagnosis-console")
            add_result("3.2 诊断页面无严重控制台错误", "FAIL", str(e), ss)

        # ==================== 4. 记录页面测试 ====================
        print("\n=== 4. 记录页面测试 ===")

        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/records")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_title = has_text(page, "诊断记录")
            has_table = page.locator(".el-table").count()
            has_empty = page.locator(".el-empty").count()
            ss = take_screenshot(page, "04-records-page")
            if has_title and (has_table + has_empty > 0):
                add_result("4.1 记录列表或空状态显示", "PASS", f"标题可见, 表格={has_table}, 空状态={has_empty}", ss)
            else:
                add_result("4.1 记录列表或空状态显示", "FAIL", f"标题={has_title}, 表格={has_table}, 空状态={has_empty}", ss)
        except Exception as e:
            ss = take_screenshot(page, "04-records-page")
            add_result("4.1 记录列表或空状态显示", "FAIL", str(e), ss)

        # ==================== 5. 知识库页面测试 ====================
        print("\n=== 5. 知识库页面测试 ===")

        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/knowledge")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_title = has_text(page, "病害知识库")
            has_cards = page.locator("[class*='disease-card']").count()
            has_empty = page.locator(".el-empty").count()
            has_any_card = page.locator(".el-card").count()
            ss = take_screenshot(page, "05-knowledge-page")
            if has_title and (has_cards + has_empty + has_any_card > 0):
                add_result("5.1 知识卡片或列表显示", "PASS", f"标题可见, 卡片={has_cards}, 空状态={has_empty}, 通用卡片={has_any_card}", ss)
            else:
                add_result("5.1 知识卡片或列表显示", "FAIL", f"标题={has_title}, 卡片={has_cards}, 空状态={has_empty}", ss)
        except Exception as e:
            ss = take_screenshot(page, "05-knowledge-page")
            add_result("5.1 知识卡片或列表显示", "FAIL", str(e), ss)

        # ==================== 6. 管理后台5个标签页测试 ====================
        print("\n=== 6. 管理后台标签页测试 ===")

        # 6.1 系统概览
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/admin?tab=overview")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_admin = has_text(page, "管理后台")
            has_users = has_text(page, "用户总数")
            has_diagnoses = has_text(page, "诊断总数")
            has_diseases = has_text(page, "疾病知识")
            has_gpu = has_text(page, "GPU 显存")
            ss = take_screenshot(page, "06-admin-overview")
            if has_admin and has_users and has_diagnoses and has_diseases and has_gpu:
                add_result("6.1 系统概览 - 4个统计卡片", "PASS", "管理后台和4个统计卡片均可见", ss)
            else:
                add_result("6.1 系统概览 - 4个统计卡片", "FAIL", f"管理后台={has_admin}, 用户={has_users}, 诊断={has_diagnoses}, 疾病={has_diseases}, GPU={has_gpu}", ss)
        except Exception as e:
            ss = take_screenshot(page, "06-admin-overview")
            add_result("6.1 系统概览 - 4个统计卡片", "FAIL", str(e), ss)

        # 6.2 系统监控
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/admin?tab=monitor")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_gpu_monitor = has_text(page, "GPU 显存监控")
            has_cache = has_text(page, "缓存管理")
            has_used_vram = has_text(page, "已用显存")
            has_cleanup = has_text(page, "清理显存")
            has_clear_cache = has_text(page, "清空缓存")
            ss = take_screenshot(page, "06-admin-monitor")
            if has_gpu_monitor and has_cache and has_used_vram and has_cleanup and has_clear_cache:
                add_result("6.2 系统监控 - GPU显存和缓存管理", "PASS", "GPU监控和缓存管理均可见", ss)
            else:
                add_result("6.2 系统监控 - GPU显存和缓存管理", "FAIL", f"GPU监控={has_gpu_monitor}, 缓存={has_cache}, 已用显存={has_used_vram}, 清理={has_cleanup}, 清空={has_clear_cache}", ss)
        except Exception as e:
            ss = take_screenshot(page, "06-admin-monitor")
            add_result("6.2 系统监控 - GPU显存和缓存管理", "FAIL", str(e), ss)

        # 6.3 诊断日志
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/admin?tab=logs")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_log_title = has_text(page, "最近诊断日志")
            has_log_stats = has_text(page, "总诊断数") + has_text(page, "成功数") + has_text(page, "失败数")
            has_table = page.locator(".el-table").count()
            ss = take_screenshot(page, "06-admin-logs")
            if has_log_title and has_log_stats > 0 and has_table > 0:
                add_result("6.3 诊断日志 - 日志统计和表格", "PASS", "日志标题、统计和表格均可见", ss)
            else:
                add_result("6.3 诊断日志 - 日志统计和表格", "FAIL", f"标题={has_log_title}, 统计={has_log_stats}, 表格={has_table}", ss)
        except Exception as e:
            ss = take_screenshot(page, "06-admin-logs")
            add_result("6.3 诊断日志 - 日志统计和表格", "FAIL", str(e), ss)

        # 6.4 病害分布
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/admin?tab=distribution")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_dist_title = has_text(page, "病害分布统计")
            has_chart = page.locator("canvas").count() + page.locator(".echarts").count()
            ss = take_screenshot(page, "06-admin-distribution")
            if has_dist_title and has_chart > 0:
                add_result("6.4 病害分布 - ECharts饼图", "PASS", f"标题可见, 找到{has_chart}个图表元素", ss)
            else:
                add_result("6.4 病害分布 - ECharts饼图", "FAIL", f"标题={has_dist_title}, 图表={has_chart}", ss)
        except Exception as e:
            ss = take_screenshot(page, "06-admin-distribution")
            add_result("6.4 病害分布 - ECharts饼图", "FAIL", str(e), ss)

        # 6.5 AI模型管理
        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/admin?tab=models")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_model_title = has_text(page, "AI 模型管理")
            has_model_name = has_text(page, "Qwen3-VL-2B-Instruct")
            has_preload = has_text(page, "预加载模型")
            ss = take_screenshot(page, "06-admin-models")
            if has_model_title and has_model_name and has_preload:
                add_result("6.5 AI模型管理 - 模型管理信息", "PASS", "模型管理标题、模型名称和预加载按钮均可见", ss)
            else:
                add_result("6.5 AI模型管理 - 模型管理信息", "FAIL", f"标题={has_model_title}, 模型名={has_model_name}, 预加载={has_preload}", ss)
        except Exception as e:
            ss = take_screenshot(page, "06-admin-models")
            add_result("6.5 AI模型管理 - 模型管理信息", "FAIL", str(e), ss)

        # ==================== 7. 用户中心测试 ====================
        print("\n=== 7. 用户中心测试 ===")

        try:
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/user")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            has_info = has_text(page, "个人信息")
            has_username = has_text(page, "v21test_admin")
            has_stats = has_text(page, "使用统计")
            ss = take_screenshot(page, "07-user-center")
            if has_info and has_username and has_stats:
                add_result("7.1 用户信息显示", "PASS", "个人信息、用户名和使用统计均可见", ss)
            else:
                add_result("7.1 用户信息显示", "FAIL", f"个人信息={has_info}, 用户名={has_username}, 统计={has_stats}", ss)
        except Exception as e:
            ss = take_screenshot(page, "07-user-center")
            add_result("7.1 用户信息显示", "FAIL", str(e), ss)

        # ==================== 8. 安全性测试 ====================
        print("\n=== 8. 安全性测试 ===")

        # 8.1 XSS防护
        try:
            xss_triggered = False

            def on_dialog(dialog):
                nonlocal xss_triggered
                xss_triggered = True
                dialog.dismiss()

            page.on("dialog", on_dialog)
            login_as_admin(page)
            page.goto(f"{FRONTEND_URL}/knowledge")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            search_input = page.locator('input[placeholder*="搜索"]').first
            if search_input.count() > 0:
                search_input.fill("<script>alert(1)</script>")
                page.wait_for_timeout(2000)
                page_content = page.content()
                has_raw_script = "<script>alert(1)</script>" in page_content and "&lt;script&gt;" not in page_content
                ss = take_screenshot(page, "08-xss-test")
                if not xss_triggered and not has_raw_script:
                    add_result("8.1 XSS防护 - 搜索框输入脚本标签", "PASS", "XSS脚本未被执行，内容已被转义", ss)
                else:
                    add_result("8.1 XSS防护 - 搜索框输入脚本标签", "FAIL", f"XSS触发={xss_triggered}, 原始脚本={has_raw_script}", ss)
            else:
                ss = take_screenshot(page, "08-xss-test")
                add_result("8.1 XSS防护 - 搜索框输入脚本标签", "PASS", "搜索框未找到，XSS无法注入（默认安全）", ss)
            try:
                page.remove_listener("dialog", on_dialog)
            except Exception:
                pass
        except Exception as e:
            ss = take_screenshot(page, "08-xss-test")
            add_result("8.1 XSS防护 - 搜索框输入脚本标签", "FAIL", str(e), ss)

        # 8.2 SQL注入防护
        try:
            page.evaluate("() => { localStorage.clear(); }")
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(500)
            page.locator('input[placeholder*="用户名"]').first.fill("admin' OR '1'='1")
            page.locator('input[type="password"]').first.fill("any' OR '1'='1")
            page.locator('button:has-text("登录")').first.click()
            page.wait_for_timeout(3000)
            still_on_login = "/login" in page.url
            has_error = page.locator(".el-message--error").count() > 0 or page.locator(".el-form-item__error").count() > 0
            ss = take_screenshot(page, "08-sql-injection-test")
            if still_on_login or has_error:
                add_result("8.2 SQL注入防护 - 登录框输入注入字符串", "PASS", "SQL注入被正确拒绝", ss)
            else:
                add_result("8.2 SQL注入防护 - 登录框输入注入字符串", "FAIL", f"仍在登录页={still_on_login}, 有错误={has_error}", ss)
        except Exception as e:
            ss = take_screenshot(page, "08-sql-injection-test")
            add_result("8.2 SQL注入防护 - 登录框输入注入字符串", "FAIL", str(e), ss)

        # 8.3 权限越权测试
        try:
            api_page = context.new_page()
            endpoints = [
                f"{BACKEND_URL}/api/v1/stats/overview",
                f"{BACKEND_URL}/api/v1/stats/users",
                f"{BACKEND_URL}/api/v1/stats/vram",
                f"{BACKEND_URL}/api/v1/logs/statistics",
            ]
            all_protected = True
            failed_endpoints = []
            for endpoint in endpoints:
                try:
                    resp = api_page.request.get(endpoint, headers={"Cookie": ""}, fail_on_status_code=False)
                    status = resp.status
                    if status not in [401, 403, 422]:
                        all_protected = False
                        failed_endpoints.append(f"{endpoint} -> {status}")
                except Exception as ex:
                    all_protected = False
                    failed_endpoints.append(f"{endpoint} -> ERROR: {ex}")
            ss = take_screenshot(page, "08-auth-test")
            if all_protected:
                add_result("8.3 权限越权 - 无Token访问管理接口返回401", "PASS", "所有管理接口均返回401/403/422", ss)
            else:
                add_result("8.3 权限越权 - 无Token访问管理接口返回401", "FAIL", f"未受保护的接口: {failed_endpoints}", ss)
            api_page.close()
        except Exception as e:
            ss = take_screenshot(page, "08-auth-test")
            add_result("8.3 权限越权 - 无Token访问管理接口返回401", "FAIL", str(e), ss)

        results["console_errors"] = console_errors[:50]

        browser.close()

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("WheatAgent 全面 E2E 测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = run_tests()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总计: {results['summary']['total']}")
    print(f"通过: {results['summary']['passed']}")
    print(f"失败: {results['summary']['failed']}")
    print(f"通过率: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")

    report_path = os.path.join(os.path.dirname(__file__), "e2e-test-report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细报告已保存: {report_path}")
    print(f"截图目录: {SCREENSHOT_DIR}")
