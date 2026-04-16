"""
统一 API 响应格式模块
提供标准化的 API 响应格式，包括成功响应和错误响应
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    错误详情模型

    用于封装错误响应中的错误信息
    """
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详细信息")


class ApiResponse(BaseModel):
    """
    统一 API 响应模型
    
    提供标准化的 API 响应格式，支持成功和错误两种响应类型
    """
    success: bool = Field(..., description="请求是否成功")
    code: int = Field(..., description="HTTP 状态码")
    message: Optional[str] = Field(None, description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error: Optional[ErrorDetail] = Field(None, description="错误详情")
    timestamp: str = Field(..., description="响应时间戳")


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: str = "操作成功",
    code: int = 200
) -> Dict[str, Any]:
    """
    生成成功响应
    
    创建一个标准化的成功响应格式，包含成功状态、状态码、消息、数据和时间戳。
    
    参数:
        data: 响应数据，默认为空字典
        message: 响应消息，默认为 "操作成功"
        code: HTTP 状态码，默认为 200
    
    返回:
        标准化的成功响应字典，格式如下：
        {
            "success": true,
            "code": 200,
            "message": "操作成功",
            "data": { ... },
            "timestamp": "2026-03-13T12:00:00Z"
        }
    
    示例:
        >>> response = success_response({"user_id": 1, "name": "张三"})
        >>> print(response)
        {
            "success": true,
            "code": 200,
            "message": "操作成功",
            "data": {"user_id": 1, "name": "张三"},
            "timestamp": "2026-03-13T12:00:00Z"
        }
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "success": True,
        "code": code,
        "message": message,
        "data": data if data is not None else {},
        "timestamp": timestamp
    }


def error_response(
    error_code: str,
    message: str,
    detail: Optional[str] = None,
    http_code: int = 400
) -> Dict[str, Any]:
    """
    生成错误响应
    
    创建一个标准化的错误响应格式，包含错误状态、HTTP状态码、错误详情和时间戳。
    
    参数:
        error_code: 错误代码，如 "AUTH_001"、"VALIDATION_002" 等
        message: 错误消息，简要描述错误类型
        detail: 错误详细信息，提供更多上下文，默认为 None
        http_code: HTTP 状态码，默认为 400
    
    返回:
        标准化的错误响应字典，格式如下：
        {
            "success": false,
            "code": 400,
            "error": {
                "error_code": "AUTH_001",
                "message": "用户名或密码错误",
                "detail": "请检查用户名和密码是否正确"
            },
            "timestamp": "2026-03-13T12:00:00Z"
        }

    示例:
        >>> response = error_response(
        ...     error_code="AUTH_001",
        ...     message="用户名或密码错误",
        ...     detail="请检查用户名和密码是否正确"
        ... )
        >>> print(response)
        {
            "success": false,
            "code": 400,
            "error": {
                "error_code": "AUTH_001",
                "message": "用户名或密码错误",
                "detail": "请检查用户名和密码是否正确"
            },
            "timestamp": "2026-03-13T12:00:00Z"
        }
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    error_info = {
        "error_code": error_code,
        "message": message
    }
    
    if detail is not None:
        error_info["detail"] = detail
    
    return {
        "success": False,
        "code": http_code,
        "error": error_info,
        "timestamp": timestamp
    }
