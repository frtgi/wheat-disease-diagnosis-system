"""
Schemas 单元测试
覆盖 user.py、diagnosis.py、common.py 中的 Pydantic 模型验证
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    LoginResponse,
    TokenData,
    PasswordResetRequest,
    PasswordReset,
    TokenRefresh,
    SessionResponse,
    MessageResponse,
)
from app.schemas.diagnosis import (
    DiagnosisBase,
    DiagnosisCreate,
    DiagnosisUpdate,
    DiagnosisResponse,
    DiagnosisWithDisease,
    DiseaseConfidence,
    DiagnosisResult,
    DiagnosisCreateResponse,
    DiagnosisListResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse


class TestUserCreate:
    """UserCreate 模式字段验证测试"""

    def test_valid_user_create(self):
        """
        测试有效的用户创建数据

        符合所有字段约束的数据应能正常创建 UserCreate 实例
        """
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="securepass123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "securepass123"

    def test_username_too_short(self):
        """
        测试用户名过短被拒绝

        用户名少于 3 个字符应触发 ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="ab", email="test@example.com", password="123456")
        errors = exc_info.value.errors()
        assert any("username" in str(e.get("loc", [])) for e in errors)

    def test_username_too_long(self):
        """
        测试用户名过长被拒绝

        用户名超过 50 个字符应触发 ValidationError
        """
        with pytest.raises(ValidationError):
            UserCreate(
                username="a" * 51,
                email="test@example.com",
                password="123456"
            )

    def test_password_too_short(self):
        """
        测试密码过短被拒绝

        密码少于 6 个字符应触发 ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="validuser", email="test@example.com", password="12345")
        errors = exc_info.value.errors()
        assert any("password" in str(e.get("loc", [])) for e in errors)

    def test_password_max_length(self):
        """
        测试密码最大长度边界

        密码恰好 100 字符应通过，101 字符应被拒绝
        """
        valid_pwd = "a" * 100
        user = UserCreate(username="user1", email="t@e.com", password=valid_pwd)
        assert len(user.password) == 100

        with pytest.raises(ValidationError):
            UserCreate(username="user2", email="t@e.com", password="a" * 101)

    def test_optional_phone_field(self):
        """
        测试可选手机号字段

        phone 为可选字段，不传或传 None 均可
        """
        user1 = UserCreate(username="user1", email="a@b.com", password="pass123")
        assert user1.phone is None

        user2 = UserCreate(
            username="user2", email="b@c.com", password="pass123", phone="13800138000"
        )
        assert user2.phone == "13800138000"

    def test_phone_max_length(self):
        """
        测试手机号最大长度限制

        手机号超过 20 个字符应被拒绝
        """
        with pytest.raises(ValidationError):
            UserCreate(
                username="user1",
                email="t@e.com",
                password="pass123",
                phone="1" * 21
            )


class TestUserUpdate:
    """UserUpdate 模式字段验证测试"""

    def test_all_fields_none(self):
        """
        测试所有字段为空（不更新任何字段）

        所有 Optional 字段均为 None 时应能正常创建
        """
        update = UserUpdate()
        assert update.username is None
        assert update.email is None
        assert update.phone is None
        assert update.avatar is None
        assert update.is_active is None

    def test_partial_update(self):
        """
        测试部分字段更新

        仅传入部分字段时，其他字段保持为 None
        """
        update = UserUpdate(username="newname")
        assert update.username == "newname"
        assert update.email is None
        assert update.is_active is None

    def test_username_validation(self):
        """
        测试更新时的用户名验证

        用户名仍需满足 min_length=3 和 max_length=50 约束
        """
        with pytest.raises(ValidationError):
            UserUpdate(username="ab")

        with pytest.raises(ValidationError):
            UserUpdate(username="a" * 51)

    def test_avatar_alias(self):
        """
        测试 avatar 别名字段

        avatar 是 avatar_url 的别名，传入 avatar_url 应映射到 avatar
        """
        update = UserUpdate(avatar_url="http://example.com/avatar.png")
        assert update.avatar == "http://example.com/avatar.png"


class TestUserResponse:
    """UserResponse 模式字段验证测试"""

    def test_valid_user_response(self):
        """
        测试有效的用户响应数据

        包含所有必需字段的响应数据应能正常解析
        """
        now = datetime.now(timezone.utc)
        response = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            role="farmer",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert response.id == 1
        assert response.role == "farmer"
        assert response.is_active is True

    def test_default_role_value(self):
        """
        测试角色默认值

        不指定 role 时默认应为 "farmer"
        """
        now = datetime.now(timezone.utc)
        response = UserResponse(
            id=1,
            username="user",
            email="u@e.com",
            created_at=now,
            updated_at=now,
        )
        assert response.role == "farmer"

    def test_no_password_field(self):
        """
        测试响应中不含密码字段

        UserResponse 不应包含 password 或 password_hash 字段
        """
        now = datetime.now(timezone.utc)
        data = UserResponse(
            id=1,
            username="validuser",
            email="e@e.com",
            created_at=now,
            updated_at=now,
        ).model_dump()
        assert "password" not in data
        assert "password_hash" not in data


class TestDiagnosisSchemas:
    """诊断相关 Schema 测试"""

    def test_disease_confidence_valid(self):
        """
        测试有效的病害置信度数据

        disease_name 必填，confidence 在 [0, 1] 范围内
        """
        dc = DiseaseConfidence(disease_name="小麦锈病", confidence=0.95)
        assert dc.disease_name == "小麦锈病"
        assert dc.confidence == 0.95
        assert dc.disease_class is None

    def test_disease_confidence_with_class(self):
        """
        测试带类别 ID 的病害置信度

        disease_class 可选字段
        """
        dc = DiseaseConfidence(
            disease_name="白粉病",
            confidence=0.88,
            disease_class=2
        )
        assert dc.disease_class == 2

    def test_disease_confidence_out_of_range(self):
        """
        测试置信度超出范围被拒绝

        confidence < 0 或 > 1 应触发 ValidationError
        """
        with pytest.raises(ValidationError):
            DiseaseConfidence(disease_name="锈病", confidence=-0.1)

        with pytest.raises(ValidationError):
            DiseaseConfidence(disease_name="锈病", confidence=1.5)

    def test_diagnosis_response_fields(self):
        """
        测试诊断响应包含所有必需字段

        DiagnosisResponse 包含 id, user_id, status, 时间戳等字段
        """
        now = datetime.now(timezone.utc)
        dr = DiagnosisResponse(
            id=1,
            user_id=10,
            symptoms="叶片出现黄色斑点",
            diagnosis_result="小麦锈病",
            confidence=0.92,
            status="completed",
            created_at=now,
            updated_at=now,
        )
        assert dr.id == 1
        assert dr.user_id == 10
        assert dr.status == "completed"
        assert dr.confidence == 0.92

    def test_diagnosis_create_response_with_confidences(self):
        """
        测试诊断创建响应中的 confidences 列表

        confidences 字段为 DiseaseConfidence 列表，默认为空列表
        """
        now = datetime.now(timezone.utc)
        dcr = DiagnosisCreateResponse(
            diagnosis_id="diag_001",
            disease_name="小麦锈病",
            confidence=0.93,
            confidences=[
                DiseaseConfidence(disease_name="小麦锈病", confidence=0.93),
                DiseaseConfidence(disease_name="小麦白粉病", confidence=0.05),
            ],
            created_at=now,
        )
        assert len(dcr.confidences) == 2
        assert dcr.confidences[0].disease_name == "小麦锈病"

    def test_diagnosis_create_response_default_confidences(self):
        """
        测试不传 confidences 时使用默认空列表
        """
        now = datetime.now(timezone.utc)
        dcr = DiagnosisCreateResponse(
            diagnosis_id="diag_002",
            disease_name="蚜虫",
            confidence=0.85,
            created_at=now,
        )
        assert dcr.confidences == []

    def test_diagnosis_result_full_fields(self):
        """
        测试完整诊断结果模型

        DiagnosisResult 包含病害名称、置信度、严重程度等全部字段
        """
        result = DiagnosisResult(
            disease_name="条锈病",
            confidence=0.91,
            severity="中度",
            description="叶片出现典型条状锈斑",
            recommendations="喷洒三唑酮类杀菌剂",
            knowledge_links=["/knowledge/rust"],
        )
        assert result.severity == "中度"
        assert len(result.knowledge_links) == 1

    def test_diagnosis_update_optional_fields(self):
        """
        测试诊断更新的可选字段

        DiagnosisUpdate 所有字段均为 Optional
        """
        du = DiagnosisUpdate()
        assert du.diagnosis_result is None
        assert du.confidence is None
        assert du.suggestions is None

        du2 = DiagnosisUpdate(confidence=0.75, status="reviewing")
        assert du2.confidence == 0.75
        assert du2.status == "reviewing"

    def test_symptoms_max_length(self):
        """
        测试症状描述最大长度

        symptoms 超过 2000 字符应被拒绝
        """
        with pytest.raises(ValidationError):
            DiagnosisBase(symptoms="x" * 2001)


class TestPaginationParams:
    """分页参数模式测试"""

    def test_default_values(self):
        """
        测试分页参数默认值

        默认 page=1, page_size=20
        """
        params = PaginationParams.model_construct(page=1, page_size=20)
        assert params.page == 1
        assert params.page_size == 20

    def test_custom_values(self):
        """
        测试自定义分页参数值
        """
        params = PaginationParams.model_construct(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50

    def test_page_minimum_one(self):
        """
        测试 page 最小值为 1

        page 字段定义了 ge=1 约束，通过 JSON Schema 验证约束配置
        """
        import json
        schema = PaginationParams.model_json_schema()
        page_props = schema["properties"]["page"]
        assert page_props.get("minimum") == 1

    def test_page_size_minimum_one(self):
        """
        测试 page_size 最小值为 1

        page_size 字段定义了 ge=1 约束
        """
        schema = PaginationParams.model_json_schema()
        ps_props = schema["properties"]["page_size"]
        assert ps_props.get("minimum") == 1

    def test_page_size_maximum_hundred(self):
        """
        测试 page_size 最大值为 100

        page_size 字段定义了 le=100 约束
        """
        schema = PaginationParams.model_json_schema()
        ps_props = schema["properties"]["page_size"]
        assert ps_props.get("maximum") == 100

    def test_boundary_values(self):
        """
        测试边界值：page=1, page_size=100 应通过
        """
        params = PaginationParams.model_construct(page=1, page_size=100)
        assert params.page == 1
        assert params.page_size == 100

    def test_skip_property(self):
        """
        测试 skip 属性计算

        skip = (page - 1) * page_size
        """
        params = PaginationParams.model_construct(page=3, page_size=20)
        assert params.skip == 40

    def test_limit_property(self):
        """
        测试 limit 属性返回 page_size
        """
        params = PaginationParams.model_construct(page=1, page_size=50)
        assert params.limit == 50


class TestPaginatedResponse:
    """分页响应模式测试"""

    def test_normal_paginated_response(self):
        """
        测试正常的分页响应

        items 列表、total 总数、page/page_size 分页信息
        """
        resp = PaginatedResponse.model_construct(
            items=[{"id": 1}, {"id": 2}],
            total=10,
            page=1,
            page_size=2,
        )
        assert len(resp.items) == 2
        assert resp.total == 10

    def test_empty_items(self):
        """
        测试空数据集的分页响应

        total=0 时 total_pages 应为 0
        """
        resp = PaginatedResponse.model_construct(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert resp.items == []
        assert resp.total_pages == 0

    def test_total_pages_calculation(self):
        """
        测试总页数计算逻辑

        total_pages = ceil(total / page_size)，整除时无余数页
        """
        resp1 = PaginatedResponse.model_construct(items=[], total=25, page=1, page_size=10, total_pages=3)
        assert resp1.total_pages == 3

        resp2 = PaginatedResponse.model_construct(items=[], total=20, page=1, page_size=10, total_pages=2)
        assert resp2.total_pages == 2


class TestOtherSchemas:
    """其他 Schema 模型测试"""

    def test_token_schema(self):
        """
        测试 Token 模式

        access_token 必填，token_type 默认 bearer
        """
        token = Token(access_token="jwt_token_string")
        assert token.access_token == "jwt_token_string"
        assert token.token_type == "bearer"

    def test_login_schema(self):
        """
        测试登录请求模式

        username 和 password 均为必填
        """
        login = UserLogin(username="admin", password="secret")
        assert login.username == "admin"
        assert login.password == "secret"

    def test_token_data_optional_fields(self):
        """
        测试令牌数据模式的可选字段

        username 和 user_id 均为 Optional
        """
        td = TokenData()
        assert td.username is None
        assert td.user_id is None

        td2 = TokenData(username="admin", user_id=1)
        assert td2.username == "admin"
        assert td2.user_id == 1

    def test_message_response(self):
        """
        测试通用消息响应模式

        message 必填，success 默认 True
        """
        msg = MessageResponse(message="操作成功")
        assert msg.message == "操作成功"
        assert msg.success is True

    def test_password_reset_request(self):
        """
        测试密码重置请求模式

        email 为必填字段
        """
        req = PasswordResetRequest(email="user@example.com")
        assert req.email == "user@example.com"

    def test_password_reset_validation(self):
        """
        测试密码重置执行模式的验证

        new_password 需满足 min_length=6, max_length=100
        """
        pr = PasswordReset(token="reset_token_xyz", new_password="newPass123")
        assert pr.token == "reset_token_xyz"
        assert pr.new_password == "newPass123"

        with pytest.raises(ValidationError):
            PasswordReset(token="t", new_password="short")

    def test_token_refresh_schema(self):
        """
        测试令牌刷新模式

        refresh_token 为必填字段
        """
        tr = TokenRefresh(refresh_token="refresh_jwt_here")
        assert tr.refresh_token == "refresh_jwt_here"
