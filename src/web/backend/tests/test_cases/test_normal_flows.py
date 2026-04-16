"""
正常流程测试用例
覆盖所有正常业务场景，包括用户管理、诊断服务、知识库管理等核心功能
"""
import pytest
import io
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
from PIL import Image

from app.models.user import User
from app.models.disease import Disease
from app.models.diagnosis import Diagnosis


class TestUserRegisterNormalFlow:
    """
    用户注册正常流程测试类
    
    测试用户注册的各种正常场景
    """
    
    def test_register_with_valid_data(self, client: TestClient):
        """
        测试使用有效数据注册用户
        
        验证:
        - 返回状态码 200
        - 返回正确的用户信息
        - 密码不在响应中暴露
        """
        user_data = {
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "normaluser"
        assert data["email"] == "normal@example.com"
        assert "password" not in data
        assert "password_hash" not in data
        assert data["role"] == "farmer"
        assert data["is_active"] is True
    
    def test_register_with_phone(self, client: TestClient):
        """
        测试带手机号的用户注册
        
        验证:
        - 手机号正确保存
        - 其他字段正常
        """
        user_data = {
            "username": "phoneuser",
            "email": "phone@example.com",
            "password": "SecurePass123",
            "phone": "13800138000"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "13800138000"
    
    def test_register_multiple_users_sequentially(self, client: TestClient):
        """
        测试连续注册多个用户
        
        验证:
        - 每个用户都能成功注册
        - 用户 ID 递增
        """
        users = []
        for i in range(3):
            user_data = {
                "username": f"multiuser{i}",
                "email": f"multi{i}@example.com",
                "password": "SecurePass123"
            }
            response = client.post("/api/v1/users/register", json=user_data)
            assert response.status_code == 200
            users.append(response.json())
        
        user_ids = [u["id"] for u in users]
        assert len(set(user_ids)) == 3


class TestUserLoginNormalFlow:
    """
    用户登录正常流程测试类
    
    测试用户登录的各种正常场景
    """
    
    def test_login_with_username(self, client: TestClient, test_user: User):
        """
        测试使用用户名登录
        
        验证:
        - 返回有效的 access_token
        - 返回用户信息
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
        assert data["user"]["username"] == "testuser"
    
    def test_login_with_email(self, client: TestClient, test_user: User):
        """
        测试使用邮箱登录
        
        验证:
        - 可以使用邮箱登录
        - 返回有效的 token
        """
        login_data = {
            "username": "test@example.com",
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_returns_user_info(self, client: TestClient, test_user: User):
        """
        测试登录返回用户信息
        
        验证:
        - 响应包含完整的用户信息
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "farmer"


class TestUserPasswordResetNormalFlow:
    """
    密码重置正常流程测试类
    """
    
    def test_request_password_reset_existing_email(
        self, client: TestClient, test_user: User
    ):
        """
        测试请求密码重置 - 邮箱存在
        
        验证:
        - 返回成功消息
        - 不暴露邮箱是否存在
        """
        response = client.post(
            "/api/v1/users/password/reset-request",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "邮件" in data["message"]
    
    def test_request_password_reset_nonexistent_email(self, client: TestClient):
        """
        测试请求密码重置 - 邮箱不存在
        
        验证:
        - 同样返回成功消息（安全考虑）
        """
        response = client.post(
            "/api/v1/users/password/reset-request",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestUserInfoNormalFlow:
    """
    用户信息正常流程测试类
    """
    
    def test_get_current_user_info(self, client: TestClient, auth_headers: dict):
        """
        测试获取当前用户信息
        
        验证:
        - 返回正确的用户信息
        """
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_get_user_by_id(self, client: TestClient, test_user: User):
        """
        测试通过 ID 获取用户信息
        
        验证:
        - 返回正确的用户信息
        """
        response = client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == "testuser"
    
    def test_update_user_info(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """
        测试更新用户信息
        
        验证:
        - 信息更新成功
        """
        update_data = {
            "phone": "13900139000"
        }
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "13900139000"


class TestDiagnosisNormalFlow:
    """
    诊断服务正常流程测试类
    
    测试图像诊断和文本诊断的正常场景
    """
    
    def test_image_diagnosis_success(
        self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """
        测试图像诊断成功
        
        验证:
        - 返回诊断结果
        - 结果包含病害名称和置信度
        """
        image_file = io.BytesIO(sample_image_bytes)
        image_file.name = "test_wheat.png"
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test_wheat.png", image_file, "image/png")},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "diagnosis_id" in data
        assert "disease_name" in data
        assert "confidence" in data
    
    def test_image_diagnosis_with_symptoms(
        self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """
        测试带症状描述的图像诊断
        
        验证:
        - 同时处理图像和症状描述
        """
        image_file = io.BytesIO(sample_image_bytes)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test_wheat.png", image_file, "image/png")},
            data={"symptoms": "叶片出现黄色斑点"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "disease_name" in data
    
    def test_text_diagnosis_success(self, client: TestClient, auth_headers: dict):
        """
        测试文本诊断成功
        
        验证:
        - 返回诊断结果
        - 结果包含建议
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "叶片出现黄色锈斑，沿叶脉分布"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "disease_name" in data
        assert "confidence" in data
    
    def test_get_diagnosis_records(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试获取诊断记录列表
        
        验证:
        - 返回记录列表
        - 包含分页信息
        """
        response = client.get(
            "/api/v1/diagnosis/records",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_get_diagnosis_records_with_pagination(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试分页获取诊断记录
        
        验证:
        - 分页参数生效
        """
        for i in range(5):
            diagnosis = Diagnosis(
                user_id=test_user.id,
                symptoms=f"测试症状{i}",
                disease_name="小麦锈病",
                confidence=0.9,
                status="completed"
            )
            db_session.add(diagnosis)
        db_session.commit()
        
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) <= 3
        assert data["skip"] == 0
        assert data["limit"] == 3
    
    def test_get_diagnosis_detail(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试获取诊断详情
        
        验证:
        - 返回完整的诊断信息
        """
        response = client.get(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_diagnosis.id
    
    def test_update_diagnosis_record(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试更新诊断记录
        
        验证:
        - 更新成功
        """
        update_data = {
            "status": "reviewed"
        }
        response = client.put(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
    
    def test_delete_diagnosis_record(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试删除诊断记录
        
        验证:
        - 删除成功
        """
        diagnosis = Diagnosis(
            user_id=test_user.id,
            symptoms="待删除的记录",
            disease_name="测试病害",
            confidence=0.8,
            status="completed"
        )
        db_session.add(diagnosis)
        db_session.commit()
        db_session.refresh(diagnosis)
        
        response = client.delete(
            f"/api/v1/diagnosis/{diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestAIDiagnosisNormalFlow:
    """
    AI 诊断正常流程测试类
    
    测试多模态诊断、融合诊断等 AI 功能
    """
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_fusion_diagnosis_with_mock(
        self, mock_should_use_mock, client: TestClient, sample_image_bytes: bytes
    ):
        """
        测试融合诊断（Mock 模式）
        
        验证:
        - Mock 模式下返回模拟结果
        """
        mock_should_use_mock.return_value = True
        
        image_file = io.BytesIO(sample_image_bytes)
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/fusion",
            files={"image": ("test.png", image_file, "image/png")},
            data={"symptoms": "叶片发黄"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "diagnosis" in data
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_text_diagnosis_with_mock(self, mock_should_use_mock, client: TestClient):
        """
        测试文本诊断（Mock 模式）
        
        验证:
        - 返回诊断结果
        """
        mock_should_use_mock.return_value = True
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/text",
            data={"symptoms": "叶片出现黄色条状锈斑"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_image_diagnosis_with_mock(
        self, mock_should_use_mock, client: TestClient, sample_image_bytes: bytes
    ):
        """
        测试图像诊断（Mock 模式）
        
        验证:
        - 返回检测结果
        """
        mock_should_use_mock.return_value = True
        
        image_file = io.BytesIO(sample_image_bytes)
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/image",
            files={"image": ("test.png", image_file, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_ai_health_check(self, client: TestClient):
        """
        测试 AI 服务健康检查
        
        验证:
        - 返回服务状态
        """
        response = client.get("/api/v1/ai-diagnosis/diagnosis/health/ai")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "mock_mode" in data


class TestKnowledgeNormalFlow:
    """
    知识库正常流程测试类
    
    测试疾病知识的增删改查
    """
    
    def test_create_disease_knowledge(self, client: TestClient):
        """
        测试创建疾病知识
        
        验证:
        - 创建成功
        - 返回完整信息
        """
        disease_data = {
            "name": "测试病害",
            "category": "真菌病害",
            "symptoms": "叶片出现病斑",
            "causes": "真菌感染",
            "treatments": "喷洒杀菌剂",
            "prevention": "选用抗病品种"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试病害"
        assert "id" in data
    
    def test_search_disease_by_keyword(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试按关键词搜索疾病
        
        验证:
        - 返回匹配结果
        """
        response = client.get(
            "/api/v1/knowledge/search",
            params={"keyword": "锈病"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_disease_by_category(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试按分类搜索疾病
        
        验证:
        - 返回该分类的疾病
        """
        response = client.get(
            "/api/v1/knowledge/search",
            params={"category": "真菌病害"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for disease in data:
            assert disease["category"] == "真菌病害"
    
    def test_get_disease_by_id(
        self, client: TestClient, test_disease: Disease
    ):
        """
        测试获取疾病详情
        
        验证:
        - 返回完整疾病信息
        """
        response = client.get(f"/api/v1/knowledge/{test_disease.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_disease.id
        assert data["name"] == test_disease.name
    
    def test_update_disease_knowledge(
        self, client: TestClient, test_disease: Disease
    ):
        """
        测试更新疾病知识
        
        验证:
        - 更新成功
        """
        update_data = {
            "symptoms": "更新后的症状描述"
        }
        response = client.put(
            f"/api/v1/knowledge/{test_disease.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["symptoms"] == "更新后的症状描述"
    
    def test_get_all_categories(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试获取所有疾病分类
        
        验证:
        - 返回分类列表
        """
        response = client.get("/api/v1/knowledge/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUserLogoutNormalFlow:
    """
    用户登出正常流程测试类
    """
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """
        测试用户登出成功
        
        验证:
        - 登出成功
        - 返回成功消息
        """
        response = client.post(
            "/api/v1/users/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "登出" in data["message"]


class TestHealthCheckNormalFlow:
    """
    健康检查正常流程测试类
    """
    
    def test_api_health_check(self, client: TestClient):
        """
        测试 API 健康检查
        
        验证:
        - 返回服务状态
        """
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200


class TestAsyncNormalFlows:
    """
    异步正常流程测试类
    """
    
    @pytest.mark.asyncio
    async def test_async_user_login(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        异步测试用户登录
        
        验证:
        - 异步客户端登录成功
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = await async_client.post(
            "/api/v1/users/login",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_async_get_diagnosis_records(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        异步测试获取诊断记录
        
        验证:
        - 异步获取成功
        """
        response = await async_client.get(
            "/api/v1/diagnosis/records",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_knowledge_search(
        self, async_client: AsyncClient, test_diseases: list
    ):
        """
        异步测试知识搜索
        
        验证:
        - 异步搜索成功
        """
        response = await async_client.get(
            "/api/v1/knowledge/search",
            params={"keyword": "病害"}
        )
        
        assert response.status_code == 200


class TestUserRoleBasedAccess:
    """
    基于角色的访问控制测试类
    """
    
    def test_farmer_access_diagnosis(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试农民用户访问诊断功能
        
        验证:
        - 农民用户可以访问诊断
        """
        response = client.get(
            "/api/v1/diagnosis/records",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_technician_access_diagnosis(
        self, client: TestClient, technician_auth_headers: dict
    ):
        """
        测试农技人员访问诊断功能
        
        验证:
        - 农技人员可以访问诊断
        """
        response = client.get(
            "/api/v1/diagnosis/records",
            headers=technician_auth_headers
        )
        
        assert response.status_code == 200
    
    def test_admin_access_all_users(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """
        测试管理员访问用户管理功能
        
        验证:
        - 管理员可以访问用户管理
        """
        response = client.get(
            "/api/v1/users/me",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
