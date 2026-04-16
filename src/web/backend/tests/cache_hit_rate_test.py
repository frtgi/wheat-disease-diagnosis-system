"""
缓存命中率测试脚本
测试 Redis 缓存的命中率和效果
"""
import asyncio
import time
from typing import Dict, Any
import redis.asyncio as aioredis
from datetime import datetime


class CacheHitRateTester:
    """
    缓存命中率测试器
    
    功能：
    1. 测试缓存命中率
    2. 监控缓存性能
    3. 生成缓存报告
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        初始化缓存测试器
        
        Args:
            redis_url: Redis 连接 URL
        """
        self.redis_url = redis_url
        self.redis = None
    
    async def connect(self):
        """连接 Redis"""
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        print("✅ 已连接到 Redis")
    
    async def disconnect(self):
        """断开 Redis 连接"""
        if self.redis:
            await self.redis.close()
            print("✅ 已断开 Redis 连接")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计字典
        """
        info = await self.redis.info("stats")
        
        keyspace_hits = info.get("keyspace_hits", 0)
        keyspace_misses = info.get("keyspace_misses", 0)
        
        total_requests = keyspace_hits + keyspace_misses
        hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "keyspace_hits": keyspace_hits,
            "keyspace_misses": keyspace_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_cache_keys_count(self) -> int:
        """
        获取缓存键数量
        
        Returns:
            键数量
        """
        return await self.redis.dbsize()
    
    async def get_cache_keys_by_pattern(self, pattern: str = "*") -> list:
        """
        获取匹配模式的所有键
        
        Args:
            pattern: 键模式
        
        Returns:
            键列表
        """
        keys = await self.redis.keys(pattern)
        return keys
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取内存使用情况
        
        Returns:
            内存使用信息
        """
        info = await self.redis.info("memory")
        
        return {
            "used_memory": info.get("used_memory", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "used_memory_peak": info.get("used_memory_peak", 0),
            "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0)
        }
    
    async def test_cache_operations(self) -> Dict[str, Any]:
        """
        测试缓存操作性能
        
        Returns:
            性能测试结果
        """
        test_key = "test:performance"
        test_value = "test_value_" + str(time.time())
        
        start_time = time.time()
        await self.redis.set(test_key, test_value, ex=60)
        set_duration = (time.time() - start_time) * 1000
        
        start_time = time.time()
        result = await self.redis.get(test_key)
        get_duration = (time.time() - start_time) * 1000
        
        start_time = time.time()
        await self.redis.delete(test_key)
        delete_duration = (time.time() - start_time) * 1000
        
        return {
            "set_operation_ms": round(set_duration, 3),
            "get_operation_ms": round(get_duration, 3),
            "delete_operation_ms": round(delete_duration, 3),
            "success": result == test_value
        }
    
    async def analyze_cache_distribution(self) -> Dict[str, Any]:
        """
        分析缓存键分布
        
        Returns:
            键分布信息
        """
        all_keys = await self.get_cache_keys_by_pattern()
        
        distribution = {}
        for key in all_keys:
            prefix = key.split(":")[0] if ":" in key else "other"
            distribution[prefix] = distribution.get(prefix, 0) + 1
        
        return {
            "total_keys": len(all_keys),
            "distribution": distribution,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        运行综合缓存测试
        
        Returns:
            综合测试结果
        """
        print("\n" + "="*60)
        print("🔍 开始缓存性能测试")
        print("="*60 + "\n")
        
        await self.connect()
        
        print("📊 1. 获取缓存统计信息...")
        stats = await self.get_cache_stats()
        print(f"   ✅ 缓存命中率：{stats['hit_rate_percent']}%")
        print(f"   ✅ 总请求数：{stats['total_requests']}")
        print(f"   ✅ 命中次数：{stats['keyspace_hits']}")
        print(f"   ✅ 未命中次数：{stats['keyspace_misses']}")
        
        print("\n📊 2. 获取缓存键数量...")
        keys_count = await self.get_cache_keys_count()
        print(f"   ✅ 当前缓存键数量：{keys_count}")
        
        print("\n📊 3. 获取内存使用情况...")
        memory = await self.get_memory_usage()
        print(f"   ✅ 已使用内存：{memory['used_memory_human']}")
        print(f"   ✅ 内存峰值：{memory['used_memory_peak_human']}")
        print(f"   ✅ 内存碎片率：{memory['mem_fragmentation_ratio']}")
        
        print("\n📊 4. 测试缓存操作性能...")
        perf = await self.test_cache_operations()
        print(f"   ✅ SET 操作耗时：{perf['set_operation_ms']} ms")
        print(f"   ✅ GET 操作耗时：{perf['get_operation_ms']} ms")
        print(f"   ✅ DELETE 操作耗时：{perf['delete_operation_ms']} ms")
        
        print("\n📊 5. 分析缓存键分布...")
        distribution = await self.analyze_cache_distribution()
        print(f"   ✅ 总键数：{distribution['total_keys']}")
        print("   ✅ 键分布：")
        for prefix, count in sorted(distribution['distribution'].items()):
            print(f"      - {prefix}: {count}")
        
        await self.disconnect()
        
        print("\n" + "="*60)
        print("📋 测试总结")
        print("="*60)
        
        if stats['hit_rate_percent'] > 80:
            print(f"✅ 缓存命中率优秀：{stats['hit_rate_percent']}%")
        elif stats['hit_rate_percent'] > 50:
            print(f"⚠️  缓存命中率良好：{stats['hit_rate_percent']}%")
        else:
            print(f"❌ 缓存命中率较低：{stats['hit_rate_percent']}%")
        
        return {
            "test_time": datetime.now().isoformat(),
            "stats": stats,
            "keys_count": keys_count,
            "memory": memory,
            "performance": perf,
            "distribution": distribution
        }


async def main():
    """主函数"""
    tester = CacheHitRateTester(redis_url="redis://localhost:6379/0")
    results = await tester.run_comprehensive_test()
    
    import json
    with open("cache_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n📄 缓存报告已保存：cache_report.json")


if __name__ == "__main__":
    asyncio.run(main())
