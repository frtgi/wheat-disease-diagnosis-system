"""
知识 Pydantic 模式
定义疾病知识数据的请求和响应格式
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DiseaseBase(BaseModel):
    """疾病基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="疾病名称")
    code: Optional[str] = Field(None, max_length=50, description="疾病编码")
    category: Optional[str] = Field(None, max_length=50, description="疾病分类")


class DiseaseCreate(DiseaseBase):
    """疾病创建请求模式"""
    symptoms: Optional[str] = Field(None, description="症状描述")
    causes: Optional[str] = Field(None, description="病因")
    treatments: Optional[str] = Field(None, description="治疗方法")
    prevention: Optional[str] = Field(None, description="预防措施")
    severity: Optional[float] = Field(0.0, ge=0, le=1, description="严重程度")


class DiseaseUpdate(BaseModel):
    """疾病更新请求模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="疾病名称")
    code: Optional[str] = Field(None, max_length=50, description="疾病编码")
    category: Optional[str] = Field(None, max_length=50, description="疾病分类")
    symptoms: Optional[str] = Field(None, description="症状描述")
    causes: Optional[str] = Field(None, description="病因")
    treatments: Optional[str] = Field(None, description="治疗方法")
    prevention: Optional[str] = Field(None, description="预防措施")
    severity: Optional[float] = Field(None, ge=0, le=1, description="严重程度")


class DiseaseResponse(DiseaseBase):
    """疾病响应模式"""
    id: int
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    treatments: Optional[str] = None
    prevention: Optional[str] = None
    severity: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DiseaseSearch(BaseModel):
    """疾病搜索请求模式"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="疾病分类")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
