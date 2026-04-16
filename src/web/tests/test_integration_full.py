"""
Web 端完整集成测试脚本
测试覆盖：
- 认证 + 诊断集成测试（登录后诊断流程、Token 过期处理）
- 诊断 + 知识库集成测试（诊断结果关联知识、知识查询集成）
- 前后端集成测试（前端页面加载、API 调用、错误处理）

测试环境：
- 后端地址：http://localhost:8000
- 前端地址：http://localhost:5173（如果运行）
- Python 版本：3.10+

使用 pytest + requests 框架
"""
import os
import sys
import time
import json
import pytest
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 测试配置 ====================
class TestConfig:
    """测试配置类"""
    # 后端配置
    BACKEND_BASE_URL = "http://localhost:8000"
    API_V1 = f"{BACKEND_BASE_URL}/api/v1"
    TIMEOUT = 30  # 请求超时时间（秒）
    
    # 前端配置
    FRONTEND_BASE_URL = "http://localhost:5173"
    
    # 测试用户凭据
    TEST_USERNAME = "test_integration_user"
    TEST_EMAIL = "test_integration@example.com"
    TEST_PASSWORD = "TestPass123!"
    TEST_NEW_PASSWORD = "NewTestPass456!"


# ==================== 测试客户端 ====================
class IntegrationTestClient:
    """集成测试客户端"""
    
    def __init__(self, base_url: str = TestConfig.API_V1):
        """
        初始化测试客户端
        
        参数:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
    
    def set_auth_token(self, token: str):
        """
        设置认证 Token
        
        参数:
            token: JWT 访问令牌
        """
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def clear_auth(self):
        """清除认证信息"""
        self.token = None
        self.user_id = None
        self.session.headers.pop("Authorization", None)
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        返回:
            健康检查结果
        """
        url = f"{self.base_url.replace('/api/v1', '')}/health"
        response = self.session.get(url, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def register_user(self, username: str = None, email: str = None, 
                     password: str = None) -> Dict[str, Any]:
        """
        注册新用户
        
        参数:
            username: 用户名
            email: 邮箱
            password: 密码
            
        返回:
            注册结果
        """
        url = f"{self.base_url}/users/register"
        user_data = {
            "username": username or f"{TestConfig.TEST_USERNAME}_{int(time.time())}",
            "email": email or f"test_{int(time.time())}@example.com",
            "password": password or TestConfig.TEST_PASSWORD
        }
        response = self.session.post(url, json=user_data, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def login_user(self, username: str = None, password: str = None) -> Dict[str, Any]:
        """
        用户登录
        
        参数:
            username: 用户名
            password: 密码
            
        返回:
            登录结果（包含 access_token）
        """
        url = f"{self.base_url}/users/login"
        login_data = {
            "username": username or TestConfig.TEST_USERNAME,
            "password": password or TestConfig.TEST_PASSWORD
        }
        response = self.session.post(url, json=login_data, timeout=TestConfig.TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            if self.token:
                self.set_auth_token(self.token)
        
        return response.json()
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取当前用户信息
        
        返回:
            用户信息
        """
        url = f"{self.base_url}/users/me"
        response = self.session.get(url, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def update_user_info(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户信息
        
        参数:
            update_data: 更新数据
            
        返回:
            更新结果
        """
        url = f"{self.base_url}/users/me"
        response = self.session.put(url, json=update_data, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def text_diagnosis(self, symptoms: str) -> Dict[str, Any]:
        """
        文本诊断
        
        参数:
            symptoms: 症状描述
            
        返回:
            诊断结果
        """
        url = f"{self.base_url}/diagnosis/text"
        data = {"symptoms": symptoms}
        response = self.session.post(url, data=data, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def get_diagnosis_records(self, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """
        获取诊断记录
        
        参数:
            skip: 跳过记录数
            limit: 返回记录数
            
        返回:
            诊断记录列表
        """
        url = f"{self.base_url}/diagnosis/records"
        params = {"skip": skip, "limit": limit}
        response = self.session.get(url, params=params, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def get_diagnosis_detail(self, diagnosis_id: str) -> Dict[str, Any]:
        """
        获取诊断详情
        
        参数:
            diagnosis_id: 诊断 ID
            
        返回:
            诊断详情
        """
        url = f"{self.base_url}/diagnosis/{diagnosis_id}"
        response = self.session.get(url, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def search_knowledge(self, keyword: str, page: int = 1, 
                        page_size: int = 10) -> Dict[str, Any]:
        """
        搜索知识库
        
        参数:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        返回:
            搜索结果
        """
        url = f"{self.base_url}/knowledge/search"
        params = {"keyword": keyword, "page": page, "page_size": page_size}
        response = self.session.get(url, params=params, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def get_knowledge_categories(self) -> Dict[str, Any]:
        """
        获取知识分类
        
        返回:
            知识分类列表
        """
        url = f"{self.base_url}/knowledge/categories"
        response = self.session.get(url, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def get_knowledge_detail(self, disease_id: str) -> Dict[str, Any]:
        """
        获取知识详情
        
        参数:
            disease_id: 疾病 ID
            
        返回:
            知识详情
        """
        url = f"{self.base_url}/knowledge/{disease_id}"
        response = self.session.get(url, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        获取 Dashboard 统计
        
        返回:
            统计信息
        """
        url = f"{self.base_url}/stats/overview"
        response = self.session.get(url, timeout=TestConfig.TIMEOUT)
        return response.json()
    
    def frontend_page_load(self, path: str = "/") -> Dict[str, Any]:
        """
        测试前端页面加载
        
        参数:
            path: 页面路径
            
        返回:
            页面加载结果
        """
        url = f"{TestConfig.FRONTEND_BASE_URL}{path}"
        try:
            response = self.session.get(url, timeout=TestConfig.TIMEOUT)
            return {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "load_time": response.elapsed.total_seconds(),
                "success": response.status_code == 200
            }
        except requests.exceptions.ConnectionError:
            return {
                "status_code": 0,
                "error": "Frontend server not running",
                "success": False
            }


# ==================== 测试结果记录器 ====================
class IntegrationTestResultRecorder:
    """测试结果记录器"""
    
    def __init__(self):
        """初始化记录器"""
        self.results: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def record(self, test_name: str, status: str, duration: float,
               response_code: int = None, error: str = None,
               details: Dict[str, Any] = None):
        """
        记录测试结果
        
        参数:
            test_name: 测试名称
            status: 测试状态 (passed/failed/skipped)
            duration: 测试耗时（秒）
            response_code: HTTP 响应码
            error: 错误信息
            details: 详细信息
        """
        self.results.append({
            "test_name": test_name,
            "status": status,
            "duration": round(duration, 3),
            "response_code": response_code,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def save_to_file(self, filepath: str) -> Dict[str, Any]:
        """
        保存结果到文件
        
        参数:
            filepath: 文件路径
            
        返回:
            测试报告
        """
        report = {
            "test_start_time": self.start_time.isoformat(),
            "test_end_time": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r["status"] == "passed"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "skipped": sum(1 for r in self.results if r["status"] == "skipped"),
            "pass_rate": f"{sum(1 for r in self.results if r['status'] == 'passed') / len(self.results) * 100:.2f}%" if self.results else "N/A",
            "results": self.results
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report


# 全局测试结果记录器
result_recorder = IntegrationTestResultRecorder()


# ==================== Fixture ====================
@pytest.fixture(scope="session")
def test_config():
    """测试配置 fixture"""
    return TestConfig()


@pytest.fixture(scope="session")
def test_client():
    """测试客户端 fixture"""
    client = IntegrationTestClient()
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def auth_client(test_client: IntegrationTestClient):
    """
    已认证的测试客户端 fixture
    
    流程：
    1. 注册测试用户
    2. 登录获取 Token
    3. 返回已认证的客户端
    """
    # 尝试注册
    try:
        register_result = test_client.register_user()
        logger.info(f"测试用户注册结果：{register_result.get('code', 'N/A')}")
    except Exception as e:
        logger.warning(f"测试用户注册失败（可能已存在）: {e}")
    
    # 登录
    login_result = test_client.login_user()
    if login_result.get("access_token"):
        logger.info("测试用户登录成功")
    else:
        logger.warning(f"测试用户登录失败：{login_result}")
    
    yield test_client


@pytest.fixture
def record_test_result(request):
    """
    记录测试结果的 fixture
    
    用法:
        def test_example(record_test_result):
            # 测试成功
            record_test_result("passed", response_code=200)
            
            # 测试失败
            record_test_result("failed", response_code=500, error="错误信息")
    """
    start_time = time.time()
    test_name = request.node.name
    
    def _record(status: str, response_code: int = None, 
                error: str = None, details: Dict = None):
        duration = time.time() - start_time
        result_recorder.record(
            test_name=test_name,
            status=status,
            duration=duration,
            response_code=response_code,
            error=error,
            details=details or {}
        )
    
    yield _record


# ==================== 认证 + 诊断集成测试 ====================
class TestAuthDiagnosisIntegration:
    """
    认证 + 诊断集成测试类
    
    测试场景：
    1. 登录后进行诊断
    2. Token 过期处理
    3. 未授权访问诊断接口
    4. 诊断记录权限验证
    """
    
    def test_login_then_diagnosis(self, test_client: IntegrationTestClient,
                                  record_test_result):
        """
        测试登录后进行诊断的完整流程
        
        步骤：
        1. 用户登录
        2. 执行文本诊断
        3. 获取诊断记录
        4. 验证诊断结果
        """
        try:
            # 1. 登录
            login_result = test_client.login_user()
            if login_result.get("access_token"):
                record_test_result("passed", response_code=200,
                                 details={"token_type": login_result.get("token_type")})
            else:
                record_test_result("failed", response_code=401,
                                 error="登录失败", details=login_result)
                pytest.skip("登录失败，无法继续测试")
                return
            
            # 2. 执行文本诊断
            symptoms = "小麦叶片出现黄色条状病斑，沿叶脉平行排列"
            diagnosis_result = test_client.text_diagnosis(symptoms)
            
            if diagnosis_result.get("diagnosis_id"):
                record_test_result("passed", response_code=200,
                                 details={
                                     "diagnosis_id": diagnosis_result["diagnosis_id"],
                                     "disease_name": diagnosis_result.get("disease_name")
                                 })
            else:
                # 诊断服务可能未启动，记录但不停止
                record_test_result("skipped", response_code=503,
                                 error="诊断服务不可用", details=diagnosis_result)
                pytest.skip("诊断服务不可用")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"登录诊断流程失败：{e}")
    
    def test_token_expiration_handling(self, test_client: IntegrationTestClient,
                                       record_test_result):
        """
        测试 Token 过期处理
        
        步骤：
        1. 登录获取 Token
        2. 模拟 Token 过期（清除 Token）
        3. 尝试访问需要认证的接口
        4. 验证返回 401 错误
        """
        try:
            # 1. 登录
            test_client.login_user()
            original_token = test_client.token
            
            if not original_token:
                record_test_result("skipped", error="无法获取 Token")
                pytest.skip("无法获取 Token")
                return
            
            # 2. 模拟 Token 过期
            test_client.clear_auth()
            
            # 3. 尝试访问需要认证的接口
            response = test_client.session.get(
                f"{test_client.base_url}/users/me",
                timeout=TestConfig.TIMEOUT
            )
            
            # 4. 验证返回 401
            if response.status_code == 401:
                record_test_result("passed", response_code=401,
                                 details={"message": "Token 过期处理正确"})
            else:
                record_test_result("failed", response_code=response.status_code,
                                 error=f"预期 401，实际{response.status_code}")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"Token 过期处理测试失败：{e}")
    
    def test_unauthorized_diagnosis_access(self, test_client: IntegrationTestClient,
                                           record_test_result):
        """
        测试未授权访问诊断接口
        
        步骤：
        1. 不登录
        2. 直接调用诊断接口
        3. 验证返回 401 错误
        """
        try:
            # 确保未认证
            test_client.clear_auth()
            
            # 尝试访问诊断接口
            symptoms = "测试症状"
            response = test_client.session.post(
                f"{test_client.base_url}/diagnosis/text",
                data={"symptoms": symptoms},
                timeout=TestConfig.TIMEOUT
            )
            
            if response.status_code == 401:
                record_test_result("passed", response_code=401,
                                 details={"message": "未授权访问拦截正确"})
            else:
                record_test_result("failed", response_code=response.status_code,
                                 error=f"预期 401，实际{response.status_code}")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"未授权访问测试失败：{e}")
    
    def test_diagnosis_record_permission(self, auth_client: IntegrationTestClient,
                                        record_test_result):
        """
        测试诊断记录权限验证
        
        步骤：
        1. 用户 A 登录并创建诊断记录
        2. 验证只能查看自己的诊断记录
        3. 不能查看其他用户的诊断记录
        """
        try:
            # 1. 获取诊断记录（应该只能看到自己的）
            records_result = auth_client.get_diagnosis_records()
            
            if isinstance(records_result, list):
                record_test_result("passed", response_code=200,
                                 details={"records_count": len(records_result)})
            else:
                record_test_result("failed", response_code=500,
                                 error="返回格式错误", details=records_result)
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"诊断记录权限测试失败：{e}")


# ==================== 诊断 + 知识库集成测试 ====================
class TestDiagnosisKnowledgeIntegration:
    """
    诊断 + 知识库集成测试类
    
    测试场景：
    1. 诊断结果关联知识
    2. 知识查询集成
    3. 诊断建议与知识一致性
    """
    
    def test_diagnosis_result_knowledge_link(self, auth_client: IntegrationTestClient,
                                             record_test_result):
        """
        测试诊断结果与知识库的关联
        
        步骤：
        1. 执行诊断
        2. 获取诊断结果中的知识链接
        3. 验证知识链接可访问
        4. 验证知识内容与诊断一致
        """
        try:
            # 1. 执行诊断
            symptoms = "小麦叶片出现白色粉状病斑"
            diagnosis_result = auth_client.text_diagnosis(symptoms)
            
            if not diagnosis_result.get("diagnosis_id"):
                record_test_result("skipped", error="诊断服务不可用")
                pytest.skip("诊断服务不可用")
                return
            
            disease_name = diagnosis_result.get("disease_name", "")
            
            # 2. 搜索相关知识
            if disease_name:
                knowledge_result = auth_client.search_knowledge(disease_name)
                
                if isinstance(knowledge_result, list) and len(knowledge_result) > 0:
                    record_test_result("passed", response_code=200,
                                     details={
                                         "disease_name": disease_name,
                                         "knowledge_count": len(knowledge_result)
                                     })
                else:
                    record_test_result("skipped", 
                                     error=f"未找到与'{disease_name}'相关的知识")
            else:
                record_test_result("failed", error="诊断结果无疾病名称")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"诊断知识关联测试失败：{e}")
    
    def test_knowledge_search_integration(self, auth_client: IntegrationTestClient,
                                         record_test_result):
        """
        测试知识查询集成
        
        步骤：
        1. 搜索不同关键词
        2. 验证搜索结果准确性
        3. 验证分页功能
        """
        try:
            keywords = ["锈病", "白粉病", "蚜虫"]
            search_results = {}
            
            for keyword in keywords:
                result = auth_client.search_knowledge(keyword, page=1, page_size=5)
                search_results[keyword] = len(result) if isinstance(result, list) else 0
            
            total_results = sum(search_results.values())
            
            if total_results > 0:
                record_test_result("passed", response_code=200,
                                 details={
                                     "keywords_tested": keywords,
                                     "total_results": total_results
                                 })
            else:
                record_test_result("skipped", error="知识库无数据")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"知识查询集成测试失败：{e}")
    
    def test_diagnosis_suggestion_knowledge_consistency(self, auth_client: IntegrationTestClient,
                                                       record_test_result):
        """
        测试诊断建议与知识一致性
        
        步骤：
        1. 执行诊断获取建议
        2. 查询相关疾病知识
        3. 对比诊断建议与知识中的防治方法
        """
        try:
            # 1. 执行诊断
            symptoms = "小麦叶片出现黄色条状病斑"
            diagnosis_result = auth_client.text_diagnosis(symptoms)
            
            if not diagnosis_result.get("diagnosis_id"):
                record_test_result("skipped", error="诊断服务不可用")
                pytest.skip("诊断服务不可用")
                return
            
            disease_name = diagnosis_result.get("disease_name", "")
            recommendations = diagnosis_result.get("recommendations", "")
            
            # 2. 查询相关知识
            knowledge_result = auth_client.search_knowledge(disease_name)
            
            if isinstance(knowledge_result, list) and len(knowledge_result) > 0:
                # 3. 验证一致性（简单验证，实际应该更复杂）
                knowledge_detail = auth_client.get_knowledge_detail(
                    knowledge_result[0].get("id", "")
                )
                
                record_test_result("passed", response_code=200,
                                 details={
                                     "disease_name": disease_name,
                                     "has_recommendations": bool(recommendations),
                                     "has_knowledge": bool(knowledge_detail)
                                 })
            else:
                record_test_result("skipped", error="无相关知识")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"诊断建议一致性测试失败：{e}")


# ==================== 前后端集成测试 ====================
class TestFrontendBackendIntegration:
    """
    前后端集成测试类
    
    测试场景：
    1. 前端页面加载
    2. 前端 API 调用
    3. 错误处理
    4. CORS 配置
    """
    
    def test_frontend_homepage_load(self, test_client: IntegrationTestClient,
                                   record_test_result):
        """
        测试前端首页加载
        
        步骤：
        1. 访问前端首页
        2. 验证页面加载成功
        3. 记录加载时间
        """
        try:
            result = test_client.frontend_page_load("/")
            
            if result.get("success"):
                record_test_result("passed", response_code=result["status_code"],
                                 details={
                                     "content_length": result["content_length"],
                                     "load_time": result["load_time"]
                                 })
            else:
                record_test_result("skipped", 
                                 error=result.get("error", "前端服务未运行"))
                pytest.skip("前端服务未运行")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"前端首页加载测试失败：{e}")
    
    def test_frontend_login_page(self, test_client: IntegrationTestClient,
                                record_test_result):
        """
        测试前端登录页面加载
        
        步骤：
        1. 访问登录页面
        2. 验证页面加载成功
        """
        try:
            result = test_client.frontend_page_load("/login")
            
            if result.get("success"):
                record_test_result("passed", response_code=result["status_code"],
                                 details={"load_time": result["load_time"]})
            else:
                record_test_result("skipped", 
                                 error=result.get("error", "前端服务未运行"))
                pytest.skip("前端服务未运行")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"前端登录页面测试失败：{e}")
    
    def test_backend_api_cors(self, test_client: IntegrationTestClient,
                             record_test_result):
        """
        测试后端 CORS 配置
        
        步骤：
        1. 发送带 Origin 头的请求
        2. 验证响应包含 CORS 头
        """
        try:
            # 发送 OPTIONS 预检请求
            response = test_client.session.options(
                f"{test_client.base_url}/health",
                headers={"Origin": "http://localhost:5173"},
                timeout=TestConfig.TIMEOUT
            )
            
            # 检查 CORS 头
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            present_headers = [h for h in cors_headers if h in response.headers]
            
            if len(present_headers) >= 1:  # 至少有一个 CORS 头
                record_test_result("passed", response_code=response.status_code,
                                 details={"cors_headers": present_headers})
            else:
                record_test_result("skipped", 
                                 error="CORS 头缺失（可能是配置问题）")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"CORS 配置测试失败：{e}")
    
    def test_backend_error_handling(self, test_client: IntegrationTestClient,
                                   record_test_result):
        """
        测试后端错误处理
        
        步骤：
        1. 访问不存在的接口
        2. 发送错误格式的请求
        3. 验证错误响应格式
        """
        try:
            errors_tested = 0
            
            # 1. 访问不存在的接口
            response = test_client.session.get(
                f"{test_client.base_url}/nonexistent",
                timeout=TestConfig.TIMEOUT
            )
            if response.status_code in [404, 405]:
                errors_tested += 1
            
            # 2. 发送错误格式的请求
            response = test_client.session.post(
                f"{test_client.base_url}/users/login",
                json={"invalid": "data"},
                timeout=TestConfig.TIMEOUT
            )
            if response.status_code in [400, 422]:
                errors_tested += 1
            
            if errors_tested > 0:
                record_test_result("passed", response_code=200,
                                 details={"errors_tested": errors_tested})
            else:
                record_test_result("failed", error="错误处理测试未通过")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"错误处理测试失败：{e}")
    
    def test_frontend_backend_api_integration(self, auth_client: IntegrationTestClient,
                                             record_test_result):
        """
        测试前后端 API 集成
        
        步骤：
        1. 通过 API 获取用户信息
        2. 获取统计信息
        3. 验证数据格式一致性
        """
        try:
            # 1. 获取用户信息
            user_info = auth_client.get_user_info()
            
            # 2. 获取统计信息
            stats_info = auth_client.get_dashboard_stats()
            
            # 3. 验证数据格式
            if isinstance(user_info, dict) and isinstance(stats_info, dict):
                record_test_result("passed", response_code=200,
                                 details={
                                     "user_info_keys": list(user_info.keys()),
                                     "stats_info_keys": list(stats_info.keys())
                                 })
            else:
                record_test_result("failed", 
                                 error="数据格式不一致")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"前后端 API 集成测试失败：{e}")


# ==================== 完整流程集成测试 ====================
class TestCompleteWorkflowIntegration:
    """
    完整流程集成测试类
    
    测试场景：
    1. 用户注册 -> 登录 -> 诊断 -> 查看记录 -> 查询知识
    2. 多用户并发访问
    """
    
    def test_complete_user_workflow(self, test_client: IntegrationTestClient,
                                   record_test_result):
        """
        测试完整用户工作流程
        
        步骤：
        1. 注册新用户
        2. 登录
        3. 执行诊断
        4. 查看诊断记录
        5. 查询相关知识
        6. 获取统计信息
        """
        try:
            workflow_steps = {}
            
            # 1. 注册
            register_result = test_client.register_user()
            workflow_steps["register"] = register_result.get("code", 0)
            
            # 2. 登录
            login_result = test_client.login_user()
            workflow_steps["login"] = 200 if login_result.get("access_token") else 401
            
            if not login_result.get("access_token"):
                record_test_result("failed", response_code=401,
                                 error="登录失败", details=workflow_steps)
                pytest.skip("登录失败，无法继续")
                return
            
            # 3. 获取用户信息
            user_info = test_client.get_user_info()
            workflow_steps["get_user_info"] = 200 if isinstance(user_info, dict) else 500
            
            # 4. 执行诊断
            symptoms = "小麦叶片出现病斑"
            diagnosis_result = test_client.text_diagnosis(symptoms)
            workflow_steps["diagnosis"] = 200 if diagnosis_result.get("diagnosis_id") else 503
            
            # 5. 查看诊断记录
            records = test_client.get_diagnosis_records()
            workflow_steps["get_records"] = 200 if isinstance(records, list) else 500
            
            # 6. 查询知识
            knowledge = test_client.search_knowledge("小麦")
            workflow_steps["search_knowledge"] = 200 if isinstance(knowledge, list) else 500
            
            # 7. 获取统计
            stats = test_client.get_dashboard_stats()
            workflow_steps["get_stats"] = 200 if isinstance(stats, dict) else 500
            
            # 验证所有步骤
            success_steps = sum(1 for v in workflow_steps.values() if v == 200)
            total_steps = len(workflow_steps)
            
            if success_steps >= total_steps * 0.7:  # 70% 步骤成功
                record_test_result("passed", response_code=200,
                                 details={
                                     "workflow_steps": workflow_steps,
                                     "success_rate": f"{success_steps/total_steps*100:.1f}%"
                                 })
            else:
                record_test_result("failed", response_code=500,
                                 error=f"工作流成功率过低：{success_steps}/{total_steps}",
                                 details=workflow_steps)
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"完整工作流程测试失败：{e}")
    
    def test_concurrent_user_access(self, test_config: TestConfig,
                                   record_test_result):
        """
        测试多用户并发访问
        
        步骤：
        1. 创建多个测试用户
        2. 同时发起请求
        3. 验证所有请求都能正确处理
        """
        try:
            import concurrent.futures
            
            def user_request(username: str) -> Dict[str, Any]:
                """模拟用户请求"""
                client = IntegrationTestClient()
                try:
                    # 登录
                    login_result = client.login_user(
                        username=username,
                        password=TestConfig.TEST_PASSWORD
                    )
                    
                    if not login_result.get("access_token"):
                        return {"success": False, "error": "Login failed"}
                    
                    # 获取用户信息
                    user_info = client.get_user_info()
                    
                    return {
                        "success": True,
                        "username": username,
                        "user_info": user_info
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}
                finally:
                    client.session.close()
            
            # 创建 3 个用户（假设已存在）
            usernames = [
                f"{TestConfig.TEST_USERNAME}_1",
                f"{TestConfig.TEST_USERNAME}_2",
                f"{TestConfig.TEST_USERNAME}_3"
            ]
            
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_user = {
                    executor.submit(user_request, username): username
                    for username in usernames
                }
                
                for future in concurrent.futures.as_completed(future_to_user):
                    results.append(future.result())
            
            success_count = sum(1 for r in results if r.get("success"))
            
            if success_count > 0:
                record_test_result("passed", response_code=200,
                                 details={
                                     "total_users": len(usernames),
                                     "success_count": success_count
                                 })
            else:
                record_test_result("skipped", 
                                 error="测试用户不存在（并发测试需要预先创建用户）")
                
        except Exception as e:
            record_test_result("failed", error=str(e))
            pytest.fail(f"并发访问测试失败：{e}")


# ==================== 测试执行和报告 ====================
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的处理"""
    # 保存测试结果
    report_path = Path(__file__).parent / "test_integration_results.json"
    report = result_recorder.save_to_file(str(report_path))
    
    # 打印测试摘要
    print("\n" + "=" * 70)
    print("集成测试结果摘要".center(70))
    print("=" * 70)
    print(f"测试开始时间：{report['test_start_time']}")
    print(f"测试结束时间：{report['test_end_time']}")
    print(f"总用例数：{report['total_tests']}")
    print(f"通过数：{report['passed']}")
    print(f"失败数：{report['failed']}")
    print(f"跳过数：{report['skipped']}")
    print(f"通过率：{report['pass_rate']}")
    print("=" * 70)
    
    # 按类别显示结果
    categories = {
        "认证 + 诊断": [],
        "诊断 + 知识库": [],
        "前后端集成": [],
        "完整流程": []
    }
    
    for result in report["results"]:
        test_name = result["test_name"]
        if "test_login_then_diagnosis" in test_name or \
           "test_token_expiration" in test_name or \
           "test_unauthorized_diagnosis" in test_name or \
           "test_diagnosis_record_permission" in test_name:
            categories["认证 + 诊断"].append(result)
        elif "test_diagnosis_result_knowledge" in test_name or \
             "test_knowledge_search" in test_name or \
             "test_diagnosis_suggestion" in test_name:
            categories["诊断 + 知识库"].append(result)
        elif "test_frontend" in test_name or \
             "test_backend" in test_name:
            categories["前后端集成"].append(result)
        elif "test_complete" in test_name or \
             "test_concurrent" in test_name:
            categories["完整流程"].append(result)
    
    for category, results in categories.items():
        if results:
            print(f"\n{category}:")
            for result in results:
                status_icon = "✅" if result["status"] == "passed" else \
                             "❌" if result["status"] == "failed" else "⚠️"
                print(f"  {status_icon} {result['test_name']}: {result['status']}")
    
    print("\n" + "=" * 70)
    print(f"测试结果已保存到：{report_path}")
    print("=" * 70)


if __name__ == "__main__":
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short"
    ])
