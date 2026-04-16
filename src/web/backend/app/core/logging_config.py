"""
结构化日志配置模块
提供 JSON 格式的结构化日志输出，支持 request_id / diagnosis_id 追踪字段

Task 5 (P1-S5) 增强：
- 新增 bind_logger() 便捷函数，支持通过 extra 字典绑定追踪字段
- 新增 DiagnosisLogContext 上下文管理器，用于诊断流程的 diagnosis_id 追踪
- ColoredFormatter / JSONFormatter 均支持 diagnosis_id 显示
- 新增 LoggerAdapter 增强版，自动合并 extra 字段到 LogRecord 属性
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from contextlib import contextmanager

try:
    from app.main import request_id_var
except ImportError:
    request_id_var = None


class JSONFormatter(logging.Formatter):
    """
    JSON 格式化器

    将日志记录转换为 JSON 格式，便于日志收集和分析
    自动提取 request_id（ContextVar）和 diagnosis_id（LogContext/extra）
    """

    def __init__(self, include_extra: bool = True):
        """
        初始化 JSON 格式化器

        Args:
            include_extra: 是否包含额外字段
        """
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            JSON 格式的日志字符串
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        if request_id_var:
            try:
                req_id = request_id_var.get()
                if req_id:
                    log_data["request_id"] = req_id
            except Exception:
                pass

        diagnosis_id = getattr(record, 'diagnosis_id', None) or LogContext.get('diagnosis_id')
        if diagnosis_id:
            log_data["diagnosis_id"] = diagnosis_id

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)

        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'pathname', 'process', 'processName', 'relativeCreated',
                    'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                    'message', 'taskName', 'diagnosis_id'
                }:
                    try:
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)

            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    彩色控制台格式化器

    为不同级别的日志添加颜色，便于开发调试
    自动显示 request_id 和 diagnosis_id 追踪信息
    """

    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            带颜色的日志字符串
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        req_id = ""
        if request_id_var:
            try:
                rid = request_id_var.get()
                if rid:
                    req_id = f" [{rid[:8]}] "
            except Exception:
                pass

        diag_id = ""
        diagnosis_id = getattr(record, 'diagnosis_id', None) or LogContext.get('diagnosis_id')
        if diagnosis_id:
            diag_id = f" [diag:{str(diagnosis_id)[:8]}] "

        log_message = f"{timestamp}{req_id}{diag_id}| {color}{record.levelname:8}{self.RESET} | {record.name} | {record.getMessage()}"

        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    配置应用日志

    Args:
        level: 日志级别
        json_format: 是否使用 JSON 格式
        log_file: 日志文件路径（可选）
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())

    root_logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


class LogContext:
    """
    日志上下文管理器

    用于在日志中添加上下文信息（如 diagnosis_id）
    通过 ContextFilter 自动注入到每条日志记录中
    """

    _context: Dict[str, Any] = {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        设置上下文值

        Args:
            key: 键
            value: 值
        """
        cls._context[key] = value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取上下文值

        Args:
            key: 键
            default: 默认值

        Returns:
            上下文值
        """
        return cls._context.get(key, default)

    @classmethod
    def clear(cls) -> None:
        """清除所有上下文"""
        cls._context.clear()

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """获取所有上下文"""
        return cls._context.copy()


class ContextFilter(logging.Filter):
    """
    日志上下文过滤器

    将 LogContext 中的值自动注入到每条日志记录的属性中，
    使 diagnosis_id 等追踪字段无需每次手动传递 extra
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录，注入 LogContext 中的值

        Args:
            record: 日志记录对象

        Returns:
            总是返回 True
        """
        for key, value in LogContext.get_all().items():
            setattr(record, key, value)
        return True


@contextmanager
def DiagnosisLogContext(diagnosis_id: Any):
    """
    诊断日志上下文管理器

    在 with 块内自动将 diagnosis_id 注入到所有日志记录中，
    用于追踪单次完整诊断流程的所有日志。

    使用示例:
        with DiagnosisLogContext(diagnosis_id=42):
            logger.info("开始视觉特征提取")  # 自动携带 diagnosis_id=42
            logger.info("融合完成")           # 同样携带 diagnosis_id=42

    Args:
        diagnosis_id: 诊断记录 ID（来自数据库主键或请求生成）

    Yields:
        None
    """
    LogContext.set('diagnosis_id', diagnosis_id)
    try:
        yield
    finally:
        LogContext._context.pop('diagnosis_id', None)


class LoggerAdapter(logging.LoggerAdapter):
    """
    日志适配器（增强版）

    支持通过构造时传入的 extra 字典自动附加到每条日志，
    适用于需要绑定 request_id / diagnosis_id 的场景。
    与标准 LoggerAdapter 不同，本实现会将 extra 字段
    合并到 LogRecord 属性中，确保 JSONFormatter 能正确提取。
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        处理日志消息，合并内置 extra 字段

        Args:
            msg: 日志消息
            kwargs: 关键字参数（含 extra 字典）

        Returns:
            (msg, kwargs) 元组
        """
        extra = kwargs.get('extra', {})
        merged_extra = {**self.extra, **extra}
        kwargs['extra'] = merged_extra
        return msg, kwargs


def bind_logger(
    name: str,
    request_id: Optional[str] = None,
    diagnosis_id: Optional[Any] = None,
    **extra_fields
) -> logging.LoggerAdapter:
    """
    创建带追踪字段的日志适配器

    便捷函数：返回一个预绑定了 request_id / diagnosis_id 等
    追踪字段的 LoggerAdapter，调用方无需每次手动传 extra。

    使用示例:
        logger = bind_logger(__name__, request_id="abc123", diagnosis_id=42)
        logger.info("处理图像")  # 自动携带 request_id + diagnosis_id

    Args:
        name: 日志记录器名称（通常为 __name__）
        request_id: 请求 ID（可选，用于跨服务追踪）
        diagnosis_id: 诊断 ID（可选，用于诊断流程追踪）
        **extra_fields: 其他自定义追踪字段

    Returns:
        LoggerAdapter: 预绑定了追踪字段的日志适配器
    """
    base_logger = logging.getLogger(name)
    base_logger.addFilter(ContextFilter())

    extra = {}
    if request_id:
        extra['request_id'] = request_id
    if diagnosis_id is not None:
        extra['diagnosis_id'] = diagnosis_id
    extra.update(extra_fields)

    return LoggerAdapter(base_logger, extra)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器（已挂载 ContextFilter）

    Args:
        name: 日志记录器名称

    Returns:
        配置好 ContextFilter 的日志记录器
    """
    logger = logging.getLogger(name)
    logger.addFilter(ContextFilter())
    return logger
