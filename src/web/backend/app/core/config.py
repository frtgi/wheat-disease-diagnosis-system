"""
应用配置模块
从环境变量加载配置信息，提供统一的配置管理
"""
import os
import logging
import secrets
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """应用配置类"""
    
    _jwt_secret_key_cache: str = None
    
    APP_NAME: str = "基于多模态融合的小麦病害诊断系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "3306"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "wheat_agent_db")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "root")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    @property
    def DATABASE_URL(self) -> str:
        """获取数据库连接 URL"""
        return (
            f"mysql+aiomysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            f"?charset=utf8mb4"
        )
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    @property
    def REDIS_URL(self) -> str:
        """获取 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    
    @property
    def JWT_SECRET_KEY(self) -> str:
        """
        获取 JWT 密钥
        从环境变量读取，如果不存在则在开发环境生成临时密钥，生产环境抛出异常
        使用缓存机制确保密钥在应用生命周期内保持一致
        """
        if Settings._jwt_secret_key_cache is not None:
            return Settings._jwt_secret_key_cache
        
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        if not jwt_secret:
            if self.DEBUG:
                jwt_secret = secrets.token_urlsafe(32)
                logger.warning("JWT_SECRET_KEY 未配置，已生成临时密钥（仅限开发环境）")
            else:
                raise ValueError("生产环境必须配置 JWT_SECRET_KEY 环境变量")
        
        Settings._jwt_secret_key_cache = jwt_secret
        return jwt_secret
    
    _cors_origins = os.environ.get("CORS_ORIGINS", "")
    if _cors_origins:
        CORS_ORIGINS: list = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
        if "*" in CORS_ORIGINS:
            logger.warning("⚠️ 检测到 CORS 配置中包含通配符 '*'，这可能导致安全风险")
            CORS_ORIGINS = [origin for origin in CORS_ORIGINS if origin != "*"]
            if not CORS_ORIGINS:
                logger.error("❌ CORS 配置无效：移除通配符后无有效域名")
                raise ValueError("CORS 配置无效：必须指定至少一个有效的允许域名")
        logger.info(f"✅ CORS 配置已从环境变量加载：{len(CORS_ORIGINS)} 个允许的域名")
        for idx, origin in enumerate(CORS_ORIGINS, 1):
            logger.info(f"   {idx}. {origin}")
    else:
        CORS_ORIGINS: list = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
        ]
        logger.warning("⚠️ CORS_ORIGINS 环境变量未配置，使用默认的 localhost 域名")
        logger.info("💡 建议：在生产环境中通过 CORS_ORIGINS 环境变量配置允许的域名")
    
    CORS_ALLOW_CREDENTIALS: bool = os.environ.get("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_MAX_AGE: int = int(os.environ.get("CORS_MAX_AGE", "600"))
    
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "wheatagent")
    
    @property
    def MINIO_CONFIGURED(self) -> bool:
        """
        检查 MinIO 是否正确配置
        验证访问密钥和秘密密钥是否都已设置
        """
        return bool(self.MINIO_ACCESS_KEY and self.MINIO_SECRET_KEY)
    
    FUSION_DEGRADATION_FACTOR: float = float(os.getenv("FUSION_DEGRADATION_FACTOR", "0.9"))
    FUSION_VISUAL_WEIGHT: float = float(os.getenv("FUSION_VISUAL_WEIGHT", "0.4"))
    FUSION_TEXTUAL_WEIGHT: float = float(os.getenv("FUSION_TEXTUAL_WEIGHT", "0.35"))
    FUSION_KNOWLEDGE_WEIGHT: float = float(os.getenv("FUSION_KNOWLEDGE_WEIGHT", "0.25"))
    
    INFERENCE_CACHE_TTL: int = int(os.getenv("INFERENCE_CACHE_TTL", str(24 * 3600)))
    INFERENCE_CACHE_ENABLE_SIMILAR_SEARCH: bool = os.getenv("INFERENCE_CACHE_ENABLE_SIMILAR_SEARCH", "true").lower() == "true"
    INFERENCE_CACHE_SIMILARITY_THRESHOLD: int = int(os.getenv("INFERENCE_CACHE_SIMILARITY_THRESHOLD", "5"))
    INFERENCE_CACHE_ENABLED: bool = os.getenv("INFERENCE_CACHE_ENABLED", "true").lower() == "true"
    
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))
    NEO4J_CONNECTION_TIMEOUT: int = int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30"))
    
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
    RATE_LIMIT_DIAGNOSIS: str = os.getenv("RATE_LIMIT_DIAGNOSIS", "10/minute")
    RATE_LIMIT_UPLOAD: str = os.getenv("RATE_LIMIT_UPLOAD", "20/minute")

    # SSE 流式响应相关配置
    SSE_TIMEOUT_SECONDS: int = int(os.getenv("SSE_TIMEOUT_SECONDS", "120"))
    SSE_HEARTBEAT_INTERVAL: int = int(os.getenv("SSE_HEARTBEAT_INTERVAL", "15"))
    SSE_BACKPRESSURE_QUEUE_SIZE: int = int(os.getenv("SSE_BACKPRESSURE_QUEUE_SIZE", "100"))

    # GPU 并发控制与诊断队列配置
    MAX_CONCURRENT_DIAGNOSIS: int = int(os.getenv("MAX_CONCURRENT_DIAGNOSIS", "3"))
    MAX_DIAGNOSIS_QUEUE_SIZE: int = int(os.getenv("MAX_DIAGNOSIS_QUEUE_SIZE", "10"))
    DIAGNOSIS_QUEUE_TIMEOUT: int = int(os.getenv("DIAGNOSIS_QUEUE_TIMEOUT", "300"))

    # GPU 显存监控阈值
    GPU_MEMORY_THRESHOLD: float = float(os.getenv("GPU_MEMORY_THRESHOLD", "0.90"))
    
    def validate_minio_config(self) -> None:
        """
        验证 MinIO 配置
        生产环境强制要求配置凭据，开发环境显示警告
        """
        if not self.MINIO_CONFIGURED:
            if self.DEBUG:
                logger.warning(
                    "⚠️ MinIO 凭据未配置（MINIO_ACCESS_KEY/MINIO_SECRET_KEY），"
                    "对象存储功能将不可用。开发环境请设置环境变量以启用 MinIO"
                )
            else:
                raise ValueError(
                    "生产环境必须配置 MinIO 凭据："
                    "请设置 MINIO_ACCESS_KEY 和 MINIO_SECRET_KEY 环境变量"
                )


settings = Settings()
settings.validate_minio_config()
