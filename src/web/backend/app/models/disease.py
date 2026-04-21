"""
疾病数据模型
定义疾病知识表结构和关系
符合 spec.md 中 diseases 表的设计规范
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum as SQLEnum, Index, JSON, Boolean
from sqlalchemy.orm import relationship

from ..core.database import Base


class Disease(Base):
    """
    疾病模型类

    对应数据库表：diseases
    存储小麦病害的详细信息，包括症状、病因、防治方法等
    """

    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="疾病 ID")
    name = Column(String(100), nullable=False, index=True, comment="疾病名称")
    scientific_name = Column(String(100), nullable=True, comment="学名")
    code = Column(String(50), unique=True, nullable=True, index=True, comment="疾病编码")
    category = Column(SQLEnum('fungal', 'bacterial', 'viral', 'pest', 'nutritional', name='disease_category'), nullable=False, index=True, comment="疾病分类：fungal(真菌性)/bacterial(细菌性)/viral(病毒性)/pest(虫害)/nutritional(营养性)")
    symptoms = Column(Text, nullable=False, comment="症状描述")
    description = Column(Text, nullable=True, comment="详细描述")
    causes = Column(Text, nullable=True, comment="病因")
    prevention_methods = Column(JSON, nullable=True, comment="预防方法 (JSON 格式)")
    treatment_methods = Column(JSON, nullable=True, comment="治疗方法 (JSON 格式)")
    suitable_growth_stage = Column(String(100), nullable=True, comment="适用生长阶段")
    image_urls = Column(JSON, nullable=True, comment="图片 URL 列表 (JSON 格式)")
    severity = Column(Float, default=0.0, index=True, comment="严重程度 (0-1)")
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index('idx_disease_category_name', 'category', 'name'),
        Index('idx_disease_severity', 'severity'),
        Index('idx_disease_category_active_severity', 'category', 'is_active', 'severity'),
    )

    @property
    def treatments(self):
        """获取治疗方法（兼容 schema 字段名）"""
        return self.treatment_methods

    @property
    def prevention(self):
        """获取预防措施（兼容 schema 字段名）"""
        return self.prevention_methods

    diagnoses = relationship("Diagnosis", back_populates="disease")
