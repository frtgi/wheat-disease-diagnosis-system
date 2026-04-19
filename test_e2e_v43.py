"""
WheatAgent 端到端功能测试脚本 (v43)
使用 Playwright 测试登录、仪表盘、诊断、知识库、管理后台、用户中心和退出登录流程
"""
import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots_v43")

TEST_USERNAME = "v21test_admin"
TEST_PASSWORD = "Test1234!"

ADMIN_TABS = [
    {"label": "系统概览", "name": "overview", "desc": "系统概览统计卡片"},
    {"label": "系统监控", "name": "monitor", "desc": "系统监控信息"},
    {"label": "诊断日志", "name": "logs", "desc": "诊断日志表格"},
    {"label": "病害分布", "name": "distribution", "desc": "病害分布图表"},
    {"label": "AI 模型管理", "name": "models", "desc": "AI模型管理面板"},
]


def ensure_screenshot_dir():
    """确保截图目录存在"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def do_login(page):
    """
    执行登录操作
    导航到登录页，填写用户名和密码，点击登录按钮，等待跳转到仪表盘
    """
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")

    username_input = page.locator('input[placeholder="请输入用户名"]')
    password_input = page.locator('input[placeholder="请输入密码"]')

    username_input.fill(TEST_USERNAME)
    password_input.fill(TEST_PASSWORD)

    login_btn = page.locator('button:has-text("登录")')
    login_btn.click()

    page.wait_for_url("**/dashboard**", timeout=15000)
    page.wait_for_load_state("networkidle")
    time.sleep(1)


def test_login_flow(page):
    """
    测试1: 登录流程
    验证登录页面元素可见、登录后跳转到仪表盘、仪表盘内容可见
    """
    result = {"name": "Test 1: Login Flow", "status": "FAIL", "errors": [], "screenshot": ""}
    try:
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")

        username_visible = page.locator('input[placeholder="请输入用户名"]').is_visible()
        password_visible = page.locator('input[placeholder="请输入密码"]').is_visible()
        login_btn_visible = page.locator('button:has-text("登录")').is_visible()

        if not username_visible:
            result["errors"].append("用户名输入框不可见")
        if not password_visible:
            result["errors"].append("密码输入框不可见")
        if not login_btn_visible:
            result["errors"].append("登录按钮不可见")

        page.locator('input[placeholder="请输入用户名"]').fill(TEST_USERNAME)
        page.locator('input[placeholder="请输入密码"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()

        page.wait_for_url("**/dashboard**", timeout=15000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        current_url = page.url
        if "/dashboard" not in current_url:
            result["errors"].append(f"登录后未跳转到 /dashboard，当前URL: {current_url}")

        dashboard_visible = page.locator(".dashboard-container").is_visible(timeout=5000)
        if not dashboard_visible:
            result["errors"].append("仪表盘容器不可见")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "01_login_dashboard.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def test_dashboard_page(page):
    """
    测试2: 仪表盘页面
    验证统计卡片可见（今日诊断次数、总诊断次数、平均准确率、活跃用户数）
    """
    result = {"name": "Test 2: Dashboard Page", "status": "FAIL", "errors": [], "screenshot": ""}
    try:
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        stat_titles = ["今日诊断次数", "总诊断次数", "平均准确率", "活跃用户数"]
        for title in stat_titles:
            locator = page.locator(f".stat-card:has-text('{title}')")
            if not locator.is_visible(timeout=5000):
                result["errors"].append(f"统计卡片 '{title}' 不可见")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "02_dashboard.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def test_diagnosis_page(page):
    """
    测试3: 诊断页面
    验证图片上传区域和诊断表单元素可见
    """
    result = {"name": "Test 3: Diagnosis Page", "status": "FAIL", "errors": [], "screenshot": ""}
    try:
        page.goto(f"{BASE_URL}/diagnosis")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        page_title = page.locator(".page-title")
        if not page_title.is_visible(timeout=5000):
            result["errors"].append("诊断页面标题不可见")

        tabs = page.locator(".diagnosis-tabs")
        if not tabs.is_visible(timeout=5000):
            result["errors"].append("诊断标签页不可见")

        upload_area = page.locator(".image-uploader").first
        if not upload_area.is_visible(timeout=5000):
            result["errors"].append("图片上传区域不可见")

        single_tab = page.locator('.el-tabs__item:has-text("单图诊断")')
        if not single_tab.is_visible(timeout=5000):
            result["errors"].append("'单图诊断' 标签不可见")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "03_diagnosis.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def test_knowledge_page(page):
    """
    测试4: 知识库页面
    验证知识库搜索栏和病害卡片可见
    """
    result = {"name": "Test 4: Knowledge Page", "status": "FAIL", "errors": [], "screenshot": ""}
    try:
        page.goto(f"{BASE_URL}/knowledge")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        search_input = page.locator('input[placeholder="搜索病害名称或症状"]')
        if not search_input.is_visible(timeout=5000):
            result["errors"].append("知识库搜索输入框不可见")

        knowledge_title = page.locator("h2:has-text('病害知识库')")
        if not knowledge_title.is_visible(timeout=5000):
            result["errors"].append("知识库标题不可见")

        disease_cards = page.locator(".disease-card, [class*='DiseaseCard'], [class*='disease-card']")
        card_count = disease_cards.count()
        if card_count == 0:
            empty_state = page.locator(".el-empty")
            if not empty_state.is_visible(timeout=3000):
                result["errors"].append("知识库既无病害卡片也无空状态提示")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "04_knowledge.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def test_admin_tabs(page):
    """
    测试5: 管理后台页面 - 全部5个标签页
    逐一点击每个标签页，等待内容加载，验证内容区域不为空，截图
    """
    result = {"name": "Test 5: Admin Page - All 5 Tabs", "status": "FAIL", "errors": [], "screenshot": "", "tab_results": []}
    try:
        page.goto(f"{BASE_URL}/admin")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        admin_tabs = page.locator(".admin-tabs")
        if not admin_tabs.is_visible(timeout=10000):
            result["errors"].append("管理后台标签页容器不可见")
            return result

        all_tabs_pass = True
        for tab_info in ADMIN_TABS:
            tab_result = {"tab": tab_info["label"], "status": "FAIL", "errors": []}
            try:
                tab_selector = f'.el-tabs__item:has-text("{tab_info["label"]}")'
                tab_element = page.locator(tab_selector)

                if not tab_element.is_visible(timeout=5000):
                    tab_result["errors"].append(f"标签页 '{tab_info['label']}' 不可见")
                    all_tabs_pass = False
                    result["tab_results"].append(tab_result)
                    continue

                tab_element.click()
                time.sleep(2)
                page.wait_for_load_state("networkidle", timeout=8000)

                tab_pane = page.locator(f'[id="pane-{tab_info["name"]}"]')
                try:
                    if tab_pane.is_visible(timeout=3000):
                        content_text = tab_pane.inner_text(timeout=3000)
                    else:
                        content_text = page.locator(".el-tabs__content").inner_text(timeout=3000)
                except Exception:
                    content_text = page.locator(".el-tabs__content").inner_text(timeout=3000)

                content_text = content_text.strip()
                if not content_text or len(content_text) < 2:
                    tab_result["errors"].append(f"标签页 '{tab_info['label']}' 内容为空")
                    all_tabs_pass = False
                else:
                    tab_result["status"] = "PASS"

                screenshot_path = os.path.join(SCREENSHOT_DIR, f"05_admin_tab_{tab_info['name']}.png")
                page.screenshot(path=screenshot_path, full_page=True)

            except Exception as e:
                tab_result["errors"].append(str(e))
                all_tabs_pass = False

            result["tab_results"].append(tab_result)

        screenshot_path = os.path.join(SCREENSHOT_DIR, "05_admin_overview.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if all_tabs_pass and not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def test_user_center(page):
    """
    测试6: 用户中心页面
    验证用户信息表单可见
    """
    result = {"name": "Test 6: User Center", "status": "FAIL", "errors": [], "screenshot": ""}
    try:
        page.goto(f"{BASE_URL}/user")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        profile_card = page.locator(".profile-card")
        if not profile_card.is_visible(timeout=5000):
            result["errors"].append("用户资料卡片不可见")

        info_card = page.locator(".info-card")
        if not info_card.is_visible(timeout=5000):
            result["errors"].append("个人信息卡片不可见")

        descriptions = page.locator(".el-descriptions")
        if not descriptions.is_visible(timeout=5000):
            result["errors"].append("用户信息描述列表不可见")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "06_user_center.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def test_logout(page):
    """
    测试7: 退出登录
    点击退出登录按钮，验证跳转到登录页
    """
    result = {"name": "Test 7: Logout", "status": "FAIL", "errors": [], "screenshot": ""}
    try:
        page.goto(f"{BASE_URL}/user")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        logout_btn = page.locator('button.logout-btn:has-text("退出登录")')
        if not logout_btn.is_visible(timeout=5000):
            result["errors"].append("退出登录按钮不可见，尝试通过下拉菜单退出")
            user_dropdown = page.locator(".user-info, .el-dropdown")
            if user_dropdown.is_visible(timeout=3000):
                user_dropdown.click()
                time.sleep(0.5)
                dropdown_logout = page.locator('.el-dropdown-menu__item:has-text("退出登录")')
                if dropdown_logout.is_visible(timeout=3000):
                    dropdown_logout.click()
                    time.sleep(0.5)
                    confirm_btn = page.locator('.el-message-box__btns button:has-text("确定")')
                    if confirm_btn.is_visible(timeout=3000):
                        confirm_btn.click()
                else:
                    result["errors"].append("下拉菜单中退出登录选项不可见")
                    return result
            else:
                result["errors"].append("用户下拉菜单也不可见，无法退出登录")
                return result
        else:
            logout_btn.click()
            time.sleep(0.5)
            confirm_btn = page.locator('.el-message-box__btns button:has-text("确定")')
            if confirm_btn.is_visible(timeout=3000):
                confirm_btn.click()

        page.wait_for_url("**/login**", timeout=15000)
        time.sleep(1)

        current_url = page.url
        if "/login" not in current_url:
            result["errors"].append(f"退出登录后未跳转到 /login，当前URL: {current_url}")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "07_logout.png")
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if not result["errors"]:
            result["status"] = "PASS"
    except Exception as e:
        result["errors"].append(str(e))
    return result


def run_all_tests():
    """
    运行所有端到端测试
    按顺序执行7个测试场景，汇总并打印结果
    """
    ensure_screenshot_dir()

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("=" * 70)
        print("  WheatAgent E2E 功能测试 (v43)")
        print("=" * 70)

        # Test 1: Login Flow
        print("\n[执行] Test 1: Login Flow...")
        r1 = test_login_flow(page)
        results.append(r1)
        print(f"  结果: {r1['status']}")
        if r1["errors"]:
            for err in r1["errors"]:
                print(f"  错误: {err}")

        if r1["status"] == "FAIL":
            print("\n登录失败，无法继续后续测试。尝试重新登录...")
            try:
                do_login(page)
                print("  重新登录成功，继续测试")
            except Exception as e:
                print(f"  重新登录也失败: {e}")
                browser.close()
                print_results(results)
                return results

        # Test 2: Dashboard Page
        print("\n[执行] Test 2: Dashboard Page...")
        r2 = test_dashboard_page(page)
        results.append(r2)
        print(f"  结果: {r2['status']}")
        if r2["errors"]:
            for err in r2["errors"]:
                print(f"  错误: {err}")

        # Test 3: Diagnosis Page
        print("\n[执行] Test 3: Diagnosis Page...")
        r3 = test_diagnosis_page(page)
        results.append(r3)
        print(f"  结果: {r3['status']}")
        if r3["errors"]:
            for err in r3["errors"]:
                print(f"  错误: {err}")

        # Test 4: Knowledge Page
        print("\n[执行] Test 4: Knowledge Page...")
        r4 = test_knowledge_page(page)
        results.append(r4)
        print(f"  结果: {r4['status']}")
        if r4["errors"]:
            for err in r4["errors"]:
                print(f"  错误: {err}")

        # Test 5: Admin Page - All 5 Tabs
        print("\n[执行] Test 5: Admin Page - All 5 Tabs...")
        r5 = test_admin_tabs(page)
        results.append(r5)
        print(f"  结果: {r5['status']}")
        if r5["errors"]:
            for err in r5["errors"]:
                print(f"  错误: {err}")
        if "tab_results" in r5:
            for tr in r5["tab_results"]:
                print(f"    标签页 '{tr['tab']}': {tr['status']}")
                if tr["errors"]:
                    for err in tr["errors"]:
                        print(f"      错误: {err}")

        # Test 6: User Center
        print("\n[执行] Test 6: User Center...")
        r6 = test_user_center(page)
        results.append(r6)
        print(f"  结果: {r6['status']}")
        if r6["errors"]:
            for err in r6["errors"]:
                print(f"  错误: {err}")

        # Test 7: Logout
        print("\n[执行] Test 7: Logout...")
        r7 = test_logout(page)
        results.append(r7)
        print(f"  结果: {r7['status']}")
        if r7["errors"]:
            for err in r7["errors"]:
                print(f"  错误: {err}")

        browser.close()

    print_results(results)
    return results


def print_results(results):
    """
    打印测试结果汇总
    统计通过/失败数量，输出每个测试的状态和错误信息
    """
    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)

    pass_count = 0
    fail_count = 0

    for r in results:
        status_icon = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"  [{status_icon}] {r['name']}")
        if r["status"] == "PASS":
            pass_count += 1
        else:
            fail_count += 1
            for err in r.get("errors", []):
                print(f"       错误: {err}")
        if "tab_results" in r:
            for tr in r["tab_results"]:
                tab_icon = "PASS" if tr["status"] == "PASS" else "FAIL"
                print(f"    [{tab_icon}] 标签页: {tr['tab']}")
                if tr["errors"]:
                    for err in tr["errors"]:
                        print(f"         错误: {err}")

    print(f"\n  总计: {len(results)} 个测试, {pass_count} 通过, {fail_count} 失败")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
