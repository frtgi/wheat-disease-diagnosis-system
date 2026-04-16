"""
用户认证 API 测试
测试用户注册、登录、获取用户信息等功能
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestUserRegister:
    """用户注册测试类"""

    def test_register_success(self, client: TestClient):
        """
        测试用户注册成功
        
        验证:
        - 返回状态码 200
        - 返回用户信息包含正确的用户名和邮箱
        - 密码不应在响应中返回
        """
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """
        测试注册重复用户名
        
        验证:
        - 返回状态码 409 (Conflict)
        - 错误信息提示用户名已被使用
        """
        user_data = {
            "username": "testuser",
            "email": "another@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 409
        assert "用户名" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """
        测试注册重复邮箱
        
        验证:
        - 返回状态码 409 (Conflict)
        - 错误信息提示邮箱已被注册
        """
        user_data = {
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 409
        assert "邮箱" in response.json()["detail"]

    def test_register_short_username(self, client: TestClient):
        """
        测试用户名过短
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        user_data = {
            "username": "ab",
            "email": "short@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """
        测试密码过短
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        user_data = {
            "username": "validuser",
            "email": "valid@example.com",
            "password": "12345"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """
        测试缺少必填字段
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        user_data = {
            "username": "incomplete"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422


class TestUserLogin:
    """用户登录测试类"""

    def test_login_success(self, client: TestClient, test_user: User):
        """
        测试用户登录成功
        
        验证:
        - 返回状态码 200
        - 返回包含 access_token 的响应
        - token 类型为 bearer
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_email(self, client: TestClient, test_user: User):
        """
        测试使用邮箱登录
        
        验证:
        - 可以使用邮箱代替用户名登录
        - 返回有效的 access_token
        """
        login_data = {
            "username": "test@example.com",
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """
        测试密码错误
        
        验证:
        - 返回状态码 401 (Unauthorized)
        - 错误信息提示用户名或密码错误
        """
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 401
        assert "密码" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """
        测试登录不存在的用户
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        login_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """
        测试登录被禁用的用户
        
        验证:
        - 返回状态码 403 (Forbidden)
        - 错误信息提示账号已被禁用
        """
        from app.core.security import get_password_hash
        
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            role="user",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "password123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 403
        assert "禁用" in response.json()["detail"]


class TestGetCurrentUser:
    """获取当前用户信息测试类"""

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict):
        """
        测试获取当前用户信息成功
        
        验证:
        - 返回状态码 200
        - 返回正确的用户信息
        """
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_no_token(self, client: TestClient):
        """
        测试无 token 获取用户信息
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """
        测试无效 token 获取用户信息
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401

    def test_get_current_user_malformed_header(self, client: TestClient):
        """
        测试格式错误的认证头
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401


class TestUserLoginAsync:
    """异步用户登录测试类"""

    @pytest.mark.asyncio
    async def test_login_success_async(self, async_client: AsyncClient, test_user: User):
        """
        异步测试用户登录成功
        
        验证:
        - 使用 AsyncClient 登录成功
        - 返回有效的 access_token
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = await async_client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user_async(self, async_client: AsyncClient, auth_headers: dict):
        """
        异步测试获取当前用户信息
        
        验证:
        - 使用 AsyncClient 获取用户信息成功
        """
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
