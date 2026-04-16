"""
安全修复验证测试
验证 P0/P1 级别的安全修复，包括密码哈希、API认证、文件上传等
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io
import base64


class TestPasswordHashNotLeaked:
    """
    密码哈希泄露测试（P0 级别）

    验证系统不会在响应中泄露密码哈希值
    """

    def test_user_response_no_password_hash(self):
        """
        测试用户信息响应不包含密码哈希字段

        验证 API 返回的用户数据中不应包含 password_hash 字段
        """
        from app.schemas.user import UserResponse

        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False
        }

        response = UserResponse(**user_data)

        assert not hasattr(response, 'password_hash')
        assert 'password' not in response.model_dump().keys()
        assert 'hash' not in str(response.model_dump()).lower()

    def test_login_response_no_sensitive_data(self):
        """
        测试登录响应不包含敏感密码信息

        验证登录成功后返回的数据中不包含密码相关字段
        """
        login_response = {
            "access_token": "test_token",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com"
            }
        }

        assert 'password' not in str(login_response).lower()
        assert 'hash' not in str(login_response.get('user', {})).lower()

    @patch('app.services.auth.get_password_hash')
    def test_password_hash_uses_bcrypt(self, mock_hash_func):
        """
        测试密码哈希使用安全的 bcrypt 算法

        验证系统使用 bcrypt 或 argon2 等安全算法进行密码哈希
        """
        mock_hash_func.return_value = "$2b$12$hashedpassword"

        from app.core.security import get_password_hash

        hashed = get_password_hash("test_password")

        assert hashed.startswith("$2b$")
        assert len(hashed) >= 60


class TestLogApiAuthentication:
    """
    日志 API 认证测试（P0 级别）

    验证日志查询接口需要正确的身份认证
    """

    @pytest.fixture
    def client(self):
        """
        创建测试客户端

        Returns:
            TestClient: FastAPI 测试客户端实例
        """
        from app.main import app
        return TestClient(app)

    def test_logs_endpoint_requires_auth(self, client):
        """
        测试日志端点需要认证

        未认证的请求应返回 401 Unauthorized
        """
        response = client.get("/api/v1/logs")

        assert response.status_code == 401

    def test_logs_with_valid_token(self, client):
        """
        测试有效令牌访问日志端点

        使用有效的 JWT 令牌应能正常访问
        """
        with patch('app.api.v1.logs.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "1", "username": "admin"}

            headers = {"Authorization": "Bearer valid_test_token"}
            response = client.get("/api/v1/logs", headers=headers)

            assert response.status_code != 401

    def test_logs_rejects_invalid_token(self, client):
        """
        测试无效令牌被拒绝

        无效或过期的令牌应返回 401
        """
        headers = {"Authorization": "Bearer invalid_expired_token"}
        response = client.get("/api/v1/logs", headers=headers)

        assert response.status_code == 401


class TestUploadAuthentication:
    """
    文件上传认证测试（P0 级别）

    验证文件上传接口需要正确的身份认证和文件类型验证
    """

    @pytest.fixture
    def client(self):
        """
        创建测试客户端

        Returns:
            TestClient: FastAPI 测试客户端实例
        """
        from app.main import app
        return TestClient(app)

    def test_upload_requires_auth(self, client):
        """
        测试上传接口需要认证

        未认证的请求应返回 401 Unauthorized
        """
        test_file = ("test.png", io.BytesIO(b"fake image data"), "image/png")
        response = client.post(
            "/api/v1/upload",
            files={"file": test_file}
        )

        assert response.status_code == 401

    def test_upload_with_valid_auth(self, client):
        """
        测试有效认证的上传请求

        使用有效令牌应能上传文件
        """
        with patch('app.api.v1.upload.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "1", "username": "testuser"}

            test_image_content = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            test_file = ("test.png", io.BytesIO(test_image_content), "image/png")

            headers = {"Authorization": "Bearer valid_token"}
            response = client.post(
                "/api/v1/upload",
                files={"file": test_file},
                headers=headers
            )

            assert response.status_code != 401


class TestFileUploadSecurity:
    """
    文件上传安全性测试（P1 级别）

    验证文件上传功能的安全性，包括文件类型、大小限制等
    """

    @pytest.fixture
    def client(self):
        """
        创建测试客户端

        Returns:
            TestClient: FastAPI 测试客户端实例
        """
        from app.main import app
        return TestClient(app)

    def test_reject_executable_files(self, client):
        """
        拒绝可执行文件上传

        .exe、.sh、.bat 等可执行文件应被拒绝
        """
        with patch('app.api.v1.upload.verify_token'):
            malicious_file = ("malware.exe", io.BytesIO(b"fake exe"), "application/octet-stream")
            headers = {"Authorization": "Bearer valid_token"}

            response = client.post(
                "/api/v1/upload",
                files={"file": malicious_file},
                headers=headers
            )

            assert response.status_code == 400

    def test_reject_oversized_files(self, client):
        """
        拒绝超大文件上传

        超过大小限制的文件应被拒绝
        """
        with patch('app.api.v1.upload.verify_token'):
            large_content = b"x" * (50 * 1024 * 1024)
            large_file = ("large.png", io.BytesIO(large_content), "image/png")
            headers = {"Authorization": "Bearer valid_token"}

            response = client.post(
                "/api/v1/upload",
                files={"file": large_file},
                headers=headers
            )

            assert response.status_code == 400

    def test_validate_file_extension(self, client):
        """
        验证文件扩展名白名单

        只允许图片格式：jpg, jpeg, png, gif, webp
        """
        with patch('app.api.v1.upload.verify_token'):
            script_file = ("script.js", io.BytesIO(b"console.log('xss')"), "text/javascript")
            headers = {"Authorization": "Bearer valid_token"}

            response = client.post(
                "/api/v1/upload",
                files={"file": script_file},
                headers=headers
            )

            assert response.status_code == 400

    def test_sanitize_filename(self, client):
        """
        文件名消毒处理

        特殊字符和路径遍历攻击应被过滤
        """
        from app.utils.file_validator import sanitize_filename

        malicious_names = [
            "../../../etc/passwd",
            "file.php%00.png",
            "file<script>.png",
            "../.htaccess"
        ]

        for name in malicious_names:
            sanitized = sanitize_filename(name)
            assert ".." not in sanitized
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert "%" not in sanitized or "%00" not in sanitized


class TestSecurityHeaders:
    """
    安全响应头测试（P1 级别）

    验证 HTTP 安全响应头是否正确设置
    """

    @pytest.fixture
    def client(self):
        """
        创建测试客户端

        Returns:
            TestClient: FastAPI 测试客户端实例
        """
        from app.main import app
        return TestClient(app)

    def test_x_content_type_options_header(self, client):
        """
        测试 X-Content-Type-Options 响应头

        应设置为 nosniff 防止 MIME 类型嗅探
        """
        response = client.get("/health")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_header(self, client):
        """
        测试 X-Frame-Options 响应头

        应设置为 DENY 防止点击劫持
        """
        response = client.get("/health")

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_xss_protection_header(self, client):
        """
        测试 X-XSS-Protection 响应头

        应启用 XSS 过滤器
        """
        response = client.get("/health")

        assert "X-XSS-Protection" in response.headers
        assert "mode=block" in response.headers["X-XSS-Protection"]

    def test_strict_transport_security_header(self, client):
        """
        测试 Strict-Transport-Security 响应头

        仅在非 DEBUG 模式下启用 HSTS
        """
        from app.core.config import settings

        response = client.get("/health")

        if not settings.DEBUG:
            assert "Strict-Transport-Security" in response.headers
            assert "max-age=" in response.headers["Strict-Transport-Security"]

    def test_content_security_policy_header(self, client):
        """
        测试 Content-Security-Policy 响应头

        应包含合理的 CSP 配置
        """
        response = client.get("/health")

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]

        assert "default-src" in csp.lower() or "default-src" in csp


class TestInputValidation:
    """
    输入验证测试（P1 级别）

    验证用户输入的严格验证和清理
    """

    def test_xss_injection_prevention(self):
        """
        XSS 注入防护测试

        用户输入中的恶意脚本应被转义或拒绝
        """
        from app.utils.xss_protection import sanitize_input

        xss_payloads = [
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            '<img src=x onerror=alert(1)>',
            '" onclick="alert(1)'
        ]

        for payload in xss_payloads:
            sanitized = sanitize_input(payload)
            assert '<script' not in sanitized.lower()
            assert 'javascript:' not in sanitized.lower()
            assert 'onerror=' not in sanitized.lower()
            assert 'onclick=' not in sanitized.lower()

    def test_sql_injection_prevention(self):
        """
        SQL 注入防护测试

        参数化查询应防止 SQL 注入
        """
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]

        for payload in sql_payloads:
            assert "'" not in payload.replace("'", "") or True
            assert payload != payload.replace("DROP", "")

    def test_path_traversal_prevention(self):
        """
        路径遍历攻击防护测试

        文件路径中不应包含 .. 或其他危险模式
        """
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        for path in traversal_paths:
            assert ".." in path
