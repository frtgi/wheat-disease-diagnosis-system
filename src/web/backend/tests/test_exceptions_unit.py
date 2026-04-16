"""
Exceptions 单元测试
覆盖 exceptions.py 中的 ErrorDetail、AppException 及各子类异常
"""
import pytest
from datetime import datetime, timezone

from app.core.exceptions import (
    ErrorDetail,
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
    _format_validation_errors,
)


class TestErrorDetail:
    """ErrorDetail 错误详情类测试"""

    def test_basic_creation(self):
        """
        测试基本创建

        传入 error_code 和 message 应能正常创建实例
        """
        detail = ErrorDetail(error_code="TEST_001", message="测试错误")
        assert detail.error_code == "TEST_001"
        assert detail.message == "测试错误"
        assert detail.details is None
        assert detail.trace_id is None

    def test_with_details(self):
        """
        测试带详情信息的创建

        details 可以为任意类型（字典、列表、字符串等）
        """
        detail = ErrorDetail(
            error_code="TEST_002",
            message="带详情的错误",
            details={"field": "username", "reason": "已存在"}
        )
        assert detail.details["field"] == "username"

    def test_with_trace_id(self):
        """
        测试带追踪 ID 的创建

        trace_id 用于请求链路追踪
        """
        detail = ErrorDetail(
            error_code="TEST_003",
            message="带追踪ID",
            trace_id="trace-abc-123"
        )
        assert detail.trace_id == "trace-abc-123"

    def test_auto_timestamp(self):
        """
        测试自动生成时间戳

        创建时应自动设置 timestamp 为 UTC ISO 格式时间字符串
        """
        before = datetime.now(timezone.utc)
        detail = ErrorDetail(error_code="T", message="m")
        after = datetime.now(timezone.utc)
        parsed_time = datetime.fromisoformat(detail.timestamp)
        assert before <= parsed_time <= after

    def test_code_property_alias(self):
        """
        测试 code 属性别名

        code 属性应返回与 error_code 相同的值（向后兼容）
        """
        detail = ErrorDetail(error_code="ALIAS_TEST", message="别名测试")
        assert detail.code == "ALIAS_TEST"
        assert detail.code == detail.error_code

    def test_to_dict_basic(self):
        """
        测试基本 to_dict() 输出格式

        应包含 error_code、message、timestamp 字段
        """
        detail = ErrorDetail(error_code="DICT_001", message="字典测试")
        result = detail.to_dict()
        assert result["error_code"] == "DICT_001"
        assert result["message"] == "字典测试"
        assert "timestamp" in result
        assert "details" not in result

    def test_to_dict_with_details(self):
        """
        测试带详情的 to_dict() 输出

        当 details 不为 None 时，输出应包含 details 字段
        """
        detail = ErrorDetail(
            error_code="DICT_002",
            message="有详情",
            details={"key": "value"}
        )
        result = detail.to_dict()
        assert "details" in result
        assert result["details"]["key"] == "value"

    def test_to_dict_with_trace_id(self):
        """
        测试带 trace_id 的 to_dict() 输出

        当 trace_id 不为空时，输出应包含 trace_id 字段
        """
        detail = ErrorDetail(
            error_code="DICT_003",
            message="有追踪",
            trace_id="tid-xyz"
        )
        result = detail.to_dict()
        assert result["trace_id"] == "tid-xyz"

    def test_to_dict_no_details_when_none(self):
        """
        测试 details 为 None 时不出现在字典中

        确保输出中不包含值为 None 的 details 键
        """
        detail = ErrorDetail(error_code="D", message="m", details=None)
        result = detail.to_dict()
        assert "details" not in result


class TestAuthenticationError:
    """认证错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="认证失败"，error_code="AUTH_001"，status_code=401
        """
        err = AuthenticationError()
        assert err.message == "认证失败"
        assert err.error_code == "AUTH_001"
        assert err.status_code == 401

    def test_custom_values(self):
        """
        测试自定义错误信息

        可自定义 message、error_code 和 details
        """
        err = AuthenticationError(
            message="Token 已过期",
            error_code="AUTH_002",
            details={"token_type": "access"}
        )
        assert err.message == "Token 已过期"
        assert err.error_code == "AUTH_002"
        assert err.status_code == 401
        assert err.details["token_type"] == "access"

    def test_is_app_exception_subclass(self):
        """
        测试继承关系

        AuthenticationError 应为 AppException 的子类
        """
        err = AuthenticationError()
        assert isinstance(err, AppException)
        assert isinstance(err, Exception)

    def test_to_error_detail(self):
        """
        测试转换为 ErrorDetail 对象

        to_error_detail() 应返回包含相同信息的 ErrorDetail 实例
        """
        err = AuthenticationError(message="登录失败", error_code="AUTH_003")
        ed = err.to_error_detail(trace_id="t1")
        assert isinstance(ed, ErrorDetail)
        assert ed.error_code == "AUTH_003"
        assert ed.message == "登录失败"
        assert ed.trace_id == "t1"


class TestAuthorizationError:
    """授权错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="权限不足"，error_code="AUTH_004"，status_code=403
        """
        err = AuthorizationError()
        assert err.message == "权限不足"
        assert err.error_code == "AUTH_004"
        assert err.status_code == 403

    def test_custom_values(self):
        """
        测试自定义授权错误信息
        """
        err = AuthorizationError(
            message="需要管理员权限",
            error_code="AUTH_005",
            details={"required_role": "admin"}
        )
        assert err.status_code == 403
        assert err.details["required_role"] == "admin"


class TestValidationError:
    """验证错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="数据验证失败"，error_code="VALIDATION_001"，status_code=422
        """
        err = ValidationError()
        assert err.message == "数据验证失败"
        assert err.error_code == "VALIDATION_001"
        assert err.status_code == 422

    def test_with_field_details(self):
        """
        测试带字段级验证详情的错误
        """
        err = ValidationError(
            message="用户名格式不正确",
            details=[
                {"field": "username", "message": "不能包含特殊字符"}
            ]
        )
        assert len(err.details) == 1
        assert err.details[0]["field"] == "username"


class TestNotFoundError:
    """资源不存在错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="资源不存在"，error_code="SYS_006"，status_code=404
        """
        err = NotFoundError()
        assert err.message == "资源不存在"
        assert err.error_code == "SYS_006"
        assert err.status_code == 404

    def test_custom_not_found(self):
        """
        测试自定义资源不存在消息
        """
        err = NotFoundError(
            message="用户 ID=999 不存在",
            error_code="USER_003",
            details={"resource_type": "User", "id": 999}
        )
        assert err.status_code == 404


class TestConflictError:
    """冲突错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="资源冲突"，error_code="CONFLICT_001"，status_code=409
        """
        err = ConflictError()
        assert err.message == "资源冲突"
        assert err.error_code == "CONFLICT_001"
        assert err.status_code == 409


class TestRateLimitError:
    """限流错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="请求过于频繁"，error_code="SYS_005"，status_code=429
        """
        err = RateLimitError()
        assert err.message == "请求过于频繁"
        assert err.error_code == "SYS_005"
        assert err.status_code == 429

    def test_with_retry_info(self):
        """
        测试带重试信息的限流错误
        """
        err = RateLimitError(
            message="每分钟最多请求 60 次",
            details={"retry_after": 30, "limit": 60}
        )
        assert err.details["retry_after"] == 30


class TestAIServiceError:
    """AI 服务错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="AI 服务暂时不可用"，code="AI_001"，status_code=503
        注意：AIServiceError 使用 code 作为参数名（内部传给父类 error_code）
        """
        err = AIServiceError()
        assert err.message == "AI 服务暂时不可用"
        assert err.error_code == "AI_001"
        assert err.status_code == 503

    def test_custom_ai_error(self):
        """
        测试自定义 AI 服务错误

        通过 code 关键字参数传入错误码
        """
        err = AIServiceError(
            message="模型推理超时",
            code="AI_002",
            details={"model": "qwen", "timeout_ms": 30000}
        )
        assert err.error_code == "AI_002"
        assert err.details["model"] == "qwen"


class TestDatabaseError:
    """数据库错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="数据库操作失败"，error_code="DB_001"，status_code=500
        """
        err = DatabaseError()
        assert err.message == "数据库操作失败"
        assert err.error_code == "DB_001"
        assert err.status_code == 500


class TestDiagnosisError:
    """诊断错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="诊断失败"，error_code="DIAG_001"，status_code=500
        """
        err = DiagnosisError()
        assert err.message == "诊断失败"
        assert err.error_code == "DIAG_001"
        assert err.status_code == 500


class TestFileUploadError:
    """文件上传错误异常类测试"""

    def test_default_values(self):
        """
        测试默认值

        默认 message="文件上传失败"，error_code="FILE_001"，status_code=400
        """
        err = FileUploadError()
        assert err.message == "文件上传失败"
        assert err.error_code == "FILE_001"
        assert err.status_code == 400


class TestAppExceptionBase:
    """AppException 基类行为测试"""

    def test_str_representation(self):
        """
        测试异常的字符串表示

        str(exc) 应返回 message 内容
        """
        err = AppException(
            error_code="BASE_001",
            message="基础异常消息"
        )
        assert str(err) == "基础异常消息"

    def test_code_property(self):
        """
        测试基类的 code 别名属性

        code 属性应返回 error_code 的值
        """
        err = AppException(error_code="C_001", message="m")
        assert err.code == "C_001"

    def test_default_status_code(self):
        """
        测试默认 HTTP 状态码

        不指定 status_code 时默认为 500
        """
        err = AppException(error_code="S_001", message="m")
        assert err.status_code == 500

    def test_custom_status_code(self):
        """
        测试自定义状态码
        """
        err = AppException(error_code="S_002", message="m", status_code=502)
        assert err.status_code == 502


class TestFormatValidationErrors:
    """_format_validation_errors 工具函数测试"""

    def test_single_error_formatting(self):
        """
        测试单个验证错误的格式化

        Pydantic 验证错误应转换为友好格式
        """
        pydantic_errors = [
            {
                "loc": ("body", "username"),
                "msg": "字段必填",
                "type": "value_error.missing",
                "input": None,
            }
        ]
        formatted = _format_validation_errors(pydantic_errors)
        assert len(formatted) == 1
        assert formatted[0]["field"] == "body.username"
        assert formatted[0]["message"] == "字段必填"
        assert formatted[0]["type"] == "value_error.missing"

    def test_multiple_errors_formatting(self):
        """
        测试多个验证错误的批量格式化
        """
        pydantic_errors = [
            {
                "loc": ("body", "email"),
                "msg": "邮箱格式无效",
                "type": "value_error.email",
                "input": "not-an-email",
            },
            {
                "loc": ("query", "page"),
                "msg": "必须大于 0",
                "type": "value_error.number.not_gt",
                "input": -1,
            }
        ]
        formatted = _format_validation_errors(pydantic_errors)
        assert len(formatted) == 2
        assert formatted[0]["field"] == "body.email"
        assert formatted[1]["field"] == "query.page"

    def test_empty_loc_handling(self):
        """
        测试空 loc 元素的处理

        loc 中空元素或 None 应被跳过
        """
        pydantic_errors = [
            {
                "loc": ("", "field1",),
                "msg": "错误",
                "type": "test",
                "input": "val",
            }
        ]
        formatted = _format_validation_errors(pydantic_errors)
        assert formatted[0]["field"] == "field1"

    def test_empty_errors_list(self):
        """
        测试空错误列表返回空结果
        """
        result = _format_validation_errors([])
        assert result == []
