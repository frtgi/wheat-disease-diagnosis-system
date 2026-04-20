"""
模型动态卸载管理模块

提供模型生命周期管理、LRU 缓存策略、内存监控和自动卸载功能
支持多模型按需加载和卸载，优化内存使用
"""
import logging
import time
import threading
import gc
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.services.cache_manager import LRUCache

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """模型状态枚举"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class ModelInfo:
    """模型信息数据类"""
    name: str
    model_type: str
    model_path: Path
    estimated_memory_mb: float
    actual_memory_mb: float = 0.0
    status: ModelStatus = ModelStatus.UNLOADED
    last_access_time: float = field(default_factory=time.time)
    load_time: float = 0.0
    access_count: int = 0
    error_message: str = ""
    model_instance: Any = None
    loader_func: Optional[Callable] = None
    unloader_func: Optional[Callable] = None


@dataclass
class MemoryInfo:
    """内存信息数据类"""
    total_mb: float
    available_mb: float
    used_mb: float
    used_percent: float
    gpu_total_mb: float = 0.0
    gpu_used_mb: float = 0.0
    gpu_available_mb: float = 0.0
    gpu_used_percent: float = 0.0



class ModelManager:
    """
    模型动态卸载管理器
    
    功能特性：
    1. LRU 缓存策略：自动卸载最近最少使用的模型
    2. 内存监控：实时监控系统内存和 GPU 显存使用情况
    3. 自动卸载：当内存使用超过阈值时自动卸载模型
    4. 按需加载：支持模型按需重新加载
    5. 线程安全：使用锁保证并发安全
    
    使用示例：
        manager = ModelManager(
            max_models=3,
            memory_threshold_percent=85.0,
            gpu_memory_threshold_percent=90.0
        )
        
        # 注册模型
        manager.register_model(
            name="yolo",
            model_type="yolo",
            model_path=Path("models/yolo.pt"),
            estimated_memory_mb=500,
            loader_func=load_yolo_model,
            unloader_func=unload_yolo_model
        )
        
        # 获取模型（自动加载）
        model = manager.get_model("yolo")
        
        # 手动卸载模型
        manager.unload_model("yolo")
    """
    
    def __init__(
        self,
        max_models: int = 5,
        memory_threshold_percent: float = 85.0,
        gpu_memory_threshold_percent: float = 90.0,
        auto_unload_enabled: bool = True,
        preload_models: Optional[list] = None
    ):
        """
        初始化模型管理器
        
        Args:
            max_models: 最大同时加载的模型数量
            memory_threshold_percent: 系统内存使用阈值百分比，超过则触发自动卸载
            gpu_memory_threshold_percent: GPU 显存使用阈值百分比，超过则触发自动卸载
            auto_unload_enabled: 是否启用自动卸载
            preload_models: 预加载模型列表（模型名称）
        """
        self._models: Dict[str, ModelInfo] = {}
        self._lru_cache = LRUCache(capacity=max_models, default_ttl=None)
        self._lock = threading.RLock()
        self._max_models = max_models
        self._memory_threshold_percent = memory_threshold_percent
        self._gpu_memory_threshold_percent = gpu_memory_threshold_percent
        self._auto_unload_enabled = auto_unload_enabled
        self._preload_models = preload_models or []
        
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_stop_event = threading.Event()
        self._monitor_interval = 30  # 监控间隔（秒）
        
        self._psutil_available = self._check_psutil()
        
        logger.info(f"ModelManager 初始化完成: max_models={max_models}, "
                   f"memory_threshold={memory_threshold_percent}%, "
                   f"gpu_threshold={gpu_memory_threshold_percent}%")
    
    def _check_psutil(self) -> bool:
        """
        检查 psutil 是否可用
        
        Returns:
            bool: psutil 是否可用
        """
        try:
            import psutil
            return True
        except ImportError:
            logger.warning("psutil 未安装，系统内存监控功能将受限")
            logger.info("安装方法: pip install psutil")
            return False
    
    def register_model(
        self,
        name: str,
        model_type: str,
        model_path: Path,
        estimated_memory_mb: float,
        loader_func: Callable,
        unloader_func: Optional[Callable] = None,
        auto_load: bool = False
    ) -> bool:
        """
        注册模型
        
        Args:
            name: 模型名称（唯一标识）
            model_type: 模型类型（如 "yolo", "qwen"）
            model_path: 模型路径
            estimated_memory_mb: 预估内存占用（MB）
            loader_func: 模型加载函数
            unloader_func: 模型卸载函数（可选）
            auto_load: 是否自动加载
        
        Returns:
            bool: 注册是否成功
        """
        with self._lock:
            if name in self._models:
                logger.warning(f"模型 '{name}' 已存在，将更新配置")
            
            model_info = ModelInfo(
                name=name,
                model_type=model_type,
                model_path=model_path,
                estimated_memory_mb=estimated_memory_mb,
                loader_func=loader_func,
                unloader_func=unloader_func
            )
            
            self._models[name] = model_info
            
            logger.info(f"模型 '{name}' 注册成功: type={model_type}, "
                       f"estimated_memory={estimated_memory_mb}MB")
            
            if auto_load:
                return self.load_model(name)
            
            return True
    
    def unregister_model(self, name: str, force_unload: bool = True) -> bool:
        """
        注销模型
        
        Args:
            name: 模型名称
            force_unload: 是否强制卸载已加载的模型
        
        Returns:
            bool: 注销是否成功
        """
        with self._lock:
            if name not in self._models:
                logger.warning(f"模型 '{name}' 不存在")
                return False
            
            model_info = self._models[name]
            
            if model_info.status == ModelStatus.LOADED:
                if force_unload:
                    self._unload_model_internal(name)
                else:
                    logger.warning(f"模型 '{name}' 已加载，无法注销（force_unload=False）")
                    return False
            
            del self._models[name]
            self._lru_cache.remove(name)
            
            logger.info(f"模型 '{name}' 已注销")
            return True
    
    def load_model(self, name: str, force_reload: bool = False) -> bool:
        """
        加载模型
        
        Args:
            name: 模型名称
            force_reload: 是否强制重新加载
        
        Returns:
            bool: 加载是否成功
        """
        with self._lock:
            if name not in self._models:
                logger.error(f"模型 '{name}' 未注册")
                return False
            
            model_info = self._models[name]
            
            if model_info.status == ModelStatus.LOADED and not force_reload:
                self._update_access(name)
                logger.debug(f"模型 '{name}' 已加载，跳过")
                return True
            
            if model_info.status == ModelStatus.LOADING:
                logger.warning(f"模型 '{name}' 正在加载中")
                return False
            
            return self._load_model_internal(name)
    
    def _load_model_internal(self, name: str) -> bool:
        """
        内部加载模型实现
        
        Args:
            name: 模型名称
        
        Returns:
            bool: 加载是否成功
        """
        model_info = self._models[name]
        model_info.status = ModelStatus.LOADING
        model_info.error_message = ""
        
        try:
            if self._auto_unload_enabled:
                self._check_and_unload_if_needed(model_info.estimated_memory_mb)
            
            if self._lru_cache.get_size() >= self._max_models:
                lru_key = self._lru_cache.get_lru_key()
                if lru_key and lru_key != name:
                    logger.info(f"缓存已满，自动卸载最久未使用的模型: {lru_key}")
                    self._unload_model_internal(lru_key)
            
            logger.info(f"开始加载模型 '{name}'...")
            start_time = time.time()
            
            if model_info.loader_func is None:
                raise ValueError(f"模型 '{name}' 未配置加载函数")
            
            model_instance = model_info.loader_func()
            
            load_time = time.time() - start_time
            actual_memory = self._measure_model_memory(name)
            
            model_info.model_instance = model_instance
            model_info.status = ModelStatus.LOADED
            model_info.load_time = load_time
            model_info.actual_memory_mb = actual_memory
            model_info.last_access_time = time.time()
            model_info.access_count += 1
            
            self._lru_cache.put(name, name)
            
            logger.info(f"模型 '{name}' 加载成功: load_time={load_time:.2f}s, "
                       f"actual_memory={actual_memory:.0f}MB")
            
            return True
            
        except Exception as e:
            error_msg = f"模型 '{name}' 加载失败: {e}"
            logger.error(error_msg)
            model_info.status = ModelStatus.ERROR
            model_info.error_message = str(e)
            return False
    
    def unload_model(self, name: str) -> bool:
        """
        卸载模型
        
        Args:
            name: 模型名称
        
        Returns:
            bool: 卸载是否成功
        """
        with self._lock:
            return self._unload_model_internal(name)
    
    def _unload_model_internal(self, name: str) -> bool:
        """
        内部卸载模型实现
        
        Args:
            name: 模型名称
        
        Returns:
            bool: 卸载是否成功
        """
        if name not in self._models:
            logger.warning(f"模型 '{name}' 不存在")
            return False
        
        model_info = self._models[name]
        
        if model_info.status != ModelStatus.LOADED:
            logger.debug(f"模型 '{name}' 未加载，无需卸载")
            return True
        
        model_info.status = ModelStatus.UNLOADING
        
        try:
            logger.info(f"开始卸载模型 '{name}'...")
            
            if model_info.unloader_func is not None:
                model_info.unloader_func(model_info.model_instance)
            elif model_info.model_instance is not None:
                self._default_unloader(model_info.model_instance)
            
            model_info.model_instance = None
            model_info.status = ModelStatus.UNLOADED
            model_info.actual_memory_mb = 0
            
            self._lru_cache.remove(name)
            
            self._cleanup_memory()
            
            logger.info(f"模型 '{name}' 卸载成功")
            return True
            
        except Exception as e:
            error_msg = f"模型 '{name}' 卸载失败: {e}"
            logger.error(error_msg)
            model_info.status = ModelStatus.ERROR
            model_info.error_message = str(e)
            return False
    
    def _default_unloader(self, model_instance: Any):
        """
        默认卸载函数
        
        Args:
            model_instance: 模型实例
        """
        try:
            import torch
            
            if hasattr(model_instance, 'to'):
                try:
                    model_instance.to('cpu')
                except Exception:
                    pass
            
            if hasattr(model_instance, 'cpu'):
                try:
                    model_instance.cpu()
                except Exception:
                    pass
            
            del model_instance
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            gc.collect()
            
        except Exception as e:
            logger.warning(f"默认卸载函数执行失败: {e}")
    
    def get_model(self, name: str, auto_load: bool = True) -> Optional[Any]:
        """
        获取模型实例
        
        Args:
            name: 模型名称
            auto_load: 如果模型未加载，是否自动加载
        
        Returns:
            模型实例，失败返回 None
        """
        with self._lock:
            if name not in self._models:
                logger.error(f"模型 '{name}' 未注册")
                return None
            
            model_info = self._models[name]
            
            if model_info.status != ModelStatus.LOADED:
                if auto_load:
                    if not self.load_model(name):
                        return None
                else:
                    logger.warning(f"模型 '{name}' 未加载")
                    return None
            
            self._update_access(name)
            return model_info.model_instance
    
    def _update_access(self, name: str):
        """
        更新模型访问记录
        
        Args:
            name: 模型名称
        """
        if name in self._models:
            self._models[name].last_access_time = time.time()
            self._models[name].access_count += 1
            self._lru_cache.put(name, name)
    
    def get_model_status(self, name: str) -> Optional[ModelStatus]:
        """
        获取模型状态
        
        Args:
            name: 模型名称
        
        Returns:
            模型状态，不存在返回 None
        """
        with self._lock:
            if name in self._models:
                return self._models[name].status
            return None
    
    def get_model_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型详细信息
        
        Args:
            name: 模型名称
        
        Returns:
            模型信息字典，不存在返回 None
        """
        with self._lock:
            if name not in self._models:
                return None
            
            model_info = self._models[name]
            return {
                "name": model_info.name,
                "model_type": model_info.model_type,
                "model_path": str(model_info.model_path),
                "estimated_memory_mb": model_info.estimated_memory_mb,
                "actual_memory_mb": model_info.actual_memory_mb,
                "status": model_info.status.value,
                "last_access_time": datetime.fromtimestamp(model_info.last_access_time).isoformat(),
                "load_time": model_info.load_time,
                "access_count": model_info.access_count,
                "error_message": model_info.error_message
            }
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有模型信息
        
        Returns:
            模型信息字典
        """
        with self._lock:
            return {name: self.get_model_info(name) for name in self._models}
    
    def get_loaded_models(self) -> list:
        """
        获取已加载的模型列表
        
        Returns:
            已加载模型名称列表
        """
        with self._lock:
            return [
                name for name, info in self._models.items()
                if info.status == ModelStatus.LOADED
            ]
    
    def get_memory_info(self) -> MemoryInfo:
        """
        获取内存信息
        
        Returns:
            MemoryInfo: 内存信息对象
        """
        memory_info = MemoryInfo(
            total_mb=0,
            available_mb=0,
            used_mb=0,
            used_percent=0
        )
        
        if self._psutil_available:
            try:
                import psutil
                mem = psutil.virtual_memory()
                memory_info.total_mb = mem.total / (1024 ** 2)
                memory_info.available_mb = mem.available / (1024 ** 2)
                memory_info.used_mb = mem.used / (1024 ** 2)
                memory_info.used_percent = mem.percent
            except Exception as e:
                logger.warning(f"获取系统内存信息失败: {e}")
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_total = torch.cuda.get_device_properties(0).total_memory
                gpu_allocated = torch.cuda.memory_allocated(0)
                gpu_reserved = torch.cuda.memory_reserved(0)
                
                memory_info.gpu_total_mb = gpu_total / (1024 ** 2)
                memory_info.gpu_used_mb = max(gpu_allocated, gpu_reserved) / (1024 ** 2)
                memory_info.gpu_available_mb = memory_info.gpu_total_mb - memory_info.gpu_used_mb
                memory_info.gpu_used_percent = (memory_info.gpu_used_mb / memory_info.gpu_total_mb * 100) if memory_info.gpu_total_mb > 0 else 0
        except Exception as e:
            logger.debug(f"获取 GPU 内存信息失败: {e}")
        
        return memory_info
    
    def _measure_model_memory(self, name: str) -> float:
        """
        测量模型实际内存占用
        
        Args:
            name: 模型名称
        
        Returns:
            float: 内存占用（MB）
        """
        try:
            import torch
            if torch.cuda.is_available():
                allocated_before = torch.cuda.memory_allocated(0)
                
                torch.cuda.synchronize()
                allocated_after = torch.cuda.memory_allocated(0)
                
                return (allocated_after - allocated_before) / (1024 ** 2)
        except Exception:
            pass
        
        return self._models[name].estimated_memory_mb
    
    def _check_and_unload_if_needed(self, required_memory_mb: float):
        """
        检查内存并在需要时卸载模型
        
        Args:
            required_memory_mb: 所需内存（MB）
        """
        memory_info = self.get_memory_info()
        
        system_memory_high = memory_info.used_percent >= self._memory_threshold_percent
        gpu_memory_high = memory_info.gpu_used_percent >= self._gpu_memory_threshold_percent
        
        if not (system_memory_high or gpu_memory_high):
            return
        
        logger.warning(f"内存使用过高: system={memory_info.used_percent:.1f}%, "
                      f"gpu={memory_info.gpu_used_percent:.1f}%")
        
        loaded_models = self._get_loaded_models_sorted_by_lru()
        
        for model_name in loaded_models:
            if memory_info.used_percent < self._memory_threshold_percent and \
               memory_info.gpu_used_percent < self._gpu_memory_threshold_percent:
                break
            
            logger.info(f"自动卸载模型 '{model_name}' 以释放内存")
            self._unload_model_internal(model_name)
            
            memory_info = self.get_memory_info()
    
    def _get_loaded_models_sorted_by_lru(self) -> list:
        """
        获取按 LRU 排序的已加载模型列表
        
        Returns:
            模型名称列表（最久未使用的在前）
        """
        loaded_models = self.get_loaded_models()
        lru_keys = self._lru_cache.get_keys()
        
        sorted_models = [name for name in lru_keys if name in loaded_models]
        
        for name in loaded_models:
            if name not in sorted_models:
                sorted_models.append(name)
        
        return sorted_models
    
    def _cleanup_memory(self):
        """清理内存"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except Exception:
            pass
        
        gc.collect()
    
    def start_monitor(self, interval: int = 30):
        """
        启动内存监控线程
        
        Args:
            interval: 监控间隔（秒）
        """
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.warning("监控线程已在运行")
            return
        
        self._monitor_interval = interval
        self._monitor_stop_event.clear()
        
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ModelManager-Monitor"
        )
        self._monitor_thread.start()
        
        logger.info(f"内存监控线程已启动，间隔 {interval} 秒")
    
    def stop_monitor(self):
        """停止内存监控线程"""
        if self._monitor_thread is None:
            return
        
        self._monitor_stop_event.set()
        self._monitor_thread.join(timeout=5)
        self._monitor_thread = None
        
        logger.info("内存监控线程已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._monitor_stop_event.is_set():
            try:
                self._check_memory_and_unload()
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
            
            self._monitor_stop_event.wait(self._monitor_interval)
    
    def _check_memory_and_unload(self):
        """检查内存并在需要时卸载模型"""
        if not self._auto_unload_enabled:
            return
        
        memory_info = self.get_memory_info()
        
        system_memory_high = memory_info.used_percent >= self._memory_threshold_percent
        gpu_memory_high = memory_info.gpu_used_percent >= self._gpu_memory_threshold_percent
        
        if not (system_memory_high or gpu_memory_high):
            return
        
        logger.warning(f"监控检测到内存使用过高: system={memory_info.used_percent:.1f}%, "
                      f"gpu={memory_info.gpu_used_percent:.1f}%")
        
        with self._lock:
            loaded_models = self._get_loaded_models_sorted_by_lru()
            
            for model_name in loaded_models:
                self._unload_model_internal(model_name)
                
                memory_info = self.get_memory_info()
                
                if memory_info.used_percent < self._memory_threshold_percent and \
                   memory_info.gpu_used_percent < self._gpu_memory_threshold_percent:
                    break
    
    def preload_models(self, model_names: Optional[list] = None):
        """
        预加载模型
        
        Args:
            model_names: 要预加载的模型名称列表，None 则使用初始化时配置的列表
        """
        names = model_names or self._preload_models
        
        for name in names:
            if name in self._models:
                logger.info(f"预加载模型: {name}")
                self.load_model(name)
            else:
                logger.warning(f"预加载失败: 模型 '{name}' 未注册")
    
    def unload_all(self):
        """卸载所有模型"""
        with self._lock:
            for name in list(self._models.keys()):
                if self._models[name].status == ModelStatus.LOADED:
                    self._unload_model_internal(name)
            
            self._cleanup_memory()
            logger.info("所有模型已卸载")
    
    def clear(self):
        """清空所有模型"""
        self.unload_all()
        
        with self._lock:
            self._models.clear()
            self._lru_cache.clear()
        
        logger.info("模型管理器已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            memory_info = self.get_memory_info()
            
            loaded_count = sum(1 for info in self._models.values() if info.status == ModelStatus.LOADED)
            total_count = len(self._models)
            total_estimated_memory = sum(info.estimated_memory_mb for info in self._models.values() if info.status == ModelStatus.LOADED)
            total_actual_memory = sum(info.actual_memory_mb for info in self._models.values() if info.status == ModelStatus.LOADED)
            
            return {
                "total_models": total_count,
                "loaded_models": loaded_count,
                "max_models": self._max_models,
                "total_estimated_memory_mb": total_estimated_memory,
                "total_actual_memory_mb": total_actual_memory,
                "memory_threshold_percent": self._memory_threshold_percent,
                "gpu_memory_threshold_percent": self._gpu_memory_threshold_percent,
                "system_memory": {
                    "total_mb": memory_info.total_mb,
                    "used_mb": memory_info.used_mb,
                    "available_mb": memory_info.available_mb,
                    "used_percent": memory_info.used_percent
                },
                "gpu_memory": {
                    "total_mb": memory_info.gpu_total_mb,
                    "used_mb": memory_info.gpu_used_mb,
                    "available_mb": memory_info.gpu_available_mb,
                    "used_percent": memory_info.gpu_used_percent
                },
                "auto_unload_enabled": self._auto_unload_enabled,
                "monitor_running": self._monitor_thread is not None and self._monitor_thread.is_alive()
            }


_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """
    获取模型管理器单例
    
    Returns:
        ModelManager 实例
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def init_model_manager(
    max_models: int = 5,
    memory_threshold_percent: float = 85.0,
    gpu_memory_threshold_percent: float = 90.0,
    auto_unload_enabled: bool = True,
    preload_models: Optional[list] = None
) -> ModelManager:
    """
    初始化模型管理器
    
    Args:
        max_models: 最大同时加载的模型数量
        memory_threshold_percent: 系统内存使用阈值百分比
        gpu_memory_threshold_percent: GPU 显存使用阈值百分比
        auto_unload_enabled: 是否启用自动卸载
        preload_models: 预加载模型列表
    
    Returns:
        ModelManager 实例
    """
    global _model_manager
    _model_manager = ModelManager(
        max_models=max_models,
        memory_threshold_percent=memory_threshold_percent,
        gpu_memory_threshold_percent=gpu_memory_threshold_percent,
        auto_unload_enabled=auto_unload_enabled,
        preload_models=preload_models
    )
    return _model_manager
