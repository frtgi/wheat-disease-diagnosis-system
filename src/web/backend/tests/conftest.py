"""
Pytest 测试配置模块
提供测试数据库、测试客户端、用户认证、测试数据等 fixtures
支持单元测试、集成测试、端到端测试
"""
import os
import sys
import asyncio
import tempfile
import shutil
from typing import Generator, AsyncGenerator
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env_test_path = Path(__file__).parent.parent / ".env.test"
if env_test_path.exists():
    load_dotenv(env_test_path, override=True)
    print(f"✅ 已加载测试环境配置文件: {env_test_path}")
else:
    print(f"⚠️ 测试环境配置文件不存在: {env_test_path}")

from app.core.database import Base
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.disease import Disease
from app.models.diagnosis import Diagnosis
from app.models.knowledge import KnowledgeGraph
from app.models.auth import PasswordResetToken, RefreshToken, LoginAttempt, UserSession


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"

TEST_DATA_DIR = Path(__file__).parent / "test_data"


def pytest_configure(config):
    """
    Pytest 配置钩子
    注册自定义标记和配置测试环境
    
    参数:
        config: pytest 配置对象
    """
    config.addinivalue_line("markers", "slow: 标记运行较慢的测试")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "unit: 标记单元测试")
    config.addinivalue_line("markers", "e2e: 标记端到端测试")
    config.addinivalue_line("markers", "api: 标记 API 测试")
    config.addinivalue_line("markers", "db: 标记需要数据库的测试")
    config.addinivalue_line("markers", "auth: 标记需要认证的测试")
    config.addinivalue_line("markers", "ai: 标记需要 AI 模型的测试")
    config.addinivalue_line("markers", "gpu: 标记需要 GPU 的测试")
    
    os.environ["TESTING"] = "true"
    os.environ["APP_ENV"] = "test"


def pytest_collection_modifyitems(config, items):
    """
    Pytest 收集修改钩子
    根据标记跳过特定测试
    
    参数:
        config: pytest 配置对象
        items: 测试项列表
    """
    skip_slow = pytest.mark.skip(reason="需要 --runslow 选项运行")
    skip_ai = pytest.mark.skip(reason="需要 --runai 选项运行")
    skip_gpu = pytest.mark.skip(reason="需要 GPU 支持")
    
    for item in items:
        if "slow" in item.keywords and not config.getoption("--runslow", default=False):
            item.add_marker(skip_slow)
        if "ai" in item.keywords and not config.getoption("--runai", default=False):
            item.add_marker(skip_ai)
        if "gpu" in item.keywords and not os.environ.get("CUDA_VISIBLE_DEVICES"):
            item.add_marker(skip_gpu)


def pytest_addoption(parser):
    """
    添加自定义命令行选项
    
    参数:
        parser: pytest 解析器
    """
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="运行标记为 slow 的测试"
    )
    parser.addoption(
        "--runai",
        action="store_true",
        default=False,
        help="运行标记为 ai 的测试（需要 AI 模型）"
    )
    parser.addoption(
        "--rungpu",
        action="store_true",
        default=False,
        help="运行标记为 gpu 的测试（需要 GPU）"
    )


@pytest.fixture(scope="session")
def event_loop():
    """
    创建会话级别的事件循环
    
    返回:
        asyncio.AbstractEventLoop: 事件循环实例
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """
    获取测试数据目录路径
    
    返回:
        Path: 测试数据目录路径
    """
    test_dir = TEST_DATA_DIR
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """
    创建临时目录用于测试
    
    返回:
        Path: 临时目录路径
    """
    temp_path = Path(tempfile.mkdtemp(prefix="wheatagent_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
async def async_engine():
    """
    创建异步测试数据库引擎
    使用内存 SQLite 数据库
    
    返回:
        AsyncEngine: 异步数据库引擎
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    创建异步数据库会话
    
    参数:
        async_engine: 异步数据库引擎
    
    返回:
        AsyncSession: 异步数据库会话
    """
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def sync_engine():
    """
    创建同步测试数据库引擎
    使用内存 SQLite 数据库
    
    返回:
        Engine: 同步数据库引擎
    """
    engine = create_engine(
        TEST_SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """设置 SQLite PRAGMA 选项"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(sync_engine) -> Generator[Session, None, None]:
    """
    创建同步数据库会话
    
    参数:
        sync_engine: 同步数据库引擎
    
    返回:
        Session: 同步数据库会话
    """
    session_maker = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    session = session_maker()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    创建测试客户端
    
    参数:
        db_session: 数据库会话
    
    返回:
        TestClient: FastAPI 测试客户端
    """
    from app.main import app
    from app.core.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建异步测试客户端
    
    参数:
        async_session: 异步数据库会话
    
    返回:
        AsyncClient: 异步 HTTP 客户端
    """
    from app.main import app
    from app.core.database import get_db_async
    
    async def override_get_db_async():
        yield async_session
    
    app.dependency_overrides[get_db_async] = override_get_db_async
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """
    创建测试用户
    
    参数:
        db_session: 数据库会话
    
    返回:
        User: 测试用户对象
    """
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        role="farmer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin(db_session: Session) -> User:
    """
    创建测试管理员用户
    
    参数:
        db_session: 数据库会话
    
    返回:
        User: 测试管理员用户对象
    """
    admin = User(
        username="adminuser",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def test_technician(db_session: Session) -> User:
    """
    创建测试农技人员用户
    
    参数:
        db_session: 数据库会话
    
    返回:
        User: 测试农技人员用户对象
    """
    technician = User(
        username="techuser",
        email="tech@example.com",
        password_hash=get_password_hash("techpass123"),
        role="technician",
        is_active=True,
    )
    db_session.add(technician)
    db_session.commit()
    db_session.refresh(technician)
    return technician


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """
    创建认证请求头
    
    参数:
        test_user: 测试用户
    
    返回:
        dict: 包含 Bearer Token 的请求头字典
    """
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(test_admin: User) -> dict:
    """
    创建管理员认证请求头
    
    参数:
        test_admin: 测试管理员用户
    
    返回:
        dict: 包含 Bearer Token 的请求头字典
    """
    access_token = create_access_token(data={"sub": test_admin.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def technician_auth_headers(test_technician: User) -> dict:
    """
    创建农技人员认证请求头
    
    参数:
        test_technician: 测试农技人员用户
    
    返回:
        dict: 包含 Bearer Token 的请求头字典
    """
    access_token = create_access_token(data={"sub": test_technician.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_disease(db_session: Session) -> Disease:
    """
    创建测试病害数据
    
    参数:
        db_session: 数据库会话
    
    返回:
        Disease: 测试病害对象
    """
    disease = Disease(
        name="小麦锈病",
        category="真菌病害",
        symptoms="叶片出现黄色锈斑",
        cause="锈菌感染",
        treatment="喷洒杀菌剂",
        prevention="选用抗病品种",
        image_url="http://example.com/rust.jpg",
    )
    db_session.add(disease)
    db_session.commit()
    db_session.refresh(disease)
    return disease


@pytest.fixture(scope="function")
def test_diseases(db_session: Session) -> list:
    """
    创建多个测试病害数据
    
    参数:
        db_session: 数据库会话
    
    返回:
        list: 测试病害列表
    """
    diseases_data = [
        {
            "name": "小麦锈病",
            "category": "真菌病害",
            "symptoms": "叶片出现黄色锈斑",
            "cause": "锈菌感染",
            "treatment": "喷洒杀菌剂",
            "prevention": "选用抗病品种",
        },
        {
            "name": "小麦白粉病",
            "category": "真菌病害",
            "symptoms": "叶片出现白色粉状物",
            "cause": "白粉菌感染",
            "treatment": "喷洒三唑酮",
            "prevention": "合理密植",
        },
        {
            "name": "小麦蚜虫",
            "category": "虫害",
            "symptoms": "叶片发黄卷曲",
            "cause": "蚜虫侵害",
            "treatment": "喷洒吡虫啉",
            "prevention": "清除田间杂草",
        },
    ]
    
    diseases = []
    for data in diseases_data:
        disease = Disease(**data)
        db_session.add(disease)
        diseases.append(disease)
    
    db_session.commit()
    for disease in diseases:
        db_session.refresh(disease)
    
    return diseases


@pytest.fixture(scope="function")
def test_diagnosis(db_session: Session, test_user: User, test_disease: Disease) -> Diagnosis:
    """
    创建测试诊断记录
    
    参数:
        db_session: 数据库会话
        test_user: 测试用户
        test_disease: 测试病害
    
    返回:
        Diagnosis: 测试诊断记录对象
    """
    diagnosis = Diagnosis(
        user_id=test_user.id,
        disease_id=test_disease.id,
        image_url="http://example.com/test.jpg",
        result="小麦锈病",
        confidence=0.95,
        status="completed",
    )
    db_session.add(diagnosis)
    db_session.commit()
    db_session.refresh(diagnosis)
    return diagnosis


@pytest.fixture(scope="function")
def multiple_test_users(db_session: Session) -> list:
    """
    创建多个测试用户
    
    参数:
        db_session: 数据库会话
    
    返回:
        list: 测试用户列表
    """
    users = []
    for i in range(5):
        user = User(
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            password_hash=get_password_hash(f"testpass{i}"),
            role="farmer",
            is_active=True,
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    
    return users


@pytest.fixture(scope="function")
def clean_db(db_session: Session):
    """
    清理数据库的 fixture
    
    参数:
        db_session: 数据库会话
    """
    yield db_session
    
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()


@pytest.fixture(scope="function")
def mock_redis():
    """
    创建 Redis 模拟对象
    
    返回:
        MagicMock: Redis 模拟对象
    """
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.keys = AsyncMock(return_value=[])
    return redis_mock


@pytest.fixture(scope="function")
def mock_yolo_service():
    """
    创建 YOLO 服务模拟对象
    
    返回:
        MagicMock: YOLO 服务模拟对象
    """
    service_mock = MagicMock()
    service_mock.detect = MagicMock(return_value={
        "success": True,
        "detections": [
            {
                "class_id": 0,
                "class_name": "Yellow Rust",
                "chinese_name": "条锈病",
                "confidence": 0.95,
                "bbox": [100, 100, 200, 200],
            }
        ],
        "count": 1,
        "inference_time": 0.05,
    })
    service_mock.is_loaded = True
    return service_mock


@pytest.fixture(scope="function")
def mock_qwen_service():
    """
    创建 Qwen 服务模拟对象
    
    返回:
        MagicMock: Qwen 服务模拟对象
    """
    service_mock = MagicMock()
    service_mock.diagnose = MagicMock(return_value={
        "success": True,
        "diagnosis": {
            "disease_name": "小麦锈病",
            "confidence": 0.92,
            "description": "叶片出现典型的锈病症状",
            "recommendations": ["建议喷洒三唑酮杀菌剂"],
        },
        "treatment": "建议喷洒三唑酮杀菌剂",
        "prevention": "选用抗病品种，合理轮作",
    })
    service_mock.is_loaded = True
    return service_mock


@pytest.fixture(scope="function")
def mock_fusion_service():
    """
    创建融合服务模拟对象
    
    返回:
        MagicMock: 融合服务模拟对象
    """
    service_mock = MagicMock()
    service_mock.diagnose = MagicMock(return_value={
        "success": True,
        "diagnosis": {
            "disease_name": "小麦锈病",
            "confidence": 0.94,
            "visual_confidence": 0.92,
            "textual_confidence": 0.88,
            "description": "叶片出现黄色锈斑",
            "recommendations": ["喷洒杀菌剂", "清除病残体"],
            "severity": "中度",
        },
        "model": "fusion_engine",
        "features": {
            "visual_detection": True,
            "textual_analysis": True,
            "graph_rag_enabled": True,
        }
    })
    service_mock._initialized = True
    return service_mock


@pytest.fixture(scope="function")
def mock_graphrag_service():
    """
    创建 GraphRAG 服务模拟对象
    
    返回:
        MagicMock: GraphRAG 服务模拟对象
    """
    service_mock = MagicMock()
    service_mock.retrieve_disease_knowledge = MagicMock(return_value=MagicMock(
        triples=[],
        entities=["小麦锈病", "锈菌", "杀菌剂"],
        citations=[],
        tokens=None,
    ))
    service_mock._initialized = True
    return service_mock


@pytest.fixture(scope="function")
def sample_image_bytes() -> bytes:
    """
    生成测试图像字节数据
    创建一个简单的 PNG 图像
    
    返回:
        bytes: PNG 图像字节数据
    """
    import io
    from PIL import Image
    
    img = Image.new('RGB', (640, 480), color=(255, 255, 255))
    
    for x in range(100, 200):
        for y in range(100, 200):
            img.putpixel((x, y), (255, 165, 0))
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture(scope="function")
def sample_image_file(temp_dir: Path, sample_image_bytes: bytes) -> Path:
    """
    创建测试图像文件
    
    参数:
        temp_dir: 临时目录
        sample_image_bytes: 图像字节数据
    
    返回:
        Path: 图像文件路径
    """
    image_path = temp_dir / "test_wheat_image.png"
    image_path.write_bytes(sample_image_bytes)
    return image_path


@pytest.fixture(scope="function")
def sample_diagnosis_request() -> dict:
    """
    创建测试诊断请求数据
    
    返回:
        dict: 诊断请求数据字典
    """
    return {
        "image_url": "http://example.com/test.jpg",
        "crop_type": "wheat",
        "location": {
            "province": "河南省",
            "city": "郑州市",
            "latitude": 34.7466,
            "longitude": 113.6253,
        },
        "environment": {
            "temperature": 25.5,
            "humidity": 65.0,
            "soil_ph": 6.8,
        },
        "notes": "发现叶片有黄色斑点",
    }


@pytest.fixture(scope="function")
def sample_user_register_data() -> dict:
    """
    创建测试用户注册数据
    
    返回:
        dict: 用户注册数据字典
    """
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "role": "farmer",
    }


@pytest.fixture(scope="function")
def sample_user_login_data() -> dict:
    """
    创建测试用户登录数据
    
    返回:
        dict: 用户登录数据字典
    """
    return {
        "username": "testuser",
        "password": "testpass123",
    }


@pytest.fixture(scope="function")
def mock_settings():
    """
    创建测试环境配置模拟
    
    返回:
        dict: 测试配置字典
    """
    return {
        "APP_NAME": "WheatAgent Test",
        "DEBUG": True,
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": "redis://localhost:6379/15",
        "JWT_SECRET_KEY": "test_secret_key_for_testing_only",
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRE_HOURS": 1,
        "CORS_ORIGINS": ["http://localhost:3000"],
    }


@pytest.fixture(scope="function")
def mock_ai_config():
    """
    创建 AI 配置模拟对象
    
    返回:
        MagicMock: AI 配置模拟对象
    """
    config_mock = MagicMock()
    config_mock.QWEN_MODEL_PATH = Path("/fake/path/to/qwen")
    config_mock.YOLO_MODEL_PATH = Path("/fake/path/to/yolo/best.pt")
    config_mock.YOLO_CONFIDENCE_THRESHOLD = 0.5
    config_mock.YOLO_IOU_THRESHOLD = 0.45
    config_mock.YOLO_MAX_DETECTIONS = 100
    config_mock.QWEN_MAX_LENGTH = 512
    config_mock.QWEN_TEMPERATURE = 0.7
    config_mock.QWEN_MAX_NEW_TOKENS = 768
    config_mock.ENABLE_KAD_FORMER = True
    config_mock.ENABLE_GRAPH_RAG = True
    return config_mock


@pytest.fixture(scope="function")
def performance_metrics():
    """
    创建性能指标收集器
    
    返回:
        dict: 性能指标字典
    """
    return {
        "start_time": None,
        "end_time": None,
        "duration": None,
        "memory_before": None,
        "memory_after": None,
        "memory_delta": None,
    }
