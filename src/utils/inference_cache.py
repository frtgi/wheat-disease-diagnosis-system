# -*- coding: utf-8 -*-
"""
推理缓存模块 (Inference Cache)

提供推理结果缓存功能，加速相同图像的重复推理：
- 图像哈希缓存
- LRU淘汰策略
- 缓存命中率统计
- 持久化缓存支持
"""
import os
import time
import json
import hashlib
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import OrderedDict
from datetime import datetime


@dataclass
class CacheEntry:
    """
    缓存条目
    
    :param result: 推理结果
    :param timestamp: 创建时间戳
    :param hit_count: 命中次数
    :param image_hash: 图像哈希值
    :param metadata: 额外元数据
    """
    result: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    hit_count: int = 0
    image_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "result": self.result,
            "timestamp": self.timestamp,
            "hit_count": self.hit_count,
            "image_hash": self.image_hash,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """从字典创建"""
        return cls(
            result=data.get("result", {}),
            timestamp=data.get("timestamp", time.time()),
            hit_count=data.get("hit_count", 0),
            image_hash=data.get("image_hash", ""),
            metadata=data.get("metadata", {})
        )


class ImageHasher:
    """
    图像哈希计算器
    
    支持多种哈希算法用于图像指纹计算
    """
    
    @staticmethod
    def compute_file_hash(file_path: str, algorithm: str = "md5") -> str:
        """
        计算文件哈希值
        
        :param file_path: 文件路径
        :param algorithm: 哈希算法 (md5, sha256)
        :return: 哈希值字符串
        """
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            hasher = hashlib.md5()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"⚠️ 计算文件哈希失败: {e}")
            return ""
    
    @staticmethod
    def compute_bytes_hash(data: bytes, algorithm: str = "md5") -> str:
        """
        计算字节数据哈希值
        
        :param data: 字节数据
        :param algorithm: 哈希算法
        :return: 哈希值字符串
        """
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            hasher = hashlib.md5()
        
        hasher.update(data)
        return hasher.hexdigest()
    
    @staticmethod
    def compute_pil_image_hash(image, algorithm: str = "md5") -> str:
        """
        计算PIL图像哈希值
        
        :param image: PIL Image对象
        :param algorithm: 哈希算法
        :return: 哈希值字符串
        """
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return ImageHasher.compute_bytes_hash(buffer.getvalue(), algorithm)


class InferenceCache:
    """
    推理缓存管理器
    
    使用LRU策略管理推理结果缓存，支持：
    - 内存缓存
    - 持久化缓存
    - 缓存统计
    - 线程安全
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        persist_dir: Optional[str] = None,
        hash_algorithm: str = "md5"
    ):
        """
        初始化推理缓存
        
        :param max_size: 最大缓存条目数
        :param ttl_seconds: 缓存过期时间（秒）
        :param persist_dir: 持久化目录（可选）
        :param hash_algorithm: 哈希算法
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.persist_dir = Path(persist_dir) if persist_dir else None
        self.hash_algorithm = hash_algorithm
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
        
        self._hasher = ImageHasher()
        
        print(f"📦 [InferenceCache] 初始化完成")
        print(f"   最大缓存数: {max_size}")
        print(f"   过期时间: {ttl_seconds}秒")
        print(f"   哈希算法: {hash_algorithm}")
        
        if self.persist_dir:
            self._load_persisted_cache()
    
    def _generate_key(self, image_source: Any, params: Optional[Dict] = None) -> str:
        """
        生成缓存键
        
        :param image_source: 图像源（路径、字节、PIL图像）
        :param params: 推理参数
        :return: 缓存键
        """
        if isinstance(image_source, str):
            image_hash = self._hasher.compute_file_hash(image_source, self.hash_algorithm)
        elif isinstance(image_source, bytes):
            image_hash = self._hasher.compute_bytes_hash(image_source, self.hash_algorithm)
        elif hasattr(image_source, 'save'):
            image_hash = self._hasher.compute_pil_image_hash(image_source, self.hash_algorithm)
        else:
            image_hash = str(hash(str(image_source)))
        
        if params:
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{image_hash}_{params_hash}"
        
        return image_hash
    
    def get(
        self,
        image_source: Any,
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果
        
        :param image_source: 图像源
        :param params: 推理参数
        :return: 缓存结果（未命中返回None）
        """
        with self._lock:
            self._stats["total_requests"] += 1
            
            key = self._generate_key(image_source, params)
            
            if key in self._cache:
                entry = self._cache[key]
                
                if self._is_expired(entry):
                    del self._cache[key]
                    self._stats["misses"] += 1
                    return None
                
                entry.hit_count += 1
                self._cache.move_to_end(key)
                self._stats["hits"] += 1
                
                hit_rate = self._stats["hits"] / self._stats["total_requests"] * 100
                print(f"🎯 [Cache] 命中! 命中率: {hit_rate:.1f}%")
                
                return entry.result
            
            self._stats["misses"] += 1
            return None
    
    def put(
        self,
        image_source: Any,
        result: Dict[str, Any],
        params: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        存入缓存
        
        :param image_source: 图像源
        :param result: 推理结果
        :param params: 推理参数
        :param metadata: 额外元数据
        """
        with self._lock:
            key = self._generate_key(image_source, params)
            
            image_hash = ""
            if isinstance(image_source, str):
                image_hash = self._hasher.compute_file_hash(image_source, self.hash_algorithm)
            
            entry = CacheEntry(
                result=result,
                timestamp=time.time(),
                hit_count=0,
                image_hash=image_hash,
                metadata=metadata or {}
            )
            
            if key in self._cache:
                del self._cache[key]
            
            self._cache[key] = entry
            
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            print(f"📝 [Cache] 已缓存 (当前: {len(self._cache)}/{self.max_size})")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """
        检查缓存是否过期
        
        :param entry: 缓存条目
        :return: 是否过期
        """
        if self.ttl_seconds <= 0:
            return False
        
        elapsed = time.time() - entry.timestamp
        return elapsed > self.ttl_seconds
    
    def invalidate(self, image_source: Any, params: Optional[Dict] = None) -> bool:
        """
        使指定缓存失效
        
        :param image_source: 图像源
        :param params: 推理参数
        :return: 是否成功删除
        """
        with self._lock:
            key = self._generate_key(image_source, params)
            
            if key in self._cache:
                del self._cache[key]
                print(f"🗑️ [Cache] 已失效: {key[:16]}...")
                return True
            
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            print(f"🗑️ [Cache] 已清空 {count} 条缓存")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        :return: 统计信息字典
        """
        with self._lock:
            total = self._stats["total_requests"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0.0
            
            return {
                "total_requests": total,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": hit_rate,
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "utilization": len(self._cache) / self.max_size * 100
            }
    
    def print_stats(self) -> None:
        """打印缓存统计"""
        stats = self.get_stats()
        print("\n📊 [Cache] 缓存统计")
        print("=" * 40)
        print(f"   总请求数: {stats['total_requests']}")
        print(f"   命中次数: {stats['hits']}")
        print(f"   未命中数: {stats['misses']}")
        print(f"   命中率: {stats['hit_rate']:.1f}%")
        print(f"   淘汰次数: {stats['evictions']}")
        print(f"   缓存大小: {stats['cache_size']}/{stats['max_size']}")
        print(f"   使用率: {stats['utilization']:.1f}%")
        print("=" * 40)
    
    def _load_persisted_cache(self) -> None:
        """加载持久化缓存"""
        if not self.persist_dir:
            return
        
        cache_file = self.persist_dir / "inference_cache.json"
        
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            loaded_count = 0
            for key, entry_data in data.get("entries", {}).items():
                entry = CacheEntry.from_dict(entry_data)
                
                if not self._is_expired(entry):
                    self._cache[key] = entry
                    loaded_count += 1
            
            print(f"📦 [Cache] 从持久化加载 {loaded_count} 条缓存")
            
        except Exception as e:
            print(f"⚠️ [Cache] 加载持久化缓存失败: {e}")
    
    def persist(self) -> None:
        """持久化缓存到磁盘"""
        if not self.persist_dir:
            return
        
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.persist_dir / "inference_cache.json"
        
        try:
            with self._lock:
                entries = {
                    key: entry.to_dict()
                    for key, entry in self._cache.items()
                    if not self._is_expired(entry)
                }
                
                data = {
                    "version": "1.0",
                    "timestamp": datetime.now().isoformat(),
                    "entries": entries
                }
                
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 [Cache] 已持久化 {len(entries)} 条缓存")
                
        except Exception as e:
            print(f"⚠️ [Cache] 持久化失败: {e}")
    
    def get_top_hits(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        获取命中次数最多的缓存条目
        
        :param top_n: 返回数量
        :return: (key, hit_count) 列表
        """
        with self._lock:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].hit_count,
                reverse=True
            )
            
            return [(key[:16] + "...", entry.hit_count) 
                    for key, entry in sorted_entries[:top_n]]


def create_inference_cache(
    max_size: int = 1000,
    ttl_seconds: int = 3600,
    persist_dir: Optional[str] = None
) -> InferenceCache:
    """
    工厂函数: 创建推理缓存实例
    
    :param max_size: 最大缓存条目数
    :param ttl_seconds: 缓存过期时间
    :param persist_dir: 持久化目录
    :return: InferenceCache实例
    """
    return InferenceCache(
        max_size=max_size,
        ttl_seconds=ttl_seconds,
        persist_dir=persist_dir
    )


_global_cache: Optional[InferenceCache] = None


def get_global_cache() -> InferenceCache:
    """
    获取全局缓存实例
    
    :return: 全局InferenceCache实例
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = InferenceCache(
            max_size=500,
            ttl_seconds=1800
        )
    
    return _global_cache
