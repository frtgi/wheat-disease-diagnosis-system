# -*- coding: utf-8 -*-
"""
WheatAgent FastAPI 主应用

提供RESTful API服务，支持：
- 图像病害诊断
- 健康检查
- 模型管理
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.vision.vision_engine import VisionAgent as VisionEngine
from src.cognition.cognition_engine import CognitionEngine
from src.fusion.fusion_engine import FusionAgent as FusionEngine
from src.graph.graph_engine import KnowledgeAgent as GraphEngine


# ============ Pydantic模型定义 ============

class DiagnosisRequest(BaseModel):
    """诊断请求模型"""
    image_path: Optional[str] = Field(None, description="图像文件路径")
    text_description: Optional[str] = Field(None, description="文本症状描述")
    use_knowledge: bool = Field(True, description="是否使用知识图谱")
    top_k: int = Field(3, ge=1, le=10, description="返回前K个结果")


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
    data: Dict[str, Any] = Field(..., description="诊断数据")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API版本")
    timestamp: str = Field(..., description="时间戳")
    components: Dict[str, bool] = Field(..., description="组件状态")


class ModelInfo(BaseModel):
    """模型信息模型"""
    name: str = Field(..., description="模型名称")
    version: str = Field(..., description="模型版本")
    status: str = Field(..., description="模型状态")
    loaded_at: Optional[str] = Field(None, description="加载时间")


class ModelsResponse(BaseModel):
    """模型列表响应模型"""
    success: bool = Field(..., description="是否成功")
    models: List[ModelInfo] = Field(..., description="模型列表")


# ============ 全局组件实例 ============

class AppState:
    """应用状态管理"""
    def __init__(self):
        self.vision_engine: Optional[VisionEngine] = None
        self.cognition_engine: Optional[CognitionEngine] = None
        self.fusion_engine: Optional[FusionEngine] = None
        self.graph_engine: Optional[GraphEngine] = None
        self.startup_time: Optional[datetime] = None
        
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
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        components=app_state.get_component_status()
    )


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
                top_k=top_k
            )
        else:
            # 降级处理：仅使用视觉引擎
            results = app_state.vision_engine.detect(str(file_path))
        
        return DiagnosisResponse(
            success=True,
            message="诊断成功",
            timestamp=datetime.now().isoformat(),
            data={
                "image_path": str(file_path),
                "results": results,
                "model_used": "fusion" if app_state.fusion_engine else "vision_only"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"诊断失败: {str(e)}"
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
