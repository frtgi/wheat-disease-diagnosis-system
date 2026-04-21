"""
性能优化配置文件
定义缓存过期策略和其他性能相关配置
"""
from typing import Dict, Any


class CacheConfig:
    """缓存配置类"""

    USER_INFO_TTL = 43200
    USER_INFO_MAX_SIZE = 1000

    DIAGNOSIS_HISTORY_TTL = 300
    DIAGNOSIS_HISTORY_MAX_SIZE = 2000

    KNOWLEDGE_QUERY_TTL = 21600
    KNOWLEDGE_QUERY_MAX_SIZE = 500

    DISEASE_INFO_TTL = 86400
    DISEASE_INFO_MAX_SIZE = 300

    DIAGNOSIS_RESULT_TTL = 86400
    DIAGNOSIS_RESULT_MAX_SIZE = 1000

    TOKEN_BLACKLIST_TTL = 86400

    LOGIN_ATTEMPTS_TTL = 1800


class DatabaseConfig:
    """数据库配置类"""

    SLOW_QUERY_THRESHOLD = 1.0

    QUERY_TIMEOUT = 30

    CONNECTION_POOL_SIZE = 10
    CONNECTION_MAX_OVERFLOW = 20
    CONNECTION_TIMEOUT = 30
    CONNECTION_RECYCLE = 3600

    ENABLE_QUERY_MONITORING = True

    ENABLE_EAGER_LOADING = True


class PerformanceConfig:
    """性能配置类"""

    ENABLE_RESPONSE_CACHE = True

    ENABLE_QUERY_OPTIMIZATION = True

    ENABLE_COMPRESSION = False

    MAX_PAGE_SIZE = 1000
    DEFAULT_PAGE_SIZE = 20

    API_RATE_LIMIT = "100/minute"

    ENABLE_METRICS = True


CACHE_EXPIRY_STRATEGY: Dict[str, Any] = {
    "user_info": {
        "ttl": CacheConfig.USER_INFO_TTL,
        "description": "用户信息缓存，12 小时过期",
        "invalidate_on": ["user_update", "user_delete", "password_change"]
    },
    "diagnosis_history": {
        "ttl": CacheConfig.DIAGNOSIS_HISTORY_TTL,
        "description": "诊断历史缓存，5 分钟过期",
        "invalidate_on": ["new_diagnosis", "diagnosis_update", "diagnosis_delete"]
    },
    "knowledge_query": {
        "ttl": CacheConfig.KNOWLEDGE_QUERY_TTL,
        "description": "知识图谱查询缓存，6 小时过期",
        "invalidate_on": ["knowledge_update", "knowledge_delete"]
    },
    "disease_info": {
        "ttl": CacheConfig.DISEASE_INFO_TTL,
        "description": "疾病信息缓存，24 小时过期",
        "invalidate_on": ["disease_update", "disease_delete"]
    },
    "diagnosis_result": {
        "ttl": CacheConfig.DIAGNOSIS_RESULT_TTL,
        "description": "诊断结果缓存，24 小时过期",
        "invalidate_on": []
    }
}


PERFORMANCE_THRESHOLDS: Dict[str, Any] = {
    "api_response_time": {
        "excellent": 100,
        "good": 300,
        "acceptable": 500,
        "slow": 1000,
        "critical": 2000
    },
    "cache_hit_rate": {
        "excellent": 90,
        "good": 80,
        "acceptable": 60,
        "poor": 40
    },
    "database_query_time": {
        "excellent": 50,
        "good": 100,
        "acceptable": 500,
        "slow": 1000
    }
}


def get_cache_ttl(cache_type: str) -> int:
    """
    获取缓存 TTL

    Args:
        cache_type: 缓存类型

    Returns:
        TTL（秒）
    """
    return CACHE_EXPIRY_STRATEGY.get(cache_type, {}).get("ttl", 3600)


def should_enable_cache(cache_type: str) -> bool:
    """
    判断是否启用缓存

    Args:
        cache_type: 缓存类型

    Returns:
        是否启用
    """
    return PerformanceConfig.ENABLE_RESPONSE_CACHE


def get_performance_threshold(metric: str, level: str) -> int:
    """
    获取性能阈值

    Args:
        metric: 性能指标
        level: 性能等级

    Returns:
        阈值
    """
    return PERFORMANCE_THRESHOLDS.get(metric, {}).get(level, 0)
