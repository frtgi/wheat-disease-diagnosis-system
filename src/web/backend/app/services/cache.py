"""
缓存服务模块
提供诊断结果等数据的缓存管理
"""
import json
from typing import Optional, Dict, Any
from datetime import timedelta
from collections import OrderedDict
import time as _time
from ..core.redis_client import get_async_redis
import redis.asyncio as aioredis
import logging
logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务类"""

    DIAGNOSIS_PREFIX = "diagnosis:"
    USER_PREFIX = "user:"
    KNOWLEDGE_PREFIX = "knowledge:"
    TOKEN_BLACKLIST_PREFIX = "revoked_token:"
    LOGIN_ATTEMPTS_PREFIX = "login_attempts:"

    DIAGNOSIS_TTL = int(timedelta(hours=24).total_seconds())
    USER_TTL = int(timedelta(hours=12).total_seconds())
    KNOWLEDGE_TTL = int(timedelta(hours=6).total_seconds())
    TOKEN_BLACKLIST_TTL = int(timedelta(hours=24).total_seconds())
    LOGIN_ATTEMPTS_TTL = int(timedelta(minutes=30).total_seconds())

    def __init__(self):
        """初始化缓存服务"""
        self._redis: Optional[aioredis.Redis] = None
        self._local_token_blacklist: OrderedDict = OrderedDict()
        self._local_token_blacklist_max = 1000
        self._local_login_attempts: Dict[str, Dict] = {}
        self._local_login_max_attempts = 5
        self._local_login_lockout_seconds = 1800

    async def _get_redis(self) -> aioredis.Redis:
        """获取 Redis 连接"""
        if self._redis is None:
            self._redis = await get_async_redis()
        return self._redis

    def _generate_diagnosis_key(self, image_md5: str) -> str:
        """生成诊断结果缓存键

        Args:
            image_md5: 图像的 MD5 哈希值

        Returns:
            缓存键字符串
        """
        return f"{self.DIAGNOSIS_PREFIX}{image_md5}"

    async def get_diagnosis(self, image_md5: str) -> Optional[Dict[str, Any]]:
        """获取诊断结果缓存

        Args:
            image_md5: 图像的 MD5 哈希值

        Returns:
            诊断结果字典，如果不存在则返回 None
        """
        try:
            redis_client = await self._get_redis()
            key = self._generate_diagnosis_key(image_md5)
            cached_data = await redis_client.get(key)

            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.debug(f"获取诊断缓存失败：{e}")
            return None

    async def set_diagnosis(self, image_md5: str, diagnosis_result: Dict[str, Any]) -> bool:
        """设置诊断结果缓存

        Args:
            image_md5: 图像的 MD5 哈希值
            diagnosis_result: 诊断结果字典

        Returns:
            是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._generate_diagnosis_key(image_md5)
            # 将字典序列化为 JSON 字符串
            await redis_client.setex(
                key,
                self.DIAGNOSIS_TTL,
                json.dumps(diagnosis_result, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.debug(f"设置诊断缓存失败：{e}")
            return False

    async def delete_diagnosis(self, image_md5: str) -> bool:
        """删除诊断结果缓存

        Args:
            image_md5: 图像的 MD5 哈希值

        Returns:
            是否删除成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._generate_diagnosis_key(image_md5)
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"删除诊断缓存失败：{e}")
            return False

    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息缓存

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典，如果不存在则返回 None
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.USER_PREFIX}{user_id}"
            cached_data = await redis_client.get(key)

            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.debug(f"获取用户缓存失败：{e}")
            return None

    async def set_user_info(self, user_id: int, user_info: Dict[str, Any]) -> bool:
        """设置用户信息缓存（自动过滤敏感字段）

        Args:
            user_id: 用户 ID
            user_info: 用户信息字典

        Returns:
            是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.USER_PREFIX}{user_id}"

            # 安全过滤：移除敏感字段，防止密码哈希泄露到缓存
            sensitive_fields = ['password', 'password_hash']
            safe_user_info = {k: v for k, v in user_info.items() if k not in sensitive_fields}

            await redis_client.setex(
                key,
                self.USER_TTL,
                json.dumps(safe_user_info, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.debug(f"设置用户缓存失败：{e}")
            return False

    async def invalidate_user_cache(self, user_id: int) -> bool:
        """使指定用户的缓存失效

        Args:
            user_id: 用户 ID

        Returns:
            是否成功
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.USER_PREFIX}{user_id}"
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"删除用户缓存失败：{e}")
            return False

    async def add_token_to_blacklist(self, token: str, expire: int = None) -> bool:
        """
        将 Token 添加到黑名单

        Args:
            token: JWT Token
            expire: 过期时间（秒），默认使用 TOKEN_BLACKLIST_TTL

        Returns:
            是否添加成功
        """
        ttl = expire or self.TOKEN_BLACKLIST_TTL
        expire_at = _time.time() + ttl
        self._local_token_blacklist[token] = expire_at
        self._local_token_blacklist.move_to_end(token)
        if len(self._local_token_blacklist) > self._local_token_blacklist_max:
            self._local_token_blacklist.popitem(last=False)
        try:
            redis_client = await self._get_redis()
            key = f"{self.TOKEN_BLACKLIST_PREFIX}{token}"
            await redis_client.setex(key, ttl, "1")
            return True
        except Exception as e:
            logger.debug(f"添加 Token 黑名单失败（已写入本地缓存）：{e}")
            return True

    async def is_token_revoked(self, token: str) -> bool:
        """
        检查 Token 是否已被撤销

        Args:
            token: JWT Token

        Returns:
            是否已被撤销
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.TOKEN_BLACKLIST_PREFIX}{token}"
            return await redis_client.exists(key) > 0
        except Exception as e:
            logger.debug(f"检查 Token 黑名单失败，检查本地缓存：{e}")
            expire_at = self._local_token_blacklist.get(token)
            if expire_at is not None:
                if _time.time() < expire_at:
                    return True
                else:
                    del self._local_token_blacklist[token]
            return False

    async def record_login_attempt(self, email: str, success: bool) -> int:
        """
        记录登录尝试

        Args:
            email: 用户邮箱
            success: 是否成功

        Returns:
            当前失败次数
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.LOGIN_ATTEMPTS_PREFIX}{email}"

            if success:
                await redis_client.delete(key)
                self._local_login_attempts.pop(email, None)
                return 0
            else:
                count = await redis_client.incr(key)
                if count == 1:
                    await redis_client.expire(key, self.LOGIN_ATTEMPTS_TTL)
                return count
        except Exception as e:
            logger.debug(f"记录登录尝试失败，使用本地计数器：{e}")
            if success:
                self._local_login_attempts.pop(email, None)
                return 0
            else:
                now = _time.time()
                attempt = self._local_login_attempts.get(email, {"count": 0, "first_attempt_at": now})
                attempt["count"] += 1
                if attempt["count"] == 1:
                    attempt["first_attempt_at"] = now
                elapsed = now - attempt["first_attempt_at"]
                if elapsed > self._local_login_lockout_seconds:
                    attempt["count"] = 1
                    attempt["first_attempt_at"] = now
                self._local_login_attempts[email] = attempt
                return attempt["count"]

    async def get_login_attempts(self, email: str) -> int:
        """
        获取登录失败次数

        Args:
            email: 用户邮箱

        Returns:
            失败次数
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.LOGIN_ATTEMPTS_PREFIX}{email}"
            count = await redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.debug(f"获取登录尝试次数失败，从本地计数器返回：{e}")
            attempt = self._local_login_attempts.get(email)
            if attempt is None:
                return 0
            now = _time.time()
            elapsed = now - attempt.get("first_attempt_at", now)
            if elapsed > self._local_login_lockout_seconds:
                self._local_login_attempts.pop(email, None)
                return 0
            return attempt.get("count", 0)

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            缓存统计字典
        """
        try:
            redis_client = await self._get_redis()
            info = await redis_client.info("stats")
            keys_count = await redis_client.dbsize()

            return {
                "connected": True,
                "keys_count": keys_count,
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }


# 创建全局缓存服务实例
cache_service = CacheService()
