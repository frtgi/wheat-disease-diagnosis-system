"""
通用工具函数
提供常用的辅助功能
"""
import uuid
from datetime import datetime
from typing import Optional


def generate_unique_id() -> str:
    """
    生成唯一 ID
    
    返回:
        UUID 字符串
    """
    return str(uuid.uuid4())


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    格式化日期时间
    
    参数:
        dt: 日期时间对象
    
    返回:
        格式化后的字符串 (YYYY-MM-DD HH:MM:SS)
    """
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def paginate(items: list, page: int, page_size: int) -> dict:
    """
    分页工具函数
    
    参数:
        items: 数据列表
        page: 页码
        page_size: 每页数量
    
    返回:
        分页后的数据及元信息
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
