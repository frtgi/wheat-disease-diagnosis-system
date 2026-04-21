# -*- coding: utf-8 -*-
"""
多模态特征融合服务 (Multimodal Feature Fusion Service) - 门面类

提供统一的多模态诊断接口，内部协调：
1. FeatureExtractor: 特征提取（YOLO/Qwen/GraphRAG）
2. FusionEngine: 融合算法（KAD-Former）
3. ResultAnnotator: 结果标注和缓存

使用 Facade 模式简化复杂子系统的访问，
保持向后兼容的同时降低整体复杂度。
"""
import logging
import time
import asyncio
import warnings
from functools import wraps
from typing import Dict, Optional, Any, Callable
from contextlib import contextmanager
from PIL import Image
import numpy as np


def deprecated(replacement: str) -> Callable:
    """
    标记已弃用的方法，调用时发出 DeprecationWarning

    Args:
        replacement: 推荐替代的方法名

    Returns:
        装饰器函数，包装原方法并在调用时发出警告
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} 已弃用，请使用 {replacement} 替代",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

from .fusion_feature_extractor import FeatureExtractor
from .fusion_engine import FusionEngine, FusionResult
from .fusion_annotator import ResultAnnotator

logger = logging.getLogger(__name__)


class PipelineTimer:
    """
    流水线计时器
    
    用于测量融合诊断流水线各阶段的耗时，
    支持上下文管理器和手动计时两种模式。
    
    使用示例:
        timer = PipelineTimer()
        
        with timer.stage("图像预处理"):
            preprocess_image(image)
            
        with timer.stage("YOLO 推理"):
            yolo.detect(image)
            
        logger.info(timer.summary())
    """
    
    def __init__(self) -> None:
        """初始化流水线计时器"""
        self._stages: Dict[str, float] = {}
        self._start: Optional[float] = None
        self._current_stage: Optional[str] = None
        self._pipeline_start: float = time.time()
    
    def start(self, stage_name: str) -> "PipelineTimer":
        """
        开始计时某个阶段
        
        Args:
            stage_name: 阶段名称
            
        Returns:
            self，支持链式调用
        """
        self._start = time.time()
        self._current_stage = stage_name
        return self
    
    def end(self, stage_name: str = None) -> float:
        """
        结束计时并返回耗时（毫秒）
        
        Args:
            stage_name: 阶段名称（可选，默认使用当前阶段名）
            
        Returns:
            float: 该阶段耗时（毫秒）
        """
        if self._start is None:
            logger.warning("PipelineTimer.end() 在 start() 之前被调用")
            return 0.0
        
        elapsed = (time.time() - self._start) * 1000
        name = stage_name or self._current_stage
        if name:
            self._stages[name] = round(elapsed, 2)
            logger.info(f"[Pipeline] {name}: {elapsed:.2f}ms")
        self._start = None
        self._current_stage = None
        return elapsed
    
    @contextmanager
    def stage(self, stage_name: str) -> Any:
        """
        上下文管理器模式计时某个阶段
        
        Args:
            stage_name: 阶段名称
            
        Yields:
            None
            
        示例:
            with timer.stage("预处理"):
                do_something()
        """
        self.start(stage_name)
        try:
            yield
        finally:
            self.end(stage_name)
    
    def summary(self) -> Dict[str, Any]:
        """
        返回所有阶段耗时摘要
        
        Returns:
            Dict: 包含各阶段耗时的字典，格式：
                {
                    "stages": {"stage1": 10.5, "stage2": 23.2},
                    "total": 33.7,
                    "stage_count": 2,
                    "pipeline_total_ms": ...
                }
        """
        total_pipeline_time = (time.time() - self._pipeline_start) * 1000
        total_stages = sum(self._stages.values())
        
        return {
            "stages": dict(self._stages),
            "total_stages_ms": round(total_stages, 2),
            "stage_count": len(self._stages),
            "pipeline_total_ms": round(total_pipeline_time, 2),
            "overhead_ms": round(total_pipeline_time - total_stages, 2)
        }
    
    def log_summary(self) -> None:
        """将计时摘要输出到日志"""
        info = self.summary()
        logger.info("=" * 50)
        logger.info("[Pipeline Timer] 性能摘要:")
        logger.info(f"  总阶段数: {info['stage_count']}")
        logger.info(f"  各阶段总耗时: {info['total_stages_ms']:.2f}ms")
        logger.info(f"  流水线总耗时: {info['pipeline_total_ms']:.2f}ms")
        logger.info(f"  开销时间: {info['overhead_ms']:.2f}ms")
        logger.info("-" * 50)
        for stage_name, elapsed in info["stages"].items():
            percentage = (elapsed / max(info["total_stages_ms"], 0.001)) * 100
            logger.info(f"  {stage_name}: {elapsed:.2f}ms ({percentage:.1f}%)")
        logger.info("=" * 50)
    
    def reset(self) -> None:
        """重置计时器"""
        self._stages.clear()
        self._start = None
        self._current_stage = None
        self._pipeline_start = time.time()


class MultimodalFusionService:
    """
    多模态融合服务（门面类）
    
    作为 Facade 模式的门面，协调三个核心子模块：
    - FeatureExtractor: 负责从 YOLO/Qwen/GraphRAG 提取特征
    - FusionEngine: 负责 KAD-Former 多模态融合算法
    - ResultAnnotator: 负责结果标注、缓存和响应构建
    
    对外提供简洁的 diagnose()/diagnose_async() 接口，
    内部处理复杂的初始化、特征提取、融合和后处理流程。
    
    Attributes:
        _feature_extractor: 特征提取器实例
        _fusion_engine: 融合引擎实例
        _result_annotator: 结果标注器实例
        _initialized: 是否已完成初始化
        _warmed_up: 是否已预热模型
    """

    def __init__(self, enable_cache: bool = True) -> None:
        """
        初始化融合服务门面
        
        Args:
            enable_cache: 是否启用推理结果缓存
        """
        # 初始化子模块（延迟加载服务实例）
        self._feature_extractor = FeatureExtractor()
        self._fusion_engine = FusionEngine()
        self._result_annotator = ResultAnnotator()
        
        # 状态标记
        self._initialized = False
        self._enable_cache = enable_cache
        self._warmed_up = False

    def initialize(self) -> None:
        """
        初始化所有依赖服务和子模块
        
        按顺序初始化：
        1. YOLO 服务 → FeatureExtractor
        2. Qwen 服务 → FeatureExtractor  
        3. GraphRAG 服务 → FeatureExtractor
        4. KAD-Former 模型 → FusionEngine
        5. 缓存服务 → ResultAnnotator
        6. 模型预热
        """
        if self._initialized:
            logger.debug("融合服务已初始化，跳过")
            return
        
        logger.info("开始初始化多模态融合服务...")
        
        try:
            # 导入并初始化各服务
            logger.debug("导入 YOLO 服务...")
            from .yolo_service import get_yolo_service
            
            logger.debug("导入 Qwen 服务...")
            from .qwen_service import get_qwen_service
            
            logger.debug("导入 GraphRAG 服务...")
            from .graphrag_service import get_graphrag_service
            
            logger.debug("导入 KAD-Former...")
            from .kad_attention import create_kad_former
            
            # 初始化 YOLO 服务
            logger.info("初始化 YOLO 服务...")
            yolo_service = get_yolo_service()
            yolo_status = "已加载" if (yolo_service and yolo_service.is_loaded) else "未加载"
            logger.info(f"YOLO 服务状态: {yolo_status}")
            self._feature_extractor.set_services(yolo_service=yolo_service)
            
            # 初始化 Qwen 服务
            logger.info("初始化 Qwen 服务...")
            qwen_service = get_qwen_service()
            qwen_status = "已加载" if (qwen_service and qwen_service.is_loaded) else "未加载"
            logger.info(f"Qwen 服务状态: {qwen_status}")
            self._feature_extractor.set_services(qwen_service=qwen_service)
            
            # 初始化 GraphRAG 服务
            logger.info("初始化 GraphRAG 服务...")
            graphrag_service = get_graphrag_service()
            graphrag_status = "已初始化" if (graphrag_service and graphrag_service._initialized) else "未初始化"
            logger.info(f"GraphRAG 服务状态: {graphrag_status}")
            self._feature_extractor.set_services(graphrag_service=graphrag_service)
            
            # 初始化 KAD-Former
            import torch
            if torch.cuda.is_available():
                logger.info("CUDA 可用，初始化 KAD-Former...")
                kad_former = create_kad_former()
                kad_former.eval()
                self._fusion_engine.set_kad_former(kad_former)
                logger.info("KAD-Former 初始化成功")
            else:
                logger.info("CUDA 不可用，跳过 KAD-Former 初始化")
            
            # 初始化缓存服务
            if self._enable_cache:
                try:
                    from .inference_cache_service import get_inference_cache
                    cache_service = get_inference_cache()
                    self._result_annotator.set_cache_service(cache_service)
                    logger.info("推理缓存服务初始化成功")
                except Exception as cache_err:
                    logger.warning(f"推理缓存服务初始化失败: {cache_err}，将继续运行但不使用缓存")
            
            self._initialized = True
            logger.info("多模态融合服务初始化成功")
            logger.info(f"服务汇总: YOLO={yolo_status}, Qwen={qwen_status}, GraphRAG={graphrag_status}, Cache={'启用' if self._result_annotator._cache_service else '禁用'}")
            
            # 模型预热
            self._warmup_models()
            
        except Exception as e:
            logger.error(f"多模态融合服务初始化失败：{e}", exc_info=True)
            self._initialized = False

    def _warmup_models(self) -> None:
        """
        模型预热机制
        
        执行一次推理以初始化 CUDA 内核，提高后续推理速度。
        预热包括：YOLO、Qwen、KAD-Former（如果可用）
        """
        if self._warmed_up:
            logger.debug("模型已预热，跳过")
            return
        
        logger.info("开始模型预热...")
        start_time = time.time()
        
        try:
            # 预热 YOLO
            yolo_service = self._feature_extractor._yolo_service
            if yolo_service and getattr(yolo_service, 'is_loaded', False):
                logger.debug("预热 YOLO 模型...")
                dummy_image = Image.fromarray(np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8))
                _ = yolo_service.detect(dummy_image)
                logger.debug("YOLO 模型预热完成")
            
            # 预热 Qwen
            qwen_service = self._feature_extractor._qwen_service
            if qwen_service and getattr(qwen_service, 'is_loaded', False):
                logger.debug("预热 Qwen 模型...")
                dummy_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
                _ = qwen_service.diagnose(
                    image=dummy_image,
                    symptoms="warmup",
                    enable_thinking=False,
                    use_graph_rag=False
                )
                logger.debug("Qwen 模型预热完成")
            
            # 预热 KAD-Former
            kad_former = self._fusion_engine._kad_former
            if kad_former is not None:
                logger.debug("预热 KAD-Former...")
                import torch
                visual_features = torch.randn(1, 1, 768) * 0.1
                text_features = torch.randn(1, 1, 2560) * 0.1
                knowledge_embeddings = torch.randn(1, 1, 256) * 0.1
                with torch.no_grad():
                    _ = kad_former(
                        visual_features=visual_features,
                        text_features=text_features,
                        knowledge_embeddings=knowledge_embeddings
                    )
                logger.debug("KAD-Former 预热完成")
            
            self._warmed_up = True
            warmup_time = time.time() - start_time
            logger.info(f"模型预热完成，耗时 {warmup_time:.2f}秒")
            
        except Exception as e:
            logger.warning(f"模型预热失败: {e}，将继续运行但可能影响首次推理速度")

    @deprecated("diagnose_async")
    def diagnose(
        self,
        image: Optional[Image.Image] = None,
        symptoms: str = "",
        enable_thinking: bool = False,
        use_graph_rag: bool = True,
        disease_context: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        ⚠️ 已弃用：请使用 diagnose_async() 替代

        执行多模态融合诊断（同步兼容层）

        此方法为向后兼容保留的同步接口，内部使用 asyncio.run() 包装异步缓存操作。
        在已运行事件循环的异步上下文中调用将引发 RuntimeError。

        推荐使用 diagnose_async() 以获得原生异步性能和避免嵌套事件循环问题。
        
        Args:
            image: PIL 图像对象
            symptoms: 症状描述文本
            enable_thinking: 是否启用 Thinking 推理链模式
            use_graph_rag: 是否使用 GraphRAG 知识增强
            disease_context: 疾病上下文（用于 GraphRAG 检索）
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 完整的诊断结果字典
        """
        start_time = time.time()
        timer = PipelineTimer()
        
        logger.info("=" * 60)
        logger.info("开始多模态融合诊断")
        logger.info(f"输入参数: image={'有' if image else '无'}, symptoms='{symptoms[:50]}...' (如有), enable_thinking={enable_thinking}, use_graph_rag={use_graph_rag}, use_cache={use_cache}")
        
        # 确保已初始化
        if not self._initialized:
            logger.warning("融合服务未初始化，正在初始化...")
            self.initialize()
            logger.info(f"融合服务初始化状态: {self._initialized}")
        
        # 初始化响应结构
        result = {
            "success": False,
            "diagnosis": None,
            "model": "fusion_engine",
            "features": {},
            "cache_hit": False
        }
        
        # 准备图像数据（用于缓存键）
        image_data = None
        if image is not None:
            image_data = self._result_annotator.pil_to_bytes(image)
        
        # 检查缓存
        if use_cache and image_data:
            try:
                cached_result = asyncio.run(self._result_annotator.check_cache(image_data, symptoms))
                if cached_result:
                    logger.info("缓存命中，直接返回缓存结果")
                    cached_result["success"] = True
                    cached_result["cache_hit"] = True
                    cached_result["features"]["cache_hit"] = True
                    return cached_result
            except Exception as cache_err:
                logger.warning(f"缓存检查失败: {cache_err}")
        
        try:
            with timer.stage("特征提取"):
                # 步骤1-3: 提取所有特征
                visual_result, textual_result, knowledge_context = \
                    self._feature_extractor.extract_all_features(
                        image=image,
                        symptoms=symptoms,
                        enable_thinking=enable_thinking,
                        use_graph_rag=use_graph_rag,
                        disease_context=disease_context
                    )
                
                # 记录特征提取状态
                result["features"]["visual_detection"] = visual_result is not None
                result["features"]["textual_analysis"] = textual_result is not None
                result["features"]["graph_rag_enabled"] = use_graph_rag and knowledge_context is not None
            
            with timer.stage("图像标注"):
                # 生成标注图像（如果有检测结果）
                annotated_image = None
                if image is not None and visual_result:
                    detections = visual_result.get("detections", [])
                    if detections:
                        annotated_image = self._result_annotator.annotate_image(
                            image=image,
                            detections=detections
                        )
            
            with timer.stage("特征融合"):
                # 步骤4: 执行融合
                fusion_result = self._fusion_engine.fuse_features(
                    visual_result=visual_result,
                    textual_result=textual_result,
                    knowledge_context=knowledge_context,
                    original_image=image,
                    annotated_image=annotated_image
                )
                logger.info(f"特征融合完成: disease_name='{fusion_result.disease_name}', confidence={fusion_result.confidence:.4f}")
            
            with timer.stage("响应构建"):
                # 构建响应字典
                result = self._result_annotator.build_response_dict(
                    fusion_result=fusion_result,
                    enable_thinking=enable_thinking,
                    timer_summary=timer.summary()
                )
                result["features"]["cache_hit"] = False
            
            # 异步保存到缓存
            if use_cache and image_data:
                try:
                    asyncio.run(self._result_annotator.save_to_cache(image_data, result, symptoms))
                except Exception as cache_err:
                    logger.warning(f"保存到缓存失败: {cache_err}")
            
            inference_time = time.time() - start_time
            logger.info(f"融合诊断完成: success={result['success']}, 总耗时={inference_time*1000:.2f}ms")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"融合诊断失败：{e}", exc_info=True)
            result["error"] = str(e)
        
        return result

    async def diagnose_async(
        self,
        image: Optional[Image.Image] = None,
        symptoms: str = "",
        enable_thinking: bool = False,
        use_graph_rag: bool = True,
        disease_context: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行多模态融合诊断（异步接口）
        
        与 diagnose() 功能完全相同，但使用原生异步方式处理缓存操作，
        避免 asyncio.run() 的嵌套调用问题（Task 2 修复）。
        
        Args:
            image: PIL 图像对象
            symptoms: 症状描述文本
            enable_thinking: 是否启用 Thinking 推理链模式
            use_graph_rag: 是否使用 GraphRAG 知识增强
            disease_context: 疾病上下文（用于 GraphRAG 检索）
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 完整的诊断结果字典
        """
        start_time = time.time()
        timer = PipelineTimer()
        
        logger.info("=" * 60)
        logger.info("开始异步多模态融合诊断")
        
        # 确保已初始化
        if not self._initialized:
            self.initialize()
        
        result = {
            "success": False,
            "diagnosis": None,
            "model": "fusion_engine",
            "features": {},
            "cache_hit": False
        }
        
        image_data = None
        if image is not None:
            image_data = self._result_annotator.pil_to_bytes(image)
        
        # 异步检查缓存
        if use_cache and image_data:
            try:
                cached_result = await self._result_annotator.check_cache(image_data, symptoms)
                if cached_result:
                    logger.info("异步缓存命中，直接返回缓存结果")
                    cached_result["success"] = True
                    cached_result["cache_hit"] = True
                    cached_result["features"]["cache_hit"] = True
                    return cached_result
            except Exception as cache_err:
                logger.warning(f"异步缓存检查失败: {cache_err}")
        
        try:
            with timer.stage("特征提取"):
                visual_result, textual_result, knowledge_context = \
                    self._feature_extractor.extract_all_features(
                        image=image,
                        symptoms=symptoms,
                        enable_thinking=enable_thinking,
                        use_graph_rag=use_graph_rag,
                        disease_context=disease_context
                    )
                
                result["features"]["visual_detection"] = visual_result is not None
                result["features"]["textual_analysis"] = textual_result is not None
                result["features"]["graph_rag_enabled"] = use_graph_rag and knowledge_context is not None
            
            with timer.stage("图像标注"):
                annotated_image = None
                if image is not None and visual_result:
                    detections = visual_result.get("detections", [])
                    if detections:
                        annotated_image = self._result_annotator.annotate_image(
                            image=image,
                            detections=detections
                        )
            
            with timer.stage("特征融合"):
                fusion_result = self._fusion_engine.fuse_features(
                    visual_result=visual_result,
                    textual_result=textual_result,
                    knowledge_context=knowledge_context,
                    original_image=image,
                    annotated_image=annotated_image
                )
            
            with timer.stage("响应构建"):
                result = self._result_annotator.build_response_dict(
                    fusion_result=fusion_result,
                    enable_thinking=enable_thinking,
                    timer_summary=timer.summary()
                )
                result["features"]["cache_hit"] = False
            
            # 原生异步保存到缓存
            if use_cache and image_data:
                try:
                    await self._result_annotator.save_to_cache(image_data, result, symptoms)
                except Exception as cache_err:
                    logger.warning(f"异步保存到缓存失败: {cache_err}")
            
            inference_time = time.time() - start_time
            logger.info(f"异步融合诊断完成: success={result['success']}, 总耗时={inference_time*1000:.2f}ms")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"异步融合诊断失败：{e}", exc_info=True)
            result["error"] = str(e)
        
        return result

    # ========== 向后兼容的代理方法 ==========
    # 这些方法保留以支持 ai_diagnosis.py 等外部代码的直接调用
    
    def _extract_visual_features(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """代理方法：提取视觉特征（委托给 FeatureExtractor）"""
        return self._feature_extractor.extract_visual_features(image)

    def _extract_textual_features(
        self,
        image: Optional[Image.Image],
        symptoms: str,
        knowledge_context: Optional[Any],
        enable_thinking: bool
    ) -> Optional[Dict[str, Any]]:
        """代理方法：提取文本特征（委托给 FeatureExtractor）"""
        return self._feature_extractor.extract_textual_features(
            image=image,
            symptoms=symptoms,
            knowledge_context=knowledge_context,
            enable_thinking=enable_thinking
        )

    def _retrieve_knowledge(
        self,
        symptoms: str,
        disease_hint: Optional[str] = None
    ) -> Optional[Any]:
        """代理方法：检索知识（委托给 FeatureExtractor）"""
        return self._feature_extractor.extract_knowledge_features(
            symptoms=symptoms,
            disease_hint=disease_hint
        )

    def _fuse_features(
        self,
        visual_result: Optional[Dict[str, Any]],
        textual_result: Optional[Dict[str, Any]],
        knowledge_context: Optional[Any],
        original_image: Optional[Image.Image] = None
    ) -> FusionResult:
        """代理方法：融合特征（委托给 FusionEngine）"""
        annotated_image = None
        if original_image and visual_result:
            detections = visual_result.get("detections", [])
            if detections:
                annotated_image = self._result_annotator.annotate_image(
                    image=original_image,
                    detections=detections
                )
        
        return self._fusion_engine.fuse_features(
            visual_result=visual_result,
            textual_result=textual_result,
            knowledge_context=knowledge_context,
            original_image=original_image,
            annotated_image=annotated_image
        )

    @deprecated("diagnose_async (内联 await 调用 _result_annotator.check_cache)")
    def _check_cache(
        self,
        image_data: bytes,
        symptoms: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ 已弃用：请在 diagnose_async() 中直接使用 await self._result_annotator.check_cache()

        代理方法：检查缓存（同步包装，内部使用 asyncio.run）
        """
        return asyncio.run(self._result_annotator.check_cache(image_data, symptoms))

    async def _save_to_cache(
        self,
        image_data: bytes,
        result: Dict[str, Any],
        symptoms: str = ""
    ) -> bool:
        """代理方法：保存到缓存（异步）"""
        return await self._result_annotator.save_to_cache(image_data, result, symptoms)


# 单例工厂函数
_fusion_service_instance: Optional[MultimodalFusionService] = None


def get_fusion_service() -> MultimodalFusionService:
    """
    获取融合服务单例
    
    使用懒加载模式，首次调用时创建实例。
    全局共享同一实例，避免重复初始化开销。
    
    Returns:
        MultimodalFusionService: 融合服务实例
    """
    global _fusion_service_instance
    
    if _fusion_service_instance is None:
        _fusion_service_instance = MultimodalFusionService()
    
    return _fusion_service_instance
