# -*- coding: utf-8 -*-
"""
WheatAgent API 中间件模块

提供以下功能:
- 请求日志记录
- 请求限流
- 响应缓存
- 安全检查
"""
import time
import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from collections import defaultdict
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    请求日志记录中间件
    
    记录所有API请求的详细信息
    """
    
    def __init__(self, app, log_file: str = "logs/api_requests.log"):
        """
        初始化请求日志中间件
        
        :param app: FastAPI应用实例
        :param log_file: 日志文件路径
        """
        super().__init__(app)
        self.log_file = log_file
        self._lock = threading.Lock()
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并记录日志"""
        start_time = time.time()
        
        request_info = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        try:
            response = await call_next(request)
            
            request_info["status_code"] = response.status_code
            request_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            request_info["success"] = 200 <= response.status_code < 400
            
            self._log_request(request_info)
            
            return response
            
        except Exception as e:
            request_info["error"] = str(e)
            request_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            request_info["success"] = False
            
            self._log_request(request_info)
            
            raise
    
    def _log_request(self, info: Dict):
        """写入日志文件"""
        try:
            import os
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            with self._lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(info, ensure_ascii=False) + "\n")
        except Exception:
            pass


class RateLimiter:
    """
    请求限流器
    
    基于IP地址的滑动窗口限流
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        """
        初始化限流器
        
        :param requests_per_minute: 每分钟最大请求数
        :param requests_per_hour: 每小时最大请求数
        :param burst_limit: 突发请求限制
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        self._minute_requests: Dict[str, list] = defaultdict(list)
        self._hour_requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, client_ip: str) -> tuple:
        """
        检查请求是否允许
        
        :param client_ip: 客户端IP地址
        :return: (是否允许, 剩余请求数, 重置时间)
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        with self._lock:
            self._minute_requests[client_ip] = [
                t for t in self._minute_requests[client_ip] if t > minute_ago
            ]
            self._hour_requests[client_ip] = [
                t for t in self._hour_requests[client_ip] if t > hour_ago
            ]
            
            minute_count = len(self._minute_requests[client_ip])
            hour_count = len(self._hour_requests[client_ip])
            
            if minute_count >= self.requests_per_minute:
                reset_in = int(60 - (now - self._minute_requests[client_ip][0]))
                return False, 0, reset_in
            
            if hour_count >= self.requests_per_hour:
                reset_in = int(3600 - (now - self._hour_requests[client_ip][0]))
                return False, 0, reset_in
            
            self._minute_requests[client_ip].append(now)
            self._hour_requests[client_ip].append(now)
            
            remaining = min(
                self.requests_per_minute - minute_count - 1,
                self.requests_per_hour - hour_count - 1
            )
            
            return True, remaining, 60
    
    def get_stats(self, client_ip: str) -> Dict:
        """
        获取客户端请求统计
        
        :param client_ip: 客户端IP地址
        :return: 统计信息
        """
        now = time.time()
        
        with self._lock:
            minute_count = len([
                t for t in self._minute_requests[client_ip] if t > now - 60
            ])
            hour_count = len([
                t for t in self._hour_requests[client_ip] if t > now - 3600
            ])
        
        return {
            "client_ip": client_ip,
            "requests_last_minute": minute_count,
            "requests_last_hour": hour_count,
            "minute_limit": self.requests_per_minute,
            "hour_limit": self.requests_per_hour
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求限流中间件
    """
    
    def __init__(self, app, rate_limiter: RateLimiter = None):
        """
        初始化限流中间件
        
        :param app: FastAPI应用实例
        :param rate_limiter: 限流器实例
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        
        self.exempt_paths = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        }
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并限流"""
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        allowed, remaining, reset_in = self.rate_limiter.is_allowed(client_ip)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": reset_in
                },
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_in),
                    "Retry-After": str(reset_in)
                }
            )
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class ResponseCache:
    """
    响应缓存
    
    基于请求路径和参数的内存缓存
    """
    
    def __init__(self, default_ttl: int = 60, max_size: int = 1000):
        """
        初始化响应缓存
        
        :param default_ttl: 默认缓存时间（秒）
        :param max_size: 最大缓存条目数
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def _generate_key(self, method: str, path: str, params: str = "") -> str:
        """
        生成缓存键
        
        :param method: HTTP方法
        :param path: 请求路径
        :param params: 请求参数
        :return: 缓存键
        """
        content = f"{method}:{path}:{params}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, method: str, path: str, params: str = "") -> Optional[Dict]:
        """
        获取缓存响应
        
        :param method: HTTP方法
        :param path: 请求路径
        :param params: 请求参数
        :return: 缓存数据或None
        """
        key = self._generate_key(method, path, params)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry["expires"]:
                    entry["hits"] += 1
                    return entry["data"]
                else:
                    del self._cache[key]
        
        return None
    
    def set(
        self,
        method: str,
        path: str,
        data: Dict,
        params: str = "",
        ttl: int = None
    ):
        """
        设置缓存响应
        
        :param method: HTTP方法
        :param path: 请求路径
        :param data: 响应数据
        :param params: 请求参数
        :param ttl: 缓存时间
        """
        key = self._generate_key(method, path, params)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = {
                "data": data,
                "expires": time.time() + ttl,
                "created": time.time(),
                "hits": 0
            }
    
    def _evict_oldest(self):
        """淘汰最旧的缓存条目"""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["created"]
        )
        del self._cache[oldest_key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        with self._lock:
            total_hits = sum(entry["hits"] for entry in self._cache.values())
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "total_hits": total_hits
            }


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全检查中间件
    
    提供基本的安全防护
    """
    
    def __init__(self, app, max_content_length: int = 50 * 1024 * 1024):
        """
        初始化安全中间件
        
        :param app: FastAPI应用实例
        :param max_content_length: 最大请求体大小（字节）
        """
        super().__init__(app)
        self.max_content_length = max_content_length
        
        self.blocked_user_agents = {
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "zap"
        }
        
        self.suspicious_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            "eval(",
            "exec(",
            "../",
            "..\\",
            "union select",
            "or 1=1",
            "drop table"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并进行安全检查"""
        user_agent = request.headers.get("user-agent", "").lower()
        
        for blocked in self.blocked_user_agents:
            if blocked in user_agent:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "success": False,
                        "message": "访问被拒绝"
                    }
                )
        
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success": False,
                    "message": f"请求体过大，最大允许 {self.max_content_length // 1024 // 1024}MB"
                }
            )
        
        query_params = str(request.query_params)
        for pattern in self.suspicious_patterns:
            if pattern.lower() in query_params.lower():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "请求包含非法字符"
                    }
                )
        
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def cached_response(ttl: int = 60):
    """
    响应缓存装饰器
    
    :param ttl: 缓存时间（秒）
    """
    cache = ResponseCache(default_ttl=ttl)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            params = json.dumps({"args": str(args), "kwargs": kwargs}, default=str)
            
            cached = cache.get("GET", func.__name__, params)
            if cached:
                return cached
            
            result = await func(*args, **kwargs)
            
            if isinstance(result, dict):
                cache.set("GET", func.__name__, result, params)
            
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


global_rate_limiter = RateLimiter()
global_response_cache = ResponseCache()
