# -*- coding: utf-8 -*-
"""
推理结果缓存服务模块
基于 Redis 实现推理结果缓存，支持图像哈希和 TTL 过期机制
"""
import json
import logging
import time
from typing import Optional, Dict, Any
from datetime import timedelta
from dataclasses import dataclass, field

from ..core.redis_client import get_async_redis
from ..utils.image_hash import ImageHash, ImageHashCacheKey

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis.asyncio 不可用，缓存功能受限")

try:
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class CacheStats:
    """缓存统计数据"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_saved_time_ms: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    @property
    def hit_rate(self) -> float:
        """计算缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    @property
    def avg_saved_time_ms(self) -> float:
        """计算平均节省时间"""
        if self.cache_hits == 0:
            return 0.0
        return self.total_saved_time_ms / self.cache_hits
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        uptime = time.time() - self.start_time
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": round(self.hit_rate, 2),
            "total_saved_time_ms": round(self.total_saved_time_ms, 2),
            "avg_saved_time_ms": round(self.avg_saved_time_ms, 2),
            "uptime_seconds": round(uptime, 2)
        }


class InferenceCacheService:
    """
    推理结果缓存服务
    
    功能：
    1. 基于 Redis 的分布式缓存
    2. 支持图像哈希（MD5 + pHash）
    3. 支持 TTL 过期机制
    4. 缓存命中/未命中统计
    5. 相似图像检测（可选）
    """
    
    CACHE_PREFIX = "inference:diagnosis:"
    STATS_PREFIX = "inference:stats:"
    PHASH_INDEX_PREFIX = "inference:phash_index:"
    
    DEFAULT_TTL = int(timedelta(hours=24).total_seconds())
    SIMILARITY_THRESHOLD = 5
    
    def __init__(
        self,
        ttl: int = None,
        enable_similar_search: bool = True,
        similarity_threshold: int = 5
    ):
        """
        初始化缓存服务
        
        Args:
            ttl: 缓存过期时间（秒），默认 24 小时
            enable_similar_search: 是否启用相似图像搜索
            similarity_threshold: 相似度阈值（汉明距离）
        """
        self._redis: Optional[aioredis.Redis] = None
        self.ttl = ttl or self.DEFAULT_TTL
        self.enable_similar_search = enable_similar_search
        self.similarity_threshold = similarity_threshold
        self._stats = CacheStats()
    
    async def _get_redis(self) -> aioredis.Redis:
        """
        获取 Redis 连接
        
        Returns:
            Redis 异步客户端
        """
        if self._redis is None:
            if not REDIS_AVAILABLE:
                raise RuntimeError("Redis 库不可用")
            self._redis = await get_async_redis()
        return self._redis
    
    def _generate_cache_key(
        self,
        image_data: bytes,
        symptoms: str = "",
        extra_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成缓存键
        
        Args:
            image_data: 图像二进制数据
            symptoms: 症状描述
            extra_params: 额外参数
            
        Returns:
            缓存键字符串
        """
        params = {}
        if symptoms:
            params["symptoms"] = symptoms[:100]
        if extra_params:
            params.update(extra_params)
        
        return ImageHashCacheKey.generate_key(
            image_data=image_data,
            prefix="diagnosis",
            include_phash=True,
            extra_params=params if params else None
        )
    
    async def get(
        self,
        image_data: bytes,
        symptoms: str = "",
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的推理结果
        
        查询策略：
        1. 精确匹配：使用 MD5 + pHash + 参数哈希
        2. 相似匹配：如果启用，搜索相似图像的缓存
        
        Args:
            image_data: 图像二进制数据
            symptoms: 症状描述
            extra_params: 额外参数
            
        Returns:
            缓存的诊断结果，未命中返回 None
        """
        self._stats.total_requests += 1
        time.time()
        
        try:
            redis_client = await self._get_redis()
            
            cache_key = self._generate_cache_key(image_data, symptoms, extra_params)
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                self._stats.cache_hits += 1
                result = json.loads(cached_data)
                result["_cache_hit"] = True
                result["_cache_key"] = cache_key[:32] + "..."
                
                logger.info(f"缓存命中: {cache_key[:32]}...")
                return result
            
            if self.enable_similar_search:
                similar_result = await self._search_similar(
                    image_data, symptoms, redis_client
                )
                if similar_result:
                    self._stats.cache_hits += 1
                    similar_result["_cache_hit"] = True
                    similar_result["_similar_match"] = True
                    logger.info("相似图像缓存命中")
                    return similar_result
            
            self._stats.cache_misses += 1
            logger.debug(f"缓存未命中: {cache_key[:32]}...")
            return None
            
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            self._stats.cache_misses += 1
            return None
    
    async def set(
        self,
        image_data: bytes,
        result: Dict[str, Any],
        symptoms: str = "",
        extra_params: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        保存推理结果到缓存
        
        Args:
            image_data: 图像二进制数据
            result: 诊断结果
            symptoms: 症状描述
            extra_params: 额外参数
            ttl: 过期时间（秒），默认使用实例 TTL
            
        Returns:
            是否保存成功
        """
        try:
            redis_client = await self._get_redis()
            
            cache_key = self._generate_cache_key(image_data, symptoms, extra_params)
            
            cache_data = {
                "result": result,
                "symptoms": symptoms[:100] if symptoms else "",
                "timestamp": time.time()
            }
            
            await redis_client.setex(
                cache_key,
                ttl or self.ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            if self.enable_similar_search:
                await self._update_phash_index(image_data, cache_key, redis_client)
            
            logger.info(f"缓存已保存: {cache_key[:32]}...")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    async def _search_similar(
        self,
        image_data: bytes,
        symptoms: str,
        redis_client: aioredis.Redis
    ) -> Optional[Dict[str, Any]]:
        """
        搜索相似图像的缓存结果
        
        Args:
            image_data: 图像二进制数据
            symptoms: 症状描述
            redis_client: Redis 客户端
            
        Returns:
            相似图像的缓存结果
        """
        try:
            phash = ImageHash.compute_phash(image_data)
            if not phash:
                return None
            
            pattern = f"{self.PHASH_INDEX_PREFIX}*"
            keys = await redis_client.keys(pattern)
            
            for key in keys[:50]:
                try:
                    stored_phash = key.split(":")[-1]
                    
                    if ImageHash.is_similar(phash, stored_phash, self.similarity_threshold):
                        cache_key = await redis_client.get(key)
                        if cache_key:
                            cached_data = await redis_client.get(cache_key)
                            if cached_data:
                                data = json.loads(cached_data)
                                if not symptoms or data.get("symptoms", "") == symptoms:
                                    return data.get("result")
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"相似图像搜索失败: {e}")
            return None
    
    async def _update_phash_index(
        self,
        image_data: bytes,
        cache_key: str,
        redis_client: aioredis.Redis
    ) -> None:
        """
        更新 pHash 索引
        
        Args:
            image_data: 图像二进制数据
            cache_key: 缓存键
            redis_client: Redis 客户端
        """
        try:
            phash = ImageHash.compute_phash(image_data)
            if phash:
                index_key = f"{self.PHASH_INDEX_PREFIX}{phash}"
                await redis_client.setex(
                    index_key,
                    self.ttl,
                    cache_key
                )
        except Exception as e:
            logger.debug(f"更新 pHash 索引失败: {e}")
    
    async def delete(
        self,
        image_data: bytes,
        symptoms: str = "",
        extra_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        删除缓存的推理结果
        
        Args:
            image_data: 图像二进制数据
            symptoms: 症状描述
            extra_params: 额外参数
            
        Returns:
            是否删除成功
        """
        try:
            redis_client = await self._get_redis()
            cache_key = self._generate_cache_key(image_data, symptoms, extra_params)
            await redis_client.delete(cache_key)
            logger.info(f"缓存已删除: {cache_key[:32]}...")
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    async def clear_all(self) -> int:
        """
        清空所有推理缓存
        
        Returns:
            删除的键数量
        """
        try:
            redis_client = await self._get_redis()
            
            patterns = [
                f"{self.CACHE_PREFIX}*",
                f"{self.PHASH_INDEX_PREFIX}*"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = await redis_client.keys(pattern)
                if keys:
                    deleted_count += await redis_client.delete(*keys)
            
            logger.info(f"已清空 {deleted_count} 个缓存键")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        try:
            redis_client = await self._get_redis()
            
            diagnosis_keys = await redis_client.keys(f"{self.CACHE_PREFIX}*")
            phash_keys = await redis_client.keys(f"{self.PHASH_INDEX_PREFIX}*")
            
            redis_info = await redis_client.info("stats")
            
            stats = self._stats.to_dict()
            stats.update({
                "cache_keys_count": len(diagnosis_keys),
                "phash_index_count": len(phash_keys),
                "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                "redis_keyspace_misses": redis_info.get("keyspace_misses", 0),
                "ttl_seconds": self.ttl,
                "similar_search_enabled": self.enable_similar_search,
                "similarity_threshold": self.similarity_threshold
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return self._stats.to_dict()
    
    def update_saved_time(self, saved_time_ms: float) -> None:
        """
        更新节省的时间统计
        
        Args:
            saved_time_ms: 节省的时间（毫秒）
        """
        self._stats.total_saved_time_ms += saved_time_ms
    
    async def get_cache_info(
        self,
        image_data: bytes,
        symptoms: str = "",
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取缓存信息（不返回结果）
        
        Args:
            image_data: 图像二进制数据
            symptoms: 症状描述
            extra_params: 额外参数
            
        Returns:
            缓存信息字典
        """
        try:
            redis_client = await self._get_redis()
            cache_key = self._generate_cache_key(image_data, symptoms, extra_params)
            
            exists = await redis_client.exists(cache_key)
            ttl = await redis_client.ttl(cache_key) if exists else -1
            
            hashes = ImageHash.compute_all_hashes(image_data)
            
            return {
                "cache_key": cache_key,
                "exists": exists > 0,
                "ttl_seconds": ttl,
                "hashes": hashes
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {"error": str(e)}


_inference_cache_instance: Optional[InferenceCacheService] = None


def get_inference_cache() -> InferenceCacheService:
    """
    获取推理缓存服务单例
    
    Returns:
        InferenceCacheService 实例
    """
    global _inference_cache_instance
    
    if _inference_cache_instance is None:
        _inference_cache_instance = InferenceCacheService(
            ttl=int(timedelta(hours=24).total_seconds()),
            enable_similar_search=True,
            similarity_threshold=5
        )
    
    return _inference_cache_instance


async def initialize_inference_cache(
    ttl: int = None,
    enable_similar_search: bool = True,
    similarity_threshold: int = 5
) -> InferenceCacheService:
    """
    初始化推理缓存服务
    
    Args:
        ttl: 缓存过期时间（秒）
        enable_similar_search: 是否启用相似图像搜索
        similarity_threshold: 相似度阈值
        
    Returns:
        InferenceCacheService 实例
    """
    global _inference_cache_instance
    
    _inference_cache_instance = InferenceCacheService(
        ttl=ttl or int(timedelta(hours=24).total_seconds()),
        enable_similar_search=enable_similar_search,
        similarity_threshold=similarity_threshold
    )
    
    logger.info(
        f"推理缓存服务已初始化: TTL={_inference_cache_instance.ttl}s, "
        f"相似搜索={'启用' if enable_similar_search else '禁用'}"
    )
    
    return _inference_cache_instance
