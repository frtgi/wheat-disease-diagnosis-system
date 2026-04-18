"""
文件上传 API 路由
处理图像文件上传功能
"""
import os
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from typing import Optional

from app.utils.file_validator import validate_upload_file, get_file_extension
from app.core.security import get_current_user, verify_token
from app.rate_limiter import limiter
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["文件上传"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "diagnosis"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/image")
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(..., description="上传的图像文件"),
    current_user: User = Depends(get_current_user)
):
    """
    上传图像文件（需认证）
    
    参数:
        request: FastAPI 请求对象（用于限流）
        file: 上传的图像文件（JPG/PNG/WEBP 格式，最大 10MB）
        current_user: 当前认证用户（通过 JWT 令牌验证）
        
    返回:
        dict: 包含上传成功的文件 URL
            - success: 是否成功
            - url: 文件访问 URL
            - filename: 保存的文件名
    
    安全验证:
        - 用户身份认证（JWT 令牌验证）
        - 频率限制（每分钟最多 10 次）
        - 用户状态检查（账号是否被禁用）
        - 文件类型白名单验证（仅允许 JPG、PNG、WEBP）
        - 文件大小限制（最大 10MB）
        - 文件内容安全检查（magic number 验证）
    """
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    
    try:
        content = await file.read()
        
        validation_result = validate_upload_file(
            file_content=content,
            filename=file.filename,
            declared_content_type=file.content_type
        )
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=validation_result.error_message
            )
        
        file_extension = get_file_extension(validation_result.detected_type)
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_url = f"/uploads/diagnosis/{filename}"
        
        logger.info(
            f"文件上传成功: {filename}, 类型: {validation_result.detected_type}, "
            f"大小: {validation_result.file_size} bytes, "
            f"上传者: {current_user.username}(ID:{current_user.id})"
        )
        
        return {
            "success": True,
            "url": file_url,
            "filename": filename,
            "size": validation_result.file_size,
            "content_type": validation_result.detected_type,
            "message": "文件上传成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="文件上传失败，请稍后重试")
