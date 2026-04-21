"""
诊断日志服务模块

提供结构化日志记录和分析：
1. 诊断请求日志
2. 模型推理日志
3. 错误日志
4. 日志分析（热门病害、成功率统计）
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisLog:
    """诊断日志条目"""
    timestamp: str
    request_id: str
    image_hash: Optional[str]
    symptoms: str
    disease_detected: str
    confidence: float
    processing_time_ms: float
    success: bool
    error: Optional[str] = None
    cache_hit: bool = False
    features: Dict[str, Any] = None


class DiagnosisLogger:
    """诊断日志记录器"""

    def __init__(self, log_dir: Path = None, max_entries: int = 10000):
        """
        初始化诊断日志记录器

        Args:
            log_dir: 日志目录
            max_entries: 最大日志条目数
        """
        self.log_dir = log_dir or Path("logs/diagnosis")
        self.max_entries = max_entries
        self._logs: List[DiagnosisLog] = []
        self._lock = threading.Lock()

        # 统计信息
        self._disease_counter = Counter()
        self._success_counter = defaultdict(int)
        self._total_requests = 0
        self._total_errors = 0

        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_diagnosis(
        self,
        request_id: str,
        image_hash: Optional[str],
        symptoms: str,
        disease_detected: str,
        confidence: float,
        processing_time_ms: float,
        success: bool,
        error: Optional[str] = None,
        cache_hit: bool = False,
        features: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录诊断日志

        Args:
            request_id: 请求 ID
            image_hash: 图像哈希
            symptoms: 症状描述
            disease_detected: 检测到的病害
            confidence: 置信度
            processing_time_ms: 处理时间（毫秒）
            success: 是否成功
            error: 错误信息
            cache_hit: 是否缓存命中
            features: 特征信息
        """
        log_entry = DiagnosisLog(
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            image_hash=image_hash,
            symptoms=symptoms[:200],  # 限制长度
            disease_detected=disease_detected,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            success=success,
            error=error[:500] if error else None,
            cache_hit=cache_hit,
            features=features or {}
        )

        with self._lock:
            # 添加到日志列表
            self._logs.append(log_entry)

            # 更新统计
            self._total_requests += 1
            if success:
                self._success_counter[disease_detected] += 1
                self._disease_counter[disease_detected] += 1
            else:
                self._total_errors += 1

            # 限制日志数量
            if len(self._logs) > self.max_entries:
                self._logs = self._logs[-self.max_entries:]

        # 异步写入文件（不阻塞）
        self._write_to_file(log_entry)

        logger.debug(f"诊断日志已记录：{request_id}, 病害：{disease_detected}")

    def _write_to_file(self, log_entry: DiagnosisLog) -> None:
        """写入日志到文件"""
        try:
            # 按日期分文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"diagnosis_{date_str}.jsonl"

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(log_entry), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"写入日志文件失败：{e}")

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        with self._lock:
            return [asdict(log) for log in self._logs[-limit:]]

    def get_statistics(self, duration_hours: int = 24) -> Dict[str, Any]:
        """获取统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)

        with self._lock:
            # 过滤时间范围内的日志
            filtered_logs = [
                log for log in self._logs
                if datetime.fromisoformat(log.timestamp) >= cutoff_time
            ]

            if not filtered_logs:
                return {
                    "duration_hours": duration_hours,
                    "total_requests": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "success_rate": 0,
                    "cache_hit_rate": 0,
                    "top_diseases": [],
                    "avg_confidence": 0,
                    "avg_processing_time_ms": 0,
                    "error_types": []
                }

            # 计算统计
            total = len(filtered_logs)
            success_count = sum(1 for log in filtered_logs if log.success)
            success_rate = success_count / total * 100 if total > 0 else 0

            # 热门病害
            disease_counts = Counter(
                log.disease_detected for log in filtered_logs if log.success
            )
            top_diseases = disease_counts.most_common(10)

            # 平均置信度
            avg_confidence = (
                sum(log.confidence for log in filtered_logs if log.success) /
                success_count if success_count > 0 else 0
            )

            # 平均处理时间
            avg_time = sum(log.processing_time_ms for log in filtered_logs) / total

            # 缓存命中率
            cache_hits = sum(1 for log in filtered_logs if log.cache_hit)
            cache_hit_rate = cache_hits / total * 100 if total > 0 else 0

            return {
                "duration_hours": duration_hours,
                "total_requests": total,
                "success_count": success_count,
                "error_count": total - success_count,
                "success_rate": round(success_rate, 2),
                "cache_hit_rate": round(cache_hit_rate, 2),
                "top_diseases": [
                    {"disease": disease, "count": count}
                    for disease, count in top_diseases
                ],
                "avg_confidence": round(avg_confidence, 3),
                "avg_processing_time_ms": round(avg_time, 2),
                "error_types": self._get_error_types(filtered_logs)
            }

    def _get_error_types(self, logs: List[DiagnosisLog]) -> List[Dict[str, Any]]:
        """获取错误类型统计"""
        error_logs = [log for log in logs if not log.success and log.error]
        error_counter = Counter(
            log.error[:50] if log.error else "unknown"
            for log in error_logs
        )

        return [
            {"error": error[:100], "count": count}
            for error, count in error_counter.most_common(10)
        ]

    def get_disease_distribution(self, duration_hours: int = 24) -> List[Dict[str, Any]]:
        """获取病害分布"""
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)

        with self._lock:
            filtered_logs = [
                log for log in self._logs
                if datetime.fromisoformat(log.timestamp) >= cutoff_time and log.success
            ]

            disease_counts = Counter(log.disease_detected for log in filtered_logs)
            total = sum(disease_counts.values())

            return [
                {
                    "disease_name": disease,
                    "count": count,
                    "percentage": round(count / total * 100, 2) if total > 0 else 0
                }
                for disease, count in disease_counts.most_common()
            ]

    def get_success_rate_trend(self, duration_hours: int = 24) -> List[Dict[str, Any]]:
        """获取成功率趋势（按小时）"""
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)

        with self._lock:
            filtered_logs = [
                log for log in self._logs
                if datetime.fromisoformat(log.timestamp) >= cutoff_time
            ]

            # 按小时分组
            hourly_stats = defaultdict(lambda: {"total": 0, "success": 0})

            for log in filtered_logs:
                hour = datetime.fromisoformat(log.timestamp).strftime("%Y-%m-%d %H:00")
                hourly_stats[hour]["total"] += 1
                if log.success:
                    hourly_stats[hour]["success"] += 1

            # 计算每小时成功率
            trend = []
            for hour, stats in sorted(hourly_stats.items()):
                trend.append({
                    "hour": hour,
                    "total_requests": stats["total"],
                    "success_count": stats["success"],
                    "success_rate": round(stats["success"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0
                })

            return trend

    def clear(self) -> None:
        """清空日志"""
        with self._lock:
            self._logs.clear()
            self._disease_counter.clear()
            self._success_counter.clear()
            self._total_requests = 0
            self._total_errors = 0

        logger.info("诊断日志已清空")


# 全局诊断日志记录器实例
diagnosis_logger: Optional[DiagnosisLogger] = None


def get_diagnosis_logger() -> DiagnosisLogger:
    """获取诊断日志记录器"""
    global diagnosis_logger
    if diagnosis_logger is None:
        diagnosis_logger = DiagnosisLogger()
    return diagnosis_logger


def initialize_diagnosis_logger(log_dir: Path = None) -> DiagnosisLogger:
    """初始化诊断日志记录器"""
    global diagnosis_logger
    diagnosis_logger = DiagnosisLogger(log_dir=log_dir)
    logger.info(f"诊断日志记录器已初始化：{diagnosis_logger.log_dir}")
    return diagnosis_logger


def log_diagnosis(
    request_id: str,
    image_hash: Optional[str],
    symptoms: str,
    disease_detected: str,
    confidence: float,
    processing_time_ms: float,
    success: bool,
    error: Optional[str] = None,
    cache_hit: bool = False,
    features: Optional[Dict[str, Any]] = None
) -> None:
    """记录诊断日志的便捷函数"""
    logger_instance = get_diagnosis_logger()
    logger_instance.log_diagnosis(
        request_id=request_id,
        image_hash=image_hash,
        symptoms=symptoms,
        disease_detected=disease_detected,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        success=success,
        error=error,
        cache_hit=cache_hit,
        features=features
    )
