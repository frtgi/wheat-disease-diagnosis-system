# -*- coding: utf-8 -*-
"""
记忆层模块 - Memory Layer
IWDDA Agent 反馈记忆层核心模块，实现病例记忆、反馈处理和记忆引用机制

功能特性:
1. 病例记忆系统 (CaseMemory): 存储和检索历史诊断病例
2. 反馈处理机制 (FeedbackHandler): 处理用户反馈并调整诊断策略
3. 记忆引用机制: 再次诊断时引用历史病例，实现上下文注入
4. 病情变化对比: 对比前后两次诊断结果，判断病情发展趋势

模块结构:
- case_memory.py: 病例记忆系统，负责病例的存储、检索和持久化
- feedback_handler.py: 反馈处理机制，负责用户反馈解析和策略调整

使用示例:
    from src.memory import CaseMemory, FeedbackHandler
    
    # 初始化病例记忆系统
    case_memory = CaseMemory(storage_path="data/case_memories.json")
    
    # 存储病例
    case_id = case_memory.store_case(
        user_id="user_001",
        image_path="field_001.jpg",
        disease_type="条锈病",
        severity="中度",
        recommendation="使用三唑酮可湿性粉剂喷雾"
    )
    
    # 检索历史病例
    history = case_memory.retrieve_history(user_id="user_001", limit=5)
    
    # 初始化反馈处理器
    feedback_handler = FeedbackHandler()
    
    # 处理用户反馈
    feedback_handler.process_feedback(
        case_id=case_id,
        feedback_type="采纳建议",
        details="施药后病情有所好转"
    )
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .case_memory import CaseMemory
from .feedback_handler import FeedbackHandler

__all__ = [
    "CaseMemory",
    "FeedbackHandler"
]

__version__ = "1.0.0"
__author__ = "IWDDA Team"
