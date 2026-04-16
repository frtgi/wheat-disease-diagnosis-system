# -*- coding: utf-8 -*-
"""
集成测试 Pytest 配置模块
提供集成测试专用的 fixtures 和配置
"""
import os
import sys
import asyncio
from typing import Generator, AsyncGenerator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from PIL import Image
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.disease import Disease
from app.models.diagnosis import Diagnosis


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """
    创建事件循环
    
    返回:
        asyncio 事件循环
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """
    创建异步测试数据库引擎
    
    返回:
        异步数据库引擎
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
        异步数据库会话
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
    
    返回:
        同步数据库引擎
    """
    engine = create_engine(
        TEST_SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
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
        同步数据库会话
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
        FastAPI 测试客户端
    """
    from app.main import app
    from app.core.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建异步测试客户端
    
    参数:
        async_session: 异步数据库会话
    
    返回:
        异步 HTTP 客户端
    """
    from app.main import app
    from app.core.database import get_db_async
    
    async def override_get_db_async():
        yield async_session
    
    app.dependency_overrides[get_db_async] = override_get_db_async
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """
    创建测试用户
    
    参数:
        db_session: 数据库会话
    
    返回:
        测试用户对象
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
        测试管理员用户对象
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
def auth_headers(test_user: User) -> dict:
    """
    创建认证请求头
    
    参数:
        test_user: 测试用户
    
    返回:
        包含 Bearer Token 的请求头字典
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
        包含 Bearer Token 的请求头字典
    """
    access_token = create_access_token(data={"sub": test_admin.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_disease(db_session: Session) -> Disease:
    """
    创建测试病害数据
    
    参数:
        db_session: 数据库会话
    
    返回:
        测试病害对象
    """
    disease = Disease(
        name="小麦条锈病",
        category="真菌病害",
        symptoms="叶片出现黄色条纹状病斑",
        cause="条形柄锈菌感染",
        treatment="喷洒三唑酮",
        prevention="选用抗病品种",
    )
    db_session.add(disease)
    db_session.commit()
    db_session.refresh(disease)
    return disease


@pytest.fixture(scope="function")
def test_diagnosis(db_session: Session, test_user: User, test_disease: Disease) -> Diagnosis:
    """
    创建测试诊断记录
    
    参数:
        db_session: 数据库会话
        test_user: 测试用户
        test_disease: 测试病害
    
    返回:
        测试诊断记录对象
    """
    diagnosis = Diagnosis(
        user_id=test_user.id,
        disease_id=test_disease.id,
        image_url="http://example.com/test.jpg",
        disease_name="小麦条锈病",
        confidence=0.95,
        status="completed",
    )
    db_session.add(diagnosis)
    db_session.commit()
    db_session.refresh(diagnosis)
    return diagnosis


@pytest.fixture(scope="function")
def sample_image() -> bytes:
    """
    创建测试用的样本图像
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (640, 480), color='green')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


@pytest.fixture(scope="function")
def sample_image_file(sample_image: bytes) -> io.BytesIO:
    """
    创建测试用的样本图像文件对象
    
    参数:
        sample_image: 样本图像字节数据
    
    返回:
        BytesIO 文件对象
    """
    return io.BytesIO(sample_image)


@pytest.fixture(scope="function")
def sample_wheat_disease_image() -> bytes:
    """
    创建模拟小麦病害图像（带有黄色斑点）
    
    返回:
        PNG 格式的图像字节数据
    """
    image = Image.new('RGB', (640, 480), color='green')
    
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    
    for _ in range(10):
        x = 50 + (_ * 50)
        y = 100 + (_ * 20)
        draw.ellipse([x, y, x + 30, y + 30], fill='yellow')
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


@pytest.fixture(scope="function")
def multiple_test_diseases(db_session: Session) -> list:
    """
    创建多个测试病害数据
    
    参数:
        db_session: 数据库会话
    
    返回:
        测试病害列表
    """
    diseases = [
        Disease(
            name="小麦条锈病",
            category="真菌病害",
            symptoms="叶片出现黄色条纹状病斑",
            cause="条形柄锈菌感染",
            treatment="喷洒三唑酮",
            prevention="选用抗病品种",
        ),
        Disease(
            name="小麦白粉病",
            category="真菌病害",
            symptoms="叶片出现白色粉状霉层",
            cause="禾本科布氏白粉菌感染",
            treatment="喷洒三唑酮",
            prevention="控制氮肥",
        ),
        Disease(
            name="小麦赤霉病",
            category="真菌病害",
            symptoms="穗部出现粉红色霉层",
            cause="禾谷镰刀菌感染",
            treatment="喷洒多菌灵",
            prevention="适期播种",
        ),
    ]
    
    for disease in diseases:
        db_session.add(disease)
    
    db_session.commit()
    
    for disease in diseases:
        db_session.refresh(disease)
    
    return diseases


def pytest_configure(config):
    """
    Pytest 配置钩子
    注册自定义标记
    """
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "api: 标记 API 测试"
    )
    config.addinivalue_line(
        "markers", "yolo: 标记 YOLO 服务测试"
    )
    config.addinivalue_line(
        "markers", "qwen: 标记 Qwen 服务测试"
    )
    config.addinivalue_line(
        "markers", "fusion: 标记 Fusion 服务测试"
    )
    config.addinivalue_line(
        "markers", "graphrag: 标记 GraphRAG 服务测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记运行较慢的测试"
    )
    config.addinivalue_line(
        "markers", "gpu: 标记需要 GPU 的测试"
    )
