"""
用户认证功能完整测试脚本
测试用户注册、登录、JWT Token 验证、权限控制等功能
"""
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.security import get_password_hash, create_access_token, decode_access_token
from app.models.user import User
from app.models.auth import PasswordResetToken, RefreshToken, LoginAttempt, UserSession
from app.main import app
from app.core.database import get_db


TEST_DATABASE_URL = "sqlite:///:memory:"


class TestResult:
    """测试结果类"""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
    
    def add_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """
        添加测试结果
        
        参数:
            test_name: 测试名称
            passed: 是否通过
            message: 测试消息
            details: 详细信息
        """
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ 通过"
        else:
            self.failed_tests += 1
            status = "❌ 失败"
        
        result = {
            "test_name": test_name,
            "status": status,
            "passed": passed,
            "message": message,
            "details": details or {}
        }
        self.test_details.append(result)
        
        print(f"{status} - {test_name}: {message}")
        if details and not passed:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("测试摘要")
        print("=" * 80)
        print(f"总测试数: {self.total_tests}")
        print(f"通过: {self.passed_tests}")
        print(f"失败: {self.failed_tests}")
        print(f"通过率: {(self.passed_tests/self.total_tests*100):.2f}%")
        print("=" * 80)
        
        if self.failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_details:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['message']}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": round(self.passed_tests/self.total_tests*100, 2) if self.total_tests > 0 else 0,
            "test_details": self.test_details,
            "timestamp": datetime.now().isoformat()
        }


class AuthTester:
    """用户认证测试器"""
    
    def __init__(self):
        self.result = TestResult()
        self.client = None
        self.db_session = None
        self.test_user = None
        self.access_token = None
        self.refresh_token = None
    
    def setup(self):
        """设置测试环境"""
        print("\n" + "=" * 80)
        print("设置测试环境")
        print("=" * 80)
        
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        Base.metadata.create_all(bind=engine)
        
        session_maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db_session = session_maker()
        
        def override_get_db():
            try:
                yield self.db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        self.client = TestClient(app, raise_server_exceptions=False)
        
        print("✅ 测试环境设置完成")
    
    def teardown(self):
        """清理测试环境"""
        if self.db_session:
            self.db_session.close()
        app.dependency_overrides.clear()
        print("\n✅ 测试环境清理完成")
    
    def create_test_user(self, username: str = "testuser", email: str = "test@example.com", 
                         password: str = "testpass123", role: str = "farmer", is_active: bool = True) -> User:
        """
        创建测试用户
        
        参数:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 角色
            is_active: 是否激活
        
        返回:
            User: 创建的用户对象
        """
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            is_active=is_active
        )
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user
    
    def test_user_registration(self):
        """测试用户注册功能"""
        print("\n" + "=" * 80)
        print("测试 1: 用户注册功能")
        print("=" * 80)
        
        print("\n1.1 测试正常注册")
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123"
        }
        response = self.client.post("/api/v1/users/register", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data["data"]["username"] == "newuser":
                self.result.add_result(
                    "正常注册",
                    True,
                    "用户注册成功，返回正确的用户信息"
                )
            else:
                self.result.add_result(
                    "正常注册",
                    False,
                    "注册响应格式不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "正常注册",
                False,
                f"注册失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n1.2 测试重复用户名注册")
        duplicate_username_data = {
            "username": "newuser",
            "email": "another@example.com",
            "password": "SecurePass123"
        }
        response = self.client.post("/api/v1/users/register", json=duplicate_username_data)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and data.get("error_code") == "AUTH_002":
                self.result.add_result(
                    "重复用户名注册",
                    True,
                    "正确拒绝重复用户名注册"
                )
            else:
                self.result.add_result(
                    "重复用户名注册",
                    False,
                    "未正确处理重复用户名",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "重复用户名注册",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n1.3 测试重复邮箱注册")
        duplicate_email_data = {
            "username": "anotheruser",
            "email": "newuser@example.com",
            "password": "SecurePass123"
        }
        response = self.client.post("/api/v1/users/register", json=duplicate_email_data)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and data.get("error_code") == "AUTH_001":
                self.result.add_result(
                    "重复邮箱注册",
                    True,
                    "正确拒绝重复邮箱注册"
                )
            else:
                self.result.add_result(
                    "重复邮箱注册",
                    False,
                    "未正确处理重复邮箱",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "重复邮箱注册",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n1.4 测试无效数据 - 用户名过短")
        short_username_data = {
            "username": "ab",
            "email": "short@example.com",
            "password": "SecurePass123"
        }
        response = self.client.post("/api/v1/users/register", json=short_username_data)
        
        if response.status_code == 422:
            self.result.add_result(
                "用户名过短验证",
                True,
                "正确拒绝过短的用户名"
            )
        else:
            self.result.add_result(
                "用户名过短验证",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n1.5 测试无效数据 - 密码过短")
        short_password_data = {
            "username": "validuser",
            "email": "valid@example.com",
            "password": "12345"
        }
        response = self.client.post("/api/v1/users/register", json=short_password_data)
        
        if response.status_code == 422:
            self.result.add_result(
                "密码过短验证",
                True,
                "正确拒绝过短的密码"
            )
        else:
            self.result.add_result(
                "密码过短验证",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n1.6 测试缺少必填字段")
        missing_fields_data = {
            "username": "incomplete"
        }
        response = self.client.post("/api/v1/users/register", json=missing_fields_data)
        
        if response.status_code == 422:
            self.result.add_result(
                "缺少必填字段验证",
                True,
                "正确拒绝缺少必填字段的请求"
            )
        else:
            self.result.add_result(
                "缺少必填字段验证",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
    
    def test_user_login(self):
        """测试用户登录功能"""
        print("\n" + "=" * 80)
        print("测试 2: 用户登录功能")
        print("=" * 80)
        
        self.test_user = self.create_test_user()
        
        print("\n2.1 测试正常登录")
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/v1/users/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "access_token" in data["data"]:
                self.access_token = data["data"]["access_token"]
                self.refresh_token = data["data"].get("refresh_token")
                self.result.add_result(
                    "正常登录",
                    True,
                    "登录成功，返回 JWT Token 和 Refresh Token"
                )
            else:
                self.result.add_result(
                    "正常登录",
                    False,
                    "登录响应格式不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "正常登录",
                False,
                f"登录失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n2.2 测试使用邮箱登录")
        login_with_email_data = {
            "username": "test@example.com",
            "password": "testpass123"
        }
        response = self.client.post("/api/v1/users/login", json=login_with_email_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "access_token" in data["data"]:
                self.result.add_result(
                    "邮箱登录",
                    True,
                    "可以使用邮箱登录"
                )
            else:
                self.result.add_result(
                    "邮箱登录",
                    False,
                    "邮箱登录响应格式不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "邮箱登录",
                False,
                f"邮箱登录失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n2.3 测试错误密码")
        wrong_password_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post("/api/v1/users/login", json=wrong_password_data)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and data.get("error_code") == "AUTH_002":
                self.result.add_result(
                    "错误密码登录",
                    True,
                    "正确拒绝错误密码"
                )
            else:
                self.result.add_result(
                    "错误密码登录",
                    False,
                    "未正确处理错误密码",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "错误密码登录",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n2.4 测试不存在的用户")
        nonexistent_user_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        response = self.client.post("/api/v1/users/login", json=nonexistent_user_data)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and data.get("error_code") == "AUTH_002":
                self.result.add_result(
                    "不存在用户登录",
                    True,
                    "正确拒绝不存在的用户"
                )
            else:
                self.result.add_result(
                    "不存在用户登录",
                    False,
                    "未正确处理不存在的用户",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "不存在用户登录",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n2.5 测试被禁用的用户")
        inactive_user = self.create_test_user(
            username="inactiveuser",
            email="inactive@example.com",
            password="testpass123",
            is_active=False
        )
        
        inactive_login_data = {
            "username": "inactiveuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/v1/users/login", json=inactive_login_data)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and data.get("error_code") == "AUTH_004":
                self.result.add_result(
                    "禁用用户登录",
                    True,
                    "正确拒绝被禁用的用户"
                )
            else:
                self.result.add_result(
                    "禁用用户登录",
                    False,
                    "未正确处理被禁用的用户",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "禁用用户登录",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
    
    def test_jwt_token_validation(self):
        """测试 JWT Token 验证"""
        print("\n" + "=" * 80)
        print("测试 3: JWT Token 验证")
        print("=" * 80)
        
        if not self.access_token:
            self.result.add_result(
                "JWT Token 验证",
                False,
                "无法测试，登录未成功获取 Token"
            )
            return
        
        print("\n3.1 测试有效 Token 访问受保护资源")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.get("/api/v1/users/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("username") == "testuser":
                self.result.add_result(
                    "有效 Token 访问",
                    True,
                    "使用有效 Token 成功访问受保护资源"
                )
            else:
                self.result.add_result(
                    "有效 Token 访问",
                    False,
                    "返回的用户信息不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "有效 Token 访问",
                False,
                f"访问失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n3.2 测试无效 Token")
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        response = self.client.get("/api/v1/users/me", headers=invalid_headers)
        
        if response.status_code == 401:
            self.result.add_result(
                "无效 Token 访问",
                True,
                "正确拒绝无效 Token"
            )
        else:
            self.result.add_result(
                "无效 Token 访问",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n3.3 测试缺少 Token")
        response = self.client.get("/api/v1/users/me")
        
        if response.status_code == 401:
            self.result.add_result(
                "缺少 Token 访问",
                True,
                "正确拒绝缺少 Token 的请求"
            )
        else:
            self.result.add_result(
                "缺少 Token 访问",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n3.4 测试格式错误的认证头")
        malformed_headers = {"Authorization": "InvalidFormat token"}
        response = self.client.get("/api/v1/users/me", headers=malformed_headers)
        
        if response.status_code == 401:
            self.result.add_result(
                "格式错误认证头",
                True,
                "正确拒绝格式错误的认证头"
            )
        else:
            self.result.add_result(
                "格式错误认证头",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n3.5 测试 Token 解码")
        decoded = decode_access_token(self.access_token)
        
        if decoded and decoded.get("sub") == "testuser":
            self.result.add_result(
                "Token 解码",
                True,
                "Token 解码成功，包含正确的用户信息"
            )
        else:
            self.result.add_result(
                "Token 解码",
                False,
                "Token 解码失败或信息不正确",
                {"decoded": decoded}
            )
    
    def test_permission_control(self):
        """测试权限控制"""
        print("\n" + "=" * 80)
        print("测试 4: 权限控制")
        print("=" * 80)
        
        print("\n4.1 测试未认证访问受保护资源")
        response = self.client.get("/api/v1/users/me")
        
        if response.status_code == 401:
            self.result.add_result(
                "未认证访问",
                True,
                "正确拒绝未认证访问"
            )
        else:
            self.result.add_result(
                "未认证访问",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n4.2 测试普通用户权限")
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.client.get("/api/v1/users/me", headers=headers)
            
            if response.status_code == 200:
                self.result.add_result(
                    "普通用户访问",
                    True,
                    "普通用户可以访问自己的信息"
                )
            else:
                self.result.add_result(
                    "普通用户访问",
                    False,
                    f"普通用户访问失败，状态码: {response.status_code}",
                    {"response": response.text}
                )
        else:
            self.result.add_result(
                "普通用户访问",
                False,
                "无法测试，未获取到 Token"
            )
        
        print("\n4.3 测试管理员用户权限")
        admin_user = self.create_test_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
            role="admin"
        )
        
        admin_token = create_access_token(data={"sub": "adminuser", "user_id": admin_user.id})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = self.client.get("/api/v1/users/me", headers=admin_headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("role") == "admin":
                self.result.add_result(
                    "管理员用户访问",
                    True,
                    "管理员用户可以访问受保护资源"
                )
            else:
                self.result.add_result(
                    "管理员用户访问",
                    False,
                    "管理员角色信息不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "管理员用户访问",
                False,
                f"管理员访问失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n4.4 测试农技人员权限")
        technician_user = self.create_test_user(
            username="techuser",
            email="tech@example.com",
            password="techpass123",
            role="technician"
        )
        
        tech_token = create_access_token(data={"sub": "techuser", "user_id": technician_user.id})
        tech_headers = {"Authorization": f"Bearer {tech_token}"}
        
        response = self.client.get("/api/v1/users/me", headers=tech_headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("role") == "technician":
                self.result.add_result(
                    "农技人员访问",
                    True,
                    "农技人员可以访问受保护资源"
                )
            else:
                self.result.add_result(
                    "农技人员访问",
                    False,
                    "农技人员角色信息不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "农技人员访问",
                False,
                f"农技人员访问失败，状态码: {response.status_code}",
                {"response": response.text}
            )
    
    def test_token_refresh(self):
        """测试 Token 刷新功能"""
        print("\n" + "=" * 80)
        print("测试 5: Token 刷新功能")
        print("=" * 80)
        
        if not self.refresh_token:
            self.result.add_result(
                "Token 刷新",
                False,
                "无法测试，登录未成功获取 Refresh Token"
            )
            return
        
        print("\n5.1 测试正常刷新 Token")
        refresh_data = {
            "refresh_token": self.refresh_token
        }
        response = self.client.post("/api/v1/users/token/refresh", json=refresh_data)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.result.add_result(
                    "正常刷新 Token",
                    True,
                    "使用 Refresh Token 成功获取新的 Access Token"
                )
            else:
                self.result.add_result(
                    "正常刷新 Token",
                    False,
                    "刷新响应格式不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "正常刷新 Token",
                False,
                f"刷新失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n5.2 测试无效 Refresh Token")
        invalid_refresh_data = {
            "refresh_token": "invalid_refresh_token_12345"
        }
        response = self.client.post("/api/v1/users/token/refresh", json=invalid_refresh_data)
        
        if response.status_code == 401:
            self.result.add_result(
                "无效 Refresh Token",
                True,
                "正确拒绝无效的 Refresh Token"
            )
        else:
            self.result.add_result(
                "无效 Refresh Token",
                False,
                f"状态码不正确: {response.status_code}",
                {"response": response.text}
            )
    
    def test_logout(self):
        """测试登出功能"""
        print("\n" + "=" * 80)
        print("测试 6: 登出功能")
        print("=" * 80)
        
        if not self.access_token:
            self.result.add_result(
                "登出功能",
                False,
                "无法测试，登录未成功获取 Token"
            )
            return
        
        print("\n6.1 测试正常登出")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post("/api/v1/users/logout", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.result.add_result(
                    "正常登出",
                    True,
                    "登出成功，撤销所有令牌"
                )
            else:
                self.result.add_result(
                    "正常登出",
                    False,
                    "登出响应格式不正确",
                    {"response": data}
                )
        else:
            self.result.add_result(
                "正常登出",
                False,
                f"登出失败，状态码: {response.status_code}",
                {"response": response.text}
            )
        
        print("\n6.2 测试登出后使用旧 Token")
        response = self.client.get("/api/v1/users/me", headers=headers)
        
        if response.status_code == 401:
            self.result.add_result(
                "登出后使用旧 Token",
                True,
                "登出后旧 Token 已失效"
            )
        else:
            self.result.add_result(
                "登出后使用旧 Token",
                False,
                "登出后旧 Token 仍然有效",
                {"status_code": response.status_code}
            )
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("开始执行用户认证功能测试")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.setup()
            
            self.test_user_registration()
            self.test_user_login()
            self.test_jwt_token_validation()
            self.test_permission_control()
            self.test_token_refresh()
            self.test_logout()
            
        except Exception as e:
            print(f"\n❌ 测试执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.teardown()
        
        self.result.print_summary()
        
        return self.result.to_dict()


def main():
    """主函数"""
    tester = AuthTester()
    results = tester.run_all_tests()
    
    output_file = "user_auth_test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试结果已保存到: {output_file}")
    
    return results


if __name__ == "__main__":
    results = main()
    
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
