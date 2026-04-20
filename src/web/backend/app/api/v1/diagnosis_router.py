"""
诊断路由注册模块
定义所有诊断相关的 API 端点，包括：
- 多模态融合诊断（POST /fusion）
- SSE 流式融合诊断（GET/POST /fusion/stream）
- 图像诊断（POST /image）
- 多模态诊断（POST /multimodal）
- 文本诊断（POST /text）
- AI 健康检查（GET /health/ai）
- 缓存管理（GET /cache/stats, POST /cache/clear）
- 批量诊断（POST /batch）
- 模型预加载（POST /admin/ai/preload）
- 诊断记录 CRUD（GET /records, GET /{id}, PUT /{id}, DELETE /{id}）

本模块作为路由注册层，负责：
- API 路由定义和参数校验
- Depends 注入
- 错误处理中间件
- 调用 sse_stream_manager 和 diagnosis_validator
"""
import logging
import time
import json
import asyncio
import os
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from PIL import Image
import io

from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.core.dependencies import get_pagination_params
from app.models.diagnosis import Diagnosis, DiagnosisConfidence
from app.models.user import User
from app.schemas.common import PaginationParams
from app.schemas.diagnosis import (
    DiagnosisResponse,
    DiagnosisUpdate,
    DiagnosisListResponse,
)
from app.utils.xss_protection import sanitize_response

from .sse_stream_manager import (
    ProgressEvent,
    LogEvent,
    StepIndicator,
    HeartbeatEvent,
    SSEStreamManager,
    format_sse_event
)
from .diagnosis_validator import (
    validate_image,
    ensure_ai_service_ready,
    get_cache_manager_safe,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnosis", tags=["AI 诊断"])


@router.post("/fusion")
async def diagnose_fusion(
    image: Optional[UploadFile] = File(None, description="病害图像文件（可选）"),
    symptoms: str = Form("", description="症状描述文本（可选）"),
    weather: str = Form("", description="天气条件（如：晴朗、阴雨、高温高湿）"),
    growth_stage: str = Form("", description="生长阶段（如：苗期、拔节期、抽穗期、灌浆期）"),
    affected_part: str = Form("", description="发病部位（如：叶片、茎秆、穗部、根部）"),
    enable_thinking: bool = Form(True, description="是否启用 Thinking 推理链模式"),
    use_graph_rag: bool = Form(True, description="是否使用 GraphRAG 知识增强"),
    use_cache: bool = Form(True, description="是否使用缓存优化"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    统一多模态融合诊断 API

    整合 KAD-Former 和 GraphRAG 实现：
    - YOLOv8 视觉特征提取
    - Qwen3-VL 语义特征提取
    - KAD-Former 知识引导注意力融合
    - GraphRAG 知识检索增强

    支持三种诊断模式：
    1. 图像+文本联合诊断：同时上传图像和输入症状描述
    2. 仅图像诊断：仅上传图像
    3. 仅文本诊断：仅输入症状描述

    参数:
        image: 上传的图像文件（可选）
        symptoms: 症状描述文本（可选）
        weather: 天气条件
        growth_stage: 生长阶段
        affected_part: 发病部位
        enable_thinking: 是否启用 Thinking 推理链模式
        use_graph_rag: 是否使用 GraphRAG 知识增强
        use_cache: 是否使用缓存优化

    返回:
        融合诊断结果，包括 disease_name、confidence、recommendations 等
    """
    start_time = time.time()

    try:
        ensure_ai_service_ready()

        pil_image = None
        image_bytes = None

        if image:
            image_bytes = await image.read()
            is_valid, error_msg = validate_image(image_bytes, image.filename or "unknown")
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            pil_image = Image.open(io.BytesIO(image_bytes))

        if not pil_image and not symptoms:
            raise HTTPException(
                status_code=400,
                detail="请至少提供图像或症状描述中的一种输入"
            )

        from app.services.fusion_service import get_fusion_service

        cache_manager = get_cache_manager_safe() if use_cache else None

        cache_hit = None
        if cache_manager and (image_bytes or symptoms):
            cache_result = cache_manager.get(image_bytes, symptoms)

            if cache_result:
                cache_hit = cache_result
                logger.info(f"融合诊断缓存命中：source={cache_result.get('source')}")

        if cache_hit:
            inference_time = time.time() - start_time
            try:
                from app.services.diagnosis_logger import log_diagnosis
                log_diagnosis(
                    request_id=f"ai_cache_{int(time.time()*1000)}",
                    image_hash=None,
                    symptoms=symptoms or "",
                    disease_detected=cache_hit["result"].get("disease_name", "未知"),
                    confidence=float(cache_hit["result"].get("confidence", 0)),
                    processing_time_ms=round(inference_time * 1000, 2),
                    success=True,
                    cache_hit=True
                )
            except Exception:
                pass

            try:
                from app.api.v1.metrics import record_inference
                record_inference(latency_ms=round(inference_time * 1000, 2), success=True)
            except Exception:
                pass

            return {
                "success": True,
                "diagnosis": cache_hit["result"],
                "cache_info": {
                    "hit": True,
                    "source": cache_hit.get("source"),
                    "similarity": cache_hit.get("similarity")
                },
                "performance": {
                    "inference_time_ms": round(inference_time * 1000, 2),
                    "cache_hit": True
                },
                "message": "从缓存获取融合诊断结果"
            }

        fusion_service = get_fusion_service()

        disease_context = None
        if symptoms:
            disease_context = symptoms
        elif affected_part:
            disease_context = f"发病部位：{affected_part}"

        result = await fusion_service.diagnose_async(
            image=pil_image,
            symptoms=symptoms,
            enable_thinking=enable_thinking,
            use_graph_rag=use_graph_rag,
            disease_context=disease_context
        )

        if not result.get("success"):
            elapsed = time.time() - start_time
            try:
                from app.services.diagnosis_logger import log_diagnosis
                log_diagnosis(
                    request_id=f"ai_{int(time.time()*1000)}",
                    image_hash=None,
                    symptoms=symptoms or "",
                    disease_detected="",
                    confidence=0.0,
                    processing_time_ms=round(elapsed * 1000, 2),
                    success=False,
                    error=result.get("error", "融合诊断失败")[:500]
                )
            except Exception:
                pass

            try:
                from app.api.v1.metrics import record_inference
                record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
            except Exception:
                pass

            return {
                "success": False,
                "error": result.get("error", "融合诊断失败"),
                "fallback_suggestion": "请检查输入或稍后重试"
            }

        if cache_manager and image_bytes and result.get("success"):
            cache_manager.set(
                image_data=image_bytes,
                symptoms=symptoms,
                diagnosis_result=result.get("diagnosis"),
                ttl=3600
            )

        inference_time = time.time() - start_time

        response = {
            "success": True,
            "diagnosis": result.get("diagnosis"),
            "features": result.get("features", {}),
            "performance": {
                "inference_time_ms": round(inference_time * 1000, 2),
                "cache_hit": False,
                "thinking_mode_enabled": enable_thinking,
                "graph_rag_enabled": use_graph_rag
            }
        }

        if enable_thinking and result.get("reasoning_chain"):
            response["reasoning_chain"] = result["reasoning_chain"]

        response["message"] = "多模态融合诊断成功"

        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id=f"ai_{int(time.time()*1000)}",
                image_hash=None,
                symptoms=symptoms or "",
                disease_detected=result.get("diagnosis", {}).get("disease_name", "未知"),
                confidence=float(result.get("diagnosis", {}).get("confidence", 0)),
                processing_time_ms=round(inference_time * 1000, 2),
                success=True
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(inference_time * 1000, 2), success=True)
        except Exception:
            pass

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"融合诊断失败：{e}", exc_info=True)
        inference_time = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=round(inference_time * 1000, 2),
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(inference_time * 1000, 2), success=False)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="融合诊断失败，请稍后重试"
        )


@router.get("/fusion/stream")
async def diagnose_fusion_stream_get(
    image_url: Optional[str] = None,
    symptoms: str = "",
    weather: str = "",
    growth_stage: str = "",
    affected_part: str = "",
    enable_thinking: bool = True,
    use_graph_rag: bool = True,
    user_id: Optional[int] = Query(None, description="用户 ID（可选，用于保存诊断记录）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    SSE 流式融合诊断 API (GET 方法)

    通过 Server-Sent Events 实时推送推理进度。

    参数:
        image_url: 已上传图像的 URL（可选）
        symptoms: 症状描述文本（可选）
        weather: 天气条件
        growth_stage: 生长阶段
        affected_part: 发病部位
        enable_thinking: 是否启用 Thinking 推理链模式
        use_graph_rag: 是否使用 GraphRAG 知识增强
        user_id: 用户 ID（可选，用于保存诊断记录）

    返回:
        StreamingResponse: SSE 流式响应
    """
    return StreamingResponse(
        _generate_diagnosis_stream_from_url(
            image_url=image_url,
            symptoms=symptoms,
            weather=weather,
            growth_stage=growth_stage,
            affected_part=affected_part,
            enable_thinking=enable_thinking,
            use_graph_rag=use_graph_rag,
            user_id=user_id,
            db=db
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def _generate_diagnosis_stream_from_url(
    image_url: Optional[str],
    symptoms: str,
    weather: str,
    growth_stage: str,
    affected_part: str,
    enable_thinking: bool,
    use_graph_rag: bool,
    user_id: Optional[int] = None,
    db: Session = None
) -> AsyncGenerator[str, None]:
    """
    从 URL 加载图像并生成诊断进度的 SSE 流

    参数:
        image_url: 已上传图像的 URL
        symptoms: 症状描述
        weather: 天气条件
        growth_stage: 生长阶段
        affected_part: 发病部位
        enable_thinking: 是否启用 Thinking 模式
        use_graph_rag: 是否使用 GraphRAG
        user_id: 用户 ID（可选）
        db: 数据库会话（可选）

    生成:
        str: SSE 格式的事件字符串
    """
    start_time = time.time()
    last_heartbeat = time.time()
    heartbeat_interval = 15

    yield StepIndicator.to_sse()

    yield ProgressEvent(
        event="start",
        stage="init",
        progress=0,
        message="开始多模态融合诊断..."
    ).to_sse()

    yield LogEvent(
        level="info",
        message="初始化诊断服务...",
        stage="init"
    ).to_sse()

    try:
        ensure_ai_service_ready()

        pil_image = None
        image_bytes = None

        if image_url:
            yield LogEvent(
                level="info",
                message=f"加载图像: {image_url}",
                stage="init"
            ).to_sse()

            try:
                from pathlib import Path as FilePath
                uploads_dir = FilePath(__file__).parent.parent.parent / "uploads"
                allowed_dir = os.path.abspath(str(uploads_dir))
                clean_image_url = image_url.replace("/uploads/", "")
                image_path_abs = os.path.abspath(os.path.join(allowed_dir, clean_image_url))

                if not image_path_abs.startswith(allowed_dir + os.sep) and image_path_abs != allowed_dir:
                    yield LogEvent(
                        level="error",
                        message="非法路径访问",
                        stage="init"
                    ).to_sse()
                    yield ProgressEvent(
                        event="error",
                        stage="init",
                        progress=0,
                        message="非法路径访问",
                        data={"error_type": "access_denied", "error_code": "DIAG_005"}
                    ).to_sse()
                    return

                image_path = FilePath(image_path_abs)

                if not image_path.exists():
                    yield LogEvent(
                        level="error",
                        message=f"图像文件不存在: {image_url}",
                        stage="init"
                    ).to_sse()
                    yield ProgressEvent(
                        event="error",
                        stage="init",
                        progress=0,
                        message=f"图像文件不存在: {image_url}",
                        data={"error_type": "file_not_found", "error_code": "DIAG_003"}
                    ).to_sse()
                    return

                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                is_valid, error_msg = validate_image(image_bytes, image_path.name)
                if not is_valid:
                    yield LogEvent(
                        level="warning",
                        message=f"图像验证失败: {error_msg}",
                        stage="init"
                    ).to_sse()
                    yield ProgressEvent(
                        event="error",
                        stage="init",
                        progress=0,
                        message=error_msg,
                        data={"error_type": "validation_error", "error_code": "DIAG_001"}
                    ).to_sse()
                    return

                pil_image = Image.open(io.BytesIO(image_bytes))
                yield LogEvent(
                    level="info",
                    message=f"图像加载成功，尺寸: {pil_image.size}",
                    stage="init"
                ).to_sse()
                yield ProgressEvent(
                    event="progress",
                    stage="init",
                    progress=5,
                    message="图像加载完成，准备开始分析..."
                ).to_sse()
            except Exception as e:
                yield LogEvent(
                    level="error",
                    message="图像读取失败，请检查文件格式",
                    stage="init"
                ).to_sse()
                yield ProgressEvent(
                    event="error",
                    stage="init",
                    progress=0,
                    message="图像读取失败，请检查文件格式",
                    data={"error_type": "image_read_error", "error_code": "DIAG_002"}
                ).to_sse()
                return

        if not pil_image and not symptoms:
            yield ProgressEvent(
                event="error",
                stage="init",
                progress=0,
                message="请至少提供图像或症状描述中的一种输入",
                data={"error_type": "validation_error", "error_code": "DIAG_004"}
            ).to_sse()
            return

        current_time = time.time()
        if current_time - last_heartbeat > heartbeat_interval:
            yield f"event: heartbeat\ndata: {json.dumps({'timestamp': current_time})}\n\n"
            last_heartbeat = current_time

        from app.services.fusion_service import get_fusion_service

        try:
            from app.services.qwen_service import get_qwen_service
            qwen_svc = get_qwen_service()
            if qwen_svc.is_lazy_load and not qwen_svc.is_loaded:
                logger.info("融合诊断：检测到懒加载模式，确保模型已加载...")
                await qwen_svc.ensure_loaded()
        except Exception as e:
            logger.warning(f"懒加载预处理失败，继续执行: {e}")

        fusion_service = get_fusion_service()

        if not fusion_service._initialized:
            yield ProgressEvent(
                event="progress",
                stage="init",
                progress=10,
                message="正在初始化融合服务..."
            ).to_sse()
            fusion_service.initialize()

        disease_context = None
        if symptoms:
            disease_context = symptoms
        elif affected_part:
            disease_context = f"发病部位：{affected_part}"

        yield ProgressEvent(
            event="progress",
            stage="visual",
            progress=15,
            message="正在提取视觉特征 (YOLOv8)..."
        ).to_sse()

        visual_result = None
        if pil_image is not None:
            visual_result = await asyncio.to_thread(fusion_service._extract_visual_features, pil_image)

        yield ProgressEvent(
            event="progress",
            stage="visual",
            progress=30,
            message=f"视觉特征提取完成，检测到 {visual_result.get('count', 0) if visual_result else 0} 个目标"
        ).to_sse()

        knowledge_context = None
        if symptoms or disease_context:
            yield ProgressEvent(
                event="progress",
                stage="knowledge",
                progress=40,
                message="正在检索知识 (GraphRAG)..."
            ).to_sse()
            knowledge_context = await asyncio.to_thread(
                fusion_service._retrieve_knowledge,
                symptoms or disease_context,
                disease_context
            )

            yield ProgressEvent(
                event="progress",
                stage="knowledge",
                progress=50,
                message="知识检索完成"
            ).to_sse()

        yield ProgressEvent(
            event="progress",
            stage="textual",
            progress=55,
            message="正在提取文本语义特征 (Qwen3-VL)..."
        ).to_sse()

        yield LogEvent(
            level="info",
            message="Qwen3-VL 推理中，Thinking 模式可能需要 2-5 分钟，请耐心等待...",
            stage="textual"
        ).to_sse()

        textual_result = await asyncio.to_thread(
            fusion_service._extract_textual_features,
            image=pil_image,
            symptoms=symptoms,
            knowledge_context=knowledge_context,
            enable_thinking=enable_thinking
        )

        yield ProgressEvent(
            event="progress",
            stage="textual",
            progress=75,
            message="文本语义特征提取完成"
        ).to_sse()

        yield LogEvent(
            level="info",
            message="文本语义特征提取完成，开始融合...",
            stage="textual"
        ).to_sse()

        yield ProgressEvent(
            event="progress",
            stage="fusion",
            progress=80,
            message="正在融合多模态特征..."
        ).to_sse()

        fusion_result = fusion_service._fuse_features(
            visual_result=visual_result,
            textual_result=textual_result,
            knowledge_context=knowledge_context,
            original_image=pil_image
        )

        yield ProgressEvent(
            event="progress",
            stage="fusion",
            progress=90,
            message="特征融合完成"
        ).to_sse()

        inference_time = time.time() - start_time

        result = {
            "success": True,
            "diagnosis": {
                "disease_name": fusion_result.disease_name,
                "disease_name_en": fusion_result.disease_name_en,
                "confidence": fusion_result.confidence,
                "visual_confidence": fusion_result.visual_confidence,
                "textual_confidence": fusion_result.textual_confidence,
                "knowledge_confidence": fusion_result.knowledge_confidence,
                "description": fusion_result.description,
                "symptoms": fusion_result.symptoms,
                "causes": fusion_result.causes,
                "recommendations": fusion_result.recommendations,
                "treatment": fusion_result.treatment,
                "medicines": fusion_result.medicines,
                "severity": fusion_result.severity,
                "knowledge_references": fusion_result.knowledge_references,
                "roi_boxes": fusion_result.roi_boxes,
                "annotated_image": fusion_result.annotated_image,
                "inference_time_ms": fusion_result.inference_time_ms,
                "kad_former_used": fusion_result.kad_former_used
            },
            "features": {
                "thinking_mode": enable_thinking,
                "graph_rag": use_graph_rag
            },
            "performance": {
                "inference_time_ms": round(inference_time * 1000, 2),
                "cache_hit": False
            }
        }

        if enable_thinking and fusion_result.reasoning_chain:
            result["reasoning_chain"] = fusion_result.reasoning_chain

        diagnosis_id = None
        if user_id and db:
            try:
                image_id = None
                if image_url:
                    try:
                        from app.models.image import ImageMetadata
                        import hashlib
                        image_path = image_url
                        if image_url.startswith("/uploads/"):
                            image_path = os.path.join("uploads", image_url.replace("/uploads/", ""))
                        if image_url.startswith("/api/v1/upload/"):
                            image_path = image_url.replace("/api/v1/upload/", "uploads/")
                        
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as f:
                                file_data = f.read()
                                hash_value = hashlib.sha256(file_data).hexdigest()
                                file_size = len(file_data)
                            
                            existing_meta = db.query(ImageMetadata).filter(ImageMetadata.hash_value == hash_value).first()
                            if existing_meta:
                                image_id = existing_meta.id
                            else:
                                image_meta = ImageMetadata(
                                    user_id=user_id,
                                    hash_value=hash_value,
                                    original_filename=os.path.basename(image_path),
                                    file_path=os.path.abspath(image_path),
                                    file_size=file_size,
                                    mime_type="image/jpeg",
                                    storage_provider="local"
                                )
                                db.add(image_meta)
                                db.flush()
                                image_id = image_meta.id
                    except Exception as e:
                        logger.warning(f"创建图像元数据失败：{e}")

                disease_id = None
                if fusion_result.disease_name:
                    try:
                        from app.models.disease import Disease
                        disease_obj = db.query(Disease).filter(Disease.name == fusion_result.disease_name).first()
                        if disease_obj:
                            disease_id = disease_obj.id
                    except Exception:
                        pass

                diagnosis_record = Diagnosis(
                    user_id=user_id,
                    image_id=image_id,
                    image_url=image_url or "",
                    symptoms=symptoms or "",
                    disease_name=fusion_result.disease_name,
                    disease_id=disease_id,
                    confidence=fusion_result.confidence,
                    severity=None,
                    description=fusion_result.description,
                    recommendations=json.dumps(fusion_result.recommendations) if fusion_result.recommendations else "",
                    growth_stage=growth_stage or None,
                    weather_data=json.dumps({"weather": weather}) if weather else None,
                    status="completed"
                )
                db.add(diagnosis_record)
                db.commit()
                db.refresh(diagnosis_record)
                diagnosis_id = diagnosis_record.id
                logger.info(f"诊断记录已保存: id={diagnosis_id}, disease={fusion_result.disease_name}")
                try:
                    from app.services.diagnosis_logger import log_diagnosis
                    log_diagnosis(
                        request_id=f"diag_{diagnosis_id}",
                        image_hash=None,
                        symptoms=symptoms or "",
                        disease_detected=fusion_result.disease_name or "未知",
                        confidence=float(fusion_result.confidence) if fusion_result.confidence else 0.0,
                        processing_time_ms=round(inference_time * 1000, 2),
                        success=True,
                        cache_hit=False,
                        features={"thinking_mode": enable_thinking, "graph_rag": use_graph_rag}
                    )
                except Exception as log_err:
                    logger.warning(f"记录诊断日志失败：{log_err}")

                try:
                    from app.api.v1.metrics import record_inference
                    record_inference(latency_ms=round(inference_time * 1000, 2), success=True)
                except Exception as metrics_err:
                    logger.warning(f"记录推理指标失败：{metrics_err}")

                try:
                    confidence_record = DiagnosisConfidence(
                        diagnosis_id=diagnosis_id,
                        disease_name=fusion_result.disease_name,
                        confidence=fusion_result.confidence,
                        rank=0
                    )
                    db.add(confidence_record)
                    db.commit()
                except Exception as e:
                    logger.warning(f"保存置信度记录失败: {e}")

                result["diagnosis_id"] = diagnosis_id
            except Exception as e:
                logger.error(f"保存诊断记录失败: {e}", exc_info=True)
                db.rollback()

        yield ProgressEvent(
            event="complete",
            stage="complete",
            progress=100,
            message="融合诊断完成",
            data=result
        ).to_sse()

    except GeneratorExit:
        logger.info("SSE 客户端断开连接，清理资源")
        if db:
            try:
                db.rollback()
            except Exception:
                pass
        raise
    except Exception as e:
        logger.error(f"SSE 流式诊断失败: {e}", exc_info=True)
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=0.0,
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=0.0, success=False)
        except Exception:
            pass

        yield ProgressEvent(
            event="error",
            stage="error",
            progress=0,
            message="诊断过程中发生错误，请稍后重试",
            data={"error_type": "internal_error"}
        ).to_sse()


@router.post("/fusion/stream")
async def diagnose_fusion_stream(
    image: Optional[UploadFile] = File(None, description="病害图像文件（可选）"),
    symptoms: str = Form("", description="症状描述文本（可选）"),
    weather: str = Form("", description="天气条件（如：晴朗、阴雨、高温高湿）"),
    growth_stage: str = Form("", description="生长阶段（如：苗期、拔节期、抽穗期、灌浆期）"),
    affected_part: str = Form("", description="发病部位（如：叶片、茎秆、穗部、根部）"),
    enable_thinking: bool = Form(True, description="是否启用 Thinking 推理链模式"),
    use_graph_rag: bool = Form(True, description="是否使用 GraphRAG 知识增强"),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    SSE 流式融合诊断 API (POST 方法)

    通过 Server-Sent Events 实时推送推理进度。

    参数:
        image: 上传的图像文件（可选）
        symptoms: 症状描述文本（可选）
        weather: 天气条件
        growth_stage: 生长阶段
        affected_part: 发病部位
        enable_thinking: 是否启用 Thinking 推理链模式
        use_graph_rag: 是否使用 GraphRAG 知识增强

    返回:
        StreamingResponse: SSE 流式响应
    """
    return StreamingResponse(
        _generate_diagnosis_stream(
            image=image,
            symptoms=symptoms,
            weather=weather,
            growth_stage=growth_stage,
            affected_part=affected_part,
            enable_thinking=enable_thinking,
            use_graph_rag=use_graph_rag
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def _generate_diagnosis_stream(
    image: Optional[UploadFile],
    symptoms: str,
    weather: str,
    growth_stage: str,
    affected_part: str,
    enable_thinking: bool,
    use_graph_rag: bool
) -> AsyncGenerator[str, None]:
    """
    生成诊断进度的 SSE 流（从上传文件）

    参数:
        image: 上传的图像文件
        symptoms: 症状描述
        weather: 天气条件
        growth_stage: 生长阶段
        affected_part: 发病部位
        enable_thinking: 是否启用 Thinking 模式
        use_graph_rag: 是否使用 GraphRAG

    生成:
        str: SSE 格式的事件字符串
    """
    start_time = time.time()
    queue: asyncio.Queue = asyncio.Queue()

    yield ProgressEvent(
        event="start",
        stage="init",
        progress=0,
        message="开始多模态融合诊断..."
    ).to_sse()

    try:
        ensure_ai_service_ready()

        pil_image = None
        image_bytes = None

        if image:
            try:
                image_bytes = await image.read()
                is_valid, error_msg = validate_image(image_bytes, image.filename or "unknown")
                if not is_valid:
                    yield ProgressEvent(
                        event="error",
                        stage="init",
                        progress=0,
                        message=error_msg,
                        data={"error_type": "validation_error"}
                    ).to_sse()
                    return
                pil_image = Image.open(io.BytesIO(image_bytes))
                yield ProgressEvent(
                    event="progress",
                    stage="init",
                    progress=5,
                    message="图像加载完成，准备开始分析..."
                ).to_sse()
            except Exception as e:
                yield ProgressEvent(
                    event="error",
                    stage="init",
                    progress=0,
                    message="图像读取失败，请检查文件格式",
                    data={"error_type": "image_read_error"}
                ).to_sse()
                return

        if not pil_image and not symptoms:
            yield ProgressEvent(
                event="error",
                stage="init",
                progress=0,
                message="请至少提供图像或症状描述中的一种输入",
                data={"error_type": "validation_error"}
            ).to_sse()
            return

        from app.services.fusion_service import get_fusion_service

        fusion_service = get_fusion_service()

        if not fusion_service._initialized:
            yield ProgressEvent(
                event="progress",
                stage="init",
                progress=5,
                message="正在初始化融合服务..."
            ).to_sse()
            fusion_service.initialize()

        yield ProgressEvent(
            event="progress",
            stage="init",
            progress=10,
            message="融合服务初始化完成"
        ).to_sse()

        disease_context = None
        if symptoms:
            disease_context = symptoms
        elif affected_part:
            disease_context = f"发病部位：{affected_part}"

        yield ProgressEvent(
            event="progress",
            stage="visual",
            progress=15,
            message="正在提取视觉特征 (YOLOv8)..."
        ).to_sse()

        visual_result = None
        if pil_image is not None:
            try:
                visual_result = await asyncio.to_thread(fusion_service._extract_visual_features, pil_image)
                detection_count = visual_result.get("count", 0) if visual_result else 0
                yield ProgressEvent(
                    event="progress",
                    stage="visual",
                    progress=30,
                    message=f"视觉特征提取完成，检测到 {detection_count} 个目标",
                    data={"detection_count": detection_count}
                ).to_sse()
            except Exception as e:
                logger.warning(f"视觉特征提取失败: {e}")
                yield ProgressEvent(
                    event="progress",
                    stage="visual",
                    progress=30,
                    message="视觉特征提取跳过"
                ).to_sse()
        else:
            yield ProgressEvent(
                event="progress",
                stage="visual",
                progress=30,
                message="跳过视觉特征提取（无图像输入）"
            ).to_sse()

        knowledge_context = None
        if symptoms or disease_context:
            yield ProgressEvent(
                event="progress",
                stage="knowledge",
                progress=40,
                message="正在检索知识库 (GraphRAG)..."
            ).to_sse()

            try:
                knowledge_context = await asyncio.to_thread(
                    fusion_service._retrieve_knowledge,
                    symptoms or disease_context,
                    disease_context
                )
                triple_count = len(knowledge_context.triples) if knowledge_context and hasattr(knowledge_context, 'triples') else 0
                yield ProgressEvent(
                    event="progress",
                    stage="knowledge",
                    progress=50,
                    message=f"知识检索完成，找到 {triple_count} 个相关三元组",
                    data={"triple_count": triple_count}
                ).to_sse()
            except Exception as e:
                logger.warning(f"知识检索失败: {e}")
                yield ProgressEvent(
                    event="progress",
                    stage="knowledge",
                    progress=50,
                    message="知识检索跳过"
                ).to_sse()
        else:
            yield ProgressEvent(
                event="progress",
                stage="knowledge",
                progress=50,
                message="跳过知识检索（无症状或上下文）"
            ).to_sse()

        yield ProgressEvent(
            event="progress",
            stage="textual",
            progress=55,
            message="正在提取文本语义特征 (Qwen3-VL)..."
        ).to_sse()

        textual_result = None
        try:
            textual_result = await asyncio.to_thread(
                fusion_service._extract_textual_features,
                image=pil_image,
                symptoms=symptoms,
                knowledge_context=knowledge_context,
                enable_thinking=enable_thinking
            )
            disease_name = textual_result.get("diagnosis", {}).get("disease_name", "未知") if textual_result else "未知"
            yield ProgressEvent(
                event="progress",
                stage="textual",
                progress=75,
                message=f"文本分析完成，识别为: {disease_name}",
                data={"disease_name": disease_name}
            ).to_sse()
        except Exception as e:
            logger.warning(f"文本特征提取失败: {e}")
            yield ProgressEvent(
                event="progress",
                stage="textual",
                progress=75,
                message="文本分析跳过"
            ).to_sse()

        yield ProgressEvent(
            event="progress",
            stage="fusion",
            progress=80,
            message="正在融合多模态特征..."
        ).to_sse()

        fusion_result = fusion_service._fuse_features(
            visual_result=visual_result,
            textual_result=textual_result,
            knowledge_context=knowledge_context,
            original_image=pil_image
        )

        yield ProgressEvent(
            event="progress",
            stage="fusion",
            progress=90,
            message=f"特征融合完成，置信度: {fusion_result.confidence:.2%}",
            data={
                "disease_name": fusion_result.disease_name,
                "confidence": fusion_result.confidence
            }
        ).to_sse()

        inference_time = time.time() - start_time

        result = {
            "success": True,
            "diagnosis": {
                "disease_name": fusion_result.disease_name,
                "disease_name_en": fusion_result.disease_name_en,
                "confidence": fusion_result.confidence,
                "visual_confidence": fusion_result.visual_confidence,
                "textual_confidence": fusion_result.textual_confidence,
                "knowledge_confidence": fusion_result.knowledge_confidence,
                "description": fusion_result.description,
                "symptoms": fusion_result.symptoms,
                "causes": fusion_result.causes,
                "recommendations": fusion_result.recommendations,
                "treatment": fusion_result.treatment,
                "medicines": fusion_result.medicines,
                "severity": fusion_result.severity,
                "knowledge_references": fusion_result.knowledge_references,
                "kad_former_used": fusion_result.kad_former_used,
                "inference_time_ms": fusion_result.inference_time_ms
            },
            "features": {
                "visual_detection": visual_result is not None,
                "textual_analysis": textual_result is not None,
                "graph_rag_enabled": use_graph_rag
            },
            "performance": {
                "inference_time_ms": round(inference_time * 1000, 2),
                "cache_hit": False,
                "thinking_mode_enabled": enable_thinking,
                "graph_rag_enabled": use_graph_rag
            }
        }

        if enable_thinking and fusion_result.reasoning_chain:
            result["reasoning_chain"] = fusion_result.reasoning_chain

        if fusion_result.roi_boxes:
            result["diagnosis"]["roi_boxes"] = fusion_result.roi_boxes

        if fusion_result.annotated_image:
            result["diagnosis"]["annotated_image"] = fusion_result.annotated_image

        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id=f"ai_{int(time.time()*1000)}",
                image_hash=None,
                symptoms=symptoms or "",
                disease_detected=fusion_result.disease_name or "未知",
                confidence=float(fusion_result.confidence) if fusion_result.confidence else 0.0,
                processing_time_ms=round(inference_time * 1000, 2),
                success=True
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(inference_time * 1000, 2), success=True)
        except Exception:
            pass

        yield ProgressEvent(
            event="complete",
            stage="complete",
            progress=100,
            message="多模态融合诊断完成",
            data=result
        ).to_sse()

    except GeneratorExit:
        logger.info("SSE 客户端断开连接，清理资源")
        raise
    except Exception as e:
        logger.error(f"SSE 流式诊断失败: {e}", exc_info=True)
        inference_time = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=round(inference_time * 1000, 2),
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(inference_time * 1000, 2), success=False)
        except Exception:
            pass

        yield ProgressEvent(
            event="error",
            stage="error",
            progress=0,
            message="诊断过程中发生错误，请稍后重试",
            data={"error_type": "internal_error"}
        ).to_sse()


@router.post("/image")
async def diagnose_image(
    image: UploadFile = File(..., description="病害图像文件"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    YOLOv8 图像病害检测

    使用 YOLOv8 目标检测模型对上传的小麦病害图像进行检测，
    识别病害类型、位置边界框和置信度。

    支持的病害类型包括：
    - 小麦条锈病 (Stripe Rust)
    - 小麦叶锈病 (Leaf Rust)
    - 小麦白粉病 (Powdery Mildew)
    - 赤霉病 (Fusarium Head Blight)
    - 其他常见小麦病害

    参数:
        image: 上传的图像文件（支持 JPG、PNG 格式）

    返回:
        Dict: 检测结果，包含以下字段：
            - success: 是否成功
            - data: 详细检测结果
                - detections: 检测到的目标列表（边界框坐标）
                - count: 检测到的目标数量
                - diagnosis: 诊断详情（病害名称、置信度等）
            - model: 使用的模型标识
            - message: 结果描述

    错误码:
        400: 图像格式不支持或文件损坏
        500: 检测服务内部错误

    认证要求: 需要用户登录令牌 (Bearer Token)
    """
    start_time = time.time()
    try:
        ensure_ai_service_ready()

        image_bytes = await image.read()

        is_valid, error_msg = validate_image(image_bytes, image.filename or "unknown")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        pil_image = Image.open(io.BytesIO(image_bytes))

        from app.services.yolo_service import get_yolo_service

        yolo_service = get_yolo_service()
        result = yolo_service.detect(pil_image)

        if not result["success"]:
            elapsed = time.time() - start_time
            try:
                from app.services.diagnosis_logger import log_diagnosis
                log_diagnosis(
                    request_id=f"ai_{int(time.time()*1000)}",
                    image_hash=None,
                    symptoms="",
                    disease_detected="",
                    confidence=0.0,
                    processing_time_ms=round(elapsed * 1000, 2),
                    success=False,
                    error=result.get("error", "检测失败")[:500]
                )
            except Exception:
                pass

            try:
                from app.api.v1.metrics import record_inference
                record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
            except Exception:
                pass

            raise HTTPException(status_code=500, detail=result.get("error", "检测失败"))

        elapsed = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id=f"ai_{int(time.time()*1000)}",
                image_hash=None,
                symptoms="",
                disease_detected=result.get("diagnosis", {}).get("disease_name", "未知"),
                confidence=float(result.get("diagnosis", {}).get("confidence", 0)),
                processing_time_ms=round(elapsed * 1000, 2),
                success=True
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(elapsed * 1000, 2), success=True)
        except Exception:
            pass

        return {
            "success": True,
            "data": result,
            "message": f"检测到 {result['count']} 个病害"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图像诊断失败：{e}", exc_info=True)
        elapsed = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=round(elapsed * 1000, 2),
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
        except Exception:
            pass

        raise HTTPException(status_code=500, detail="诊断失败，请稍后重试")


@router.post("/multimodal")
async def diagnose_multimodal(
    image: Optional[UploadFile] = File(None, description="病害图像文件（可选）"),
    symptoms: str = Form("", description="症状描述"),
    thinking_mode: bool = Form(True, description="是否启用 Thinking 推理链模式"),
    use_graph_rag: bool = Form(True, description="是否使用 Graph-RAG 知识增强"),
    enable_kad_former: bool = Form(True, description="是否启用 KAD-Former 融合"),
    disease_context: Optional[str] = Form(None, description="疾病上下文（用于 Graph-RAG 检索）"),
    use_cache: bool = Form(True, description="是否使用缓存优化"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Qwen3-VL 多模态诊断（增强版）

    参数:
        image: 上传的图像文件（可选）
        symptoms: 症状描述文本
        thinking_mode: 是否启用 Thinking 推理链模式
        use_graph_rag: 是否使用 Graph-RAG 知识增强
        enable_kad_former: 是否启用 KAD-Former 融合
        disease_context: 疾病上下文（用于 Graph-RAG 检索）
        use_cache: 是否使用缓存优化

    返回:
        综合诊断结果，包括病害识别、推理链、知识引用等
    """
    start_time = time.time()

    try:
        ensure_ai_service_ready()

        pil_image = None
        image_bytes = None
        if image:
            image_bytes = await image.read()
            pil_image = Image.open(io.BytesIO(image_bytes))

        from app.services.qwen_service import get_qwen_service
        from app.services.cache_manager import get_cache_manager

        qwen_service = get_qwen_service()
        if qwen_service.is_lazy_load and not qwen_service.is_loaded:
            logger.info("多模态诊断：检测到懒加载模式，正在加载模型...")
            try:
                await qwen_service.ensure_loaded()
                logger.info("多模态诊断：模型加载完成")
            except Exception as e:
                logger.error(f"模型加载失败: {e}")
                elapsed = time.time() - start_time
                try:
                    from app.services.diagnosis_logger import log_diagnosis
                    log_diagnosis(
                        request_id="error",
                        image_hash=None,
                        symptoms=symptoms or "",
                        disease_detected="",
                        confidence=0.0,
                        processing_time_ms=round(elapsed * 1000, 2),
                        success=False,
                        error=f"模型加载失败：{str(e)}"[:500]
                    )
                except Exception:
                    pass

                try:
                    from app.api.v1.metrics import record_inference
                    record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
                except Exception:
                    pass

                return {
                    "success": False,
                    "error": f"模型加载失败：{str(e)}",
                    "fallback_suggestion": "请稍后重试或联系管理员",
                    "model_loading": True
                }

        cache_hit = None
        if use_cache and image_bytes:
            cache_manager = get_cache_manager()
            cache_result = cache_manager.get(image_bytes, symptoms)

            if cache_result:
                cache_hit = cache_result
                logger.info(f"缓存命中：source={cache_result.get('source')}")

        if cache_hit:
            inference_time = time.time() - start_time
            try:
                from app.services.diagnosis_logger import log_diagnosis
                log_diagnosis(
                    request_id=f"ai_cache_{int(time.time()*1000)}",
                    image_hash=None,
                    symptoms=symptoms or "",
                    disease_detected=cache_hit["result"].get("disease_name", "未知"),
                    confidence=float(cache_hit["result"].get("confidence", 0)),
                    processing_time_ms=round(inference_time * 1000, 2),
                    success=True,
                    cache_hit=True
                )
            except Exception:
                pass

            try:
                from app.api.v1.metrics import record_inference
                record_inference(latency_ms=round(inference_time * 1000, 2), success=True)
            except Exception:
                pass

            response = {
                "success": True,
                "data": cache_hit["result"],
                "cache_info": {
                    "hit": True,
                    "source": cache_hit.get("source"),
                    "similarity": cache_hit.get("similarity")
                },
                "performance": {
                    "inference_time_ms": round(inference_time * 1000, 2),
                    "cache_hit": True
                },
                "message": "从缓存获取诊断结果"
            }
            return response

        try:
            qwen_service = get_qwen_service()

            if not qwen_service.is_loaded:
                logger.warning("Qwen 模型未加载，使用文本诊断降级方案")
                result = qwen_service.diagnose(
                    symptoms=symptoms,
                    enable_thinking=thinking_mode,
                    use_graph_rag=use_graph_rag,
                    disease_context=disease_context or symptoms
                )
            else:
                result = qwen_service.diagnose(
                    image=pil_image,
                    symptoms=symptoms,
                    enable_thinking=thinking_mode,
                    use_graph_rag=use_graph_rag,
                    disease_context=disease_context or symptoms
                )

            if use_cache and image_bytes and result["success"]:
                cache_manager = get_cache_manager()
                cache_manager.set(
                    image_data=image_bytes,
                    symptoms=symptoms,
                    diagnosis_result=result["diagnosis"],
                    ttl=3600
                )

            if not result["success"]:
                logger.error(f"诊断失败：{result.get('error')}")
                elapsed = time.time() - start_time
                try:
                    from app.services.diagnosis_logger import log_diagnosis
                    log_diagnosis(
                        request_id=f"ai_{int(time.time()*1000)}",
                        image_hash=None,
                        symptoms=symptoms or "",
                        disease_detected="",
                        confidence=0.0,
                        processing_time_ms=round(elapsed * 1000, 2),
                        success=False,
                        error=result.get("error", "诊断服务暂时不可用")[:500]
                    )
                except Exception:
                    pass

                try:
                    from app.api.v1.metrics import record_inference
                    record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
                except Exception:
                    pass

                return {
                    "success": False,
                    "error": result.get("error", "诊断服务暂时不可用"),
                    "fallback_suggestion": "请稍后重试或仅使用症状描述进行诊断"
                }

        except Exception as e:
            logger.error(f"诊断过程异常：{e}")
            elapsed = time.time() - start_time
            try:
                from app.services.diagnosis_logger import log_diagnosis
                log_diagnosis(
                    request_id=f"ai_{int(time.time()*1000)}",
                    image_hash=None,
                    symptoms=symptoms or "",
                    disease_detected="",
                    confidence=0.0,
                    processing_time_ms=round(elapsed * 1000, 2),
                    success=False,
                    error=f"诊断异常：{str(e)}"[:500]
                )
            except Exception:
                pass

            try:
                from app.api.v1.metrics import record_inference
                record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
            except Exception:
                pass

            return {
                "success": False,
                "error": f"诊断异常：{str(e)}",
                "fallback_suggestion": "请检查模型配置或稍后重试"
            }

        inference_time = time.time() - start_time

        response = {
            "success": True,
            "data": result["diagnosis"],
            "model": result["model"],
            "features": result.get("features", {}),
            "performance": {
                "inference_time_ms": round(inference_time * 1000, 2),
                "thinking_mode_enabled": thinking_mode,
                "graph_rag_enabled": use_graph_rag,
                "kad_former_enabled": enable_kad_former
            }
        }

        if thinking_mode and result.get("reasoning_chain"):
            response["reasoning_chain"] = result["reasoning_chain"]

        if use_graph_rag and result.get("knowledge_references"):
            response["knowledge_references"] = result["knowledge_references"]

        diagnosis = result["diagnosis"]
        response["confidence_analysis"] = {
            "overall_confidence": diagnosis.get("confidence", 0.0),
            "visual_confidence": diagnosis.get("visual_confidence", 0.0),
            "textual_confidence": diagnosis.get("textual_confidence", 0.0),
            "knowledge_confidence": diagnosis.get("knowledge_confidence", 0.0) if use_graph_rag else None
        }

        response["message"] = "多模态诊断成功"

        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id=f"ai_{int(time.time()*1000)}",
                image_hash=None,
                symptoms=symptoms or "",
                disease_detected=result.get("diagnosis", {}).get("disease_name", "未知"),
                confidence=float(result.get("diagnosis", {}).get("confidence", 0)),
                processing_time_ms=round(inference_time * 1000, 2),
                success=True
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(inference_time * 1000, 2), success=True)
        except Exception:
            pass

        return response

    except Exception as e:
        logger.error(f"多模态诊断失败：{e}", exc_info=True)
        inference_time = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=round(inference_time * 1000, 2),
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(inference_time * 1000, 2), success=False)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="诊断失败，请稍后重试"
        )


@router.post("/text")
async def diagnose_text(
    symptoms: str = Form(..., description="症状描述"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    LLM 文本诊断

    基于大语言模型（Qwen3-VL）的纯文本症状诊断接口。
    用户输入小麦病害的症状描述，AI 模型将分析并返回：
    - 可能的病害类型
    - 置信度评分
    - 详细病因分析
    - 防治建议和用药方案

    适用场景：
    - 无法获取图像时的远程诊断
    - 辅助图像诊断的补充信息
    - 快速初步筛查

    参数:
        symptoms: 症状描述（建议包含：发病部位、症状特征、
                 发病时间、环境条件、传播情况等）

    返回:
        Dict: 诊断结果，包含以下字段：
            - success: 是否成功
            - data: 诊断详情
                - disease_name: 病害名称
                - confidence: 置信度 (0-1)
                - description: 病害描述
                - symptoms: 症状分析
                - causes: 可能的病因
                - recommendations: 防治建议
                - treatment: 治疗方案
            - model: 使用的模型标识
            - message: 结果描述

    错误码:
        400: 症状描述为空或格式错误
        500: 诊断服务内部错误
        503: 模型加载失败

    认证要求: 需要用户登录令牌 (Bearer Token)
    """
    start_time = time.time()

    try:
        ensure_ai_service_ready()

        from app.services.qwen_service import get_qwen_service

        qwen_service = get_qwen_service()

        if qwen_service.is_lazy_load and not qwen_service.is_loaded:
            logger.info("文本诊断：检测到懒加载模式，正在加载模型...")
            try:
                await qwen_service.ensure_loaded()
                logger.info("文本诊断：模型加载完成")
            except Exception as e:
                logger.error(f"模型加载失败: {e}")
                elapsed = time.time() - start_time
                try:
                    from app.services.diagnosis_logger import log_diagnosis
                    log_diagnosis(
                        request_id="error",
                        image_hash=None,
                        symptoms=symptoms or "",
                        disease_detected="",
                        confidence=0.0,
                        processing_time_ms=round(elapsed * 1000, 2),
                        success=False,
                        error=f"模型加载失败：{str(e)}"[:500]
                    )
                except Exception:
                    pass

                try:
                    from app.api.v1.metrics import record_inference
                    record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
                except Exception:
                    pass

                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": f"模型加载失败：{str(e)}",
                        "model_loading": True,
                        "suggestion": "请稍后重试"
                    }
                )

        result = qwen_service.diagnose(symptoms=symptoms)

        if not result["success"]:
            elapsed = time.time() - start_time
            try:
                from app.services.diagnosis_logger import log_diagnosis
                log_diagnosis(
                    request_id=f"ai_{int(time.time()*1000)}",
                    image_hash=None,
                    symptoms=symptoms or "",
                    disease_detected="",
                    confidence=0.0,
                    processing_time_ms=round(elapsed * 1000, 2),
                    success=False,
                    error=result.get("error", "诊断失败")[:500]
                )
            except Exception:
                pass

            try:
                from app.api.v1.metrics import record_inference
                record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
            except Exception:
                pass

            raise HTTPException(status_code=500, detail=result.get("error", "诊断失败"))

        elapsed = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id=f"ai_{int(time.time()*1000)}",
                image_hash=None,
                symptoms=symptoms or "",
                disease_detected=result.get("diagnosis", {}).get("disease_name", "未知"),
                confidence=float(result.get("diagnosis", {}).get("confidence", 0)),
                processing_time_ms=round(elapsed * 1000, 2),
                success=True
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(elapsed * 1000, 2), success=True)
        except Exception:
            pass

        return {
            "success": True,
            "data": result["diagnosis"],
            "model": result["model"],
            "message": "文本诊断成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本诊断失败：{e}", exc_info=True)
        elapsed = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=round(elapsed * 1000, 2),
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(elapsed * 1000, 2), success=False)
        except Exception:
            pass

        raise HTTPException(status_code=500, detail="诊断失败，请稍后重试")


@router.get("/health/ai")
async def ai_health() -> Dict[str, Any]:
    """
    AI 服务健康检查（PERF-01 增强）

    返回各 AI 模型的详细状态，包括懒加载状态信息。

    Returns:
        Dict: AI 健康状态信息
    """
    health_info = {
        "status": "healthy",
        "services": {}
    }

    try:
        from app.services.yolo_service import get_yolo_service
        from app.services.qwen_service import get_qwen_service

        try:
            yolo_service = get_yolo_service()
            yolo_info = yolo_service.get_model_info()
            health_info["services"]["yolov8"] = yolo_info
            if not yolo_info.get("is_loaded", False):
                health_info["status"] = "degraded"
                logger.warning("YOLO 服务未加载模型")
        except Exception as e:
            logger.error(f"YOLO 健康检查失败：{e}")
            health_info["services"]["yolov8"] = {
                "status": "error",
                "error": str(e)
            }
            health_info["status"] = "degraded"

        try:
            qwen_service = get_qwen_service()
            qwen_info = qwen_service.get_model_info()

            loader_status = qwen_service.loader.get_model_status()
            qwen_info.update({
                "state": loader_status.get("state", "unknown"),
                "lazy_load": loader_status.get("lazy_load", False),
                "load_progress": (
                    100 if loader_status.get("is_loaded") else 0
                ),
                "last_error": loader_status.get("last_error")
            })

            health_info["services"]["qwen3vl"] = qwen_info

            model_state = loader_status.get("state")
            if model_state == "unloaded":
                health_info["status"] = "degraded"
                logger.info("Qwen3-VL 模型未加载（懒加载模式）")
            elif model_state == "loading":
                health_info["status"] = "degraded"
                health_info["message"] = "Qwen3-VL 模型正在加载中..."
            elif model_state == "error":
                health_info["status"] = "degraded"
                logger.warning(f"Qwen3-VL 模型加载失败: {loader_status.get('last_error')}")
            elif not qwen_info.get("is_loaded", False):
                health_info["status"] = "degraded"
                logger.warning("Qwen 服务未加载模型")

        except Exception as e:
            logger.error(f"Qwen 健康检查失败：{e}")
            health_info["services"]["qwen3vl"] = {
                "status": "error",
                "error": str(e)
            }
            health_info["status"] = "degraded"

        return health_info

    except Exception as e:
        logger.error(f"AI 健康检查失败：{e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取缓存统计信息

    返回:
        缓存性能指标，包括命中率、缓存大小等
    """
    try:
        from app.services.cache_manager import get_cache_manager

        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取缓存统计失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取缓存统计失败，请稍后重试")


@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    清空所有诊断缓存

    管理员专用接口，用于清除系统中所有诊断结果的缓存数据。
    缓存用于优化重复查询的响应速度，但在以下情况可能需要清空：
    - 模型更新后需要刷新缓存
    - 诊断算法调整后需要重新计算
    - 排查缓存相关问题时
    - 释放内存空间

    注意事项：
    - 此操作不可逆，清空后所有缓存数据将丢失
    - 清空后的首次查询会重新计算，响应时间可能较长
    - 建议在低峰期执行此操作

    返回:
        Dict: 操作结果，包含以下字段：
            - success: 是否成功
            - message: 操作描述

    错误码:
        401: 未提供管理员令牌
        403: 权限不足（非管理员用户）
        500: 缓存服务内部错误

    权限要求: 需要管理员权限 (require_admin)
    """
    try:
        from app.services.cache_manager import get_cache_manager

        cache_manager = get_cache_manager()
        cache_manager.clear()

        return {
            "success": True,
            "message": "缓存已清空"
        }

    except Exception as e:
        logger.error(f"清空缓存失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="清空缓存失败，请稍后重试")


@router.post("/batch")
async def diagnose_batch(
    images: List[UploadFile] = File(..., description="病害图像文件列表"),
    symptoms: str = Form("", description="症状描述"),
    thinking_mode: bool = Form(False, description="是否启用 Thinking 推理链模式（批量模式默认关闭）"),
    use_graph_rag: bool = Form(False, description="是否使用 Graph-RAG（批量模式默认关闭）"),
    use_cache: bool = Form(True, description="是否使用缓存优化"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    批量图像诊断

    参数:
        images: 上传的图像文件列表（最多 10 张）
        symptoms: 症状描述（应用于所有图像）
        thinking_mode: 是否启用 Thinking 推理链模式
        use_graph_rag: 是否使用 Graph-RAG
        use_cache: 是否使用缓存优化

    返回:
        批量诊断结果汇总
    """
    start_time = time.time()

    if len(images) > 10:
        raise HTTPException(status_code=400, detail="单次最多支持 10 张图像")

    try:
        ensure_ai_service_ready()

        from app.services.qwen_service import get_qwen_service
        from app.services.cache_manager import get_cache_manager
        from app.services.vram_manager import get_vram_manager

        vram_mgr = get_vram_manager()
        vram_mgr.check_and_warn()

        cache_manager = get_cache_manager() if use_cache else None
        results = []
        success_count = 0
        cache_hits = 0

        for i, image in enumerate(images):
            try:
                image_bytes = await image.read()
                pil_image = Image.open(io.BytesIO(image_bytes))

                cache_result = None
                if cache_manager:
                    cache_result = cache_manager.get(image_bytes, symptoms)
                    if cache_result:
                        cache_hits += 1
                        results.append({
                            "index": i,
                            "filename": image.filename,
                            "success": True,
                            "diagnosis": cache_result["result"],
                            "cache_hit": True,
                            "cache_source": cache_result.get("source")
                        })
                        continue

                qwen_service = get_qwen_service()
                result = qwen_service.diagnose(
                    image=pil_image,
                    symptoms=symptoms,
                    enable_thinking=thinking_mode,
                    use_graph_rag=use_graph_rag
                )

                if cache_manager and result["success"]:
                    cache_manager.set(
                        image_bytes=image_bytes,
                        symptoms=symptoms,
                        diagnosis_result=result["diagnosis"],
                        ttl=3600
                    )

                if result["success"]:
                    success_count += 1
                    results.append({
                        "index": i,
                        "filename": image.filename,
                        "success": True,
                        "diagnosis": result["diagnosis"]
                    })
                else:
                    results.append({
                        "index": i,
                        "filename": image.filename,
                        "success": False,
                        "error": result.get("error", "诊断失败")
                    })

            except Exception as e:
                logger.error(f"批量诊断中第 {i} 张图像失败：{e}")
                results.append({
                    "index": i,
                    "filename": image.filename,
                    "success": False,
                    "error": str(e)
                })
            finally:
                if (i + 1) % 3 == 0:
                    vram_mgr.cleanup(aggressive=False)

        vram_mgr.cleanup(aggressive=True)

        total_time = time.time() - start_time

        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id=f"ai_batch_{int(time.time()*1000)}",
                image_hash=None,
                symptoms=symptoms or "",
                disease_detected=f"批量诊断({success_count}/{len(images)}成功)",
                confidence=0.0,
                processing_time_ms=round(total_time * 1000, 2),
                success=True
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(total_time * 1000, 2), success=True)
        except Exception:
            pass

        return {
            "success": True,
            "summary": {
                "total_images": len(images),
                "success_count": success_count,
                "failed_count": len(images) - success_count,
                "cache_hits": cache_hits,
                "cache_hit_rate": round(cache_hits / len(images) * 100, 2) if images else 0,
                "success_rate": round(success_count / len(images) * 100, 2) if images else 0
            },
            "results": results,
            "performance": {
                "total_time_ms": round(total_time * 1000, 2),
                "avg_time_per_image_ms": round((total_time * 1000) / len(images), 2) if images else 0
            },
            "message": f"批量诊断完成，成功 {success_count}/{len(images)} 张，缓存命中 {cache_hits} 次"
        }

    except Exception as e:
        logger.error(f"批量诊断失败：{e}", exc_info=True)
        total_time = time.time() - start_time
        try:
            from app.services.diagnosis_logger import log_diagnosis
            log_diagnosis(
                request_id="error",
                image_hash=None,
                symptoms="",
                disease_detected="",
                confidence=0.0,
                processing_time_ms=round(total_time * 1000, 2),
                success=False,
                error=str(e)[:500]
            )
        except Exception:
            pass

        try:
            from app.api.v1.metrics import record_inference
            record_inference(latency_ms=round(total_time * 1000, 2), success=False)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="批量诊断失败，请稍后重试"
        )


@router.post("/admin/ai/preload")
async def preload_ai_models(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    管理员接口：预加载 AI 模型（PERF-01）

    手动触发 Qwen3-VL 模型的预加载，适用于：
    - 管理后台的模型预热操作
    - 低峰期提前加载以优化用户体验
    - 维护后的模型重新加载

    权限要求：需要管理员权限（require_admin）

    Returns:
        Dict: 预加载结果
    """
    start_time = time.time()

    try:
        from app.services.qwen_service import get_qwen_service

        qwen_service = get_qwen_service()
        current_state = qwen_service.loader.get_state().value

        logger.info(f"[管理员] 触发 AI 模型预加载，当前状态: {current_state}")

        if current_state == "ready":
            return {
                "success": True,
                "model_state": "ready",
                "load_time_ms": 0,
                "message": "模型已处于就绪状态，无需重复加载",
                "skipped": True
            }

        if current_state == "loading":
            return {
                "success": False,
                "model_state": "loading",
                "load_time_ms": 0,
                "message": "模型正在加载中，请稍候...",
                "skipped": True
            }

        success = qwen_service.loader.preload_model(
            model_path=qwen_service.model_path,
            device=qwen_service.device,
            load_in_4bit=qwen_service.load_in_4bit,
            cpu_offload=qwen_service.cpu_offload,
            enable_flash_attention=qwen_service.enable_flash_attention,
            torch_compile=qwen_service.torch_compile
        )

        load_time = time.time() - start_time
        final_state = qwen_service.loader.get_state().value

        if success and final_state == "ready":
            qwen_service.loader.warmup()
            logger.info(f"[管理员] AI 模型预加载成功，耗时: {load_time:.2f}s")

            return {
                "success": True,
                "model_state": final_state,
                "load_time_ms": round(load_time * 1000, 2),
                "message": f"Qwen3-VL-2B-Instruct 预加载完成（{load_time:.1f}s）",
                "model_info": qwen_service.get_model_info()
            }
        else:
            error_msg = qwen_service.loader._last_error or "未知错误"
            logger.error(f"[管理员] AI 模型预加载失败: {error_msg}")

            return {
                "success": False,
                "model_state": final_state,
                "load_time_ms": round(load_time * 1000, 2),
                "error": error_msg,
                "message": f"预加载失败: {error_msg}"
            }

    except Exception as e:
        load_time = time.time() - start_time
        logger.error(f"[管理员] AI 模型预加载异常: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail="预加载异常，请稍后重试"
        )


RECORD_TAG = "诊断记录"


@router.get(
    "/records",
    response_model=DiagnosisListResponse,
    summary="查询诊断记录",
    description="获取当前用户的诊断历史记录列表，支持分页查询。",
    tags=[RECORD_TAG],
)
@sanitize_response(fields_to_sanitize=["symptoms", "diagnosis_result", "suggestions"])
async def get_diagnosis_records(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询诊断历史记录

    获取当前用户的诊断历史记录列表，支持分页查询。
    """
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
            diagnosis_result=record.disease.name if record.disease else record.disease_name,
            confidence=float(record.confidence) if record.confidence else None,
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
    description="根据诊断记录 ID 获取单条诊断记录的详细信息。",
    tags=[RECORD_TAG],
)
@sanitize_response(fields_to_sanitize=["symptoms", "diagnosis_result", "suggestions"])
async def get_diagnosis_detail(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取诊断详情

    根据诊断记录 ID 获取单条诊断记录的详细信息。
    只能查询自己的诊断记录。
    """
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
        diagnosis_result=record.disease.name if record.disease else record.disease_name,
        confidence=float(record.confidence) if record.confidence else None,
        suggestions=record.recommendations if isinstance(record.recommendations, list) else (json.loads(record.recommendations) if isinstance(record.recommendations, str) and record.recommendations else None),
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


@router.put(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
    summary="更新诊断记录",
    description="更新指定诊断记录的信息（如添加备注、修改状态等）。",
    tags=[RECORD_TAG],
)
async def update_diagnosis_record(
    diagnosis_id: int,
    update_data: DiagnosisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新诊断记录

    更新指定诊断记录的信息，只能更新自己的诊断记录。
    """
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
        diagnosis_result=record.disease.name if record.disease else record.disease_name,
        confidence=float(record.confidence) if record.confidence else None,
        suggestions=record.recommendations,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


@router.delete(
    "/{diagnosis_id}",
    summary="删除诊断记录",
    description="删除指定的诊断记录及其关联的图像文件。",
    tags=[RECORD_TAG],
)
async def delete_diagnosis_record(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除诊断记录

    删除指定的诊断记录及其关联的图像文件，只能删除自己的诊断记录。
    """
    record = db.query(Diagnosis).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="诊断记录不存在")

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
