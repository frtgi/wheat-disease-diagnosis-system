"""
XSS 防护工具模块
提供输入转义、验证和安全响应功能
"""
import re
import html
import functools
from typing import Tuple, Any, Dict, List, Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


def sanitize_input(text: str) -> str:
    """
    转义 HTML 特殊字符，防止 XSS 攻击
    
    参数:
        text: 需要转义的文本
        
    返回:
        转义后的文本
        
    示例:
        >>> sanitize_input("<script>alert('XSS')</script>")
        '&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;'
    """
    if not text:
        return text
    
    return html.escape(text)


def sanitize_dict(data: Dict[str, Any], fields_to_sanitize: List[str] = None) -> Dict[str, Any]:
    """
    转义字典中指定字段的 HTML 特殊字符
    
    参数:
        data: 需要处理的字典
        fields_to_sanitize: 需要转义的字段列表，如果为 None 则转义所有字符串字段
        
    返回:
        处理后的字典
        
    示例:
        >>> data = {"username": "<script>alert('XSS')</script>", "email": "test@test.com"}
        >>> sanitize_dict(data, ["username"])
        {'username': '&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;', 'email': 'test@test.com'}
    """
    sanitized = data.copy()
    
    for key, value in sanitized.items():
        if fields_to_sanitize is None or key in fields_to_sanitize:
            if isinstance(value, str):
                sanitized[key] = sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = sanitize_dict(value, fields_to_sanitize)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_dict(item, fields_to_sanitize) if isinstance(item, dict)
                    else sanitize_input(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
    
    return sanitized


class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    """
    Content-Security-Policy 中间件
    
    添加 CSP 头以防止 XSS 攻击
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


def validate_username(username: str) -> Tuple[bool, str]:
    """
    验证用户名，只允许字母、数字、下划线
    
    参数:
        username: 用户名
        
    返回:
        (是否有效, 错误消息)
        
    示例:
        >>> validate_username("test_user123")
        (True, '')
        >>> validate_username("<script>alert('XSS')</script>")
        (False, '用户名只能包含字母、数字和下划线')
    """
    if not username:
        return False, "用户名不能为空"
    
    if len(username) < 3 or len(username) > 50:
        return False, "用户名长度必须在 3-50 个字符之间"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""


def validate_input_no_html(text: str, field_name: str = "输入") -> Tuple[bool, str]:
    """
    验证输入是否包含 HTML 标签
    
    参数:
        text: 需要验证的文本
        field_name: 字段名称（用于错误消息）
        
    返回:
        (是否有效, 错误消息)
        
    示例:
        >>> validate_input_no_html("正常文本", "症状描述")
        (True, '')
        >>> validate_input_no_html("<script>alert('XSS')</script>", "症状描述")
        (False, '症状描述不能包含 HTML 标签')
    """
    if not text:
        return True, ""
    
    html_pattern = re.compile(r'<[^>]+>')
    if html_pattern.search(text):
        return False, f"{field_name}不能包含 HTML 标签"
    
    return True, ""


class XSSProtectedResponse(JSONResponse):
    """
    XSS 保护的 JSON 响应类
    
    自动转义响应中的 HTML 内容
    """
    
    def render(self, content: Any) -> bytes:
        if isinstance(content, dict):
            content = self._sanitize_content(content)
        return super().render(content)
    
    def _sanitize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """递归转义字典中的字符串值"""
        sanitized = {}
        for key, value in content.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_content(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_content(item) if isinstance(item, dict)
                    else sanitize_input(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


def _sanitize_data(result: Any, fields_to_sanitize: List[str] = None) -> Any:
    """
    对响应数据进行 XSS 清理的辅助函数

    参数:
        result: 需要清理的数据（字典、列表或字符串）
        fields_to_sanitize: 需要转义的字段列表

    返回:
        清理后的数据
    """
    if isinstance(result, dict):
        return sanitize_dict(result, fields_to_sanitize)
    elif isinstance(result, list):
        return [
            sanitize_dict(item, fields_to_sanitize) if isinstance(item, dict)
            else sanitize_input(item) if isinstance(item, str)
            else item
            for item in result
        ]
    elif isinstance(result, str):
        return sanitize_input(result)

    return result


def sanitize_response(fields_to_sanitize: List[str] = None):
    """
    响应数据自动转义装饰器，支持同步和异步函数

    自动转义响应数据中的指定字段，防止 XSS 攻击

    参数:
        fields_to_sanitize: 需要转义的字段列表，如果为 None 则转义所有字符串字段

    返回:
        装饰器函数

    示例:
        >>> @sanitize_response(fields_to_sanitize=["username", "email"])
        >>> def get_user(user_id: int):
        >>>     return {"username": "<script>alert('XSS')</script>", "email": "test@test.com"}
        >>> # 返回: {"username": "&lt;script&gt;alert('XSS')&lt;/script&gt;", "email": "test@test.com"}
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            return _sanitize_data(result, fields_to_sanitize)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return _sanitize_data(result, fields_to_sanitize)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def sanitize_model_fields(data: Any, fields: List[str]) -> Any:
    """
    转义 Pydantic 模型或字典中的指定字段
    
    参数:
        data: Pydantic 模型实例或字典
        fields: 需要转义的字段列表
        
    返回:
        转义后的数据
        
    示例:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        >>>     username: str
        >>>     email: str
        >>> user = User(username="<script>alert('XSS')</script>", email="test@test.com")
        >>> sanitize_model_fields(user, ["username"])
        >>> # user.username 现在是: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
    """
    if hasattr(data, 'model_dump'):
        data_dict = data.model_dump()
        sanitized_dict = sanitize_dict(data_dict, fields)
        
        for field, value in sanitized_dict.items():
            if hasattr(data, field):
                setattr(data, field, value)
        
        return data
    elif isinstance(data, dict):
        return sanitize_dict(data, fields)
    
    return data


def escape_html_in_string(text: str) -> str:
    """
    转义字符串中的 HTML 特殊字符（增强版）
    
    除了基本的 HTML 转义外，还处理一些特殊的 XSS 攻击向量
    
    参数:
        text: 需要转义的文本
        
    返回:
        转义后的文本
        
    示例:
        >>> escape_html_in_string("javascript:alert('XSS')")
        'javascript:alert(&#x27;XSS&#x27;)'
    """
    if not text:
        return text
    
    sanitized = html.escape(text)
    
    dangerous_patterns = [
        (r'javascript:', 'javascript&#58;'),
        (r'vbscript:', 'vbscript&#58;'),
        (r'on\w+\s*=', 'on&#95;'),
    ]
    
    for pattern, replacement in dangerous_patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized
