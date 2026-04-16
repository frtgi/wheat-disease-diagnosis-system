"""
数据库查询监控模块
提供慢查询日志、查询性能分析等功能
"""
import time
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class QueryMetric:
    """查询指标数据类"""
    query: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    params: Optional[Dict[str, Any]] = None
    caller: Optional[str] = None
    is_slow: bool = False


class QueryMonitor:
    """
    数据库查询监控器
    
    功能：
    1. 记录查询执行时间
    2. 识别慢查询
    3. 统计查询性能指标
    4. 生成性能报告
    """
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """
        初始化查询监控器
        
        Args:
            slow_query_threshold: 慢查询阈值（秒），默认 1 秒
        """
        self.slow_query_threshold = slow_query_threshold
        self._metrics: List[QueryMetric] = []
        self._total_queries = 0
        self._slow_queries = 0
        self._total_time = 0.0
    
    @contextmanager
    def track_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """
        跟踪查询执行的上下文管理器
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Yields:
            None
        """
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            is_slow = duration >= self.slow_query_threshold
            
            metric = QueryMetric(
                query=query,
                duration=duration,
                params=params,
                is_slow=is_slow
            )
            
            self._metrics.append(metric)
            self._total_queries += 1
            self._total_time += duration
            
            if is_slow:
                self._slow_queries += 1
                logger.warning(
                    f"慢查询检测 [{duration:.3f}s]: {query[:200]}..."
                )
    
    def record_query(self, query: str, duration: float, params: Optional[Dict[str, Any]] = None):
        """
        记录查询指标
        
        Args:
            query: SQL 查询语句
            duration: 执行时间（秒）
            params: 查询参数
        """
        is_slow = duration >= self.slow_query_threshold
        
        metric = QueryMetric(
            query=query,
            duration=duration,
            params=params,
            is_slow=is_slow
        )
        
        self._metrics.append(metric)
        self._total_queries += 1
        self._total_time += duration
        
        if is_slow:
            self._slow_queries += 1
            logger.warning(
                f"慢查询检测 [{duration:.3f}s]: {query[:200]}..."
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取查询统计信息
        
        Returns:
            统计信息字典
        """
        avg_time = (
            self._total_time / self._total_queries 
            if self._total_queries > 0 else 0
        )
        
        slow_query_rate = (
            (self._slow_queries / self._total_queries * 100)
            if self._total_queries > 0 else 0
        )
        
        return {
            "total_queries": self._total_queries,
            "slow_queries": self._slow_queries,
            "slow_query_rate": round(slow_query_rate, 2),
            "total_time": round(self._total_time, 3),
            "average_time": round(avg_time, 4),
            "slow_query_threshold": self.slow_query_threshold
        }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取慢查询列表
        
        Args:
            limit: 返回数量限制
        
        Returns:
            慢查询列表
        """
        slow_queries = [
            {
                "query": m.query,
                "duration": round(m.duration, 3),
                "timestamp": m.timestamp.isoformat(),
                "params": m.params
            }
            for m in self._metrics if m.is_slow
        ]
        
        return sorted(slow_queries, key=lambda x: x["duration"], reverse=True)[:limit]
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最耗时的查询
        
        Args:
            limit: 返回数量限制
        
        Returns:
            最耗时查询列表
        """
        all_queries = [
            {
                "query": m.query,
                "duration": round(m.duration, 3),
                "timestamp": m.timestamp.isoformat(),
                "is_slow": m.is_slow
            }
            for m in self._metrics
        ]
        
        return sorted(all_queries, key=lambda x: x["duration"], reverse=True)[:limit]
    
    def clear(self):
        """清空统计数据"""
        self._metrics.clear()
        self._total_queries = 0
        self._slow_queries = 0
        self._total_time = 0.0
    
    def export_report(self) -> str:
        """
        导出性能报告
        
        Returns:
            JSON 格式的报告
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_stats(),
            "slow_queries": self.get_slow_queries(),
            "top_queries": self.get_top_queries()
        }
        
        return json.dumps(report, ensure_ascii=False, indent=2)


# 全局查询监控器实例
query_monitor = QueryMonitor(slow_query_threshold=1.0)


def get_query_monitor() -> QueryMonitor:
    """
    获取全局查询监控器实例
    
    Returns:
        查询监控器实例
    """
    return query_monitor
