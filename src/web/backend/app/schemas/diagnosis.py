"""
诊断 Pydantic 模式
定义诊断数据的请求和响应格式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DiagnosisBase(BaseModel):
    """诊断基础模式"""
    symptoms: str = Field(default="", max_length=2000, description="症状描述")


class DiagnosisCreate(DiagnosisBase):
    """诊断创建请求模式"""
    disease_id: Optional[int] = Field(None, description="疾病 ID")


class DiagnosisUpdate(BaseModel):
    """诊断更新请求模式"""
    diagnosis_result: Optional[str] = Field(None, description="诊断结果")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="置信度")
    suggestions: Optional[List[str]] = Field(None, description="建议")
    status: Optional[str] = Field(None, description="状态")


class DiagnosisResponse(DiagnosisBase):
    """诊断响应模式"""
    id: int
    user_id: int
    disease_id: Optional[int] = None
    diagnosis_result: Optional[str] = None
    confidence: Optional[float] = None
    suggestions: Optional[List[str]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DiagnosisWithDisease(DiagnosisResponse):
    """带疾病信息的诊断响应"""
    disease_name: Optional[str] = None
    disease_category: Optional[str] = None


class DiseaseConfidence(BaseModel):
    """病害置信度模型（统一格式，支持多候选病害）"""
    disease_name: str = Field(..., description="病害名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度 0-1")
    disease_class: Optional[int] = Field(None, description="类别ID")


class DiagnosisResult(BaseModel):
    """诊断结果模式（用于 AI 诊断返回）"""
    disease_name: str = Field(..., description="病害名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    severity: Optional[str] = Field(None, description="严重程度")
    description: Optional[str] = Field(None, description="诊断描述")
    recommendations: Optional[str] = Field(None, description="防治建议")
    knowledge_links: List[str] = Field(default_factory=list, description="相关知识链接")


class DiagnosisCreateResponse(BaseModel):
    """诊断创建响应模式"""
    diagnosis_id: str
    disease_name: str
    confidence: float
    confidences: List[DiseaseConfidence] = Field(default_factory=list, description="所有候选病害置信度列表（统一格式）")
    severity: Optional[str] = None
    description: Optional[str] = None
    recommendations: Optional[str] = None
    knowledge_links: List[str] = Field(default_factory=list, description="相关知识链接")
    created_at: datetime


class DiagnosisListResponse(BaseModel):
    """诊断记录列表响应模式（带分页信息）"""
    records: List[DiagnosisResponse]
    total: int
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
