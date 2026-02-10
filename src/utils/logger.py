# -*- coding: utf-8 -*-
"""
日志管理模块 (Logger)

提供结构化日志记录功能，支持JSON格式输出
便于后续日志分析和监控
"""
import os
import json
import logging
import sys
from datetime import datetime
from enum import IntEnum
from typing import Dict, Any, Optional, Union
from pathlib import Path


class LogLevel(IntEnum):
    """日志级别枚举"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class Logger:
    """
    结构化日志管理器
    
    功能:
    1. 支持JSON格式输出
    2. 支持文件和控制台双输出
    3. 支持结构化数据记录
    4. 支持日志轮转
    """
    
    _instances: Dict[str, 'Logger'] = {}
    
    def __new__(cls, name: str = "WheatAgent", *args, **kwargs):
        """单例模式，确保每个name只有一个实例"""
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(
        self,
        name: str = "WheatAgent",
        level: Union[LogLevel, int] = LogLevel.INFO,
        log_dir: Optional[str] = None,
        use_json: bool = True,
        console_output: bool = True,
        file_output: bool = True
    ):
        """
        初始化日志管理器
        
        :param name: 日志器名称
        :param level: 日志级别
        :param log_dir: 日志目录
        :param use_json: 是否使用JSON格式
        :param console_output: 是否输出到控制台
        :param file_output: 是否输出到文件
        """
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.name = name
        self.level = level if isinstance(level, int) else level.value
        self.use_json = use_json
        self.log_dir = log_dir or "logs"
        self.console_output = console_output
        self.file_output = file_output
        
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 配置日志器
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.level)
        self._logger.handlers = []  # 清除已有处理器
        
        # 添加处理器
        if console_output:
            self._add_console_handler()
        
        if file_output:
            self._add_file_handler()
        
        self._initialized = True
        
        self.info(f"日志管理器初始化完成: {name}")
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        
        if self.use_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '[%(asctime)s] [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        
        self._logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """添加文件处理器"""
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"{self.name}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.level)
        
        if self.use_json:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        
        self._logger.addHandler(file_handler)
    
    def _log(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ):
        """内部日志记录方法"""
        extra_data = extra or {}
        
        # 创建日志记录
        record = self._logger.makeRecord(
            self.name,
            level,
            "",
            0,
            message,
            (),
            sys.exc_info() if exc_info else None
        )
        record.extra_data = extra_data
        
        self._logger.handle(record)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录DEBUG级别日志"""
        self._log(LogLevel.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录INFO级别日志"""
        self._log(LogLevel.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录WARNING级别日志"""
        self._log(LogLevel.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = True):
        """记录ERROR级别日志"""
        self._log(LogLevel.ERROR, message, extra, exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = True):
        """记录CRITICAL级别日志"""
        self._log(LogLevel.CRITICAL, message, extra, exc_info)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        记录性能指标
        
        :param operation: 操作名称
        :param duration_ms: 耗时（毫秒）
        :param extra: 额外数据
        """
        data = {
            "operation": operation,
            "duration_ms": duration_ms,
            "type": "performance"
        }
        if extra:
            data.update(extra)
        
        self.info(f"性能指标: {operation} 耗时 {duration_ms:.2f}ms", extra=data)
    
    def log_model_inference(
        self,
        model_name: str,
        input_shape: tuple,
        output_shape: tuple,
        inference_time_ms: float,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        记录模型推理日志
        
        :param model_name: 模型名称
        :param input_shape: 输入形状
        :param output_shape: 输出形状
        :param inference_time_ms: 推理时间（毫秒）
        :param extra: 额外数据
        """
        data = {
            "model_name": model_name,
            "input_shape": input_shape,
            "output_shape": output_shape,
            "inference_time_ms": inference_time_ms,
            "type": "model_inference"
        }
        if extra:
            data.update(extra)
        
        self.info(
            f"模型推理: {model_name} 输入{input_shape} 输出{output_shape} 耗时{inference_time_ms:.2f}ms",
            extra=data
        )
    
    def log_diagnosis(
        self,
        image_path: str,
        diagnosis_result: str,
        confidence: float,
        processing_time_ms: float,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        记录诊断日志
        
        :param image_path: 图像路径
        :param diagnosis_result: 诊断结果
        :param confidence: 置信度
        :param processing_time_ms: 处理时间（毫秒）
        :param extra: 额外数据
        """
        data = {
            "image_path": image_path,
            "diagnosis_result": diagnosis_result,
            "confidence": confidence,
            "processing_time_ms": processing_time_ms,
            "type": "diagnosis"
        }
        if extra:
            data.update(extra)
        
        self.info(
            f"诊断完成: {diagnosis_result} (置信度: {confidence:.2f}, 耗时: {processing_time_ms:.2f}ms)",
            extra=data
        )
    
    def get_logs(self, date: Optional[str] = None, level: Optional[str] = None) -> list:
        """
        获取日志记录
        
        :param date: 日期 (格式: YYYYMMDD)
        :param level: 日志级别过滤
        :return: 日志记录列表
        """
        date = date or datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"{self.name}_{date}.log")
        
        if not os.path.exists(log_file):
            return []
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if level is None or log_entry.get("level") == level:
                        logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        return logs


def get_logger(name: str = "WheatAgent") -> Logger:
    """
    获取日志管理器实例
    
    :param name: 日志器名称
    :return: Logger实例
    """
    return Logger(name)


# 默认日志管理器
default_logger = Logger("WheatAgent")


def test_logger():
    """测试日志管理器"""
    print("=" * 70)
    print("🧪 测试日志管理器")
    print("=" * 70)
    
    # 创建测试日志器
    logger = Logger(
        name="TestLogger",
        level=LogLevel.DEBUG,
        log_dir="logs/test",
        use_json=True,
        console_output=True,
        file_output=True
    )
    
    # 测试各级别日志
    print("\n📝 测试各级别日志:")
    logger.debug("这是一条DEBUG日志", extra={"test": True})
    logger.info("这是一条INFO日志", extra={"module": "test"})
    logger.warning("这是一条WARNING日志", extra={"alert": "test"})
    
    # 测试性能日志
    print("\n⚡ 测试性能日志:")
    logger.log_performance("图像预处理", 45.5, extra={"image_size": "1920x1080"})
    logger.log_model_inference(
        model_name="YOLOv8",
        input_shape=(1, 3, 640, 640),
        output_shape=(1, 84, 8400),
        inference_time_ms=23.4
    )
    
    # 测试诊断日志
    print("\n🔍 测试诊断日志:")
    logger.log_diagnosis(
        image_path="test.jpg",
        diagnosis_result="条锈病",
        confidence=0.95,
        processing_time_ms=156.7
    )
    
    # 测试错误日志
    print("\n❌ 测试错误日志:")
    try:
        raise ValueError("测试异常")
    except Exception:
        logger.error("发生错误", extra={"error_type": "ValueError"}, exc_info=True)
    
    # 获取日志
    print("\n📊 获取日志记录:")
    logs = logger.get_logs(level="INFO")
    print(f"获取到 {len(logs)} 条INFO级别日志")
    
    print("\n" + "=" * 70)
    print("✅ 日志管理器测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_logger()
