"""
安全模块单元测试
覆盖 security.py 中的核心函数：密码验证、哈希、Token 生成/验证、黑名单功能
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
import bcrypt

from app.core.security import (
    verify_password,
    get_password_hash,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_token,
    add_token_to_blacklist,
    is_token_blacklisted,
    BCRYPT_MAX_PASSWORD_LENGTH,
    TOKEN_BLACKLIST_PREFIX,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ALGORITHM,
)


class TestVerifyPassword:
    """verify_password 函数测试套件"""

    def test_correct_password_verification(self):
        """
        测试正确密码验证成功

        使用 bcrypt 哈希后验证相同明文密码应返回 True
        """
        password = "my_secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_verification(self):
        """
        测试错误密码验证失败

        使用不同密码验证应返回 False
        """
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_empty_plain_password(self):
        """
        测试空明文密码验证

        空字符串作为明文密码应返回 False
        """
        hashed = get_password_hash("some_password")
        assert verify_password("", hashed) is False

    def test_invalid_hashed_password_format(self):
        """
        测试无效的哈希格式

        非标准 bcrypt 哈希字符串应优雅地返回 False
        """
        assert verify_password("password", "not_a_valid_hash") is False

    def test_none_like_inputs(self):
        """
        测试异常类型输入

        传入可能导致 TypeError 的输入应返回 False 而非抛出异常
        """
        hashed = get_password_hash("test")
        result = verify_password("test", hashed)
        assert result is True
        assert verify_password("test", "") is False


class TestGetPasswordHash:
    """get_password_hash / hash_password 函数测试套件"""

    def test_normal_password_hashing(self):
        """
        测试正常密码哈希生成

        生成的哈希应以 $2b$ 开头（bcrypt 格式），且长度 >= 60
        """
        password = "normal_password_123"
        hashed = get_password_hash(password)
        assert hashed.startswith("$2b$")
        assert len(hashed) >= 60

    def test_empty_password_raises_error(self):
        """
        测试空密码抛出 ValueError

        空字符串或 None 作为密码应触发 ValueError 异常
        """
        with pytest.raises(ValueError, match="密码不能为空"):
            get_password_hash("")
        with pytest.raises(ValueError, match="密码不能为空"):
            get_password_hash(None)

    def test_long_password_truncation(self):
        """
        测试超长密码自动截断

        超过 72 字节的密码应被截断，且不抛出异常
        """
        long_password = "a" * 200
        hashed = get_password_hash(long_password)
        assert hashed.startswith("$2b$")
        assert len(hashed) >= 60

    def test_unicode_password_hashing(self):
        """
        测试 Unicode 密码哈希

        包含中文等 Unicode 字符的密码应能正常哈希
        """
        password = "密码测试中文123"
        hashed = get_password_hash(password)
        assert hashed.startswith("$2b$")
        assert verify_password(password, hashed) is True

    def test_hash_password_alias(self):
        """
        测试 hash_password 别名函数

        hash_password 应与 get_password_hash 行为一致
        """
        password = "alias_test_password"
        h1 = get_password_hash(password)
        h2 = hash_password(password)
        assert h1 != h2
        assert verify_password(password, h1) is True
        assert verify_password(password, h2) is True

    def test_each_hash_is_unique(self):
        """
        测试每次哈希结果唯一性

        相同密码多次哈希应产生不同结果（因 salt 随机）
        """
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestCreateAccessToken:
    """create_access_token 函数测试套件"""

    def test_normal_token_creation(self):
        """
        测试正常创建访问令牌

        应返回有效的 JWT 字符串，包含 exp 和 sub 字段
        """
        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_custom_expires_delta(self):
        """
        测试自定义过期时间

        传入自定义 timedelta 应覆盖默认过期时间
        """
        custom_delta = timedelta(minutes=5)
        token = create_access_token(
            data={"sub": "custom_user"},
            expires_delta=custom_delta
        )
        payload = decode_access_token(token)
        assert payload is not None
        exp_timestamp = payload["exp"]
        time_diff = datetime.utcfromtimestamp(exp_timestamp) - datetime.utcnow()
        assert abs(time_diff.total_seconds() - 300) < 10

    def test_token_with_multiple_fields(self):
        """
        测试包含多个字段的 Token

        Payload 中可包含多个自定义字段
        """
        data = {"sub": "user1", "role": "admin", "user_id": 42}
        token = create_access_token(data=data)
        payload = decode_access_token(token)
        assert payload["sub"] == "user1"
        assert payload["role"] == "admin"
        assert payload["user_id"] == 42

    def test_empty_data_token(self):
        """
        测试空数据创建 Token

        空字典数据也能创建有效 Token
        """
        token = create_access_token(data={})
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload


class TestCreateRefreshToken:
    """create_refresh_token 函数测试套件"""

    def test_normal_refresh_token_creation(self):
        """
        测试正常创建刷新令牌

        刷新令牌应包含 type=refresh 标记和较长的有效期
        """
        token = create_refresh_token(data={"sub": "testuser"})
        assert isinstance(token, str)

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["sub"] == "testuser"

    def test_refresh_token_custom_expires(self):
        """
        测试刷新令牌自定义过期时间

        传入自定义过期时间应覆盖默认 7 天
        """
        custom_delta = timedelta(days=1)
        token = create_refresh_token(
            data={"sub": "user1"},
            expires_delta=custom_delta
        )
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        exp_timestamp = payload["exp"]
        time_diff = datetime.utcfromtimestamp(exp_timestamp) - datetime.utcnow()
        assert abs(time_diff.total_seconds() - 86400) < 10

    def test_refresh_token_default_expiry_days(self):
        """
        测试刷新令牌默认 7 天有效期

        不传 expires_delta 时，默认应为 REFRESH_TOKEN_EXPIRE_DAYS 天
        """
        token = create_refresh_token(data={"sub": "test"})
        payload = decode_access_token(token)
        exp_timestamp = payload["exp"]
        time_diff = datetime.utcfromtimestamp(exp_timestamp) - datetime.utcnow()
        expected_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        assert abs(time_diff.total_seconds() - expected_seconds) < 10


class TestVerifyToken:
    """verify_token / decode_access_token 函数测试套件"""

    def test_valid_token_verification(self):
        """
        测试有效 Token 验证成功

        正确签发的 Token 应能被成功解码并返回 payload
        """
        token = create_access_token(data={"sub": "valid_user", "user_id": 1})
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "valid_user"
        assert payload["user_id"] == 1

    def test_invalid_token_returns_none(self):
        """
        测试无效 Token 返回 None

        篡改或伪造的 Token 应返回 None
        """
        assert verify_token("invalid.token.here") is None
        assert verify_token("") is None
        assert verify_token("not_a_jwt") is None

    def test_tampered_token_rejected(self):
        """
        测试被篡改的 Token 被拒绝

        修改 Token 的部分字符后应无法通过验证
        """
        token = create_access_token(data={"sub": "original"})
        tampered = token[:-5] + "xxxxx"
        assert verify_token(tampered) is None

    def test_decode_access_token_valid(self):
        """
        测试 decode_access_token 解码有效 Token

        与 verify_token 功能一致的解码能力
        """
        token = create_access_token(data={"sub": "decode_test"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "decode_test"

    def test_decode_access_token_invalid(self):
        """
        测试 decode_access_token 处理无效 Token

        无效 Token 应返回 None 而非抛出异常
        """
        assert decode_access_token("garbage") is None
        assert decode_access_token("a.b.c") is None


class TestTokenBlacklist:
    """Token 黑名单功能测试套件（Mock Redis）"""

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist_success(self):
        """
        测试成功将 Token 加入黑名单

        Mock Redis 成功时应返回 True
        """
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.add_token_to_blacklist = AsyncMock(return_value=True)
            result = await add_token_to_blacklist("test_token_123")
            assert result is True
            mock_cache.add_token_to_blacklist.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist_failure(self):
        """
        测试 Redis 失败时加入黑名单

        Mock Redis 抛出异常时应捕获并返回 False
        """
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.add_token_to_blacklist = AsyncMock(
                side_effect=Exception("Redis connection error")
            )
            result = await add_token_to_blacklist("test_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_add_token_with_custom_ttl(self):
        """
        测试使用自定义 TTL 加入黑名单

        指定 ttl 参数时，应使用该值而非从 Token 解析
        """
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.add_token_to_blacklist = AsyncMock(return_value=True)
            result = await add_token_to_blacklist("token_xyz", ttl=3600)
            assert result is True
            call_kwargs = mock_cache.add_token_to_blacklist.call_args[1]
            assert call_kwargs["expire"] == 3600

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_true(self):
        """
        测试 Token 在黑名单中返回 True

        Mock Redis exists 返回非零值表示 Token 已被列入黑名单
        """
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.is_token_revoked = AsyncMock(return_value=True)
            result = await is_token_blacklisted("blacklisted_token")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_false(self):
        """
        测试 Token 不在黑名单中返回 False

        Mock Redis exists 返回 0 表示 Token 未被列入黑名单
        """
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.is_token_revoked = AsyncMock(return_value=False)
            result = await is_token_blacklisted("valid_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_exception(self):
        """
        测试 Redis 异常时黑名单检查降级

        Redis 连接失败时应返回 False（允许请求通过）
        """
        with patch('app.core.security.cache_service') as mock_cache:
            mock_cache.is_token_revoked = AsyncMock(
                side_effect=Exception("Redis timeout")
            )
            result = await is_token_blacklisted("any_token")
            assert result is False


class TestSecurityConstants:
    """安全模块常量测试"""

    def test_bcrypt_max_length(self):
        """
        测试 bcrypt 最大密码长度常量

        应等于标准 bcrypt 的 72 字节限制
        """
        assert BCRYPT_MAX_PASSWORD_LENGTH == 72

    def test_token_config_constants(self):
        """
        测试 Token 配置常量值

        验证各配置常量的预期值
        """
        assert TOKEN_BLACKLIST_PREFIX == "token:blacklist:"
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert ALGORITHM == "HS256"


class TestTruncatePassword:
    """_truncate_password 内部函数测试"""

    def test_short_password_not_truncated(self):
        """
        测试短密码不被截断

        小于 72 字节的密码应原样返回
        """
        from app.core.security import _truncate_password
        pwd = b"short_password"
        result = _truncate_password("short_password")
        assert result == pwd

    def test_exact_max_length_password(self):
        """
        测试恰好 72 字节密码不被截断

        边界值：刚好 72 字节不应截断
        """
        from app.core.security import _truncate_password
        pwd = "a" * 72
        result = _truncate_password(pwd)
        assert len(result) == 72

    def test_over_max_length_truncated(self):
        """
        测试超过 72 字节密码被截断

        超过 72 字节的密码应截断到 72 字节
        """
        from app.core.security import _truncate_password
        long_pwd = "a" * 100
        result = _truncate_password(long_pwd)
        assert len(result) == 72
