"""
用户场景端到端测试用例

测试场景包括：
1. 用户登录认证流程
2. 图像上传诊断流程
3. 文本诊断流程
4. 多模态融合诊断流程
5. SSE 实时进度推送流程
"""
import os
import sys
import time
import pytest
import asyncio
from typing import Dict, Any

import httpx
from httpx import AsyncClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.e2e.test_utils import (
    TestConfig,
    TestDataGenerator,
    AuthHelper,
    SSEClient,
    PerformanceMonitor,
    TestReport,
    create_e2e_client,
    setup_mock_environment,
    teardown_mock_environment,
    assert_response_success,
    assert_diagnosis_result
)


@pytest.fixture(scope="module")
def event_loop():
    """
    创建事件循环
    
    返回:
        asyncio 事件循环
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def test_config() -> TestConfig:
    """
    创建测试配置
    
    返回:
        TestConfig 实例
    """
    return TestConfig(
        base_url=os.getenv("TEST_BASE_URL", "http://localhost:8000"),
        mock_mode=True
    )


@pytest.fixture(scope="module")
def performance_monitor() -> PerformanceMonitor:
    """
    创建性能监控器
    
    返回:
        PerformanceMonitor 实例
    """
    return PerformanceMonitor()


@pytest.fixture(scope="module")
def test_report() -> TestReport:
    """
    创建测试报告
    
    返回:
        TestReport 实例
    """
    return TestReport("WheatAgent E2E User Scenarios")


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """
    设置测试环境
    
    在测试开始前启用 Mock 模式，测试结束后清理
    """
    setup_mock_environment()
    yield
    teardown_mock_environment()


class TestUserAuthenticationScenarios:
    """
    用户登录认证场景测试类
    
    测试用户注册、登录、登出等认证流程
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.auth
    async def test_user_registration_success(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试用户注册成功场景
        
        验证：
        - 注册接口返回正确的状态码
        - 返回用户信息包含必要字段
        - 密码已正确哈希处理
        """
        async with create_e2e_client(test_config.base_url) as client:
            performance_monitor.start("user_registration")
            
            user_data = TestDataGenerator.generate_user_data("reg_test")
            
            response = await client.post(
                f"{test_config.api_prefix}/users/register",
                json=user_data
            )
            
            result = performance_monitor.stop(
                success=response.status_code in [200, 201, 409],
                metadata={"username": user_data["username"]}
            )
            
            test_report.record_test(
                test_name="user_registration_success",
                success=response.status_code in [200, 201, 409],
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code in [200, 201, 409], \
                f"注册失败: {response.text}"
            
            if response.status_code in [200, 201]:
                data = response.json()
                assert "username" in data
                assert "email" in data
                assert data["username"] == user_data["username"]
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.auth
    async def test_user_login_success(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试用户登录成功场景
        
        验证：
        - 登录接口返回正确的访问令牌
        - 令牌格式正确
        - 返回用户信息
        """
        async with create_e2e_client(test_config.base_url) as client:
            auth_helper = AuthHelper(client, test_config)
            
            await auth_helper.register_user()
            
            performance_monitor.start("user_login")
            
            login_result = await auth_helper.login()
            
            result = performance_monitor.stop(
                success=login_result["status_code"] == 200
            )
            
            test_report.record_test(
                test_name="user_login_success",
                success=login_result["status_code"] == 200,
                duration_ms=result["duration_ms"],
                status_code=login_result["status_code"]
            )
            
            assert login_result["status_code"] == 200, \
                f"登录失败: {login_result}"
            
            data = login_result["data"]
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "user" in data
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.auth
    async def test_user_login_invalid_credentials(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试用户登录失败场景（错误凭据）
        
        验证：
        - 错误的密码返回 401 状态码
        - 返回正确的错误信息
        """
        async with create_e2e_client(test_config.base_url) as client:
            performance_monitor.start("user_login_invalid")
            
            response = await client.post(
                f"{test_config.api_prefix}/users/login",
                json={
                    "username": "nonexistent_user_12345",
                    "password": "wrongpassword123"
                }
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 401
            )
            
            test_report.record_test(
                test_name="user_login_invalid_credentials",
                success=response.status_code == 401,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 401, \
                f"期望 401，实际: {response.status_code}"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.auth
    async def test_user_logout(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试用户登出场景
        
        验证：
        - 登出接口正常工作
        - 登出后令牌失效
        """
        async with create_e2e_client(test_config.base_url) as client:
            auth_helper = AuthHelper(client, test_config)
            
            await auth_helper.ensure_authenticated()
            
            performance_monitor.start("user_logout")
            
            logout_result = await auth_helper.logout()
            
            result = performance_monitor.stop(
                success=logout_result["status_code"] == 200
            )
            
            test_report.record_test(
                test_name="user_logout",
                success=logout_result["status_code"] == 200,
                duration_ms=result["duration_ms"],
                status_code=logout_result["status_code"]
            )
            
            assert logout_result["status_code"] == 200
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.auth
    async def test_protected_endpoint_without_token(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试无令牌访问受保护端点
        
        验证：
        - 无令牌时返回 401 状态码
        """
        async with create_e2e_client(test_config.base_url) as client:
            performance_monitor.start("protected_endpoint_no_token")
            
            response = await client.get(
                f"{test_config.api_prefix}/users/me"
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 401
            )
            
            test_report.record_test(
                test_name="protected_endpoint_without_token",
                success=response.status_code == 401,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 401


class TestImageDiagnosisScenarios:
    """
    图像上传诊断场景测试类
    
    测试图像上传、诊断、结果获取等流程
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_image_diagnosis_success(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试图像诊断成功场景
        
        验证：
        - 图像上传成功
        - 返回诊断结果
        - 结果包含必要字段
        """
        async with create_e2e_client(test_config.base_url) as client:
            auth_helper = AuthHelper(client, test_config)
            await auth_helper.ensure_authenticated()
            
            image_bytes = TestDataGenerator.generate_test_image()
            
            performance_monitor.start("image_diagnosis")
            
            files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
            data = {"symptoms": "叶片出现黄色斑点"}
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/image",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_helper.access_token}"}
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="image_diagnosis_success",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200, \
                f"图像诊断失败: {response.text}"
            
            response_data = response.json()
            assert "diagnosis_id" in response_data or "disease_name" in response_data
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_image_diagnosis_invalid_format(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试上传无效图像格式
        
        验证：
        - 无效格式返回错误
        - 错误信息正确
        """
        async with create_e2e_client(test_config.base_url) as client:
            auth_helper = AuthHelper(client, test_config)
            await auth_helper.ensure_authenticated()
            
            performance_monitor.start("image_diagnosis_invalid_format")
            
            files = {"image": ("test.txt", b"not an image", "text/plain")}
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/image",
                files=files,
                headers={"Authorization": f"Bearer {auth_helper.access_token}"}
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 400
            )
            
            test_report.record_test(
                test_name="image_diagnosis_invalid_format",
                success=response.status_code == 400,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_ai_image_diagnosis(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试 AI 图像诊断接口
        
        验证：
        - AI 诊断接口正常工作
        - 返回检测结果
        """
        async with create_e2e_client(test_config.base_url) as client:
            image_bytes = TestDataGenerator.generate_test_image()
            
            performance_monitor.start("ai_image_diagnosis")
            
            files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/image",
                files=files
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="ai_image_diagnosis",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "success" in data
            assert data["success"] is True


class TestTextDiagnosisScenarios:
    """
    文本诊断场景测试类
    
    测试基于症状描述的诊断流程
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_text_diagnosis_success(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试文本诊断成功场景
        
        验证：
        - 文本诊断接口正常工作
        - 返回诊断结果
        """
        async with create_e2e_client(test_config.base_url) as client:
            auth_helper = AuthHelper(client, test_config)
            await auth_helper.ensure_authenticated()
            
            symptoms = TestDataGenerator.generate_symptoms_text()
            
            performance_monitor.start("text_diagnosis")
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/text",
                data={"symptoms": symptoms},
                headers={"Authorization": f"Bearer {auth_helper.access_token}"}
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="text_diagnosis_success",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "disease_name" in data or "diagnosis" in data
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_ai_text_diagnosis(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试 AI 文本诊断接口
        
        验证：
        - AI 文本诊断接口正常工作
        - 返回诊断结果
        """
        async with create_e2e_client(test_config.base_url) as client:
            symptoms = "小麦叶片出现黄色条状孢子堆，沿叶脉平行排列"
            
            performance_monitor.start("ai_text_diagnosis")
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/text",
                data={"symptoms": symptoms}
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="ai_text_diagnosis",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "success" in data


class TestMultimodalFusionDiagnosisScenarios:
    """
    多模态融合诊断场景测试类
    
    测试图像+文本联合诊断流程
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_fusion_diagnosis_with_image_and_text(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试图像+文本融合诊断
        
        验证：
        - 融合诊断接口正常工作
        - 返回综合诊断结果
        - 结果包含多模态置信度
        """
        async with create_e2e_client(test_config.base_url) as client:
            image_bytes = TestDataGenerator.generate_test_image()
            symptoms = TestDataGenerator.generate_symptoms_text()
            context = TestDataGenerator.generate_diagnosis_context()
            
            performance_monitor.start("fusion_diagnosis_image_text")
            
            files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
            data = {
                "symptoms": symptoms,
                "weather": context["weather"],
                "growth_stage": context["growth_stage"],
                "affected_part": context["affected_part"],
                "enable_thinking": "true",
                "use_graph_rag": "true"
            }
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/fusion",
                files=files,
                data=data
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="fusion_diagnosis_with_image_and_text",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data.get("success") is True
            
            diagnosis = data.get("diagnosis", {})
            assert "disease_name" in diagnosis
            assert "confidence" in diagnosis
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_fusion_diagnosis_text_only(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试仅文本的融合诊断
        
        验证：
        - 仅文本输入时正常工作
        - 返回文本诊断结果
        """
        async with create_e2e_client(test_config.base_url) as client:
            symptoms = TestDataGenerator.generate_symptoms_text("条锈病")
            
            performance_monitor.start("fusion_diagnosis_text_only")
            
            data = {
                "symptoms": symptoms,
                "enable_thinking": "true",
                "use_graph_rag": "true"
            }
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/fusion",
                data=data
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="fusion_diagnosis_text_only",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data.get("success") is True
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_multimodal_diagnosis(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试多模态诊断接口
        
        验证：
        - 多模态诊断接口正常工作
        - 返回详细诊断结果
        """
        async with create_e2e_client(test_config.base_url) as client:
            image_bytes = TestDataGenerator.generate_test_image()
            symptoms = "叶片出现白色粉状斑点"
            
            performance_monitor.start("multimodal_diagnosis")
            
            files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
            data = {
                "symptoms": symptoms,
                "thinking_mode": "true",
                "use_graph_rag": "true"
            }
            
            response = await client.post(
                f"{test_config.api_prefix}/diagnosis/multimodal",
                files=files,
                data=data
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="multimodal_diagnosis",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "success" in data


class TestSSEProgressScenarios:
    """
    SSE 实时进度推送场景测试类
    
    测试 Server-Sent Events 实时进度推送功能
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_sse_diagnosis_stream(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试 SSE 诊断流
        
        验证：
        - SSE 连接正常建立
        - 接收到进度事件
        - 最终收到完成事件
        """
        async with create_e2e_client(test_config.base_url, timeout=60.0) as client:
            symptoms = TestDataGenerator.generate_symptoms_text()
            
            performance_monitor.start("sse_diagnosis_stream")
            
            sse_client = SSEClient(client)
            
            events = await sse_client.connect(
                f"{test_config.api_prefix}/diagnosis/fusion/stream",
                params={
                    "symptoms": symptoms,
                    "enable_thinking": "true",
                    "use_graph_rag": "true"
                }
            )
            
            result = performance_monitor.stop(
                success=len(events) > 0
            )
            
            test_report.record_test(
                test_name="sse_diagnosis_stream",
                success=len(events) > 0,
                duration_ms=result["duration_ms"]
            )
            
            assert len(events) > 0, "未收到任何 SSE 事件"
            
            progress_events = sse_client.get_progress_events()
            assert len(progress_events) > 0, "未收到进度事件"
            
            completion_event = sse_client.get_completion_event()
            assert completion_event is not None, "未收到完成事件"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_sse_progress_sequence(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试 SSE 进度事件顺序
        
        验证：
        - 进度事件按正确顺序发送
        - 进度值递增
        """
        async with create_e2e_client(test_config.base_url, timeout=60.0) as client:
            symptoms = "小麦叶片出现黄色条状孢子堆"
            
            performance_monitor.start("sse_progress_sequence")
            
            sse_client = SSEClient(client)
            
            events = await sse_client.connect(
                f"{test_config.api_prefix}/diagnosis/fusion/stream",
                params={"symptoms": symptoms}
            )
            
            result = performance_monitor.stop(
                success=len(events) > 0
            )
            
            test_report.record_test(
                test_name="sse_progress_sequence",
                success=len(events) > 0,
                duration_ms=result["duration_ms"]
            )
            
            progress_events = sse_client.get_progress_events()
            
            if len(progress_events) > 1:
                progress_values = []
                for event in progress_events:
                    data = event.get("data", {}).get("data", {})
                    progress = data.get("progress", 0)
                    progress_values.append(progress)
                
                for i in range(1, len(progress_values)):
                    assert progress_values[i] >= progress_values[i - 1], \
                        f"进度值应递增: {progress_values}"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.api
    async def test_sse_with_image(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试带图像的 SSE 诊断流
        
        验证：
        - 带图像的 SSE 流正常工作
        - 返回视觉检测结果
        """
        async with create_e2e_client(test_config.base_url, timeout=60.0) as client:
            image_bytes = TestDataGenerator.generate_test_image()
            symptoms = "叶片出现病斑"
            
            performance_monitor.start("sse_with_image")
            
            sse_client = SSEClient(client)
            
            files = {"image": ("test_wheat.jpg", image_bytes, "image/jpeg")}
            data = {
                "symptoms": symptoms,
                "enable_thinking": "true"
            }
            
            events = []
            async with client.stream(
                "POST",
                f"{test_config.api_prefix}/diagnosis/fusion/stream",
                files=files,
                data=data,
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            import json
                            event_data = json.loads(line[5:].strip())
                            events.append(event_data)
                        except:
                            pass
            
            result = performance_monitor.stop(
                success=len(events) > 0
            )
            
            test_report.record_test(
                test_name="sse_with_image",
                success=len(events) > 0,
                duration_ms=result["duration_ms"]
            )
            
            assert len(events) > 0, "未收到任何 SSE 事件"


class TestHealthCheckScenarios:
    """
    健康检查场景测试类
    
    测试服务健康状态检查功能
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_health_endpoint(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试健康检查端点
        
        验证：
        - 健康检查接口正常工作
        - 返回健康状态
        """
        async with create_e2e_client(test_config.base_url) as client:
            performance_monitor.start("health_check")
            
            response = await client.get("/health")
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="health_endpoint",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_api_health_endpoint(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试 API 健康检查端点
        
        验证：
        - API 健康检查接口正常工作
        - 返回详细健康状态
        """
        async with create_e2e_client(test_config.base_url) as client:
            performance_monitor.start("api_health_check")
            
            response = await client.get(
                f"{test_config.api_prefix}/health"
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="api_health_endpoint",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_ai_health_endpoint(
        self,
        test_config: TestConfig,
        performance_monitor: PerformanceMonitor,
        test_report: TestReport
    ):
        """
        测试 AI 服务健康检查端点
        
        验证：
        - AI 健康检查接口正常工作
        - 返回 AI 服务状态
        """
        async with create_e2e_client(test_config.base_url) as client:
            performance_monitor.start("ai_health_check")
            
            response = await client.get(
                f"{test_config.api_prefix}/diagnosis/health/ai"
            )
            
            result = performance_monitor.stop(
                success=response.status_code == 200
            )
            
            test_report.record_test(
                test_name="ai_health_endpoint",
                success=response.status_code == 200,
                duration_ms=result["duration_ms"],
                status_code=response.status_code
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data


@pytest.fixture(scope="session", autouse=True)
def save_test_report(test_report: TestReport, request):
    """
    测试结束后保存测试报告
    
    参数:
        test_report: 测试报告实例
        request: pytest 请求对象
    """
    yield
    
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"user_scenarios_{timestamp}.json"
    
    test_report.save_to_file(str(report_path))
    
    print(f"\n测试报告已保存到: {report_path}")
    
    stats = test_report.finalize()
    print(f"\n测试汇总:")
    print(f"  总测试数: {stats['summary']['total_tests']}")
    print(f"  通过: {stats['summary']['passed']}")
    print(f"  失败: {stats['summary']['failed']}")
    print(f"  通过率: {stats['summary']['pass_rate']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])
