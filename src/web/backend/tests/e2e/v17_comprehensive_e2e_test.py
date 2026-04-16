"""
WheatAgent 综合端到端测试脚本 v17

自包含测试脚本，仅依赖 requests 库，无需 pytest。
覆盖 7 大测试模块：认证流程、诊断流程、知识图谱、健康检查、
统计报表、边界条件、事件循环非阻塞验证。

运行方式:
    conda activate wheatagent-py310
    python v17_comprehensive_e2e_test.py
"""
import json
import sys
import time
import threading
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import requests

BASE_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "test_admin"
TEST_PASSWORD = "test123"
IMAGE_PATH = r"d:\Project\wheatagent\src\web\backend\tests\test_data\images\wheat_rust.png"
SSE_TIMEOUT = 600


@dataclass
class TestResult:
    """测试结果记录类，跟踪单个测试的名称、通过状态、执行时间和错误信息"""
    name: str
    passed: bool
    duration_ms: float
    error_message: str = ""

    def __str__(self):
        """格式化输出测试结果"""
        status = "PASS" if self.passed else "FAIL"
        msg = f"  [{status}] {self.name} ({self.duration_ms:.0f}ms)"
        if not self.passed and self.error_message:
            msg += f"\n        Error: {self.error_message}"
        return msg


class TestRunner:
    """测试运行器，管理所有测试类的执行和结果汇总"""

    def __init__(self):
        """初始化测试运行器，创建结果列表和认证令牌存储"""
        self.results: List[TestResult] = []
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()

    def record(self, name: str, passed: bool, duration_ms: float, error_message: str = ""):
        """记录一条测试结果并实时打印"""
        result = TestResult(name=name, passed=passed, duration_ms=duration_ms, error_message=error_message)
        self.results.append(result)
        print(result)

    def auth_headers(self) -> Dict[str, str]:
        """构造带 Bearer Token 的请求头"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    def ensure_auth(self):
        """确保有有效的认证令牌，如无则重新登录"""
        if self.access_token:
            return
        resp = self.session.post(
            f"{BASE_URL}/users/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        if resp.status_code == 200:
            data = resp.json()
            token_data = data.get("data", data)
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")

    def run_test(self, test_func):
        """执行单个测试函数，自动计时和异常捕获"""
        name = test_func.__name__
        start = time.time()
        try:
            test_func()
            duration = (time.time() - start) * 1000
            self.record(name, True, duration)
        except AssertionError as e:
            duration = (time.time() - start) * 1000
            self.record(name, False, duration, str(e))
        except requests.ConnectionError as e:
            duration = (time.time() - start) * 1000
            self.record(name, False, duration, f"连接错误: {e}")
        except requests.Timeout as e:
            duration = (time.time() - start) * 1000
            self.record(name, False, duration, f"请求超时: {e}")
        except Exception as e:
            duration = (time.time() - start) * 1000
            self.record(name, False, duration, f"异常: {type(e).__name__}: {e}")

    def summary(self):
        """打印测试汇总信息并返回退出码"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_time = sum(r.duration_ms for r in self.results)

        print("\n" + "=" * 70)
        print("  测试汇总")
        print("=" * 70)
        print(f"  总测试数: {total}")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  总耗时: {total_time:.0f}ms ({total_time / 1000:.1f}s)")
        print("=" * 70)

        if failed > 0:
            print("\n  失败测试详情:")
            for r in self.results:
                if not r.passed:
                    print(f"    - {r.name}: {r.error_message}")

        return 0 if failed == 0 else 1


class TestAuthFlow:
    """认证流程测试类，覆盖登录、令牌验证、登出等场景"""

    def __init__(self, runner: TestRunner):
        """初始化认证流程测试类"""
        self.runner = runner

    def test_login_success(self):
        """测试正确凭据登录成功，验证返回 access_token"""
        resp = self.runner.session.post(
            f"{BASE_URL}/users/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        if data.get("success") is False:
            raise AssertionError(f"登录失败: {data.get('error', data)}")
        token_data = data.get("data", data)
        assert "access_token" in token_data, f"响应中缺少 access_token: {list(token_data.keys())}"
        self.runner.access_token = token_data["access_token"]
        self.runner.refresh_token = token_data.get("refresh_token")

    def test_login_wrong_password(self):
        """测试错误密码登录，验证返回错误响应"""
        resp = self.runner.session.post(
            f"{BASE_URL}/users/login",
            json={"username": TEST_USERNAME, "password": "wrong_password_123"}
        )
        assert resp.status_code != 200 or resp.json().get("success") is False, \
            f"错误密码应返回错误响应，实际: {resp.status_code}"

    def test_login_nonexistent_user(self):
        """测试不存在的用户登录，验证返回错误响应"""
        resp = self.runner.session.post(
            f"{BASE_URL}/users/login",
            json={"username": "nonexistent_user_xyz_999", "password": "any_password"}
        )
        assert resp.status_code != 200 or resp.json().get("success") is False, \
            f"不存在用户应返回错误响应，实际: {resp.status_code}"

    def test_access_protected_resource(self):
        """测试使用有效令牌访问受保护资源 /users/me"""
        assert self.runner.access_token, "无有效令牌，跳过"
        resp = self.runner.session.get(
            f"{BASE_URL}/users/me",
            headers=self.runner.auth_headers()
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_access_with_invalid_token(self):
        """测试使用无效令牌访问受保护资源，验证返回 401"""
        resp = self.runner.session.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}"

    def test_token_refresh(self):
        """测试使用 refresh_token 刷新令牌"""
        if not self.runner.refresh_token:
            raise AssertionError("无 refresh_token，跳过刷新测试")
        resp = self.runner.session.post(
            f"{BASE_URL}/users/token/refresh",
            json={"refresh_token": self.runner.refresh_token}
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_logout(self):
        """测试用户登出，验证返回 200"""
        assert self.runner.access_token, "无有效令牌，跳过登出测试"
        resp = self.runner.session.post(
            f"{BASE_URL}/users/logout",
            headers=self.runner.auth_headers()
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def run_all(self):
        """按顺序执行所有认证流程测试"""
        print("\n[模块 1/7] 认证流程测试")
        print("-" * 50)
        self.runner.run_test(self.test_login_success)
        self.runner.run_test(self.test_login_wrong_password)
        self.runner.run_test(self.test_login_nonexistent_user)
        self.runner.run_test(self.test_access_protected_resource)
        self.runner.run_test(self.test_access_with_invalid_token)
        self.runner.run_test(self.test_token_refresh)
        self.runner.run_test(self.test_logout)


class TestDiagnosisFlow:
    """诊断流程测试类，覆盖 SSE 融合诊断、记录查询、字段完整性验证"""

    FUSION_RESULT_FIELDS = [
        "disease_name", "disease_name_en", "confidence",
        "visual_confidence", "textual_confidence", "knowledge_confidence",
        "description", "symptoms", "causes", "recommendations",
        "treatment", "medicines", "severity", "knowledge_references", "roi_boxes"
    ]

    def __init__(self, runner: TestRunner):
        """初始化诊断流程测试类"""
        self.runner = runner
        self.last_diagnosis_id: Optional[int] = None
        self.complete_event_data: Optional[Dict] = None

    def _ensure_auth(self):
        """确保有有效的认证令牌，委托给 runner.ensure_auth()"""
        self.runner.ensure_auth()

    def test_sse_fusion_diagnosis(self):
        """测试 SSE 融合诊断流，验证收到 start/progress/complete 事件"""
        self._ensure_auth()
        assert self.runner.access_token, "无法获取认证令牌"

        events_received = {"start": False, "progress": False, "complete": False}

        with open(IMAGE_PATH, "rb") as img_file:
            resp = self.runner.session.post(
                f"{BASE_URL}/diagnosis/fusion/stream",
                files={"image": ("wheat_rust.png", img_file, "image/png")},
                data={
                    "symptoms": "叶片出现黄色条状锈斑",
                    "enable_thinking": "true",
                    "use_graph_rag": "true"
                },
                headers=self.runner.auth_headers(),
                stream=True,
                timeout=SSE_TIMEOUT
            )

        assert resp.status_code == 200, f"SSE 请求失败: {resp.status_code} {resp.text[:200]}"

        current_event = ""
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            if raw_line.startswith("event:"):
                current_event = raw_line[len("event:"):].strip()
            elif raw_line.startswith("data:"):
                data_str = raw_line[len("data:"):].strip()
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                event_type = data.get("event", current_event)

                if event_type == "start":
                    events_received["start"] = True
                elif event_type == "progress":
                    events_received["progress"] = True
                elif event_type == "complete":
                    events_received["complete"] = True
                    self.complete_event_data = data

        assert events_received["start"], "未收到 SSE start 事件"
        assert events_received["progress"], "未收到 SSE progress 事件"
        assert events_received["complete"], "未收到 SSE complete 事件"

    def test_diagnosis_records(self):
        """测试查询诊断记录列表，验证返回 200 且包含记录"""
        self._ensure_auth()
        resp = self.runner.session.get(
            f"{BASE_URL}/diagnosis/records",
            headers=self.runner.auth_headers()
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        records = data.get("records", [])
        if records:
            self.last_diagnosis_id = records[0].get("id")

    def test_diagnosis_detail(self):
        """测试查询诊断详情，验证 suggestions 为 List[str] 类型"""
        self._ensure_auth()
        if not self.last_diagnosis_id:
            resp = self.runner.session.get(
                f"{BASE_URL}/diagnosis/records",
                headers=self.runner.auth_headers()
            )
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                if records:
                    self.last_diagnosis_id = records[0].get("id")

        if not self.last_diagnosis_id:
            raise AssertionError("无诊断记录 ID，跳过详情测试")

        resp = self.runner.session.get(
            f"{BASE_URL}/diagnosis/{self.last_diagnosis_id}",
            headers=self.runner.auth_headers()
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"
        detail = resp.json()
        suggestions = detail.get("suggestions")
        if suggestions is not None:
            if isinstance(suggestions, str):
                try:
                    suggestions = json.loads(suggestions)
                except json.JSONDecodeError:
                    suggestions = [suggestions]
            assert isinstance(suggestions, list), \
                f"suggestions 应为 List[str]，实际类型: {type(suggestions).__name__}"

    def test_diagnosis_field_completeness(self):
        """验证 SSE complete 事件中包含全部 15 个 FusionDiagnosisResult 字段"""
        if not self.complete_event_data:
            raise AssertionError("无 SSE complete 事件数据，跳过字段完整性测试")

        data = self.complete_event_data.get("data", self.complete_event_data)
        diagnosis = data.get("diagnosis", data)

        missing_fields = []
        for field_name in self.FUSION_RESULT_FIELDS:
            if field_name not in diagnosis:
                missing_fields.append(field_name)

        assert len(missing_fields) == 0, \
            f"FusionDiagnosisResult 缺少字段: {missing_fields}"

    def run_all(self):
        """按顺序执行所有诊断流程测试"""
        print("\n[模块 2/7] 诊断流程测试")
        print("-" * 50)
        self.runner.run_test(self.test_sse_fusion_diagnosis)
        self.runner.run_test(self.test_diagnosis_records)
        self.runner.run_test(self.test_diagnosis_detail)
        self.runner.run_test(self.test_diagnosis_field_completeness)


class TestKnowledgeFlow:
    """知识图谱流程测试类，覆盖搜索、分类、详情查询"""

    def __init__(self, runner: TestRunner):
        """初始化知识图谱流程测试类"""
        self.runner = runner

    def test_knowledge_search(self):
        """测试知识搜索接口，验证搜索关键词'白粉病'返回 200"""
        resp = self.runner.session.get(
            f"{BASE_URL}/knowledge/search",
            params={"keyword": "白粉病"}
        )
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_knowledge_categories(self):
        """测试获取知识分类列表，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/knowledge/categories")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_knowledge_detail(self):
        """测试获取知识详情，验证返回 200 或 404"""
        resp = self.runner.session.get(f"{BASE_URL}/knowledge/1")
        assert resp.status_code in [200, 404], \
            f"期望 200 或 404，实际 {resp.status_code}"

    def run_all(self):
        """按顺序执行所有知识图谱流程测试"""
        print("\n[模块 3/7] 知识图谱流程测试")
        print("-" * 50)
        self.runner.run_test(self.test_knowledge_search)
        self.runner.run_test(self.test_knowledge_categories)
        self.runner.run_test(self.test_knowledge_detail)


class TestHealthCheck:
    """健康检查测试类，覆盖根路径、API、AI、数据库、启动状态检查"""

    def __init__(self, runner: TestRunner):
        """初始化健康检查测试类"""
        self.runner = runner

    def test_root_health(self):
        """测试根路径健康检查 GET /health，验证返回 200"""
        resp = self.runner.session.get("http://localhost:8000/health")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}"

    def test_api_health(self):
        """测试 API 健康检查 GET /api/v1/health，验证返回 200 且含 status 字段"""
        resp = self.runner.session.get(f"{BASE_URL}/health")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "status" in data, f"响应中缺少 status 字段: {list(data.keys())}"

    def test_ai_health(self):
        """测试 AI 服务健康检查 GET /diagnosis/health/ai，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/diagnosis/health/ai")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_database_health(self):
        """测试数据库健康检查 GET /api/v1/health/database，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/health/database")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_startup_status(self):
        """测试启动状态检查 GET /api/v1/health/startup，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/health/startup")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def run_all(self):
        """按顺序执行所有健康检查测试"""
        print("\n[模块 4/7] 健康检查测试")
        print("-" * 50)
        self.runner.run_test(self.test_root_health)
        self.runner.run_test(self.test_api_health)
        self.runner.run_test(self.test_ai_health)
        self.runner.run_test(self.test_database_health)
        self.runner.run_test(self.test_startup_status)


class TestStatsAndReports:
    """统计报表测试类，覆盖概览统计、诊断统计、缓存统计"""

    def __init__(self, runner: TestRunner):
        """初始化统计报表测试类"""
        self.runner = runner

    def test_stats_overview(self):
        """测试概览统计 GET /stats/overview，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/stats/overview")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_diagnosis_stats(self):
        """测试诊断统计 GET /stats/diagnoses，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/stats/diagnoses")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def test_cache_stats(self):
        """测试缓存统计 GET /stats/cache，验证返回 200"""
        resp = self.runner.session.get(f"{BASE_URL}/stats/cache")
        assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {resp.text[:200]}"

    def run_all(self):
        """按顺序执行所有统计报表测试"""
        print("\n[模块 5/7] 统计报表测试")
        print("-" * 50)
        self.runner.run_test(self.test_stats_overview)
        self.runner.run_test(self.test_diagnosis_stats)
        self.runner.run_test(self.test_cache_stats)


class TestBoundaryConditions:
    """边界条件测试类，覆盖无效令牌、不存在资源、空请求体、畸形 JSON"""

    def __init__(self, runner: TestRunner):
        """初始化边界条件测试类"""
        self.runner = runner

    def test_invalid_token_401(self):
        """测试无效 Bearer 令牌访问受保护资源，验证返回 401"""
        resp = self.runner.session.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}"

    def test_nonexistent_diagnosis_404(self):
        """测试查询不存在的诊断记录，验证返回 404"""
        self.runner.ensure_auth()
        resp = self.runner.session.get(
            f"{BASE_URL}/diagnosis/999999",
            headers=self.runner.auth_headers()
        )
        assert resp.status_code == 404, f"期望 404，实际 {resp.status_code}"

    def test_empty_login_body(self):
        """测试空请求体登录，验证返回 422 验证错误"""
        resp = self.runner.session.post(
            f"{BASE_URL}/users/login",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422, f"期望 422，实际 {resp.status_code}"

    def test_malformed_json(self):
        """测试畸形 JSON 请求体，验证返回适当的错误响应"""
        resp = self.runner.session.post(
            f"{BASE_URL}/users/login",
            data="{invalid json content",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code in [400, 422], \
            f"期望 400 或 422，实际 {resp.status_code}"

    def run_all(self):
        """按顺序执行所有边界条件测试"""
        print("\n[模块 6/7] 边界条件测试")
        print("-" * 50)
        self.runner.run_test(self.test_invalid_token_401)
        self.runner.run_test(self.test_nonexistent_diagnosis_404)
        self.runner.run_test(self.test_empty_login_body)
        self.runner.run_test(self.test_malformed_json)


class TestEventLoopNonBlocking:
    """事件循环非阻塞测试类，验证推理期间健康检查请求不被阻塞"""

    def __init__(self, runner: TestRunner):
        """初始化事件循环非阻塞测试类"""
        self.runner = runner
        self.health_check_results: List[bool] = []
        self.diagnosis_done = threading.Event()

    def _ensure_auth(self):
        """确保有有效的认证令牌，委托给 runner.ensure_auth()"""
        self.runner.ensure_auth()

    def _health_check_worker(self):
        """健康检查工作线程，每 3 秒发送一次健康检查请求"""
        while not self.diagnosis_done.is_set():
            try:
                resp = requests.get("http://localhost:8000/health", timeout=10)
                self.health_check_results.append(resp.status_code == 200)
            except Exception:
                self.health_check_results.append(False)
            self.diagnosis_done.wait(timeout=3)

    def test_health_during_inference(self):
        """测试推理期间健康检查不被阻塞，验证至少一次健康检查成功"""
        self._ensure_auth()
        assert self.runner.access_token, "无法获取认证令牌"

        self.health_check_results = []
        self.diagnosis_done.clear()

        health_thread = threading.Thread(target=self._health_check_worker, daemon=True)
        health_thread.start()

        try:
            with open(IMAGE_PATH, "rb") as img_file:
                resp = self.runner.session.post(
                    f"{BASE_URL}/diagnosis/fusion/stream",
                    files={"image": ("wheat_rust.png", img_file, "image/png")},
                    data={
                        "symptoms": "叶片出现锈斑",
                        "enable_thinking": "false",
                        "use_graph_rag": "true"
                    },
                    headers=self.runner.auth_headers(),
                    stream=True,
                    timeout=SSE_TIMEOUT
                )

            if resp.status_code == 200:
                for _ in resp.iter_lines(decode_unicode=True):
                    pass
        except Exception:
            pass
        finally:
            self.diagnosis_done.set()
            health_thread.join(timeout=15)

        success_count = sum(1 for r in self.health_check_results if r)
        assert success_count >= 1, \
            f"推理期间至少应有一次健康检查成功，实际: {success_count}/{len(self.health_check_results)}"

    def run_all(self):
        """执行事件循环非阻塞测试"""
        print("\n[模块 7/7] 事件循环非阻塞测试")
        print("-" * 50)
        self.runner.run_test(self.test_health_during_inference)


def main():
    """主函数，按顺序执行所有测试模块并输出汇总"""
    print("=" * 70)
    print("  WheatAgent v17 综合端到端测试")
    print("=" * 70)
    print(f"  基础 URL: {BASE_URL}")
    print(f"  测试用户: {TEST_USERNAME}")
    print(f"  测试图像: {IMAGE_PATH}")
    print(f"  SSE 超时: {SSE_TIMEOUT}s")
    print(f"  开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        pre_check = requests.get("http://localhost:8000/health", timeout=30)
        if pre_check.status_code != 200:
            print(f"\n[警告] 服务器健康检查返回 {pre_check.status_code}，测试可能失败")
    except requests.ConnectionError:
        print("\n[错误] 无法连接到服务器 http://localhost:8000")
        print("  请确保服务器已启动: python -m app.main")
        return 1
    except requests.Timeout:
        print("\n[警告] 服务器健康检查超时，可能仍在加载中，继续测试...")

    runner = TestRunner()

    fast_only = "--fast" in sys.argv

    TestAuthFlow(runner).run_all()
    if not fast_only:
        TestDiagnosisFlow(runner).run_all()
    TestKnowledgeFlow(runner).run_all()
    TestHealthCheck(runner).run_all()
    TestStatsAndReports(runner).run_all()
    TestBoundaryConditions(runner).run_all()
    if not fast_only:
        TestEventLoopNonBlocking(runner).run_all()

    exit_code = runner.summary()
    print(f"\n退出码: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
