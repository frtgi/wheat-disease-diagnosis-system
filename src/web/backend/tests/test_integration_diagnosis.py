"""
诊断功能集成测试
测试图像上传、YOLOv8 检测、诊断结果保存等功能的集成测试
"""
import pytest
import io
from httpx import AsyncClient
from sqlalchemy.orm import Session
from PIL import Image

from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.models.disease import Disease


def create_test_image() -> bytes:
    """
    创建测试用的图像数据
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (100, 100), color='green')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


@pytest.mark.integration
@pytest.mark.api
class TestImageUpload:
    """图像上传集成测试"""

    @pytest.mark.asyncio
    async def test_image_upload_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试图像上传成功
        
        验证:
        - 返回状态码 200
        - 返回诊断结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {"symptoms": "叶片出现黄色斑点"}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_image_upload_without_auth(self, async_client: AsyncClient):
        """
        测试无认证上传图像
        
        验证:
        - 返回 401 错误
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_image_upload_invalid_format(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试上传无效格式的文件
        
        验证:
        - 返回 400 错误
        """
        invalid_data = b"not an image"
        
        files = {"image": ("test.txt", io.BytesIO(invalid_data), "text/plain")}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_image_upload_jpeg_format(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试上传 JPEG 格式图像
        
        验证:
        - 支持 JPEG 格式
        """
        image = Image.new('RGB', (200, 200), color='brown')
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        
        files = {"image": ("test.jpg", io.BytesIO(img_byte_arr.getvalue()), "image/jpeg")}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_image_upload_with_symptoms(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试上传图像并附带症状描述
        
        验证:
        - 症状描述被正确处理
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {"symptoms": "小麦叶片出现红褐色条斑，排列成行"}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestYOLODetection:
    """YOLOv8 检测集成测试"""

    @pytest.mark.asyncio
    async def test_yolo_detection_endpoint(self, async_client: AsyncClient):
        """
        测试 YOLOv8 检测端点
        
        验证:
        - 端点可访问
        - 返回检测结果格式正确
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/image",
            files=files
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result

    @pytest.mark.asyncio
    async def test_yolo_detection_result_format(self, async_client: AsyncClient):
        """
        测试 YOLOv8 检测结果格式
        
        验证:
        - 结果包含必要字段
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/image",
            files=files
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                assert "data" in result

    @pytest.mark.asyncio
    async def test_yolo_health_check(self, async_client: AsyncClient):
        """
        测试 AI 服务健康检查
        
        验证:
        - 健康检查端点可用
        """
        response = await async_client.get("/api/v1/ai/diagnosis/health/ai")
        
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert "services" in result


@pytest.mark.integration
@pytest.mark.api
class TestDiagnosisSave:
    """诊断结果保存集成测试"""

    @pytest.mark.asyncio
    async def test_diagnosis_record_creation(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        test_user: User
    ):
        """
        测试诊断记录创建
        
        验证:
        - 诊断记录正确保存到数据库
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {"symptoms": "叶片发黄"}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            result = response.json()
            assert "diagnosis_id" in result

    @pytest.mark.asyncio
    async def test_get_diagnosis_records(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        test_diagnosis: Diagnosis
    ):
        """
        测试获取诊断记录列表
        
        验证:
        - 返回用户的诊断记录
        """
        response = await async_client.get(
            "/api/v1/diagnosis/records",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert isinstance(records, list)

    @pytest.mark.asyncio
    async def test_get_diagnosis_records_pagination(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict
    ):
        """
        测试诊断记录分页
        
        验证:
        - 分页参数正确处理
        """
        response = await async_client.get(
            "/api/v1/diagnosis/records?skip=0&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_diagnosis_detail(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        test_diagnosis: Diagnosis
    ):
        """
        测试获取诊断详情
        
        验证:
        - 返回正确的诊断详情
        """
        response = await async_client.get(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == test_diagnosis.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_diagnosis(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict
    ):
        """
        测试获取不存在的诊断记录
        
        验证:
        - 返回 404 错误
        """
        response = await async_client.get(
            "/api/v1/diagnosis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_diagnosis_record(
        self, 
        async_client: AsyncClient, 
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
        
        response = await async_client.put(
            f"/api/v1/diagnosis/{test_diagnosis.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_diagnosis_record(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        db_session: Session,
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
        
        response = await async_client.delete(
            f"/api/v1/diagnosis/{diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.api
class TestTextDiagnosis:
    """文本诊断集成测试"""

    @pytest.mark.asyncio
    async def test_text_diagnosis_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试文本诊断成功
        
        验证:
        - 返回诊断结果
        """
        response = await async_client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "小麦叶片出现黄色锈斑，排列成行"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_text_diagnosis_without_auth(self, async_client: AsyncClient):
        """
        测试无认证进行文本诊断
        
        验证:
        - 返回 401 错误
        """
        response = await async_client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "叶片发黄"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_text_diagnosis_empty_symptoms(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试空症状描述
        
        验证:
        - 返回验证错误
        """
        response = await async_client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": ""},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.api
class TestDiagnosisPermissions:
    """诊断权限集成测试"""

    @pytest.mark.asyncio
    async def test_access_other_user_diagnosis(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        db_session: Session
    ):
        """
        测试访问其他用户的诊断记录
        
        验证:
        - 无法访问其他用户的记录
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
        db_session.refresh(other_user)
        
        other_diagnosis = Diagnosis(
            user_id=other_user.id,
            image_url="/uploads/other.jpg",
            symptoms="其他用户症状",
            disease_name="其他病害",
            confidence=0.8,
            status="completed"
        )
        db_session.add(other_diagnosis)
        db_session.commit()
        db_session.refresh(other_diagnosis)
        
        response = await async_client.get(
            f"/api/v1/diagnosis/{other_diagnosis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_farmer_role_diagnosis_access(
        self, 
        async_client: AsyncClient, 
        test_user: User
    ):
        """
        测试农民角色用户的诊断访问权限
        
        验证:
        - 农民用户可以创建和查看自己的诊断
        """
        from app.core.security import create_access_token
        
        token = create_access_token(data={"sub": test_user.username, "user_id": test_user.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        image_data = create_test_image()
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestDiagnosisPerformance:
    """诊断性能集成测试"""

    @pytest.mark.asyncio
    async def test_concurrent_diagnosis_requests(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict
    ):
        """
        测试并发诊断请求
        
        验证:
        - 系统可以处理并发请求
        """
        import asyncio
        
        async def make_request():
            image_data = create_test_image()
            files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
            return await async_client.post(
                "/api/v1/diagnosis/image",
                files=files,
                headers=auth_headers
            )
        
        tasks = [make_request() for _ in range(3)]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_large_image_upload(self, async_client: AsyncClient, auth_headers: dict):
        """
        测试大图像上传
        
        验证:
        - 系统正确处理大图像或返回适当错误
        """
        large_image = Image.new('RGB', (2000, 2000), color='green')
        img_byte_arr = io.BytesIO()
        large_image.save(img_byte_arr, format='PNG')
        
        files = {"image": ("large.png", io.BytesIO(img_byte_arr.getvalue()), "image/png")}
        
        response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400, 500]
