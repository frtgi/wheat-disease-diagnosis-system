"""
QwenModelLoader.__new__() API 兼容性修复单元测试

验证 __new__ 签名从 def __new__(cls) 改为 def __new__(cls, *args, **kwargs) 后：
1. QwenModelLoader(lazy_load=True/False) 不再抛 TypeError
2. 单例模式仍然正常工作
3. get_model_loader() 函数正常工作
"""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestQwenModelLoaderNewSignature:
    """
    测试 QwenModelLoader.__new__() 签名兼容性修复

    覆盖场景：
    - 带关键字参数的构造调用（lazy_load=True/False）
    - 单例模式正确性
    - get_model_loader() 工厂函数
    """

    @pytest.fixture(autouse=True)
    def _reset_singleton(self):
        """
        每个测试前重置单例状态，确保测试隔离

        通过重置 _instance 和 _initialized 保证每个测试从干净状态开始
        """
        from app.services.qwen.qwen_loader import QwenModelLoader
        QwenModelLoader._instance = None
        yield
        QwenModelLoader._instance = None

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_lazy_load_true_no_type_error(self):
        """
        测试 QwenModelLoader(lazy_load=True) 不抛 TypeError

        验证修复后的 __new__(cls, *args, **kwargs) 签名可以正确接收
        lazy_load=True 关键字参数并透传给 __init__
        """
        from app.services.qwen.qwen_loader import QwenModelLoader

        instance = QwenModelLoader(lazy_load=True)

        assert instance is not None
        assert instance.is_lazy_load is True
        assert instance.get_state().value == "unloaded"

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_lazy_load_false_no_type_error(self):
        """
        测试 QwenModelLoader(lazy_load=False) 不抛 TypeError

        验证 lazy_load=False 关键字参数也能正常传递
        """
        from app.services.qwen.qwen_loader import QwenModelLoader

        instance = QwenModelLoader(lazy_load=False)

        assert instance is not None
        assert instance.is_lazy_load is False
        assert instance.get_state().value == "loading"

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_no_args_still_works(self):
        """
        测试无参数构造仍然正常工作

        确保向后兼容：不传参数时使用默认值 lazy_load=True
        """
        from app.services.qwen.qwen_loader import QwenModelLoader

        instance = QwenModelLoader()

        assert instance is not None
        assert instance.is_lazy_load is True

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_singleton_pattern_with_kwargs(self):
        """
        测试带关键字参数时单例模式仍然正常

        多次调用 QwenModelLoader(lazy_load=...) 应返回同一个实例
        """
        from app.services.qwen.qwen_loader import QwenModelLoader

        instance1 = QwenModelLoader(lazy_load=True)
        instance2 = QwenModelLoader(lazy_load=False)

        assert instance1 is instance2, "单例模式失效：两次调用返回了不同实例"

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_singleton_idempotent_init(self):
        """
        测试单例的 __init__ 幂等性

        单例首次创建后，后续调用不应重新初始化属性（_initialized 守卫）
        """
        from app.services.qwen.qwen_loader import QwenModelLoader

        instance1 = QwenModelLoader(lazy_load=True)
        original_id = id(instance1)

        instance2 = QwenModelLoader(lazy_load=False)

        assert id(instance2) == original_id
        assert instance2.is_lazy_load is True, "单例属性不应被第二次调用覆盖"

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_get_model_loader_lazy_true(self):
        """
        测试 get_model_loader(lazy_load=True) 正常工作

        get_model_loader 是工厂函数，内部调用 QwenModelLoader(lazy_load=...)
        """
        from app.services.qwen.qwen_loader import get_model_loader, QwenModelLoader

        loader = get_model_loader(lazy_load=True)

        assert loader is not None
        assert isinstance(loader, QwenModelLoader)
        assert loader.is_lazy_load is True

    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_get_model_loader_lazy_false(self):
        """
        测试 get_model_loader(lazy_load=False) 正常工作
        """
        from app.services.qwen.qwen_loader import get_model_loader, QwenModelLoader

        loader = get_model_loader(lazy_load=False)

        assert loader is not None
        assert isinstance(loader, QwenModelLoader)
        assert loader.is_lazy_load is False

    @pytest.mark.unit
    @patch.dict(sys.modules, {
        'torch': MagicMock(),
        'PIL': MagicMock(),
        'PIL.Image': MagicMock(),
    })
    def test_get_model_loader_returns_singleton(self):
        """
        测试 get_model_loader 多次调用返回同一单例

        无论 lazy_load 参数如何变化，都应返回同一个实例
        """
        from app.services.qwen.qwen_loader import get_model_loader

        loader1 = get_model_loader(lazy_load=True)
        loader2 = get_model_loader(lazy_load=False)

        assert loader1 is loader2, "get_model_loader 应始终返回同一单例"
