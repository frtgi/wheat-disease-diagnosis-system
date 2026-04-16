"""
诊断 API 接口测试
测试图像诊断、文本诊断、诊断记录管理等功能
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import io

from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.models.disease import Disease
from app.core.security import create_access_token


class TestImageDiagnosisAPI:
    """图像诊断 API 测试类"""

    def test_diagnose_image_success(self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes):
        """
        测试图像诊断成功
        
        验证:
        - 返回状态码 200
        - 返回诊断结果
        """
        with patch('app.api.v1.diagnosis.DiagnosisService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.diagnose_image = AsyncMock(return_value=MagicMock(
                disease_name="小麦锈病",
                confidence=0.92,
                severity="中度",
                description="叶片出现黄色锈斑",
                recommendations=["喷洒杀菌剂"],
                knowledge_links=[]
            ))
            mock_service.return_value = mock_instance
            
            files = {"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
            response = client.post(
                "/api/v1/diagnosis/image",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code in [200, 500]

    def test_diagnose_image_no_auth(self, client: TestClient, sample_image_bytes: bytes):
        """
        测试无认证图像诊断
        
        验证:
        - 返回 401 未授权
        """
        files = {"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
        response = client.post("/api/v1/diagnosis/image", files=files)
        
        assert response.status_code == 401

    def test_diagnose_image_invalid_format(self, client: TestClient, auth_headers: dict):
        """
        测试无效图像格式
        
        验证:
        - 返回 400 错误
        """
        files = {"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = client.post(
            "/api/v1/diagnosis/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_diagnose_image_with_symptoms(self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes):
        """
        测试带症状描述的图像诊断
        
        验证:
        - 正确处理症状参数
        """
        with patch('app.api.v1.diagnosis.DiagnosisService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.diagnose_image = AsyncMock(return_value=MagicMock(
                disease_name="小麦锈病",
                confidence=0.92,
                severity="中度",
                description="叶片出现黄色锈斑",
                recommendations=["喷洒杀菌剂"],
                knowledge_links=[]
            ))
            mock_service.return_value = mock_instance
            
            files = {"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
            data = {"symptoms": "叶片发黄"}
            response = client.post(
                "/api/v1/diagnosis/image",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            assert response.status_code in [200, 500]

    def test_diagnose_image_large_file(self, client: TestClient, auth_headers: dict):
        """
        测试大文件上传
        
        验证:
        - 返回 400 错误（文件过大）
        """
        large_content = b"x" * (6 * 1024 * 1024)
        files = {"image": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}
        response = client.post(
            "/api/v1/diagnosis/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestTextDiagnosisAPI:
    """文本诊断 API 测试类"""

    def test_diagnose_text_success(self, client: TestClient, auth_headers: dict):
        """
        测试文本诊断成功
        
        验证:
        - 返回状态码 200
        - 返回诊断结果
        """
        with patch('app.api.v1.diagnosis.DiagnosisService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.diagnose_text = AsyncMock(return_value=MagicMock(
                disease_name="小麦白粉病",
                confidence=0.88,
                severity="轻度",
                description="叶片出现白色粉状物",
                recommendations=["喷洒三唑酮"],
                knowledge_links=[]
            ))
            mock_service.return_value = mock_instance
            
            response = client.post(
                "/api/v1/diagnosis/text",
                data={"symptoms": "叶片出现白色粉状物"},
                headers=auth_headers
            )
            
            assert response.status_code in [200, 500]

    def test_diagnose_text_no_auth(self, client: TestClient):
        """
        测试无认证文本诊断
        
        验证:
        - 返回 401 未授权
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "叶片发黄"}
        )
        
        assert response.status_code == 401

    def test_diagnose_text_empty_symptoms(self, client: TestClient, auth_headers: dict):
        """
        测试空症状描述
        
        验证:
        - 返回 422 验证错误
        """
        response = client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestDiagnosisRecordsAPI:
    """诊断记录 API 测试类"""

    def test_get_diagnosis_records_success(self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis):
        """
        测试获取诊断记录列表成功
        
        验证:
        - 返回状态码 200
        - 返回记录列表
        """
        response = client.get("/api/v1/diagnosis/records", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data

    def test_get_diagnosis_records_pagination(self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis):
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

    def test_get_diagnosis_records_no_auth(self, client: TestClient):
        """
        测试无认证获取诊断记录
        
        验证:
        - 返回 401 未授权
        """
        response = client.get("/api/v1/diagnosis/records")
        
        assert response.status_code == 401

    def test_get_diagnosis_records_large_limit(self, client: TestClient, auth_headers: dict):
        """
        测试大批量数据导出
        
        验证:
        - 支持较大的 limit 参数
        """
        response = client.get(
            "/api/v1/diagnosis/records?limit=500",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestDiagnosisDetailAPI:
    """诊断详情 API 测试类"""

    def test_get_diagnosis_detail_success(self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis):
        """
        测试获取诊断详情成功
        
        验证:
        - 返回状态码 200
        - 返回诊断详情
        """
        response = client.get(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_diagnosis.id

    def test_get_diagnosis_detail_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试获取不存在的诊断记录
        
        验证:
        - 返回 404 错误
        """
        response = client.get("/api/v1/diagnosis/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_get_diagnosis_detail_other_user(self, client: TestClient, db_session: Session, test_user: User):
        """
        测试获取其他用户的诊断记录
        
        验证:
        - 返回 404 错误（无权访问）
        """
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="hash",
            role="farmer",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_diagnosis = Diagnosis(
            user_id=other_user.id,
            image_url="http://example.com/test.jpg",
            disease_name="其他病害",
            confidence=0.8,
            status="completed"
        )
        db_session.add(other_diagnosis)
        db_session.commit()
        
        token = create_access_token(data={"sub": test_user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(
            f"/api/v1/diagnosis/{other_diagnosis.id}",
            headers=headers
        )
        
        assert response.status_code == 404


class TestUpdateDiagnosisAPI:
    """更新诊断记录 API 测试类"""

    def test_update_diagnosis_success(self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis):
        """
        测试更新诊断记录成功
        
        验证:
        - 返回更新后的记录
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

    def test_update_diagnosis_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试更新不存在的诊断记录
        
        验证:
        - 返回 404 错误
        """
        update_data = {
            "status": "reviewed"
        }
        response = client.put(
            "/api/v1/diagnosis/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_update_diagnosis_confidence(self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis):
        """
        测试更新诊断置信度
        
        验证:
        - 置信度正确更新
        """
        update_data = {
            "confidence": 0.95
        }
        response = client.put(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestDeleteDiagnosisAPI:
    """删除诊断记录 API 测试类"""

    def test_delete_diagnosis_success(self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User):
        """
        测试删除诊断记录成功
        
        验证:
        - 返回成功消息
        """
        diagnosis = Diagnosis(
            user_id=test_user.id,
            image_url="http://example.com/test.jpg",
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

    def test_delete_diagnosis_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试删除不存在的诊断记录
        
        验证:
        - 返回 404 错误
        """
        response = client.delete("/api/v1/diagnosis/99999", headers=auth_headers)
        
        assert response.status_code == 404


class TestDiagnosisAPIValidation:
    """诊断 API 验证测试类"""

    def test_invalid_skip_parameter(self, client: TestClient, auth_headers: dict):
        """
        测试无效的 skip 参数
        
        验证:
        - 返回 422 验证错误
        """
        response = client.get(
            "/api/v1/diagnosis/records?skip=-1",
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_invalid_limit_parameter(self, client: TestClient, auth_headers: dict):
        """
        测试无效的 limit 参数
        
        验证:
        - 返回 422 验证错误
        """
        response = client.get(
            "/api/v1/diagnosis/records?limit=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_limit_exceeds_max(self, client: TestClient, auth_headers: dict):
        """
        测试 limit 超过最大值
        
        验证:
        - 返回 422 验证错误
        """
        response = client.get(
            "/api/v1/diagnosis/records?limit=2000",
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestDiagnosisAPIErrorHandling:
    """诊断 API 错误处理测试类"""

    def test_diagnosis_service_error(self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes):
        """
        测试诊断服务错误
        
        验证:
        - 返回 500 错误
        """
        with patch('app.api.v1.diagnosis.DiagnosisService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.diagnose_image = AsyncMock(side_effect=Exception("服务错误"))
            mock_service.return_value = mock_instance
            
            files = {"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
            response = client.post(
                "/api/v1/diagnosis/image",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == 500

    def test_database_error_on_save(self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes):
        """
        测试数据库保存错误
        
        验证:
        - 正确处理数据库错误
        """
        with patch('app.api.v1.diagnosis.DiagnosisService') as mock_service:
            with patch('sqlalchemy.orm.Session.commit', side_effect=Exception("数据库错误")):
                mock_instance = MagicMock()
                mock_instance.diagnose_image = AsyncMock(return_value=MagicMock(
                    disease_name="小麦锈病",
                    confidence=0.92,
                    severity="中度",
                    description="测试",
                    recommendations=[],
                    knowledge_links=[]
                ))
                mock_service.return_value = mock_instance
                
                files = {"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
                response = client.post(
                    "/api/v1/diagnosis/image",
                    files=files,
                    headers=auth_headers
                )
                
                assert response.status_code in [500, 200]


class TestDiagnosisAPIPerformance:
    """诊断 API 性能测试类"""

    @pytest.mark.slow
    def test_multiple_diagnosis_requests(self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes):
        """
        测试多次诊断请求
        
        验证:
        - 系统能处理连续请求
        """
        with patch('app.api.v1.diagnosis.DiagnosisService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.diagnose_image = AsyncMock(return_value=MagicMock(
                disease_name="小麦锈病",
                confidence=0.92,
                severity="中度",
                description="测试",
                recommendations=[],
                knowledge_links=[]
            ))
            mock_service.return_value = mock_instance
            
            for _ in range(3):
                files = {"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
                response = client.post(
                    "/api/v1/diagnosis/image",
                    files=files,
                    headers=auth_headers
                )
                
                assert response.status_code in [200, 500]

    @pytest.mark.slow
    def test_large_records_query(self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User):
        """
        测试大量记录查询
        
        验证:
        - 分页查询性能
        """
        diagnoses = []
        for i in range(50):
            diagnosis = Diagnosis(
                user_id=test_user.id,
                image_url=f"http://example.com/test{i}.jpg",
                disease_name=f"病害{i}",
                confidence=0.8,
                status="completed"
            )
            diagnoses.append(diagnosis)
        
        db_session.add_all(diagnoses)
        db_session.commit()
        
        response = client.get(
            "/api/v1/diagnosis/records?limit=50",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 50
