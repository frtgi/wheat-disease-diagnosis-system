"""
诊断 API 路由
处理诊断记录的查询、更新、删除等 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import logging
import json
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_pagination_params
from app.core.security import get_current_user
from app.schemas.common import PaginationParams
from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import (
    DiagnosisResponse,
    DiagnosisUpdate,
    DiagnosisListResponse,
)
from app.utils.xss_protection import sanitize_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnosis")

RECORD_TAG = "诊断记录"


@router.get(
    "/records",
    response_model=DiagnosisListResponse,
    summary="查询诊断记录",
    description="""
## 查询诊断历史记录

获取当前用户的诊断历史记录列表，支持分页查询。

### 认证要求
- 需要在请求头中携带有效的 Bearer Token

### 查询参数
- **page**: 页码（从 1 开始，默认 1）
- **page_size**: 每页数量（1-100，默认 20）

### 返回信息
- 记录列表（包含诊断结果、置信度、状态等）
- 总记录数（用于前端分页）
- 当前分页参数（page, page_size, total_pages）

### 性能优化
- 使用索引优化查询（user_id, created_at 复合索引）
- 使用 Eager Loading 避免 N+1 查询
- 查询结果缓存 5 分钟
""",
    tags=[RECORD_TAG],
    responses={
        200: {
            "description": "查询成功",
            "content": {
                "application/json": {
                    "example": {
                        "records": [
                            {
                                "id": 1,
                                "user_id": 1,
                                "disease_id": 1,
                                "symptoms": "叶片出现黄色条状锈斑",
                                "diagnosis_result": "小麦条锈病",
                                "confidence": 0.92,
                                "suggestions": "及时喷施三唑酮等杀菌剂",
                                "status": "completed",
                                "created_at": "2026-03-27T10:30:00",
                                "updated_at": "2026-03-27T10:30:00"
                            }
                        ],
                        "total": 15,
                        "page": 1,
                        "page_size": 20,
                        "total_pages": 1
                    }
                }
            }
        }
    }
)
@sanitize_response(fields_to_sanitize=["symptoms", "diagnosis_result", "suggestions"])
async def get_diagnosis_records(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ...services.optimized_queries import get_optimized_query_service

    query_service = get_optimized_query_service(db)
    result = query_service.get_user_diagnoses_paginated(
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )

    total_pages = (result["total"] + pagination.limit - 1) // pagination.limit if result["total"] > 0 else 0

    record_responses = [
        DiagnosisResponse(
            id=record.id,
            user_id=record.user_id,
            disease_id=record.disease_id,
            symptoms=record.symptoms,
            diagnosis_result=record.disease.name if record.disease else None,
            confidence=float(record.primary_confidence) if record.primary_confidence else None,
            suggestions=record.recommendations if isinstance(record.recommendations, list) else (json.loads(record.recommendations) if isinstance(record.recommendations, str) and record.recommendations else None),
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at
        )
        for record in result["records"]
    ]

    return DiagnosisListResponse(
        records=record_responses,
        total=result["total"],
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
    summary="诊断详情",
    description="""
## 获取诊断详情

根据诊断记录 ID 获取单条诊断记录的详细信息。

### 路径参数
- **diagnosis_id**: 诊断记录 ID（整数）

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- 只能查询自己的诊断记录

### 返回信息
- 诊断记录 ID
- 用户 ID
- 关联病害 ID
- 症状描述
- 诊断结果
- 置信度
- 防治建议
- 诊断状态
- 创建和更新时间
""",
    tags=[RECORD_TAG],
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "disease_id": 1,
                        "symptoms": "叶片出现黄色条状锈斑",
                        "diagnosis_result": "小麦条锈病",
                        "confidence": 0.92,
                        "suggestions": "及时喷施三唑酮等杀菌剂",
                        "status": "completed",
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T10:30:00"
                    }
                }
            }
        },
        404: {
            "description": "记录不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "诊断记录不存在"}
                }
            }
        }
    }
)
@sanitize_response(fields_to_sanitize=["symptoms", "diagnosis_result", "suggestions"])
async def get_diagnosis_detail(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(Diagnosis).options(
        joinedload(Diagnosis.disease)
    ).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="诊断记录不存在")
    
    return DiagnosisResponse(
        id=record.id,
        user_id=record.user_id,
        disease_id=record.disease_id,
        symptoms=record.symptoms,
        diagnosis_result=record.disease.name if record.disease else None,
        confidence=float(record.primary_confidence) if record.primary_confidence else None,
        suggestions=record.recommendations if isinstance(record.recommendations, list) else (json.loads(record.recommendations) if isinstance(record.recommendations, str) and record.recommendations else None),
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


@router.put(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
    summary="更新诊断记录",
    description="""
## 更新诊断记录

更新指定诊断记录的信息（如添加备注、修改状态等）。

### 路径参数
- **diagnosis_id**: 诊断记录 ID（整数）

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- 只能更新自己的诊断记录

### 可更新字段
- **diagnosis_result**: 诊断结果
- **confidence**: 置信度（0-1）
- **suggestions**: 防治建议
- **status**: 诊断状态（pending/completed/failed）
""",
    tags=[RECORD_TAG],
    responses={
        200: {
            "description": "更新成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "disease_id": 1,
                        "symptoms": "叶片出现黄色条状锈斑",
                        "diagnosis_result": "小麦条锈病",
                        "confidence": 0.95,
                        "suggestions": "更新后的防治建议",
                        "status": "completed",
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T12:00:00"
                    }
                }
            }
        },
        404: {
            "description": "记录不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "诊断记录不存在"}
                }
            }
        }
    }
)
async def update_diagnosis_record(
    diagnosis_id: int,
    update_data: DiagnosisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(Diagnosis).options(
        joinedload(Diagnosis.disease)
    ).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="诊断记录不存在")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(record, field):
            setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    
    return DiagnosisResponse(
        id=record.id,
        user_id=record.user_id,
        disease_id=record.disease_id,
        symptoms=record.symptoms,
        diagnosis_result=record.disease.name if record.disease else None,
        confidence=float(record.primary_confidence) if record.primary_confidence else None,
        suggestions=record.recommendations,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


@router.delete(
    "/{diagnosis_id}",
    summary="删除诊断记录",
    description="""
## 删除诊断记录

删除指定的诊断记录及其关联的图像文件。

### 路径参数
- **diagnosis_id**: 诊断记录 ID（整数）

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- 只能删除自己的诊断记录

### 删除内容
- 诊断记录数据
- 关联的上传图像文件

### 注意事项
- 删除操作不可恢复
- 建议在删除前导出重要记录
""",
    tags=[RECORD_TAG],
    responses={
        200: {
            "description": "删除成功",
            "content": {
                "application/json": {
                    "example": {"message": "诊断记录已删除"}
                }
            }
        },
        404: {
            "description": "记录不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "诊断记录不存在"}
                }
            }
        }
    }
)
async def delete_diagnosis_record(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(Diagnosis).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="诊断记录不存在")
    
    # 删除关联的图像文件
    if record.image_url:
        try:
            image_path = Path(__file__).parent.parent.parent / "uploads" / "diagnosis" / record.image_url.split("/")[-1]
            if image_path.exists():
                image_path.unlink()
        except Exception as e:
            logger.warning(f"删除图像文件失败：{e}")
    
    db.delete(record)
    db.commit()
    
    return {"message": "诊断记录已删除"}
