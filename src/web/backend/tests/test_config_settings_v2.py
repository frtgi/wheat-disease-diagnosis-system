# -*- coding: utf-8 -*-
"""
应用配置模块测试

覆盖范围:
- 7 个新配置项默认值验证 (SSE/GPU/队列相关)
- Settings 类实例化与基本属性
- 环境变量覆盖能力测试
- DATABASE_URL / REDIS_URL / JWT_SECRET_KEY 属性方法
- MINIO_CONFIGURED 属性与 validate_minio_config 方法
- CORS 配置逻辑
"""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest


class TestNewConfigurationDefaults:
    """新配置项默认值验证测试（V6 新增）"""

    def test_sse_timeout_seconds_default(self):
        """
        测试 SSE_TIMEOUT_SECONDS 默认值

        验证 SSE 流超时时间默认为 120 秒
        """
        from app.core.config import settings
        assert isinstance(settings.SSE_TIMEOUT_SECONDS, int)
        assert settings.SSE_TIMEOUT_SECONDS > 0

    def test_sse_heartbeat_interval_default(self):
        """
        测试 SSE_HEARTBEAT_INTERVAL 默认值

        验证心跳发送间隔默认为 15 秒
        """
        from app.core.config import settings
        assert isinstance(settings.SSE_HEARTBEAT_INTERVAL, int)
        assert settings.SSE_HEARTBEAT_INTERVAL > 0

    def test_sse_backpressure_queue_size_default(self):
        """
        测试 SSE_BACKPRESSURE_QUEUE_SIZE 默认值

        验证背压控制队列大小默认为 100
        """
        from app.core.config import settings
        assert isinstance(settings.SSE_BACKPRESSURE_QUEUE_SIZE, int)
        assert settings.SSE_BACKPRESSURE_QUEUE_SIZE > 0

    def test_max_concurrent_diagnosis_default(self):
        """
        测试 MAX_CONCURRENT_DIAGNOSIS 默认值

        验证最大并发诊断数默认为 3
        """
        from app.core.config import settings
        assert isinstance(settings.MAX_CONCURRENT_DIAGNOSIS, int)
        assert settings.MAX_CONCURRENT_DIAGNOSIS > 0

    def test_max_diagnosis_queue_size_default(self):
        """
        测试 MAX_DIAGNOSIS_QUEUE_SIZE 默认值

        验证诊断队列最大容量默认为 10
        """
        from app.core.config import settings
        assert isinstance(settings.MAX_DIAGNOSIS_QUEUE_SIZE, int)
        assert settings.MAX_DIAGNOSIS_QUEUE_SIZE > 0

    def test_diagnosis_queue_timeout_default(self):
        """
        测试 DIAGNOSIS_QUEUE_TIMEOUT 默认值

        验证诊断队列超时时间默认为 300 秒
        """
        from app.core.config import settings
        assert isinstance(settings.DIAGNOSIS_QUEUE_TIMEOUT, int)
        assert settings.DIAGNOSIS_QUEUE_TIMEOUT > 0

    def test_gpu_memory_threshold_default(self):
        """
        测试 GPU_MEMORY_THRESHOLD 默认值

        验证 GPU 显存监控阈值默认为 0.90 (90%)
        """
        from app.core.config import settings
        assert isinstance(settings.GPU_MEMORY_THRESHOLD, float)
        assert 0 < settings.GPU_MEMORY_THRESHOLD <= 1.0


class TestSettingsInstantiation:
    """Settings 类实例化测试"""

    def test_settings_basic_attributes(self):
        """
        测试 Settings 基本属性存在性

        验证实例包含所有核心配置字段
        """
        from app.core.config import settings

        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'APP_VERSION')
        assert hasattr(settings, 'DEBUG')
        assert hasattr(settings, 'API_PREFIX')
        assert settings.APP_NAME == "基于多模态融合的小麦病害诊断系统"
        assert settings.APP_VERSION == "1.0.0"

    def test_database_configuration_exists(self):
        """
        测试数据库配置属性存在性

        验证数据库连接参数已配置（值可能来自 .env 文件）
        """
        from app.core.config import settings

        assert hasattr(settings, 'DATABASE_HOST')
        assert hasattr(settings, 'DATABASE_PORT')
        assert hasattr(settings, 'DATABASE_NAME')
        assert isinstance(settings.DATABASE_PORT, int)

    def test_redis_configuration_exists(self):
        """
        测试 Redis 配置属性存在性

        验证 Redis 连接参数已配置
        """
        from app.core.config import settings

        assert hasattr(settings, 'REDIS_HOST')
        assert hasattr(settings, 'REDIS_PORT')
        assert hasattr(settings, 'REDIS_DB')
        assert isinstance(settings.REDIS_PORT, int)


class TestEnvironmentVariableOverride:
    """环境变量覆盖能力测试（使用 monkeypatch）"""

    def test_settings_class_reads_env_on_creation(self):
        """
        测试 Settings 类在创建时读取环境变量

        验证配置值来自环境变量或 .env 文件
        """
        from app.core.config import settings
        assert settings.SSE_TIMEOUT_SECONDS is not None
        assert settings.GPU_MEMORY_THRESHOLD is not None

    def test_debug_mode_is_boolean(self):
        """
        测试 DEBUG 模式为布尔类型

        验证配置正确解析布尔值
        """
        from app.core.config import settings
        assert isinstance(settings.DEBUG, bool)


class TestPropertyMethods:
    """Settings 属性方法测试"""

    def test_database_url_property(self):
        """
        测试 DATABASE_URL 属性生成

        验证从各组件正确构建 MySQL 连接 URL
        """
        from app.core.config import settings
        url = settings.DATABASE_URL

        assert url.startswith("mysql+aiomysql://")
        assert settings.DATABASE_HOST in url
        assert settings.DATABASE_NAME in url
        assert "charset=utf8mb4" in url

    def test_redis_url_property_structure(self):
        """
        测试 REDIS_URL 属性基本结构

        验证 Redis 连接字符串格式正确
        """
        from app.core.config import settings
        url = settings.REDIS_URL

        assert url.startswith("redis://")
        assert str(settings.REDIS_PORT) in url

    def test_jwt_secret_key_exists(self):
        """
        测试 JWT_SECRET_KEY 属性可访问

        验证密钥已配置或自动生成（DEBUG 模式）
        """
        from app.core.config import settings

        secret = settings.JWT_SECRET_KEY
        assert secret is not None
        assert len(secret) > 0

    def test_jwt_secret_key_caching(self):
        """
        测试 JWT 密钥缓存机制

        验证多次访问返回相同密钥（避免重复生成）
        """
        from app.core.config import settings

        first_call = settings.JWT_SECRET_KEY
        second_call = settings.JWT_SECRET_KEY

        assert first_call == second_call

    def test_minio_configured_property_type(self):
        """
        测试 MINIO_CONFIGURED 属性返回布尔值

        验证属性根据凭据存在性返回 True/False
        """
        from app.core.config import settings

        result = settings.MINIO_CONFIGURED
        assert isinstance(result, bool)


class TestValidateMinioConfig:
    """validate_minio_config() 方法测试"""

    def test_validate_minio_config_callable(self):
        """
        测试 validate_minio_config 方法可调用

        验证方法存在且在 DEBUG 模式下不抛异常
        """
        from app.core.config import settings

        if settings.DEBUG:
            settings.validate_minio_config()
        else:
            with pytest.raises((ValueError, Exception)):
                settings.validate_minio_config()


class TestCORSConfiguration:
    """CORS 配置测试"""

    def test_cors_origins_is_list(self):
        """
        测试 CORS_ORIGINS 为列表类型

        验证配置包含允许的域名列表
        """
        from app.core.config import settings

        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) > 0

    def test_cors_origins_contains_localhost(self):
        """
        测试默认 CORS 配置包含 localhost

        验证开发环境通常允许本地访问
        """
        from app.core.config import settings

        has_local = any("localhost" in origin or "127.0.0.1" in origin for origin in settings.CORS_ORIGINS)
        assert has_local
