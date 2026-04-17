"""
诊断报告生成 API
提供 PDF 和 HTML 格式的诊断报告导出功能
"""
import logging
import os
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import Optional
from PIL import Image
import io

from app.core.security import get_current_user
from app.models.user import User
from app.api.v1.diagnosis_validator import ensure_ai_service_ready

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["诊断报告"])


@router.post("/generate")
async def generate_report(
    image: Optional[UploadFile] = File(None, description="病害图像文件"),
    symptoms: str = Form("", description="症状描述"),
    thinking_mode: bool = Form(True, description="是否启用 Thinking 模式"),
    use_graph_rag: bool = Form(True, description="是否使用 Graph-RAG"),
    report_format: str = Form("both", description="报告格式：pdf/html/both"),
    current_user: User = Depends(get_current_user)
):
    """
    生成诊断报告
    
    参数:
        image: 上传的图像文件
        symptoms: 症状描述
        thinking_mode: 是否启用 Thinking 模式
        use_graph_rag: 是否使用 Graph-RAG
        report_format: 报告格式（pdf/html/both）
        
    返回:
        诊断结果和报告文件路径
    """
    try:
        from app.services.qwen_service import get_qwen_service
        from app.services.report_generator import get_report_generator
        
        pil_image = None
        image_bytes = None
        if image:
            image_bytes = await image.read()
            if not image_bytes or len(image_bytes) < 10:
                raise HTTPException(
                    status_code=422,
                    detail="上传的图像文件为空或数据不完整，请提供有效的病害图像"
                )
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                pil_image.verify()
                pil_image = Image.open(io.BytesIO(image_bytes))
            except Exception as img_err:
                raise HTTPException(
                    status_code=422,
                    detail=f"图像文件格式无效或已损坏：{str(img_err)}"
                )
        
        if not pil_image and not symptoms.strip():
            raise HTTPException(
                status_code=422,
                detail="请至少提供病害图像或症状描述中的一项"
            )

        ensure_ai_service_ready()
        qwen_service = get_qwen_service()
        diagnosis_result = qwen_service.diagnose(
            image=pil_image,
            symptoms=symptoms,
            enable_thinking=thinking_mode,
            use_graph_rag=use_graph_rag
        )
        
        if not diagnosis_result["success"]:
            raise HTTPException(status_code=500, detail=diagnosis_result.get("error", "诊断失败"))
        
        # 生成报告
        report_generator = get_report_generator()
        report_files = report_generator.generate_report(
            diagnosis_result=diagnosis_result,
            image_data=image_bytes,
            format=report_format
        )
        
        return {
            "success": True,
            "diagnosis": diagnosis_result["diagnosis"],
            "report_files": {
                fmt: str(path) for fmt, path in report_files.items()
            },
            "message": f"报告生成成功，共 {len(report_files)} 个文件"
        }
        
    except Exception as e:
        logger.error(f"报告生成失败：{e}")
        raise HTTPException(status_code=500, detail=f"报告生成失败：{str(e)}")


@router.get("/download/{filename}")
async def download_report(filename: str, current_user: User = Depends(get_current_user)):
    """
    下载报告文件
    
    参数:
        filename: 报告文件名
        
    返回:
        报告文件
    """
    try:
        from app.services.report_generator import get_report_generator
        from fastapi.responses import FileResponse
        
        report_generator = get_report_generator()
        allowed_dir = os.path.abspath(str(report_generator.output_dir))
        file_path = os.path.abspath(os.path.join(allowed_dir, filename))
        
        if not file_path.startswith(allowed_dir + os.sep) and file_path != allowed_dir:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="报告文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf" if filename.endswith(".pdf") else "text/html"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告失败：{e}")
        raise HTTPException(status_code=500, detail=f"下载失败：{str(e)}")


@router.get("/list")
async def list_reports(current_user: User = Depends(get_current_user)):
    """
    列出所有报告文件
    
    返回:
        报告文件列表
    """
    try:
        from app.services.report_generator import get_report_generator
        
        report_generator = get_report_generator()
        
        if not report_generator.output_dir.exists():
            return {"success": True, "reports": [], "message": "报告目录不存在"}
        
        reports = []
        for file in report_generator.output_dir.glob("diagnosis_report_*"):
            if file.is_file():
                reports.append({
                    "filename": file.name,
                    "size": file.stat().st_size,
                    "created_at": file.stat().st_ctime,
                    "format": "pdf" if file.suffix == ".pdf" else "html"
                })
        
        # 按创建时间倒序排序
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "reports": reports,
            "total": len(reports)
        }
        
    except Exception as e:
        logger.error(f"列出报告失败：{e}")
        raise HTTPException(status_code=500, detail=f"列出报告失败：{str(e)}")
