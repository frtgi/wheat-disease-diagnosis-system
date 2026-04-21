"""
Redis 连接管理模块
提供 Redis 连接池和客户端管理
"""
import redis
from redis import asyncio as aioredis
from typing import Optional
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 客户端管理类"""

    _instance: Optional[redis.Redis] = None
    _async_instance: Optional[aioredis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        获取同步 Redis 客户端（单例模式）

        配置说明：
        - max_connections: 最大连接数
        - socket_connect_timeout: 连接超时
        - socket_timeout: 读写超时
        - retry_on_timeout: 超时时自动重试
        """
        if cls._instance is None:
            cls._instance = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=50,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            logger.info("Redis 同步客户端初始化完成")
        return cls._instance

    @classmethod
    async def get_async_client(cls) -> aioredis.Redis:
        """
        获取异步 Redis 客户端（单例模式）

        配置说明：
        - max_connections: 最大连接数
        - socket_connect_timeout: 连接超时
        - socket_timeout: 读写超时
        - retry_on_timeout: 超时时自动重试
        - health_check_interval: 健康检查间隔
        """
        if cls._async_instance is None:
            cls._async_instance = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=50,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            logger.info("Redis 异步客户端初始化完成")
        return cls._async_instance

    @classmethod
    def test_connection(cls) -> bool:
        """测试 Redis 连接"""
        try:
            client = cls.get_client()
            client.ping()
            return True
        except Exception as e:
            logger.debug(f"Redis 连接测试失败: {e}")
            return False

    @classmethod
    async def test_async_connection(cls) -> bool:
        """测试异步 Redis 连接"""
        try:
            client = await cls.get_async_client()
            await client.ping()
            return True
        except Exception as e:
            logger.debug(f"Redis 异步连接测试失败: {e}")
            return False

    @classmethod
    def close(cls):
        """关闭 Redis 连接"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis 同步客户端连接已关闭")

    @classmethod
    async def close_async(cls):
        """关闭异步 Redis 连接"""
        if cls._async_instance:
            await cls._async_instance.close()
            cls._async_instance = None
            logger.info("Redis 异步客户端连接已关闭")


def get_redis() -> redis.Redis:
    """获取 Redis 客户端实例"""
    return RedisClient.get_client()


async def get_async_redis() -> aioredis.Redis:
    """获取异步 Redis 客户端实例"""
    return await RedisClient.get_async_client()
