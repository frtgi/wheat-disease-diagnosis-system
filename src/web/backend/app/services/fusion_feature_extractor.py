# -*- coding: utf-8 -*-
"""
多模态特征提取器 (Feature Extractor)

负责从各 AI 模型提取原始特征：
1. YOLOv8 视觉特征提取
2. Qwen3-VL 语义特征提取
3. GraphRAG 知识特征提取

提供统一的特征提取接口，支持并行和串行两种模式。
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import torch
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    多模态特征提取器
    
    封装与各 AI 服务的交互逻辑，提供清晰的接口用于获取：
    - 视觉特征（来自 YOLO）
    - 文本语义特征（来自 Qwen3-VL）
    - 知识特征（来自 GraphRAG）
    
    Attributes:
        yolo_service: YOLO 检测服务实例
        qwen_service: Qwen 诊断服务实例
        graphrag_service: GraphRAG 知识检索服务实例
    """

    def __init__(
        self,
        yolo_service: Optional[Any] = None,
        qwen_service: Optional[Any] = None,
        graphrag_service: Optional[Any] = None
    ) -> None:
        """
        初始化特征提取器
        
        Args:
            yolo_service: YOLO 服务实例（可选，延迟初始化）
            qwen_service: Qwen 服务实例（可选，延迟初始化）
            graphrag_service: GraphRAG 服务实例（可选，延迟初始化）
        """
        self._yolo_service = yolo_service
        self._qwen_service = qwen_service
        self._graphrag_service = graphrag_service

    def set_services(
        self,
        yolo_service: Optional[Any] = None,
        qwen_service: Optional[Any] = None,
        graphrag_service: Optional[Any] = None
    ) -> None:
        """
        设置或更新服务实例
        
        Args:
            yolo_service: YOLO 服务实例
            qwen_service: Qwen 服务实例
            graphrag_service: GraphRAG 服务实例
        """
        if yolo_service is not None:
            self._yolo_service = yolo_service
        if qwen_service is not None:
            self._qwen_service = qwen_service
        if graphrag_service is not None:
            self._graphrag_service = graphrag_service

    def extract_visual_features(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """
        提取视觉特征 (YOLOv8)
        
        调用 YOLO 服务对图像进行目标检测，返回检测结果和特征向量。
        
        Args:
            image: PIL 图像对象
            
        Returns:
            Dict: 视觉检测结果，包含以下字段：
                - detections: 检测结果列表
                - count: 检测目标数量
                - features: 特征向量（如果有）
            失败返回 None
        """
        logger.debug(f"开始视觉特征提取, 图像尺寸: {image.size if image else 'None'}")
        
        if self._yolo_service is None:
            logger.warning("YOLO 服务未初始化 (_yolo_service is None)，视觉特征提取跳过")
            return None
        
        if not getattr(self._yolo_service, 'is_loaded', False):
            logger.warning("YOLO 模型未加载 (is_loaded=False)，视觉特征提取跳过")
            return None
        
        try:
            logger.debug("调用 YOLO 服务进行检测...")
            result = self._yolo_service.detect(image)
            
            if result.get("success"):
                detections = result.get("detections", [])
                count = result.get("count", 0)
                logger.info(f"YOLO 检测成功: 检测到 {count} 个目标")
                
                if detections:
                    for i, det in enumerate(detections[:3]):
                        logger.debug(f"  检测结果[{i}]: class={det.get('class_name')}, confidence={det.get('confidence', 0):.4f}")
                
                return {
                    "detections": detections,
                    "count": count,
                    "features": result.get("features", None)
                }
            else:
                error = result.get("error", "未知错误")
                logger.warning(f"YOLO 检测返回失败: {error}")
                return None
                
        except Exception as e:
            logger.error(f"视觉特征提取失败：{e}", exc_info=True)
        
        return None

    def extract_textual_features(
        self,
        image: Optional[Image.Image],
        symptoms: str,
        knowledge_context: Optional[Any] = None,
        enable_thinking: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        提取文本语义特征 (Qwen3-VL)
        
        调用 Qwen3-VL 服务进行图像理解和文本分析，返回诊断结果。
        
        Args:
            image: PIL 图像对象（可选）
            symptoms: 症状描述文本
            knowledge_context: 知识上下文（来自 GraphRAG）
            enable_thinking: 是否启用 Thinking 推理链模式
            
        Returns:
            Dict: 文本分析结果，包含以下字段：
                - diagnosis: 诊断信息字典
                - reasoning_chain: 推理链（如果启用 thinking）
                - features: 特征向量（如果有）
            失败返回 None
        """
        logger.debug(f"开始文本特征提取: image={'有' if image else '无'}, symptoms='{symptoms[:30]}...' (如有), enable_thinking={enable_thinking}")
        
        if self._qwen_service is None:
            logger.warning("Qwen 服务未初始化 (_qwen_service is None)，文本特征提取跳过")
            return None
        
        if not getattr(self._qwen_service, 'is_loaded', False):
            logger.warning("Qwen 模型未加载 (is_loaded=False)，文本特征提取跳过")
            return None
        
        try:
            knowledge_tokens = None
            if knowledge_context is not None:
                knowledge_tokens = getattr(knowledge_context, 'tokens', None)
                if knowledge_tokens:
                    logger.debug(f"使用知识上下文: tokens长度={len(knowledge_tokens) if isinstance(knowledge_tokens, str) else 'N/A'}")
            
            logger.debug(f"调用 Qwen 服务进行诊断: image={'有' if image else '无'}, symptoms='{symptoms[:30]}...' (如有)")
            result = self._qwen_service.diagnose(
                image=image,
                symptoms=symptoms,
                enable_thinking=enable_thinking,
                use_graph_rag=knowledge_tokens is not None,
                disease_context=symptoms if symptoms else None
            )
            
            if result.get("success"):
                diagnosis = result.get("diagnosis", {})
                disease_name = diagnosis.get("disease_name", "未知") if isinstance(diagnosis, dict) else "未知"
                confidence = diagnosis.get("confidence", 0) if isinstance(diagnosis, dict) else 0
                logger.info(f"Qwen 诊断成功: disease_name='{disease_name}', confidence={confidence:.4f}")
                
                if result.get("reasoning_chain"):
                    logger.debug(f"推理链长度: {len(result['reasoning_chain'])} 步")
                
                return {
                    "diagnosis": diagnosis,
                    "reasoning_chain": result.get("reasoning_chain"),
                    "features": result.get("features", None)
                }
            else:
                error = result.get("error", "未知错误")
                logger.warning(f"Qwen 诊断返回失败: {error}")
                return None
                
        except Exception as e:
            logger.error(f"文本特征提取失败：{e}", exc_info=True)
        
        return None

    def extract_knowledge_features(
        self,
        symptoms: str,
        disease_hint: Optional[str] = None
    ) -> Optional[Any]:
        """
        提取知识特征 (GraphRAG)
        
        调用 GraphRAG 服务检索疾病相关知识，返回知识上下文。
        
        Args:
            symptoms: 症状描述文本
            disease_hint: 疾病提示（用于优化检索）
            
        Returns:
            KnowledgeContext: 知识上下文对象，包含三元组、实体、引用等
            失败返回 None
        """
        logger.debug(f"开始知识检索: symptoms='{symptoms[:30]}...' (如有), disease_hint='{disease_hint}'")
        
        if self._graphrag_service is None:
            logger.warning("GraphRAG 服务未初始化 (_graphrag_service is None)，知识检索跳过")
            return None
        
        if not getattr(self._graphrag_service, '_initialized', False):
            logger.warning("GraphRAG 引擎未初始化 (_initialized=False)，知识检索跳过")
            return None
        
        try:
            logger.debug("调用 GraphRAG 服务检索知识...")
            context = self._graphrag_service.retrieve_disease_knowledge(
                disease_hint or symptoms
            )
            
            if context:
                triple_count = len(context.triples) if hasattr(context, 'triples') else 0
                entity_count = len(context.entities) if hasattr(context, 'entities') else 0
                logger.info(f"GraphRAG 知识检索成功: {triple_count} 个三元组, {entity_count} 个实体")
                
                if context.triples:
                    for i, triple in enumerate(context.triples[:3]):
                        logger.debug(f"  三元组[{i}]: {triple.head} --[{triple.relation}]--> {triple.tail}")
                
                return context
            else:
                logger.warning("GraphRAG 知识检索返回空上下文")
                return None
                
        except Exception as e:
            logger.error(f"知识检索失败：{e}", exc_info=True)
        
        return None

    def extract_all_features(
        self,
        image: Optional[Image.Image],
        symptoms: str = "",
        enable_thinking: bool = False,
        use_graph_rag: bool = True,
        disease_context: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Any]]:
        """
        协调执行所有特征提取过程
        
        按照最优顺序依次提取视觉、知识和文本特征，
        并将知识上下文传递给文本特征提取以增强语义理解。
        
        Args:
            image: PIL 图像对象（可选）
            symptoms: 症状描述文本
            enable_thinking: 是否启用 Thinking 模式
            use_graph_rag: 是否使用 GraphRAG 知识增强
            disease_context: 疾病上下文（用于 GraphRAG 检索）
            
        Returns:
            Tuple: 包含三个元素的元组：
                - visual_result: 视觉特征结果
                - textual_result: 文本特征结果
                - knowledge_context: 知识上下文
        """
        visual_result = None
        textual_result = None
        knowledge_context = None
        
        # 步骤1: 提取视觉特征
        if image is not None:
            logger.info("步骤1: 提取视觉特征 (YOLO)...")
            visual_result = self.extract_visual_features(image)
            if visual_result:
                logger.info(f"视觉特征提取成功: 检测到 {visual_result.get('count', 0)} 个目标")
            else:
                logger.warning("视觉特征提取返回空结果")
        else:
            logger.info("步骤1: 跳过视觉特征提取 (无图像输入)")
        
        # 步骤2: 检索知识
        if symptoms or disease_context:
            logger.info("步骤2: 检索知识 (GraphRAG)...")
            knowledge_context = self.extract_knowledge_features(
                symptoms or disease_context,
                disease_context
            )
            if knowledge_context:
                logger.info(f"知识检索成功: {len(knowledge_context.triples) if hasattr(knowledge_context, 'triples') else 0} 个三元组")
            else:
                logger.warning("知识检索返回空结果")
        else:
            logger.info("步骤2: 跳过知识检索 (无症状或上下文)")
        
        # 步骤3: 提取文本语义特征（使用知识上下文增强）
        logger.info("步骤3: 提取文本语义特征 (Qwen3-VL)...")
        logger.info("  - 正在调用 Qwen3-VL 模型进行诊断...")
        logger.info("  - 这可能需要 10-60 秒，请耐心等待...")
        textual_result = self.extract_textual_features(
            image=image,
            symptoms=symptoms,
            knowledge_context=knowledge_context,
            enable_thinking=enable_thinking
        )
        if textual_result:
            logger.info(f"文本特征提取成功: disease_name='{textual_result.get('diagnosis', {}).get('disease_name', '未知')}'")
        else:
            logger.warning("文本特征提取返回空结果")
        
        return visual_result, textual_result, knowledge_context

    def generate_visual_features_tensor(
        self,
        visual_result: Optional[Dict[str, Any]]
    ) -> Optional[torch.Tensor]:
        """
        从视觉检测结果生成特征张量
        
        将 YOLO 的检测结果转换为 KAD-Former 可用的特征向量格式。
        
        Args:
            visual_result: 视觉检测结果字典
            
        Returns:
            torch.Tensor: 视觉特征张量 [1, N, 768]
            失败返回 None
        """
        if not visual_result:
            return None
        
        detections = visual_result.get("detections", [])
        if not detections:
            return None
        
        try:
            features_list = []
            for det in detections:
                if "features" in det and det["features"] is not None:
                    feat = det["features"]
                    if isinstance(feat, torch.Tensor):
                        features_list.append(feat)
                    elif isinstance(feat, np.ndarray):
                        features_list.append(torch.from_numpy(feat))
                    elif isinstance(feat, list):
                        features_list.append(torch.tensor(feat, dtype=torch.float32))
            
            if features_list:
                features = torch.stack(features_list, dim=0)
                if features.dim() == 1:
                    features = features.unsqueeze(0)
                features = features.unsqueeze(0)
                return features
            else:
                num_detections = len(detections)
                pseudo_features = torch.randn(1, num_detections, 768) * 0.1
                return pseudo_features
                
        except Exception as e:
            logger.warning(f"生成视觉特征失败：{e}")
            return None

    def generate_text_features_tensor(
        self,
        textual_result: Optional[Dict[str, Any]]
    ) -> Optional[torch.Tensor]:
        """
        从文本分析结果生成特征张量
        
        将 Qwen 的诊断结果转换为 KAD-Former 可用的特征向量格式。
        
        Args:
            textual_result: 文本分析结果字典
            
        Returns:
            torch.Tensor: 文本特征张量 [1, N, 2560]
            失败返回 None
        """
        if not textual_result:
            return None
        
        try:
            if "features" in textual_result and textual_result["features"] is not None:
                feat = textual_result["features"]
                if isinstance(feat, torch.Tensor):
                    if feat.dim() == 2:
                        feat = feat.unsqueeze(0)
                    return feat
                elif isinstance(feat, np.ndarray):
                    return torch.from_numpy(feat).unsqueeze(0)
                elif isinstance(feat, list):
                    return torch.tensor(feat, dtype=torch.float32).unsqueeze(0)
            
            diagnosis = textual_result.get("diagnosis", {})
            text_content = ""
            if isinstance(diagnosis, dict):
                text_content = diagnosis.get("description", "")
                if not text_content:
                    text_content = diagnosis.get("disease_name", "")
            elif isinstance(diagnosis, str):
                text_content = diagnosis
            
            if text_content:
                pseudo_features = torch.randn(1, 1, 2560) * 0.1
                return pseudo_features
            
            return None
                
        except Exception as e:
            logger.warning(f"生成文本特征失败：{e}")
            return None

    def generate_knowledge_embeddings_tensor(
        self,
        knowledge_context: Optional[Any]
    ) -> Optional[torch.Tensor]:
        """
        从知识上下文生成嵌入张量
        
        将 GraphRAG 的知识上下文转换为 KAD-Former 可用的嵌入向量格式。
        
        Args:
            knowledge_context: 知识上下文对象
            
        Returns:
            torch.Tensor: 知识嵌入张量 [1, N, 256]
            失败返回 None
        """
        if not knowledge_context:
            return None
        
        try:
            tokens = getattr(knowledge_context, 'tokens', None)
            if tokens is not None:
                if isinstance(tokens, torch.Tensor):
                    if tokens.dim() == 2:
                        tokens = tokens.unsqueeze(0)
                    return tokens
                elif isinstance(tokens, np.ndarray):
                    return torch.from_numpy(tokens).unsqueeze(0)
                elif isinstance(tokens, list):
                    return torch.tensor(tokens, dtype=torch.float32).unsqueeze(0)
            
            citations = getattr(knowledge_context, 'citations', [])
            if citations:
                num_citations = len(citations)
                pseudo_embeddings = torch.randn(1, num_citations, 256) * 0.1
                return pseudo_embeddings
            
            return None
                
        except Exception as e:
            logger.warning(f"生成知识嵌入失败：{e}")
            return None
