"""
FastAPI 依赖项
提供分页参数等通用依赖注入功能
"""
from fastapi import Query

from app.schemas.common import PaginationParams


def get_pagination_params(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大 100")
) -> PaginationParams:
    """获取统一分页参数的依赖函数

    从查询参数中提取分页信息，返回 PaginationParams 对象。
    所有列表查询 API 均应使用此依赖函数以保持分页参数一致。

    参数:
        page: 页码，从 1 开始，默认为 1
        page_size: 每页数量，范围 1-100，默认为 20

    返回:
        PaginationParams: 包含 skip/limit 计算属性的分页参数对象
    """
    return PaginationParams(page=page, page_size=page_size)
