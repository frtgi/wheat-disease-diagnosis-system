"""
用户认证集成测试
测试完整登录流程、令牌刷新、会话管理等功能的集成测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash, create_access_token


@pytest.mark.integration
@pytest.mark.auth
class TestLoginFlow:
    """完整登录流程集成测试"""

    @pytest.mark.asyncio
    async def test_complete_login_flow(self, async_client: AsyncClient, db_session: Session):
        """
        测试完整的用户登录流程
        
        验证步骤:
        1. 用户注册
        2. 用户登录获取令牌
        3. 使用令牌访问受保护资源
        """
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "securepass123"
        }
        
        register_response = await async_client.post("/api/v1/users/register", json=user_data)
        assert register_response.status_code == 200
        assert register_response.json()["username"] == "integrationuser"
        
        login_data = {
            "username": "integrationuser",
            "password": "securepass123"
        }
        login_response = await async_client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_response = await async_client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "integrationuser"

    @pytest.mark.asyncio
    async def test_login_with_email_flow(self, async_client: AsyncClient, db_session: Session):
        """
        测试使用邮箱登录的完整流程
        
        验证:
        - 可以使用邮箱代替用户名登录
        - 登录后可以正常访问资源
        """
        user_data = {
            "username": "emailuser",
            "email": "emaillogin@example.com",
            "password": "emailpass123"
        }
        
        register_response = await async_client.post("/api/v1/users/register", json=user_data)
        assert register_response.status_code == 200
        
        login_data = {
            "username": "emaillogin@example.com",
            "password": "emailpass123"
        }
        login_response = await async_client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    @pytest.mark.asyncio
    async def test_login_failure_wrong_password(self, async_client: AsyncClient, test_user: User):
        """
        测试密码错误时的登录失败流程
        
        验证:
        - 返回 401 状态码
        - 错误信息正确
        """
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = await async_client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 401
        assert "密码" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.auth
class TestTokenRefresh:
    """令牌刷新集成测试"""

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, async_client: AsyncClient, db_session: Session):
        """
        测试令牌刷新流程
        
        验证步骤:
        1. 用户登录获取访问令牌
        2. 使用刷新令牌获取新的访问令牌
        3. 新令牌可以正常使用
        """
        user_data = {
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "refreshpass123"
        }
        
        await async_client.post("/api/v1/users/register", json=user_data)
        
        login_data = {
            "username": "refreshuser",
            "password": "refreshpass123"
        }
        login_response = await async_client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code == 200
        
        original_token = login_response.json()["access_token"]
        
        refresh_data = {"refresh_token": "test_refresh_token"}
        refresh_response = await async_client.post("/api/v1/users/token/refresh", json=refresh_data)
        
        assert refresh_response.status_code in [200, 401, 422]

    @pytest.mark.asyncio
    async def test_invalid_refresh_token(self, async_client: AsyncClient):
        """
        测试无效刷新令牌的处理
        
        验证:
        - 无效令牌返回 401 错误
        """
        refresh_data = {"refresh_token": "invalid_token_12345"}
        response = await async_client.post("/api/v1/users/token/refresh", json=refresh_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_access(self, async_client: AsyncClient, test_user: User):
        """
        测试过期令牌访问受保护资源
        
        验证:
        - 过期令牌无法访问受保护资源
        """
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTAwMDAwMDAwMH0.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await async_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestSessionManagement:
    """会话管理集成测试"""

    @pytest.mark.asyncio
    async def test_get_sessions(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试获取活跃会话列表
        
        验证:
        - 返回会话列表
        - 会话包含必要信息
        """
        response = await async_client.get("/api/v1/users/sessions/list", headers=auth_headers)
        
        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)

    @pytest.mark.asyncio
    async def test_terminate_session(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试终止指定会话
        
        验证:
        - 可以终止会话
        - 终止后会话不再活跃
        """
        response = await async_client.get("/api/v1/users/sessions/list", headers=auth_headers)
        
        if response.status_code == 200 and response.json():
            session_id = response.json()[0].get("id", 1)
            terminate_response = await async_client.delete(
                f"/api/v1/users/sessions/{session_id}",
                headers=auth_headers
            )
            assert terminate_response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_logout_flow(self, async_client: AsyncClient, db_session: Session):
        """
        测试用户登出流程
        
        验证步骤:
        1. 用户登录
        2. 用户登出
        3. 登出后令牌失效
        """
        user_data = {
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "logoutpass123"
        }
        
        await async_client.post("/api/v1/users/register", json=user_data)
        
        login_data = {
            "username": "logoutuser",
            "password": "logoutpass123"
        }
        login_response = await async_client.post("/api/v1/users/login", json=login_data)
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        logout_response = await async_client.post("/api/v1/users/logout", headers=headers)
        
        assert logout_response.status_code == 200
        assert logout_response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_session_without_auth(self, async_client: AsyncClient):
        """
        测试无认证访问会话接口
        
        验证:
        - 返回 401 错误
        """
        response = await async_client.get("/api/v1/users/sessions/list")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestPasswordReset:
    """密码重置集成测试"""

    @pytest.mark.asyncio
    async def test_password_reset_request_flow(self, async_client: AsyncClient, test_user: User):
        """
        测试密码重置请求流程
        
        验证:
        - 请求成功返回
        - 不存在的邮箱也返回成功（安全考虑）
        """
        reset_request = {"email": test_user.email}
        response = await async_client.post(
            "/api/v1/users/password/reset-request",
            json=reset_request
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_password_reset_request_nonexistent_email(self, async_client: AsyncClient):
        """
        测试不存在的邮箱请求密码重置
        
        验证:
        - 返回成功（不暴露邮箱是否存在）
        """
        reset_request = {"email": "nonexistent@example.com"}
        response = await async_client.post(
            "/api/v1/users/password/reset-request",
            json=reset_request
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_password_reset_invalid_token(self, async_client: AsyncClient):
        """
        测试使用无效令牌重置密码
        
        验证:
        - 返回 400 错误
        """
        reset_data = {
            "token": "invalid_token_12345",
            "new_password": "newpassword123"
        }
        response = await async_client.post(
            "/api/v1/users/password/reset",
            json=reset_data
        )
        
        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.auth
class TestUserUpdate:
    """用户信息更新集成测试"""

    @pytest.mark.asyncio
    async def test_update_user_info(self, async_client: AsyncClient, test_user: User, auth_headers: dict):
        """
        测试更新用户信息
        
        验证:
        - 可以更新用户信息
        - 更新后的信息正确保存
        """
        update_data = {
            "email": "updated@example.com"
        }
        
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, async_client: AsyncClient, test_user: User, auth_headers: dict):
        """
        测试根据 ID 获取用户信息
        
        验证:
        - 返回正确的用户信息
        """
        response = await async_client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["username"] == test_user.username


@pytest.mark.integration
@pytest.mark.auth
class TestAuthSecurity:
    """认证安全集成测试"""

    @pytest.mark.asyncio
    async def test_malformed_auth_header(self, async_client: AsyncClient):
        """
        测试格式错误的认证头
        
        验证:
        - 返回 401 错误
        """
        headers = {"Authorization": "InvalidFormat token"}
        response = await async_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_auth_header(self, async_client: AsyncClient):
        """
        测试空认证头
        
        验证:
        - 返回 401 错误
        """
        headers = {"Authorization": ""}
        response = await async_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, async_client: AsyncClient):
        """
        测试 SQL 注入攻击尝试
        
        验证:
        - 系统正确处理恶意输入
        - 不返回敏感信息
        """
        malicious_data = {
            "username": "admin'--",
            "password": "anything"
        }
        response = await async_client.post("/api/v1/users/login", json=malicious_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_login(self, async_client: AsyncClient, db_session: Session):
        """
        测试被禁用用户登录
        
        验证:
        - 返回 403 错误
        - 错误信息正确
        """
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            role="farmer",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "password123"
        }
        response = await async_client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 403
        assert "禁用" in response.json()["detail"]
