"""
V21 后端单元测试
测试核心服务层：CacheService、VRAMManager、Security、InferenceCacheService
"""
import sys
import os
import asyncio
import time
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("WHEATAGENT_MOCK_AI", "true")


def _reset_redis_singleton():
    """重置 Redis 异步客户端单例，确保 asyncio.run() 新事件循环中创建新连接"""
    try:
        from app.core.redis_client import RedisClient
        if RedisClient._async_instance is not None:
            try:
                loop = RedisClient._async_instance.loop
                if loop and not loop.is_closed():
                    loop.run_until_complete(RedisClient._async_instance.close())
            except Exception:
                pass
            RedisClient._async_instance = None
    except Exception:
        pass


class TestCacheService(unittest.TestCase):
    """CacheService 核心功能测试类"""

    def setUp(self):
        """每个测试前创建新的 CacheService 实例并重置 Redis 单例"""
        _reset_redis_singleton()
        from app.services.cache import CacheService
        self.cache = CacheService()

    def tearDown(self):
        """测试结束后清理 Redis 连接"""
        _reset_redis_singleton()

    def test_token_blacklist_redis(self):
        """测试 add_token_to_blacklist + is_token_revoked 通过 Redis 正常工作"""
        async def _test():
            token = f"test_token_redis_{int(time.time()*1000)}"
            result = await self.cache.add_token_to_blacklist(token, expire=300)
            self.assertTrue(result, "添加 Token 到黑名单应返回 True")
            revoked = await self.cache.is_token_revoked(token)
            self.assertTrue(revoked, "Token 应已被标记为撤销")
            not_revoked = await self.cache.is_token_revoked("nonexistent_token_xyz")
            self.assertFalse(not_revoked, "不存在的 Token 不应被标记为撤销")
        asyncio.run(_test())

    def test_token_blacklist_local_fallback(self):
        """测试 Redis 不可用时本地 LRU 缓存降级"""
        async def _test():
            async def _no_redis(self_instance):
                raise Exception("Redis connection refused")
            with patch.object(type(self.cache), '_get_redis', _no_redis):
                token = f"test_token_local_{int(time.time()*1000)}"
                result = await self.cache.add_token_to_blacklist(token, expire=300)
                self.assertTrue(result, "Redis 不可用时添加到本地缓存应返回 True")
                revoked = await self.cache.is_token_revoked(token)
                self.assertTrue(revoked, "本地缓存中应能查到已撤销的 Token")
        asyncio.run(_test())

    def test_login_rate_limit_redis(self):
        """测试 record_login_attempt + get_login_attempts 通过 Redis 正常工作"""
        async def _test():
            email = f"rate_test_{int(time.time()*1000)}@test.com"
            count1 = await self.cache.record_login_attempt(email, success=False)
            self.assertEqual(count1, 1, "第一次失败登录应返回 1")
            count2 = await self.cache.record_login_attempt(email, success=False)
            self.assertEqual(count2, 2, "第二次失败登录应返回 2")
            attempts = await self.cache.get_login_attempts(email)
            self.assertEqual(attempts, 2, "获取登录失败次数应为 2")
            count_reset = await self.cache.record_login_attempt(email, success=True)
            self.assertEqual(count_reset, 0, "成功登录后应重置为 0")
            attempts_after = await self.cache.get_login_attempts(email)
            self.assertEqual(attempts_after, 0, "成功登录后获取次数应为 0")
        asyncio.run(_test())

    def test_login_rate_limit_local_fallback(self):
        """测试 Redis 不可用时本地计数器降级"""
        async def _test():
            async def _no_redis(self_instance):
                raise Exception("Redis connection refused")
            with patch.object(type(self.cache), '_get_redis', _no_redis):
                email = f"local_rate_{int(time.time()*1000)}@test.com"
                count1 = await self.cache.record_login_attempt(email, success=False)
                self.assertEqual(count1, 1, "本地计数器第一次失败应返回 1")
                count2 = await self.cache.record_login_attempt(email, success=False)
                self.assertEqual(count2, 2, "本地计数器第二次失败应返回 2")
                attempts = await self.cache.get_login_attempts(email)
                self.assertEqual(attempts, 2, "本地获取登录失败次数应为 2")
                count_reset = await self.cache.record_login_attempt(email, success=True)
                self.assertEqual(count_reset, 0, "本地成功登录后应重置为 0")
        asyncio.run(_test())

    def test_diagnosis_cache(self):
        """测试 set_diagnosis + get_diagnosis 正常读写"""
        async def _test():
            import hashlib
            image_md5 = hashlib.md5(f"test_image_{time.time()}".encode()).hexdigest()
            diagnosis_data = {
                "disease": "小麦锈病",
                "confidence": 0.95,
                "severity": "中度"
            }
            set_result = await self.cache.set_diagnosis(image_md5, diagnosis_data)
            self.assertTrue(set_result, "设置诊断缓存应返回 True")
            cached = await self.cache.get_diagnosis(image_md5)
            self.assertIsNotNone(cached, "应能读取到缓存的诊断结果")
            self.assertEqual(cached["disease"], "小麦锈病", "疾病名称应一致")
            self.assertEqual(cached["confidence"], 0.95, "置信度应一致")
            await self.cache.delete_diagnosis(image_md5)
        asyncio.run(_test())


class TestVRAMManager(unittest.TestCase):
    """VRAMManager 显存管理测试类"""

    def setUp(self):
        """每个测试前创建新的 VRAMManager 实例"""
        from app.services.vram_manager import VRAMManager
        self.manager = VRAMManager(max_vram_mb=4096)

    def test_get_vram_usage(self):
        """测试 get_vram_usage 返回正确结构"""
        usage = self.manager.get_vram_usage()
        self.assertIn("used_mb", usage, "应包含 used_mb 字段")
        self.assertIn("free_mb", usage, "应包含 free_mb 字段")
        self.assertIn("total_mb", usage, "应包含 total_mb 字段")
        self.assertIn("usage_ratio", usage, "应包含 usage_ratio 字段")
        self.assertIsInstance(usage["used_mb"], (int, float), "used_mb 应为数值类型")
        self.assertIsInstance(usage["free_mb"], (int, float), "free_mb 应为数值类型")
        self.assertIsInstance(usage["total_mb"], (int, float), "total_mb 应为数值类型")
        self.assertIsInstance(usage["usage_ratio"], (int, float), "usage_ratio 应为数值类型")
        self.assertGreaterEqual(usage["usage_ratio"], 0, "usage_ratio 不应为负")
        self.assertLessEqual(usage["usage_ratio"], 1, "usage_ratio 不应超过 1")

    def test_is_vram_sufficient(self):
        """测试 is_vram_sufficient 判断逻辑"""
        result_small = self.manager.is_vram_sufficient(required_mb=1)
        self.assertTrue(result_small, "请求 1MB 显存应充足")
        result_huge = self.manager.is_vram_sufficient(required_mb=999999)
        self.assertFalse(result_huge, "请求超大量显存应不足")

    def test_get_optimal_batch_size(self):
        """测试根据显存调整批处理大小"""
        batch_1 = self.manager.get_optimal_batch_size(base_batch_size=1)
        self.assertGreaterEqual(batch_1, 1, "批处理大小至少为 1")
        batch_large = self.manager.get_optimal_batch_size(base_batch_size=100)
        self.assertGreaterEqual(batch_large, 1, "即使请求大批次也应返回至少 1")

    def test_cleanup(self):
        """测试 cleanup 返回 before/after/freed_mb 结构"""
        result = self.manager.cleanup()
        self.assertIn("before", result, "应包含 before 字段")
        self.assertIn("after", result, "应包含 after 字段")
        self.assertIn("freed_mb", result, "应包含 freed_mb 字段")
        self.assertIn("used_mb", result["before"], "before 应包含 used_mb")
        self.assertIn("used_mb", result["after"], "after 应包含 used_mb")
        self.assertIsInstance(result["freed_mb"], (int, float), "freed_mb 应为数值类型")

    def test_inference_context(self):
        """测试 inference_context 上下文管理器正常工作"""
        with self.manager.inference_context() as ctx:
            self.assertIs(ctx, self.manager, "上下文应返回 VRAMManager 实例")


class TestSecurity(unittest.TestCase):
    """Security 安全认证测试类"""

    def test_create_and_decode_token(self):
        """测试 create_access_token + decode_access_token 正常工作"""
        from app.core.security import create_access_token, decode_access_token
        data = {"sub": "testuser", "user_id": 42}
        token = create_access_token(data=data)
        self.assertIsInstance(token, str, "Token 应为字符串")
        self.assertTrue(len(token) > 0, "Token 不应为空")
        payload = decode_access_token(token)
        self.assertIsNotNone(payload, "解码结果不应为 None")
        self.assertEqual(payload["sub"], "testuser", "sub 字段应一致")
        self.assertEqual(payload["user_id"], 42, "user_id 字段应一致")
        self.assertIn("exp", payload, "应包含 exp 过期时间字段")

    def test_get_token_from_request_header(self):
        """测试从 Authorization Header 提取 Token"""
        from app.core.security import get_token_from_request
        token = asyncio.run(get_token_from_request(
            authorization="Bearer my_jwt_token_123",
            access_token_cookie=None
        ))
        self.assertEqual(token, "my_jwt_token_123", "应从 Header 提取到正确的 Token")

    def test_get_token_from_request_cookie(self):
        """测试从 Cookie 提取 Token（Header 为空时）"""
        from app.core.security import get_token_from_request
        token = asyncio.run(get_token_from_request(
            authorization=None,
            access_token_cookie="cookie_jwt_token_456"
        ))
        self.assertEqual(token, "cookie_jwt_token_456", "应从 Cookie 提取到正确的 Token")

    def test_get_token_from_request_priority(self):
        """测试 Header 优先于 Cookie"""
        from app.core.security import get_token_from_request
        token = asyncio.run(get_token_from_request(
            authorization="Bearer header_token",
            access_token_cookie="cookie_token"
        ))
        self.assertEqual(token, "header_token", "Header 中的 Token 应优先于 Cookie")

    def test_token_blacklist_check(self):
        """测试 is_token_blacklisted 正常工作"""
        from app.core.security import is_token_blacklisted
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.is_token_revoked = AsyncMock(return_value=True)
            result = asyncio.run(is_token_blacklisted("blacklisted_token"))
            self.assertTrue(result, "黑名单中的 Token 应返回 True")
            mock_cache.is_token_revoked = AsyncMock(return_value=False)
            result = asyncio.run(is_token_blacklisted("valid_token"))
            self.assertFalse(result, "不在黑名单的 Token 应返回 False")


class TestInferenceCacheService(unittest.TestCase):
    """InferenceCacheService 推理缓存测试类"""

    def setUp(self):
        """每个测试前创建新的 InferenceCacheService 实例并重置 Redis 单例"""
        _reset_redis_singleton()
        from app.services.inference_cache_service import InferenceCacheService
        self.service = InferenceCacheService(
            ttl=300,
            enable_similar_search=False,
            similarity_threshold=5
        )
        self.test_image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100 + f"v21_test_{time.time()}".encode()

    def tearDown(self):
        """测试结束后清理 Redis 连接"""
        _reset_redis_singleton()

    def test_cache_set_and_get(self):
        """测试缓存写入和读取"""
        async def _test():
            result_data = {"disease": "白粉病", "confidence": 0.88}
            set_ok = await self.service.set(
                image_data=self.test_image_data,
                result=result_data,
                symptoms="叶片发白"
            )
            self.assertTrue(set_ok, "缓存写入应返回 True")
            cached = await self.service.get(
                image_data=self.test_image_data,
                symptoms="叶片发白"
            )
            self.assertIsNotNone(cached, "应能读取到缓存结果")
            self.assertIn("result", cached, "缓存结果应包含 result 字段")
            self.assertEqual(cached["result"]["disease"], "白粉病", "疾病名称应一致")
        asyncio.run(_test())

    def test_cache_miss(self):
        """测试缓存未命中返回 None"""
        async def _test():
            unique_data = b'\x89PNG\r\n\x1a\n' + os.urandom(64)
            cached = await self.service.get(
                image_data=unique_data,
                symptoms="不存在的症状描述_xyz"
            )
            self.assertIsNone(cached, "未命中的缓存应返回 None")
        asyncio.run(_test())

    def test_cache_delete(self):
        """测试缓存删除"""
        async def _test():
            result_data = {"disease": "锈病", "confidence": 0.77}
            await self.service.set(
                image_data=self.test_image_data,
                result=result_data,
                symptoms="删除测试"
            )
            delete_ok = await self.service.delete(
                image_data=self.test_image_data,
                symptoms="删除测试"
            )
            self.assertTrue(delete_ok, "删除缓存应返回 True")
            cached = await self.service.get(
                image_data=self.test_image_data,
                symptoms="删除测试"
            )
            self.assertIsNone(cached, "删除后应返回 None")
        asyncio.run(_test())

    def test_cache_stats(self):
        """测试 get_stats 返回正确结构"""
        async def _test():
            stats = await self.service.get_stats()
            self.assertIn("total_requests", stats, "应包含 total_requests 字段")
            self.assertIn("cache_hits", stats, "应包含 cache_hits 字段")
            self.assertIn("cache_misses", stats, "应包含 cache_misses 字段")
            self.assertIn("hit_rate", stats, "应包含 hit_rate 字段")
            self.assertIsInstance(stats["total_requests"], int, "total_requests 应为整数")
            self.assertIsInstance(stats["hit_rate"], (int, float), "hit_rate 应为数值类型")
        asyncio.run(_test())


def run_tests():
    """运行所有测试并输出详细结果"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCacheService))
    suite.addTests(loader.loadTestsFromTestCase(TestVRAMManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestInferenceCacheService))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("V21 后端单元测试结果汇总")
    print("=" * 70)
    print(f"  总测试数: {result.testsRun}")
    print(f"  通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  跳过: {len(result.skipped)}")
    print("=" * 70)

    if result.failures:
        print("\n失败详情:")
        for test, traceback in result.failures:
            print(f"  [FAIL] {test}")
            print(f"         {traceback}")

    if result.errors:
        print("\n错误详情:")
        for test, traceback in result.errors:
            print(f"  [ERROR] {test}")
            print(f"          {traceback}")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
