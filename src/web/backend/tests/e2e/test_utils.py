"""
端到端测试辅助工具模块
提供测试客户端、认证辅助、测试数据生成等功能
"""
import os
import sys
import time
import json
import asyncio
import hashlib
import random
import io
from typing import Dict, Any, Optional, List, AsyncGenerator, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import pytest
import httpx
from httpx import AsyncClient
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


@dataclass
class TestConfig:
    """
    测试配置数据类
    
    属性:
        base_url: API 基础 URL
        api_prefix: API 前缀
        timeout: 请求超时时间（秒）
        mock_mode: 是否启用 Mock 模式
        test_user_username: 测试用户名
        test_user_password: 测试用户密码
        test_user_email: 测试用户邮箱
    """
    base_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"
    timeout: float = 30.0
    mock_mode: bool = True
    test_user_username: str = "e2e_test_user"
    test_user_password: str = "testpass123"
    test_user_email: str = "e2e_test@example.com"


@dataclass
class TestResult:
    """
    测试结果数据类
    
    属性:
        test_name: 测试名称
        success: 是否成功
        duration_ms: 执行耗时（毫秒）
        status_code: HTTP 状态码
        response_data: 响应数据
        error_message: 错误信息
        timestamp: 时间戳
    """
    test_name: str
    success: bool
    duration_ms: float
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TestDataGenerator:
    """
    测试数据生成器
    
    用于生成测试所需的各类数据，包括图像、文本等
    """
    
    DISEASE_SYMPTOMS = {
        "条锈病": [
            "叶片出现黄色条状孢子堆",
            "沿叶脉平行排列",
            "病斑呈鲜黄色",
            "后期产生黑色夏孢子堆"
        ],
        "白粉病": [
            "叶片表面出现白色粉状斑点",
            "逐渐扩大形成白色粉层",
            "后期产生黑色小粒点",
            "叶片变黄枯萎"
        ],
        "赤霉病": [
            "穗部出现水渍状病斑",
            "后期产生粉红色霉层",
            "病穗枯白",
            "籽粒干瘪"
        ],
        "蚜虫": [
            "叶片背面有密集蚜虫",
            "叶片卷曲发黄",
            "植株生长受阻",
            "分泌蜜露"
        ]
    }
    
    WEATHER_CONDITIONS = ["晴朗", "阴雨", "高温高湿", "干旱", "多风"]
    GROWTH_STAGES = ["苗期", "拔节期", "抽穗期", "灌浆期", "成熟期"]
    AFFECTED_PARTS = ["叶片", "茎秆", "穗部", "根部", "全株"]
    
    @classmethod
    def generate_test_image(
        cls,
        width: int = 640,
        height: int = 480,
        color: tuple = (139, 69, 19),
        format: str = "JPEG"
    ) -> bytes:
        """
        生成测试用图像
        
        参数:
            width: 图像宽度
            height: 图像高度
            color: 背景颜色 (R, G, B)
            format: 图像格式 (JPEG/PNG/WEBP)
        
        返回:
            图像字节数据
        """
        img = Image.new("RGB", (width, height), color)
        
        for _ in range(random.randint(3, 8)):
            x = random.randint(50, width - 50)
            y = random.randint(50, height - 50)
            r = random.randint(10, 40)
            spot_color = (
                random.randint(100, 200),
                random.randint(150, 255),
                random.randint(0, 100)
            )
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        if 0 <= x + dx < width and 0 <= y + dy < height:
                            img.putpixel((x + dx, y + dy), spot_color)
        
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()
    
    @classmethod
    def generate_symptoms_text(
        cls,
        disease_type: Optional[str] = None,
        include_context: bool = True
    ) -> str:
        """
        生成症状描述文本
        
        参数:
            disease_type: 指定病害类型（可选）
            include_context: 是否包含环境上下文
        
        返回:
            症状描述文本
        """
        if disease_type and disease_type in cls.DISEASE_SYMPTOMS:
            symptoms = cls.DISEASE_SYMPTOMS[disease_type]
        else:
            all_symptoms = []
            for s_list in cls.DISEASE_SYMPTOMS.values():
                all_symptoms.extend(s_list)
            symptoms = random.sample(all_symptoms, k=random.randint(2, 4))
        
        text = "、".join(symptoms[:2])
        if len(symptoms) > 2:
            text += f"，伴有{symptoms[2]}"
        
        if include_context:
            weather = random.choice(cls.WEATHER_CONDITIONS)
            stage = random.choice(cls.GROWTH_STAGES)
            text = f"当前{stage}，近期天气{weather}。{text}"
        
        return text
    
    @classmethod
    def generate_diagnosis_context(cls) -> Dict[str, str]:
        """
        生成诊断上下文信息
        
        返回:
            包含天气、生长阶段、发病部位的字典
        """
        return {
            "weather": random.choice(cls.WEATHER_CONDITIONS),
            "growth_stage": random.choice(cls.GROWTH_STAGES),
            "affected_part": random.choice(cls.AFFECTED_PARTS)
        }
    
    @classmethod
    def generate_user_data(
        cls,
        username_prefix: str = "test_user"
    ) -> Dict[str, str]:
        """
        生成用户注册数据
        
        参数:
            username_prefix: 用户名前缀
        
        返回:
            用户数据字典
        """
        timestamp = int(time.time() * 1000)
        return {
            "username": f"{username_prefix}_{timestamp}",
            "email": f"{username_prefix}_{timestamp}@test.com",
            "password": "TestPass123!"
        }


class AuthHelper:
    """
    认证辅助类
    
    提供用户注册、登录、令牌管理等功能
    """
    
    def __init__(self, client: AsyncClient, config: TestConfig):
        """
        初始化认证辅助类
        
        参数:
            client: 异步 HTTP 客户端
            config: 测试配置
        """
        self.client = client
        self.config = config
        self._access_token: Optional[str] = None
        self._user_data: Optional[Dict[str, Any]] = None
    
    async def register_user(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        注册新用户
        
        参数:
            username: 用户名（可选，默认使用配置值）
            email: 邮箱（可选，默认使用配置值）
            password: 密码（可选，默认使用配置值）
        
        返回:
            注册结果
        """
        user_data = {
            "username": username or self.config.test_user_username,
            "email": email or self.config.test_user_email,
            "password": password or self.config.test_user_password
        }
        
        response = await self.client.post(
            f"{self.config.api_prefix}/users/register",
            json=user_data
        )
        
        if response.status_code in [200, 201]:
            self._user_data = response.json()
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None
        }
    
    async def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        用户登录
        
        参数:
            username: 用户名（可选，默认使用配置值）
            password: 密码（可选，默认使用配置值）
        
        返回:
            登录结果，包含访问令牌
        """
        login_data = {
            "username": username or self.config.test_user_username,
            "password": password or self.config.test_user_password
        }
        
        response = await self.client.post(
            f"{self.config.api_prefix}/users/login",
            json=login_data
        )
        
        if response.status_code == 200:
            data = response.json()
            self._access_token = data.get("access_token")
            self._user_data = data.get("user")
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None
        }
    
    async def ensure_authenticated(self) -> str:
        """
        确保已认证，如未认证则自动注册并登录
        
        返回:
            访问令牌
        
        异常:
            RuntimeError: 认证失败时抛出
        """
        if self._access_token:
            return self._access_token
        
        register_result = await self.register_user()
        if register_result["status_code"] not in [200, 201, 409]:
            pass
        
        login_result = await self.login()
        
        if login_result["status_code"] != 200:
            raise RuntimeError(f"认证失败: {login_result}")
        
        return self._access_token
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        获取认证请求头
        
        返回:
            包含 Bearer Token 的请求头字典
        """
        if not self._access_token:
            raise RuntimeError("尚未认证，请先调用 ensure_authenticated()")
        
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
    
    @property
    def access_token(self) -> Optional[str]:
        """获取当前访问令牌"""
        return self._access_token
    
    @property
    def user_data(self) -> Optional[Dict[str, Any]]:
        """获取当前用户数据"""
        return self._user_data
    
    async def logout(self) -> Dict[str, Any]:
        """
        用户登出
        
        返回:
            登出结果
        """
        if not self._access_token:
            return {"status_code": 400, "data": {"detail": "未登录"}}
        
        response = await self.client.post(
            f"{self.config.api_prefix}/users/logout",
            headers=self.get_auth_headers()
        )
        
        if response.status_code == 200:
            self._access_token = None
            self._user_data = None
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None
        }


class SSEClient:
    """
    SSE (Server-Sent Events) 客户端
    
    用于测试实时进度推送功能
    """
    
    def __init__(self, client: AsyncClient):
        """
        初始化 SSE 客户端
        
        参数:
            client: 异步 HTTP 客户端
        """
        self.client = client
        self.events: List[Dict[str, Any]] = []
    
    async def connect(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        连接 SSE 端点并收集事件
        
        参数:
            url: SSE 端点 URL
            params: 请求参数
            headers: 请求头
        
        返回:
            收集到的事件列表
        """
        self.events = []
        
        request_headers = headers or {}
        request_headers["Accept"] = "text/event-stream"
        request_headers["Cache-Control"] = "no-cache"
        
        async with self.client.stream(
            "GET",
            url,
            params=params,
            headers=request_headers,
            timeout=60.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        self.events.append({
                            "event": event_type if 'event_type' in dir() else "message",
                            "data": data
                        })
                    except json.JSONDecodeError:
                        pass
                elif line.strip() == "":
                    event_type = "message"
        
        return self.events
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        按类型获取事件
        
        参数:
            event_type: 事件类型
        
        返回:
            匹配的事件列表
        """
        return [
            e for e in self.events
            if e.get("event") == event_type or e.get("data", {}).get("event") == event_type
        ]
    
    def get_progress_events(self) -> List[Dict[str, Any]]:
        """
        获取所有进度事件
        
        返回:
            进度事件列表
        """
        return self.get_events_by_type("progress")
    
    def get_completion_event(self) -> Optional[Dict[str, Any]]:
        """
        获取完成事件
        
        返回:
            完成事件，如无则返回 None
        """
        events = self.get_events_by_type("complete")
        return events[0] if events else None
    
    def get_error_events(self) -> List[Dict[str, Any]]:
        """
        获取所有错误事件
        
        返回:
            错误事件列表
        """
        return self.get_events_by_type("error")


class PerformanceMonitor:
    """
    性能监控器
    
    用于测量和记录测试性能指标
    """
    
    def __init__(self):
        """初始化性能监控器"""
        self.measurements: List[Dict[str, Any]] = []
        self._start_time: Optional[float] = None
        self._operation_name: Optional[str] = None
    
    def start(self, operation_name: str) -> "PerformanceMonitor":
        """
        开始测量
        
        参数:
            operation_name: 操作名称
        
        返回:
            self 以支持链式调用
        """
        self._start_time = time.time()
        self._operation_name = operation_name
        return self
    
    def stop(self, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        停止测量并记录结果
        
        参数:
            success: 操作是否成功
            metadata: 附加元数据
        
        返回:
            测量结果
        """
        if self._start_time is None:
            raise RuntimeError("未调用 start() 开始测量")
        
        duration_ms = (time.time() - self._start_time) * 1000
        
        result = {
            "operation": self._operation_name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            result["metadata"] = metadata
        
        self.measurements.append(result)
        
        self._start_time = None
        self._operation_name = None
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        返回:
            统计信息字典
        """
        if not self.measurements:
            return {"total_operations": 0}
        
        durations = [m["duration_ms"] for m in self.measurements]
        success_count = sum(1 for m in self.measurements if m["success"])
        
        return {
            "total_operations": len(self.measurements),
            "successful_operations": success_count,
            "failed_operations": len(self.measurements) - success_count,
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "min_duration_ms": round(min(durations), 2),
            "max_duration_ms": round(max(durations), 2),
            "total_duration_ms": round(sum(durations), 2)
        }
    
    def get_slow_operations(self, threshold_ms: float = 1000.0) -> List[Dict[str, Any]]:
        """
        获取耗时超过阈值的操作
        
        参数:
            threshold_ms: 时间阈值（毫秒）
        
        返回:
            慢操作列表
        """
        return [
            m for m in self.measurements
            if m["duration_ms"] > threshold_ms
        ]


class TestReport:
    """
    测试报告生成器
    
    用于生成和保存测试报告
    """
    
    def __init__(self, report_name: str = "E2E Test Report"):
        """
        初始化测试报告生成器
        
        参数:
            report_name: 报告名称
        """
        self.report_name = report_name
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
    
    def add_result(self, result: TestResult) -> None:
        """
        添加测试结果
        
        参数:
            result: 测试结果
        """
        self.results.append(result)
    
    def record_test(
        self,
        test_name: str,
        success: bool,
        duration_ms: float,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> TestResult:
        """
        记录测试结果
        
        参数:
            test_name: 测试名称
            success: 是否成功
            duration_ms: 耗时（毫秒）
            status_code: HTTP 状态码
            response_data: 响应数据
            error_message: 错误信息
        
        返回:
            测试结果对象
        """
        result = TestResult(
            test_name=test_name,
            success=success,
            duration_ms=duration_ms,
            status_code=status_code,
            response_data=response_data,
            error_message=error_message
        )
        self.results.append(result)
        return result
    
    def finalize(self) -> Dict[str, Any]:
        """
        完成报告并生成汇总
        
        返回:
            报告汇总字典
        """
        self.end_time = datetime.now()
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.duration_ms for r in self.results)
        
        report = {
            "report_name": self.report_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration_ms": round(total_duration, 2),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "status_code": r.status_code,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }
        
        return report
    
    def save_to_file(self, filepath: str) -> None:
        """
        保存报告到文件
        
        参数:
            filepath: 文件路径
        """
        report = self.finalize()
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


@asynccontextmanager
async def create_e2e_client(
    base_url: str = "http://localhost:8000",
    timeout: float = 30.0
) -> AsyncGenerator[AsyncClient, None]:
    """
    创建端到端测试客户端的上下文管理器
    
    参数:
        base_url: API 基础 URL
        timeout: 请求超时时间
    
    生成:
        AsyncClient: 异步 HTTP 客户端
    """
    async with AsyncClient(
        base_url=base_url,
        timeout=timeout
    ) as client:
        yield client


def setup_mock_environment() -> None:
    """
    设置 Mock 环境变量
    
    启用 AI 服务的 Mock 模式，用于测试环境
    """
    os.environ["WHEATAGENT_MOCK_AI"] = "true"


def teardown_mock_environment() -> None:
    """
    清理 Mock 环境变量
    """
    if "WHEATAGENT_MOCK_AI" in os.environ:
        del os.environ["WHEATAGENT_MOCK_AI"]


def assert_response_success(
    response: httpx.Response,
    expected_status: int = 200
) -> Dict[str, Any]:
    """
    断言响应成功
    
    参数:
        response: HTTP 响应
        expected_status: 期望的状态码
    
    返回:
        响应 JSON 数据
    
    异常:
        AssertionError: 断言失败时抛出
    """
    assert response.status_code == expected_status, \
        f"期望状态码 {expected_status}，实际为 {response.status_code}，响应: {response.text}"
    
    return response.json()


def assert_diagnosis_result(data: Dict[str, Any]) -> None:
    """
    断言诊断结果格式正确
    
    参数:
        data: 诊断结果数据
    
    异常:
        AssertionError: 断言失败时抛出
    """
    assert "success" in data, "诊断结果缺少 success 字段"
    assert data["success"] is True, f"诊断失败: {data.get('error', '未知错误')}"
    
    diagnosis = data.get("diagnosis") or data.get("data")
    assert diagnosis is not None, "诊断结果缺少 diagnosis 或 data 字段"
    
    assert "disease_name" in diagnosis, "诊断结果缺少 disease_name 字段"
    assert "confidence" in diagnosis, "诊断结果缺少 confidence 字段"
    assert 0 <= diagnosis["confidence"] <= 1, "confidence 应在 0-1 之间"


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 10.0,
    interval: float = 0.1
) -> bool:
    """
    等待条件满足
    
    参数:
        condition: 条件函数
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
    
    返回:
        条件是否在超时前满足
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)
    return False


async def async_wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 10.0,
    interval: float = 0.1
) -> bool:
    """
    异步等待条件满足
    
    参数:
        condition: 条件函数
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
    
    返回:
        条件是否在超时前满足
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False
