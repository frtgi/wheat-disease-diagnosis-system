# -*- coding: utf-8 -*-
"""
WheatAgent Web 界面模块

提供Gradio交互式Web界面

功能特性:
- 图像诊断: 单张图像病害检测
- 批量诊断: 多张图像批量处理
- 文本诊断: 基于症状描述的诊断
- 知识库查询: 病害信息检索
- 系统状态监控: 引擎状态实时显示
- 报告导出: TXT/JSON格式导出
"""

__all__ = ['create_app', 'WheatAgentWebApp', 'LazyEngineManager']


def __getattr__(name):
    """
    延迟导入，避免 python -m src.web.app 时的 RuntimeWarning
    
    当访问模块属性时才进行实际导入，避免模块被提前加载到 sys.modules
    """
    if name == 'create_app':
        from .app import create_app
        return create_app
    elif name == 'WheatAgentWebApp':
        from .app import WheatAgentWebApp
        return WheatAgentWebApp
    elif name == 'LazyEngineManager':
        from .app import LazyEngineManager
        return LazyEngineManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
