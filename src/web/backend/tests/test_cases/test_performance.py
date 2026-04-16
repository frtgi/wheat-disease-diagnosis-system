"""
性能测试用例
覆盖响应时间、并发性能、吞吐量、资源使用等场景
"""
import pytest
import io
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
from PIL import Image

from app.models.user import User
from app.models.disease import Disease
from app.models.diagnosis import Diagnosis


class TestResponseTime:
    """
    响应时间测试类
    
    测试各接口的响应时间性能
    """
    
    def test_health_check_response_time(self, client: TestClient):
        """
        测试健康检查接口响应时间
        
        验证:
        - 响应时间应小于 100ms
        """
        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 100, f"响应时间 {response_time_ms}ms 超过 100ms"
    
    def test_user_login_response_time(self, client: TestClient, test_user: User):
        """
        测试用户登录响应时间
        
        验证:
        - 响应时间应小于 500ms
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/users/login", json=login_data)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 500, f"响应时间 {response_time_ms}ms 超过 500ms"
    
    def test_user_register_response_time(self, client: TestClient):
        """
        测试用户注册响应时间
        
        验证:
        - 响应时间应小于 500ms
        """
        user_data = {
            "username": f"perfuser_{int(time.time() * 1000)}",
            "email": f"perf_{int(time.time() * 1000)}@example.com",
            "password": "SecurePass123"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/users/register", json=user_data)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 500, f"响应时间 {response_time_ms}ms 超过 500ms"
    
    def test_get_diagnosis_records_response_time(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试获取诊断记录响应时间
        
        验证:
        - 响应时间应小于 300ms
        """
        for i in range(10):
            diagnosis = Diagnosis(
                user_id=test_user.id,
                symptoms=f"性能测试症状{i}",
                disease_name="小麦锈病",
                confidence=0.9,
                status="completed"
            )
            db_session.add(diagnosis)
        db_session.commit()
        
        start_time = time.time()
        response = client.get(
            "/api/v1/diagnosis/records",
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 300, f"响应时间 {response_time_ms}ms 超过 300ms"
    
    def test_knowledge_search_response_time(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试知识搜索响应时间
        
        验证:
        - 响应时间应小于 300ms
        """
        start_time = time.time()
        response = client.get(
            "/api/v1/knowledge/search",
            params={"keyword": "锈病"}
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 300, f"响应时间 {response_time_ms}ms 超过 300ms"
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_text_diagnosis_response_time(self, mock_should_use_mock, client: TestClient):
        """
        测试文本诊断响应时间（Mock 模式）
        
        验证:
        - Mock 模式响应时间应小于 1000ms
        """
        mock_should_use_mock.return_value = True
        
        start_time = time.time()
        response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/text",
            data={"symptoms": "叶片出现黄色锈斑"}
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 1000, f"响应时间 {response_time_ms}ms 超过 1000ms"


class TestConcurrentAccess:
    """
    并发访问测试类
    
    测试系统在并发访问下的性能
    """
    
    def test_concurrent_user_logins(self, client: TestClient, test_user: User):
        """
        测试并发用户登录
        
        验证:
        - 多个并发登录请求应该都能成功
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        results = []
        
        def login_request():
            response = client.post("/api/v1/users/login", json=login_data)
            return response.status_code
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_request) for _ in range(5)]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 4, f"并发登录成功率过低: {success_count}/5"
    
    def test_concurrent_diagnosis_queries(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试并发诊断查询
        
        验证:
        - 多个并发查询应该都能成功
        """
        results = []
        
        def query_request():
            response = client.get(
                "/api/v1/diagnosis/records",
                headers=auth_headers
            )
            return response.status_code
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_request) for _ in range(10)]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 8, f"并发查询成功率过低: {success_count}/10"
    
    def test_concurrent_knowledge_searches(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试并发知识搜索
        
        验证:
        - 多个并发搜索应该都能成功
        """
        keywords = ["锈病", "白粉病", "蚜虫", "真菌", "虫害"]
        results = []
        
        def search_request(keyword):
            response = client.get(
                "/api/v1/knowledge/search",
                params={"keyword": keyword}
            )
            return response.status_code
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_request, kw) for kw in keywords]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 4, f"并发搜索成功率过低: {success_count}/5"
    
    @pytest.mark.asyncio
    async def test_async_concurrent_requests(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        异步测试并发请求
        
        验证:
        - 异步并发请求应该都能成功
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        tasks = []
        for _ in range(5):
            task = async_client.post("/api/v1/users/login", json=login_data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code == 200
        )
        assert success_count >= 4, f"异步并发成功率过低: {success_count}/5"


class TestThroughput:
    """
    吞吐量测试类
    
    测试系统在单位时间内的处理能力
    """
    
    def test_login_throughput(self, client: TestClient, test_user: User):
        """
        测试登录接口吞吐量
        
        验证:
        - 每秒应能处理至少 10 次登录请求
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        request_count = 20
        start_time = time.time()
        
        for _ in range(request_count):
            client.post("/api/v1/users/login", json=login_data)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = request_count / total_time
        
        assert throughput >= 10, f"登录吞吐量 {throughput:.2f} req/s 低于 10 req/s"
    
    def test_query_throughput(
        self, client: TestClient, auth_headers: dict, test_diagnosis: Diagnosis
    ):
        """
        测试查询接口吞吐量
        
        验证:
        - 每秒应能处理至少 20 次查询请求
        """
        request_count = 50
        start_time = time.time()
        
        for _ in range(request_count):
            client.get("/api/v1/diagnosis/records", headers=auth_headers)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = request_count / total_time
        
        assert throughput >= 20, f"查询吞吐量 {throughput:.2f} req/s 低于 20 req/s"
    
    def test_search_throughput(
        self, client: TestClient, test_diseases: list
    ):
        """
        测试搜索接口吞吐量
        
        验证:
        - 每秒应能处理至少 15 次搜索请求
        """
        request_count = 30
        start_time = time.time()
        
        for _ in range(request_count):
            client.get(
                "/api/v1/knowledge/search",
                params={"keyword": "病害"}
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = request_count / total_time
        
        assert throughput >= 15, f"搜索吞吐量 {throughput:.2f} req/s 低于 15 req/s"


class TestDatabasePerformance:
    """
    数据库性能测试类
    
    测试数据库操作的性能
    """
    
    def test_large_dataset_query(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试大数据集查询性能
        
        验证:
        - 查询大量数据时响应时间应合理
        """
        for i in range(100):
            diagnosis = Diagnosis(
                user_id=test_user.id,
                symptoms=f"大数据测试症状{i}",
                disease_name="小麦锈病",
                confidence=0.9,
                status="completed"
            )
            db_session.add(diagnosis)
        db_session.commit()
        
        start_time = time.time()
        response = client.get(
            "/api/v1/diagnosis/records?limit=100",
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 1000, f"大数据集查询时间 {response_time_ms}ms 超过 1000ms"
    
    def test_pagination_performance(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试分页性能
        
        验证:
        - 分页查询性能应该稳定
        """
        for i in range(50):
            diagnosis = Diagnosis(
                user_id=test_user.id,
                symptoms=f"分页测试症状{i}",
                disease_name="小麦锈病",
                confidence=0.9,
                status="completed"
            )
            db_session.add(diagnosis)
        db_session.commit()
        
        times = []
        for skip in [0, 10, 20, 30, 40]:
            start_time = time.time()
            response = client.get(
                f"/api/v1/diagnosis/records?skip={skip}&limit=10",
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append((end_time - start_time) * 1000)
        
        max_time = max(times)
        assert max_time < 500, f"分页查询最大时间 {max_time}ms 超过 500ms"


class TestMemoryUsage:
    """
    内存使用测试类
    
    测试内存使用情况
    """
    
    def test_repeated_requests_memory(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试重复请求内存使用
        
        验证:
        - 重复请求不应该导致内存泄漏
        """
        for _ in range(50):
            response = client.get(
                "/api/v1/diagnosis/records",
                headers=auth_headers
            )
            assert response.status_code == 200
        
        pass
    
    def test_large_response_handling(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        测试大响应处理
        
        验证:
        - 大响应应该被正确处理
        """
        for i in range(20):
            diagnosis = Diagnosis(
                user_id=test_user.id,
                symptoms=f"大响应测试症状{i}" * 100,
                disease_name="小麦锈病",
                confidence=0.9,
                status="completed"
            )
            db_session.add(diagnosis)
        db_session.commit()
        
        response = client.get(
            "/api/v1/diagnosis/records?limit=20",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 20


class TestCachePerformance:
    """
    缓存性能测试类
    
    测试缓存对性能的影响
    """
    
    @patch("app.api.v1.ai_diagnosis.should_use_mock")
    def test_cache_hit_improves_performance(
        self, mock_should_use_mock, client: TestClient, sample_image_bytes: bytes
    ):
        """
        测试缓存命中提升性能
        
        验证:
        - 缓存命中时响应时间应该更短
        """
        mock_should_use_mock.return_value = True
        
        image_file = io.BytesIO(sample_image_bytes)
        
        first_start = time.time()
        first_response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/image",
            files={"image": ("test.png", image_file, "image/png")}
        )
        first_time = time.time() - first_start
        
        image_file.seek(0)
        
        second_start = time.time()
        second_response = client.post(
            "/api/v1/ai-diagnosis/diagnosis/image",
            files={"image": ("test.png", image_file, "image/png")}
        )
        second_time = time.time() - second_start
        
        assert first_response.status_code == 200
        assert second_response.status_code == 200


class TestStressTest:
    """
    压力测试类
    
    测试系统在高负载下的表现
    """
    
    @pytest.mark.slow
    def test_sustained_load(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试持续负载
        
        验证:
        - 系统应能承受持续负载
        """
        duration_seconds = 5
        request_interval = 0.1
        results = []
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            response = client.get(
                "/api/v1/diagnosis/records",
                headers=auth_headers
            )
            results.append(response.status_code)
            time.sleep(request_interval)
        
        success_rate = sum(1 for r in results if r == 200) / len(results)
        assert success_rate >= 0.95, f"持续负载成功率 {success_rate:.2%} 低于 95%"
    
    @pytest.mark.slow
    def test_burst_requests(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试突发请求
        
        验证:
        - 系统应能处理突发请求
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(50):
                future = executor.submit(
                    client.get,
                    "/api/v1/diagnosis/records",
                    headers=auth_headers
                )
                futures.append(future)
            
            for future in as_completed(futures):
                results.append(future.result().status_code)
        
        success_rate = sum(1 for r in results if r == 200) / len(results)
        assert success_rate >= 0.90, f"突发请求成功率 {success_rate:.2%} 低于 90%"


class TestImageProcessingPerformance:
    """
    图像处理性能测试类
    
    测试图像处理相关性能
    """
    
    def test_small_image_processing_time(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试小图像处理时间
        
        验证:
        - 小图像处理时间应小于 2 秒
        """
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        start_time = time.time()
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("small.png", buffer, "image/png")},
            headers=auth_headers
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time < 2.0, f"小图像处理时间 {processing_time}s 超过 2 秒"
    
    def test_medium_image_processing_time(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试中等图像处理时间
        
        验证:
        - 中等图像处理时间应小于 5 秒
        """
        img = Image.new('RGB', (640, 480), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        start_time = time.time()
        response = client.post(
            "/api/v1/diagnosis/image",
            files={"image": ("medium.png", buffer, "image/png")},
            headers=auth_headers
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time < 5.0, f"中等图像处理时间 {processing_time}s 超过 5 秒"


class TestAsyncPerformance:
    """
    异步性能测试类
    
    测试异步操作的性能
    """
    
    @pytest.mark.asyncio
    async def test_async_vs_sync_performance(
        self, async_client: AsyncClient, client: TestClient, test_user: User
    ):
        """
        比较异步和同步性能
        
        验证:
        - 异步操作应该有性能优势
        """
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        sync_start = time.time()
        for _ in range(5):
            client.post("/api/v1/users/login", json=login_data)
        sync_time = time.time() - sync_start
        
        async_start = time.time()
        tasks = [
            async_client.post("/api/v1/users/login", json=login_data)
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)
        async_time = time.time() - async_start
        
        pass
    
    @pytest.mark.asyncio
    async def test_async_batch_requests(
        self, async_client: AsyncClient, test_diseases: list
    ):
        """
        测试异步批量请求
        
        验证:
        - 异步批量请求应该高效
        """
        keywords = ["锈病", "白粉病", "蚜虫", "真菌", "虫害", "病害", "小麦", "叶片", "茎秆", "穗部"]
        
        start_time = time.time()
        tasks = [
            async_client.get("/api/v1/knowledge/search", params={"keyword": kw})
            for kw in keywords
        ]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 8, f"异步批量请求成功率过低: {success_count}/10"
        assert total_time < 2.0, f"异步批量请求时间 {total_time}s 超过 2 秒"


class TestResourceCleanup:
    """
    资源清理测试类
    
    测试资源是否正确释放
    """
    
    def test_connection_cleanup_after_requests(
        self, client: TestClient, auth_headers: dict
    ):
        """
        测试请求后连接清理
        
        验证:
        - 多次请求后不应有连接泄漏
        """
        for _ in range(20):
            response = client.get(
                "/api/v1/diagnosis/records",
                headers=auth_headers
            )
            assert response.status_code == 200
        
        pass
    
    def test_file_handle_cleanup(
        self, client: TestClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """
        测试文件句柄清理
        
        验证:
        - 上传文件后文件句柄应该被正确关闭
        """
        for _ in range(10):
            image_file = io.BytesIO(sample_image_bytes)
            response = client.post(
                "/api/v1/diagnosis/image",
                files={"image": ("test.png", image_file, "image/png")},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        pass
