"""
缓存装饰器模块
提供便捷的缓存装饰器，用于 API 响应缓存
"""
import functools
import hashlib
import json
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def cache_response(
    ttl: int = 3600,
    key_prefix: str = "",
    cache_none: bool = False
):
    """
    API 响应缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        cache_none: 是否缓存 None 值

    Returns:
        装饰器函数

    使用示例:
        @cache_response(ttl=3600, key_prefix="user")
        async def get_user(user_id: int, db: Session):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            from ..services.cache import cache_service

            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            try:
                cached_result = await cache_service._get_redis().get(cache_key)
                if cached_result:
                    logger.debug(f"缓存命中：{cache_key}")
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"读取缓存失败：{e}")

            result = await func(*args, **kwargs)

            if result is not None or cache_none:
                try:
                    await cache_service._get_redis().setex(
                        cache_key,
                        ttl,
                        json.dumps(result, ensure_ascii=False, default=str)
                    )
                    logger.debug(f"缓存已设置：{cache_key}")
                except Exception as e:
                    logger.warning(f"设置缓存失败：{e}")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            from ..services.cache import cache_service
            import asyncio

            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            try:
                loop = asyncio.get_event_loop()
                cached_result = loop.run_until_complete(
                    cache_service._get_redis().get(cache_key)
                )
                if cached_result:
                    logger.debug(f"缓存命中：{cache_key}")
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"读取缓存失败：{e}")

            result = func(*args, **kwargs)

            if result is not None or cache_none:
                try:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(
                        cache_service._get_redis().setex(
                            cache_key,
                            ttl,
                            json.dumps(result, ensure_ascii=False, default=str)
                        )
                    )
                    logger.debug(f"缓存已设置：{cache_key}")
                except Exception as e:
                    logger.warning(f"设置缓存失败：{e}")

            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cache_user_info(ttl: int = 43200):
    """
    用户信息缓存装饰器（默认 12 小时）

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        装饰器函数
    """
    return cache_response(ttl=ttl, key_prefix="user_info")


def cache_diagnosis_history(ttl: int = 300):
    """
    诊断历史缓存装饰器（默认 5 分钟）

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        装饰器函数
    """
    return cache_response(ttl=ttl, key_prefix="diagnosis_history")


def cache_knowledge_query(ttl: int = 21600):
    """
    知识图谱查询缓存装饰器（默认 6 小时）

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        装饰器函数
    """
    return cache_response(ttl=ttl, key_prefix="knowledge_query")


def cache_disease_info(ttl: int = 86400):
    """
    疾病信息缓存装饰器（默认 24 小时）

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        装饰器函数
    """
    return cache_response(ttl=ttl, key_prefix="disease_info")


def _generate_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: str
) -> str:
    """
    生成缓存键

    Args:
        func: 函数对象
        args: 位置参数
        kwargs: 关键字参数
        prefix: 键前缀

    Returns:
        缓存键字符串
    """
    key_parts = [prefix, func.__module__, func.__name__]

    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(str(arg.id))
        elif isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))

    for k, v in sorted(kwargs.items()):
        if k not in ['db', 'request', 'current_user']:
            if hasattr(v, 'id'):
                key_parts.append(f"{k}:{v.id}")
            elif isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")

    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()

    return f"cache:{key_hash}"


async def invalidate_cache_pattern(pattern: str):
    """
    使匹配模式的所有缓存失效

    Args:
        pattern: 缓存键模式（支持通配符 *）
    """
    from ..services.cache import cache_service

    try:
        redis = await cache_service._get_redis()
        keys = await redis.keys(pattern)

        if keys:
            await redis.delete(*keys)
            logger.info(f"已清除 {len(keys)} 个缓存键：{pattern}")
    except Exception as e:
        logger.error(f"清除缓存失败：{e}")


async def invalidate_user_cache(user_id: int):
    """
    使用户相关的所有缓存失效

    Args:
        user_id: 用户 ID
    """
    await invalidate_cache_pattern(f"*user*:{user_id}*")
    await invalidate_cache_pattern(f"*diagnosis_history*:{user_id}*")


async def invalidate_knowledge_cache():
    """
    使知识图谱相关的所有缓存失效
    """
    await invalidate_cache_pattern("*knowledge_query*")
    await invalidate_cache_pattern("*disease_info*")
