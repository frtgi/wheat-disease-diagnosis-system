# -*- coding: utf-8 -*-
"""
工具基类 - Base Tool
定义所有工具的通用接口和规范
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class BaseTool(ABC):
    """
    工具基类（抽象类）
    
    所有工具类都必须继承此类，并实现以下抽象方法：
    - get_name(): 获取工具名称
    - get_description(): 获取工具描述
    - execute(): 执行工具功能
    
    属性:
        name: 工具名称
        description: 工具描述
        version: 工具版本号
        created_at: 创建时间
        is_available: 工具是否可用
    """
    
    def __init__(self, name: str = "BaseTool", description: str = "基础工具"):
        """
        初始化工具基类
        
        :param name: 工具名称
        :param description: 工具描述
        """
        self.name = name
        self.description = description
        self.version = "1.0.0"
        self.created_at = datetime.now()
        self.is_available = True
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取工具名称
        
        :return: 工具名称字符串
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取工具描述
        
        :return: 工具描述字符串
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具功能（核心方法）
        
        :param kwargs: 工具执行所需的参数
        :return: 执行结果字典，包含：
            - success: 是否执行成功
            - data: 执行结果数据
            - message: 执行消息
            - error: 错误信息（如果失败）
        """
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证输入参数
        
        :param kwargs: 输入参数
        :return: 参数是否有效
        """
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取工具元数据
        
        :return: 工具元数据字典
        """
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "is_available": self.is_available
        }
    
    def initialize(self) -> bool:
        """
        初始化工具（可选的重写方法）
        
        :return: 初始化是否成功
        """
        return True
    
    def cleanup(self) -> None:
        """
        清理工具资源（可选的重写方法）
        """
        pass
    
    def __str__(self) -> str:
        """
        工具的字符串表示
        
        :return: 工具描述字符串
        """
        return f"{self.get_name()}: {self.get_description()}"
