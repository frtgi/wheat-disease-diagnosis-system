"""
知识 API 路由
处理疾病知识的增删改查等功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.database import get_db
from ...core.dependencies import get_pagination_params
from ...core.security import get_current_user, require_admin
from ...models.user import User
from ...models.disease import Disease
from ...models.knowledge import KnowledgeGraph
from ...schemas.common import PaginationParams
from ...schemas.knowledge import DiseaseCreate, DiseaseResponse, DiseaseUpdate, DiseaseSearch
from ...services.knowledge import (
    create_disease,
    get_disease_by_id,
    search_diseases,
    update_disease,
    delete_disease,
    get_all_categories
)

router = APIRouter(prefix="/knowledge")

KNOWLEDGE_TAG = "病害知识库"
CATEGORY_TAG = "病害分类"


@router.post(
    "/",
    response_model=DiseaseResponse,
    summary="创建病害知识",
    description="""
## 创建病害知识记录

向知识库中添加新的病害信息，用于诊断参考。

### 请求字段
- **name**: 病害名称（必填，1-100 字符）
- **code**: 病害编码（可选，用于标准化分类）
- **category**: 病害分类（可选，如：真菌病害、细菌病害、病毒病害等）
- **symptoms**: 症状描述（详细描述病害症状特征）
- **causes**: 病因（病害发生的原因和条件）
- **treatments**: 治疗方法（推荐的防治措施）
- **prevention**: 预防措施（预防病害发生的方法）
- **severity**: 严重程度（0-1，0 表示轻微，1 表示严重）

### 权限要求
- 需要管理员或专家角色
""",
    tags=[KNOWLEDGE_TAG],
    responses={
        200: {
            "description": "创建成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "小麦条锈病",
                        "code": "WHEAT_STRIPE_RUST",
                        "category": "真菌病害",
                        "symptoms": "叶片上出现条状黄色锈斑，主要分布在叶片正面，严重时病斑连成片",
                        "causes": "由条形柄锈菌引起，适宜温度 10-15°C，高湿环境易发病",
                        "treatments": "1. 发病初期喷施三唑酮可湿性粉剂\n2. 严重时使用丙环唑乳油\n3. 每 7-10 天喷施一次，连续 2-3 次",
                        "prevention": "1. 选用抗病品种\n2. 合理密植，改善通风\n3. 清除田间病残体\n4. 适时晚播",
                        "severity": 0.7,
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T10:30:00"
                    }
                }
            }
        }
    }
)
def create_knowledge(
    disease_data: DiseaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    disease = create_disease(db=db, disease_data=disease_data)
    return disease


@router.get(
    "/search",
    response_model=List[DiseaseResponse],
    summary="搜索病害知识",
    description="""
## 搜索病害知识

根据关键词或分类搜索病害知识库。

### 查询参数
- **keyword**: 搜索关键词，匹配病害名称、症状、病因等字段
- **category**: 病害分类筛选（如：真菌病害、细菌病害、病毒病害）
- **page**: 页码（从 1 开始，默认 1）
- **page_size**: 每页数量（1-100，默认 20）

### 搜索范围
- 病害名称
- 症状描述
- 病因说明
- 治疗方法

### 使用示例
- 搜索关键词 "锈病" 可匹配：小麦条锈病、小麦叶锈病等
- 按分类筛选 "真菌病害" 可获取所有真菌性病害

### 性能优化
- 使用索引优化查询（name, category 索引）
- 查询结果缓存 6 小时
- 使用优化查询服务减少数据库负载
""",
    tags=[KNOWLEDGE_TAG],
    responses={
        200: {
            "description": "搜索成功",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "小麦条锈病",
                            "code": "WHEAT_STRIPE_RUST",
                            "category": "真菌病害",
                            "symptoms": "叶片上出现条状黄色锈斑",
                            "causes": "由条形柄锈菌引起",
                            "treatments": "喷施三唑酮可湿性粉剂",
                            "prevention": "选用抗病品种",
                            "severity": 0.7,
                            "created_at": "2026-03-27T10:30:00",
                            "updated_at": "2026-03-27T10:30:00"
                        },
                        {
                            "id": 2,
                            "name": "小麦叶锈病",
                            "code": "WHEAT_LEAF_RUST",
                            "category": "真菌病害",
                            "symptoms": "叶片上出现圆形或椭圆形橙褐色锈斑",
                            "causes": "由小麦叶锈菌引起",
                            "treatments": "喷施三唑酮或戊唑醇",
                            "prevention": "清除田间病残体",
                            "severity": 0.6,
                            "created_at": "2026-03-27T10:30:00",
                            "updated_at": "2026-03-27T10:30:00"
                        }
                    ]
                }
            }
        }
    }
)
async def search_knowledge(
    keyword: str = Query(None, description="搜索关键词"),
    category: str = Query(None, description="病害分类"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    from ...services.optimized_queries import get_optimized_query_service
    from ...services.cache import cache_service
    import json

    cache_key = f"knowledge_search:{keyword or 'none'}:{category or 'none'}:{pagination.page}:{pagination.page_size}"

    try:
        cached_result = await cache_service._get_redis().get(cache_key)
        if cached_result:
            return json.loads(cached_result)
    except Exception:
        pass

    query_service = get_optimized_query_service(db)
    diseases = query_service.search_diseases_optimized(
        keyword=keyword,
        category=category,
        skip=pagination.skip,
        limit=pagination.limit
    )

    try:
        await cache_service._get_redis().setex(
            cache_key,
            21600,
            json.dumps([d.__dict__ for d in diseases], ensure_ascii=False, default=str)
        )
    except Exception:
        pass

    return diseases


@router.get(
    "/categories",
    response_model=List[str],
    summary="获取病害分类列表",
    description="""
## 获取病害分类列表

获取知识库中所有病害的分类标签，用于筛选和导航。

### 返回内容
返回所有已存在的病害分类名称列表。

### 常见分类
- 真菌病害
- 细菌病害
- 病毒病害
- 线虫病害
- 生理性病害
- 虫害
""",
    tags=[CATEGORY_TAG],
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": ["真菌病害", "细菌病害", "病毒病害", "线虫病害", "生理性病害", "虫害"]
                }
            }
        }
    }
)
def get_categories(db: Session = Depends(get_db)):
    categories = get_all_categories(db=db)
    return categories


@router.get("/graph", summary="获取知识图谱")
def get_knowledge_graph(
    disease_id: Optional[int] = Query(None, description="病害ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取知识图谱数据
    
    如果指定 disease_id，返回该病害的关联图谱（症状、病因、治疗等节点）；
    如果未指定，返回所有病害的概览图谱。
    
    节点类型：disease, symptom, cause, treatment, prevention
    关系类型：has_symptom, caused_by, treated_by, prevented_by
    """
    nodes = []
    edges = []
    
    if disease_id:
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="疾病不存在"
            )
        nodes.append({
            "id": f"disease_{disease.id}",
            "label": disease.name,
            "type": "disease",
            "properties": {"category": disease.category, "severity": disease.severity}
        })
        if disease.symptoms:
            for idx, symptom in enumerate(disease.symptoms.split("\n") if "\n" in disease.symptoms else [disease.symptoms]):
                symptom = symptom.strip()
                if symptom:
                    nodes.append({
                        "id": f"symptom_{disease.id}_{idx}",
                        "label": symptom,
                        "type": "symptom"
                    })
                    edges.append({
                        "source": f"disease_{disease.id}",
                        "target": f"symptom_{disease.id}_{idx}",
                        "relation": "has_symptom"
                    })
        if disease.causes:
            for idx, cause in enumerate(disease.causes.split("\n") if "\n" in disease.causes else [disease.causes]):
                cause = cause.strip()
                if cause:
                    nodes.append({
                        "id": f"cause_{disease.id}_{idx}",
                        "label": cause,
                        "type": "cause"
                    })
                    edges.append({
                        "source": f"disease_{disease.id}",
                        "target": f"cause_{disease.id}_{idx}",
                        "relation": "caused_by"
                    })
        if disease.treatment_methods:
            treatments = disease.treatment_methods if isinstance(disease.treatment_methods, list) else [disease.treatment_methods]
            for idx, treatment in enumerate(treatments):
                label = treatment if isinstance(treatment, str) else str(treatment)
                if label:
                    nodes.append({
                        "id": f"treatment_{disease.id}_{idx}",
                        "label": label,
                        "type": "treatment"
                    })
                    edges.append({
                        "source": f"disease_{disease.id}",
                        "target": f"treatment_{disease.id}_{idx}",
                        "relation": "treated_by"
                    })
        if disease.prevention_methods:
            preventions = disease.prevention_methods if isinstance(disease.prevention_methods, list) else [disease.prevention_methods]
            for idx, prevention in enumerate(preventions):
                label = prevention if isinstance(prevention, str) else str(prevention)
                if label:
                    nodes.append({
                        "id": f"prevention_{disease.id}_{idx}",
                        "label": label,
                        "type": "prevention"
                    })
                    edges.append({
                        "source": f"disease_{disease.id}",
                        "target": f"prevention_{disease.id}_{idx}",
                        "relation": "prevented_by"
                    })
    else:
        diseases = db.query(Disease).filter(Disease.is_active == True).all()
        for disease in diseases:
            nodes.append({
                "id": f"disease_{disease.id}",
                "label": disease.name,
                "type": "disease",
                "properties": {"category": disease.category, "severity": disease.severity}
            })
        kg_edges = db.query(KnowledgeGraph).filter(
            KnowledgeGraph.relation.isnot(None),
            KnowledgeGraph.target_entity.isnot(None)
        ).all()
        for kg in kg_edges:
            edges.append({
                "source": kg.entity,
                "target": kg.target_entity,
                "relation": kg.relation
            })
    
    return {"nodes": nodes, "edges": edges}


@router.get("/stats", summary="获取知识库统计")
def get_knowledge_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取知识库统计信息
    
    返回 total 总数和 by_category 按类别统计
    """
    total = db.query(func.count(Disease.id)).filter(Disease.is_active == True).scalar()
    category_stats = db.query(
        Disease.category,
        func.count(Disease.id)
    ).filter(Disease.is_active == True).group_by(Disease.category).all()
    
    return {
        "total": total,
        "by_category": {cat: count for cat, count in category_stats}
    }


@router.get(
    "/{disease_id}",
    response_model=DiseaseResponse,
    summary="获取病害详情",
    description="""
## 获取病害详情

根据病害 ID 获取病害的完整信息。

### 路径参数
- **disease_id**: 病害 ID（整数）

### 返回信息
- 病害基本信息（名称、编码、分类）
- 症状描述
- 病因说明
- 治疗方法
- 预防措施
- 严重程度
- 创建和更新时间
""",
    tags=[KNOWLEDGE_TAG],
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "小麦条锈病",
                        "code": "WHEAT_STRIPE_RUST",
                        "category": "真菌病害",
                        "symptoms": "叶片上出现条状黄色锈斑，主要分布在叶片正面，严重时病斑连成片",
                        "causes": "由条形柄锈菌引起，适宜温度 10-15°C，高湿环境易发病",
                        "treatments": "1. 发病初期喷施三唑酮可湿性粉剂\n2. 严重时使用丙环唑乳油\n3. 每 7-10 天喷施一次，连续 2-3 次",
                        "prevention": "1. 选用抗病品种\n2. 合理密植，改善通风\n3. 清除田间病残体\n4. 适时晚播",
                        "severity": 0.7,
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T10:30:00"
                    }
                }
            }
        },
        404: {
            "description": "病害不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "疾病不存在"}
                }
            }
        }
    }
)
def get_knowledge(disease_id: int, db: Session = Depends(get_db)):
    disease = get_disease_by_id(db, disease_id)
    
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="疾病不存在"
        )
    
    return disease


@router.put(
    "/{disease_id}",
    response_model=DiseaseResponse,
    summary="更新病害知识",
    description="""
## 更新病害知识

更新知识库中的病害信息。

### 路径参数
- **disease_id**: 病害 ID（整数）

### 可更新字段
- **name**: 病害名称
- **code**: 病害编码
- **category**: 病害分类
- **symptoms**: 症状描述
- **causes**: 病因
- **treatments**: 治疗方法
- **prevention**: 预防措施
- **severity**: 严重程度

### 权限要求
- 需要管理员或专家角色
""",
    tags=[KNOWLEDGE_TAG],
    responses={
        200: {
            "description": "更新成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "小麦条锈病",
                        "code": "WHEAT_STRIPE_RUST",
                        "category": "真菌病害",
                        "symptoms": "更新后的症状描述",
                        "causes": "更新后的病因",
                        "treatments": "更新后的治疗方法",
                        "prevention": "更新后的预防措施",
                        "severity": 0.8,
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T12:00:00"
                    }
                }
            }
        }
    }
)
def update_knowledge(
    disease_id: int,
    update_data: DiseaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    disease = update_disease(db=db, disease_id=disease_id, update_data=update_data)
    return disease


@router.delete(
    "/{disease_id}",
    summary="删除病害知识",
    description="""
## 删除病害知识

从知识库中删除指定的病害信息。

### 路径参数
- **disease_id**: 病害 ID（整数）

### 权限要求
- 需要管理员角色

### 注意事项
- 删除操作不可恢复
- 删除后关联的诊断记录将失去知识链接
- 建议在删除前确认无重要关联数据
""",
    tags=[KNOWLEDGE_TAG],
    responses={
        200: {
            "description": "删除成功",
            "content": {
                "application/json": {
                    "example": {"message": "疾病知识已删除"}
                }
            }
        }
    }
)
def delete_knowledge(disease_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    delete_disease(db=db, disease_id=disease_id)
    return {"message": "疾病知识已删除"}
