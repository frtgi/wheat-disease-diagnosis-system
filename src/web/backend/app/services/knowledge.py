"""
知识服务
处理疾病知识相关的业务逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from ..models.disease import Disease
from ..schemas.knowledge import DiseaseCreate, DiseaseUpdate


def create_disease(db: Session, disease_data: DiseaseCreate) -> Disease:
    """
    创建疾病知识记录
    
    参数:
        db: 数据库会话
        disease_data: 疾病数据
    
    返回:
        创建的疾病对象
    
    异常:
        HTTPException: 疾病名称已存在
    """
    # 检查疾病名称是否已存在
    if db.query(Disease).filter(Disease.name == disease_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="疾病名称已存在"
        )
    
    data = disease_data.model_dump()
    # 映射字段名：schema 的 treatments/prevention → 模型的 treatment_methods/prevention_methods
    if 'treatments' in data:
        data['treatment_methods'] = data.pop('treatments')
    if 'prevention' in data:
        data['prevention_methods'] = data.pop('prevention')
    
    disease = Disease(**data)
    
    db.add(disease)
    db.commit()
    db.refresh(disease)
    
    return disease


def get_disease_by_id(db: Session, disease_id: int) -> Optional[Disease]:
    """
    根据 ID 获取疾病知识
    
    参数:
        db: 数据库会话
        disease_id: 疾病 ID
    
    返回:
        疾病对象，不存在返回 None
    """
    return db.query(Disease).filter(Disease.id == disease_id).first()


def get_disease_by_name(db: Session, name: str) -> Optional[Disease]:
    """
    根据名称获取疾病知识
    
    参数:
        db: 数据库会话
        name: 疾病名称
    
    返回:
        疾病对象，不存在返回 None
    """
    return db.query(Disease).filter(Disease.name == name).first()


def search_diseases(
    db: Session,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> List[Disease]:
    """
    搜索疾病知识
    
    参数:
        db: 数据库会话
        keyword: 搜索关键词
        category: 疾病分类
        skip: 跳过数量
        limit: 返回数量
    
    返回:
        疾病列表
    """
    query = db.query(Disease)
    
    # 构建搜索条件
    conditions = []
    
    if keyword:
        conditions.append(Disease.name.contains(keyword))
        conditions.append(Disease.symptoms.contains(keyword))
        conditions.append(Disease.causes.contains(keyword))
        conditions.append(Disease.code.contains(keyword))
        conditions.append(Disease.scientific_name.contains(keyword))
        conditions.append(Disease.description.contains(keyword))
    
    if category:
        conditions.append(Disease.category == category)
    
    if conditions:
        query = query.filter(or_(*conditions))
    
    return query.order_by(Disease.name).offset(skip).limit(limit).all()


def update_disease(db: Session, disease_id: int, update_data: DiseaseUpdate) -> Disease:
    """
    更新疾病知识
    
    参数:
        db: 数据库会话
        disease_id: 疾病 ID
        update_data: 更新数据
    
    返回:
        更新后的疾病对象
    
    异常:
        HTTPException: 疾病不存在
    """
    disease = get_disease_by_id(db, disease_id)
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="疾病不存在"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    # 映射字段名：schema 的 treatments/prevention → 模型的 treatment_methods/prevention_methods
    if 'treatments' in update_dict:
        update_dict['treatment_methods'] = update_dict.pop('treatments')
    if 'prevention' in update_dict:
        update_dict['prevention_methods'] = update_dict.pop('prevention')
    
    for field, value in update_dict.items():
        setattr(disease, field, value)
    
    db.commit()
    db.refresh(disease)
    
    return disease


def delete_disease(db: Session, disease_id: int) -> bool:
    """
    删除疾病知识
    
    参数:
        db: 数据库会话
        disease_id: 疾病 ID
    
    返回:
        是否删除成功
    
    异常:
        HTTPException: 疾病不存在
    """
    disease = get_disease_by_id(db, disease_id)
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="疾病不存在"
        )
    
    db.delete(disease)
    db.commit()
    
    return True


def get_all_categories(db: Session) -> List[str]:
    """
    获取所有疾病分类
    
    参数:
        db: 数据库会话
    
    返回:
        分类列表
    """
    categories = db.query(Disease.category).filter(
        Disease.category.isnot(None)
    ).distinct().all()
    
    return [cat[0] for cat in categories if cat[0]]
