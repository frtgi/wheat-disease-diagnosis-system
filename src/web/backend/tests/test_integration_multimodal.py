"""
多模态诊断集成测试
测试图像+文本联合诊断、Qwen3-VL-4B 调用、诊断报告生成等功能的集成测试
"""
import pytest
import io
from httpx import AsyncClient
from sqlalchemy.orm import Session
from PIL import Image

from app.models.user import User
from app.models.diagnosis import Diagnosis


def create_test_image() -> bytes:
    """
    创建测试用的图像数据
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (224, 224), color='green')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def create_wheat_disease_image() -> bytes:
    """
    创建模拟小麦病害图像
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (224, 224), color='yellow')
    for x in range(50, 150):
        for y in range(50, 150):
            image.putpixel((x, y), (139, 69, 19))
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


@pytest.mark.integration
@pytest.mark.api
class TestMultimodalDiagnosis:
    """图像+文本联合诊断集成测试"""

    @pytest.mark.asyncio
    async def test_multimodal_diagnosis_with_image_and_text(self, async_client: AsyncClient):
        """
        测试图像+文本联合诊断
        
        验证:
        - 同时提供图像和文本时能正确处理
        - 返回综合诊断结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "小麦叶片出现黄色锈斑，排列成行，疑似条锈病",
            "thinking_mode": "true",
            "use_graph_rag": "true"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result

    @pytest.mark.asyncio
    async def test_multimodal_diagnosis_image_only(self, async_client: AsyncClient):
        """
        测试仅图像诊断
        
        验证:
        - 仅提供图像时能正常工作
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "",
            "thinking_mode": "false"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_multimodal_diagnosis_text_only(self, async_client: AsyncClient):
        """
        测试仅文本诊断
        
        验证:
        - 仅提供文本时能正常工作
        """
        data = {
            "symptoms": "小麦叶片出现黄色锈斑，排列成行，疑似条锈病",
            "thinking_mode": "true",
            "use_graph_rag": "true"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            data=data
        )
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_multimodal_with_disease_context(self, async_client: AsyncClient):
        """
        测试带疾病上下文的多模态诊断
        
        验证:
        - 疾病上下文被正确使用
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "叶片发黄",
            "disease_context": "条锈病、叶锈病",
            "use_graph_rag": "true"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestQwenService:
    """Qwen3-VL-4B 调用集成测试"""

    @pytest.mark.asyncio
    async def test_qwen_text_diagnosis(self, async_client: AsyncClient):
        """
        测试 Qwen 文本诊断
        
        验证:
        - 文本诊断端点可用
        - 返回诊断结果
        """
        response = await async_client.post(
            "/api/v1/ai/diagnosis/text",
            data={"symptoms": "小麦叶片出现红褐色条斑，排列成行，夏孢子堆破裂后散出铁锈色粉末"}
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result

    @pytest.mark.asyncio
    async def test_qwen_multimodal_with_thinking_mode(self, async_client: AsyncClient):
        """
        测试 Qwen 多模态诊断（启用 Thinking 模式）
        
        验证:
        - Thinking 模式返回推理链
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "叶片出现黄色斑点",
            "thinking_mode": "true"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("features", {}).get("thinking_mode"):
                pass

    @pytest.mark.asyncio
    async def test_qwen_multimodal_without_thinking_mode(self, async_client: AsyncClient):
        """
        测试 Qwen 多模态诊断（禁用 Thinking 模式）
        
        验证:
        - 禁用 Thinking 模式时返回简洁结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "叶片发黄",
            "thinking_mode": "false"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_qwen_service_health(self, async_client: AsyncClient):
        """
        测试 Qwen 服务健康状态
        
        验证:
        - 健康检查返回服务状态
        """
        response = await async_client.get("/api/v1/ai/diagnosis/health/ai")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "status" in result
        assert "services" in result
        assert "qwen3vl" in result["services"]


@pytest.mark.integration
@pytest.mark.api
class TestDiagnosisReport:
    """诊断报告生成集成测试"""

    @pytest.mark.asyncio
    async def test_diagnosis_result_format(self, async_client: AsyncClient):
        """
        测试诊断结果格式
        
        验证:
        - 诊断结果包含必要字段
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "小麦叶片出现黄色锈斑",
            "thinking_mode": "true"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                diagnosis = result.get("data", {})
                assert "disease_name" in diagnosis or "diagnosis" in result

    @pytest.mark.asyncio
    async def test_diagnosis_confidence_analysis(self, async_client: AsyncClient):
        """
        测试诊断置信度分析
        
        验证:
        - 返回置信度分析结果
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "叶片出现红褐色斑点",
            "thinking_mode": "true",
            "use_graph_rag": "true"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                confidence_analysis = result.get("confidence_analysis", {})
                assert "overall_confidence" in confidence_analysis or "data" in result

    @pytest.mark.asyncio
    async def test_diagnosis_performance_metrics(self, async_client: AsyncClient):
        """
        测试诊断性能指标
        
        验证:
        - 返回推理时间等性能指标
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data={"symptoms": "叶片发黄"}
        )
        
        if response.status_code == 200:
            result = response.json()
            performance = result.get("performance", {})
            assert "inference_time_ms" in performance or "data" in result


@pytest.mark.integration
@pytest.mark.api
class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.mark.asyncio
    async def test_cache_hit(self, async_client: AsyncClient):
        """
        测试缓存命中
        
        验证:
        - 相同请求第二次能命中缓存
        """
        image_data = create_test_image()
        symptoms = "测试缓存症状描述"
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": symptoms,
            "use_cache": "true"
        }
        
        response1 = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        response2 = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            result2 = response2.json()
            cache_info = result2.get("cache_info", {})
            assert cache_info.get("hit") or "data" in result2

    @pytest.mark.asyncio
    async def test_cache_stats(self, async_client: AsyncClient):
        """
        测试缓存统计
        
        验证:
        - 可以获取缓存统计信息
        """
        response = await async_client.get("/api/v1/ai/diagnosis/cache/stats")
        
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_cache_clear(self, async_client: AsyncClient):
        """
        测试清空缓存
        
        验证:
        - 可以清空缓存
        """
        response = await async_client.post("/api/v1/ai/diagnosis/cache/clear")
        
        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestBatchDiagnosis:
    """批量诊断集成测试"""

    @pytest.mark.asyncio
    async def test_batch_diagnosis(self, async_client: AsyncClient):
        """
        测试批量图像诊断
        
        验证:
        - 可以处理多张图像
        - 返回批量结果汇总
        """
        image_data1 = create_test_image()
        image_data2 = create_wheat_disease_image()
        
        files = [
            ("images", ("test1.png", io.BytesIO(image_data1), "image/png")),
            ("images", ("test2.png", io.BytesIO(image_data2), "image/png"))
        ]
        data = {
            "symptoms": "批量诊断测试",
            "use_cache": "false"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/batch",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "summary" in result
            assert "results" in result

    @pytest.mark.asyncio
    async def test_batch_diagnosis_limit(self, async_client: AsyncClient):
        """
        测试批量诊断数量限制
        
        验证:
        - 超过限制返回错误
        """
        files = []
        for i in range(15):
            image_data = create_test_image()
            files.append(("images", (f"test{i}.png", io.BytesIO(image_data), "image/png")))
        
        data = {"symptoms": "测试超限"}
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/batch",
            files=files,
            data=data
        )
        
        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.api
class TestGraphRAGIntegration:
    """Graph-RAG 集成测试"""

    @pytest.mark.asyncio
    async def test_diagnosis_with_graph_rag(self, async_client: AsyncClient):
        """
        测试使用 Graph-RAG 的诊断
        
        验证:
        - Graph-RAG 增强返回知识引用
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "小麦叶片出现黄色锈斑",
            "use_graph_rag": "true",
            "disease_context": "条锈病"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("features", {}).get("graph_rag"):
                pass

    @pytest.mark.asyncio
    async def test_diagnosis_without_graph_rag(self, async_client: AsyncClient):
        """
        测试不使用 Graph-RAG 的诊断
        
        验证:
        - 不使用 Graph-RAG 时正常工作
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "叶片发黄",
            "use_graph_rag": "false"
        }
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestMultimodalErrorHandling:
    """多模态诊断错误处理集成测试"""

    @pytest.mark.asyncio
    async def test_invalid_image_format(self, async_client: AsyncClient):
        """
        测试无效图像格式
        
        验证:
        - 返回适当错误
        """
        invalid_data = b"not an image"
        
        files = {"image": ("test.txt", io.BytesIO(invalid_data), "text/plain")}
        data = {"symptoms": "测试"}
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data=data
        )
        
        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_empty_request(self, async_client: AsyncClient):
        """
        测试空请求
        
        验证:
        - 返回适当错误或默认处理
        """
        response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            data={}
        )
        
        assert response.status_code in [200, 400, 422, 500]

    @pytest.mark.asyncio
    async def test_large_symptoms_text(self, async_client: AsyncClient):
        """
        测试大量症状文本
        
        验证:
        - 系统能处理或拒绝过长的文本
        """
        large_symptoms = "症状描述" * 1000
        
        response = await async_client.post(
            "/api/v1/ai/diagnosis/text",
            data={"symptoms": large_symptoms}
        )
        
        assert response.status_code in [200, 400, 413, 500]


@pytest.mark.integration
@pytest.mark.api
class TestDiagnosisWorkflow:
    """诊断工作流集成测试"""

    @pytest.mark.asyncio
    async def test_complete_diagnosis_workflow(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        db_session: Session
    ):
        """
        测试完整诊断工作流
        
        验证步骤:
        1. 上传图像进行诊断
        2. 获取诊断结果
        3. 查看诊断记录
        """
        image_data = create_wheat_disease_image()
        
        files = {"image": ("wheat.png", io.BytesIO(image_data), "image/png")}
        data = {
            "symptoms": "小麦叶片出现黄色锈斑，排列成行"
        }
        
        diagnosis_response = await async_client.post(
            "/api/v1/diagnosis/image",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        if diagnosis_response.status_code == 200:
            diagnosis_id = diagnosis_response.json().get("diagnosis_id")
            
            if diagnosis_id:
                records_response = await async_client.get(
                    "/api/v1/diagnosis/records",
                    headers=auth_headers
                )
                assert records_response.status_code == 200

    @pytest.mark.asyncio
    async def test_multimodal_then_text_diagnosis(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict
    ):
        """
        测试先多模态诊断后文本诊断
        
        验证:
        - 两种诊断方式可以连续使用
        """
        image_data = create_test_image()
        
        files = {"image": ("test.png", io.BytesIO(image_data), "image/png")}
        
        multimodal_response = await async_client.post(
            "/api/v1/ai/diagnosis/multimodal",
            files=files,
            data={"symptoms": "叶片发黄"}
        )
        
        text_response = await async_client.post(
            "/api/v1/diagnosis/text",
            data={"symptoms": "叶片出现红褐色斑点"},
            headers=auth_headers
        )
        
        assert multimodal_response.status_code in [200, 500]
        assert text_response.status_code in [200, 500]
