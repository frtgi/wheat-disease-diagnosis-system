"""
数据库连接模块
提供 SQLAlchemy 数据库引擎和会话管理
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, AsyncAdaptedQueuePool

from .config import settings

logger = logging.getLogger(__name__)

DB_POOL_SIZE = settings.DB_POOL_SIZE
DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW
DB_POOL_TIMEOUT = settings.DB_POOL_TIMEOUT
DB_POOL_RECYCLE = settings.DB_POOL_RECYCLE
DB_ECHO = settings.DEBUG

engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    echo=DB_ECHO,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

sync_engine = create_engine(
    settings.DATABASE_URL.replace("+aiomysql", "+pymysql"),
    poolclass=QueuePool,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    echo=DB_ECHO,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    expire_on_commit=False
)


@event.listens_for(sync_engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """数据库连接建立时的回调"""
    logger.debug(f"数据库连接建立: {id(dbapi_connection)}")


@event.listens_for(sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """从连接池获取连接时的回调"""


@event.listens_for(sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """连接归还到连接池时的回调"""

Base = declarative_base()


def get_db() -> Session:
    """
    获取数据库会话的依赖注入函数（同步版本）
    
    使用方式:
        @app.get("/items/")
        def get_items(db: Session = Depends(get_db)):
            ...
    
    返回:
        数据库会话对象
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_async() -> Session:
    """
    获取数据库会话的依赖注入函数（异步版本）
    
    使用方式:
        @app.get("/items/")
        async def get_items(db: Session = Depends(get_db_async)):
            ...
    
    返回:
        数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    创建所有数据表（使用同步引擎）
    """
    Base.metadata.create_all(bind=sync_engine)


async def init_db_async() -> None:
    """
    初始化数据库（异步版本）
    创建所有数据表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
