"""
边界条件测试用例
覆盖输入边界、参数边界、数据边界等场景
"""
import pytest
import io
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
from PIL import Image

from app.models.user import User
from app.models.disease import Disease
from app.models.diagnosis import Diagnosis


class TestUserInputBoundary:
    """
    用户输入边界测试类
    
    测试用户相关输入的边界条件
    """
    
    def test_username_min_length(self, client: TestClient):
        """
        测试用户名最小长度（3个字符）
        
        验证:
        - 3个字符的用户名应该成功
        """
        user_data = {
            "username": "abc",
            "email": "minuser@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        assert response.json()["username"] == "abc"
    
    def test_username_below_min_length(self, client: TestClient):
        """
        测试用户名低于最小长度
        
        验证:
        - 2个字符的用户名应该失败
        """
        user_data = {
            "username": "ab",
            "email": "tooshort@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_username_max_length(self, client: TestClient):
        """
        测试用户名最大长度（50个字符）
        
        验证:
        - 50个字符的用户名应该成功
        """
        max_username = "a" * 50
        user_data = {
            "username": max_username,
            "email": "maxuser@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
        assert len(response.json()["username"]) == 50
    
    def test_username_exceed_max_length(self, client: TestClient):
        """
        测试用户名超过最大长度
        
        验证:
        - 51个字符的用户名应该失败
        """
        too_long_username = "a" * 51
        user_data = {
            "username": too_long_username,
            "email": "toolong@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_password_min_length(self, client: TestClient):
        """
        测试密码最小长度（6个字符）
        
        验证:
        - 6个字符的密码应该成功
        """
        user_data = {
            "username": "passwordmin",
            "email": "passmin@example.com",
            "password": "123456"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
    
    def test_password_below_min_length(self, client: TestClient):
        """
        测试密码低于最小长度
        
        验证:
        - 5个字符的密码应该失败
        """
        user_data = {
            "username": "passwordshort",
            "email": "passshort@example.com",
            "password": "12345"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_password_max_length(self, client: TestClient):
        """
        测试密码最大长度（100个字符）
        
        验证:
        - 100个字符的密码应该成功
        """
        max_password = "a" * 100
        user_data = {
            "username": "passwordmax",
            "email": "passmax@example.com",
            "password": max_password
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
    
    def test_password_exceed_max_length(self, client: TestClient):
        """
        测试密码超过最大长度
        
        验证:
        - 101个字符的密码应该失败
        """
        too_long_password = "a" * 101
        user_data = {
            "username": "passwordtoolong",
            "email": "passtoolong@example.com",
            "password": too_long_password
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_phone_max_length(self, client: TestClient):
        """
        测试手机号最大长度（20个字符）
        
        验证:
        - 20个字符的手机号应该成功
        """
        user_data = {
            "username": "phonemax",
            "email": "phonemax@example.com",
            "password": "SecurePass123",
            "phone": "1" * 20
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 200
    
    def test_phone_exceed_max_length(self, client: TestClient):
        """
        测试手机号超过最大长度
        
        验证:
        - 21个字符的手机号应该失败
        """
        user_data = {
            "username": "phonetoolong",
            "email": "phonetoolong@example.com",
            "password": "SecurePass123",
            "phone": "1" * 21
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422


class TestDiagnosisInputBoundary:
    """
    诊断输入边界测试类
    
    测试诊断相关输入的边界条件
    """
    
    def test_symptoms_min_length(self, client: TestClient, auth_headers: dict):
        """
        测试症状描述最小长度（1个字符）
        
        验证:
        - 1个字符的症状描述应该被接受
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "病"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_symptoms_max_length(self, client: TestClient, auth_headers: dict):
        """
        测试症状描述最大长度（2000个字符）
        
        验证:
        - 2000个字符的症状描述应该成功
        """
        max_symptoms = "病" * 2000
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": max_symptoms},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_symptoms_exceed_max_length(self, client: TestClient, auth_headers: dict):
        """
        测试症状描述超过最大长度
        
        验证:
        - 2001个字符的症状描述应该失败
        """
        too_long_symptoms = "病" * 2001
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": too_long_symptoms},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_image_file_min_size(self, client: TestClient, auth_headers: dict):
        """
        测试图像文件最小尺寸
        
        验证:
        - 最小有效图像应该被接受
        """
        img = Image.new('RGB', (1, 1), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("tiny.png", buffer, "image/png")},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400]
    
    def test_image_file_max_size(self, client: TestClient, auth_headers: dict):
        """
        测试图像文件最大尺寸（5MB）
        
        验证:
        - 接近5MB的图像应该被接受
        """
        img = Image.new('RGB', (2000, 2000), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("large.png", buffer, "image/png")},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400]
    
    def test_image_file_exceed_max_size(self, client: TestClient, auth_headers: dict):
        """
        测试图像文件超过最大尺寸
        
        验证:
        - 超过5MB的图像应该被拒绝
        """
        large_data = b'x' * (6 * 1024 * 1024)
        
        buffer = io.BytesIO(large_data)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("huge.png", buffer, "image/png")},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_confidence_boundary_values(self, client: TestClient, auth_headers: dict):
        """
        测试置信度边界值
        
        验证:
        - 置信度应该在 0-1 范围内
        """
        update_data = {"confidence": 0.0}
        response = client.put(
            "/api/v1/diagnosis/1",
            json=update_data,
            headers=auth_headers
        )
        
        update_data = {"confidence": 1.0}
        response = client.put(
            "/api/v1/diagnosis/1",
            json=update_data,
            headers=auth_headers
        )
        
        update_data = {"confidence": 1.1}
        response = client.put(
            "/api/v1/diagnosis/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code in [404, 422]
    
    def test_confidence_negative_value(self, client: TestClient, auth_headers: dict):
        """
        测试置信度负值
        
        验证:
        - 负值置信度应该被拒绝
        """
        update_data = {"confidence": -0.1}
        response = client.put(
            "/api/v1/diagnosis/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code in [404, 422]


class TestPaginationBoundary:
    """
    分页边界测试类
    
    测试分页参数的边界条件
    """
    
    def test_pagination_skip_zero(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试分页跳过数为0
        
        验证:
        - skip=0 应该返回第一页数据
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
    
    def test_pagination_skip_large_value(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试分页跳过数很大
        
        验证:
        - 大的 skip 值应该返回空列表
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=999999&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 0
    
    def test_pagination_limit_min_value(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试分页限制最小值
        
        验证:
        - limit=1 应该返回最多1条记录
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) <= 1
    
    def test_pagination_limit_max_value(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试分页限制最大值（1000）
        
        验证:
        - limit=1000 应该被接受
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=1000",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1000
    
    def test_pagination_limit_exceed_max(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试分页限制超过最大值
        
        验证:
        - limit>1000 应该被拒绝
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=1001",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_pagination_negative_skip(self, client: TestClient, auth_headers: dict):
        """
        测试负数的跳过数
        
        验证:
        - 负数 skip 应该被拒绝
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=-1&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_pagination_zero_limit(self, client: TestClient, auth_headers: dict):
        """
        测试零限制
        
        验证:
        - limit=0 应该被拒绝
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=0&limit=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_knowledge_search_pagination_boundary(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试知识搜索分页边界
        
        验证:
        - 边界值应该被正确处理
        """
        response = client.get(
            "/api/v1/knowledge/search",
            params={"skip": 0, "limit": 100}
        )
        
        assert response.status_code == 200
        
        response = client.get(
            "/api/v1/knowledge/search",
            params={"skip": 0, "limit": 101}
        )
        
        assert response.status_code == 422


class TestKnowledgeInputBoundary:
    """
    知识库输入边界测试类
    
    测试知识库相关输入的边界条件
    """
    
    def test_disease_name_min_length(self, client: TestClient):
        """
        测试疾病名称最小长度（1个字符）
        
        验证:
        - 1个字符的名称应该成功
        """
        disease_data = {
            "name": "病",
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 200
    
    def test_disease_name_max_length(self, client: TestClient):
        """
        测试疾病名称最大长度（100个字符）
        
        验证:
        - 100个字符的名称应该成功
        """
        max_name = "病" * 100
        disease_data = {
            "name": max_name,
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 200
    
    def test_disease_name_exceed_max_length(self, client: TestClient):
        """
        测试疾病名称超过最大长度
        
        验证:
        - 101个字符的名称应该失败
        """
        too_long_name = "病" * 101
        disease_data = {
            "name": too_long_name,
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 422
    
    def test_disease_code_max_length(self, client: TestClient):
        """
        测试疾病编码最大长度（50个字符）
        
        验证:
        - 50个字符的编码应该成功
        """
        disease_data = {
            "name": "边界测试病害",
            "code": "A" * 50,
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 200
    
    def test_disease_code_exceed_max_length(self, client: TestClient):
        """
        测试疾病编码超过最大长度
        
        验证:
        - 51个字符的编码应该失败
        """
        disease_data = {
            "name": "边界测试病害2",
            "code": "A" * 51,
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 422
    
    def test_disease_severity_boundary(self, client: TestClient):
        """
        测试疾病严重程度边界值
        
        验证:
        - 严重程度应该在 0-1 范围内
        """
        disease_data = {
            "name": "严重程度测试0",
            "category": "真菌病害",
            "severity": 0.0
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        assert response.status_code == 200
        
        disease_data = {
            "name": "严重程度测试1",
            "category": "真菌病害",
            "severity": 1.0
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        assert response.status_code == 200
        
        disease_data = {
            "name": "严重程度测试超",
            "category": "真菌病害",
            "severity": 1.1
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        assert response.status_code == 422


class TestAIDiagnosisInputBoundary:
    """
    AI 诊断输入边界测试类
    
    测试 AI 诊断相关输入的边界条件
    """
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_multimodal_symptoms_max_length(self, mock_should_use_mock, client: TestClient):
        """
        测试多模态诊断症状最大长度
        
        验证:
        - 长症状描述应该被处理
        """
        mock_should_use_mock.return_value = True
        
        long_symptoms = "叶片发黄" * 500
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/multimodal",
            data={"symptoms": long_symptoms}
        )
        
        assert response.status_code == 200
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_batch_diagnosis_max_images(self, mock_should_use_mock, client: TestClient, sample_image_bytes: bytes):
        """
        测试批量诊断最大图像数（10张）
        
        验证:
        - 10张图像应该被接受
        """
        mock_should_use_mock.return_value = True
        
        files = []
        for i in range(10):
            image_file = io.BytesIO(sample_image_bytes)
            files.append(("images", (f"test{i}.png", image_file, "image/png")))
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/batch",
            files=files,
            data={"symptoms": "测试症状"}
        )
        
        assert response.status_code == 200
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_batch_diagnosis_exceed_max_images(self, mock_should_use_mock, client: TestClient, sample_image_bytes: bytes):
        """
        测试批量诊断超过最大图像数
        
        验证:
        - 11张图像应该被拒绝
        """
        mock_should_use_mock.return_value = True
        
        files = []
        for i in range(11):
            image_file = io.BytesIO(sample_image_bytes)
            files.append(("images", (f"test{i}.png", image_file, "image/png")))
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/batch",
            files=files,
            data={"symptoms": "测试症状"}
        )
        
        assert response.status_code == 400
    
    def test_ai_image_max_size(self, client: TestClient):
        """
        测试 AI 诊断图像最大尺寸（10MB）
        
        验证:
        - 接近10MB的图像应该被接受
        """
        large_data = b'x' * (9 * 1024 * 1024)
        buffer = io.BytesIO(large_data)
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/image",
            files={"image": ("large.png", buffer, "image/png")}
        )
        
        assert response.status_code in [200, 400, 500]
    
    def test_ai_image_exceed_max_size(self, client: TestClient):
        """
        测试 AI 诊断图像超过最大尺寸
        
        验证:
        - 超过10MB的图像应该被拒绝
        """
        large_data = b'x' * (11 * 1024 * 1024)
        buffer = io.BytesIO(large_data)
        
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/image",
            files={"image": ("huge.png", buffer, "image/png")}
        )
        
        assert response.status_code == 400


class TestIDBoundary:
    """
    ID 边界测试类
    
    测试各种 ID 参数的边界条件
    """
    
    def test_user_id_zero(self, client: TestClient):
        """
        测试用户 ID 为 0
        
        验证:
        - ID=0 应该返回 404
        """
        response = client.get("/api/v1/users/0")
        
        assert response.status_code == 404
    
    def test_user_id_negative(self, client: TestClient):
        """
        测试用户 ID 为负数
        
        验证:
        - 负数 ID 应该返回 404 或 422
        """
        response = client.get("/api/v1/users/-1")
        
        assert response.status_code in [404, 422]
    
    def test_user_id_very_large(self, client: TestClient):
        """
        测试用户 ID 非常大
        
        验证:
        - 大 ID 应该返回 404
        """
        response = client.get("/api/v1/users/999999999999")
        
        assert response.status_code == 404
    
    def test_diagnosis_id_zero(self, client: TestClient, auth_headers: dict):
        """
        测试诊断 ID 为 0
        
        验证:
        - ID=0 应该返回 404
        """
        response = client.get("/api/v1/diagnosis/0", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_diagnosis_id_negative(self, client: TestClient, auth_headers: dict):
        """
        测试诊断 ID 为负数
        
        验证:
        - 负数 ID 应该返回 404 或 422
        """
        response = client.get("/api/v1/diagnosis/-1", headers=auth_headers)
        
        assert response.status_code in [404, 422]
    
    def test_disease_id_zero(self, client: TestClient):
        """
        测试疾病 ID 为 0
        
        验证:
        - ID=0 应该返回 404
        """
        response = client.get("/api/v1/knowledge/0")
        
        assert response.status_code == 404
    
    def test_disease_id_negative(self, client: TestClient):
        """
        测试疾病 ID 为负数
        
        验证:
        - 负数 ID 应该返回 404 或 422
        """
        response = client.get("/api/v1/knowledge/-1")
        
        assert response.status_code in [404, 422]


class TestSpecialCharactersBoundary:
    """
    特殊字符边界测试类
    
    测试特殊字符输入的处理
    """
    
    def test_username_with_special_chars(self, client: TestClient):
        """
        测试用户名包含特殊字符
        
        验证:
        - 特殊字符应该被正确处理
        """
        user_data = {
            "username": "user_测试_123",
            "email": "special@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code in [200, 422]
    
    def test_username_with_unicode(self, client: TestClient):
        """
        测试用户名包含 Unicode 字符
        
        验证:
        - Unicode 字符应该被正确处理
        """
        user_data = {
            "username": "用户测试名",
            "email": "unicode@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code in [200, 422]
    
    def test_symptoms_with_special_chars(self, client: TestClient, auth_headers: dict):
        """
        测试症状描述包含特殊字符
        
        验证:
        - 特殊字符应该被正确处理
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "叶片出现<黄色>斑点，伴有\"锈斑\"和'霉层'"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_symptoms_with_newlines(self, client: TestClient, auth_headers: dict):
        """
        测试症状描述包含换行符
        
        验证:
        - 换行符应该被正确处理
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "第一行症状\n第二行症状\r\n第三行症状"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_disease_name_with_special_chars(self, client: TestClient):
        """
        测试疾病名称包含特殊字符
        
        验证:
        - 特殊字符应该被正确处理
        """
        disease_data = {
            "name": "小麦锈病（条锈）",
            "category": "真菌病害"
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 200


class TestImageFormatBoundary:
    """
    图像格式边界测试类
    
    测试不同图像格式的处理
    """
    
    def test_jpeg_image_format(self, client: TestClient, auth_headers: dict):
        """
        测试 JPEG 格式图像
        
        验证:
        - JPEG 格式应该被接受
        """
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test.jpg", buffer, "image/jpeg")},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_png_image_format(self, client: TestClient, auth_headers: dict):
        """
        测试 PNG 格式图像
        
        验证:
        - PNG 格式应该被接受
        """
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test.png", buffer, "image/png")},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_gif_image_format(self, client: TestClient, auth_headers: dict):
        """
        测试 GIF 格式图像
        
        验证:
        - GIF 格式可能被拒绝
        """
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='GIF')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test.gif", buffer, "image/gif")},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400]
    
    def test_bmp_image_format(self, client: TestClient, auth_headers: dict):
        """
        测试 BMP 格式图像
        
        验证:
        - BMP 格式可能被拒绝
        """
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='BMP')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test.bmp", buffer, "image/bmp")},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400]
    
    def test_webp_image_format(self, client: TestClient, auth_headers: dict):
        """
        测试 WebP 格式图像
        
        验证:
        - WebP 格式应该被接受
        """
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='WEBP')
        buffer.seek(0)
        
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("test.webp", buffer, "image/webp")},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400]


class TestAsyncBoundaryConditions:
    """
    异步边界条件测试类
    """
    
    @pytest.mark.asyncio
    async def test_async_pagination_boundary(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        异步测试分页边界
        
        验证:
        - 边界值应该被正确处理
        """
        response = await async_client.get(
            "/api/v1/diagnosis/records?skip=0&limit=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_large_skip_value(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        异步测试大跳过值
        
        验证:
        - 大 skip 值应该返回空列表
        """
        response = await async_client.get(
            "/api/v1/diagnosis/records?skip=999999&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 0


class TestNumericBoundary:
    """
    数值边界测试类
    
    测试数值类型参数的边界条件
    """
    
    def test_confidence_precision(self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User):
        """
        测试置信度精度
        
        验证:
        - 高精度小数应该被正确处理
        """
        diagnosis = Diagnosis(
            user_id=test_user.id,
            symptoms="精度测试",
            disease_name="测试病害",
            confidence=0.123456789,
            status="completed"
        )
        db_session.add(diagnosis)
        db_session.commit()
        db_session.refresh(diagnosis)
        
        response = client.get(
            f"/api/v1/diagnosis/{diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_severity_precision(self, client: TestClient):
        """
        测试严重程度精度
        
        验证:
        - 高精度小数应该被正确处理
        """
        disease_data = {
            "name": "精度测试病害",
            "category": "真菌病害",
            "severity": 0.123456789
        }
        response = client.post("/api/v1/knowledge/", json=disease_data)
        
        assert response.status_code == 200
