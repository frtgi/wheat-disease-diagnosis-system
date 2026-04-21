"""
缓存管理服务模块

提供多层次的推理缓存优化：
1. 图像哈希缓存（基于 MD5 和感知哈希）
2. LRU 缓存策略（带 TTL）
3. 语义缓存（基于症状描述相似性）
4. 缓存性能监控
"""

import hashlib
import time
import logging
import threading
from typing import Any, Dict, Optional
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime

try:
    import io
    import numpy as np
    from PIL import Image
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None  # Time To Live (秒)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl
    
    def touch(self) -> None:
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1


class ImageHasher:
    """图像哈希生成器"""
    
    @staticmethod
    def compute_md5(image_data: Optional[bytes]) -> Optional[str]:
        """
        计算图像 MD5 哈希

        Args:
            image_data: 图像二进制数据，如果为 None 则返回 None

        Returns:
            MD5 哈希字符串，如果 image_data 为 None 则返回 None
        """
        if image_data is None:
            return None
        return hashlib.md5(image_data).hexdigest()
    
    @staticmethod
    def compute_perceptual_hash(image_data: bytes, hash_size: int = 8) -> Optional[str]:
        """
        计算感知哈希 (pHash)
        
        感知哈希对图像的缩放、旋转、亮度变化具有鲁棒性
        适合用于相似图像检索
        """
        if not IMAGE_PROCESSING_AVAILABLE:
            logger.warning("PIL 或 numpy 不可用，无法计算感知哈希")
            return None
        
        try:
            # 转换为灰度图并调整大小
            image = Image.open(io.BytesIO(image_data))
            image = image.convert("L")  # 转为灰度
            image = image.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            
            # 计算像素差异
            pixels = np.array(image)
            diff = pixels[:, 1:] > pixels[:, :-1]
            
            # 转换为十六进制字符串
            hash_array = diff.flatten()
            hash_int = int("".join(str(int(b)) for b in hash_array), 2)
            return f"{hash_int:0{hash_size * hash_size // 4}x}"
        
        except Exception as e:
            logger.error(f"计算感知哈希失败：{e}")
            return None
    
    @staticmethod
    def compute_hash(image_data: bytes, method: str = "both") -> Dict[str, str]:
        """
        计算图像哈希
        
        Args:
            image_data: 图像二进制数据
            method: "md5", "perceptual", 或 "both"
        
        Returns:
            包含哈希值的字典
        """
        result = {}
        
        if method in ("md5", "both"):
            result["md5"] = ImageHasher.compute_md5(image_data)
        
        if method in ("perceptual", "both"):
            phash = ImageHasher.compute_perceptual_hash(image_data)
            if phash:
                result["perceptual"] = phash
        
        return result
    
    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """计算两个哈希值的汉明距离"""
        if len(hash1) != len(hash2):
            raise ValueError("哈希长度不匹配")
        
        distance = 0
        for c1, c2 in zip(hash1, hash2):
            # 十六进制转换为二进制并计算差异
            val1 = int(c1, 16)
            val2 = int(c2, 16)
            xor = val1 ^ val2
            distance += bin(xor).count("1")
        
        return distance
    
    @staticmethod
    def is_similar(hash1: str, hash2: str, threshold: int = 5) -> bool:
        """判断两个哈希是否相似（汉明距离小于阈值）"""
        try:
            return ImageHasher.hamming_distance(hash1, hash2) <= threshold
        except Exception:
            return False


class LRUCache:
    """LRU 缓存实现（线程安全，支持 TTL）"""

    def __init__(self, capacity: int = 1000, default_ttl: Optional[float] = None):
        """
        初始化 LRU 缓存

        Args:
            capacity: 最大容量
            default_ttl: 默认 TTL（秒），None 表示永不过期
        """
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            if entry.is_expired():
                self.delete(key)
                self._misses += 1
                return None

            self._hits += 1
            entry.touch()
            self._cache.move_to_end(key)

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

            while len(self._cache) >= self.capacity:
                self._evict_oldest()

            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl if ttl is not None else self.default_ttl,
                metadata=metadata or {}
            )

            self._cache[key] = entry

    def put(self, key: str, value: Any, ttl: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        添加缓存项（兼容接口）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            metadata: 元数据

        Returns:
            如果缓存已满，返回被移除的最久未使用的键；否则返回 None
        """
        with self._lock:
            evicted_key = None
            if key in self._cache:
                del self._cache[key]
            else:
                if len(self._cache) >= self.capacity:
                    evicted_key = self._evict_oldest()

            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl if ttl is not None else self.default_ttl,
                metadata=metadata or {}
            )
            self._cache[key] = entry
            return evicted_key

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def remove(self, key: str) -> Optional[Any]:
        """
        移除缓存项并返回值（兼容接口）

        Args:
            key: 缓存键

        Returns:
            被移除的缓存值，不存在则返回 None
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                return entry.value
            return None

    def _evict_oldest(self) -> Optional[str]:
        """淘汰最旧的条目，返回被淘汰的键"""
        if self._cache:
            oldest_key, _ = self._cache.popitem(last=False)
            self._evictions += 1
            return oldest_key
        return None

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """清理所有过期条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]
                self._evictions += 1

            return len(expired_keys)

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)

    def get_size(self) -> int:
        """获取当前缓存大小（兼容接口）"""
        return self.size()

    def get_lru_key(self) -> Optional[str]:
        """
        获取最久未使用的键（兼容接口）

        Returns:
            最久未使用的键，缓存为空则返回 None
        """
        with self._lock:
            if not self._cache:
                return None
            return next(iter(self._cache.keys()))

    def get_keys(self) -> list:
        """获取所有键（按访问时间排序，最近访问的在最后）"""
        with self._lock:
            return list(self._cache.keys())

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "capacity": self.capacity,
                "size": self.size(),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": round(hit_rate, 2),
                "utilization": round(self.size() / self.capacity * 100, 2)
            }


class SemanticCache:
    """语义缓存（基于症状描述相似性）"""
    
    def __init__(self, capacity: int = 500, similarity_threshold: float = 0.85):
        """
        初始化语义缓存
        
        Args:
            capacity: 最大容量
            similarity_threshold: 相似度阈值（0-1）
        """
        self.capacity = capacity
        self.similarity_threshold = similarity_threshold
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._embeddings: Dict[str, np.ndarray] = {}
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """
        计算文本嵌入（简化版：使用词袋模型）
        
        实际应用中应使用 Sentence-BERT 等模型
        """
        # 简化实现：词频向量
        words = text.lower().split()
        embedding = np.zeros(1000)  # 简化词袋
        
        for i, word in enumerate(words[:100]):  # 限制词汇量
            idx = int(hashlib.sha256(word.encode('utf-8')).hexdigest()[:8], 16) % 1000
            embedding[idx] += 1
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def search(self, symptoms: str) -> Optional[Dict[str, Any]]:
        """搜索相似症状的缓存结果"""
        query_embedding = self._compute_embedding(symptoms)
        
        for key, entry in self._cache.items():
            if key in self._embeddings:
                similarity = self._cosine_similarity(
                    query_embedding, 
                    self._embeddings[key]
                )
                
                if similarity >= self.similarity_threshold:
                    # 更新访问统计
                    entry.touch()
                    self._cache.move_to_end(key)
                    
                    logger.debug(f"语义缓存命中：相似度={similarity:.3f}")
                    return {
                        "result": entry.value,
                        "similarity": round(similarity, 3),
                        "metadata": entry.metadata
                    }
        
        return None
    
    def add(self, symptoms: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加到缓存"""
        # 计算嵌入
        embedding = self._compute_embedding(symptoms)
        
        # 如果超出容量，删除最旧的
        while len(self._cache) >= self.capacity:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            if oldest_key in self._embeddings:
                del self._embeddings[oldest_key]
        
        # 创建条目
        key = f"semantic_{hashlib.md5(symptoms.encode()).hexdigest()[:16]}"
        entry = CacheEntry(
            key=key,
            value=result,
            ttl=3600,  # 1 小时 TTL
            metadata=metadata or {}
        )
        
        self._cache[key] = entry
        self._embeddings[key] = embedding
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._embeddings.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class CacheManager:
    """缓存管理器（统一管理多层缓存）"""
    
    def __init__(
        self,
        image_cache_capacity: int = 1000,
        semantic_cache_capacity: int = 500,
        default_ttl: float = 3600,
        enable_image_cache: bool = True,
        enable_semantic_cache: bool = True
    ):
        """
        初始化缓存管理器
        
        Args:
            image_cache_capacity: 图像缓存容量
            semantic_cache_capacity: 语义缓存容量
            default_ttl: 默认 TTL（秒）
            enable_image_cache: 是否启用图像缓存
            enable_semantic_cache: 是否启用语义缓存
        """
        self.enable_image_cache = enable_image_cache
        self.enable_semantic_cache = enable_semantic_cache
        
        # 图像哈希缓存
        self.image_cache = LRUCache(
            capacity=image_cache_capacity,
            default_ttl=default_ttl
        )
        
        # 语义缓存
        self.semantic_cache = SemanticCache(
            capacity=semantic_cache_capacity,
            similarity_threshold=0.85
        )
        
        # 统计信息
        self._total_requests = 0
        self._cache_hits = 0
        self._start_time = time.time()
    
    def _generate_image_cache_key(self, image_data: Optional[bytes], symptoms: str = "") -> Optional[str]:
        """
        生成图像缓存键

        Args:
            image_data: 图像二进制数据，如果为 None 则返回 None
            symptoms: 症状描述

        Returns:
            缓存键字符串，如果 image_data 为 None 则返回 None
        """
        if image_data is None:
            return None
        image_hash = ImageHasher.compute_md5(image_data)
        if image_hash is None:
            return None
        symptoms_hash = hashlib.md5(symptoms.encode()).hexdigest()[:8]
        return f"image_{image_hash}_{symptoms_hash}"
    
    def get(self, image_data: Optional[bytes], symptoms: str = "") -> Optional[Dict[str, Any]]:
        """
        从缓存获取诊断结果

        Args:
            image_data: 图像二进制数据，如果为 None 则仅使用语义缓存
            symptoms: 症状描述

        Returns:
            缓存的诊断结果，None 表示未命中
        """
        self._total_requests += 1

        # 1. 尝试图像哈希缓存（仅当 image_data 不为 None 时）
        if self.enable_image_cache and image_data is not None:
            cache_key = self._generate_image_cache_key(image_data, symptoms)
            if cache_key is not None:
                result = self.image_cache.get(cache_key)

                if result is not None:
                    self._cache_hits += 1
                    logger.info(f"图像缓存命中：{cache_key[:16]}...")
                    return {"source": "image_cache", "result": result}

        # 2. 尝试语义缓存（如果有症状描述）
        if self.enable_semantic_cache and symptoms:
            semantic_result = self.semantic_cache.search(symptoms)

            if semantic_result is not None:
                self._cache_hits += 1
                logger.info(
                    f"语义缓存命中：相似度={semantic_result['similarity']:.3f}"
                )
                return {
                    "source": "semantic_cache",
                    "result": semantic_result["result"],
                    "similarity": semantic_result["similarity"]
                }

        return None
    
    def set(
        self,
        image_data: Optional[bytes],
        symptoms: str,
        diagnosis_result: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        将诊断结果添加到缓存

        Args:
            image_data: 图像二进制数据，如果为 None 则仅使用语义缓存
            symptoms: 症状描述
            diagnosis_result: 诊断结果
            ttl: TTL（秒）
        """
        # 1. 添加到图像缓存（仅当 image_data 不为 None 时）
        if self.enable_image_cache and image_data is not None:
            cache_key = self._generate_image_cache_key(image_data, symptoms)
            if cache_key is not None:
                self.image_cache.set(
                    key=cache_key,
                    value=diagnosis_result,
                    ttl=ttl,
                    metadata={
                        "symptoms": symptoms[:100],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.debug(f"图像缓存已更新：{cache_key[:16]}...")

        # 2. 添加到语义缓存
        if self.enable_semantic_cache and symptoms:
            image_hash = ImageHasher.compute_md5(image_data)
            self.semantic_cache.add(
                symptoms=symptoms,
                result=diagnosis_result,
                metadata={
                    "image_hash": image_hash[:16] if image_hash else "no_image",
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.debug(f"语义缓存已更新")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        uptime = time.time() - self._start_time
        
        image_stats = self.image_cache.stats() if self.enable_image_cache else {}
        semantic_stats = {
            "size": self.semantic_cache.size(),
            "capacity": self.semantic_cache.capacity
        } if self.enable_semantic_cache else {}
        
        hit_rate = (
            self._cache_hits / self._total_requests * 100
            if self._total_requests > 0
            else 0.0
        )
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "overall_hit_rate": round(hit_rate, 2),
            "image_cache": image_stats,
            "semantic_cache": semantic_stats,
            "enabled": {
                "image_cache": self.enable_image_cache,
                "semantic_cache": self.enable_semantic_cache
            }
        }
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.image_cache.clear()
        self.semantic_cache.clear()
        self._total_requests = 0
        self._cache_hits = 0
        logger.info("缓存已清空")
    
    def cleanup(self) -> Dict[str, int]:
        """清理过期缓存"""
        expired_count = 0
        
        if self.enable_image_cache:
            expired_count += self.image_cache.cleanup_expired()
        
        logger.info(f"清理了 {expired_count} 个过期缓存条目")
        return {"expired_count": expired_count}


# 全局缓存管理器实例
cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager(
            image_cache_capacity=1000,
            semantic_cache_capacity=500,
            default_ttl=3600,
            enable_image_cache=True,
            enable_semantic_cache=True
        )
    return cache_manager


def initialize_cache(
    image_capacity: int = 1000,
    semantic_capacity: int = 500,
    ttl: float = 3600
) -> CacheManager:
    """初始化缓存管理器"""
    global cache_manager
    cache_manager = CacheManager(
        image_cache_capacity=image_capacity,
        semantic_cache_capacity=semantic_capacity,
        default_ttl=ttl,
        enable_image_cache=True,
        enable_semantic_cache=True
    )
    logger.info(f"缓存管理器已初始化：图像容量={image_capacity}, 语义容量={semantic_capacity}")
    return cache_manager
