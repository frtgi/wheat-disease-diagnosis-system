# 核心配置包
"""
核心模块

包含应用的配置、异常处理、错误码定义、日志记录等核心功能。

模块说明:
- config: 应用配置管理
- database: 数据库连接管理
- exceptions: 统一异常处理
- error_codes: 错误码定义
- error_logger: 错误日志记录
- logging_config: 日志配置
- response: API 响应格式
- security: 安全相关功能
- redis_client: Redis 客户端
- metrics: 性能指标
- startup_manager: 启动管理
- ai_config: AI 服务配置
"""

from app.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    AIServiceError,
    DatabaseError,
    DiagnosisError,
    FileUploadError,
    ErrorDetail,
    register_exception_handlers,
    raise_from_code
)

from app.core.error_codes import (
    ErrorCode,
    SystemErrorCode,
    AuthErrorCode,
    UserErrorCode,
    DiagnosisErrorCode,
    AIErrorCode,
    DatabaseErrorCode,
    FileErrorCode,
    ValidationErrorCode,
    ExternalServiceErrorCode,
    KnowledgeGraphErrorCode,
    get_error_code,
    get_error_message,
    get_http_code,
    get_error_solution,
    get_errors_by_category,
    get_all_error_codes,
    get_all_categories,
    validate_error_code,
    error_code_to_response,
    register_custom_error_code
)

from app.core.error_logger import (
    ErrorLogger,
    ErrorLogEntry,
    ErrorSeverity,
    ErrorStatistics,
    error_logger,
    email_alert_handler,
    webhook_alert_handler
)

from app.core.response import (
    ApiResponse,
    ErrorDetail as ResponseErrorDetail,
    success_response,
    error_response
)

__all__ = [
    # 异常类
    'AppException',
    'AuthenticationError',
    'AuthorizationError',
    'ValidationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitError',
    'AIServiceError',
    'DatabaseError',
    'DiagnosisError',
    'FileUploadError',
    'ErrorDetail',
    'register_exception_handlers',
    'raise_from_code',
    
    # 错误码
    'ErrorCode',
    'SystemErrorCode',
    'AuthErrorCode',
    'UserErrorCode',
    'DiagnosisErrorCode',
    'AIErrorCode',
    'DatabaseErrorCode',
    'FileErrorCode',
    'ValidationErrorCode',
    'ExternalServiceErrorCode',
    'KnowledgeGraphErrorCode',
    'get_error_code',
    'get_error_message',
    'get_http_code',
    'get_error_solution',
    'get_errors_by_category',
    'get_all_error_codes',
    'get_all_categories',
    'validate_error_code',
    'error_code_to_response',
    'register_custom_error_code',
    
    # 错误日志
    'ErrorLogger',
    'ErrorLogEntry',
    'ErrorSeverity',
    'ErrorStatistics',
    'error_logger',
    'email_alert_handler',
    'webhook_alert_handler',
    
    # 响应
    'ApiResponse',
    'ResponseErrorDetail',
    'success_response',
    'error_response'
]
