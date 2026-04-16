"""
错误码定义模块

定义了系统统一的错误码体系，包含错误码类和各类错误码枚举。
所有错误码遵循命名规范：模块前缀_三位数字，如 AUTH_001、DIAG_002 等。

错误码分类：
- SYS: 系统级错误
- AUTH: 认证授权错误
- USER: 用户相关错误
- DIAG: 诊断相关错误
- AI: AI 服务错误
- DB: 数据库错误
- FILE: 文件操作错误
- VALIDATION: 验证错误
- EXTERNAL: 外部服务错误
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Callable, Any


@dataclass
class ErrorCode:
    """
    错误码数据类
    
    用于封装单个错误码的完整信息。
    
    Attributes:
        code: 错误码字符串，如 "AUTH_001"
        message: 错误消息描述
        http_code: 对应的 HTTP 状态码
        category: 错误类别（可选）
        solution: 解决方案建议（可选）
    """
    code: str
    message: str
    http_code: int
    category: Optional[str] = None
    solution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            包含错误码信息的字典
        """
        result = {
            "error_code": self.code,
            "message": self.message,
            "http_code": self.http_code
        }
        if self.category:
            result["category"] = self.category
        if self.solution:
            result["solution"] = self.solution
        return result


class SystemErrorCode(Enum):
    """
    系统级错误码枚举
    
    用于表示系统层面的错误，如内部错误、服务不可用等。
    HTTP 状态码范围：500-599
    """
    
    SYS_001 = ErrorCode(
        code="SYS_001",
        message="系统内部错误",
        http_code=500,
        category="system",
        solution="请稍后重试，如问题持续请联系技术支持"
    )
    SYS_002 = ErrorCode(
        code="SYS_002",
        message="服务不可用",
        http_code=503,
        category="system",
        solution="服务正在维护中，请稍后重试"
    )
    SYS_003 = ErrorCode(
        code="SYS_003",
        message="请求参数错误",
        http_code=400,
        category="system",
        solution="请检查请求参数格式是否正确"
    )
    SYS_004 = ErrorCode(
        code="SYS_004",
        message="请求方法不允许",
        http_code=405,
        category="system",
        solution="请使用正确的 HTTP 方法"
    )
    SYS_005 = ErrorCode(
        code="SYS_005",
        message="请求频率超限",
        http_code=429,
        category="system",
        solution="请降低请求频率，稍后重试"
    )
    SYS_006 = ErrorCode(
        code="SYS_006",
        message="资源不存在",
        http_code=404,
        category="system",
        solution="请检查请求的资源路径是否正确"
    )
    SYS_007 = ErrorCode(
        code="SYS_007",
        message="服务超时",
        http_code=504,
        category="system",
        solution="请求处理超时，请稍后重试"
    )
    SYS_008 = ErrorCode(
        code="SYS_008",
        message="功能暂未开放",
        http_code=403,
        category="system",
        solution="该功能正在开发中，敬请期待"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class AuthErrorCode(Enum):
    """
    认证相关错误码枚举
    
    用于表示用户认证、授权相关的错误。
    HTTP 状态码范围：401、403
    """
    
    AUTH_001 = ErrorCode(
        code="AUTH_001",
        message="用户名或密码错误",
        http_code=401,
        category="auth",
        solution="请检查用户名和密码是否正确"
    )
    AUTH_002 = ErrorCode(
        code="AUTH_002",
        message="Token 无效或过期",
        http_code=401,
        category="auth",
        solution="请重新登录获取新的 Token"
    )
    AUTH_003 = ErrorCode(
        code="AUTH_003",
        message="账号已被禁用",
        http_code=403,
        category="auth",
        solution="请联系管理员解除禁用"
    )
    AUTH_004 = ErrorCode(
        code="AUTH_004",
        message="权限不足",
        http_code=403,
        category="auth",
        solution="您没有权限执行此操作"
    )
    AUTH_005 = ErrorCode(
        code="AUTH_005",
        message="登录已过期，请重新登录",
        http_code=401,
        category="auth",
        solution="请重新登录"
    )
    AUTH_006 = ErrorCode(
        code="AUTH_006",
        message="验证码错误",
        http_code=400,
        category="auth",
        solution="请输入正确的验证码"
    )
    AUTH_007 = ErrorCode(
        code="AUTH_007",
        message="验证码已过期",
        http_code=400,
        category="auth",
        solution="请重新获取验证码"
    )
    AUTH_008 = ErrorCode(
        code="AUTH_008",
        message="账号未激活",
        http_code=403,
        category="auth",
        solution="请先激活账号"
    )
    AUTH_009 = ErrorCode(
        code="AUTH_009",
        message="登录失败次数过多",
        http_code=403,
        category="auth",
        solution="账号已被临时锁定，请稍后重试或联系管理员"
    )
    AUTH_010 = ErrorCode(
        code="AUTH_010",
        message="密码强度不足",
        http_code=400,
        category="auth",
        solution="密码需包含字母、数字，长度至少8位"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class UserErrorCode(Enum):
    """
    用户相关错误码枚举
    
    用于表示用户管理相关的错误。
    HTTP 状态码范围：400、404、409
    """
    
    USER_001 = ErrorCode(
        code="USER_001",
        message="用户已存在",
        http_code=409,
        category="user",
        solution="请使用其他用户名注册"
    )
    USER_002 = ErrorCode(
        code="USER_002",
        message="邮箱已注册",
        http_code=409,
        category="user",
        solution="请使用其他邮箱或直接登录"
    )
    USER_003 = ErrorCode(
        code="USER_003",
        message="用户不存在",
        http_code=404,
        category="user",
        solution="请检查用户名是否正确"
    )
    USER_004 = ErrorCode(
        code="USER_004",
        message="密码修改失败",
        http_code=400,
        category="user",
        solution="请确保新密码符合要求"
    )
    USER_005 = ErrorCode(
        code="USER_005",
        message="用户信息更新失败",
        http_code=500,
        category="user",
        solution="请稍后重试"
    )
    USER_006 = ErrorCode(
        code="USER_006",
        message="手机号已注册",
        http_code=409,
        category="user",
        solution="请使用其他手机号"
    )
    USER_007 = ErrorCode(
        code="USER_007",
        message="原密码错误",
        http_code=400,
        category="user",
        solution="请输入正确的原密码"
    )
    USER_008 = ErrorCode(
        code="USER_008",
        message="用户头像上传失败",
        http_code=500,
        category="user",
        solution="请检查图片格式和大小"
    )
    USER_009 = ErrorCode(
        code="USER_009",
        message="用户资料不完整",
        http_code=400,
        category="user",
        solution="请完善用户资料"
    )
    USER_010 = ErrorCode(
        code="USER_010",
        message="账号注销失败",
        http_code=500,
        category="user",
        solution="请联系客服处理"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class DiagnosisErrorCode(Enum):
    """
    诊断相关错误码枚举
    
    用于表示小麦病害诊断相关的错误。
    HTTP 状态码范围：400、404、500、504
    """
    
    DIAG_001 = ErrorCode(
        code="DIAG_001",
        message="诊断失败",
        http_code=500,
        category="diagnosis",
        solution="请稍后重试，如问题持续请联系技术支持"
    )
    DIAG_002 = ErrorCode(
        code="DIAG_002",
        message="图像上传失败",
        http_code=400,
        category="diagnosis",
        solution="请检查图像文件是否有效"
    )
    DIAG_003 = ErrorCode(
        code="DIAG_003",
        message="图像格式不支持",
        http_code=400,
        category="diagnosis",
        solution="支持的格式：JPG、PNG、WEBP"
    )
    DIAG_004 = ErrorCode(
        code="DIAG_004",
        message="图像大小超限",
        http_code=400,
        category="diagnosis",
        solution="图像大小不能超过 10MB"
    )
    DIAG_005 = ErrorCode(
        code="DIAG_005",
        message="诊断记录不存在",
        http_code=404,
        category="diagnosis",
        solution="请检查诊断记录 ID 是否正确"
    )
    DIAG_006 = ErrorCode(
        code="DIAG_006",
        message="图像解析失败",
        http_code=400,
        category="diagnosis",
        solution="请上传有效的图像文件"
    )
    DIAG_007 = ErrorCode(
        code="DIAG_007",
        message="诊断任务超时",
        http_code=504,
        category="diagnosis",
        solution="诊断处理时间过长，请稍后查看结果"
    )
    DIAG_008 = ErrorCode(
        code="DIAG_008",
        message="诊断结果保存失败",
        http_code=500,
        category="diagnosis",
        solution="请稍后重试"
    )
    DIAG_009 = ErrorCode(
        code="DIAG_009",
        message="图像质量不足",
        http_code=400,
        category="diagnosis",
        solution="请上传清晰度更高的图像"
    )
    DIAG_010 = ErrorCode(
        code="DIAG_010",
        message="未检测到病害区域",
        http_code=400,
        category="diagnosis",
        solution="请确保图像中包含病害区域"
    )
    DIAG_011 = ErrorCode(
        code="DIAG_011",
        message="批量诊断数量超限",
        http_code=400,
        category="diagnosis",
        solution="单次最多支持 20 张图像"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class AIErrorCode(Enum):
    """
    AI 服务错误码枚举
    
    用于表示 AI 模型服务相关的错误。
    HTTP 状态码范围：404、500、503、504
    """
    
    AI_001 = ErrorCode(
        code="AI_001",
        message="AI 服务不可用",
        http_code=503,
        category="ai",
        solution="AI 服务正在启动或维护中，请稍后重试"
    )
    AI_002 = ErrorCode(
        code="AI_002",
        message="模型加载失败",
        http_code=500,
        category="ai",
        solution="请联系技术支持"
    )
    AI_003 = ErrorCode(
        code="AI_003",
        message="模型推理失败",
        http_code=500,
        category="ai",
        solution="请稍后重试"
    )
    AI_004 = ErrorCode(
        code="AI_004",
        message="模型不存在",
        http_code=404,
        category="ai",
        solution="请检查模型名称是否正确"
    )
    AI_005 = ErrorCode(
        code="AI_005",
        message="模型版本不匹配",
        http_code=400,
        category="ai",
        solution="请更新到最新版本"
    )
    AI_006 = ErrorCode(
        code="AI_006",
        message="AI 服务超时",
        http_code=504,
        category="ai",
        solution="推理时间过长，请稍后重试"
    )
    AI_007 = ErrorCode(
        code="AI_007",
        message="模型配置错误",
        http_code=500,
        category="ai",
        solution="请联系技术支持"
    )
    AI_008 = ErrorCode(
        code="AI_008",
        message="GPU 内存不足",
        http_code=503,
        category="ai",
        solution="服务器资源紧张，请稍后重试"
    )
    AI_009 = ErrorCode(
        code="AI_009",
        message="多模态融合失败",
        http_code=500,
        category="ai",
        solution="请稍后重试"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class DatabaseErrorCode(Enum):
    """
    数据库错误码枚举
    
    用于表示数据库操作相关的错误。
    HTTP 状态码范围：500、504
    """
    
    DB_001 = ErrorCode(
        code="DB_001",
        message="数据库连接失败",
        http_code=500,
        category="database",
        solution="请稍后重试"
    )
    DB_002 = ErrorCode(
        code="DB_002",
        message="数据库查询错误",
        http_code=500,
        category="database",
        solution="请稍后重试"
    )
    DB_003 = ErrorCode(
        code="DB_003",
        message="数据插入失败",
        http_code=500,
        category="database",
        solution="请检查数据格式后重试"
    )
    DB_004 = ErrorCode(
        code="DB_004",
        message="数据更新失败",
        http_code=500,
        category="database",
        solution="请稍后重试"
    )
    DB_005 = ErrorCode(
        code="DB_005",
        message="数据删除失败",
        http_code=500,
        category="database",
        solution="请稍后重试"
    )
    DB_006 = ErrorCode(
        code="DB_006",
        message="数据已存在",
        http_code=409,
        category="database",
        solution="数据重复，请检查后重试"
    )
    DB_007 = ErrorCode(
        code="DB_007",
        message="事务提交失败",
        http_code=500,
        category="database",
        solution="请稍后重试"
    )
    DB_008 = ErrorCode(
        code="DB_008",
        message="数据库超时",
        http_code=504,
        category="database",
        solution="数据库响应超时，请稍后重试"
    )
    DB_009 = ErrorCode(
        code="DB_009",
        message="数据外键约束错误",
        http_code=400,
        category="database",
        solution="关联数据不存在或无法删除"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class FileErrorCode(Enum):
    """
    文件操作错误码枚举
    
    用于表示文件上传、下载、处理相关的错误。
    HTTP 状态码范围：400、404、413、500
    """
    
    FILE_001 = ErrorCode(
        code="FILE_001",
        message="文件上传失败",
        http_code=500,
        category="file",
        solution="请稍后重试"
    )
    FILE_002 = ErrorCode(
        code="FILE_002",
        message="文件类型不支持",
        http_code=400,
        category="file",
        solution="请上传支持的文件类型"
    )
    FILE_003 = ErrorCode(
        code="FILE_003",
        message="文件大小超限",
        http_code=413,
        category="file",
        solution="文件大小超过限制"
    )
    FILE_004 = ErrorCode(
        code="FILE_004",
        message="文件不存在",
        http_code=404,
        category="file",
        solution="请检查文件路径是否正确"
    )
    FILE_005 = ErrorCode(
        code="FILE_005",
        message="文件读取失败",
        http_code=500,
        category="file",
        solution="文件可能已损坏，请重新上传"
    )
    FILE_006 = ErrorCode(
        code="FILE_006",
        message="文件删除失败",
        http_code=500,
        category="file",
        solution="请稍后重试"
    )
    FILE_007 = ErrorCode(
        code="FILE_007",
        message="文件名非法",
        http_code=400,
        category="file",
        solution="文件名包含非法字符"
    )
    FILE_008 = ErrorCode(
        code="FILE_008",
        message="存储空间不足",
        http_code=507,
        category="file",
        solution="服务器存储空间不足，请联系管理员"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class ValidationErrorCode(Enum):
    """
    验证错误码枚举
    
    用于表示数据验证相关的错误。
    HTTP 状态码范围：422
    """
    
    VALIDATION_001 = ErrorCode(
        code="VALIDATION_001",
        message="请求参数验证失败",
        http_code=422,
        category="validation",
        solution="请检查请求参数格式"
    )
    VALIDATION_002 = ErrorCode(
        code="VALIDATION_002",
        message="必填字段缺失",
        http_code=422,
        category="validation",
        solution="请填写所有必填字段"
    )
    VALIDATION_003 = ErrorCode(
        code="VALIDATION_003",
        message="字段格式错误",
        http_code=422,
        category="validation",
        solution="请检查字段格式是否正确"
    )
    VALIDATION_004 = ErrorCode(
        code="VALIDATION_004",
        message="字段长度超限",
        http_code=422,
        category="validation",
        solution="请缩短字段内容"
    )
    VALIDATION_005 = ErrorCode(
        code="VALIDATION_005",
        message="字段值不在允许范围内",
        http_code=422,
        category="validation",
        solution="请使用有效的字段值"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class ExternalServiceErrorCode(Enum):
    """
    外部服务错误码枚举
    
    用于表示第三方服务调用相关的错误。
    HTTP 状态码范围：502、503
    """
    
    EXT_001 = ErrorCode(
        code="EXT_001",
        message="外部服务不可用",
        http_code=503,
        category="external",
        solution="第三方服务暂时不可用，请稍后重试"
    )
    EXT_002 = ErrorCode(
        code="EXT_002",
        message="外部服务超时",
        http_code=504,
        category="external",
        solution="外部服务响应超时，请稍后重试"
    )
    EXT_003 = ErrorCode(
        code="EXT_003",
        message="外部服务返回错误",
        http_code=502,
        category="external",
        solution="外部服务异常，请稍后重试"
    )
    EXT_004 = ErrorCode(
        code="EXT_004",
        message="API 密钥无效",
        http_code=500,
        category="external",
        solution="请联系管理员"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


class KnowledgeGraphErrorCode(Enum):
    """
    知识图谱错误码枚举
    
    用于表示知识图谱相关操作的错误。
    HTTP 状态码范围：400、404、500
    """
    
    KG_001 = ErrorCode(
        code="KG_001",
        message="知识图谱查询失败",
        http_code=500,
        category="knowledge_graph",
        solution="请稍后重试"
    )
    KG_002 = ErrorCode(
        code="KG_002",
        message="实体不存在",
        http_code=404,
        category="knowledge_graph",
        solution="未找到相关实体信息"
    )
    KG_003 = ErrorCode(
        code="KG_003",
        message="关系不存在",
        http_code=404,
        category="knowledge_graph",
        solution="未找到相关关系信息"
    )
    KG_004 = ErrorCode(
        code="KG_004",
        message="知识图谱连接失败",
        http_code=500,
        category="knowledge_graph",
        solution="知识图谱服务不可用，请稍后重试"
    )
    KG_005 = ErrorCode(
        code="KG_005",
        message="图谱数据导入失败",
        http_code=500,
        category="knowledge_graph",
        solution="请检查数据格式后重试"
    )
    
    @property
    def error(self) -> ErrorCode:
        """获取错误码对象"""
        return self.value


_ERROR_CODE_MAP: Dict[str, ErrorCode] = {}

_CATEGORY_MAP: Dict[str, List[str]] = {}

_ERROR_CODE_ENUMS = [
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
]

for enum_class in _ERROR_CODE_ENUMS:
    for error_enum in enum_class:
        error_code = error_enum.value
        _ERROR_CODE_MAP[error_code.code] = error_code
        
        if error_code.category:
            if error_code.category not in _CATEGORY_MAP:
                _CATEGORY_MAP[error_code.category] = []
            _CATEGORY_MAP[error_code.category].append(error_code.code)


def get_error_code(code: str) -> Optional[ErrorCode]:
    """
    根据错误码字符串获取错误信息
    
    Args:
        code: 错误码字符串，如 "AUTH_001"
    
    Returns:
        ErrorCode 对象，如果不存在则返回 None
    
    Example:
        >>> error = get_error_code("AUTH_001")
        >>> print(error.message)
        用户名或密码错误
    """
    return _ERROR_CODE_MAP.get(code)


def get_error_message(code: str, default: str = "未知错误") -> str:
    """
    根据错误码字符串获取错误消息
    
    Args:
        code: 错误码字符串，如 "AUTH_001"
        default: 默认错误消息，当错误码不存在时返回
    
    Returns:
        错误消息字符串
    
    Example:
        >>> message = get_error_message("AUTH_001")
        >>> print(message)
        用户名或密码错误
    """
    error = get_error_code(code)
    return error.message if error else default


def get_http_code(code: str, default: int = 500) -> int:
    """
    根据错误码字符串获取 HTTP 状态码
    
    Args:
        code: 错误码字符串，如 "AUTH_001"
        default: 默认 HTTP 状态码，当错误码不存在时返回
    
    Returns:
        HTTP 状态码
    
    Example:
        >>> http_code = get_http_code("AUTH_001")
        >>> print(http_code)
        401
    """
    error = get_error_code(code)
    return error.http_code if error else default


def get_error_solution(code: str, default: str = "请稍后重试") -> str:
    """
    根据错误码字符串获取解决方案建议
    
    Args:
        code: 错误码字符串，如 "AUTH_001"
        default: 默认解决方案，当错误码不存在时返回
    
    Returns:
        解决方案字符串
    
    Example:
        >>> solution = get_error_solution("AUTH_001")
        >>> print(solution)
        请检查用户名和密码是否正确
    """
    error = get_error_code(code)
    if error and error.solution:
        return error.solution
    return default


def get_errors_by_category(category: str) -> List[ErrorCode]:
    """
    根据类别获取所有错误码
    
    Args:
        category: 错误类别，如 "auth"、"diagnosis"
    
    Returns:
        该类别下的所有错误码列表
    
    Example:
        >>> errors = get_errors_by_category("auth")
        >>> for e in errors:
        ...     print(e.code, e.message)
    """
    codes = _CATEGORY_MAP.get(category, [])
    return [_ERROR_CODE_MAP[code] for code in codes if code in _ERROR_CODE_MAP]


def get_all_error_codes() -> Dict[str, ErrorCode]:
    """
    获取所有错误码
    
    Returns:
        所有错误码的字典，键为错误码字符串，值为 ErrorCode 对象
    """
    return _ERROR_CODE_MAP.copy()


def get_all_categories() -> List[str]:
    """
    获取所有错误类别
    
    Returns:
        所有错误类别的列表
    """
    return list(_CATEGORY_MAP.keys())


def validate_error_code(code: str) -> bool:
    """
    验证错误码是否有效
    
    Args:
        code: 错误码字符串
    
    Returns:
        如果错误码存在则返回 True，否则返回 False
    """
    return code in _ERROR_CODE_MAP


def error_code_to_response(code: str, details: Any = None) -> Dict[str, Any]:
    """
    将错误码转换为标准响应格式

    Args:
        code: 错误码字符串
        details: 错误详情

    Returns:
        标准错误响应字典
    """
    error = get_error_code(code)

    if not error:
        return {
            "success": False,
            "error": {
                "error_code": code,
                "message": "未知错误",
                "details": details
            }
        }

    response = {
        "success": False,
        "error": {
            "error_code": error.code,
            "message": error.message,
        }
    }

    if details is not None:
        response["error"]["details"] = details

    if error.solution:
        response["error"]["solution"] = error.solution

    return response


def register_custom_error_code(
    code: str,
    message: str,
    http_code: int,
    category: Optional[str] = None,
    solution: Optional[str] = None
) -> ErrorCode:
    """
    注册自定义错误码
    
    允许在运行时添加新的错误码。
    
    Args:
        code: 错误码字符串
        message: 错误消息
        http_code: HTTP 状态码
        category: 错误类别
        solution: 解决方案
    
    Returns:
        新创建的 ErrorCode 对象
    
    Raises:
        ValueError: 如果错误码已存在
    
    Example:
        >>> error = register_custom_error_code(
        ...     "CUSTOM_001",
        ...     "自定义错误",
        ...     400,
        ...     category="custom"
        ... )
    """
    if code in _ERROR_CODE_MAP:
        raise ValueError(f"错误码 {code} 已存在")
    
    error = ErrorCode(
        code=code,
        message=message,
        http_code=http_code,
        category=category,
        solution=solution
    )
    
    _ERROR_CODE_MAP[code] = error
    
    if category:
        if category not in _CATEGORY_MAP:
            _CATEGORY_MAP[category] = []
        _CATEGORY_MAP[category].append(code)
    
    return error
