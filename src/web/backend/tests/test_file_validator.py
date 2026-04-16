"""
文件验证工具测试脚本
演示如何使用文件上传安全验证功能
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.file_validator import (
    validate_upload_file,
    get_file_extension,
    is_allowed_image_type,
    FileValidationErrorType
)


def test_jpeg_validation():
    """
    测试 JPEG 文件验证
    
    创建一个包含 JPEG magic number 的测试文件内容
    """
    jpeg_header = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
    jpeg_content = jpeg_header + b"\x00" * 100
    
    result = validate_upload_file(
        file_content=jpeg_content,
        filename="test.jpg",
        declared_content_type="image/jpeg"
    )
    
    print("=" * 60)
    print("测试 1: JPEG 文件验证")
    print("=" * 60)
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    print(f"检测类型: {result.detected_type}")
    print(f"文件大小: {result.file_size} bytes")
    if not result.is_valid:
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
    print()


def test_png_validation():
    """
    测试 PNG 文件验证
    
    创建一个包含 PNG magic number 的测试文件内容
    """
    png_header = b"\x89PNG\r\n\x1a\n"
    png_content = png_header + b"\x00" * 100
    
    result = validate_upload_file(
        file_content=png_content,
        filename="test.png",
        declared_content_type="image/png"
    )
    
    print("=" * 60)
    print("测试 2: PNG 文件验证")
    print("=" * 60)
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    print(f"检测类型: {result.detected_type}")
    print(f"文件大小: {result.file_size} bytes")
    if not result.is_valid:
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
    print()


def test_webp_validation():
    """
    测试 WebP 文件验证
    
    创建一个包含 WebP magic number 的测试文件内容
    """
    webp_header = b"RIFF\x00\x00\x00\x00WEBP"
    webp_content = webp_header + b"\x00" * 100
    
    result = validate_upload_file(
        file_content=webp_content,
        filename="test.webp",
        declared_content_type="image/webp"
    )
    
    print("=" * 60)
    print("测试 3: WebP 文件验证")
    print("=" * 60)
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    print(f"检测类型: {result.detected_type}")
    print(f"文件大小: {result.file_size} bytes")
    if not result.is_valid:
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
    print()


def test_invalid_file_type():
    """
    测试无效文件类型验证
    
    创建一个不包含有效 magic number 的测试文件内容
    """
    invalid_content = b"INVALID_FILE_CONTENT"
    
    result = validate_upload_file(
        file_content=invalid_content,
        filename="test.txt",
        declared_content_type="text/plain"
    )
    
    print("=" * 60)
    print("测试 4: 无效文件类型验证")
    print("=" * 60)
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    if not result.is_valid:
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
    print()


def test_file_size_exceeded():
    """
    测试文件大小超限验证
    
    创建一个超过大小限制的测试文件内容
    """
    jpeg_header = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
    large_content = jpeg_header + b"\x00" * (11 * 1024 * 1024)
    
    result = validate_upload_file(
        file_content=large_content,
        filename="large.jpg",
        declared_content_type="image/jpeg",
        max_size=10 * 1024 * 1024
    )
    
    print("=" * 60)
    print("测试 5: 文件大小超限验证")
    print("=" * 60)
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    print(f"文件大小: {result.file_size / (1024 * 1024):.2f} MB")
    if not result.is_valid:
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
    print()


def test_empty_file():
    """
    测试空文件验证
    """
    result = validate_upload_file(
        file_content=b"",
        filename="empty.jpg",
        declared_content_type="image/jpeg"
    )
    
    print("=" * 60)
    print("测试 6: 空文件验证")
    print("=" * 60)
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    if not result.is_valid:
        print(f"错误类型: {result.error_type}")
        print(f"错误消息: {result.error_message}")
    print()


def test_helper_functions():
    """
    测试辅助函数
    """
    print("=" * 60)
    print("测试 7: 辅助函数测试")
    print("=" * 60)
    
    print(f"get_file_extension('image/jpeg'): {get_file_extension('image/jpeg')}")
    print(f"get_file_extension('image/png'): {get_file_extension('image/png')}")
    print(f"get_file_extension('image/webp'): {get_file_extension('image/webp')}")
    
    print(f"\nis_allowed_image_type('image/jpeg'): {is_allowed_image_type('image/jpeg')}")
    print(f"is_allowed_image_type('image/png'): {is_allowed_image_type('image/png')}")
    print(f"is_allowed_image_type('application/pdf'): {is_allowed_image_type('application/pdf')}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("文件上传安全验证功能测试")
    print("=" * 60 + "\n")
    
    test_jpeg_validation()
    test_png_validation()
    test_webp_validation()
    test_invalid_file_type()
    test_file_size_exceeded()
    test_empty_file()
    test_helper_functions()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)
