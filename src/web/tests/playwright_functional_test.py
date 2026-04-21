# -*- coding: utf-8 -*-
"""
WheatAgent 前端功能测试脚本
使用 Playwright 对登录页面、知识图谱页面、Admin页面、会话管理、诊断记录进行自动化测试
"""
import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:8000"

TEST_USERNAME = "test_session_user"
TEST_PASSWORD = "Test1234!"

test_results = []


def take_screenshot(page: Page, name: str) -> str:
    """
    截图并保存到指定目录
    @param page Playwright页面对象
    @param name 截图文件名（不含扩展名）
    @return 截图文件完整路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=filepath, full_page=True)
    print(f"  截图已保存: {filepath}")
    return filepath


def add_result(test_name: str, passed: bool, screenshot_path: str, details: str = ""):
    """
    记录测试结果
    @param test_name 测试名称
    @param passed 是否通过
    @param screenshot_path 截图路径
    @param details 详细信息
    """
    result = {
        "test_name": test_name,
        "status": "PASS" if passed else "FAIL",
        "screenshot": screenshot_path,
        "details": details
    }
    test_results.append(result)
    status_icon = "✅" if passed else "❌"
    print(f"  {status_icon} {test_name}: {'PASS' if passed else 'FAIL'}")
    if details:
        print(f"     详情: {details}")


def test_login_page(page: Page):
    """
    测试1: 登录页面渲染
    访问 /login 页面，确认页面正常渲染，检查标题、输入框、按钮等元素
    """
    print("\n" + "=" * 60)
    print("测试1: 登录页面渲染")
    print("=" * 60)

    try:
        page.goto(f"{FRONTEND_URL}/login", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(1)

        screenshot_path = take_screenshot(page, "01_login_page")

        heading = page.locator("h2")
        heading_visible = heading.is_visible()
        heading_text = heading.inner_text() if heading_visible else ""

        username_input = page.locator('input[placeholder="请输入用户名"]')
        password_input = page.locator('input[placeholder="请输入密码"]')
        login_button = page.locator('button:has-text("登录")')

        username_visible = username_input.is_visible()
        password_visible = password_input.is_visible()
        button_visible = login_button.is_visible()

        all_visible = heading_visible and username_visible and password_visible and button_visible
        details_parts = []
        if not heading_visible:
            details_parts.append("标题不可见")
        else:
            details_parts.append(f"标题文本: {heading_text}")
        if not username_visible:
            details_parts.append("用户名输入框不可见")
        if not password_visible:
            details_parts.append("密码输入框不可见")
        if not button_visible:
            details_parts.append("登录按钮不可见")

        details = "; ".join(details_parts)
        add_result("登录页面渲染", all_visible, screenshot_path, details)

    except Exception as e:
        screenshot_path = take_screenshot(page, "01_login_page_error")
        add_result("登录页面渲染", False, screenshot_path, f"异常: {str(e)}")


def do_login(page: Page, username: str, password: str) -> dict:
    """
    通过API获取token后注入localStorage实现登录
    @param page Playwright页面对象
    @param username 用户名
    @param password 密码
    @return 登录结果字典，包含success和role字段
    """
    try:
        import requests as req_lib
        api_resp = req_lib.post(
            f"{BACKEND_URL}/api/v1/users/login",
            json={"username": username, "password": password},
            timeout=10
        )
        api_data = api_resp.json()

        if not api_data.get("success"):
            print(f"  API登录失败: {api_data.get('error', '未知错误')}")
            return {"success": False, "role": ""}

        token = api_data["data"]["access_token"]
        refresh_token_val = api_data["data"].get("refresh_token", "")
        user_info = api_data["data"]["user"]
        user_role = user_info.get("role", "user")

        page.goto(f"{FRONTEND_URL}/login", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)

        page.evaluate(
            """(args) => {
                localStorage.setItem('token', args.token);
                localStorage.setItem('refresh_token', args.refresh_token);
                localStorage.setItem('userInfo', JSON.stringify(args.userInfo));
            }""",
            {
                "token": token,
                "refresh_token": refresh_token_val,
                "userInfo": {
                    "id": user_info["id"],
                    "username": user_info["username"],
                    "email": user_info["email"],
                    "avatar": user_info.get("avatar_url", ""),
                    "role": user_role
                }
            }
        )

        page.goto(f"{FRONTEND_URL}/dashboard", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        current_url = page.url
        if "/login" not in current_url:
            print(f"  登录成功，当前页面: {current_url}，角色: {user_role}")
            return {"success": True, "role": user_role}
        else:
            print(f"  登录注入后仍在登录页: {current_url}")
            return {"success": False, "role": user_role}

    except Exception as e:
        print(f"  登录异常: {str(e)}")
        return {"success": False, "role": ""}


def test_knowledge_page(page: Page):
    """
    测试2: 知识图谱页面
    登录后访问知识图谱功能，确认数据展示，检查搜索框、分类选择、病害卡片等
    """
    print("\n" + "=" * 60)
    print("测试2: 知识图谱页面")
    print("=" * 60)

    try:
        page.goto(f"{FRONTEND_URL}/knowledge", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(3)

        screenshot_path = take_screenshot(page, "02_knowledge_page")

        page_heading = page.locator("h2")
        heading_visible = page_heading.is_visible()
        heading_text = page_heading.inner_text() if heading_visible else ""

        search_input = page.locator('input[placeholder="搜索病害名称或症状"]')
        search_visible = search_input.is_visible()

        category_select = page.locator(".category-select")
        category_visible = category_select.is_visible() if category_select.count() > 0 else False

        disease_cards = page.locator(".knowledge-container .el-card")
        card_count = disease_cards.count()

        empty_state = page.locator(".knowledge-container .el-empty")
        has_empty = empty_state.is_visible() if empty_state.count() > 0 else False

        loading = page.locator(".el-loading-mask")
        is_loading = loading.is_visible() if loading.count() > 0 else False

        details_parts = []
        if heading_visible:
            details_parts.append(f"标题: {heading_text}")
        else:
            details_parts.append("标题不可见")

        details_parts.append(f"搜索框: {'可见' if search_visible else '不可见'}")
        details_parts.append(f"分类选择: {'可见' if category_visible else '不可见'}")
        details_parts.append(f"病害卡片数量: {card_count}")

        if has_empty:
            details_parts.append("页面显示空状态（无数据）")
        if is_loading:
            details_parts.append("页面仍在加载中")

        passed = heading_visible and search_visible
        add_result("知识图谱页面", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        screenshot_path = take_screenshot(page, "02_knowledge_page_error")
        add_result("知识图谱页面", False, screenshot_path, f"异常: {str(e)}")


def test_admin_overview(page: Page, is_admin: bool = True):
    """
    测试3a: Admin页面 - 系统概览Tab
    检查统计卡片、用户统计、诊断统计等数据显示
    @param page Playwright页面对象
    @param is_admin 当前用户是否为管理员
    """
    print("\n" + "-" * 40)
    print("测试3a: Admin页面 - 系统概览")
    print("-" * 40)

    try:
        page.goto(f"{FRONTEND_URL}/admin", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(3)

        current_url = page.url
        if "/admin" not in current_url:
            screenshot_path = take_screenshot(page, "03a_admin_overview_redirect")
            add_result("Admin-系统概览", False, screenshot_path,
                       f"非管理员用户被重定向到: {current_url}")
            return

        screenshot_path = take_screenshot(page, "03a_admin_overview")

        page_title = page.locator(".page-title")
        title_visible = page_title.is_visible() if page_title.count() > 0 else False

        stat_cards = page.locator(".stat-card")
        stat_count = stat_cards.count()

        overview_tab = page.locator('.el-tabs__item:has-text("系统概览")')
        overview_active = False
        if overview_tab.count() > 0:
            overview_active = "is-active" in (overview_tab.get_attribute("class") or "")

        user_total_stat = page.locator(".el-statistic").first
        has_stats = user_total_stat.is_visible() if user_total_stat.count() > 0 else False

        details_parts = []
        details_parts.append(f"页面标题: {'可见' if title_visible else '不可见'}")
        details_parts.append(f"统计卡片数量: {stat_count}")
        details_parts.append(f"系统概览Tab激活: {overview_active}")
        details_parts.append(f"统计数据可见: {has_stats}")

        passed = title_visible and stat_count >= 3
        add_result("Admin-系统概览", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        screenshot_path = take_screenshot(page, "03a_admin_overview_error")
        add_result("Admin-系统概览", False, screenshot_path, f"异常: {str(e)}")


def test_admin_logs(page: Page):
    """
    测试3b: Admin页面 - 诊断日志Tab
    检查日志表格、统计描述、日志行数等
    """
    print("\n" + "-" * 40)
    print("测试3b: Admin页面 - 诊断日志")
    print("-" * 40)

    try:
        current_url = page.url
        if "/admin" not in current_url:
            screenshot_path = take_screenshot(page, "03b_admin_logs_skip")
            add_result("Admin-诊断日志", False, screenshot_path,
                       "非管理员用户，无法访问Admin页面")
            return

        logs_tab = page.locator('.el-tabs__item:has-text("诊断日志")')
        if logs_tab.count() > 0:
            logs_tab.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)
        else:
            raise Exception("找不到诊断日志Tab")

        screenshot_path = take_screenshot(page, "03b_admin_logs")

        log_table = page.locator("#pane-logs .el-table")
        table_visible = log_table.is_visible() if log_table.count() > 0 else False

        log_stats = page.locator(".log-stats-desc")
        stats_visible = log_stats.is_visible() if log_stats.count() > 0 else False

        table_rows = page.locator("#pane-logs .el-table__body-wrapper .el-table__row")
        row_count = table_rows.count()

        empty_in_logs = page.locator("#pane-logs .el-empty")
        has_empty = empty_in_logs.is_visible() if empty_in_logs.count() > 0 else False

        details_parts = []
        details_parts.append(f"日志表格: {'可见' if table_visible else '不可见'}")
        details_parts.append(f"统计描述: {'可见' if stats_visible else '不可见'}")
        details_parts.append(f"日志行数: {row_count}")
        if has_empty:
            details_parts.append("显示空状态")

        passed = table_visible or stats_visible or has_empty
        add_result("Admin-诊断日志", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        screenshot_path = take_screenshot(page, "03b_admin_logs_error")
        add_result("Admin-诊断日志", False, screenshot_path, f"异常: {str(e)}")


def test_admin_distribution(page: Page):
    """
    测试3c: Admin页面 - 病害分布Tab
    检查ECharts图表容器和Canvas元素渲染
    """
    print("\n" + "-" * 40)
    print("测试3c: Admin页面 - 病害分布")
    print("-" * 40)

    try:
        current_url = page.url
        if "/admin" not in current_url:
            screenshot_path = take_screenshot(page, "03c_admin_distribution_skip")
            add_result("Admin-病害分布", False, screenshot_path,
                       "非管理员用户，无法访问Admin页面")
            return

        dist_tab = page.locator('.el-tabs__item:has-text("病害分布")')
        if dist_tab.count() > 0:
            dist_tab.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)
        else:
            raise Exception("找不到病害分布Tab")

        screenshot_path = take_screenshot(page, "03c_admin_distribution")

        chart_container = page.locator("#pane-distribution > .el-card > .el-card__body > div").first
        chart_visible = chart_container.is_visible() if chart_container.count() > 0 else False

        canvas_elements = page.locator("#pane-distribution canvas")
        canvas_count = canvas_elements.count()

        details_parts = []
        details_parts.append(f"图表容器: {'可见' if chart_visible else '不可见'}")
        details_parts.append(f"Canvas元素数量: {canvas_count}")

        if canvas_count == 0 and chart_visible:
            details_parts.append("注意: 图表容器可见但Canvas未渲染，ECharts可能未加载")

        passed = chart_visible
        add_result("Admin-病害分布", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        screenshot_path = take_screenshot(page, "03c_admin_distribution_error")
        add_result("Admin-病害分布", False, screenshot_path, f"异常: {str(e)}")


def test_admin_monitor(page: Page):
    """
    测试3d: Admin页面 - 系统监控Tab
    检查GPU监控、系统资源监控、缓存管理等卡片
    """
    print("\n" + "-" * 40)
    print("测试3d: Admin页面 - 系统监控")
    print("-" * 40)

    try:
        current_url = page.url
        if "/admin" not in current_url:
            screenshot_path = take_screenshot(page, "03d_admin_monitor_skip")
            add_result("Admin-系统监控", False, screenshot_path,
                       "非管理员用户，无法访问Admin页面")
            return

        monitor_tab = page.locator('.el-tabs__item:has-text("系统监控")')
        if monitor_tab.count() > 0:
            monitor_tab.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)
        else:
            raise Exception("找不到系统监控Tab")

        screenshot_path = take_screenshot(page, "03d_admin_monitor")

        gpu_card = page.locator("#pane-monitor .section-card:has-text('GPU')")
        gpu_visible = gpu_card.is_visible() if gpu_card.count() > 0 else False

        system_card = page.locator("#pane-monitor .section-card:has-text('系统资源')")
        system_visible = system_card.is_visible() if system_card.count() > 0 else False

        cache_card = page.locator("#pane-monitor .section-card:has-text('缓存管理')")
        cache_visible = cache_card.is_visible() if cache_card.count() > 0 else False

        progress_bars = page.locator("#pane-monitor .el-progress")
        progress_count = progress_bars.count()

        details_parts = []
        details_parts.append(f"GPU监控卡片: {'可见' if gpu_visible else '不可见'}")
        details_parts.append(f"系统资源卡片: {'可见' if system_visible else '不可见'}")
        details_parts.append(f"缓存管理卡片: {'可见' if cache_visible else '不可见'}")
        details_parts.append(f"进度条数量: {progress_count}")

        passed = gpu_visible or system_visible
        add_result("Admin-系统监控", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        screenshot_path = take_screenshot(page, "03d_admin_monitor_error")
        add_result("Admin-系统监控", False, screenshot_path, f"异常: {str(e)}")


def test_sessions_page(page: Page):
    """
    测试4: 会话管理页面
    检查用户会话列表功能是否可用，包括会话表格、刷新按钮、终止按钮等
    """
    print("\n" + "=" * 60)
    print("测试4: 会话管理页面")
    print("=" * 60)

    try:
        page.goto(f"{FRONTEND_URL}/sessions", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)

        screenshot_path = take_screenshot(page, "04_sessions_page")

        session_heading = page.locator("span:has-text('会话管理')")
        heading_visible = session_heading.is_visible() if session_heading.count() > 0 else False

        refresh_button = page.locator('button:has-text("刷新列表")')
        refresh_visible = refresh_button.is_visible() if refresh_button.count() > 0 else False

        terminate_all_button = page.locator('button:has-text("终止所有其他会话")')
        terminate_visible = terminate_all_button.is_visible() if terminate_all_button.count() > 0 else False

        session_table = page.locator(".sessions-container .el-table")
        table_visible = session_table.is_visible() if session_table.count() > 0 else False

        table_rows = page.locator(".sessions-container .el-table__body-wrapper .el-table__row")
        row_count = table_rows.count()

        empty_state = page.locator(".sessions-container .el-empty")
        has_empty = empty_state.is_visible() if empty_state.count() > 0 else False

        loading_mask = page.locator(".el-loading-mask")
        is_loading = loading_mask.is_visible() if loading_mask.count() > 0 else False

        details_parts = []
        details_parts.append(f"会话管理标题: {'可见' if heading_visible else '不可见'}")
        details_parts.append(f"刷新按钮: {'可见' if refresh_visible else '不可见'}")
        details_parts.append(f"终止所有按钮: {'可见' if terminate_visible else '不可见'}")
        details_parts.append(f"会话表格: {'可见' if table_visible else '不可见'}")
        details_parts.append(f"会话行数: {row_count}")

        if has_empty:
            details_parts.append("显示空状态（无活跃会话）")
        if is_loading:
            details_parts.append("页面仍在加载中")

        passed = heading_visible and (table_visible or has_empty)
        add_result("会话管理页面", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        try:
            screenshot_path = take_screenshot(page, "04_sessions_page_error")
        except Exception:
            screenshot_path = "N/A"
        add_result("会话管理页面", False, screenshot_path, f"异常: {str(e)}")


def test_records_page(page: Page):
    """
    测试5: 诊断记录页面
    检查记录列表和导出报告功能，包括表格、搜索框、分页、导出按钮等
    """
    print("\n" + "=" * 60)
    print("测试5: 诊断记录页面")
    print("=" * 60)

    try:
        page.goto(f"{FRONTEND_URL}/records", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(3)

        screenshot_path = take_screenshot(page, "05_records_page")

        records_heading = page.locator(".records-container .card-header span:has-text('诊断记录')").first
        heading_visible = records_heading.is_visible() if records_heading.count() > 0 else False

        search_input = page.locator('.records-container input[placeholder="搜索记录"]')
        search_visible = search_input.is_visible() if search_input.count() > 0 else False

        records_table = page.locator(".records-container .el-table")
        table_visible = records_table.is_visible() if records_table.count() > 0 else False

        table_rows = page.locator(".records-container .el-table__body-wrapper .el-table__row")
        row_count = table_rows.count()

        empty_state = page.locator(".records-container .el-empty")
        has_empty = empty_state.is_visible() if empty_state.count() > 0 else False

        pagination = page.locator(".records-container .el-pagination")
        pagination_visible = pagination.is_visible() if pagination.count() > 0 else False

        export_buttons = page.locator('.records-container button:has-text("导出报告")')
        export_count = export_buttons.count()

        view_detail_buttons = page.locator('.records-container button:has-text("查看详情")')
        view_detail_count = view_detail_buttons.count()

        details_parts = []
        details_parts.append(f"诊断记录标题: {'可见' if heading_visible else '不可见'}")
        details_parts.append(f"搜索框: {'可见' if search_visible else '不可见'}")
        details_parts.append(f"记录表格: {'可见' if table_visible else '不可见'}")
        details_parts.append(f"记录行数: {row_count}")
        details_parts.append(f"分页组件: {'可见' if pagination_visible else '不可见'}")
        details_parts.append(f"导出报告按钮数量: {export_count}")
        details_parts.append(f"查看详情按钮数量: {view_detail_count}")

        if has_empty:
            details_parts.append("显示空状态（暂无诊断记录）")

        if row_count > 0 and export_count > 0:
            details_parts.append("导出报告功能可用（有记录且有导出按钮）")
        elif row_count == 0:
            details_parts.append("无记录数据，导出报告功能无法验证")

        passed = heading_visible and (table_visible or has_empty)
        add_result("诊断记录页面", passed, screenshot_path, "; ".join(details_parts))

    except Exception as e:
        try:
            screenshot_path = take_screenshot(page, "05_records_page_error")
        except Exception:
            screenshot_path = "N/A"
        add_result("诊断记录页面", False, screenshot_path, f"异常: {str(e)}")


def check_backend_health() -> bool:
    """
    检查后端服务是否可用
    @return 后端是否健康
    """
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{BACKEND_URL}/api/v1/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def check_frontend_health() -> bool:
    """
    检查前端服务是否可用
    @return 前端是否健康
    """
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(FRONTEND_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    """
    主测试入口
    依次执行所有前端功能测试，输出汇总报告
    """
    print("=" * 60)
    print("WheatAgent 前端功能测试")
    print(f"前端地址: {FRONTEND_URL}")
    print(f"后端地址: {BACKEND_URL}")
    print(f"截图目录: {SCREENSHOT_DIR}")
    print("=" * 60)

    print("\n预检: 检查服务可用性...")
    frontend_ok = check_frontend_health()
    backend_ok = check_backend_health()
    print(f"  前端服务: {'✅ 可用' if frontend_ok else '❌ 不可用'}")
    print(f"  后端服务: {'✅ 可用' if backend_ok else '❌ 不可用'}")

    if not frontend_ok:
        print("\n❌ 前端服务不可用，测试终止！")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # 测试1: 登录页面
        test_login_page(page)

        # 通过API注入token登录
        print("\n正在登录测试账号...")
        login_result = do_login(page, TEST_USERNAME, TEST_PASSWORD)
        login_ok = login_result["success"]
        user_role = login_result["role"]
        if not login_ok:
            print("⚠️ 登录失败，尝试继续测试（部分页面可能被重定向到登录页）")
            take_screenshot(page, "login_failed")

        # 测试2: 知识图谱页面
        test_knowledge_page(page)

        # 测试3: Admin页面（需要管理员权限）
        if user_role == "admin":
            test_admin_overview(page, is_admin=True)
            test_admin_logs(page)
            test_admin_distribution(page)
            test_admin_monitor(page)
        else:
            print(f"\n⚠️ 当前用户角色为 '{user_role}'，非管理员，尝试用管理员账号登录Admin页面...")
            admin_login_result = do_login(page, "v21test_admin", "Test1234!")
            if admin_login_result["success"] and admin_login_result["role"] == "admin":
                test_admin_overview(page, is_admin=True)
                test_admin_logs(page)
                test_admin_distribution(page)
                test_admin_monitor(page)
                do_login(page, TEST_USERNAME, TEST_PASSWORD)
            else:
                print("  管理员账号登录失败，跳过Admin页面测试")
                add_result("Admin-系统概览", False, "", "无法以管理员身份登录，测试跳过")
                add_result("Admin-诊断日志", False, "", "无法以管理员身份登录，测试跳过")
                add_result("Admin-病害分布", False, "", "无法以管理员身份登录，测试跳过")
                add_result("Admin-系统监控", False, "", "无法以管理员身份登录，测试跳过")

        # 测试4: 会话管理页面
        test_sessions_page(page)

        # 测试5: 诊断记录页面
        test_records_page(page)

        browser.close()

    # 输出汇总报告
    print("\n" + "=" * 60)
    print("测试汇总报告")
    print("=" * 60)

    pass_count = sum(1 for r in test_results if r["status"] == "PASS")
    fail_count = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)

    print(f"\n总测试数: {total}")
    print(f"通过: {pass_count}")
    print(f"失败: {fail_count}")
    print(f"通过率: {pass_count / total * 100:.1f}%" if total > 0 else "N/A")

    print("\n详细结果:")
    print("-" * 60)
    for r in test_results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"{icon} [{r['status']}] {r['test_name']}")
        print(f"   截图: {r['screenshot']}")
        if r['details']:
            print(f"   详情: {r['details']}")
        print()

    # 保存JSON格式报告
    report_path = os.path.join(SCREENSHOT_DIR, "test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "frontend_url": FRONTEND_URL,
            "backend_url": BACKEND_URL,
            "total": total,
            "passed": pass_count,
            "failed": fail_count,
            "results": test_results
        }, f, ensure_ascii=False, indent=2)
    print(f"测试报告已保存: {report_path}")


if __name__ == "__main__":
    main()
