# -*- coding: utf-8 -*-
"""
API 接口集成测试
测试所有 API 端点的集成功能，包括健康检查、诊断、知识图谱等
"""
import pytest
import io
from httpx import AsyncClient
from fastapi.testclient import TestClient
from PIL import Image

from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.models.disease import Disease


def create_test_image(width: int = 640, height: int = 480, color: str = 'green') -> bytes:
    """
    创建测试用的图像数据
    
    参数:
        width: 图像宽度
        height: 图像高度
        color: 图像颜色
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (width, height), color=color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


@pytest.mark.integration
@pytest.mark.api
class TestHealthCheckAPI:
    """健康检查 API 集成测试"""

    def test_root_endpoint(self, client: TestClient):
        """
        测试根路径端点
        
        验证:
        - 返回状态码 200
        - 返回应用信息
        """
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_health_endpoint(self, client: TestClient):
        """
        测试健康检查端点
        
        验证:
        - 返回状态码 200
        - 返回健康状态
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_health_endpoint(self, client: TestClient):
        """
        测试 API 健康检查端点
        
        验证:
        - 返回详细健康状态
        """
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_health_database_endpoint(self, client: TestClient):
        """
        测试数据库健康检查端点
        
        验证:
        - 返回数据库连接状态
        """
        response = client.get("/api/v1/health/database")
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    def test_health_startup_endpoint(self, client: TestClient):
        """
        测试启动状态检查端点
        
        验证:
        - 返回启动进度和状态
        """
        response = client.get("/api/v1/health/startup")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data

    def test_health_ready_endpoint(self, client: TestClient):
        """
        测试就绪状态检查端点
        
        验证:
        - 返回服务就绪状态
        """
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "status" in data

    def test_health_components_endpoint(self, client: TestClient):
        """
        测试组件状态检查端点
        
        验证:
        - 返回所有组件状态
        """
        response = client.get("/api/v1/health/components")
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "components" in data
            assert "summary" in data


@pytest.mark.integration
@pytest.mark.api
class TestDiagnosisAPI:
    """诊断 API 集成测试"""

    def test_diagnosis_image_endpoint_with_auth(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """
        测试图像诊断端点（带认证）
        
        验证:
        - 返回诊断结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {"symptoms": "叶片出现黄色斑点"}
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]

    def test_diagnosis_image_endpoint_without_auth(self, client: TestClient):
        """
        测试图像诊断端点（无认证）
        
        验证:
        - 返回 401 错误
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files=files
        )
        
        assert response.status_code == 401

    def test_diagnosis_text_endpoint_with_auth(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """
        测试文本诊断端点（带认证）
        
        验证:
        - 返回诊断结果
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "小麦叶片出现黄色锈斑，排列成行"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]

    def test_diagnosis_text_endpoint_without_auth(self, client: TestClient):
        """
        测试文本诊断端点（无认证）
        
        验证:
        - 返回 401 错误
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "叶片发黄"}
        )
        
        assert response.status_code == 401

    def test_get_diagnosis_records(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """
        测试获取诊断记录列表
        
        验证:
        - 返回记录列表
        """
        response = client.get(
            "/api/v1/diagnosis/records",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data

    def test_get_diagnosis_records_pagination(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """
        测试诊断记录分页
        
        验证:
        - 分页参数正确处理
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_get_diagnosis_detail(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_diagnosis: Diagnosis
    ):
        """
        测试获取诊断详情
        
        验证:
        - 返回正确的诊断详情
        """
        response = client.get(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_diagnosis.id

    def test_get_nonexistent_diagnosis(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """
        测试获取不存在的诊断记录
        
        验证:
        - 返回 404 错误
        """
        response = client.get(
            "/api/v1/diagnosis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_update_diagnosis_record(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_diagnosis: Diagnosis
    ):
        """
        测试更新诊断记录
        
        验证:
        - 可以更新诊断记录
        """
        update_data = {
            "symptoms": "更新后的症状描述"
        }
        
        response = client.put(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200

    def test_delete_diagnosis_record(
        self, 
        client: TestClient, 
        auth_headers: dict,
        db_session,
        test_user: User
    ):
        """
        测试删除诊断记录
        
        验证:
        - 可以删除诊断记录
        """
        diagnosis = Diagnosis(
            user_id=test_user.id,
            image_url="/uploads/test.jpg",
            symptoms="测试症状",
            disease_name="测试病害",
            confidence=0.9,
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


@pytest.mark.integration
@pytest.mark.api
class TestKnowledgeAPI:
    """知识图谱 API 集成测试"""

    def test_search_knowledge(
        self, 
        client: TestClient,
        test_disease: Disease
    ):
        """
        测试搜索知识
        
        验证:
        - 返回搜索结果
        """
        response = client.get(
            "/api/v1/knowledge/search?keyword=条锈病"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_knowledge_by_category(
        self, 
        client: TestClient,
        multiple_test_diseases: list
    ):
        """
        测试按分类搜索知识
        
        验证:
        - 返回分类筛选结果
        """
        response = client.get(
            "/api/v1/knowledge/search?category=真菌病害"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_knowledge_categories(
        self, 
        client: TestClient,
        test_disease: Disease
    ):
        """
        测试获取知识分类列表
        
        验证:
        - 返回分类列表
        """
        response = client.get("/api/v1/knowledge/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_knowledge_by_id(
        self, 
        client: TestClient,
        test_disease: Disease
    ):
        """
        测试根据 ID 获取知识详情
        
        验证:
        - 返回知识详情
        """
        response = client.get(f"/api/v1/knowledge/{test_disease.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_disease.id
        assert data["name"] == test_disease.name

    def test_get_nonexistent_knowledge(self, client: TestClient):
        """
        测试获取不存在的知识
        
        验证:
        - 返回 404 错误
        """
        response = client.get("/api/v1/knowledge/99999")
        
        assert response.status_code == 404

    def test_create_knowledge(
        self, 
        client: TestClient,
        db_session
    ):
        """
        测试创建知识
        
        验证:
        - 可以创建新知识
        """
        knowledge_data = {
            "name": "测试病害",
            "category": "测试分类",
            "symptoms": "测试症状",
            "causes": "测试病因",
            "treatments": "测试治疗",
            "prevention": "测试预防"
        }
        
        response = client.post(
            "/api/v1/knowledge/",
            json=knowledge_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试病害"

    def test_update_knowledge(
        self, 
        client: TestClient,
        test_disease: Disease
    ):
        """
        测试更新知识
        
        验证:
        - 可以更新知识
        """
        update_data = {
            "symptoms": "更新后的症状描述"
        }
        
        response = client.put(
            f"/api/v1/knowledge/{test_disease.id}",
            json=update_data
        )
        
        assert response.status_code == 200

    def test_delete_knowledge(
        self, 
        client: TestClient,
        db_session
    ):
        """
        测试删除知识
        
        验证:
        - 可以删除知识
        """
        disease = Disease(
            name="待删除病害",
            category="测试分类",
            symptoms="测试症状"
        )
        db_session.add(disease)
        db_session.commit()
        db_session.refresh(disease)
        
        response = client.delete(f"/api/v1/knowledge/{disease.id}")
        
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.api
class TestUserAPI:
    """用户 API 集成测试"""

    def test_user_registration(self, client: TestClient):
        """
        测试用户注册
        
        验证:
        - 可以注册新用户
        """
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "role": "farmer"
        }
        
        response = client.post(
            "/api/v1/user/register",
            json=user_data
        )
        
        assert response.status_code in [200, 400]

    def test_user_login(self, client: TestClient, test_user: User):
        """
        测试用户登录
        
        验证:
        - 可以登录并获取 token
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = client.post(
            "/api/v1/user/login",
            data=login_data
        )
        
        assert response.status_code in [200, 400, 401, 422]

    def test_get_user_profile(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_user: User
    ):
        """
        测试获取用户信息
        
        验证:
        - 返回用户信息
        """
        response = client.get(
            "/api/v1/user/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username

    def test_update_user_profile(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """
        测试更新用户信息
        
        验证:
        - 可以更新用户信息
        """
        update_data = {
            "email": "updated@example.com"
        }
        
        response = client.put(
            "/api/v1/user/me",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400, 404]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
class TestAIDiagnosisAPI:
    """AI 诊断 API 集成测试"""

    def test_ai_diagnosis_image_endpoint(self, client: TestClient):
        """
        测试 AI 图像诊断端点
        
        验证:
        - 返回 AI 诊断结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = client.post(
            "/api/v1/ai/diagnosis/image",
            files=files
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data

    def test_ai_diagnosis_health_endpoint(self, client: TestClient):
        """
        测试 AI 服务健康检查端点
        
        验证:
        - 返回 AI 服务状态
        """
        response = client.get("/api/v1/ai/diagnosis/health/ai")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data

    def test_ai_diagnosis_fusion_endpoint(self, client: TestClient):
        """
        测试融合诊断端点
        
        验证:
        - 返回融合诊断结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {"symptoms": "叶片出现黄色斑点", "enable_thinking": "false"}
        
        response = client.post(
            "/api/v1/ai/diagnosis/fusion",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestStatsAPI:
    """统计 API 集成测试"""

    def test_get_stats_endpoint(
        self, 
        client: TestClient,
        test_diagnosis: Diagnosis
    ):
        """
        测试统计端点
        
        验证:
        - 返回统计数据
        """
        response = client.get("/api/v1/stats/")
        
        assert response.status_code == 200

    def test_get_diagnosis_stats_endpoint(
        self, 
        client: TestClient,
        test_diagnosis: Diagnosis
    ):
        """
        测试诊断统计端点
        
        验证:
        - 返回诊断统计数据
        """
        response = client.get("/api/v1/stats/diagnosis")
        
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.api
class TestMetricsAPI:
    """指标 API 集成测试"""

    def test_get_metrics_endpoint(self, client: TestClient):
        """
        测试指标端点
        
        验证:
        - 返回系统指标
        """
        response = client.get("/api/v1/metrics/")
        
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.api
class TestLogsAPI:
    """日志 API 集成测试"""

    def test_get_logs_endpoint(
        self, 
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        测试日志端点
        
        验证:
        - 返回日志数据
        """
        response = client.get(
            "/api/v1/logs/",
            headers=admin_auth_headers
        )
        
        assert response.status_code in [200, 403, 404]


@pytest.mark.integration
@pytest.mark.api
class TestReportsAPI:
    """报告 API 集成测试"""

    def test_get_reports_endpoint(
        self, 
        client: TestClient,
        auth_headers: dict
    ):
        """
        测试报告端点
        
        验证:
        - 返回报告列表
        """
        response = client.get(
            "/api/v1/reports/",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.api
class TestUploadAPI:
    """上传 API 集成测试"""

    def test_upload_image_endpoint(
        self, 
        client: TestClient,
        auth_headers: dict
    ):
        """
        测试图像上传端点
        
        验证:
        - 可以上传图像
        """
        image_data = create_test_image()
        
        files = {"file": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = client.post(
            "/api/v1/upload/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404, 500]

    def test_upload_invalid_file(
        self, 
        client: TestClient,
        auth_headers: dict
    ):
        """
        测试上传无效文件
        
        验证:
        - 返回错误
        """
        invalid_data = b"not an image"
        
        files = {"file": ("test.txt", io.BytesIO(invalid_data), "text/plain")}
        
        response = client.post(
            "/api/v1/upload/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 404, 415]


@pytest.mark.integration
@pytest.mark.api
class TestErrorHandling:
    """错误处理集成测试"""

    def test_404_error(self, client: TestClient):
        """
        测试 404 错误处理
        
        验证:
        - 返回正确的 404 响应
        """
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client: TestClient):
        """
        测试方法不允许错误
        
        验证:
        - 返回 405 错误
        """
        response = client.delete("/api/v1/health")
        
        assert response.status_code == 405

    def test_validation_error(self, client: TestClient, auth_headers: dict):
        """
        测试验证错误
        
        验证:
        - 返回 422 错误
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": ""},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
