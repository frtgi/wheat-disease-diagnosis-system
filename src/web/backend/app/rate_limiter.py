"""
限流器模块
提供 API 请求限流功能
"""
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, HTTPException


if os.getenv("TESTING", "false").lower() == "true":
    limiter = Limiter(key_func=get_remote_address, enabled=False)
else:
    limiter = Limiter(key_func=get_remote_address)


def add_rate_limit_middleware(app: FastAPI):
    """
    为应用添加限流中间件

    参数:
        app: FastAPI 应用实例
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    限流异常处理器

    参数:
        request: 请求对象
        exc: 限流异常

    返回:
        HTTPException: 429 错误响应
    """
    raise HTTPException(
        status_code=429,
        detail=f"请求频率超限，请稍后重试: {exc.detail}"
    )
