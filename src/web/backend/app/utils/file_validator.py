"""
文件上传安全验证工具
提供文件类型、大小和内容的综合安全验证功能
"""
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FileValidationErrorType(Enum):
    """
    文件验证错误类型枚举
    
    定义所有可能的文件验证错误类型
    """
    INVALID_TYPE = "invalid_type"
    INVALID_SIZE = "invalid_size"
    INVALID_CONTENT = "invalid_content"
    EMPTY_FILE = "empty_file"


@dataclass
class FileValidationResult:
    """
    文件验证结果数据类
    
    封装文件验证的结果信息
    
    Attributes:
        is_valid: 是否验证通过
        error_type: 错误类型（验证失败时）
        error_message: 错误消息（验证失败时）
        detected_type: 检测到的实际文件类型
        file_size: 文件大小（字节）
    """
    is_valid: bool
    error_type: Optional[FileValidationErrorType] = None
    error_message: Optional[str] = None
    detected_type: Optional[str] = None
    file_size: Optional[int] = None


MAGIC_NUMBERS: Dict[str, list] = {
    "image/jpeg": [
        b"\xFF\xD8\xFF\xDB",
        b"\xFF\xD8\xFF\xE0",
        b"\xFF\xD8\xFF\xE1",
        b"\xFF\xD8\xFF\xEE",
        b"\xFF\xD8\xFF\xFE",
    ],
    "image/png": [b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"],
    "image/webp": [b"RIFF"],
}

MIME_TO_EXTENSION: Dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_upload_file(
    file_content: bytes,
    filename: Optional[str] = None,
    declared_content_type: Optional[str] = None,
    max_size: int = MAX_FILE_SIZE,
    allowed_types: Optional[list] = None
) -> FileValidationResult:
    """
    验证上传文件的安全性
    
    执行文件类型、大小和内容的综合验证，包括：
    1. 文件大小验证
    2. 文件类型白名单验证
    3. 文件头 magic number 验证
    
    Args:
        file_content: 文件二进制内容
        filename: 原始文件名（可选，用于日志记录）
        declared_content_type: HTTP 声明的内容类型（可选）
        max_size: 最大文件大小（字节），默认 10MB
        allowed_types: 允许的 MIME 类型列表，默认为图片类型
    
    Returns:
        FileValidationResult: 验证结果对象，包含是否通过、错误信息等
    
    Example:
        >>> with open("image.jpg", "rb") as f:
        ...     content = f.read()
        >>> result = validate_upload_file(content, "image.jpg", "image/jpeg")
        >>> if result.is_valid:
        ...     print("文件验证通过")
        ... else:
        ...     print(f"验证失败: {result.error_message}")
    """
    if allowed_types is None:
        allowed_types = ALLOWED_MIME_TYPES
    
    if not file_content:
        logger.warning(f"空文件上传: {filename}")
        return FileValidationResult(
            is_valid=False,
            error_type=FileValidationErrorType.EMPTY_FILE,
            error_message="上传的文件内容为空",
            file_size=0
        )
    
    file_size = len(file_content)
    
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)
        logger.warning(
            f"文件大小超限: {filename}, 大小: {size_mb:.2f}MB, 限制: {max_size_mb:.2f}MB"
        )
        return FileValidationResult(
            is_valid=False,
            error_type=FileValidationErrorType.INVALID_SIZE,
            error_message=f"文件大小超过限制（{size_mb:.2f}MB），最大支持 {max_size_mb:.0f}MB",
            file_size=file_size
        )
    
    detected_type = _detect_file_type_by_magic_number(file_content)
    
    if detected_type is None:
        logger.warning(f"无法识别文件类型: {filename}")
        return FileValidationResult(
            is_valid=False,
            error_type=FileValidationErrorType.INVALID_CONTENT,
            error_message="无法识别文件类型，文件可能已损坏或不是有效的图片文件",
            file_size=file_size
        )
    
    if detected_type not in allowed_types:
        logger.warning(
            f"文件类型不在白名单中: {filename}, 检测类型: {detected_type}, "
            f"允许类型: {allowed_types}"
        )
        return FileValidationResult(
            is_valid=False,
            error_type=FileValidationErrorType.INVALID_TYPE,
            error_message=f"不支持的文件类型: {detected_type}，仅支持 JPG、PNG、WEBP 格式",
            detected_type=detected_type,
            file_size=file_size
        )
    
    if declared_content_type and declared_content_type != detected_type:
        logger.warning(
            f"声明的文件类型与实际类型不匹配: {filename}, "
            f"声明: {declared_content_type}, 实际: {detected_type}"
        )
    
    logger.info(
        f"文件验证通过: {filename}, 类型: {detected_type}, 大小: {file_size} bytes"
    )
    
    return FileValidationResult(
        is_valid=True,
        detected_type=detected_type,
        file_size=file_size
    )


def _detect_file_type_by_magic_number(file_content: bytes) -> Optional[str]:
    """
    通过文件头 magic number 检测文件类型
    
    读取文件的前几个字节，与已知的 magic number 进行比对，
    以确定文件的真实类型。这是一种安全措施，防止攻击者
    通过修改文件扩展名来绕过类型检查。
    
    Args:
        file_content: 文件二进制内容
    
    Returns:
        检测到的 MIME 类型字符串，如果无法识别则返回 None
    
    Note:
        - JPEG 文件有多种 magic number 变体
        - PNG 文件有固定的 8 字节 magic number
        - WebP 文件以 "RIFF" 开头，需要进一步验证
    """
    if len(file_content) < 4:
        return None
    
    for mime_type, magic_list in MAGIC_NUMBERS.items():
        for magic in magic_list:
            if file_content.startswith(magic):
                if mime_type == "image/webp":
                    if len(file_content) >= 12:
                        webp_signature = file_content[8:12]
                        if webp_signature == b"WEBP":
                            return mime_type
                    return None
                return mime_type
    
    return None


def get_file_extension(mime_type: str) -> str:
    """
    根据 MIME 类型获取文件扩展名
    
    Args:
        mime_type: MIME 类型字符串
    
    Returns:
        文件扩展名（不含点号），如果未知类型则返回 "bin"
    
    Example:
        >>> get_file_extension("image/jpeg")
        'jpg'
        >>> get_file_extension("image/png")
        'png'
    """
    return MIME_TO_EXTENSION.get(mime_type, "bin")


def is_allowed_image_type(content_type: str) -> bool:
    """
    检查内容类型是否在允许的图片类型列表中
    
    Args:
        content_type: MIME 类型字符串
    
    Returns:
        是否为允许的图片类型
    
    Example:
        >>> is_allowed_image_type("image/jpeg")
        True
        >>> is_allowed_image_type("application/pdf")
        False
    """
    return content_type in ALLOWED_MIME_TYPES
