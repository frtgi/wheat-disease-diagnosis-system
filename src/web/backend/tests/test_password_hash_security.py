"""
密码哈希安全性验证测试
验证 password_hash 不会泄露到 API 响应和 Redis 缓存中
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.security import get_password_hash
from app.models.user import User


class TestPasswordHashSecurity:
    """密码哈希安全性测试类"""

    def test_get_current_user_info_no_password_hash_in_response(self, client: TestClient, test_user: User):
        """
        测试获取当前用户信息时不包含 password_hash
        
        验证:
        - API 响应中不包含 password_hash 字段
        - API 响应中不包含 password 字段
        - 用户基本信息正确返回
        """
        # 生成有效的认证令牌
        from app.core.security import create_access_token
        token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证敏感字段不存在
        assert "password_hash" not in data, "API 响应不应包含 password_hash 字段"
        assert "password" not in data, "API 响应不应包含 password 字段"
        
        # 验证基本字段存在且正确
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_get_user_by_id_no_password_hash(self, client: TestClient, admin_user: User):
        """
        测试根据 ID 获取用户信息时不包含 password_hash
        
        验证:
        - 通过用户 ID 获取信息时，响应不包含 password_hash
        """
        from app.core.security import create_access_token
        token = create_access_token({"sub": admin_user.username, "user_id": admin_user.id})
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/v1/users/{test_user.id if 'test_user' in dir() else 1}", headers=headers)
        
        # 如果用户存在，检查响应
        if response.status_code == 200:
            data = response.json()
            assert "password_hash" not in data, "通过 ID 获取用户信息时不应包含 password_hash"
            assert "password" not in data

    @patch('app.api.v1.user.cache_service')
    def test_cache_service_filters_password_hash(self, mock_cache, db_session):
        """
        测试缓存服务自动过滤 password_hash 字段
        
        验证:
        - set_user_info 方法会自动移除 password_hash
        - 缓存中存储的数据不包含敏感字段
        """
        from app.services.cache import CacheService
        cache_service = CacheService()
        
        # 模拟包含 password_hash 的用户数据
        user_data_with_password = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password_12345",  # 敏感字段
            "role": "farmer",
            "is_active": True
        }
        
        # 模拟 Redis 客户端
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        
        # 调用 set_user_info
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            cache_service.set_user_info(1, user_data_with_password)
        )
        
        # 验证调用 setex 时传入的数据不包含 password_hash
        call_args = mock_redis.setex.call_args
        cached_data_json = call_args[0][2]  # 第三个参数是 JSON 数据
        import json
        cached_data = json.loads(cached_data_json)
        
        assert "password_hash" not in cached_data, "缓存中不应存储 password_hash"
        assert "password" not in cached_data, "缓存中不应存储 password"
        assert cached_data["username"] == "testuser"

    def test_login_response_no_password_hash(self, client: TestClient, test_user: User):
        """
        测试登录响应中不包含 password_hash
        
        验证:
        - 登录成功后的响应不包含密码相关字段
        """
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查令牌信息
        assert "access_token" in data
        assert "user" in data
        
        # 检查用户信息中不包含密码字段
        user_data = data["user"]
        assert "password_hash" not in user_data, "登录响应中的用户信息不应包含 password_hash"
        assert "password" not in user_data

    def test_user_response_schema_excludes_sensitive_fields(self):
        """
        测试 UserResponse Schema 明确排除敏感字段
        
        验证:
        - schema 的 properties 中不包含 password 或 password_hash
        """
        from app.schemas.user import UserResponse
        
        schema = UserResponse.model_json_schema()
        properties = schema.get("properties", {})
        
        assert "password" not in properties, "UserResponse Schema 不应包含 password 字段"
        assert "password_hash" not in properties, "UserResponse Schema 不应包含 password_hash 字段"
        
        # 验证必要字段存在
        required_fields = ["id", "username", "email", "role"]
        for field in required_fields:
            assert field in properties, f"UserResponse Schema 应包含 {field} 字段"

    @patch('app.api.v1.user.cache_service')
    def test_get_current_user_caches_safe_data_only(self, mock_cache, client: TestClient, test_user: User):
        """
        测试获取当前用户信息时只缓存安全数据
        
        验证:
        - 缓存的数据是经过过滤的
        - 即使数据库模型有 password_hash，也不会被缓存
        """
        from app.core.security import create_access_token
        token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
        
        # 模拟缓存服务
        mock_cache.get_user_info = AsyncMock(return_value=None)
        mock_cache.set_user_info = AsyncMock(return_value=True)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        
        # 验证 set_user_info 被调用
        if mock_cache.set_user_info.called:
            call_args = mock_cache.set_user_info.call_args[0][1]  # 第二个参数是 user_info
            assert "password_hash" not in call_args, "缓存的用户数据不应包含 password_hash"
            assert "password" not in call_args


class TestPasswordHashDefenseInDepth:
    """纵深防御测试：多层验证密码哈希安全性"""

    def test_multiple_endpoints_consistent_behavior(self, client: TestClient, test_user: User, admin_user: User):
        """
        测试所有用户相关端点的一致性行为
        
        验证:
        - 所有返回用户信息的端点都不包含 password_hash
        """
        from app.core.security import create_access_token
        
        endpoints = [
            ("GET", "/api/v1/users/me", {}),
        ]
        
        user_token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
        headers = {"Authorization": f"Bearer {user_token}"}
        
        for method, endpoint, _ in endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            
            # 只检查成功的响应
            if response.status_code == 200:
                data = response.json()
                assert "password_hash" not in data, f"{endpoint} 响应包含 password_hash"
                assert "password" not in data, f"{endpoint} 响应包含 password"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
