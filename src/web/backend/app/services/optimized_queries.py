"""
优化查询服务模块
提供使用 Eager Loading 和查询优化的数据访问层
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from ..models.user import User
from ..models.diagnosis import Diagnosis
from ..models.disease import Disease
from ..models.knowledge import KnowledgeGraph


class OptimizedQueryService:
    """
    优化查询服务类
    
    使用 Eager Loading 避免 N+1 查询问题
    提供高效的数据库查询方法
    """
    
    def __init__(self, db: Session):
        """
        初始化查询服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get_user_with_diagnoses(self, user_id: int) -> Optional[User]:
        """
        获取用户及其诊断记录（使用 Eager Loading）
        
        Args:
            user_id: 用户 ID
        
        Returns:
            用户对象（包含诊断记录）
        """
        return self.db.query(User).options(
            joinedload(User.diagnoses)
        ).filter(User.id == user_id).first()
    
    def get_diagnosis_with_details(self, diagnosis_id: int) -> Optional[Diagnosis]:
        """
        获取诊断记录及其关联信息（使用 Eager Loading）
        
        Args:
            diagnosis_id: 诊断记录 ID
        
        Returns:
            诊断记录对象（包含用户和疾病信息）
        """
        return self.db.query(Diagnosis).options(
            joinedload(Diagnosis.user),
            joinedload(Diagnosis.disease)
        ).filter(Diagnosis.id == diagnosis_id).first()
    
    def get_user_diagnoses_paginated(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户诊断记录（分页）
        
        Args:
            user_id: 用户 ID
            skip: 跳过记录数
            limit: 返回记录数
            status: 状态筛选
        
        Returns:
            包含记录列表和总数的字典
        """
        query = self.db.query(Diagnosis).filter(Diagnosis.user_id == user_id)
        
        if status:
            query = query.filter(Diagnosis.status == status)
        
        total = query.count()
        
        records = query.options(
            joinedload(Diagnosis.disease)
        ).order_by(
            Diagnosis.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return {
            "records": records,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    def search_diseases_optimized(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Disease]:
        """
        优化的疾病搜索
        
        Args:
            keyword: 搜索关键词
            category: 疾病分类
            skip: 跳过记录数
            limit: 返回记录数
        
        Returns:
            疾病列表
        """
        query = self.db.query(Disease)
        
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    Disease.name.contains(keyword),
                    Disease.symptoms.contains(keyword),
                    Disease.causes.contains(keyword),
                    Disease.code.contains(keyword),
                    Disease.scientific_name.contains(keyword),
                    Disease.description.contains(keyword)
                )
            )
        
        if category:
            conditions.append(Disease.category == category)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query.order_by(Disease.name).offset(skip).limit(limit).all()
    
    def get_disease_with_diagnoses_count(self, disease_id: int) -> Optional[Dict[str, Any]]:
        """
        获取疾病信息及其诊断次数
        
        Args:
            disease_id: 疾病 ID
        
        Returns:
            包含疾病信息和诊断次数的字典
        """
        disease = self.db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            return None
        
        diagnoses_count = self.db.query(func.count(Diagnosis.id)).filter(
            Diagnosis.disease_id == disease_id
        ).scalar()
        
        return {
            "disease": disease,
            "diagnoses_count": diagnoses_count
        }
    
    def get_recent_diagnoses(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Diagnosis]:
        """
        获取最近的诊断记录
        
        Args:
            hours: 时间范围（小时）
            limit: 返回记录数
        
        Returns:
            诊断记录列表
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db.query(Diagnosis).options(
            joinedload(Diagnosis.user),
            joinedload(Diagnosis.disease)
        ).filter(
            Diagnosis.created_at >= since
        ).order_by(
            Diagnosis.created_at.desc()
        ).limit(limit).all()
    
    def get_diagnosis_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取诊断统计信息
        
        Args:
            user_id: 用户 ID（可选，不提供则统计全部）
        
        Returns:
            统计信息字典
        """
        query = self.db.query(Diagnosis)
        
        if user_id:
            query = query.filter(Diagnosis.user_id == user_id)
        
        total = query.count()
        
        status_counts = self.db.query(
            Diagnosis.status,
            func.count(Diagnosis.id).label('count')
        )
        
        if user_id:
            status_counts = status_counts.filter(Diagnosis.user_id == user_id)
        
        status_counts = status_counts.group_by(Diagnosis.status).all()
        
        disease_counts = self.db.query(
            Disease.name.label('disease_name'),
            func.count(Diagnosis.id).label('count')
        ).join(
            Disease, Diagnosis.disease_id == Disease.id, isouter=True
        )
        
        if user_id:
            disease_counts = disease_counts.filter(Diagnosis.user_id == user_id)
        
        disease_counts = disease_counts.group_by(
            Disease.name
        ).order_by(
            func.count(Diagnosis.id).desc()
        ).limit(10).all()
        
        return {
            "total": total,
            "by_status": {status: count for status, count in status_counts},
            "top_diseases": [
                {"name": name, "count": count} 
                for name, count in disease_counts
            ]
        }
    
    def get_knowledge_by_entity(
        self,
        entity_type: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeGraph]:
        """
        查询知识图谱实体
        
        Args:
            entity_type: 实体类型
            entity: 实体名称
            limit: 返回数量限制
        
        Returns:
            知识图谱记录列表
        """
        query = self.db.query(KnowledgeGraph)
        
        if entity_type:
            query = query.filter(KnowledgeGraph.entity_type == entity_type)
        
        if entity:
            query = query.filter(KnowledgeGraph.entity.contains(entity))
        
        return query.limit(limit).all()
    
    def batch_get_users(self, user_ids: List[int]) -> List[User]:
        """
        批量获取用户信息
        
        Args:
            user_ids: 用户 ID 列表
        
        Returns:
            用户列表
        """
        return self.db.query(User).filter(User.id.in_(user_ids)).all()
    
    def batch_get_diseases(self, disease_ids: List[int]) -> List[Disease]:
        """
        批量获取疾病信息
        
        Args:
            disease_ids: 疾病 ID 列表
        
        Returns:
            疾病列表
        """
        return self.db.query(Disease).filter(Disease.id.in_(disease_ids)).all()


def get_optimized_query_service(db: Session) -> OptimizedQueryService:
    """
    获取优化查询服务实例
    
    Args:
        db: 数据库会话
    
    Returns:
        优化查询服务实例
    """
    return OptimizedQueryService(db)
