# -*- coding: utf-8 -*-
"""
错误处理模块 (Error Handler)

提供统一的错误处理和异常捕获机制
支持错误分类、恢复策略和监控告警
"""
import sys
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from functools import wraps


class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = "low"           # 轻微错误，可忽略
    MEDIUM = "medium"     # 中等错误，需要记录
    HIGH = "high"         # 严重错误，需要处理
    CRITICAL = "critical" # 致命错误，系统可能无法继续


class ErrorCategory(Enum):
    """错误分类"""
    MODEL_LOAD = "model_load"       # 模型加载错误
    INFERENCE = "inference"         # 推理错误
    DATA_PROCESSING = "data"        # 数据处理错误
    NETWORK = "network"             # 网络错误
    CONFIGURATION = "config"        # 配置错误
    RESOURCE = "resource"           # 资源错误（内存、显存等）
    UNKNOWN = "unknown"             # 未知错误


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    exception: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    traceback_str: str
    recoverable: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_type": type(self.exception).__name__,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "traceback": self.traceback_str,
            "recoverable": self.recoverable
        }


class ErrorHandler:
    """
    统一错误处理器
    
    功能:
    1. 错误分类和严重级别评估
    2. 错误恢复策略
    3. 错误统计和监控
    4. 装饰器支持
    """
    
    _instance: Optional['ErrorHandler'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.error_counts: Dict[ErrorCategory, int] = {cat: 0 for cat in ErrorCategory}
        self.error_history: List[ErrorInfo] = []
        self.max_history = 100
        
        # 错误处理策略
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.error_callbacks: Dict[ErrorSeverity, List[Callable]] = {
            sev: [] for sev in ErrorSeverity
        }
        
        self._initialized = True
    
    def classify_error(self, exception: Exception) -> tuple:
        """
        分类错误并确定严重级别
        
        :param exception: 异常对象
        :return: (ErrorCategory, ErrorSeverity)
        """
        error_type = type(exception).__name__
        error_msg = str(exception).lower()
        
        # 模型加载错误
        if any(kw in error_msg for kw in ['model', 'checkpoint', 'weights', 'load']):
            return ErrorCategory.MODEL_LOAD, ErrorSeverity.HIGH
        
        # 推理错误
        if any(kw in error_msg for kw in ['inference', 'forward', 'predict']):
            return ErrorCategory.INFERENCE, ErrorSeverity.HIGH
        
        # 数据处理错误
        if any(kw in error_msg for kw in ['data', 'image', 'preprocess', 'transform']):
            return ErrorCategory.DATA_PROCESSING, ErrorSeverity.MEDIUM
        
        # 网络错误
        if any(kw in error_msg for kw in ['network', 'connection', 'timeout', 'http']):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        
        # 配置错误
        if any(kw in error_msg for kw in ['config', 'configuration', 'setting']):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH
        
        # 资源错误
        if any(kw in error_msg for kw in ['memory', 'cuda', 'gpu', 'oom', 'resource']):
            return ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL
        
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM
    
    def handle(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        raise_on_critical: bool = True
    ) -> ErrorInfo:
        """
        处理异常
        
        :param exception: 异常对象
        :param context: 上下文信息
        :param raise_on_critical: 严重错误是否抛出
        :return: 错误信息
        """
        context = context or {}
        
        # 获取traceback
        tb_str = traceback.format_exc()
        
        # 分类错误
        category, severity = self.classify_error(exception)
        
        # 判断是否可恢复
        recoverable = self._is_recoverable(exception, category)
        
        # 创建错误信息
        error_info = ErrorInfo(
            exception=exception,
            category=category,
            severity=severity,
            message=str(exception),
            context=context,
            traceback_str=tb_str,
            recoverable=recoverable
        )
        
        # 记录错误
        self._record_error(error_info)
        
        # 执行恢复策略
        if recoverable and category in self.recovery_strategies:
            try:
                self.recovery_strategies[category](error_info)
            except Exception as e:
                print(f"恢复策略执行失败: {e}")
        
        # 执行回调
        self._execute_callbacks(error_info)
        
        # 严重错误抛出
        if severity == ErrorSeverity.CRITICAL and raise_on_critical:
            raise exception
        
        return error_info
    
    def _is_recoverable(self, exception: Exception, category: ErrorCategory) -> bool:
        """判断错误是否可恢复"""
        # 资源错误通常不可恢复
        if category == ErrorCategory.RESOURCE:
            return False
        
        # 模型加载错误不可恢复
        if category == ErrorCategory.MODEL_LOAD:
            return False
        
        # 其他错误可尝试恢复
        return True
    
    def _record_error(self, error_info: ErrorInfo):
        """记录错误"""
        self.error_counts[error_info.category] += 1
        self.error_history.append(error_info)
        
        # 限制历史记录大小
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # 打印错误信息
        print(f"\n❌ [错误] {error_info.category.value}: {error_info.message}")
        if error_info.severity == ErrorSeverity.CRITICAL:
            print(f"   严重级别: {error_info.severity.value}")
            print(f"   可恢复: {error_info.recoverable}")
    
    def _execute_callbacks(self, error_info: ErrorInfo):
        """执行错误回调"""
        for callback in self.error_callbacks.get(error_info.severity, []):
            try:
                callback(error_info)
            except Exception as e:
                print(f"回调执行失败: {e}")
    
    def register_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: Callable[[ErrorInfo], None]
    ):
        """
        注册错误恢复策略
        
        :param category: 错误类别
        :param strategy: 恢复策略函数
        """
        self.recovery_strategies[category] = strategy
    
    def register_callback(
        self,
        severity: ErrorSeverity,
        callback: Callable[[ErrorInfo], None]
    ):
        """
        注册错误回调
        
        :param severity: 严重级别
        :param callback: 回调函数
        """
        self.error_callbacks[severity].append(callback)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "category_counts": {cat.value: count for cat, count in self.error_counts.items()},
            "recent_errors": [err.to_dict() for err in self.error_history[-10:]]
        }
    
    def clear_history(self):
        """清除错误历史"""
        self.error_history.clear()
        self.error_counts = {cat: 0 for cat in ErrorCategory}


def handle_errors(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    错误处理装饰器
    
    :param category: 错误类别（可选，自动检测）
    :param severity: 严重级别（可选，自动检测）
    :param context: 上下文信息
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = context or {}
                ctx.update({
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                })
                error_info = handler.handle(e, ctx)
                
                # 如果不可恢复，重新抛出
                if not error_info.recoverable:
                    raise
                
                # 返回None表示处理失败
                return None
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    error_context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """
    安全执行函数
    
    :param func: 要执行的函数
    :param args: 位置参数
    :param default_return: 错误时的默认返回值
    :param error_context: 错误上下文
    :param kwargs: 关键字参数
    :return: 函数返回值或默认值
    """
    handler = ErrorHandler()
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ctx = error_context or {}
        ctx.update({"function": func.__name__})
        handler.handle(e, ctx)
        return default_return


# 全局错误处理器实例
error_handler = ErrorHandler()


def test_error_handler():
    """测试错误处理器"""
    print("=" * 70)
    print("🧪 测试错误处理器")
    print("=" * 70)
    
    handler = ErrorHandler()
    
    # 测试错误分类
    print("\n📝 测试错误分类:")
    
    test_exceptions = [
        Exception("Failed to load model weights"),
        Exception("CUDA out of memory"),
        Exception("Cannot preprocess image"),
        Exception("Network connection timeout"),
    ]
    
    for exc in test_exceptions:
        category, severity = handler.classify_error(exc)
        print(f"   {exc}: {category.value} ({severity.value})")
    
    # 测试错误处理
    print("\n🔍 测试错误处理:")
    
    try:
        raise ValueError("测试模型加载错误")
    except Exception as e:
        error_info = handler.handle(e, {"test": True}, raise_on_critical=False)
        print(f"   处理结果: {error_info.category.value}, 可恢复: {error_info.recoverable}")
    
    # 测试装饰器
    print("\n⚡ 测试错误处理装饰器:")
    
    @handle_errors(context={"module": "test"})
    def failing_function():
        raise RuntimeError("装饰器测试错误")
    
    result = failing_function()
    print(f"   装饰器捕获错误，返回: {result}")
    
    # 测试安全执行
    print("\n🛡️ 测试安全执行:")
    
    def risky_function(x):
        if x < 0:
            raise ValueError("负数错误")
        return x * 2
    
    result = safe_execute(risky_function, -5, default_return=0)
    print(f"   安全执行结果: {result}")
    
    result = safe_execute(risky_function, 5, default_return=0)
    print(f"   正常执行结果: {result}")
    
    # 获取统计
    print("\n📊 错误统计:")
    stats = handler.get_error_stats()
    print(f"   总错误数: {stats['total_errors']}")
    
    print("\n" + "=" * 70)
    print("✅ 错误处理器测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_error_handler()
