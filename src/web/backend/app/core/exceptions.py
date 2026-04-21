"""
统一异常处理模块

提供应用级别的异常类和全局异常处理器，支持统一的错误响应格式。
所有错误响应遵循格式: { success: false, error: { error_code: string, message: string, details: any } }
"""
import logging
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import (
    get_error_code
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ErrorDetail:
    """
    错误详情类

    用于封装错误响应中的错误信息，提供统一的错误详情格式。

    Attributes:
        error_code: 错误代码，如 "AUTH_001"
        code: error_code 的别名属性（向后兼容）
        message: 错误消息
        details: 错误详情，可以是任意类型
        timestamp: 错误发生时间戳
        trace_id: 请求追踪ID（可选）
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        details: Any = None,
        trace_id: Optional[str] = None
    ):
        """
        初始化错误详情

        Args:
            error_code: 错误代码
            message: 错误消息
            details: 错误详情
            trace_id: 请求追踪ID
        """
        self.error_code = error_code
        self.message = message
        self.details = details
        self.trace_id = trace_id
        self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def code(self) -> str:
        """
        获取错误代码（向后兼容别名）

        Returns:
            错误代码字符串
        """
        return self.error_code

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            包含错误信息的字典
        """
        result = {
            "error_code": self.error_code,
            "message": self.message,
        }

        if self.details is not None:
            result["details"] = self.details

        if self.trace_id:
            result["trace_id"] = self.trace_id

        result["timestamp"] = self.timestamp

        return result


class AppException(Exception):
    """
    应用异常基类

    用于业务逻辑中抛出的可预期异常，支持错误码、消息和详情。
    所有子类异常都会被统一处理器捕获并转换为标准错误响应格式。

    Attributes:
        error_code: 错误代码
        code: error_code 的别名属性（向后兼容）
        message: 错误消息
        status_code: HTTP 状态码
        details: 错误详情
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        """
        初始化应用异常

        Args:
            error_code: 错误代码，如 "AUTH_001"、"VALIDATION_002"
            message: 错误消息
            status_code: HTTP 状态码
            details: 错误详情，可以是字典、列表或任意类型
        """
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

    @property
    def code(self) -> str:
        """
        获取错误代码（向后兼容别名）

        Returns:
            错误代码字符串
        """
        return self.error_code

    def to_error_detail(self, trace_id: Optional[str] = None) -> ErrorDetail:
        """
        转换为错误详情对象

        Args:
            trace_id: 请求追踪ID

        Returns:
            ErrorDetail 对象
        """
        return ErrorDetail(
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            trace_id=trace_id
        )


class AuthenticationError(AppException):
    """
    认证错误

    用于表示用户身份验证失败的情况，如用户名密码错误、Token 无效等。
    """

    def __init__(
        self,
        message: str = "认证失败",
        error_code: str = "AUTH_001",
        details: Optional[Any] = None
    ):
        """
        初始化认证错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=401,
            details=details
        )


class AuthorizationError(AppException):
    """
    授权错误

    用于表示用户权限不足的情况。
    """

    def __init__(
        self,
        message: str = "权限不足",
        error_code: str = "AUTH_004",
        details: Optional[Any] = None
    ):
        """
        初始化授权错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=403,
            details=details
        )


class ValidationError(AppException):
    """
    验证错误

    用于表示请求数据验证失败的情况。
    """

    def __init__(
        self,
        message: str = "数据验证失败",
        error_code: str = "VALIDATION_001",
        details: Optional[Any] = None
    ):
        """
        初始化验证错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=422,
            details=details
        )


class NotFoundError(AppException):
    """
    资源不存在错误

    用于表示请求的资源不存在的情况。
    """

    def __init__(
        self,
        message: str = "资源不存在",
        error_code: str = "SYS_006",
        details: Optional[Any] = None
    ):
        """
        初始化资源不存在错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=404,
            details=details
        )


class ConflictError(AppException):
    """
    冲突错误

    用于表示资源冲突的情况，如重复创建。
    """

    def __init__(
        self,
        message: str = "资源冲突",
        error_code: str = "CONFLICT_001",
        details: Optional[Any] = None
    ):
        """
        初始化冲突错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=409,
            details=details
        )


class RateLimitError(AppException):
    """
    限流错误

    用于表示请求频率超限的情况。
    """

    def __init__(
        self,
        message: str = "请求过于频繁",
        error_code: str = "SYS_005",
        details: Optional[Any] = None
    ):
        """
        初始化限流错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=429,
            details=details
        )


class AIServiceError(AppException):
    """
    AI 服务错误
    
    用于表示 AI 模型服务相关的错误。
    """
    
    def __init__(
        self,
        message: str = "AI 服务暂时不可用",
        code: str = "AI_001",
        details: Optional[Any] = None
    ):
        """
        初始化 AI 服务错误
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=code,
            message=message,
            status_code=503,
            details=details
        )


class DatabaseError(AppException):
    """
    数据库错误

    用于表示数据库操作相关的错误。
    """

    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: str = "DB_001",
        details: Optional[Any] = None
    ):
        """
        初始化数据库错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=500,
            details=details
        )


class DiagnosisError(AppException):
    """
    诊断错误

    用于表示小麦病害诊断相关的错误。
    """

    def __init__(
        self,
        message: str = "诊断失败",
        error_code: str = "DIAG_001",
        details: Optional[Any] = None
    ):
        """
        初始化诊断错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=500,
            details=details
        )


class FileUploadError(AppException):
    """
    文件上传错误

    用于表示文件上传相关的错误。
    """

    def __init__(
        self,
        message: str = "文件上传失败",
        error_code: str = "FILE_001",
        details: Optional[Any] = None
    ):
        """
        初始化文件上传错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=400,
            details=details
        )


def _get_trace_id(request: Request) -> Optional[str]:
    """
    从请求中获取追踪ID
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        追踪ID字符串，如果不存在则返回 None
    """
    trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        try:
            from app.main import request_id_var
            if request_id_var:
                trace_id = request_id_var.get()
        except (ImportError, AttributeError):
            pass
    return trace_id


def _build_error_response(
    error_detail: ErrorDetail,
    status_code: int
) -> JSONResponse:
    """
    构建标准错误响应
    
    Args:
        error_detail: 错误详情对象
        status_code: HTTP 状态码
        
    Returns:
        JSONResponse 对象
    """
    response = JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error_detail.to_dict()
        }
    )
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    应用异常处理器
    
    处理 AppException 及其子类异常，返回统一的错误响应格式。
    
    Args:
        request: FastAPI 请求对象
        exc: 应用异常实例
        
    Returns:
        标准格式的错误响应
    """
    trace_id = _get_trace_id(request)
    
    _log_error(
        request=request,
        error_code=exc.error_code,
        error_message=exc.message,
        details=exc.details,
        trace_id=trace_id,
        level="error"
    )
    
    error_detail = exc.to_error_detail(trace_id)
    return _build_error_response(error_detail, exc.status_code)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 异常处理器
    
    处理 FastAPI HTTPException 异常，转换为统一的错误响应格式。
    
    Args:
        request: FastAPI 请求对象
        exc: HTTP 异常实例
        
    Returns:
        标准格式的错误响应
    """
    trace_id = _get_trace_id(request)
    
    error_code = f"HTTP_{exc.status_code}"
    error_message = str(exc.detail) if exc.detail else "请求处理失败"
    
    _log_error(
        request=request,
        error_code=error_code,
        error_message=error_message,
        details=None,
        trace_id=trace_id,
        level="warning"
    )
    
    error_detail = ErrorDetail(
        error_code=error_code,
        message=error_message,
        details=None,
        trace_id=trace_id
    )

    return _build_error_response(error_detail, exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    
    处理 Pydantic 验证错误，转换为统一的错误响应格式。
    
    Args:
        request: FastAPI 请求对象
        exc: 请求验证异常实例
        
    Returns:
        标准格式的错误响应
    """
    trace_id = _get_trace_id(request)
    
    errors = exc.errors()
    formatted_errors = _format_validation_errors(errors)
    
    _log_error(
        request=request,
        error_code="VALIDATION_001",
        error_message="请求参数验证失败",
        details=formatted_errors,
        trace_id=trace_id,
        level="warning"
    )
    
    error_detail = ErrorDetail(
        error_code="VALIDATION_001",
        message="请求参数验证失败",
        details=formatted_errors,
        trace_id=trace_id
    )

    return _build_error_response(error_detail, 422)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    
    捕获所有未处理的异常，返回统一的错误响应格式。
    记录详细的错误日志用于调试。
    
    Args:
        request: FastAPI 请求对象
        exc: 异常实例
        
    Returns:
        标准格式的错误响应
    """
    trace_id = _get_trace_id(request)
    
    _log_error(
        request=request,
        error_code="SYS_001",
        error_message=str(exc),
        details={
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc() if getattr(settings, 'DEBUG', False) else None
        },
        trace_id=trace_id,
        level="critical"
    )
    
    error_detail = ErrorDetail(
        error_code="SYS_001",
        message="服务器内部错误，请稍后重试",
        details={"trace_id": trace_id} if trace_id else None,
        trace_id=trace_id
    )

    return _build_error_response(error_detail, 500)


def _format_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    格式化验证错误列表
    
    将 Pydantic 验证错误转换为更友好的格式。
    
    Args:
        errors: Pydantic 验证错误列表
        
    Returns:
        格式化后的错误列表
    """
    formatted = []
    for error in errors:
        loc = error.get("loc", [])
        field = ".".join(str(x) for x in loc if x)
        
        formatted.append({
            "field": field,
            "message": error.get("msg", "验证失败"),
            "type": error.get("type", "validation_error"),
            "input": error.get("input")
        })
    return formatted


def _log_error(
    request: Request,
    error_code: str,
    error_message: str,
    details: Any,
    trace_id: Optional[str],
    level: str = "error"
) -> None:
    """
    记录错误日志
    
    将错误信息记录到日志系统，包含请求上下文信息。
    
    Args:
        request: FastAPI 请求对象
        error_code: 错误代码
        error_message: 错误消息
        details: 错误详情
        trace_id: 追踪ID
        level: 日志级别
    """
    log_data = {
        "error_code": error_code,
        "error_message": error_message,
        "path": request.url.path,
        "method": request.method,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "trace_id": trace_id,
        "details": details
    }
    
    log_method = getattr(logger, level, logger.error)
    log_method(f"[{error_code}] {error_message}", extra=log_data)


def register_exception_handlers(app):
    """
    注册异常处理器到 FastAPI 应用
    
    将所有异常处理器注册到 FastAPI 应用实例中，
    确保所有异常都能被统一处理并返回标准格式。
    
    Args:
        app: FastAPI 应用实例
        
    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    
    logger.info("异常处理器注册完成，统一错误响应格式已启用")


def raise_from_code(code: str, details: Optional[Any] = None) -> None:
    """
    根据错误码抛出对应的异常
    
    根据错误码自动选择合适的异常类型并抛出。
    
    Args:
        code: 错误代码
        details: 错误详情
        
    Raises:
        对应的 AppException 子类异常
        
    Example:
        >>> raise_from_code("AUTH_001", {"reason": "密码错误"})
    """
    error_info = get_error_code(code)
    
    if not error_info:
        raise AppException(
            error_code=code,
            message="未知错误",
            status_code=500,
            details=details
        )

    message = error_info.message
    http_code = error_info.http_code

    if code.startswith("AUTH_"):
        if "权限" in message or "禁用" in message:
            raise AuthorizationError(message=message, error_code=code, details=details)
        raise AuthenticationError(message=message, error_code=code, details=details)

    if code.startswith("USER_"):
        if "不存在" in message:
            raise NotFoundError(message=message, error_code=code, details=details)
        if "已存在" in message or "已注册" in message:
            raise ConflictError(message=message, error_code=code, details=details)
        raise AppException(error_code=code, message=message, status_code=http_code, details=details)

    if code.startswith("DIAG_"):
        raise DiagnosisError(message=message, error_code=code, details=details)

    if code.startswith("AI_"):
        raise AIServiceError(message=message, error_code=code, details=details)

    if code.startswith("DB_"):
        raise DatabaseError(message=message, error_code=code, details=details)

    if code.startswith("SYS_"):
        if "不存在" in message:
            raise NotFoundError(message=message, error_code=code, details=details)
        if "频率" in message or "超限" in message:
            raise RateLimitError(message=message, error_code=code, details=details)

    raise AppException(error_code=code, message=message, status_code=http_code, details=details)
