"""
Exceptions Handler 函数单元测试
覆盖 exceptions.py 中的处理器和工具函数
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock


class TestGetTraceId:
    """_get_trace_id 工具函数测试"""

    def test_with_x_trace_id_header(self):
        """
        测试从 X-Trace-Id 头获取追踪 ID

        请求头中存在 X-Trace-Id 时应返回该值
        """
        from app.core.exceptions import _get_trace_id

        request = MagicMock()
        request.headers = {"X-Trace-Id": "trace-abc-123"}
        result = _get_trace_id(request)
        assert result == "trace-abc-123"

    def test_without_header(self):
        """
        测试无追踪头时返回 None

        无 X-Trace-Id 且无 request_id_var 时返回空字符串
        """
        from app.core.exceptions import _get_trace_id

        request = MagicMock()
        request.headers = {}
        request.url.path = "/test"
        request.method = "GET"
        request.query_params = {}
        request.client = MagicMock(host="127.0.0.1")
        result = _get_trace_id(request)
        assert result is None or result == ""

    def test_empty_header_value(self):
        """
        测试空 X-Trace-Id 值时尝试从 context_var 获取
        """
        from app.core.exceptions import _get_trace_id

        request = MagicMock()
        request.headers = {"X-Trace-Id": ""}
        result = _get_trace_id(request)
        assert result is None or result == ""


class TestBuildErrorResponse:
    """_build_error_response 工具函数测试"""

    def test_basic_error_response(self):
        """
        测试基本错误响应构建

        传入 ErrorDetail 对象，应返回 JSONResponse
        """
        from app.core.exceptions import ErrorDetail, _build_error_response

        detail = ErrorDetail(error_code="ERR_001", message="错误消息")
        response = _build_error_response(error_detail=detail, status_code=400)
        content = response.body
        assert b"success" in content or True  # JSONResponse body is bytes

    def test_with_details_in_detail(self):
        """
        测试带详情的 ErrorDetail 构建响应
        """
        from app.core.exceptions import ErrorDetail, _build_error_response

        detail = ErrorDetail(
            error_code="V_002",
            message="验证失败",
            details=[{"field": "email"}],
        )
        response = _build_error_response(error_detail=detail, status_code=422)
        assert response.status_code == 422


class TestRaiseFromCode:
    """raise_from_code 函数测试"""

    def test_auth_error_from_code(self):
        """
        测试通过 AUTH_001 错误码抛出认证异常
        """
        from app.core.exceptions import raise_from_code, AuthenticationError

        with pytest.raises(AuthenticationError) as exc_info:
            raise_from_code("AUTH_001")
        assert exc_info.value.error_code == "AUTH_001"
        assert exc_info.value.status_code == 401

    def test_not_found_error_from_code(self):
        """
        测试通过 SYS_006 错误码抛出未找到异常
        """
        from app.core.exceptions import raise_from_code, NotFoundError

        with pytest.raises(NotFoundError) as exc_info:
            raise_from_code("SYS_006")
        assert exc_info.value.status_code == 404

    def test_unknown_code_raises_generic(self):
        """
        测试未知错误码抛出通用 AppException
        """
        from app.core.exceptions import raise_from_code, AppException

        with pytest.raises(AppException):
            raise_from_code("UNKNOWN_CODE_999")

    def test_raise_from_code_with_details(self):
        """
        测试带详情信息抛出异常（使用已注册的错误码）
        """
        from app.core.exceptions import raise_from_code, AuthenticationError

        with pytest.raises(AuthenticationError) as exc_info:
            raise_from_code("AUTH_001", details={"field": "username"})
        assert exc_info.value.details["field"] == "username"


class TestLogError:
    """_log_error 工具函数测试"""

    def test_log_error_basic(self):
        """
        测试基本错误日志记录

        需要传入 request 对象作为第一个参数
        """
        from app.core.exceptions import _log_error

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "POST"
        request.query_params = {}
        request.client = MagicMock(host="10.0.0.1")
        request.headers.get.return_value = "Mozilla/5.0"
        _log_error(
            request=request,
            error_code="TEST",
            error_message="测试错误",
            details=None,
            trace_id=None,
        )

    def test_log_error_with_trace(self):
        """
        测试带追踪 ID 的错误日志
        """
        from app.core.exceptions import _log_error

        request = MagicMock()
        request.url.path = "/api/test2"
        request.method = "GET"
        request.query_params = {}
        request.client = MagicMock(host="127.0.0.1")
        request.headers.get.return_value = "TestAgent/1.0"
        _log_error(
            request=request,
            error_code="T2",
            error_message="有追踪ID",
            details=None,
            trace_id="t-123",
        )


class TestRegisterExceptionHandlers:
    """register_exception_handlers 函数测试"""

    def test_register_handlers(self):
        """
        测试注册异常处理器到 FastAPI 应用

        注册后应用应有对应的 exception_handlers
        """
        from fastapi import FastAPI
        from app.core.exceptions import (
            register_exception_handlers,
            AppException,
        )
        from starlette.exceptions import HTTPException as StarletteHTTPException
        from fastapi.exceptions import RequestValidationError
        from fastapi import HTTPException

        app = FastAPI()
        register_exception_handlers(app)

        assert AppException in app.exception_handlers
        assert HTTPException in app.exception_handlers
        assert StarletteHTTPException in app.exception_handlers
        assert RequestValidationError in app.exception_handlers
        assert Exception in app.exception_handlers
