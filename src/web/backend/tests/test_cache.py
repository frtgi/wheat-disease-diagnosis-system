"""
Redis 缓存功能测试脚本
测试诊断结果缓存功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.web.backend.app.services.cache import cache_service
from src.web.backend.app.core.redis_client import RedisClient


async def test_redis_connection():
    """测试 Redis 连接"""
    print("=" * 60)
    print("Redis 连接测试")
    print("=" * 60)
    
    # 测试同步连接
    print("\n[测试 1] 同步 Redis 连接")
    sync_connected = RedisClient.test_connection()
    print(f"  同步连接：{'✅ 成功' if sync_connected else '❌ 失败'}")
    
    # 测试异步连接
    print("\n[测试 2] 异步 Redis 连接")
    async_connected = await RedisClient.test_async_connection()
    print(f"  异步连接：{'✅ 成功' if async_connected else '❌ 失败'}")
    
    return sync_connected and async_connected


async def test_diagnosis_cache():
    """测试诊断结果缓存功能"""
    print("\n" + "=" * 60)
    print("诊断结果缓存测试")
    print("=" * 60)
    
    # 测试数据
    test_image_md5 = "test_md5_12345"
    test_diagnosis = {
        'disease_name': '小麦条锈病',
        'confidence': 0.95,
        'severity': 'high',
        'description': '小麦条锈病，病斑呈条状黄色，沿叶脉平行分布',
        'recommendations': [
            '选用抗病品种',
            '喷洒粉锈宁',
            '使用烯唑醇'
        ],
        'knowledge_links': [
            '预防措施：合理施肥，增强植株抗病能力',
            '病原体：Puccinia striiformis'
        ]
    }
    
    # 测试 1: 设置缓存
    print("\n[测试 1] 设置诊断缓存")
    set_success = await cache_service.set_diagnosis(test_image_md5, test_diagnosis)
    print(f"  缓存设置：{'✅ 成功' if set_success else '❌ 失败'}")
    
    # 测试 2: 获取缓存
    print("\n[测试 2] 获取诊断缓存")
    cached_result = await cache_service.get_diagnosis(test_image_md5)
    if cached_result:
        print(f"  ✅ 缓存获取成功")
        print(f"     病害名称：{cached_result['disease_name']}")
        print(f"     置信度：{cached_result['confidence']:.2%}")
        print(f"     严重程度：{cached_result['severity']}")
    else:
        print(f"  ❌ 缓存获取失败")
    
    # 测试 3: 缓存命中率测试
    print("\n[测试 3] 缓存命中率测试 (100 次查询)")
    hits = 0
    misses = 0
    for i in range(100):
        if i % 2 == 0:
            # 使用已存在的 MD5
            result = await cache_service.get_diagnosis(test_image_md5)
            if result:
                hits += 1
            else:
                misses += 1
        else:
            # 使用不存在的 MD5
            result = await cache_service.get_diagnosis(f"nonexistent_md5_{i}")
            if result:
                hits += 1
            else:
                misses += 1
    
    hit_rate = hits / 100 * 100
    print(f"  命中次数：{hits}")
    print(f"  未命中次数：{misses}")
    print(f"  命中率：{hit_rate:.1f}%")
    
    # 测试 4: 删除缓存
    print("\n[测试 4] 删除诊断缓存")
    delete_success = await cache_service.delete_diagnosis(test_image_md5)
    print(f"  缓存删除：{'✅ 成功' if delete_success else '❌ 失败'}")
    
    # 验证删除
    verify_result = await cache_service.get_diagnosis(test_image_md5)
    print(f"  验证删除：{'✅ 已删除' if not verify_result else '❌ 未删除'}")


async def test_cache_stats():
    """测试缓存统计功能"""
    print("\n" + "=" * 60)
    print("缓存统计信息")
    print("=" * 60)
    
    stats = await cache_service.get_stats()
    
    if stats.get('connected'):
        print(f"\n  ✅ Redis 已连接")
        print(f"     键数量：{stats.get('keys_count', 0)}")
        print(f"     命中率：{stats.get('hit_rate', 0):.2%}")
    else:
        print(f"\n  ❌ Redis 未连接")
        print(f"     错误：{stats.get('error', '未知')}")


async def main():
    """主测试函数"""
    try:
        # 测试 Redis 连接
        connected = await test_redis_connection()
        
        if connected:
            # 测试诊断缓存功能
            await test_diagnosis_cache()
            
            # 测试统计功能
            await test_cache_stats()
            
            print("\n" + "=" * 60)
            print("✅ 所有缓存测试完成！")
            print("=" * 60)
        else:
            print("\n❌ Redis 未连接，请确保 Redis 服务已启动")
            print("   启动命令：redis-server")
            
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
