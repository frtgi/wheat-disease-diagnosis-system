"""
启动管理器模块

提供应用启动流程管理、进度追踪和组件状态监控
增强版：支持错误收集、摘要生成和修复建议
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class StartupPhase(Enum):
    """启动阶段枚举"""
    INIT = "initializing"
    DATABASE = "database"
    AI_LOADING = "ai_loading"
    SERVICES = "services"
    READY = "ready"
    FAILED = "failed"


class ComponentStatus(Enum):
    """组件状态枚举"""
    PENDING = "pending"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"
    DEGRADED = "degraded"


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    component: str
    error_message: str
    suggestion: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "component": self.component,
            "error_message": self.error_message,
            "suggestion": self.suggestion,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat()
        }


@dataclass
class ComponentInfo:
    """组件信息"""
    name: str
    status: ComponentStatus = ComponentStatus.PENDING
    progress: int = 0
    message: str = ""
    error: Optional[str] = None
    load_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "load_time": round(self.load_time, 2),
            "metadata": self.metadata
        }


@dataclass
class StartupProgress:
    """启动进度"""
    phase: StartupPhase = StartupPhase.INIT
    overall_progress: int = 0
    current_component: str = ""
    components: Dict[str, ComponentInfo] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    estimated_total_time: float = 120.0
    
    def elapsed_time(self) -> float:
        """获取已用时间"""
        return time.time() - self.start_time
    
    def remaining_time(self) -> float:
        """获取预计剩余时间"""
        if self.overall_progress == 0:
            return self.estimated_total_time
        
        estimated_total = self.elapsed_time() / (self.overall_progress / 100)
        return max(0, estimated_total - self.elapsed_time())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "phase": self.phase.value,
            "overall_progress": self.overall_progress,
            "current_component": self.current_component,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "elapsed_time": round(self.elapsed_time(), 2),
            "estimated_remaining_time": round(self.remaining_time(), 2),
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }


class StartupManager:
    """启动管理器（增强版）
    
    支持错误收集、摘要生成和修复建议
    """
    
    def __init__(self, timeout: float = 120.0):
        """
        初始化启动管理器
        
        Args:
            timeout: 启动超时时间（秒）
        """
        self.timeout = timeout
        self.progress = StartupProgress()
        self.callbacks: list[Callable[[StartupProgress], Awaitable[None]]] = []
        self._failed = False
        self._error_message: Optional[str] = None
        self._errors: List[ErrorInfo] = []
        self._gpu_info: Dict[str, Any] = {}
    
    def register_callback(self, callback: Callable[[StartupProgress], Awaitable[None]]) -> None:
        """
        注册进度回调函数
        
        Args:
            callback: 进度回调函数
        """
        self.callbacks.append(callback)
    
    async def _notify_progress(self) -> None:
        """通知进度更新"""
        for callback in self.callbacks:
            try:
                await callback(self.progress)
            except Exception as e:
                logger.error(f"进度回调失败：{e}")
    
    def update_phase(self, phase: StartupPhase, message: str = "") -> None:
        """
        更新启动阶段
        
        Args:
            phase: 启动阶段
            message: 阶段消息
        """
        self.progress.phase = phase
        if message:
            logger.info(f"[{phase.value.upper()}] {message}")
    
    def register_component(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        注册组件
        
        Args:
            name: 组件名称
            metadata: 组件元数据
        """
        component = ComponentInfo(
            name=name,
            status=ComponentStatus.PENDING,
            metadata=metadata or {}
        )
        self.progress.components[name] = component
        logger.debug(f"注册组件：{name}")
    
    def update_component_status(
        self,
        name: str,
        status: ComponentStatus,
        progress: int = 0,
        message: str = "",
        error: Optional[str] = None
    ) -> None:
        """
        更新组件状态
        
        Args:
            name: 组件名称
            status: 组件状态
            progress: 加载进度（0-100）
            message: 状态消息
            error: 错误信息
        """
        if name not in self.progress.components:
            self.register_component(name)
        
        component = self.progress.components[name]
        component.status = status
        component.progress = min(100, max(0, progress))
        component.message = message
        component.error = error
        
        if status == ComponentStatus.READY:
            component.load_time = time.time() - self.progress.start_time
        
        self.progress.current_component = name
        self._calculate_overall_progress()
    
    def add_error(self, component: str, error_message: str, suggestion: str = "") -> None:
        """
        添加错误信息
        
        Args:
            component: 组件名称
            error_message: 错误消息
            suggestion: 修复建议
        """
        error_info = ErrorInfo(
            component=component,
            error_message=error_message,
            suggestion=suggestion or self._get_default_suggestion(component, error_message)
        )
        self._errors.append(error_info)
        logger.error(f"[{component}] 错误: {error_message}")
        if error_info.suggestion:
            logger.info(f"[{component}] 建议: {error_info.suggestion}")
    
    def _get_default_suggestion(self, component: str, error_message: str) -> str:
        """
        根据组件和错误信息生成默认建议
        
        Args:
            component: 组件名称
            error_message: 错误消息
        
        Returns:
            修复建议
        """
        suggestions = {
            "yolo": {
                "not found": "检查模型路径是否正确，确保 best.pt 文件存在",
                "load": "检查 YOLO 模型文件是否损坏，尝试重新下载",
                "cuda": "检查 GPU 驱动和 CUDA 版本是否兼容"
            },
            "qwen": {
                "not found": "检查 Qwen 模型目录是否存在",
                "memory": "GPU 显存不足，尝试关闭其他程序或使用 CPU 模式",
                "cuda": "检查 GPU 驱动和 CUDA 版本，确保支持 INT4 量化",
                "load": "检查模型文件完整性，尝试重新下载"
            },
            "database": {
                "connection": "检查数据库服务是否启动，连接参数是否正确",
                "auth": "检查数据库用户名和密码是否正确"
            },
            "graphrag": {
                "connection": "检查 Neo4j 服务是否启动，端口是否正确",
                "auth": "检查 Neo4j 用户名和密码是否正确"
            }
        }
        
        component_suggestions = suggestions.get(component, {})
        error_lower = error_message.lower()
        
        for key, suggestion in component_suggestions.items():
            if key in error_lower:
                return suggestion
        
        return "检查相关配置和日志，确保依赖服务正常运行"
    
    def set_gpu_info(self, gpu_info: Dict[str, Any]) -> None:
        """
        设置 GPU 信息
        
        Args:
            gpu_info: GPU 信息字典
        """
        self._gpu_info = gpu_info
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        获取设备信息（GPU/CPU）
        
        Returns:
            设备信息字典
        """
        try:
            from ..utils.gpu_monitor import get_device_info
            return get_device_info()
        except ImportError:
            return {
                "cuda_available": False,
                "device_count": 0,
                "devices": [],
                "message": "GPU 监控模块未安装"
            }
    
    def _calculate_overall_progress(self) -> None:
        """计算总体进度"""
        if not self.progress.components:
            return
        
        weights = {
            StartupPhase.INIT: 0.2,
            StartupPhase.DATABASE: 0.2,
            StartupPhase.AI_LOADING: 0.5,
            StartupPhase.SERVICES: 0.1,
            StartupPhase.READY: 0.0
        }
        
        phase_weight = weights.get(self.progress.phase, 0.0)
        
        if self.progress.components:
            avg_progress = sum(c.progress for c in self.progress.components.values()) / len(self.progress.components)
        else:
            avg_progress = 0
        
        phase_start = {
            StartupPhase.INIT: 0,
            StartupPhase.DATABASE: 20,
            StartupPhase.AI_LOADING: 40,
            StartupPhase.SERVICES: 90,
            StartupPhase.READY: 100
        }
        
        phase_base = phase_start.get(self.progress.phase, 0)
        self.progress.overall_progress = min(100, phase_base + int(avg_progress * phase_weight))
    
    def fail(self, error: str) -> None:
        """
        标记启动失败
        
        Args:
            error: 错误信息
        """
        self._failed = True
        self._error_message = error
        self.progress.phase = StartupPhase.FAILED
        logger.error(f"启动失败：{error}")
    
    def is_ready(self) -> bool:
        """检查是否已就绪"""
        return self.progress.phase == StartupPhase.READY and not self._failed
    
    def is_failed(self) -> bool:
        """检查是否失败"""
        return self._failed or self.progress.phase == StartupPhase.FAILED
    
    def is_degraded(self) -> bool:
        """检查是否降级运行"""
        if self._failed:
            return False
        
        for component in self.progress.components.values():
            if component.status == ComponentStatus.DEGRADED:
                return True
        
        return False
    
    def get_errors(self) -> List[ErrorInfo]:
        """获取所有错误信息"""
        return self._errors
    
    def get_error_summary(self) -> str:
        """
        生成错误摘要报告
        
        Returns:
            错误摘要字符串
        """
        if not self._errors:
            return "无错误"
        
        lines = ["=" * 50, "启动错误摘要", "=" * 50]
        
        for i, error in enumerate(self._errors, 1):
            lines.append(f"\n错误 {i}: [{error.component}]")
            lines.append(f"  消息: {error.error_message}")
            if error.suggestion:
                lines.append(f"  建议: {error.suggestion}")
        
        lines.append("\n" + "=" * 50)
        return "\n".join(lines)
    
    def get_startup_report(self) -> str:
        """
        生成启动报告
        
        Returns:
            启动报告字符串
        """
        lines = [
            "=" * 70,
            "WheatAgent 启动报告",
            "=" * 70,
            f"启动时间: {datetime.fromtimestamp(self.progress.start_time).strftime('%Y-%m-%d %H:%M:%S')}",
            f"总耗时: {self.progress.elapsed_time():.2f}秒",
            f"最终状态: {'就绪' if self.is_ready() else '降级' if self.is_degraded() else '失败'}",
            "",
            "组件状态:",
            "-" * 50
        ]
        
        for name, component in self.progress.components.items():
            status_icon = {
                ComponentStatus.READY: "✅",
                ComponentStatus.FAILED: "❌",
                ComponentStatus.DEGRADED: "⚠️",
                ComponentStatus.LOADING: "⏳",
                ComponentStatus.PENDING: "⏸️"
            }.get(component.status, "❓")
            
            lines.append(f"  {status_icon} {name}: {component.status.value} - {component.message}")
            if component.error:
                lines.append(f"      错误: {component.error}")
        
        if self._gpu_info:
            lines.extend([
                "",
                "GPU 信息:",
                "-" * 50
            ])
            if self._gpu_info.get("cuda_available"):
                for device in self._gpu_info.get("devices", []):
                    lines.append(f"  GPU {device['id']}: {device['name']} ({device['total_memory_mb']:.0f}MB)")
            else:
                lines.append(f"  CUDA 不可用: {self._gpu_info.get('message', '未知原因')}")
        
        if self._errors:
            lines.extend([
                "",
                "错误详情:",
                "-" * 50
            ])
            for error in self._errors:
                lines.append(f"  [{error.component}] {error.error_message}")
                if error.suggestion:
                    lines.append(f"    建议: {error.suggestion}")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def get_status(self) -> Dict[str, Any]:
        """获取启动状态"""
        return {
            "status": "ready" if self.is_ready() else ("failed" if self.is_failed() else "degraded" if self.is_degraded() else "starting"),
            "progress": self.progress.to_dict(),
            "is_ready": self.is_ready(),
            "is_failed": self.is_failed(),
            "is_degraded": self.is_degraded(),
            "error": self._error_message,
            "errors": [e.to_dict() for e in self._errors],
            "gpu_info": self._gpu_info
        }
    
    async def wait_for_ready(self, poll_interval: float = 1.0) -> bool:
        """
        等待启动完成
        
        Args:
            poll_interval: 轮询间隔（秒）
        
        Returns:
            是否成功启动
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            if self.is_ready():
                return True
            
            if self.is_failed():
                return False
            
            await asyncio.sleep(poll_interval)
        
        self.fail(f"启动超时（{self.timeout}秒）")
        return False


startup_manager: Optional[StartupManager] = None


def get_startup_manager() -> StartupManager:
    """获取启动管理器实例"""
    global startup_manager
    if startup_manager is None:
        startup_manager = StartupManager(timeout=120.0)
    return startup_manager


def initialize_startup_manager(timeout: float = 120.0) -> StartupManager:
    """初始化启动管理器"""
    global startup_manager
    startup_manager = StartupManager(timeout=timeout)
    logger.info(f"启动管理器已初始化（超时={timeout}秒）")
    return startup_manager
