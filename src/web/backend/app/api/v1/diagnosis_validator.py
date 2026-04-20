"""
请求验证与预处理模块
提供诊断请求的完整验证流程，包括：
- 文件验证（大小、格式、Magic Number 检查）
- AI 服务可用性检查
- GPU 显存检查
- 并发限流获取/释放
- 图像预处理
- 缓存管理
"""
import logging
import os
from typing import Optional, Tuple, Any, Dict
from PIL import Image
import io

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

_cache_manager = None
_cache_available = False

try:
    from app.services.cache_manager import get_cache_manager as _get_cache_manager
    _cache_available = True
except ImportError as e:
    logger.warning(f"缓存管理器不可用：{e}，将禁用缓存功能")
    _cache_available = False


def validate_image(
    image_bytes: bytes,
    filename: str = "unknown"
) -> Tuple[bool, Optional[str]]:
    """
    验证图像文件的大小和格式

    执行以下检查：
    1. 文件大小限制（最大 10MB）
    2. 图像格式支持性（JPEG/PNG/WEBP）
    3. 文件完整性（能否被 PIL 解析）

    参数:
        image_bytes: 图像的字节数据
        filename: 文件名（用于错误提示）

    返回:
        Tuple[bool, Optional[str]]: (是否有效, 错误消息)
            - (True, None): 验证通过
            - (False, error_msg): 验证失败及原因
    """
    if len(image_bytes) > MAX_IMAGE_SIZE:
        size_mb = len(image_bytes) / (1024 * 1024)
        return False, f"图像文件过大（{size_mb:.2f}MB），最大支持 10MB，请压缩后重试"

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_format = img.format
        if img_format and img_format.upper() not in ALLOWED_IMAGE_FORMATS:
            return False, f"不支持的图像格式：{img_format}，仅支持 JPEG、PNG、WEBP 格式"
        return True, None
    except Exception as e:
        return False, f"无法解析图像文件：{str(e)}，请确保上传的是有效的图像文件"


def check_image_magic_number(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    检查图像文件的 Magic Number（文件头标识）

    通过检查文件头字节来识别真实的文件类型，
    防止恶意文件伪装扩展名。

    支持的格式：
    - JPEG: FF D8 FF
    - PNG: 89 50 4E 47 0D 0A 1A 0A
    - WEBP: 52 49 46 46 (RIFF)

    参数:
        image_bytes: 图像字节数据（至少前 12 字节）

    返回:
        Tuple[bool, Optional[str]]: (是否合法, 错误消息)
    """
    if len(image_bytes) < 12:
        return False, "文件太小，无法读取文件头信息"

    header = image_bytes[:12]

    if header[:3] == b'\xff\xd8\xff':
        return True, None  # JPEG
    elif header[:8] == b'\x89PNG\r\n\x1a\n':
        return True, None  # PNG
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return True, None  # WEBP
    else:
        return False, "不支持的图像文件格式或文件已损坏"


def ensure_ai_service_ready():
    """
    检查 AI 诊断服务是否已加载并可用

    在诊断请求处理前调用，确保 Qwen 服务已加载。
    如果服务未加载，抛出 HTTPException(503)。

    异常:
        HTTPException: AI 服务未加载时抛出 503
    """
    from fastapi import HTTPException
    try:
        from app.services.qwen_service import get_qwen_service
        service = get_qwen_service()
        if not service.is_loaded:
            raise HTTPException(
                status_code=503,
                detail="AI 诊断服务尚未加载，请稍后重试或联系管理员"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI 诊断服务不可用: {str(e)}"
        )


def get_cache_manager_safe() -> Optional[Any]:
    """
    安全获取缓存管理器实例

    在缓存服务不可用时优雅降级，返回 None 而不是抛出异常。

    返回:
        cache_manager 或 None: 缓存可用则返回管理器实例，否则返回 None
    """
    if not _cache_available:
        return None
    try:
        return _get_cache_manager()
    except Exception as e:
        logger.warning(f"获取缓存管理器失败：{e}")
        return None


def check_gpu_memory(required_memory_mb: float = 1024.0) -> Tuple[bool, Optional[str]]:
    """
    检查 GPU 显存是否满足要求

    用于在执行 GPU 密集型任务前验证资源可用性。

    参数:
        required_memory_mb: 所需显存（MB），默认 1024MB

    返回:
        Tuple[bool, Optional[str]]: (是否可用, 错误消息)
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return False, "GPU 不可用"

        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
        free_memory = torch.cuda.mem_get_info(0)[0] / (1024 * 1024)

        if free_memory < required_memory_mb:
            return False, f"GPU 显存不足：需要 {required_memory_mb:.0f}MB，可用 {free_memory:.0f}MB"

        logger.info(f"GPU 显存检查通过：总 {total_memory:.0f}MB，可用 {free_memory:.0f}MB")
        return True, None

    except ImportError:
        logger.warning("PyTorch 未安装，跳过 GPU 显存检查")
        return True, None
    except Exception as e:
        logger.error(f"GPU 显存检查异常: {e}")
        return False, f"GPU 检查失败: {str(e)}"


async def acquire_rate_limit(resource_type: str = "diagnosis") -> bool:
    """
    获取并发限流许可

    用于控制同时进行的诊断任务数量，防止系统过载。

    参数:
        resource_type: 资源类型（如 diagnosis, batch 等），默认 "diagnosis"

    返回:
        bool: 是否成功获取许可
    """
    try:
        from app.core.rate_limiter import RateLimiter
        limiter = RateLimiter()
        acquired = await limiter.acquire(resource_type)
        if acquired:
            logger.debug(f"成功获取限流许可: {resource_type}")
        else:
            logger.warning(f"限流拒绝请求: {resource_type}（达到并发上限）")
        return acquired
    except ImportError:
        logger.debug("限流器未安装，允许所有请求")
        return True
    except Exception as e:
        logger.warning(f"限流器异常: {e}，允许请求继续")
        return True


async def release_rate_limit(resource_type: str = "diagnosis") -> None:
    """
    释放并发限流许可

    任务完成后必须调用此函数释放资源。

    参数:
        resource_type: 资源类型
    """
    try:
        from app.core.rate_limiter import RateLimiter
        limiter = RateLimiter()
        await limiter.release(resource_type)
        logger.debug(f"已释放限流许可: {resource_type}")
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"释放限流许可异常: {e}")


def preprocess_image(
    image_bytes: bytes,
    target_size: Optional[Tuple[int, int]] = None,
    normalize: bool = True
) -> Tuple[Image.Image, bytes]:
    """
    图像预处理函数

    对上传的图像进行标准化处理：
    1. 打开并转换为 RGB 格式
    2. 可选的尺寸调整
    3. 可选的像素值归一化准备

    参数:
        image_bytes: 原始图像字节数据
        target_size: 目标尺寸 (width, height)，可选
        normalize: 是否进行归一化处理标记

    返回:
        Tuple[PIL.Image.Image, bytes]: (处理后图像对象, 处理后字节)

    异常:
        ValueError: 图像无法解析时抛出
    """
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode != 'RGB':
        img = img.convert('RGB')

    if target_size:
        img = img.resize(target_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    processed_bytes = buffer.getvalue()

    logger.info(f"图像预处理完成：尺寸={img.size}, 大小={len(processed_bytes)/1024:.2f}KB")
    return img, processed_bytes


class DiagnosisRequestValidator:
    """
    诊断请求验证器类
    封装完整的请求验证流程，提供统一的验证接口
    """

    def __init__(
        self,
        enable_gpu_check: bool = False,
        enable_rate_limit: bool = True,
        enable_cache: bool = True
    ) -> None:
        """
        初始化请求验证器

        参数:
            enable_gpu_check: 是否启用 GPU 显存检查
            enable_rate_limit: 是否启用并发限流
            enable_cache: 是否启用缓存功能
        """
        self.enable_gpu_check = enable_gpu_check
        self.enable_rate_limit = enable_rate_limit
        self.enable_cache = enable_cache
        self._rate_limit_acquired = False

    async def validate_image_upload(
        self,
        image_bytes: bytes,
        filename: str = "unknown"
    ) -> Tuple[bool, Optional[str]]:
        """
        验证上传的图像文件

        完整的图像验证流程：大小 + 格式 + Magic Number

        参数:
            image_bytes: 图像字节数据
            filename: 文件名

        返回:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        is_valid, error_msg = validate_image(image_bytes, filename)
        if not is_valid:
            return False, error_msg

        magic_ok, magic_error = check_image_magic_number(image_bytes)
        if not magic_ok:
            return False, magic_error

        return True, None

    async def validate_request_context(
        self,
        has_image: bool,
        has_symptoms: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        验证请求上下文完整性

        确保至少提供了图像或症状描述中的一种输入。

        参数:
            has_image: 是否有图像输入
            has_symptoms: 是否有症状描述

        返回:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        if not has_image and not has_symptoms:
            return False, "请至少提供图像或症状描述中的一种输入"
        return True, None

    async def preflight_checks(self) -> Tuple[bool, Optional[str]]:
        """
        执行预检检查（GPU + 限流）

        在实际执行诊断前进行资源检查和限流控制。

        返回:
            Tuple[bool, Optional[str]]: (是否通过, 错误消息)
        """
        if self.enable_gpu_check:
            gpu_ok, gpu_error = check_gpu_memory()
            if not gpu_ok:
                return False, gpu_error

        if self.enable_rate_limit:
            acquired = await acquire_rate_limit()
            if not acquired:
                return False, "服务器繁忙，请稍后重试"
            self._rate_limit_acquired = True

        return True, None

    async def cleanup(self) -> None:
        """
        清理资源（释放限流许可等）

        必须在请求处理完成后调用，即使发生异常也要确保清理。
        """
        if self._rate_limit_acquired:
            await release_rate_limit()
            self._rate_limit_acquired = False
