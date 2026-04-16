# -*- coding: utf-8 -*-
"""
WheatAgent FastAPI 主应用

提供RESTful API服务，支持：
- 图像病害诊断
- 文本症状诊断
- 批量诊断
- 反馈提交
- 健康检查
- 模型管理

根据文档8.2节软件技术栈实现

优化特性:
- 请求日志记录
- 请求限流
- 响应缓存
- 安全检查
"""
import os
import sys
import asyncio
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, HTTPException, status, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.middleware import (
    RequestLoggerMiddleware,
    RateLimitMiddleware,
    RateLimiter,
    SecurityMiddleware,
    ResponseCache,
    global_rate_limiter,
    global_response_cache
)

# 尝试导入各模块，提供优雅降级
VisionEngine = None
CognitionEngine = None
FusionEngine = None
GraphEngine = None

try:
    from src.vision.vision_engine import VisionAgent as VisionEngine
except ImportError as e:
    print(f"⚠️ 视觉引擎导入失败: {e}")

try:
    from src.cognition.cognition_engine import CognitionEngine
except ImportError as e:
    print(f"⚠️ 认知引擎导入失败: {e}")

try:
    from src.fusion.fusion_engine import FusionAgent as FusionEngine
except ImportError as e:
    print(f"⚠️ 融合引擎导入失败: {e}")

try:
    from src.graph.graph_engine import KnowledgeAgent as GraphEngine
except ImportError as e:
    print(f"⚠️ 知识图谱引擎导入失败: {e}")


# ============ Pydantic模型定义 ============

class DiagnosisRequest(BaseModel):
    """诊断请求模型"""
    image_path: Optional[str] = Field(None, description="图像文件路径")
    text_description: Optional[str] = Field(None, description="文本症状描述")
    use_knowledge: bool = Field(True, description="是否使用知识图谱")
    top_k: int = Field(3, ge=1, le=10, description="返回前K个结果")


class BatchDiagnosisRequest(BaseModel):
    """批量诊断请求模型"""
    image_paths: List[str] = Field(..., description="图像文件路径列表")
    use_knowledge: bool = Field(True, description="是否使用知识图谱")
    top_k: int = Field(3, ge=1, le=10, description="返回前K个结果")


class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    diagnosis_id: str = Field(..., description="诊断ID")
    image_path: str = Field(..., description="图像路径")
    system_diagnosis: str = Field(..., description="系统诊断结果")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    user_correction: Optional[str] = Field(None, description="用户修正")
    comments: Optional[str] = Field(None, description="评论")
    reviewer_id: Optional[str] = Field(None, description="审核人ID")


class DiagnosisResult(BaseModel):
    """诊断结果模型"""
    disease_name: str = Field(..., description="病害名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    bbox: Optional[List[float]] = Field(None, description="检测框坐标 [x1, y1, x2, y2]")
    severity: Optional[str] = Field(None, description="严重程度")
    description: Optional[str] = Field(None, description="病害描述")
    treatment: Optional[str] = Field(None, description="防治建议")


class DiagnosisResponse(BaseModel):
    """诊断响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="状态消息")
    timestamp: str = Field(..., description="时间戳")
    diagnosis_id: Optional[str] = Field(None, description="诊断ID")
    data: Dict[str, Any] = Field(..., description="诊断数据")


class BatchDiagnosisResponse(BaseModel):
    """批量诊断响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="状态消息")
    batch_id: str = Field(..., description="批量任务ID")
    total: int = Field(..., description="总数量")
    completed: int = Field(..., description="已完成数量")
    results: List[Dict[str, Any]] = Field(..., description="诊断结果列表")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API版本")
    timestamp: str = Field(..., description="时间戳")
    uptime_seconds: Optional[float] = Field(None, description="运行时间(秒)")
    components: Dict[str, bool] = Field(..., description="组件状态")
    gpu_available: bool = Field(..., description="GPU是否可用")


class ModelInfo(BaseModel):
    """模型信息模型"""
    name: str = Field(..., description="模型名称")
    version: str = Field(..., description="模型版本")
    status: str = Field(..., description="模型状态")
    loaded_at: Optional[str] = Field(None, description="加载时间")
    params_count: Optional[int] = Field(None, description="参数量")


class ModelsResponse(BaseModel):
    """模型列表响应模型"""
    success: bool = Field(..., description="是否成功")
    models: List[ModelInfo] = Field(..., description="模型列表")


class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="状态消息")
    feedback_id: str = Field(..., description="反馈ID")
    status: str = Field(..., description="反馈状态")


class SystemStats(BaseModel):
    """系统统计模型"""
    total_diagnoses: int = Field(0, description="总诊断次数")
    total_feedbacks: int = Field(0, description="总反馈次数")
    avg_response_time_ms: float = Field(0, description="平均响应时间(毫秒)")
    uptime_seconds: float = Field(0, description="运行时间(秒)")


# ============ 全局组件实例 ============

class AppState:
    """应用状态管理"""
    def __init__(self):
        self.vision_engine: Optional[VisionEngine] = None
        self.cognition_engine: Optional[CognitionEngine] = None
        self.fusion_engine: Optional[FusionEngine] = None
        self.graph_engine: Optional[GraphEngine] = None
        self.startup_time: Optional[datetime] = None
        
        # 统计信息
        self.total_diagnoses: int = 0
        self.total_feedbacks: int = 0
        self.response_times: List[float] = []
        
        # 线程池用于异步处理
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 诊断历史记录
        self.diagnosis_history: Dict[str, Dict] = {}
        
    def initialize(self):
        """初始化所有组件"""
        print("🚀 初始化WheatAgent组件...")
        
        try:
            # 初始化知识图谱引擎（先初始化，因为其他模块可能依赖它）
            print("  📚 加载知识图谱引擎...")
            self.graph_engine = GraphEngine()
            
            # 初始化视觉引擎
            print("  📷 加载视觉引擎...")
            self.vision_engine = VisionEngine()
            
            # 初始化认知引擎
            print("  🧠 加载认知引擎...")
            self.cognition_engine = CognitionEngine()
            
            # 初始化融合引擎
            print("  🔗 加载融合引擎...")
            self.fusion_engine = FusionEngine(
                knowledge_agent=self.graph_engine
            )
            
            self.startup_time = datetime.now()
            print("✅ 所有组件初始化完成!")
            
        except Exception as e:
            print(f"❌ 组件初始化失败: {e}")
            raise
    
    def get_component_status(self) -> Dict[str, bool]:
        """获取组件状态"""
        return {
            "vision": self.vision_engine is not None,
            "cognition": self.cognition_engine is not None,
            "fusion": self.fusion_engine is not None,
            "graph": self.graph_engine is not None
        }
    
    def is_gpu_available(self) -> bool:
        """检查GPU是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def get_uptime_seconds(self) -> float:
        """获取运行时间（秒）"""
        if self.startup_time:
            return (datetime.now() - self.startup_time).total_seconds()
        return 0
    
    def record_diagnosis(self, diagnosis_id: str, result: Dict):
        """记录诊断结果"""
        self.diagnosis_history[diagnosis_id] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.total_diagnoses += 1
    
    def record_response_time(self, response_time: float):
        """记录响应时间"""
        self.response_times.append(response_time)
        # 只保留最近1000条记录
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times) * 1000  # 转换为毫秒


# 全局状态实例
app_state = AppState()


# ============ 生命周期管理 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    app_state.initialize()
    yield
    # 关闭时清理
    print("🛑 关闭WheatAgent服务...")


# ============ FastAPI应用实例 ============

app = FastAPI(
    title="WheatAgent API",
    description="基于多模态特征融合的小麦病害诊断智能体API服务",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityMiddleware, max_content_length=50 * 1024 * 1024)
app.add_middleware(RateLimitMiddleware, rate_limiter=global_rate_limiter)
app.add_middleware(RequestLoggerMiddleware)


# ============ API端点 ============

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径 - API信息"""
    return {
        "name": "WheatAgent API",
        "version": "1.0.0",
        "description": "基于多模态特征融合的小麦病害诊断智能体",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy" if all(app_state.get_component_status().values()) else "degraded",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        uptime_seconds=app_state.get_uptime_seconds(),
        components=app_state.get_component_status(),
        gpu_available=app_state.is_gpu_available()
    )


@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """获取系统统计信息"""
    return SystemStats(
        total_diagnoses=app_state.total_diagnoses,
        total_feedbacks=app_state.total_feedbacks,
        avg_response_time_ms=app_state.get_avg_response_time(),
        uptime_seconds=app_state.get_uptime_seconds()
    )


@app.get("/stats/rate-limit")
async def get_rate_limit_stats(request: Request):
    """
    获取限流统计信息
    
    返回当前客户端的请求统计
    """
    client_ip = request.client.host if request.client else "unknown"
    stats = global_rate_limiter.get_stats(client_ip)
    return {
        "success": True,
        "data": stats
    }


@app.get("/stats/cache")
async def get_cache_stats():
    """
    获取缓存统计信息
    
    返回响应缓存的统计信息
    """
    return {
        "success": True,
        "data": global_response_cache.get_stats()
    }


@app.post("/cache/clear")
async def clear_cache():
    """
    清空响应缓存
    
    管理员操作，清空所有缓存数据
    """
    global_response_cache.clear()
    return {
        "success": True,
        "message": "缓存已清空"
    }


@app.post("/diagnose/image", response_model=DiagnosisResponse)
async def diagnose_image(
    file: UploadFile = File(..., description="病害图像文件"),
    use_knowledge: bool = True,
    top_k: int = 3
):
    """
    图像病害诊断端点
    
    上传小麦病害图像，返回诊断结果
    """
    start_time = datetime.now()
    diagnosis_id = str(uuid.uuid4())
    
    try:
        # 验证文件类型
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持图像文件"
            )
        
        # 保存上传的文件
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = upload_dir / f"{timestamp}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 执行诊断
        if app_state.fusion_engine:
            results = app_state.fusion_engine.diagnose(
                image_path=str(file_path),
                use_knowledge=use_knowledge,
                top_k=top_k,
                vision_engine=app_state.vision_engine,
                cognition_engine=app_state.cognition_engine
            )
        else:
            # 降级处理：仅使用视觉引擎
            results = app_state.vision_engine.detect(str(file_path))
        
        # 记录诊断结果
        app_state.record_diagnosis(diagnosis_id, results)
        
        # 记录响应时间
        response_time = (datetime.now() - start_time).total_seconds()
        app_state.record_response_time(response_time)
        
        return DiagnosisResponse(
            success=True,
            message="诊断成功",
            timestamp=datetime.now().isoformat(),
            diagnosis_id=diagnosis_id,
            data={
                "image_path": str(file_path),
                "results": results,
                "model_used": "fusion" if app_state.fusion_engine else "vision_only",
                "response_time_ms": response_time * 1000
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"诊断失败: {str(e)}"
        )


@app.post("/diagnose/batch", response_model=BatchDiagnosisResponse)
async def batch_diagnose(
    request: BatchDiagnosisRequest,
    background_tasks: BackgroundTasks
):
    """
    批量诊断端点
    
    对多张图像进行批量诊断
    """
    batch_id = str(uuid.uuid4())
    results = []
    
    for image_path in request.image_paths:
        try:
            if not os.path.exists(image_path):
                results.append({
                    "image_path": image_path,
                    "success": False,
                    "error": "文件不存在"
                })
                continue
            
            if app_state.fusion_engine:
                result = app_state.fusion_engine.diagnose(
                    image_path=image_path,
                    use_knowledge=request.use_knowledge,
                    top_k=request.top_k,
                    vision_engine=app_state.vision_engine,
                    cognition_engine=app_state.cognition_engine
                )
            else:
                result = app_state.vision_engine.detect(image_path)
            
            results.append({
                "image_path": image_path,
                "success": True,
                "result": result
            })
            
        except Exception as e:
            results.append({
                "image_path": image_path,
                "success": False,
                "error": str(e)
            })
    
    app_state.total_diagnoses += len(request.image_paths)
    
    return BatchDiagnosisResponse(
        success=True,
        message=f"批量诊断完成: {len(results)}/{len(request.image_paths)}",
        batch_id=batch_id,
        total=len(request.image_paths),
        completed=len([r for r in results if r.get("success")]),
        results=results
    )


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    提交诊断反馈端点
    
    用户可以提交对诊断结果的反馈，用于模型改进
    """
    feedback_id = str(uuid.uuid4())
    
    try:
        # 保存反馈
        feedback_dir = Path("data/human_feedback")
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        feedback_data = {
            "feedback_id": feedback_id,
            "diagnosis_id": request.diagnosis_id,
            "image_path": request.image_path,
            "system_diagnosis": request.system_diagnosis,
            "confidence": request.confidence,
            "user_correction": request.user_correction,
            "comments": request.comments,
            "reviewer_id": request.reviewer_id,
            "timestamp": datetime.now().isoformat()
        }
        
        feedback_file = feedback_dir / f"feedback_{feedback_id}.json"
        import json
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        
        app_state.total_feedbacks += 1
        
        # 判断反馈状态
        if request.confidence < 0.6:
            status_msg = "pending_review"
        elif request.user_correction:
            status_msg = "correction_submitted"
        else:
            status_msg = "accepted"
        
        return FeedbackResponse(
            success=True,
            message="反馈提交成功",
            feedback_id=feedback_id,
            status=status_msg
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"反馈提交失败: {str(e)}"
        )


@app.post("/diagnose/text", response_model=DiagnosisResponse)
async def diagnose_text(
    description: str,
    use_knowledge: bool = True,
    top_k: int = 3
):
    """
    文本症状诊断端点
    
    根据文本症状描述返回诊断结果
    """
    try:
        if not app_state.cognition_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="认知引擎未加载"
            )
        
        # 执行文本诊断
        results = app_state.cognition_engine.analyze_text(
            text=description,
            use_knowledge=use_knowledge,
            top_k=top_k
        )
        
        return DiagnosisResponse(
            success=True,
            message="诊断成功",
            timestamp=datetime.now().isoformat(),
            data={
                "text_input": description,
                "results": results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"诊断失败: {str(e)}"
        )


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """获取已加载的模型列表"""
    models = []
    
    if app_state.vision_engine:
        models.append(ModelInfo(
            name="VisionEngine",
            version="1.0.0",
            status="loaded",
            loaded_at=app_state.startup_time.isoformat() if app_state.startup_time else None
        ))
    
    if app_state.cognition_engine:
        models.append(ModelInfo(
            name="CognitionEngine",
            version="1.0.0",
            status="loaded",
            loaded_at=app_state.startup_time.isoformat() if app_state.startup_time else None
        ))
    
    if app_state.fusion_engine:
        models.append(ModelInfo(
            name="FusionEngine",
            version="1.0.0",
            status="loaded",
            loaded_at=app_state.startup_time.isoformat() if app_state.startup_time else None
        ))
    
    if app_state.graph_engine:
        models.append(ModelInfo(
            name="GraphEngine",
            version="1.0.0",
            status="loaded",
            loaded_at=app_state.startup_time.isoformat() if app_state.startup_time else None
        ))
    
    return ModelsResponse(success=True, models=models)


@app.get("/knowledge/diseases")
async def list_diseases():
    """获取知识图谱中的病害列表"""
    try:
        if not app_state.graph_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="知识图谱引擎未加载"
            )
        
        diseases = app_state.graph_engine.get_all_diseases()
        
        return {
            "success": True,
            "count": len(diseases),
            "diseases": diseases
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取病害列表失败: {str(e)}"
        )


@app.get("/knowledge/disease/{disease_name}")
async def get_disease_info(disease_name: str):
    """获取特定病害的详细信息"""
    try:
        if not app_state.graph_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="知识图谱引擎未加载"
            )
        
        info = app_state.graph_engine.get_disease_info(disease_name)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到病害: {disease_name}"
            )
        
        return {
            "success": True,
            "disease": disease_name,
            "info": info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取病害信息失败: {str(e)}"
        )


# ============ 错误处理 ============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"服务器错误: {str(exc)}",
            "timestamp": datetime.now().isoformat()
        }
    )


# ============ 主函数 ============

def main():
    """启动API服务"""
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
