# 后端优化计划

## 概述

对 `src/web/backend` 目录下的后端代码进行了全面分析，识别出以下主要优化领域：

---

## 1. 数据库性能优化

### 1.1 连接池优化
**文件**: [app/core/database.py](file:///D:/Project/wheatagent/src/web/backend/app/core/database.py)

**当前问题**:
- 连接池参数固定，未根据负载动态调整
- 缺少连接健康检查和自动重连机制
- 异步和同步引擎配置不一致

**优化方案**:
```python
# 动态连接池配置
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "60")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
    echo=settings.DEBUG,
    echo_pool=settings.DEBUG,
)
```

### 1.2 索引优化
**文件**: [app/models/diagnosis.py](file:///D:/Project/wheatagent/src/web/backend/app/models/diagnosis.py)

**当前问题**:
- `disease_name` 字段缺少索引，影响按病害名称查询
- `created_at` 已有索引但缺少复合索引
- 缺少全文索引支持症状搜索

**优化方案**:
```python
# 添加复合索引
Index('idx_user_created', 'user_id', 'created_at'),
Index('idx_disease_created', 'disease_name', 'created_at'),
Index('idx_status_created', 'status', 'created_at'),
```

### 1.3 查询优化
**文件**: [app/services/diagnosis.py](file:///D:/Project/wheatagent/src/web/backend/app/services/diagnosis.py)

**当前问题**:
- 存在 N+1 查询问题（用户-诊断记录关联）
- 缺少查询预加载（joinedload）
- 分页查询未优化

**优化方案**:
```python
from sqlalchemy.orm import joinedload

def get_user_diagnoses(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(Diagnosis).options(
        joinedload(Diagnosis.disease)
    ).filter(
        Diagnosis.user_id == user_id
    ).order_by(
        Diagnosis.created_at.desc()
    ).offset(skip).limit(limit).all()
```

---

## 2. 缓存系统优化

### 2.1 Redis 连接池
**文件**: [app/core/redis_client.py](file:///D:/Project/wheatagent/src/web/backend/app/core/redis_client.py)

**当前问题**:
- 缺少连接池配置
- 无连接超时和重试机制
- 单例模式未处理连接断开重连

**优化方案**:
```python
async def get_async_client(cls) -> aioredis.Redis:
    if cls._async_instance is None:
        cls._async_instance = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            max_connections=50,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return cls._async_instance
```

### 2.2 认证缓存
**文件**: [app/services/auth.py](file:///D:/Project/wheatagent/src/web/backend/app/services/auth.py)

**当前问题**:
- 用户认证每次都查询数据库
- 无 Token 黑名单缓存
- 会话验证未缓存

**优化方案**:
```python
async def get_cached_user(db: Session, user_id: int, cache: CacheService) -> Optional[User]:
    # 先查缓存
    cached_user = await cache.get_user_info(user_id)
    if cached_user:
        return User(**cached_user)
    
    # 缓存未命中，查数据库
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        await cache.set_user_info(user_id, {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        })
    return user
```

### 2.3 诊断结果缓存
**文件**: [app/services/diagnosis.py](file:///D:/Project/wheatagent/src/web/backend/app/services/diagnosis.py)

**当前问题**:
- 缓存服务已存在但未在诊断流程中使用
- 无图像特征缓存
- 无知识图谱查询缓存

**优化方案**:
```python
async def diagnose_image(self, image_path: str, symptoms: Optional[str] = None):
    # 计算图像 MD5 作为缓存键
    image_md5 = self._calculate_image_md5(image_path)
    
    # 检查缓存
    cached_result = await cache_service.get_diagnosis(image_md5)
    if cached_result:
        logger.info(f"命中诊断缓存：{image_md5}")
        return DiagnosisResult(**cached_result)
    
    # 执行诊断
    result = await self._do_diagnose(image_path, symptoms)
    
    # 缓存结果
    await cache_service.set_diagnosis(image_md5, asdict(result))
    
    return result
```

---

## 3. API 性能优化

### 3.1 请求限流
**文件**: [app/main.py](file:///D:/Project/wheatagent/src/web/backend/app/main.py)

**当前问题**:
- 无请求限流保护
- 认证接口易受暴力攻击
- AI 诊断接口无并发限制

**优化方案**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 在路由中应用
@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    ...
```

### 3.2 响应压缩
**文件**: [app/main.py](file:///D:/Project/wheatagent/src/web/backend/app/main.py)

**优化方案**:
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3.3 分页优化
**文件**: [app/api/v1/diagnosis.py](file:///D:/Project/wheatagent/src/web/backend/app/api/v1/diagnosis.py)

**当前问题**:
- 分页未返回总数，前端无法正确分页
- 无游标分页支持大数据量

**优化方案**:
```python
from typing import Tuple

async def get_diagnosis_records_paginated(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 20
) -> Tuple[List[Diagnosis], int]:
    query = db.query(Diagnosis).filter(Diagnosis.user_id == user_id)
    
    total = query.count()
    records = query.order_by(Diagnosis.created_at.desc()).offset(skip).limit(limit).all()
    
    return records, total
```

---

## 4. 安全性增强

### 4.1 安全头中间件
**文件**: [app/main.py](file:///D:/Project/wheatagent/src/web/backend/app/main.py)

**优化方案**:
```python
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# 生产环境启用 HTTPS 重定向
if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)

# 安全头中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### 4.2 输入验证增强
**文件**: [app/schemas/diagnosis.py](file:///D:/Project/wheatagent/src/web/backend/app/schemas/diagnosis.py)

**优化方案**:
```python
from pydantic import validator, Field
import re

class DiagnosisCreate(BaseModel):
    symptoms: str = Field(..., min_length=10, max_length=2000)
    
    @validator('symptoms')
    def sanitize_symptoms(cls, v):
        # 移除潜在危险字符
        v = re.sub(r'<[^>]*>', '', v)  # 移除 HTML 标签
        v = re.sub(r'[\'";\\]', '', v)  # 移除 SQL 注入字符
        return v.strip()
```

### 4.3 JWT 安全增强
**文件**: [app/core/security.py](file:///D:/Project/wheatagent/src/web/backend/app/core/security.py)

**当前问题**:
- JWT 密钥默认值不安全
- 无 Token 黑名单机制
- 缺少 Token 刷新策略

**优化方案**:
```python
import secrets

# 生成安全的 JWT 密钥
def generate_jwt_secret() -> str:
    return secrets.token_urlsafe(64)

# Token 黑名单（使用 Redis）
async def is_token_revoked(token: str, redis: aioredis.Redis) -> bool:
    return await redis.exists(f"revoked_token:{token}")

async def revoke_token(token: str, redis: aioredis.Redis, expire: int = 86400):
    await redis.setex(f"revoked_token:{token}", expire, "1")
```

---

## 5. 错误处理优化

### 5.1 统一异常处理
**文件**: [app/core/response.py](file:///D:/Project/wheatagent/src/web/backend/app/core/response.py)

**优化方案**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"应用异常: {exc.code} - {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试"
        }
    )
```

### 5.2 结构化日志
**文件**: [app/main.py](file:///D:/Project/wheatagent/src/web/backend/app/main.py)

**优化方案**:
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

---

## 6. AI 服务优化

### 6.1 模型加载优化
**文件**: [app/services/qwen_service.py](file:///D:/Project/wheatagent/src/web/backend/app/services/qwen_service.py)

**当前问题**:
- 模型同步加载阻塞启动
- 无模型预热机制
- 缺少 GPU 内存管理

**优化方案**:
```python
import torch

class QwenService:
    def __init__(self, ...):
        self._model_loaded = asyncio.Event()
        
    async def load_model_async(self):
        """异步加载模型"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
        self._model_loaded.set()
        
    def _warmup(self):
        """模型预热"""
        if not self.is_loaded:
            return
        try:
            with torch.no_grad():
                dummy_input = "测试输入"
                _ = self._generate_text(dummy_input)
            logger.info("模型预热完成")
        except Exception as e:
            logger.warning(f"模型预热失败: {e}")
            
    def clear_cache(self):
        """清理 GPU 缓存"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
```

### 6.2 推理并发控制
**文件**: [app/services/diagnosis.py](file:///D:/Project/wheatagent/src/web/backend/app/services/diagnosis.py)

**优化方案**:
```python
from asyncio import Semaphore

# 限制并发推理数量
INFERENCE_SEMAPHORE = Semaphore(3)

async def diagnose_image(self, image_path: str, symptoms: Optional[str] = None):
    async with INFERENCE_SEMAPHORE:
        # 执行诊断
        ...
```

---

## 7. 代码质量优化

### 7.1 依赖注入模式
**文件**: [app/core/dependencies.py](file:///D:/Project/wheatagent/src/web/backend/app/core/dependencies.py)（新建）

**优化方案**:
```python
from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session
from .database import SyncSessionLocal
from .redis_client import get_redis
from ..services.cache import CacheService

@lru_cache()
def get_cache_service() -> CacheService:
    return CacheService()

def get_db() -> Generator[Session, None, None]:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
) -> User:
    # 使用缓存的用户验证
    ...
```

### 7.2 配置管理优化
**文件**: [app/core/config.py](file:///D:/Project/wheatagent/src/web/backend/app/core/config.py)

**优化方案**:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 60
    DB_POOL_RECYCLE: int = 1800
    
    # Redis 配置
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    
    # JWT 配置
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # 限流配置
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_API: str = "100/minute"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 8. 监控与可观测性

### 8.1 健康检查增强
**文件**: [app/api/v1/health.py](file:///D:/Project/wheatagent/src/web/backend/app/api/v1/health.py)

**优化方案**:
```python
@router.get("/health/detailed")
async def detailed_health_check(
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_async_redis)
):
    checks = {}
    
    # 数据库检查
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis 检查
    try:
        start = time.time()
        await redis.ping()
        latency = (time.time() - start) * 1000
        checks["redis"] = {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # AI 模型检查
    checks["ai_models"] = {
        "yolo": {"loaded": yolo_service.is_loaded if yolo_service else False},
        "qwen": {"loaded": qwen_service.is_loaded if qwen_service else False}
    }
    
    all_healthy = all(c.get("status") == "healthy" or c.get("loaded") for c in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
```

### 8.2 性能指标收集
**文件**: [app/api/v1/metrics.py](file:///D:/Project/wheatagent/src/web/backend/app/api/v1/metrics.py)

**优化方案**:
```python
from prometheus_client import Counter, Histogram, generate_latest

# 定义指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

DIAGNOSIS_COUNT = Counter(
    'diagnosis_total',
    'Total diagnosis requests',
    ['type', 'result']
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(latency)
    
    return response
```

---

## 实施优先级

| 优先级 | 优化项 | 预期收益 | 工作量 |
|--------|--------|----------|--------|
| P0 | 数据库索引优化 | 高 | 低 |
| P0 | 认证缓存 | 高 | 中 |
| P0 | 请求限流 | 高 | 低 |
| P1 | Redis 连接池 | 中 | 低 |
| P1 | 统一异常处理 | 中 | 中 |
| P1 | 安全头中间件 | 中 | 低 |
| P2 | AI 服务并发控制 | 中 | 中 |
| P2 | 分页优化 | 中 | 低 |
| P2 | 结构化日志 | 低 | 中 |
| P3 | 性能指标收集 | 低 | 中 |

---

## 实施步骤

### 第一阶段（P0 - 紧急）
1. 添加数据库索引
2. 实现认证缓存
3. 添加请求限流中间件

### 第二阶段（P1 - 重要）
4. 优化 Redis 连接池
5. 实现统一异常处理
6. 添加安全头中间件

### 第三阶段（P2 - 改进）
7. AI 服务并发控制
8. 分页查询优化
9. 结构化日志

### 第四阶段（P3 - 监控）
10. 性能指标收集
11. 健康检查增强
12. 监控告警配置

---

## 测试验证

### 功能测试
- 运行现有测试套件确保功能正确
- 添加缓存相关的单元测试
- 添加限流相关的集成测试

### 性能测试
- 使用 Locust 进行负载测试
- 对比优化前后的响应时间
- 监控资源使用情况

### 安全测试
- SQL 注入测试
- XSS 攻击测试
- 限流有效性测试
