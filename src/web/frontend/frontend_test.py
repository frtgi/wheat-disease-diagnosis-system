"""
WheatAgent 前端功能验证测试脚本
使用 Playwright 对各页面进行自动化测试和截图
"""
import os
import sys
import io
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, expect

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:5173"
TEST_RESULTS = []


def take_screenshot(page, name):
    """截取页面截图并保存"""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    return path


def add_result(test_name, passed, description, screenshot_path=""):
    """记录测试结果"""
    TEST_RESULTS.append({
        "test_name": test_name,
        "passed": passed,
        "description": description,
        "screenshot": screenshot_path,
        "timestamp": datetime.now().isoformat()
    })


def test_login(page):
    """测试登录功能"""
    print("\n=== 1. 登录测试 ===")
    console_errors = []
    page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)
    page.on("response", lambda resp: print(f"  [HTTP] {resp.status} {resp.url}") if "login" in resp.url else None)
    try:
        page.goto(f"{BASE_URL}/login", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(1)

        screenshot_path = take_screenshot(page, "01_login_page")
        print(f"  登录页面截图: {screenshot_path}")

        username_input = page.locator('input[placeholder="请输入用户名"]')
        password_input = page.locator('input[placeholder="请输入密码"]')

        if username_input.count() == 0 or password_input.count() == 0:
            add_result("登录页面渲染", False, "未找到用户名或密码输入框", screenshot_path)
            return False

        username_input.fill("v21test_admin")
        password_input.fill("Test1234!")

        login_button = page.locator('button:has-text("登录")')
        login_button.click()

        try:
            page.wait_for_url("**/dashboard**", timeout=10000)
        except Exception:
            pass

        time.sleep(3)

        current_url = page.url
        screenshot_path = take_screenshot(page, "02_after_login")

        if "/login" not in current_url:
            add_result("登录功能", True, f"登录成功，跳转到: {current_url}", screenshot_path)
            print(f"  OK 登录成功，当前URL: {current_url}")
            return True
        else:
            error_msgs = []
            error_el = page.locator('.el-message--error')
            if error_el.count() > 0:
                error_msgs.append(error_el.first.text_content())
            
            page_text = page.locator('body').text_content() or ""
            
            details = f"登录失败，仍在登录页。"
            if error_msgs:
                details += f" 页面错误提示: {'; '.join(error_msgs)}"
            if console_errors:
                details += f" 控制台错误: {'; '.join(console_errors[-5:])}"
            
            add_result("登录功能", False, details, screenshot_path)
            print(f"  FAIL 登录失败: {details}")
            return False

    except Exception as e:
        screenshot_path = take_screenshot(page, "02_login_error") if page else ""
        add_result("登录功能", False, f"登录测试异常: {str(e)}", screenshot_path)
        print(f"  FAIL 登录测试异常: {e}")
        return False


def test_dashboard(page):
    """测试首页功能"""
    print("\n=== 2. 首页功能测试 ===")
    try:
        page.goto(f"{BASE_URL}/dashboard", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        screenshot_path = take_screenshot(page, "03_dashboard")
        print(f"  首页截图: {screenshot_path}")

        welcome_text = page.locator('h1:has-text("欢迎使用")')
        has_welcome = welcome_text.count() > 0

        stat_cards = page.locator('.stat-card')
        has_stats = stat_cards.count() > 0

        nav_menu = page.locator('.header-menu')
        has_nav = nav_menu.count() > 0

        logo_text = page.locator('.logo')
        has_logo = logo_text.count() > 0

        details = []
        if has_welcome:
            details.append("欢迎卡片显示正常")
        else:
            details.append("欢迎卡片未找到")

        if has_stats:
            details.append(f"统计卡片数量: {stat_cards.count()}")
        else:
            details.append("统计卡片未找到")

        if has_nav:
            details.append("导航栏显示正常")
        else:
            details.append("导航栏未找到")

        if has_logo:
            details.append(f"Logo文本: {logo_text.first.text_content()}")
        else:
            details.append("Logo未找到")

        passed = has_welcome and has_nav
        add_result("首页渲染", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 首页渲染: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        add_result("导航栏显示", has_nav, "导航栏" + ("显示正常" if has_nav else "未找到"), screenshot_path)
        print(f"  {'✓' if has_nav else '✗'} 导航栏: {'通过' if has_nav else '失败'}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "03_dashboard_error") if page else ""
        add_result("首页功能", False, f"首页测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 首页测试异常: {e}")
        return False


def test_records(page):
    """测试诊断记录页面"""
    print("\n=== 3. 诊断记录页面测试 ===")
    try:
        page.goto(f"{BASE_URL}/records", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        screenshot_path = take_screenshot(page, "04_records")
        print(f"  记录页面截图: {screenshot_path}")

        table = page.locator('.el-table')
        has_table = table.count() > 0

        table_rows = page.locator('.el-table__body-wrapper .el-table__row')
        row_count = table_rows.count()

        empty_block = page.locator('.el-table__empty-block')
        has_empty = empty_block.count() > 0

        details = []
        if has_table:
            details.append("表格组件已渲染")
        else:
            details.append("表格组件未找到")

        if row_count > 0:
            details.append(f"记录数量: {row_count}")
        elif has_empty:
            details.append("表格为空（无数据）")
        else:
            details.append("未检测到表格行或空状态")

        passed = has_table
        add_result("诊断记录页面", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 诊断记录页面: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "04_records_error") if page else ""
        add_result("诊断记录页面", False, f"记录页面测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 记录页面测试异常: {e}")
        return False


def test_admin_overview(page):
    """测试管理后台-概览"""
    print("\n=== 4a. 管理后台-概览测试 ===")
    try:
        page.goto(f"{BASE_URL}/admin?tab=overview", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        screenshot_path = take_screenshot(page, "05_admin_overview")
        print(f"  概览页面截图: {screenshot_path}")

        stat_items = page.locator('.el-statistic, .stat-card, .overview-card, [class*="stat"], [class*="overview"]')
        has_stats = stat_items.count() > 0

        page_content = page.locator('.layout-main').first.text_content() if page.locator('.layout-main').count() > 0 else ""

        details = []
        if has_stats:
            details.append(f"统计项数量: {stat_items.count()}")
        else:
            details.append("统计项未找到")

        numbers_in_content = [w for w in page_content.split() if w.replace(',', '').replace('.', '').isdigit()] if page_content else []
        if numbers_in_content:
            details.append(f"检测到数值数据: {len(numbers_in_content)}个")

        passed = has_stats or len(numbers_in_content) > 0
        add_result("管理后台-概览", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 概览统计: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "05_admin_overview_error") if page else ""
        add_result("管理后台-概览", False, f"概览测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 概览测试异常: {e}")
        return False


def test_admin_logs(page):
    """测试管理后台-日志统计"""
    print("\n=== 4b. 管理后台-日志统计测试 ===")
    try:
        page.goto(f"{BASE_URL}/admin?tab=logs", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        screenshot_path = take_screenshot(page, "06_admin_logs")
        print(f"  日志统计截图: {screenshot_path}")

        log_table = page.locator('.el-table, [class*="log"], [class*="table"]')
        has_log_data = log_table.count() > 0

        page_content = page.locator('.layout-main').first.text_content() if page.locator('.layout-main').count() > 0 else ""

        details = []
        if has_log_data:
            details.append("日志数据组件已渲染")
        else:
            details.append("日志数据组件未找到")

        log_keywords = ["日志", "log", "操作", "记录"]
        found_keywords = [kw for kw in log_keywords if kw.lower() in page_content.lower()]
        if found_keywords:
            details.append(f"检测到关键词: {', '.join(found_keywords)}")

        passed = has_log_data or len(found_keywords) > 0
        add_result("管理后台-日志统计", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 日志统计: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "06_admin_logs_error") if page else ""
        add_result("管理后台-日志统计", False, f"日志测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 日志测试异常: {e}")
        return False


def test_admin_distribution(page):
    """测试管理后台-病害分布图表"""
    print("\n=== 4c. 管理后台-病害分布测试 ===")
    try:
        page.goto(f"{BASE_URL}/admin?tab=distribution", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(3)

        screenshot_path = take_screenshot(page, "07_admin_distribution")
        print(f"  病害分布截图: {screenshot_path}")

        chart_canvas = page.locator('canvas, [class*="chart"], [class*="echarts"], [class*="distribution"]')
        has_chart = chart_canvas.count() > 0

        page_content = page.locator('.layout-main').first.text_content() if page.locator('.layout-main').count() > 0 else ""

        details = []
        if has_chart:
            details.append(f"图表组件数量: {chart_canvas.count()}")
        else:
            details.append("图表组件未找到")

        dist_keywords = ["分布", "病害", "disease", "chart"]
        found_keywords = [kw for kw in dist_keywords if kw.lower() in page_content.lower()]
        if found_keywords:
            details.append(f"检测到关键词: {', '.join(found_keywords)}")

        passed = has_chart or len(found_keywords) > 0
        add_result("管理后台-病害分布", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 病害分布图表: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "07_admin_distribution_error") if page else ""
        add_result("管理后台-病害分布", False, f"分布测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 分布测试异常: {e}")
        return False


def test_admin_monitor(page):
    """测试管理后台-系统监控"""
    print("\n=== 4d. 管理后台-系统监控测试 ===")
    try:
        page.goto(f"{BASE_URL}/admin?tab=monitor", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        screenshot_path = take_screenshot(page, "08_admin_monitor")
        print(f"  系统监控截图: {screenshot_path}")

        monitor_elements = page.locator('[class*="monitor"], [class*="cpu"], [class*="memory"], [class*="gpu"], [class*="system"], .el-progress, canvas')
        has_monitor = monitor_elements.count() > 0

        page_content = page.locator('.layout-main').first.text_content() if page.locator('.layout-main').count() > 0 else ""

        details = []
        if has_monitor:
            details.append(f"监控组件数量: {monitor_elements.count()}")
        else:
            details.append("监控组件未找到")

        monitor_keywords = ["CPU", "内存", "GPU", "监控", "monitor", "使用率", "系统"]
        found_keywords = [kw for kw in monitor_keywords if kw.lower() in page_content.lower()]
        if found_keywords:
            details.append(f"检测到关键词: {', '.join(found_keywords)}")

        passed = has_monitor or len(found_keywords) > 0
        add_result("管理后台-系统监控", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 系统监控: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "08_admin_monitor_error") if page else ""
        add_result("管理后台-系统监控", False, f"监控测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 监控测试异常: {e}")
        return False


def test_knowledge(page):
    """测试知识库页面"""
    print("\n=== 5. 知识库页面测试 ===")
    try:
        page.goto(f"{BASE_URL}/knowledge", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

        screenshot_path = take_screenshot(page, "09_knowledge")
        print(f"  知识库页面截图: {screenshot_path}")

        page_content = page.locator('.layout-main').first.text_content() if page.locator('.layout-main').count() > 0 else ""

        knowledge_elements = page.locator('[class*="knowledge"], [class*="card"], .el-card, [class*="disease"]')
        has_knowledge = knowledge_elements.count() > 0

        details = []
        if has_knowledge:
            details.append(f"知识库组件数量: {knowledge_elements.count()}")
        else:
            details.append("知识库组件未找到")

        knowledge_keywords = ["知识", "病害", "防治", "小麦", "knowledge"]
        found_keywords = [kw for kw in knowledge_keywords if kw.lower() in page_content.lower()]
        if found_keywords:
            details.append(f"检测到关键词: {', '.join(found_keywords)}")

        passed = has_knowledge or len(found_keywords) > 0
        add_result("知识库页面", passed, "; ".join(details), screenshot_path)
        print(f"  {'✓' if passed else '✗'} 知识库页面: {'通过' if passed else '失败'}")
        print(f"    详情: {'; '.join(details)}")

        return passed

    except Exception as e:
        screenshot_path = take_screenshot(page, "09_knowledge_error") if page else ""
        add_result("知识库页面", False, f"知识库测试异常: {str(e)}", screenshot_path)
        print(f"  ✗ 知识库测试异常: {e}")
        return False


def generate_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("           WheatAgent 前端功能验证测试报告")
    print("=" * 60)

    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["passed"])
    failed = total - passed

    print(f"\n总测试项: {total}  |  通过: {passed}  |  失败: {failed}")
    print("-" * 60)

    for i, result in enumerate(TEST_RESULTS, 1):
        status = "✓ 通过" if result["passed"] else "✗ 失败"
        print(f"\n{i}. [{status}] {result['test_name']}")
        print(f"   描述: {result['description']}")
        if result['screenshot']:
            print(f"   截图: {result['screenshot']}")

    print("\n" + "=" * 60)

    report_path = os.path.join(os.path.dirname(__file__), "frontend_test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "report_time": datetime.now().isoformat(),
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": TEST_RESULTS
        }, f, ensure_ascii=False, indent=2)

    print(f"测试报告已保存至: {report_path}")
    print(f"截图目录: {SCREENSHOT_DIR}")

    return passed, failed


def main():
    """主测试流程"""
    print("=" * 60)
    print("    WheatAgent 前端功能验证 - Playwright 自动化测试")
    print(f"    测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    前端地址: {BASE_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = context.new_page()

        # 1. 登录测试
        login_ok = test_login(page)
        if not login_ok:
            print("\n⚠ 登录失败，后续测试可能无法正常进行（需要认证）")

        # 2. 首页功能测试
        test_dashboard(page)

        # 3. 诊断记录页面测试
        test_records(page)

        # 4. 管理后台测试
        test_admin_overview(page)
        test_admin_logs(page)
        test_admin_distribution(page)
        test_admin_monitor(page)

        # 5. 知识库页面测试
        test_knowledge(page)

        browser.close()

    # 生成报告
    generate_report()


if __name__ == "__main__":
    main()
