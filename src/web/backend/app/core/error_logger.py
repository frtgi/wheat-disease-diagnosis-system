"""
错误日志记录模块

提供结构化的错误日志记录功能，支持：
- 错误日志持久化存储
- 错误统计和分析
- 错误告警通知
- 日志轮转和清理
"""
import json
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """
    错误严重程度枚举
    
    定义错误的严重级别，用于日志分类和告警。
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorLogEntry:
    """
    错误日志条目数据类
    
    封装单个错误日志的所有信息。
    
    Attributes:
        id: 日志唯一标识
        error_code: 错误代码
        error_message: 错误消息
        error_details: 错误详情
        severity: 严重程度
        timestamp: 时间戳
        request_path: 请求路径
        request_method: 请求方法
        client_ip: 客户端 IP
        user_id: 用户 ID
        trace_id: 追踪 ID
        stack_trace: 堆栈信息
        additional_data: 附加数据
    """
    id: str
    error_code: str
    error_message: str
    error_details: Any
    severity: ErrorSeverity
    timestamp: str
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    client_ip: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    stack_trace: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含所有字段的字典
        """
        result = asdict(self)
        result["severity"] = self.severity.value
        return result
    
    def to_json(self) -> str:
        """
        转换为 JSON 字符串
        
        Returns:
            JSON 格式的字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class ErrorLogStorage:
    """
    错误日志存储类
    
    提供错误日志的持久化存储和管理功能。
    """
    
    def __init__(self, log_dir: str = "logs/errors", max_file_size: int = 10 * 1024 * 1024):
        """
        初始化错误日志存储
        
        Args:
            log_dir: 日志存储目录
            max_file_size: 单个日志文件最大大小（字节）
        """
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self._lock = threading.Lock()
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        """
        获取日志文件路径
        
        Args:
            date: 日期，默认为当前日期
            
        Returns:
            日志文件路径
        """
        if date is None:
            date = datetime.now()
        
        filename = f"errors_{date.strftime('%Y-%m-%d')}.jsonl"
        return self.log_dir / filename
    
    def _rotate_if_needed(self, file_path: Path) -> None:
        """
        如果文件大小超过限制，进行轮转
        
        Args:
            file_path: 日志文件路径
        """
        if not file_path.exists():
            return
        
        if file_path.stat().st_size >= self.max_file_size:
            timestamp = datetime.now().strftime('%H%M%S')
            new_path = file_path.with_suffix(f'.{timestamp}.jsonl')
            file_path.rename(new_path)
    
    def save(self, entry: ErrorLogEntry) -> None:
        """
        保存错误日志条目
        
        Args:
            entry: 错误日志条目
        """
        with self._lock:
            file_path = self._get_log_file_path()
            self._rotate_if_needed(file_path)
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(entry.to_json() + '\n')
    
    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error_code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100
    ) -> List[ErrorLogEntry]:
        """
        查询错误日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            error_code: 错误代码过滤
            severity: 严重程度过滤
            limit: 返回数量限制
            
        Returns:
            匹配的错误日志条目列表
        """
        results = []
        
        if start_time and end_time:
            current = start_time
            while current <= end_time:
                file_path = self._get_log_file_path(current)
                if file_path.exists():
                    results.extend(self._read_file(file_path, error_code, severity))
                current += timedelta(days=1)
        else:
            file_path = self._get_log_file_path()
            if file_path.exists():
                results = self._read_file(file_path, error_code, severity)
        
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
    
    def _read_file(
        self,
        file_path: Path,
        error_code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> List[ErrorLogEntry]:
        """
        读取日志文件
        
        Args:
            file_path: 日志文件路径
            error_code: 错误代码过滤
            severity: 严重程度过滤
            
        Returns:
            匹配的错误日志条目列表
        """
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if error_code and data.get('error_code') != error_code:
                            continue
                        if severity and data.get('severity') != severity.value:
                            continue
                        
                        data['severity'] = ErrorSeverity(data['severity'])
                        entries.append(ErrorLogEntry(**data))
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            logger.error(f"读取错误日志文件失败: {e}")
        
        return entries
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        清理过期的日志文件
        
        Args:
            days: 保留天数
            
        Returns:
            删除的文件数量
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file_path in self.log_dir.glob("errors_*.jsonl"):
            try:
                date_str = file_path.stem.replace("errors_", "").split('.')[0]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            except (ValueError, OSError):
                continue
        
        return deleted_count


class ErrorStatistics:
    """
    错误统计类
    
    提供错误发生频率、类型分布等统计功能。
    """
    
    def __init__(self):
        """初始化错误统计"""
        self._counts: Dict[str, int] = defaultdict(int)
        self._by_severity: Dict[ErrorSeverity, int] = defaultdict(int)
        self._by_hour: Dict[int, int] = defaultdict(int)
        self._by_path: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        self._total_count = 0
    
    def record(self, entry: ErrorLogEntry) -> None:
        """
        记录错误统计
        
        Args:
            entry: 错误日志条目
        """
        with self._lock:
            self._counts[entry.error_code] += 1
            self._by_severity[entry.severity] += 1
            
            try:
                timestamp = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                self._by_hour[timestamp.hour] += 1
            except (ValueError, TypeError):
                pass
            
            if entry.request_path:
                self._by_path[entry.request_path] += 1
            
            self._total_count += 1
    
    def get_error_counts(self) -> Dict[str, int]:
        """
        获取各错误码的发生次数
        
        Returns:
            错误码到次数的映射
        """
        with self._lock:
            return dict(self._counts)
    
    def get_severity_counts(self) -> Dict[str, int]:
        """
        获取各严重程度的错误次数
        
        Returns:
            严重程度到次数的映射
        """
        with self._lock:
            return {k.value: v for k, v in self._by_severity.items()}
    
    def get_hourly_distribution(self) -> Dict[int, int]:
        """
        获取错误的小时分布
        
        Returns:
            小时到次数的映射
        """
        with self._lock:
            return dict(self._by_hour)
    
    def get_top_paths(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取错误最多的请求路径
        
        Args:
            limit: 返回数量限制
            
        Returns:
            路径统计列表
        """
        with self._lock:
            sorted_paths = sorted(self._by_path.items(), key=lambda x: x[1], reverse=True)
            return [{"path": path, "count": count} for path, count in sorted_paths[:limit]]
    
    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取发生最频繁的错误
        
        Args:
            limit: 返回数量限制
            
        Returns:
            错误统计列表
        """
        with self._lock:
            sorted_errors = sorted(self._counts.items(), key=lambda x: x[1], reverse=True)
            return [{"error_code": code, "count": count} for code, count in sorted_errors[:limit]]
    
    def get_total_count(self) -> int:
        """
        获取错误总数
        
        Returns:
            错误总数
        """
        with self._lock:
            return self._total_count
    
    def reset(self) -> None:
        """重置所有统计数据"""
        with self._lock:
            self._counts.clear()
            self._by_severity.clear()
            self._by_hour.clear()
            self._by_path.clear()
            self._total_count = 0


class ErrorLogger:
    """
    错误日志记录器
    
    统一的错误日志记录入口，整合存储和统计功能。
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        log_dir: str = "logs/errors",
        max_file_size: int = 10 * 1024 * 1024,
        enable_storage: bool = True,
        enable_statistics: bool = True,
        alert_handlers: Optional[List[Callable[[ErrorLogEntry], None]]] = None
    ):
        """
        初始化错误日志记录器
        
        Args:
            log_dir: 日志存储目录
            max_file_size: 单个日志文件最大大小
            enable_storage: 是否启用持久化存储
            enable_statistics: 是否启用统计
            alert_handlers: 告警处理器列表
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.enable_storage = enable_storage
        self.enable_statistics = enable_statistics
        
        if enable_storage:
            self.storage = ErrorLogStorage(log_dir, max_file_size)
        else:
            self.storage = None
        
        if enable_statistics:
            self.statistics = ErrorStatistics()
        else:
            self.statistics = None
        
        self.alert_handlers = alert_handlers or []
    
    def _generate_id(self, entry_data: Dict[str, Any]) -> str:
        """
        生成日志 ID
        
        Args:
            entry_data: 日志数据
            
        Returns:
            唯一的日志 ID
        """
        content = f"{entry_data.get('timestamp', '')}{entry_data.get('error_code', '')}{entry_data.get('request_path', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _determine_severity(self, error_code: str) -> ErrorSeverity:
        """
        根据错误码确定严重程度
        
        Args:
            error_code: 错误代码
            
        Returns:
            错误严重程度
        """
        if error_code.startswith('SYS_'):
            if error_code in ['SYS_001', 'SYS_002']:
                return ErrorSeverity.CRITICAL
            return ErrorSeverity.HIGH
        
        if error_code.startswith('AI_'):
            return ErrorSeverity.HIGH
        
        if error_code.startswith('DB_'):
            return ErrorSeverity.HIGH
        
        if error_code.startswith('AUTH_'):
            return ErrorSeverity.MEDIUM
        
        if error_code.startswith('VALIDATION_'):
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def log(
        self,
        error_code: str,
        error_message: str,
        error_details: Any = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> ErrorLogEntry:
        """
        记录错误日志
        
        Args:
            error_code: 错误代码
            error_message: 错误消息
            error_details: 错误详情
            request_path: 请求路径
            request_method: 请求方法
            client_ip: 客户端 IP
            user_id: 用户 ID
            trace_id: 追踪 ID
            stack_trace: 堆栈信息
            additional_data: 附加数据
            
        Returns:
            创建的错误日志条目
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        severity = self._determine_severity(error_code)
        
        entry_data = {
            'error_code': error_code,
            'error_message': error_message,
            'error_details': error_details,
            'request_path': request_path,
            'request_method': request_method,
            'client_ip': client_ip,
            'user_id': user_id,
            'trace_id': trace_id,
            'stack_trace': stack_trace,
            'timestamp': timestamp
        }
        
        entry = ErrorLogEntry(
            id=self._generate_id(entry_data),
            severity=severity,
            additional_data=additional_data or {},
            **entry_data
        )
        
        if self.storage:
            try:
                self.storage.save(entry)
            except Exception as e:
                logger.error(f"保存错误日志失败: {e}")
        
        if self.statistics:
            self.statistics.record(entry)
        
        for handler in self.alert_handlers:
            try:
                handler(entry)
            except Exception as e:
                logger.error(f"执行告警处理器失败: {e}")
        
        log_method = {
            ErrorSeverity.LOW: logger.info,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }.get(severity, logger.error)
        
        log_method(
            f"[{error_code}] {error_message}",
            extra={
                'error_code': error_code,
                'error_details': error_details,
                'request_path': request_path,
                'client_ip': client_ip,
                'trace_id': trace_id,
                'severity': severity.value
            }
        )
        
        return entry
    
    def log_from_exception(
        self,
        error_code: str,
        exception: Exception,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> ErrorLogEntry:
        """
        从异常对象记录错误日志
        
        Args:
            error_code: 错误代码
            exception: 异常对象
            request_path: 请求路径
            request_method: 请求方法
            client_ip: 客户端 IP
            user_id: 用户 ID
            trace_id: 追踪 ID
            additional_data: 附加数据
            
        Returns:
            创建的错误日志条目
        """
        import traceback
        
        return self.log(
            error_code=error_code,
            error_message=str(exception),
            error_details={'exception_type': type(exception).__name__},
            request_path=request_path,
            request_method=request_method,
            client_ip=client_ip,
            user_id=user_id,
            trace_id=trace_id,
            stack_trace=traceback.format_exc(),
            additional_data=additional_data
        )
    
    def query_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error_code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100
    ) -> List[ErrorLogEntry]:
        """
        查询错误日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            error_code: 错误代码过滤
            severity: 严重程度过滤
            limit: 返回数量限制
            
        Returns:
            匹配的错误日志条目列表
        """
        if not self.storage:
            return []
        
        return self.storage.query(start_time, end_time, error_code, severity, limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计数据
        
        Returns:
            统计数据字典
        """
        if not self.statistics:
            return {}
        
        return {
            'total_count': self.statistics.get_total_count(),
            'by_severity': self.statistics.get_severity_counts(),
            'top_errors': self.statistics.get_top_errors(),
            'top_paths': self.statistics.get_top_paths(),
            'hourly_distribution': self.statistics.get_hourly_distribution()
        }
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        清理过期日志
        
        Args:
            days: 保留天数
            
        Returns:
            删除的文件数量
        """
        if not self.storage:
            return 0
        
        return self.storage.cleanup_old_logs(days)
    
    def add_alert_handler(self, handler: Callable[[ErrorLogEntry], None]) -> None:
        """
        添加告警处理器
        
        Args:
            handler: 告警处理函数
        """
        self.alert_handlers.append(handler)


def email_alert_handler(smtp_config: Dict[str, Any]) -> Callable[[ErrorLogEntry], None]:
    """
    创建邮件告警处理器
    
    Args:
        smtp_config: SMTP 配置
        
    Returns:
        告警处理函数
    """
    def handler(entry: ErrorLogEntry) -> None:
        if entry.severity not in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['from_addr']
            msg['To'] = smtp_config['to_addr']
            msg['Subject'] = f"[{entry.severity.value.upper()}] 错误告警: {entry.error_code}"
            
            body = f"""
错误告警通知

错误代码: {entry.error_code}
错误消息: {entry.error_message}
严重程度: {entry.severity.value}
发生时间: {entry.timestamp}
请求路径: {entry.request_path or 'N/A'}
客户端IP: {entry.client_ip or 'N/A'}
追踪ID: {entry.trace_id or 'N/A'}

错误详情:
{json.dumps(entry.error_details, ensure_ascii=False, indent=2) if entry.error_details else 'N/A'}

堆栈信息:
{entry.stack_trace or 'N/A'}
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                if smtp_config.get('use_tls'):
                    server.starttls()
                if smtp_config.get('username'):
                    server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"发送错误告警邮件失败: {e}")
    
    return handler


def webhook_alert_handler(webhook_url: str) -> Callable[[ErrorLogEntry], None]:
    """
    创建 Webhook 告警处理器
    
    Args:
        webhook_url: Webhook URL
        
    Returns:
        告警处理函数
    """
    def handler(entry: ErrorLogEntry) -> None:
        if entry.severity not in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return
        
        try:
            import httpx
            
            payload = {
                'error_code': entry.error_code,
                'error_message': entry.error_message,
                'severity': entry.severity.value,
                'timestamp': entry.timestamp,
                'request_path': entry.request_path,
                'client_ip': entry.client_ip,
                'trace_id': entry.trace_id
            }
            
            httpx.post(webhook_url, json=payload, timeout=5.0)
            
        except Exception as e:
            logger.error(f"发送错误告警 Webhook 失败: {e}")
    
    return handler


error_logger = ErrorLogger()
