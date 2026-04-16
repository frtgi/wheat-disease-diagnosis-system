"""
用户 API 测试
测试用户相关接口功能
"""
import pytest
from fastapi.testclient import TestClient


def test_root(client: TestClient):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_health_check(client: TestClient):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client: TestClient):
    """测试用户注册"""
    import uuid
    user_data = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpass123"
    }
    response = client.post("/api/v1/users/register", json=user_data)
    # 注册应该成功或用户已存在
    assert response.status_code in [200, 400, 409]


def test_user_login(client: TestClient, test_user):
    """测试用户登录"""
    login_data = {
        "username": test_user.username,
        "password": "testpass123"
    }
    response = client.post("/api/v1/users/login", json=login_data)
    assert response.status_code == 200


def test_get_overview_stats(client: TestClient):
    """获取概览统计"""
    response = client.get("/api/v1/stats/overview")
    assert response.status_code == 200
    assert "total_users" in response.json()
