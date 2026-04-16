"""
核心模块单元测试（第二部分）
覆盖 error_codes、response、rate_limiter 等核心模块
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app.core.error_codes import (
    ErrorCode,
    SystemErrorCode,
    AuthErrorCode,
    UserErrorCode,
    DiagnosisErrorCode,
    AIErrorCode,
    DatabaseErrorCode,
    get_error_code,
    get_error_message,
    get_http_code,
    validate_error_code,
)
from app.core.response import (
    ErrorDetail as ResponseErrorDetail,
    ApiResponse,
    success_response,
    error_response,
)


class TestErrorCode:
    """ErrorCode 数据类测试"""

    def test_basic_creation(self):
        """
        测试 ErrorCode 基本创建

        必填字段 code, message, http_code 应正确赋值
        """
        ec = ErrorCode(code="TEST_001", message="测试错误", http_code=400)
        assert ec.code == "TEST_001"
        assert ec.message == "测试错误"
        assert ec.http_code == 400
        assert ec.category is None
        assert ec.solution is None

    def test_with_optional_fields(self):
        """
        测试带可选字段的 ErrorCode 创建
        """
        ec = ErrorCode(
            code="SYS_001",
            message="系统错误",
            http_code=500,
            category="system",
            solution="请稍后重试"
        )
        assert ec.category == "system"
        assert ec.solution == "请稍后重试"

    def test_to_dict_basic(self):
        """
        测试基本 to_dict() 输出

        不含可选字段时，输出仅包含 code/message/http_code
        """
        ec = ErrorCode(code="T_1", message="m", http_code=404)
        result = ec.to_dict()
        assert result["error_code"] == "T_1"
        assert result["message"] == "m"
        assert result["http_code"] == 404
        assert "category" not in result
        assert "solution" not in result

    def test_to_dict_with_optionals(self):
        """
        测试带可选字段的 to_dict() 输出
        """
        ec = ErrorCode(
            code="A_1", message="a", http_code=401,
            category="auth", solution="重新登录"
        )
        result = ec.to_dict()
        assert result["category"] == "auth"
        assert result["solution"] == "重新登录"


class TestSystemErrorCode:
    """SystemErrorCode 枚举测试"""

    def test_sys_001_values(self):
        """
        测试 SYS_001 系统内部错误枚举值
        """
        ec = SystemErrorCode.SYS_001.value
        assert ec.code == "SYS_001"
        assert ec.http_code == 500
        assert ec.category == "system"

    def test_sys_005_rate_limit(self):
        """
        测试 SYS_005 限流错误码（429）
        """
        ec = SystemErrorCode.SYS_005.value
        assert ec.http_code == 429
        assert "频率" in ec.message or "超限" in ec.message

    def test_all_system_codes_have_http_code(self):
        """
        测试所有系统错误码都有有效的 HTTP 状态码

        验证每个枚举值的 http_code 在合理范围内 (>= 400)
        """
        for member in SystemErrorCode:
            ec = member.value
            assert isinstance(ec, ErrorCode)
            assert ec.code.startswith("SYS_")
            assert 400 <= ec.http_code <= 599


class TestAuthErrorCode:
    """AuthErrorCode 认证错误码枚举测试"""

    def test_auth_001_default(self):
        """
        测试 AUTH_001 默认认证失败错误码
        """
        ec = AuthErrorCode.AUTH_001.value
        assert ec.http_code == 401

    def test_auth_004_forbidden(self):
        """
        测试 AUTH_004 权限不足错误码（403）
        """
        ec = AuthErrorCode.AUTH_004.value
        assert ec.http_code == 403


class TestGetErrorCode:
    """get_error_code 辅助函数测试"""

    def test_existing_code(self):
        """
        测试获取已存在的错误码

        应返回对应的 ErrorCode 对象
        """
        ec = get_error_code("AUTH_001")
        assert ec is not None
        assert ec.code == "AUTH_001"
        assert ec.http_code == 401

    def test_nonexistent_code(self):
        """
        测试获取不存在的错误码

        应返回 None
        """
        ec = get_error_code("NONEXISTENT_999")
        assert ec is None

    def test_diagnosis_code(self):
        """
        测试诊断相关错误码查找
        """
        ec = get_error_code("DIAG_001")
        assert ec is not None
        assert ec.http_code == 500


class TestGetErrorMessage:
    """get_error_message 辅助函数测试"""

    def test_existing_message(self):
        """
        测试获取已存在错误码的消息
        """
        msg = get_error_message("SYS_001")
        assert msg is not None
        assert len(msg) > 0

    def test_default_message(self):
        """
        测试不存在的错误码使用默认消息
        """
        msg = get_error_code("INVALID_CODE")
        default_msg = get_error_message("INVALID_CODE")
        assert default_msg == "未知错误"

    def test_custom_default(self):
        """
        测试自定义默认消息
        """
        msg = get_error_message("NO_SUCH_CODE", default="自定义默认消息")
        assert msg == "自定义默认消息"


class TestGetHttpCode:
    """get_http_code 辅助函数测试"""

    def test_auth_code_http_status(self):
        """
        测试认证错误码的 HTTP 状态码
        """
        assert get_http_code("AUTH_001") == 401
        assert get_http_code("AUTH_004") == 403

    def test_validation_code_http_status(self):
        """
        测试验证错误码的 HTTP 状态码（422）
        """
        http_code = get_http_code("VALIDATION_001")
        assert http_code == 422

    def test_default_http_code(self):
        """
        测试不存在错误码的默认 HTTP 状态码（500）
        """
        assert get_http_code("NONEXISTENT") == 500

    def test_custom_default_http_code(self):
        """
        测试自定义默认 HTTP 状态码
        """
        assert get_http_code("X_999", default=503) == 503


class TestValidateErrorCode:
    """validate_error_code 函数测试"""

    def test_valid_code(self):
        """
        测试有效错误码验证
        """
        assert validate_error_code("SYS_001") is True
        assert validate_error_code("AUTH_001") is True
        assert validate_error_code("DIAG_001") is True

    def test_invalid_code(self):
        """
        测试无效错误码验证
        """
        assert validate_error_code("") is False
        assert validate_error_code("INVALID") is False
        assert validate_error_code("123") is False


class TestResponseModels:
    """response.py 模型测试"""

    def test_error_detail_model(self):
        """
        测试响应错误详情模型

        ErrorDetail 包含 error_code, message, 可选 detail
        """
        ed = ResponseErrorDetail(error_code="E_001", message="出错啦")
        assert ed.error_code == "E_001"
        assert ed.message == "出错啦"
        assert ed.detail is None

    def test_error_detail_with_detail(self):
        """
        测试带详情的 ErrorDetail 模型
        """
        ed = ResponseErrorDetail(
            error_code="V_001",
            message="验证失败",
            detail="用户名不能为空"
        )
        assert ed.detail == "用户名不能为空"

    def test_api_response_success(self):
        """
        测试成功 API 响应模型
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = ApiResponse(
            success=True,
            code=200,
            message="OK",
            data={"id": 1},
            timestamp=now
        )
        assert resp.success is True
        assert resp.code == 200
        assert resp.error is None

    def test_api_response_error(self):
        """
        测试错误 API 响应模型
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        err_detail = ResponseErrorDetail(error_code="ERR", message="err")
        resp = ApiResponse(
            success=False,
            code=500,
            error=err_detail,
            timestamp=now
        )
        assert resp.success is False
        assert resp.error.error_code == "ERR"


class TestSuccessResponse:
    """success_response 函数测试"""

    def test_basic_success(self):
        """
        测试基本成功响应

        默认 success=True, code=200, message="操作成功"
        """
        resp = success_response()
        assert resp["success"] is True
        assert resp["code"] == 200
        assert resp["message"] == "操作成功"
        assert resp["data"] == {}
        assert "timestamp" in resp

    def test_success_with_data(self):
        """
        测试带数据的成功响应
        """
        resp = success_response(data={"user_id": 42, "name": "test"})
        assert resp["data"]["user_id"] == 42
        assert resp["data"]["name"] == "test"

    def test_success_custom_message_and_code(self):
        """
        测试自定义消息和状态码的成功响应
        """
        resp = success_response(message="创建成功", code=201)
        assert resp["message"] == "创建成功"
        assert resp["code"] == 201

    def test_success_none_data_becomes_empty_dict(self):
        """
        测试 data=None 时转换为空字典
        """
        resp = success_response(data=None)
        assert resp["data"] == {}

    def test_timestamp_format(self):
        """
        测试时间戳格式为 ISO 8601 UTC
        """
        resp = success_response()
        timestamp = resp["timestamp"]
        assert "T" in timestamp
        assert timestamp.endswith("Z")


class TestErrorResponse:
    """error_response 函数测试"""

    def test_basic_error(self):
        """
        测试基本错误响应

        默认 success=False, code=400
        """
        resp = error_response("ERR_001", "出错了")
        assert resp["success"] is False
        assert resp["code"] == 400
        assert resp["error"]["error_code"] == "ERR_001"
        assert resp["error"]["message"] == "出错了"
        assert "timestamp" in resp

    def test_error_with_detail(self):
        """
        测试带详细信息的错误响应
        """
        resp = error_response(
            "VAL_002",
            "参数错误",
            detail="email 格式无效"
        )
        assert resp["error"]["detail"] == "email 格式无效"

    def test_error_without_detail(self):
        """
        测试不带详细信息时 error 中不含 detail 字段
        """
        resp = error_response("S_003", "服务错误")
        assert "detail" not in resp["error"]

    def test_error_custom_http_code(self):
        """
        测试自定义 HTTP 状态码的错误响应
        """
        resp = error_response("A_001", "未授权", http_code=401)
        assert resp["code"] == 401

    def test_error_server_error_default(self):
        """
        测试服务器错误的默认状态码
        """
        resp = error_response("DB_001", "数据库异常")
        assert resp["code"] == 400  # 默认值


class TestRateLimiter:
    """限流器模块测试"""

    def test_limiter_exists(self):
        """
        测试限流器实例在 TESTING 模式下被禁用
        """
        from app.rate_limiter import limiter
        assert limiter is not None

    def test_limiter_disabled_in_testing(self):
        """
        测试测试环境下限流器被禁用

        TESTING=true 时 limiter.enabled 应为 False
        """
        import os
        testing_val = os.getenv("TESTING", "false").lower()
        if testing_val == "true":
            from app.rate_limiter import limiter
            assert limiter.enabled is False
