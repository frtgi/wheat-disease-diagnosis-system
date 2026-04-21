"""
公共 Pydantic 模式
定义分页等通用请求和响应格式
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """统一分页参数模式"""

    page: int = Field(1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大 100")

    model_config = {"extra": "allow"}

    def __init__(self, page: int = 1, page_size: int = 20, **data):
        super().__init__(page=page, page_size=page_size, **data)

    @property
    def skip(self) -> int:
        """计算跳过的记录数"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """获取每页限制数"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """统一分页响应模式"""

    items: List[T] = Field(..., description="当前页数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(0, description="总页数")

    model_config = {"extra": "allow"}

    def __init__(self, items: List[T], total: int, page: int, page_size: int, **data):
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        super().__init__(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, **data)
