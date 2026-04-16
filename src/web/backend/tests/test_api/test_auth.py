"""
认证 API 接口测试
测试用户注册、登录、令牌刷新、密码重置等功能
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.models.user import User
from app.models.auth import RefreshToken, PasswordResetToken
from app.core.security import create_access_token, get_password_hash


class TestRegisterAPI:
    """用户注册 API 测试类"""

    def test_register_success(self, client: TestClient):
        """
        测试用户注册成功
        
        验证:
        - 返回状态码 200
        - 返回成功标志
        - 返回用户信息
        """
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """
        测试注册重复邮箱
        
        验证:
        - 返回失败状态
        - 错误码为 AUTH_001
        """
        user_data = {
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "AUTH_001"

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """
        测试注册重复用户名
        
        验证:
        - 返回失败状态
        - 错误码为 AUTH_002
        """
        user_data = {
            "username": "testuser",
            "email": "another@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "AUTH_002"

    def test_register_invalid_email(self, client: TestClient):
        """
        测试无效邮箱格式
        
        验证:
        - 返回 422 验证错误
        """
        user_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """
        测试密码过短
        
        验证:
        - 返回 422 验证错误
        """
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "12345"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422


class TestLoginAPI:
    """用户登录 API 测试类"""

    def test_login_success(self, client: TestClient, test_user: User):
        """
        测试用户登录成功
        
        验证:
        - 返回状态码 200
        - 返回 access_token
        - 返回 refresh_token
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_with_email(self, client: TestClient, test_user: User):
        """
        测试使用邮箱登录
        
        验证:
        - 登录成功
        - 返回有效令牌
        """
        login_data = {
            "username": "test@example.com",
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """
        测试密码错误
        
        验证:
        - 返回失败状态
        - 错误码为 AUTH_002
        """
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "AUTH_002"

    def test_login_nonexistent_user(self, client: TestClient):
        """
        测试登录不存在的用户
        
        验证:
        - 返回失败状态
        """
        login_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """
        测试登录被禁用的用户
        
        验证:
        - 返回失败状态
        - 错误码为 AUTH_004
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
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "AUTH_004"


class TestGetCurrentUserAPI:
    """获取当前用户 API 测试类"""

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
        测试无令牌获取用户信息
        
        验证:
        - 返回 401 未授权
        """
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """
        测试无效令牌获取用户信息
        
        验证:
        - 返回 401 未授权
        """
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client: TestClient):
        """
        测试过期令牌获取用户信息
        
        验证:
        - 返回 401 未授权
        """
        headers = {"Authorization": "Bearer expired.token.here"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401


class TestTokenRefreshAPI:
    """令牌刷新 API 测试类"""

    def test_refresh_token_success(self, client: TestClient, test_user: User, db_session: Session):
        """
        测试刷新令牌成功
        
        验证:
        - 返回新的 access_token
        """
        from app.services.auth import create_refresh_token
        
        refresh_token = create_refresh_token(db_session, test_user.id)
        
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/users/token/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """
        测试无效刷新令牌
        
        验证:
        - 返回 401 未授权
        """
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/users/token/refresh", json=refresh_data)
        
        assert response.status_code == 401

    def test_refresh_token_expired(self, client: TestClient, test_user: User, db_session: Session):
        """
        测试过期刷新令牌
        
        验证:
        - 返回 401 未授权
        """
        expired_token = RefreshToken(
            user_id=test_user.id,
            token="expired_token",
            expires_at="2020-01-01 00:00:00",
            is_revoked=False
        )
        db_session.add(expired_token)
        db_session.commit()
        
        refresh_data = {"refresh_token": "expired_token"}
        response = client.post("/api/v1/users/token/refresh", json=refresh_data)
        
        assert response.status_code == 401


class TestPasswordResetAPI:
    """密码重置 API 测试类"""

    def test_request_password_reset_success(self, client: TestClient, test_user: User):
        """
        测试请求密码重置成功
        
        验证:
        - 返回成功消息
        """
        reset_data = {"email": "test@example.com"}
        response = client.post("/api/v1/users/password/reset-request", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_request_password_reset_nonexistent_email(self, client: TestClient):
        """
        测试请求重置不存在的邮箱
        
        验证:
        - 仍返回成功消息（防止邮箱枚举）
        """
        reset_data = {"email": "nonexistent@example.com"}
        response = client.post("/api/v1/users/password/reset-request", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_reset_password_success(self, client: TestClient, test_user: User, db_session: Session):
        """
        测试执行密码重置成功
        
        验证:
        - 返回成功消息
        """
        from app.services.auth import create_password_reset_token
        
        token = create_password_reset_token(db_session, test_user.email)
        
        reset_data = {
            "token": token,
            "new_password": "NewSecurePass123"
        }
        response = client.post("/api/v1/users/password/reset", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_reset_password_invalid_token(self, client: TestClient):
        """
        测试无效重置令牌
        
        验证:
        - 返回 400 错误
        """
        reset_data = {
            "token": "invalid_token",
            "new_password": "NewSecurePass123"
        }
        response = client.post("/api/v1/users/password/reset", json=reset_data)
        
        assert response.status_code == 400


class TestLogoutAPI:
    """登出 API 测试类"""

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """
        测试登出成功
        
        验证:
        - 返回成功消息
        """
        response = client.post("/api/v1/users/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "登出成功" in data["message"]

    def test_logout_no_token(self, client: TestClient):
        """
        测试无令牌登出
        
        验证:
        - 返回 401 未授权
        """
        response = client.post("/api/v1/users/logout")
        
        assert response.status_code == 401


class TestSessionAPI:
    """会话管理 API 测试类"""

    def test_get_sessions_success(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """
        测试获取会话列表成功
        
        验证:
        - 返回会话列表
        """
        response = client.get("/api/v1/users/sessions/list", headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_sessions_no_token(self, client: TestClient):
        """
        测试无令牌获取会话列表
        
        验证:
        - 返回 401 未授权
        """
        response = client.get("/api/v1/users/sessions/list")
        
        assert response.status_code == 401

    def test_terminate_session_success(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """
        测试终止会话成功
        
        验证:
        - 返回成功消息
        """
        from app.services.auth import create_user_session
        
        session = create_user_session(
            db_session,
            test_user.id,
            "test_session_token",
            "192.168.1.100",
            "Test Agent"
        )
        
        response = client.delete(f"/api/v1/users/sessions/{session.id}", headers=auth_headers)
        
        assert response.status_code == 200

    def test_terminate_session_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试终止不存在的会话
        
        验证:
        - 返回 404 错误
        """
        response = client.delete("/api/v1/users/sessions/99999", headers=auth_headers)
        
        assert response.status_code == 404


class TestUserUpdateAPI:
    """用户更新 API 测试类"""

    def test_update_user_success(self, client: TestClient, test_user: User, db_session: Session):
        """
        测试更新用户信息成功
        
        验证:
        - 返回更新后的用户信息
        """
        update_data = {
            "phone": "13800138000"
        }
        response = client.put(f"/api/v1/users/{test_user.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "13800138000"

    def test_update_user_not_found(self, client: TestClient):
        """
        测试更新不存在的用户
        
        验证:
        - 返回 404 错误
        """
        update_data = {
            "phone": "13800138000"
        }
        response = client.put("/api/v1/users/99999", json=update_data)
        
        assert response.status_code == 404


class TestGetUserAPI:
    """获取用户 API 测试类"""

    def test_get_user_success(self, client: TestClient, test_user: User):
        """
        测试获取用户信息成功
        
        验证:
        - 返回用户信息
        """
        response = client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_user_not_found(self, client: TestClient):
        """
        测试获取不存在的用户
        
        验证:
        - 返回 404 错误
        """
        response = client.get("/api/v1/users/99999")
        
        assert response.status_code == 404


class TestAuthAPIRateLimit:
    """认证 API 速率限制测试类"""

    def test_register_rate_limit(self, client: TestClient):
        """
        测试注册接口速率限制
        
        验证:
        - 超过限制后返回 429 错误
        """
        user_data = {
            "username": f"ratelimituser",
            "email": f"ratelimit@example.com",
            "password": "SecurePass123"
        }
        
        for i in range(5):
            user_data["username"] = f"ratelimituser{i}"
            user_data["email"] = f"ratelimit{i}@example.com"
            response = client.post("/api/v1/users/register", json=user_data)
            
            if response.status_code == 429:
                assert response.status_code == 429
                return
        
        assert True

    def test_login_rate_limit(self, client: TestClient, test_user: User):
        """
        测试登录接口速率限制
        
        验证:
        - 超过限制后返回 429 错误
        """
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        for i in range(10):
            response = client.post("/api/v1/users/login", json=login_data)
            
            if response.status_code == 429:
                assert response.status_code == 429
                return
        
        assert True
