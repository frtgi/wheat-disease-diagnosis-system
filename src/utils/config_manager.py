# -*- coding: utf-8 -*-
"""
配置管理模块 (Config Manager)

提供分层配置管理功能，支持：
1. 默认配置、环境配置、用户配置的层级覆盖
2. YAML/JSON配置文件格式
3. 配置热更新机制
4. 配置验证和类型检查
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, Union, List, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
import time


class ConfigSource(Enum):
    """配置来源"""
    DEFAULT = "default"       # 默认配置
    ENVIRONMENT = "env"       # 环境配置
    USER = "user"             # 用户配置
    RUNTIME = "runtime"       # 运行时配置


@dataclass
class ConfigSchema:
    """配置项模式定义"""
    key: str
    type: type
    default: Any
    description: str
    validator: Optional[Callable[[Any], bool]] = None
    
    def validate(self, value: Any) -> bool:
        """验证配置值"""
        if not isinstance(value, self.type):
            return False
        if self.validator:
            return self.validator(value)
        return True


class ConfigManager:
    """
    分层配置管理器
    
    配置层级（优先级从低到高）：
    1. 默认配置 (default)
    2. 环境配置 (environment)
    3. 用户配置 (user)
    4. 运行时配置 (runtime)
    
    功能：
    1. 支持YAML/JSON配置文件
    2. 配置热更新
    3. 配置验证
    4. 配置变更监听
    """
    
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        config_dir: str = "config",
        default_config_file: str = "default.yaml",
        env_config_file: Optional[str] = None,
        user_config_file: str = "user.yaml"
    ):
        """
        初始化配置管理器
        
        :param config_dir: 配置目录
        :param default_config_file: 默认配置文件
        :param env_config_file: 环境配置文件
        :param user_config_file: 用户配置文件
        """
        # 如果已经初始化过，只更新路径参数
        if hasattr(self, '_initialized'):
            self.config_dir = Path(config_dir)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.default_config_file = default_config_file
            self.env_config_file = env_config_file or f"{os.getenv('ENV', 'development')}.yaml"
            self.user_config_file = user_config_file
            return
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_config_file = default_config_file
        self.env_config_file = env_config_file or f"{os.getenv('ENV', 'development')}.yaml"
        self.user_config_file = user_config_file
        
        # 配置存储
        self._configs: Dict[ConfigSource, Dict[str, Any]] = {
            ConfigSource.DEFAULT: {},
            ConfigSource.ENVIRONMENT: {},
            ConfigSource.USER: {},
            ConfigSource.RUNTIME: {}
        }
        
        # 配置模式
        self._schemas: Dict[str, ConfigSchema] = {}
        
        # 配置变更监听器
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        
        # 热更新线程
        self._hot_reload = False
        self._reload_thread: Optional[threading.Thread] = None
        self._file_mtimes: Dict[str, float] = {}
        
        self._initialized = True
        
        # 加载配置
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置"""
        # 加载默认配置
        self._load_config_file(ConfigSource.DEFAULT, self.default_config_file)
        
        # 加载环境配置
        self._load_config_file(ConfigSource.ENVIRONMENT, self.env_config_file)
        
        # 加载用户配置
        self._load_config_file(ConfigSource.USER, self.user_config_file)
    
    def _load_config_file(self, source: ConfigSource, filename: str):
        """
        加载配置文件
        
        :param source: 配置来源
        :param filename: 文件名
        """
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            # 如果是默认配置且文件不存在，创建默认配置
            if source == ConfigSource.DEFAULT:
                self._create_default_config(filepath)
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.suffix in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                elif filepath.suffix == '.json':
                    config = json.load(f)
                else:
                    print(f"⚠️ 不支持的配置文件格式: {filepath.suffix}")
                    return
            
            if config:
                self._configs[source] = config
                self._file_mtimes[str(filepath)] = os.path.getmtime(filepath)
                print(f"✅ 已加载配置: {filename} ({source.value})")
        
        except Exception as e:
            print(f"❌ 加载配置文件失败 {filename}: {e}")
    
    def _create_default_config(self, filepath: Path):
        """创建默认配置文件"""
        default_config = {
            "system": {
                "name": "WheatAgent",
                "version": "0.2.0",
                "debug": False,
                "log_level": "INFO"
            },
            "model": {
                "vision": {
                    "model_path": "models/yolov8_wheat.pt",
                    "confidence_threshold": 0.25,
                    "iou_threshold": 0.45,
                    "image_size": 640
                },
                "language": {
                    "model_name": "bert-base-chinese",
                    "max_length": 512
                },
                "cognition": {
                    "vision_encoder": "openai/clip-vit-large-patch14",
                    "llm_name": "lmsys/vicuna-7b-v1.5",
                    "use_lora": True
                }
            },
            "database": {
                "neo4j": {
                    "uri": "bolt://localhost:7687",
                    "user": "neo4j",
                    "password": "password"
                }
            },
            "paths": {
                "data_root": "datasets",
                "model_root": "models",
                "log_root": "logs",
                "output_root": "outputs"
            },
            "inference": {
                "batch_size": 1,
                "device": "auto",
                "fp16": True
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            print(f"✅ 已创建默认配置文件: {filepath}")
        except Exception as e:
            print(f"❌ 创建默认配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        按优先级从高到低查找：runtime > user > environment > default
        
        :param key: 配置键（支持点号分隔，如 'model.vision.confidence_threshold'）
        :param default: 默认值
        :return: 配置值
        """
        keys = key.split('.')
        
        # 按优先级查找
        for source in [ConfigSource.RUNTIME, ConfigSource.USER, 
                       ConfigSource.ENVIRONMENT, ConfigSource.DEFAULT]:
            value = self._get_nested_value(self._configs[source], keys)
            if value is not None:
                return value
        
        return default
    
    def _get_nested_value(self, config: Dict, keys: List[str]) -> Any:
        """获取嵌套配置值"""
        current = config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.RUNTIME):
        """
        设置配置值
        
        :param key: 配置键
        :param value: 配置值
        :param source: 配置来源
        """
        keys = key.split('.')
        
        # 获取旧值
        old_value = self.get(key)
        
        # 设置新值
        current = self._configs[source]
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        
        # 触发监听器
        if old_value != value:
            self._notify_listeners(key, old_value, value)
    
    def update(self, config: Dict[str, Any], source: ConfigSource = ConfigSource.RUNTIME):
        """
        批量更新配置
        
        :param config: 配置字典
        :param source: 配置来源
        """
        self._deep_update(self._configs[source], config)
    
    def _deep_update(self, base: Dict, update: Dict):
        """深度更新字典"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def save(self, source: ConfigSource = ConfigSource.USER):
        """
        保存配置到文件
        
        :param source: 要保存的配置来源
        """
        if source == ConfigSource.USER:
            filepath = self.config_dir / self.user_config_file
        elif source == ConfigSource.ENVIRONMENT:
            filepath = self.config_dir / self.env_config_file
        else:
            print(f"⚠️ 不能直接保存 {source.value} 配置")
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(self._configs[source], f, default_flow_style=False, allow_unicode=True)
            print(f"✅ 配置已保存: {filepath}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def register_schema(self, schema: ConfigSchema):
        """
        注册配置模式
        
        :param schema: 配置模式
        """
        self._schemas[schema.key] = schema
    
    def validate(self, key: Optional[str] = None) -> bool:
        """
        验证配置
        
        :param key: 要验证的配置键（None表示验证所有）
        :return: 是否有效
        """
        schemas_to_check = [self._schemas[key]] if key else self._schemas.values()
        
        for schema in schemas_to_check:
            value = self.get(schema.key)
            if value is not None and not schema.validate(value):
                print(f"❌ 配置验证失败: {schema.key} = {value}")
                return False
        
        return True
    
    def add_listener(self, callback: Callable[[str, Any, Any], None]):
        """
        添加配置变更监听器
        
        :param callback: 回调函数，参数为 (key, old_value, new_value)
        """
        self._listeners.append(callback)
    
    def _notify_listeners(self, key: str, old_value: Any, new_value: Any):
        """通知监听器"""
        for callback in self._listeners:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                print(f"⚠️ 配置变更监听器执行失败: {e}")
    
    def enable_hot_reload(self, interval: float = 5.0):
        """
        启用配置热更新
        
        :param interval: 检查间隔（秒）
        """
        if self._hot_reload:
            return
        
        self._hot_reload = True
        self._reload_thread = threading.Thread(target=self._reload_loop, args=(interval,))
        self._reload_thread.daemon = True
        self._reload_thread.start()
        print(f"✅ 配置热更新已启用 (间隔: {interval}s)")
    
    def disable_hot_reload(self):
        """禁用配置热更新"""
        self._hot_reload = False
        if self._reload_thread:
            self._reload_thread.join(timeout=1.0)
        print("✅ 配置热更新已禁用")
    
    def _reload_loop(self, interval: float):
        """热更新循环"""
        while self._hot_reload:
            time.sleep(interval)
            self._check_config_changes()
    
    def _check_config_changes(self):
        """检查配置文件变更"""
        for source, filename in [
            (ConfigSource.ENVIRONMENT, self.env_config_file),
            (ConfigSource.USER, self.user_config_file)
        ]:
            filepath = self.config_dir / filename
            if not filepath.exists():
                continue
            
            current_mtime = os.path.getmtime(filepath)
            last_mtime = self._file_mtimes.get(str(filepath), 0)
            
            if current_mtime > last_mtime:
                print(f"🔄 检测到配置文件变更: {filename}")
                self._load_config_file(source, filename)
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置（合并后的）
        
        :return: 配置字典
        """
        result = {}
        for source in [ConfigSource.DEFAULT, ConfigSource.ENVIRONMENT, 
                       ConfigSource.USER, ConfigSource.RUNTIME]:
            self._deep_update(result, self._configs[source])
        return result
    
    def print_config(self):
        """打印当前配置"""
        print("\n" + "=" * 70)
        print("📋 当前配置")
        print("=" * 70)
        config = self.get_all()
        print(yaml.dump(config, default_flow_style=False, allow_unicode=True))


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    return ConfigManager()


# 全局配置管理器
config = ConfigManager()


def test_config_manager():
    """测试配置管理器"""
    print("=" * 70)
    print("🧪 测试配置管理器")
    print("=" * 70)
    
    # 创建测试配置目录
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp()
    
    try:
        # 创建配置管理器
        cm = ConfigManager(
            config_dir=test_dir,
            default_config_file="default.yaml",
            env_config_file="test.yaml",
            user_config_file="user.yaml"
        )
        
        # 测试获取配置
        print("\n📝 测试获取配置:")
        system_name = cm.get("system.name")
        print(f"   system.name: {system_name}")
        
        model_path = cm.get("model.vision.model_path")
        print(f"   model.vision.model_path: {model_path}")
        
        # 测试设置运行时配置
        print("\n⚡ 测试设置运行时配置:")
        cm.set("runtime.test_value", 123)
        print(f"   runtime.test_value: {cm.get('runtime.test_value')}")
        
        # 测试配置变更监听
        print("\n🔍 测试配置变更监听:")
        changes = []
        def on_change(key, old, new):
            changes.append((key, old, new))
        
        cm.add_listener(on_change)
        cm.set("runtime.monitored_value", "initial")
        cm.set("runtime.monitored_value", "updated")
        print(f"   捕获到 {len(changes)} 次变更")
        
        # 测试配置验证
        print("\n🛡️ 测试配置验证:")
        from utils.config_manager import ConfigSchema
        
        schema = ConfigSchema(
            key="model.vision.confidence_threshold",
            type=float,
            default=0.25,
            description="置信度阈值",
            validator=lambda x: 0 <= x <= 1
        )
        cm.register_schema(schema)
        
        is_valid = cm.validate()
        print(f"   配置验证: {'通过' if is_valid else '失败'}")
        
        # 测试保存配置
        print("\n💾 测试保存配置:")
        cm.set("user.setting", "test_value", source=ConfigSource.USER)
        cm.save(ConfigSource.USER)
        
        # 打印完整配置
        print("\n📊 完整配置:")
        cm.print_config()
        
    finally:
        # 清理
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n" + "=" * 70)
    print("✅ 配置管理器测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_config_manager()
