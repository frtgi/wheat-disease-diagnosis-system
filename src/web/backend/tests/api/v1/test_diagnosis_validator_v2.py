# -*- coding: utf-8 -*-
"""
诊断请求验证器测试模块

覆盖范围:
- validate_image() 图像大小和格式验证
- check_image_magic_number() Magic Number 校验
- ensure_ai_service_ready() AI 服务就绪检查
- check_gpu_memory() GPU 显存检查
- acquire_rate_limit() / release_rate_limit() 并发限流
- preprocess_image() 图像预处理
- DiagnosisRequestValidator 类完整流程
"""

import asyncio
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from PIL import Image

# 导入被测模块
from app.api.v1.diagnosis_validator import (
    MAX_IMAGE_SIZE,
    ALLOWED_IMAGE_FORMATS,
    validate_image,
    check_image_magic_number,
    ensure_ai_service_ready,
    get_cache_manager_safe,
    check_gpu_memory,
    acquire_rate_limit,
    release_rate_limit,
    preprocess_image,
    DiagnosisRequestValidator,
)


class TestValidateImage:
    """validate_image() 图像验证函数测试"""

    def test_valid_jpeg_image(self):
        """
        测试有效的 JPEG 图像通过验证

        验证标准 JPEG 文件能正确识别并返回 (True, None)
        """
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.jpg")
        assert is_valid is True
        assert error is None

    def test_valid_png_image(self):
        """
        测试有效的 PNG 图像通过验证

        验证 PNG 格式被支持
        """
        img = Image.new('RGB', (50, 50), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.png")
        assert is_valid is True
        assert error is None

    def test_valid_webp_image(self):
        """
        测试有效的 WEBP 图像通过验证

        验证 WEBP 格式被支持
        """
        img = Image.new('RGB', (80, 80), color='green')
        buffer = BytesIO()
        img.save(buffer, format='WEBP')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.webp")
        assert is_valid is True
        assert error is None

    def test_image_exceeds_size_limit(self):
        """
        测试超过 10MB 大小限制的图像

        验证大文件被拒绝并返回有意义的错误消息
        """
        large_data = b'\x00' * (MAX_IMAGE_SIZE + 1024)  # 超过限制 1KB
        is_valid, error = validate_image(large_data, "large.jpg")

        assert is_valid is False
        assert "过大" in error
        assert "10MB" in error

    def test_invalid_image_format(self):
        """
        测试不支持的图像格式（如 BMP）

        验证非 JPEG/PNG/WEBP 格式被拒绝
        """
        img = Image.new('RGB', (60, 60))
        buffer = BytesIO()
        img.save(buffer, format='BMP')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.bmp")
        assert is_valid is False
        assert "不支持" in error or "格式" in error

    def test_corrupted_image_data(self):
        """
        测试损坏的图像数据

        验证无法解析的无效字节序列被正确处理
        """
        invalid_data = b'\xff\xd8\xff\x00' * 1000  # 假 JPEG 头但内容无效
        is_valid, error = validate_image(invalid_data, "corrupted.jpg")

        assert is_valid is False
        assert error is not None

    def test_empty_image_data(self):
        """
        测试空图像数据

        验证空字节数组被正确处理
        """
        is_valid, error = validate_image(b'', "empty.jpg")
        assert is_valid is False


class TestCheckImageMagicNumber:
    """check_image_magic_number() Magic Number 校验测试"""

    def test_valid_jpeg_magic_number(self):
        """
        测试 JPEG 的 Magic Number: FF D8 FF

        验证正确的 JPEG 文件头被识别
        """
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 4
        is_valid, error = check_image_magic_number(jpeg_header)

        assert is_valid is True
        assert error is None

    def test_valid_png_magic_number(self):
        """
        测试 PNG 的 Magic Number: 89 50 4E 47 0D 0A 1A 0A

        验证标准的 PNG 文件签名被识别
        """
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 4
        is_valid, error = check_image_magic_number(png_header)

        assert is_valid is True
        assert error is None

    def test_valid_webp_magic_number(self):
        """
        测试 WEBP 的 Magic Number: RIFF....WEBP

        验证 WEBP 格式的 RIFF 容器头被识别
        """
        webp_header = b'RIFF\x00\x00\x00\x00WEBP'
        is_valid, error = check_image_magic_number(webp_header)

        assert is_valid is True
        assert error is None

    def test_invalid_magic_number(self):
        """
        测试无效的 Magic Number

        验证未知格式的文件头被拒绝
        """
        invalid_header = b'GIF89a' + b'\x00' * 6
        is_valid, error = check_image_magic_number(invalid_header)

        assert is_valid is False
        assert error is not None

    def test_file_too_small_for_magic_check(self):
        """
        测试小于 12 字节的文件

        验证过小的文件无法进行 Magic Number 检查
        """
        small_data = b'\xff\xd8'
        is_valid, error = check_image_magic_number(small_data)

        assert is_valid is False
        assert "太小" in error


class TestEnsureAIServiceReady:
    """ensure_ai_service_ready() AI 服务就绪检查测试"""

    def test_ensure_ai_service_ready_when_loaded(self):
        """
        测试 Qwen 服务已加载时不抛异常

        验证服务正常加载时函数静默通过
        """
        mock_service = MagicMock()
        mock_service.is_loaded = True
        with patch('app.services.qwen_service.get_qwen_service', return_value=mock_service):
            ensure_ai_service_ready()

    def test_ensure_ai_service_ready_when_not_loaded(self):
        """
        测试 Qwen 服务未加载时抛出 HTTPException(503)

        验证服务未加载时返回 503 状态码
        """
        from fastapi import HTTPException
        mock_service = MagicMock()
        mock_service.is_loaded = False
        with patch('app.services.qwen_service.get_qwen_service', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                ensure_ai_service_ready()
            assert exc_info.value.status_code == 503

    def test_ensure_ai_service_ready_when_import_fails(self):
        """
        测试导入 Qwen 服务失败时抛出 HTTPException(503)

        验证导入异常被捕获并转换为 503 错误
        """
        from fastapi import HTTPException
        with patch('app.services.qwen_service.get_qwen_service', side_effect=ImportError("模块不存在")):
            with pytest.raises(HTTPException) as exc_info:
                ensure_ai_service_ready()
            assert exc_info.value.status_code == 503


class TestGPUMemoryCheck:
    """check_gpu_memory() GPU 显存检查测试"""

    def test_gpu_check_returns_tuple(self):
        """
        测试 GPU 检查返回元组

        验证函数始终返回 (bool, Optional[str]) 格式
        """
        is_ok, error = check_gpu_memory()
        assert isinstance(is_ok, bool)
        assert isinstance(error, (str, type(None)))

    def test_gpu_check_handles_no_gpu(self):
        """
        测试无 GPU 环境的处理

        验证在无 GPU 或 PyTorch 时优雅降级
        """
        is_ok, error = check_gpu_memory(1024)
        # 应该返回结果而不抛异常
        assert isinstance(is_ok, bool)


class TestRateLimitFunctions:
    """acquire_rate_limit / release_rate_limit 并发限流测试"""

    @pytest.mark.asyncio
    async def test_acquire_rate_limit_returns_bool(self):
        """
        测试获取限流许可返回布尔值

        验证函数返回类型正确
        """
        result = await acquire_rate_limit("diagnosis")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_release_rate_limit_no_exception(self):
        """
        测试释放限流许可不抛异常

        验证 release 操作正常执行
        """
        await release_rate_limit("diagnosis")
        # 如果没有抛异常则测试通过


class TestPreprocessImage:
    """preprocess_image() 图像预处理测试"""

    def test_preprocess_basic_rgb_image(self):
        """
        测试基本 RGB 图像预处理

        验证图像被正确转换为 RGB 并保存为 JPEG 字节
        """
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        original_bytes = buffer.getvalue()

        processed_img, processed_bytes = preprocess_image(original_bytes)

        assert processed_img.mode == 'RGB'
        assert len(processed_bytes) > 0
        assert isinstance(processed_bytes, bytes)

    def test_preprocess_with_resize(self):
        """
        测试带尺寸调整的预处理

        验证 target_size 参数生效
        """
        img = Image.new('RGB', (200, 200), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        original_bytes = buffer.getvalue()

        processed_img, _ = preprocess_image(original_bytes, target_size=(64, 64))

        assert processed_img.size == (64, 64)


class TestDiagnosisRequestValidator:
    """DiagnosisRequestValidator 诊断请求验证器类测试"""

    def test_validator_initialization_default(self):
        """
        测试验证器默认初始化

        验证默认参数值正确设置
        """
        validator = DiagnosisRequestValidator()

        assert validator.enable_gpu_check is False
        assert validator.enable_rate_limit is True
        assert validator.enable_cache is True
        assert validator._rate_limit_acquired is False

    def test_validator_custom_init(self):
        """
        测试自定义参数初始化

        验证构造函数参数正确传递
        """
        validator = DiagnosisRequestValidator(
            enable_gpu_check=True,
            enable_rate_limit=False,
            enable_cache=False
        )

        assert validator.enable_gpu_check is True
        assert validator.enable_rate_limit is False
        assert validator.enable_cache is False

    @pytest.mark.asyncio
    async def test_validate_image_upload_valid(self):
        """
        测试有效图像上传验证

        验证完整验证流程（大小+格式+Magic Number）通过
        """
        validator = DiagnosisRequestValidator()
        img = Image.new('RGB', (100, 100))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()

        is_valid, error = await validator.validate_image_upload(image_bytes, "test.jpg")
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_image_upload_too_large(self):
        """
        测试超大图像上传被拒绝

        验证大小检查在完整流程中生效
        """
        validator = DiagnosisRequestValidator()
        large_data = b'\x00' * (MAX_IMAGE_SIZE + 1024)

        is_valid, error = await validator.validate_image_upload(large_data, "large.jpg")
        assert is_valid is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_validate_request_context_both_missing(self):
        """
        测试缺少所有输入的上下文验证

        验证必须至少提供图像或症状描述之一
        """
        validator = DiagnosisRequestValidator()
        is_valid, error = await validator.validate_request_context(
            has_image=False,
            has_symptoms=False
        )
        assert is_valid is False
        assert "至少" in error

    @pytest.mark.asyncio
    async def test_validate_request_context_has_image(self):
        """
        测试提供图像时的上下文验证

        验证仅提供图像时验证通过
        """
        validator = DiagnosisRequestValidator()
        is_valid, error = await validator.validate_request_context(
            has_image=True,
            has_symptoms=False
        )
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_request_context_has_symptoms(self):
        """
        测试提供症状描述时的上下文验证

        验证仅提供症状时验证通过
        """
        validator = DiagnosisRequestValidator()
        is_valid, error = await validator.validate_request_context(
            has_image=False,
            has_symptoms=True
        )
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_preflight_checks_without_gpu_and_rate_limit(self):
        """
        测试禁用 GPU 和限流的预检检查

        验证简化配置下预检直接通过
        """
        validator = DiagnosisRequestValidator(
            enable_gpu_check=False,
            enable_rate_limit=False
        )

        is_valid, error = await validator.preflight_checks()
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_preflight_checks_with_gpu_failure(self):
        """
        测试 GPU 检查失败的预检

        验证 GPU 不可用时预检失败
        """
        validator = DiagnosisRequestValidator(
            enable_gpu_check=True,
            enable_rate_limit=False
        )

        with patch('app.api.v1.diagnosis_validator.check_gpu_memory', return_value=(False, "GPU不可用")):
            is_valid, error = await validator.preflight_checks()
            assert is_valid is False
            assert "GPU" in error

    @pytest.mark.asyncio
    async def test_cleanup_release_rate_limit(self):
        """
        测试清理操作释放限流许可

        验证 cleanup() 正确调用 release_rate_limit
        """
        validator = DiagnosisRequestValidator(enable_rate_limit=True)
        validator._rate_limit_acquired = True

        with patch('app.api.v1.diagnosis_validator.release_rate_limit', new_callable=AsyncMock) as mock_release:
            await validator.cleanup()
            mock_release.assert_called_once()


class TestGetCacheManagerSafe:
    """get_cache_manager_safe() 缓存管理器安全获取测试"""

    def test_get_cache_manager_when_available(self):
        """
        测试缓存服务可用时获取实例

        验证正常返回缓存管理器
        """
        mock_manager = MagicMock()
        with patch('app.api.v1.diagnosis_validator._cache_available', True):
            with patch('app.api.v1.diagnosis_validator._get_cache_manager', return_value=mock_manager):
                result = get_cache_manager_safe()
                assert result == mock_manager

    def test_get_cache_manager_when_unavailable(self):
        """
        测试缓存服务不可用时返回 None

        验证优雅降级不抛异常
        """
        with patch('app.api.v1.diagnosis_validator._cache_available', False):
            result = get_cache_manager_safe()
            assert result is None
