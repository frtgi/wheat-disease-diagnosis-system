"""
知识 API 路由
处理疾病知识的增删改查等功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

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

logger = logging.getLogger(__name__)

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
        serialized = [DiseaseResponse.model_validate(d).model_dump(mode='json') for d in diseases]
        await cache_service._get_redis().setex(
            cache_key,
            21600,
            json.dumps(serialized, ensure_ascii=False, default=str)
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

    需要用户认证。返回病害-症状-防治措施的关系图谱。
    数据来源优先级：
    1. knowledge_graph SQL 三元组表（结构化关系）
    2. Disease 平表（补充症状、治疗、病因、预防关系）

    参数:
        disease_id: 可选病害ID，用于筛选特定病害
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        包含节点和关系的知识图谱数据
    """
    try:
        nodes = []
        relations = []
        node_ids = set()
        rel_keys = set()

        kg_query = db.query(KnowledgeGraph)
        if disease_id:
            disease = db.query(Disease).filter(Disease.id == disease_id).first()
            if disease:
                kg_query = kg_query.filter(
                    (KnowledgeGraph.entity == disease.name) |
                    (KnowledgeGraph.target_entity == disease.name)
                )
        kg_triples = kg_query.all()

        for triple in kg_triples:
            src_id = f"{triple.entity_type}_{triple.entity}"
            if src_id not in node_ids:
                node_ids.add(src_id)
                nodes.append({
                    "id": src_id,
                    "name": triple.entity,
                    "type": triple.entity_type,
                    "attributes": triple.attributes
                })

            if triple.target_entity:
                target_type = _infer_target_type(triple.relation)
                tgt_id = f"{target_type}_{triple.target_entity}"
                if tgt_id not in node_ids:
                    node_ids.add(tgt_id)
                    nodes.append({
                        "id": tgt_id,
                        "name": triple.target_entity,
                        "type": target_type
                    })
                rel_key = f"{src_id}->{triple.relation.upper()}->{tgt_id}"
                if rel_key not in rel_keys:
                    rel_keys.add(rel_key)
                    relations.append({"from": src_id, "to": tgt_id, "type": triple.relation.upper()})

        diseases = db.query(Disease).filter(Disease.is_active == True)
        if disease_id:
            diseases = diseases.filter(Disease.id == disease_id)
        diseases = diseases.limit(20).all()

        for disease in diseases:
            d_id = f"disease_{disease.name}"
            if d_id not in node_ids:
                node_ids.add(d_id)
                nodes.append({
                    "id": d_id,
                    "name": disease.name,
                    "type": "disease",
                    "category": disease.category,
                    "severity": disease.severity
                })

            if disease.symptoms:
                symptom_list = _split_text(disease.symptoms)
                for symptom in symptom_list[:5]:
                    symptom = symptom.strip()
                    if symptom:
                        s_id = f"symptom_{symptom}"
                        if s_id not in node_ids:
                            node_ids.add(s_id)
                            nodes.append({"id": s_id, "name": symptom, "type": "symptom"})
                        rel_key = f"{d_id}->HAS_SYMPTOM->{s_id}"
                        if rel_key not in rel_keys:
                            rel_keys.add(rel_key)
                            relations.append({"from": d_id, "to": s_id, "type": "HAS_SYMPTOM"})

            if disease.causes:
                causes_list = _split_text(disease.causes)
                for cause in causes_list[:3]:
                    cause = cause.strip()
                    if cause:
                        c_id = f"cause_{cause}"
                        if c_id not in node_ids:
                            node_ids.add(c_id)
                            nodes.append({"id": c_id, "name": cause, "type": "cause"})
                        rel_key = f"{d_id}->CAUSED_BY->{c_id}"
                        if rel_key not in rel_keys:
                            rel_keys.add(rel_key)
                            relations.append({"from": d_id, "to": c_id, "type": "CAUSED_BY"})

            if disease.treatment_methods:
                treatments = _parse_json_list(disease.treatment_methods)
                for treatment in treatments[:5]:
                    treatment = str(treatment).strip()
                    if treatment:
                        t_id = f"treatment_{treatment}"
                        if t_id not in node_ids:
                            node_ids.add(t_id)
                            nodes.append({"id": t_id, "name": treatment, "type": "treatment"})
                        rel_key = f"{d_id}->TREATED_BY->{t_id}"
                        if rel_key not in rel_keys:
                            rel_keys.add(rel_key)
                            relations.append({"from": d_id, "to": t_id, "type": "TREATED_BY"})

            if disease.prevention_methods:
                preventions = _parse_json_list(disease.prevention_methods)
                for prevention in preventions[:5]:
                    prevention = str(prevention).strip()
                    if prevention:
                        p_id = f"prevention_{prevention}"
                        if p_id not in node_ids:
                            node_ids.add(p_id)
                            nodes.append({"id": p_id, "name": prevention, "type": "prevention"})
                        rel_key = f"{d_id}->PREVENTED_BY->{p_id}"
                        if rel_key not in rel_keys:
                            rel_keys.add(rel_key)
                            relations.append({"from": d_id, "to": p_id, "type": "PREVENTED_BY"})

        return {"nodes": nodes, "relations": relations}
    except Exception as e:
        logger.error(f"获取知识图谱失败：{e}")
        return {"nodes": [], "relations": []}


def _infer_target_type(relation: str) -> str:
    """
    根据关系类型推断目标实体类型

    Args:
        relation: 关系类型字符串

    Returns:
        str: 推断的目标实体类型
    """
    mapping = {
        "causes": "cause",
        "indicates": "disease",
        "treats": "disease",
        "susceptible_to": "disease",
        "HAS_SYMPTOM": "symptom",
        "CAUSED_BY": "cause",
        "TREATED_BY": "treatment",
        "PREVENTED_BY": "prevention",
    }
    return mapping.get(relation, "entity")


def _split_text(text: str) -> list:
    """
    智能分割文本，支持多种分隔符

    Args:
        text: 待分割的文本

    Returns:
        list: 分割后的字符串列表
    """
    if not text:
        return []
    for sep in ['\n', '；', ';', '、', '。']:
        if sep in text:
            return [s.strip() for s in text.split(sep) if s.strip()]
    return [text.strip()]


def _parse_json_list(data) -> list:
    """
    解析 JSON 列表字段，兼容列表和字符串格式

    Args:
        data: 可能是列表、JSON字符串或普通字符串的数据

    Returns:
        list: 解析后的列表
    """
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        import json
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return _split_text(data)
    return [str(data)]


@router.get("/stats", summary="获取知识库统计")
def get_knowledge_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取知识库统计信息

    需要用户认证。返回知识库中病害总数和按分类统计信息。

    参数:
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        包含总数和分类统计的字典
    """
    try:
        total = db.query(func.count(Disease.id)).filter(Disease.is_active == True).scalar()
        
        by_category = {}
        category_stats = db.query(
            Disease.category,
            func.count(Disease.id)
        ).filter(Disease.is_active == True).group_by(Disease.category).all()
        
        for cat, count in category_stats:
            by_category[cat or "unknown"] = count
        
        return {"total": total, "by_category": by_category}
    except Exception as e:
        logger.error(f"获取知识库统计失败：{e}")
        return {"total": 0, "by_category": {}}


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
