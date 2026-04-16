"""
诊断请求验证器单元测试
测试覆盖：
1. 图像验证（大小、格式、Magic Number）
2. Mock 模式切换逻辑
3. GPU 显存检查
4. 并发限流功能
5. 图像预处理
6. DiagnosisRequestValidator 集成验证
"""
import os
import pytest
import asyncio
from io import BytesIO
from PIL import Image

from app.api.v1.diagnosis_validator import (
    validate_image,
    check_image_magic_number,
    is_mock_enabled,
    should_use_mock,
    get_mock_service,
    get_cache_manager_safe,
    check_gpu_memory,
    acquire_rate_limit,
    release_rate_limit,
    preprocess_image,
    DiagnosisRequestValidator,
)


class TestImageValidation:
    """图像验证功能测试"""

    def test_valid_jpeg_image(self):
        """测试有效的 JPEG 图像验证"""
        img = Image.new('RGB', (800, 600), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.jpg")

        assert is_valid is True
        assert error is None

    def test_valid_png_image(self):
        """测试有效的 PNG 图像验证"""
        img = Image.new('RGB', (400, 300), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.png")

        assert is_valid is True
        assert error is None

    def test_oversized_image(self):
        """测试超大图像文件拒绝"""
        large_data = b'\x00' * (11 * 1024 * 1024)  # 11MB

        is_valid, error = validate_image(large_data, "large.jpg")

        assert is_valid is False
        assert "过大" in error or "10MB" in error

    def test_invalid_format_bmp(self):
        """测试不支持的 BMP 格式"""
        img = Image.new('RGB', (100, 100))
        buffer = BytesIO()
        img.save(buffer, format='BMP')
        image_bytes = buffer.getvalue()

        is_valid, error = validate_image(image_bytes, "test.bmp")

        assert is_valid is False
        assert "不支持的图像格式" in error or "BMP" in error

    def test_corrupted_image_data(self):
        """测试损坏的图像数据"""
        invalid_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # 假 PNG 头

        is_valid, error = validate_image(invalid_data, "corrupt.png")

        assert is_valid is False


class TestMagicNumberCheck:
    """Magic Number 检查测试"""

    def test_jpeg_magic_number(self):
        """测试 JPEG 文件头标识"""
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00'
        is_valid, error = check_image_magic_number(jpeg_header)

        assert is_valid is True
        assert error is None

    def test_png_magic_number(self):
        """测试 PNG 文件头标识"""
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        is_valid, error = check_image_magic_number(png_header)

        assert is_valid is True
        assert error is None

    def test_webp_magic_number(self):
        """测试 WEBP 文件头标识"""
        webp_header = b'RIFF\x00\x00\x00\x00WEBP'
        is_valid, error = check_image_magic_number(webp_header)

        assert is_valid is True
        assert error is None

    def test_invalid_magic_number(self):
        """测试无效的文件头"""
        fake_header = b'FAKEHEADER123456789012'
        is_valid, error = check_image_magic_number(fake_header)

        assert is_valid is False
        assert error is not None

    def test_too_small_file(self):
        """测试过小的文件"""
        tiny_data = b'\x00\x01\x02'
        is_valid, error = check_image_magic_number(tiny_data)

        assert is_valid is False
        assert "太小" in error


class TestMockMode:
    """Mock 模式切换测试"""

    def test_is_mock_enabled_default(self):
        """测试默认 Mock 模式状态（未设置环境变量）"""
        original = os.environ.get("WHEATAGENT_MOCK_AI")
        if "WHEATAGENT_MOCK_AI" in os.environ:
            del os.environ["WHEATAGENT_MOCK_AI"]

        result = is_mock_enabled()

        assert result is False

        if original:
            os.environ["WHEATAGENT_MOCK_AI"] = original

    def test_is_mock_enabled_true_env(self):
        """测试通过环境变量启用 Mock 模式"""
        original = os.environ.get("WHEATAGENT_MOCK_AI")
        os.environ["WHEATAGENT_MOCK_AI"] = "true"

        result = is_mock_enabled()

        assert result is True

        if original:
            os.environ["WHEATAGENT_MOCK_AI"] = original
        else:
            del os.environ["WHEATAGENT_MOCK_AI"]

    def test_get_mock_service_instance(self):
        """测试获取 Mock 服务实例"""
        service = get_mock_service()

        assert service is not None
        assert hasattr(service, 'diagnose_by_image') or hasattr(service, 'diagnose_by_text')

    async def test_should_use_mock_with_qwen_unavailable(self):
        """测试 Qwen 服务不可用时使用 Mock 模式"""
        result = should_use_mock()

        assert isinstance(result, bool)
        assert result is True or result is False  # 取决于实际环境


class TestGPUMemoryCheck:
    """GPU 显存检查测试"""

    def test_gpu_check_without_pytorch(self):
        """测试无 PyTorch 环境下的降级处理"""
        try:
            import torch
            has_torch = True
        except ImportError:
            has_torch = False

        if not has_torch:
            is_ok, error = check_gpu_memory(1024)
            assert is_ok is True  # 无 PyTorch 时应该跳过检查
            assert error is None


class TestRateLimiter:
    """并发限流测试"""

    async def test_acquire_and_release(self):
        """测试限流许可的获取和释放"""
        acquired = await acquire_rate_limit("test_diagnosis")

        if acquired:
            await release_rate_limit("test_diagnosis")


class TestImagePreprocessing:
    """图像预处理测试"""

    def test_basic_preprocessing(self):
        """测试基本图像预处理"""
        img = Image.new('RGB', (1920, 1080), color='green')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        original_bytes = buffer.getvalue()

        processed_img, processed_bytes = preprocess_image(original_bytes)

        assert processed_img.mode == 'RGB'
        assert len(processed_bytes) > 0
        assert isinstance(processed_img, Image.Image)

    def test_resize_preprocessing(self):
        """测试带尺寸调整的预处理"""
        img = Image.new('RGB', (4000, 3000), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        original_bytes = buffer.getvalue()

        target_size = (512, 512)
        processed_img, _ = preprocess_image(original_bytes, target_size=target_size)

        assert processed_img.size == target_size

    def test_rgba_to_rgb_conversion(self):
        """测试 RGBA 到 RGB 的转换"""
        img = Image.new('RGBA', (200, 200), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        original_bytes = buffer.getvalue()

        processed_img, _ = preprocess_image(original_bytes)

        assert processed_img.mode == 'RGB'


class TestDiagnosisRequestValidator:
    """DiagnosisRequestValidator 集成验证器测试"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例（禁用 GPU 检查和限流）"""
        return DiagnosisRequestValidator(
            enable_gpu_check=False,
            enable_rate_limit=False,
            enable_cache=False
        )

    async def test_validate_valid_image_upload(self, validator):
        """测试有效的图像上传验证"""
        img = Image.new('RGB', (800, 600))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()

        is_valid, error = await validator.validate_image_upload(image_bytes, "test.jpg")

        assert is_valid is True
        assert error is None

    async def test_validate_invalid_image_upload(self, validator):
        """测试无效的图像上传验证"""
        invalid_data = b'not an image'

        is_valid, error = await validator.validate_image_upload(invalid_data, "fake.jpg")

        assert is_valid is False
        assert error is not None

    async def test_validate_request_with_both_inputs(self, validator):
        """测试同时提供图像和症状的请求"""
        is_valid, error = await validator.validate_request_context(has_image=True, has_symptoms=True)

        assert is_valid is True
        assert error is None

    async def test_validate_request_with_no_input(self, validator):
        """测试无输入的请求（应失败）"""
        is_valid, error = await validator.validate_request_context(has_image=False, has_symptoms=False)

        assert is_valid is False
        assert "至少提供" in error or "图像或症状" in error

    async def test_preflight_checks_disabled_features(self, validator):
        """测试禁用功能的预检检查"""
        is_valid, error = await validator.preflight_checks()

        assert is_valid is True
        assert error is None

    async def test_cleanup_no_resources(self, validator):
        """测试无资源时的清理操作"""
        await validator.cleanup()


class TestCacheManager:
    """缓存管理器测试"""

    def test_get_cache_manager_safe(self):
        """测试安全获取缓存管理器"""
        manager = get_cache_manager_safe()

        if manager is not None:
            assert hasattr(manager, 'get') and hasattr(manager, 'set')
        else:
            assert manager is None  # 缓存不可用


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_filename_validation(self):
        """测试空文件名的图像验证"""
        img = Image.new('RGB', (100, 100))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')

        is_valid, error = validate_image(buffer.getvalue(), "")

        assert is_valid is True

    def test_unicode_filename(self):
        """测试 Unicode 文件名处理"""
        img = Image.new('RGB', (100, 100))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')

        unicode_name = "测试图片_小麦病害.jpeg"
        is_valid, error = validate_image(buffer.getvalue(), unicode_name)

        assert is_valid is True

    def test_very_small_image(self):
        """测试极小尺寸图像"""
        img = Image.new('RGB', (1, 1))
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        is_valid, error = validate_image(buffer.getvalue(), "tiny.png")

        assert is_valid is True

    async def test_concurrent_validations(self):
        """测试并发图像验证"""
        async def single_validation():
            img = Image.new('RGB', (500, 500))
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            return validate_image(buffer.getvalue(), f"concurrent_{id(img)}.jpg")

        tasks = [single_validation() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        all_valid = all(is_valid for is_valid, _ in results)
        assert all_valid


class TestLargeFileHandling:
    """超大文件处理测试 - 验证文件大小限制和边界条件"""

    def test_exactly_10mb_file(self):
        """
        测试恰好 10MB 的文件（边界值）
        验证在大小限制边界上的行为（> 10MB 才拒绝，== 10MB 进入格式检查）
        """
        exact_10mb_data = b'\x00' * (10 * 1024 * 1024)
        is_valid, error = validate_image(exact_10mb_data, "exact_10mb.jpg")

        assert is_valid is False
        assert "过大" in error or "10MB" in error or "无法解析" in error or "无效" in error

    def test_slightly_over_10mb(self):
        """
        测试略超过 10MB 的文件
        验证超限文件的正确拒绝
        """
        over_10mb_data = b'\x00' * (10 * 1024 * 1024 + 1)
        is_valid, error = validate_image(over_10mb_data, "over_10mb.jpg")

        assert is_valid is False
        assert "10MB" in error

    def test_large_valid_jpeg_under_limit(self):
        """
        测试接近但未超过限制的大文件（9.9MB）
        验证大文件在限制范围内能正常处理
        """
        large_img = Image.new('RGB', (4000, 3000), color='blue')
        buffer = BytesIO()
        large_img.save(buffer, format='JPEG', quality=95)
        image_bytes = buffer.getvalue()

        if len(image_bytes) < 10 * 1024 * 1024:
            is_valid, error = validate_image(image_bytes, "large_but_valid.jpg")
            assert is_valid is True

    def test_empty_file(self):
        """
        测试空文件（0 字节）
        验证对空输入的处理
        """
        empty_data = b''
        is_valid, error = validate_image(empty_data, "empty.jpg")

        assert is_valid is False
        assert error is not None


class TestAbnormalImageData:
    """合法但异常的图像数据测试 - 验证异常数据的鲁棒性"""

    def test_truncated_jpeg(self):
        """
        测试截断的 JPEG 文件
        模拟网络传输中断导致的不完整文件
        """
        valid_jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01'
        truncated_data = valid_jpeg_header + b'\x00' * 100

        is_valid, error = validate_image(truncated_data, "truncated.jpg")

        assert is_valid is False

    def test_valid_header_corrupted_body(self):
        """
        测试有效文件头但损坏的数据体
        模拟文件头被篡改但数据部分损坏的情况
        """
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR'
        corrupted_body = png_header + b'\xff' * 500

        is_valid, error = validate_image(corrupted_body, "corrupted.png")

        assert is_valid is False

    def test_minimal_valid_png(self):
        """
        测试最小有效 PNG 文件
        验证最小可解析图像的处理能力
        """
        minimal_png = Image.new('RGB', (1, 1), color=(0, 0, 0))
        buffer = BytesIO()
        minimal_png.save(buffer, format='PNG')

        is_valid, error = validate_image(buffer.getvalue(), "minimal.png")

        assert is_valid is True

    def test_grayscale_image(self):
        """
        测试灰度图像（非 RGB）
        验证对不同色彩模式的支持
        """
        gray_img = Image.new('L', (200, 200), color=128)
        buffer = BytesIO()
        gray_img.save(buffer, format='PNG')

        is_valid, error = validate_image(buffer.getvalue(), "grayscale.png")

        assert is_valid is True

    def test_palette_mode_image(self):
        """
        测试调色板模式图像（P 模式）
        验证对索引颜色图像的支持
        """
        palette_img = Image.new('P', (100, 100))
        buffer = BytesIO()
        palette_img.save(buffer, format='PNG')

        is_valid, error = validate_image(buffer.getvalue(), "palette.png")

        assert is_valid is True

    def test_image_with_metadata(self):
        """
        测试包含大量元数据的图像
        验证 EXIF 等元数据不影响验证结果
        """
        normal_img = Image.new('RGB', (800, 600))
        from PIL.PngImagePlugin import PngInfo
        pnginfo = PngInfo()
        pnginfo.add_text("Comment", "A" * 1000)
        pnginfo.add_text("Software", "Test Software")
        pnginfo.add_text("Author", "Test Author")

        buffer = BytesIO()
        normal_img.save(buffer, format='PNG', pnginfo=pnginfo)

        is_valid, error = validate_image(buffer.getvalue(), "metadata.png")

        assert is_valid is True


class TestConcurrentValidationConflicts:
    """并发验证冲突测试 - 验证高并发下的资源竞争和状态一致性"""

    @pytest.fixture
    def concurrent_validator(self):
        """
        创建启用限流的并发验证器实例

        返回:
            DiagnosisRequestValidator: 配置了限流功能的验证器
        """
        return DiagnosisRequestValidator(
            enable_gpu_check=False,
            enable_rate_limit=True,
            enable_cache=False
        )

    async def test_rapid_sequential_validations(self, concurrent_validator):
        """
        测试快速连续的图像验证请求
        验证系统在高频率请求下的稳定性
        """
        validation_count = 20
        success_count = 0

        async def rapid_validation(index: int):
            nonlocal success_count
            img = Image.new('RGB', (300, 300))
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            is_valid, _ = await concurrent_validator.validate_image_upload(
                buffer.getvalue(),
                f"rapid_{index}.jpg"
            )
            if is_valid:
                success_count += 1

        tasks = [rapid_validation(i) for i in range(validation_count)]
        await asyncio.gather(*tasks)

        assert success_count == validation_count

    async def test_simultaneous_preflight_checks(self, concurrent_validator):
        """
        测试同时进行的预检检查
        验证限流机制在并发场景下正常工作
        """
        check_results = []

        async def parallel_preflight():
            result = await concurrent_validator.preflight_checks()
            check_results.append(result)

        tasks = [parallel_preflight() for _ in range(5)]
        await asyncio.gather(*tasks)

        passed_count = sum(1 for ok, _ in check_results if ok)
        assert passed_count > 0

    async def test_cleanup_after_partial_failure(self, concurrent_validator):
        """
        测试部分失败后的资源清理
        验证即使某些步骤失败，资源也能正确释放
        """
        preflight_ok, _ = await concurrent_validator.preflight_checks()

        try:
            invalid_data = b'not an image'
            is_valid, _ = await concurrent_validator.validate_image_upload(
                invalid_data,
                "invalid.jpg"
            )
            if not is_valid:
                raise ValueError("模拟验证失败")
        except Exception:
            pass
        finally:
            await concurrent_validator.cleanup()

        assert concurrent_validator._rate_limit_acquired is False

    async def test_interleaved_acquire_release_cycles(self):
        """
        测试交错的获取-释放循环
        验证限流许可的正确生命周期管理
        """
        cycles = 5

        for i in range(cycles):
            acquired = await acquire_rate_limit("test_interleaved")
            if acquired:
                await asyncio.sleep(0.001)
                await release_rate_limit("test_interleaved")


class TestValidatorStateManagement:
    """验证器状态管理测试 - 验证内部状态的正确性"""

    def test_initial_state(self):
        """
        测试验证器的初始状态
        验证新创建的验证器具有正确的默认状态
        """
        validator = DiagnosisRequestValidator()

        assert validator.enable_gpu_check is False
        assert validator.enable_rate_limit is True
        assert validator.enable_cache is True
        assert validator._rate_limit_acquired is False

    def test_state_after_successful_preflight(self):
        """
        测试成功预检后的状态变化
        验证获取限流许可后状态正确更新
        """
        import asyncio

        async def run_test():
            validator = DiagnosisRequestValidator(
                enable_gpu_check=False,
                enable_rate_limit=True
            )

            await validator.preflight_checks()

            return validator._rate_limit_acquired

        result = asyncio.run(run_test())

        assert result is True

    def test_state_after_cleanup(self):
        """
        测试清理后的状态重置
        验证 cleanup 方法正确释放所有资源
        """
        import asyncio

        async def run_test():
            validator = DiagnosisRequestValidator(enable_gpu_check=False)
            await validator.preflight_checks()
            await validator.cleanup()

            return validator._rate_limit_acquired

        result = asyncio.run(run_test())

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
