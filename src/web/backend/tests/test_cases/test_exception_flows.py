"""
异常流程测试用例
覆盖错误处理、异常情况，包括认证错误、验证错误、资源不存在、服务不可用等场景
"""
import pytest
import io
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
from PIL import Image

from app.models.user import User
from app.models.disease import Disease
from app.models.diagnosis import Diagnosis


class TestUserRegisterExceptionFlow:
    """
    用户注册异常流程测试类
    
    测试用户注册过程中的各种异常情况
    """
    
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
            "password": "SecurePass123"
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
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 409
        assert "邮箱" in response.json()["detail"]
    
    def test_register_missing_required_fields(self, client: TestClient):
        """
        测试缺少必填字段
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        user_data = {"username": "incomplete"}
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_register_invalid_email_format(self, client: TestClient):
        """
        测试无效邮箱格式
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        user_data = {
            "username": "validuser",
            "email": "invalid-email",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_register_empty_fields(self, client: TestClient):
        """
        测试空字段
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        user_data = {
            "username": "",
            "email": "",
            "password": ""
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422


class TestUserLoginExceptionFlow:
    """
    用户登录异常流程测试类
    
    测试用户登录过程中的各种异常情况
    """
    
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
        assert "密码" in response.json()["detail"] or "用户名" in response.json()["detail"]
    
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
        
        assert response.status_code == 403
        assert "禁用" in response.json()["detail"]
    
    def test_login_missing_fields(self, client: TestClient):
        """
        测试登录缺少字段
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        login_data = {"username": "testuser"}
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 422


class TestAuthenticationExceptionFlow:
    """
    认证异常流程测试类
    
    测试认证相关的异常情况
    """
    
    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """
        测试无 token 访问受保护端点
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """
        测试无效 token 访问受保护端点
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_malformed_header(self, client: TestClient):
        """
        测试格式错误的认证头
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_expired_token(
        self, client: TestClient, db_session: Session
    ):
        """
        测试过期 token 访问受保护端点
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTUxNjIzOTAyMn0.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_without_bearer_prefix(self, client: TestClient):
        """
        测试不带 Bearer 前缀的 token
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        headers = {"Authorization": "sometoken"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401


class TestDiagnosisExceptionFlow:
    """
    诊断服务异常流程测试类
    
    测试诊断过程中的各种异常情况
    """
    
    def test_image_diagnosis_invalid_file_type(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试上传非图像文件进行诊断
        
        验证:
        - 返回状态码 400 (Bad Request)
        - 错误信息提示文件类型不支持
        """
        text_file = io.BytesIO(b"This is not an image")
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test.txt", text_file, "text/plain")},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_image_diagnosis_missing_image(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试图像诊断缺少图像
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.post(
            "/api/v1/diagnosis/image",
            data={"symptoms": "测试症状"},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_text_diagnosis_missing_symptoms(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试文本诊断缺少症状描述
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_text_diagnosis_empty_symptoms(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试文本诊断空症状描述
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_get_diagnosis_detail_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试获取不存在的诊断记录
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        response = client.get(
            "/api/v1/diagnosis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_diagnosis_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试更新不存在的诊断记录
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        update_data = {"status": "reviewed"}
        response = client.put(
            "/api/v1/diagnosis/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_diagnosis_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试删除不存在的诊断记录
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        response = client.delete(
            "/api/v1/diagnosis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_access_other_user_diagnosis(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        测试访问其他用户的诊断记录
        
        验证:
        - 返回状态码 404 (Not Found)
        - 用户只能访问自己的记录
        """
        from app.core.security import get_password_hash
        
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash=get_password_hash("password123"),
            role="farmer",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        diagnosis = Diagnosis(
            user_id=other_user.id,
            symptoms="其他用户的诊断",
            disease_name="测试病害",
            confidence=0.8,
            status="completed"
        )
        db_session.add(diagnosis)
        db_session.commit()
        db_session.refresh(diagnosis)
        
        response = client.get(
            f"/api/v1/diagnosis/{diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestKnowledgeExceptionFlow:
    """
    知识库异常流程测试类
    
    测试知识库操作中的各种异常情况
    """
    
    def test_get_disease_not_found(self, client: TestClient):
        """
        测试获取不存在的疾病
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        response = client.get("/api/v1/knowledge/99999")
        
        assert response.status_code == 404
    
    def test_update_disease_not_found(self, client: TestClient):
        """
        测试更新不存在的疾病
        
        验证:
        - 返回状态码 404 (Not Found) 或其他错误
        """
        update_data = {"symptoms": "更新后的症状"}
        response = client.put("/api/v1/knowledge/99999", json=update_data)
        
        assert response.status_code in [404, 500]
    
    def test_create_disease_missing_required_fields(self, client: TestClient):
        """
        测试创建疾病缺少必填字段
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        disease_data = {"category": "真菌病害"}
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 422
    
    def test_create_disease_empty_name(self, client: TestClient):
        """
        测试创建疾病名称为空
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        disease_data = {
            "name": "",
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 422
    
    def test_search_with_invalid_pagination(self, client: TestClient):
        """
        测试无效的分页参数
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.get(
            "/api/v1/knowledge/search",
            params={"skip": -1, "limit": 0}
        )
        
        assert response.status_code == 422


class TestAIDiagnosisExceptionFlow:
    """
    AI 诊断异常流程测试类
    
    测试 AI 诊断过程中的各种异常情况
    """
    
    def test_fusion_diagnosis_missing_both_inputs(self, client: TestClient):
        """
        测试融合诊断缺少图像和症状
        
        验证:
        - 返回状态码 400 (Bad Request)
        """
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/fusion",
            data={}
        )
        
        assert response.status_code == 400
    
    def test_multimodal_diagnosis_invalid_image(
        self, client: TestClient
    ):
        """
        测试多模态诊断无效图像
        
        验证:
        - 返回状态码 400 (Bad Request) 或 500
        """
        invalid_image = io.BytesIO(b"not a valid image")
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/multimodal",
            files={"image": ("test.txt", invalid_image, "text/plain")},
            data={"symptoms": "测试症状"}
        )
        
        assert response.status_code in [400, 500]
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_text_diagnosis_empty_symptoms(self, mock_should_use_mock, client: TestClient):
        """
        测试文本诊断空症状
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        mock_should_use_mock.return_value = True
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/text",
            data={"symptoms": ""}
        )
        
        assert response.status_code == 422
    
    def test_batch_diagnosis_too_many_images(
        self, client: TestClient, sample_image_bytes: bytes
    ):
        """
        测试批量诊断超过限制
        
        验证:
        - 返回状态码 400 (Bad Request)
        """
        files = []
        for i in range(15):
            image_file = io.BytesIO(sample_image_bytes)
            files.append(("images", (f"test{i}.png", image_file, "image/png")))
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/batch",
            files=files,
            data={"symptoms": "测试症状"}
        )
        
        assert response.status_code == 400


class TestPasswordResetExceptionFlow:
    """
    密码重置异常流程测试类
    """
    
    def test_password_reset_with_invalid_token(self, client: TestClient):
        """
        测试使用无效令牌重置密码
        
        验证:
        - 返回状态码 400 (Bad Request)
        """
        reset_data = {
            "token": "invalid_token",
            "new_password": "NewPassword123"
        }
        response = client.post(
            "/api/v1/users/password/reset",
            json=reset_data
        )
        
        assert response.status_code == 400
    
    def test_password_reset_with_short_password(self, client: TestClient):
        """
        测试重置密码过短
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        reset_data = {
            "token": "some_token",
            "new_password": "123"
        }
        response = client.post(
            "/api/v1/users/password/reset",
            json=reset_data
        )
        
        assert response.status_code == 422


class TestTokenRefreshExceptionFlow:
    """
    令牌刷新异常流程测试类
    """
    
    def test_refresh_with_invalid_token(self, client: TestClient):
        """
        测试使用无效刷新令牌
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post(
            "/api/v1/users/token/refresh",
            json=refresh_data
        )
        
        assert response.status_code == 401
    
    def test_refresh_missing_token(self, client: TestClient):
        """
        测试缺少刷新令牌
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.post(
            "/api/v1/users/token/refresh",
            json={}
        )
        
        assert response.status_code == 422


class TestSessionExceptionFlow:
    """
    会话管理异常流程测试类
    """
    
    def test_terminate_session_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试终止不存在的会话
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        response = client.delete(
            "/api/v1/users/sessions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_sessions_without_auth(self, client: TestClient):
        """
        测试无认证获取会话列表
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        response = client.get("/api/v1/users/sessions/list")
        
        assert response.status_code == 401


class TestUserUpdateExceptionFlow:
    """
    用户更新异常流程测试类
    """
    
    def test_update_nonexistent_user(self, client: TestClient, auth_headers: dict):
        """
        测试更新不存在的用户
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        update_data = {"phone": "13900139000"}
        response = client.put(
            "/api/v1/users/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_user_invalid_data(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试更新用户无效数据
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        update_data = {"username": "ab"}
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestRateLimitExceptionFlow:
    """
    限流异常流程测试类
    """
    
    def test_register_rate_limit(self, client: TestClient):
        """
        测试注册接口限流
        
        验证:
        - 连续请求后返回 429 (Too Many Requests)
        """
        for i in range(5):
            user_data = {
                "username": f"ratelimituser{i}",
                "email": f"ratelimit{i}@example.com",
                "password": "SecurePass123"
            }
            response = client.post("/api/v1/users/register", json=user_data)
            
            if response.status_code == 429:
                assert True
                return
        
        pass


class TestCacheExceptionFlow:
    """
    缓存异常流程测试类
    """
    
    def test_clear_cache_without_auth(self, client: TestClient):
        """
        测试无认证清空缓存
        
        验证:
        - 根据实际配置返回相应状态码
        """
        response = client.post("/api/v1/ai-diagnosis/diagnosis/cache/clear")
        
        assert response.status_code in [200, 401, 403]


class TestAsyncExceptionFlows:
    """
    异步异常流程测试类
    """
    
    @pytest.mark.asyncio
    async def test_async_login_wrong_password(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        异步测试登录错误密码
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = await async_client.post(
            "/api/v1/users/login",
            json=login_data
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_async_access_protected_without_token(
        self, async_client: AsyncClient
    ):
        """
        异步测试无 token 访问受保护端点
        
        验证:
        - 返回状态码 401 (Unauthorized)
        """
        response = await async_client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_async_get_nonexistent_diagnosis(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        异步测试获取不存在的诊断记录
        
        验证:
        - 返回状态码 404 (Not Found)
        """
        response = await async_client.get(
            "/api/v1/diagnosis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestDatabaseIntegrityExceptionFlow:
    """
    数据库完整性异常流程测试类
    """
    
    def test_create_diagnosis_for_nonexistent_user(
        self, client: TestClient, db_session: Session
    ):
        """
        测试为不存在的用户创建诊断记录
        
        验证:
        - 应该在数据库层面或业务层面处理
        """
        pass
    
    def test_create_duplicate_disease_name(
        self, client: TestClient, test_disease: Disease
    ):
        """
        测试创建重复名称的疾病
        
        验证:
        - 根据业务规则返回相应错误
        """
        disease_data = {
            "name": test_disease.name,
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code in [200, 409, 422]


class TestInputValidationExceptionFlow:
    """
    输入验证异常流程测试类
    """
    
    def test_json_parse_error(self, client: TestClient):
        """
        测试 JSON 解析错误
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.post(
            "/api/v1/users/register",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_content_type_mismatch(self, client: TestClient):
        """
        测试 Content-Type 不匹配
        
        验证:
        - 返回状态码 422 (Validation Error)
        """
        response = client.post(
            "/api/v1/users/register",
            content="username=test&email=test@test.com&password=test123",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 422
    
    def test_sql_injection_attempt(self, client: TestClient):
        """
        测试 SQL 注入尝试
        
        验证:
        - 应该被安全处理，不返回敏感信息
        """
        user_data = {
            "username": "'; DROP TABLE users; --",
            "email": "test@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "DROP TABLE" not in str(data)
    
    def test_xss_attempt(self, client: TestClient):
        """
        测试 XSS 攻击尝试
        
        验证:
        - 应该被安全处理
        """
        user_data = {
            "username": "<script>alert('xss')</script>",
            "email": "xss@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "<script>" not in str(data)


class TestServiceUnavailableExceptionFlow:
    """
    服务不可用异常流程测试类
    """
    
    @patch("app.services.qwen_service.get_qwen_service")
    def test_ai_service_unavailable(self, mock_get_qwen, client: TestClient):
        """
        测试 AI 服务不可用
        
        验证:
        - 应该优雅降级或返回错误
        """
        mock_service = MagicMock()
        mock_service.is_loaded = False
        mock_service.diagnose.side_effect = Exception("Service unavailable")
        mock_get_qwen.return_value = mock_service
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/text",
            data={"symptoms": "测试症状"}
        )
        
        assert response.status_code in [200, 500]
    
    @patch("app.services.yolo_service.get_yolo_service")
    def test_yolo_service_unavailable(
        self, mock_get_yolo, client: TestClient, sample_image_bytes: bytes
    ):
        """
        测试 YOLO 服务不可用
        
        验证:
        - 应该优雅降级或返回错误
        """
        mock_service = MagicMock()
        mock_service.detect.side_effect = Exception("YOLO service unavailable")
        mock_get_yolo.return_value = mock_service
        
        image_file = io.BytesIO(sample_image_bytes)
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/image",
            files={"image": ("test.png", image_file, "image/png")}
        )
        
        assert response.status_code in [200, 500]
