# -*- coding: utf-8 -*-
"""
多模态融合引擎 (Fusion Engine)

实现 KAD-Former 交叉注意力融合算法，负责：
1. 多模态特征的深度融合
2. 动态权重置信度计算
3. 模态缺失时的降级处理
4. 融合结果构建

核心算法：
- KAD-Former (Knowledge-Aware Dual-modal Transformer)
  使用知识引导的交叉注意力机制融合视觉和文本特征
"""
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import torch

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FusionResult:
    """
    融合诊断结果数据类
    
    存储多模态融合后的完整诊断信息，
    包含来自各模态的置信度和详细诊断内容。
    
    Attributes:
        disease_name: 病害中文名称
        disease_name_en: 病害英文名称
        confidence: 融合后总置信度 [0, 1]
        visual_confidence: 视觉模态置信度
        textual_confidence: 文本模态置信度
        knowledge_confidence: 知识模态置信度
        description: 病害描述
        symptoms: 症状列表
        causes: 病因列表
        recommendations: 预防建议列表
        treatment: 治疗方案列表
        medicines: 用药建议列表
        knowledge_references: 知识引用来源
        reasoning_chain: 推理链（Thinking 模式）
        roi_boxes: ROI 检测框列表
        annotated_image: Base64 编码的标注图像
        inference_time_ms: 推理耗时（毫秒）
        kad_former_used: 是否使用了 KAD-Former 融合
        model_used: 使用的模型标识
        severity: 严重程度 (low/medium/high)
    """
    disease_name: str
    disease_name_en: str = ""
    confidence: float = 0.0
    visual_confidence: float = 0.0
    textual_confidence: float = 0.0
    knowledge_confidence: float = 0.0
    description: str = ""
    symptoms: Optional[List[str]] = None
    causes: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    treatment: Optional[List[str]] = None
    medicines: Optional[List[Dict[str, Any]]] = None
    knowledge_references: Optional[List[Dict[str, Any]]] = None
    reasoning_chain: Optional[List[str]] = None
    roi_boxes: Optional[List[Dict[str, Any]]] = None
    annotated_image: Optional[str] = None
    inference_time_ms: float = 0.0
    kad_former_used: bool = False
    model_used: str = "fusion_engine"
    severity: str = "medium"

    def __post_init__(self) -> None:
        """初始化默认值，将 None 的可选字段设为空列表"""
        if self.symptoms is None:
            self.symptoms = []
        if self.causes is None:
            self.causes = []
        if self.recommendations is None:
            self.recommendations = []
        if self.treatment is None:
            self.treatment = []
        if self.medicines is None:
            self.medicines = []
        if self.knowledge_references is None:
            self.knowledge_references = []


class FusionEngine:
    """
    多模态融合引擎
    
    实现 KAD-Former 知识引导的双模态融合算法，
    支持视觉、文本、知识三种模态的特征融合。
    
    核心功能：
    - KAD-Former 交叉注意力深度融合
    - 动态权重置信度计算
    - 模态缺失时的优雅降级
    - 疫病知识库增强
    
    Attributes:
        kad_former: KAD-Former 模型实例（可选）
    """

    def __init__(self, kad_former: Optional[Any] = None) -> None:
        """
        初始化融合引擎
        
        Args:
            kad_former: KAD-Former 模型实例（可选，不提供则跳过深度融合）
        """
        self._kad_former = kad_former

    def set_kad_former(self, kad_former: Optional[Any]) -> None:
        """
        设置或更新 KAD-Former 模型实例
        
        Args:
            kad_former: KAD-Former 模型实例
        """
        self._kad_former = kad_former

    def fuse_features(
        self,
        visual_result: Optional[Dict[str, Any]],
        textual_result: Optional[Dict[str, Any]],
        knowledge_context: Optional[Any],
        original_image: Optional[Any] = None,
        annotated_image: Optional[str] = None
    ) -> FusionResult:
        """
        执行多模态特征融合（核心方法）
        
        协调各模态特征，执行 KAD-Former 深度融合或传统加权融合，
        并从病害知识库获取完整诊断信息。
        
        Args:
            visual_result: 视觉检测结果（来自 FeatureExtractor）
            textual_result: 文本分析结果（来自 FeatureExtractor）
            knowledge_context: 知识上下文（来自 FeatureExtractor）
            original_image: 原始图像对象（用于生成标注图）
            annotated_image: 预生成的标注图像 Base64 字符串
            
        Returns:
            FusionResult: 完整的融合诊断结果
        """
        start_time = time.time()
        
        # 初始化各字段
        disease_name = "未知病害"
        confidence = 0.0
        visual_confidence = 0.0
        textual_confidence = 0.0
        knowledge_confidence = 0.0
        description = ""
        recommendations = []
        knowledge_references = []
        reasoning_chain = []
        roi_boxes = None
        detections = []
        
        # 处理视觉特征
        if visual_result:
            detections = visual_result.get("detections", [])
            if detections:
                top_detection = max(detections, key=lambda x: x.get("confidence", 0))
                disease_name = top_detection.get("class_name", disease_name)
                visual_confidence = top_detection.get("confidence", 0)
                
                # 构建 ROI 框列表
                roi_boxes = []
                for det in detections:
                    bbox = det.get("bbox") or det.get("box")
                    if bbox:
                        if isinstance(bbox, dict):
                            box = [
                                bbox.get("x1", 0),
                                bbox.get("y1", 0),
                                bbox.get("x2", 0),
                                bbox.get("y2", 0)
                            ]
                        else:
                            box = bbox
                        roi_boxes.append({
                            "box": box,
                            "class_name": det.get("class_name"),
                            "confidence": det.get("confidence")
                        })
        
        # 处理文本特征
        if textual_result:
            diagnosis = textual_result.get("diagnosis", {})
            if diagnosis:
                if disease_name == "未知病害":
                    disease_name = diagnosis.get("disease_name", disease_name)
                textual_confidence = diagnosis.get("confidence", 0.0)
                description = diagnosis.get("description", description)
                recommendations = diagnosis.get("recommendations", recommendations)
                
                # 提取推理链
                raw_reasoning_chain = textual_result.get("reasoning_chain")
                if raw_reasoning_chain:
                    if isinstance(raw_reasoning_chain, list):
                        reasoning_chain = raw_reasoning_chain
                    elif isinstance(raw_reasoning_chain, str):
                        reasoning_chain = [raw_reasoning_chain]
        
        # 处理知识特征
        if knowledge_context:
            citations = getattr(knowledge_context, 'citations', [])
            knowledge_references = [
                {
                    "entity_name": c.get("entity_name"),
                    "relation": c.get("relation"),
                    "tail": c.get("tail"),
                    "source": c.get("source"),
                    "confidence": c.get("confidence", 0.0)
                }
                for c in citations
            ]
            if citations:
                knowledge_confidence = sum(c.get("confidence", 0.0) for c in citations) / len(citations)
        
        # 尝试 KAD-Former 深度融合
        kad_fusion_boost = 0.0
        kad_former_used = False
        
        if self._kad_former is not None and visual_result and textual_result:
            try:
                from .fusion_feature_extractor import FeatureExtractor
                
                feature_extractor = FeatureExtractor()
                visual_features = feature_extractor.generate_visual_features_tensor(visual_result)
                text_features = feature_extractor.generate_text_features_tensor(textual_result)
                knowledge_embeddings = feature_extractor.generate_knowledge_embeddings_tensor(knowledge_context)
                
                if visual_features is not None and text_features is not None and knowledge_embeddings is not None:
                    fused_features = self._apply_kad_former_fusion(
                        visual_features, text_features, knowledge_embeddings
                    )
                    
                    if fused_features is not None:
                        kad_former_used = True
                        confidence_boost = torch.sigmoid(fused_features.mean()).item()
                        kad_fusion_boost = confidence_boost * 0.15
                        logger.info(f"KAD-Former 融合增强: boost={kad_fusion_boost:.4f}")
                    else:
                        logger.debug("KAD-Former 融合返回空结果，使用原始融合逻辑")
                else:
                    missing = []
                    if visual_features is None:
                        missing.append("visual")
                    if text_features is None:
                        missing.append("text")
                    if knowledge_embeddings is None:
                        missing.append("knowledge")
                    logger.debug(f"KAD-Former 跳过: 缺少特征 {missing}")
                    
            except Exception as e:
                logger.warning(f"KAD-Former 融合过程异常: {e}，降级使用原始融合逻辑")
                kad_former_used = False
        
        # 计算最终置信度
        confidence = self._calculate_fused_confidence(
            visual_confidence,
            textual_confidence,
            knowledge_confidence,
            has_visual=visual_result is not None,
            has_textual=textual_result is not None,
            has_knowledge=knowledge_context is not None
        )
        
        # 应用 KAD-Former 增强增益
        if kad_former_used:
            confidence = min(1.0, confidence + kad_fusion_boost)
            logger.info(f"KAD-Former 增强后置信度: {confidence:.4f}")
        
        inference_time_ms = (time.time() - start_time) * 1000
        
        # 从病害知识库获取完整信息
        return self._build_fusion_result_with_knowledge(
            disease_name=disease_name,
            confidence=confidence,
            visual_confidence=visual_confidence,
            textual_confidence=textual_confidence,
            knowledge_confidence=knowledge_confidence,
            description=description,
            recommendations=recommendations,
            knowledge_references=knowledge_references,
            reasoning_chain=reasoning_chain,
            roi_boxes=roi_boxes,
            annotated_image=annotated_image,
            inference_time_ms=inference_time_ms,
            kad_former_used=kad_former_used
        )

    def _apply_kad_former_fusion(
        self,
        visual_features: torch.Tensor,
        text_features: torch.Tensor,
        knowledge_embeddings: torch.Tensor
    ) -> Optional[torch.Tensor]:
        """
        应用 KAD-Former 进行深度融合
        
        使用知识引导的交叉注意力机制融合多模态特征。
        
        Args:
            visual_features: 视觉特征张量 [B, N_v, 768]
            text_features: 文本特征张量 [B, N_t, 2560]
            knowledge_embeddings: 知识嵌入张量 [B, N_k, 256]
            
        Returns:
            torch.Tensor: 融合后的特征张量 [B, N_v, 768]
            失败或模型不可用返回 None
        """
        if self._kad_former is None:
            return None
        
        try:
            with torch.no_grad():
                fused_features = self._kad_former(
                    visual_features=visual_features,
                    text_features=text_features,
                    knowledge_embeddings=knowledge_embeddings
                )
            logger.info("KAD-Former 深度融合成功")
            return fused_features
        except Exception as e:
            logger.warning(f"KAD-Former 融合失败：{e}")
            return None

    def _calculate_fused_confidence(
        self,
        visual_conf: float,
        textual_conf: float,
        knowledge_conf: float,
        has_visual: bool,
        has_textual: bool,
        has_knowledge: bool
    ) -> float:
        """
        计算融合置信度（动态权重策略）
        
        根据可用模态动态调整权重，支持降级场景：
        - 三模态完整：使用配置的权重进行加权平均
        - 双模态：应用降级因子降低置信度
        - 单模态：进一步降低置信度
        - 无模态：返回中性值 0.5
        
        Args:
            visual_conf: 视觉模态置信度 [0, 1]
            textual_conf: 文本模态置信度 [0, 1]
            knowledge_conf: 知识模态置信度 [0, 1]
            has_visual: 是否有视觉模态
            has_textual: 是否有文本模态
            has_knowledge: 是否有知识模态
            
        Returns:
            float: 融合后的置信度 [0, 1]
        """
        base_weights = {
            "visual": settings.FUSION_VISUAL_WEIGHT,
            "textual": settings.FUSION_TEXTUAL_WEIGHT,
            "knowledge": settings.FUSION_KNOWLEDGE_WEIGHT
        }
        
        degradation_factor = settings.FUSION_DEGRADATION_FACTOR
        
        available_modalities = sum([has_visual, has_textual, has_knowledge])
        
        if available_modalities == 0:
            return 0.5
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        if has_visual:
            weighted_confidence += visual_conf * base_weights["visual"]
            total_weight += base_weights["visual"]
        
        if has_textual:
            weighted_confidence += textual_conf * base_weights["textual"]
            total_weight += base_weights["textual"]
        
        if has_knowledge:
            weighted_confidence += knowledge_conf * base_weights["knowledge"]
            total_weight += base_weights["knowledge"]
        
        if total_weight > 0:
            fused_conf = weighted_confidence / total_weight
            apply_degradation = available_modalities < 3
            return fused_conf * (degradation_factor if apply_degradation else 1.0)
        
        return 0.5

    def _apply_degradation_factor(
        self,
        confidence: float,
        available_modalities: int
    ) -> float:
        """
        应用降级因子
        
        当模态不完整时，对置信度应用惩罚因子，
        反映信息不完整性带来的不确定性。
        
        Args:
            confidence: 原始置信度
            available_modalities: 可用模态数量 (1-3)
            
        Returns:
            float: 应用降级后的置信度
        """
        if available_modalities >= 3:
            return confidence
        
        degradation_factor = settings.FUSION_DEGRADATION_FACTOR
        
        if available_modalities == 2:
            return confidence * degradation_factor
        elif available_modalities == 1:
            return confidence * (degradation_factor ** 2)
        else:
            return 0.5

    def _build_fusion_result_with_knowledge(
        self,
        disease_name: str,
        confidence: float,
        visual_confidence: float,
        textual_confidence: float,
        knowledge_confidence: float,
        description: str,
        recommendations: List[str],
        knowledge_references: List[Dict[str, Any]],
        reasoning_chain: List[str],
        roi_boxes: Optional[List[Dict[str, Any]]],
        annotated_image: Optional[str],
        inference_time_ms: float,
        kad_former_used: bool
    ) -> FusionResult:
        """
        构建融合结果（结合病害知识库增强）
        
        从病害知识库获取完整的病害信息，
        补充症状、病因、治疗方案等详细信息。
        
        Args:
            disease_name: 病害名称
            confidence: 融合置信度
            visual_confidence: 视觉置信度
            textual_confidence: 文本置信度
            knowledge_confidence: 知识置信度
            description: 描述文本
            recommendations: 推荐建议
            knowledge_references: 知识引用
            reasoning_chain: 推理链
            roi_boxes: ROI 检测框
            annotated_image: 标注图像
            inference_time_ms: 推理耗时
            kad_former_used: 是否使用 KAD-Former
            
        Returns:
            FusionResult: 完整的融合诊断结果
        """
        try:
            from ..core.disease_knowledge import get_disease_info
            
            disease_info = get_disease_info(disease_name)
            
            # 初始化默认值
            disease_name_en = ""
            symptoms = []
            causes = []
            treatment = []
            medicines = []
            severity = "medium"
            
            if disease_info:
                disease_name_en = disease_info.name_en
                if disease_info.name_cn:
                    disease_name = disease_info.name_cn
                symptoms = disease_info.symptoms
                causes = disease_info.causes
                treatment = disease_info.treatment
                medicines = disease_info.medicines
                severity = disease_info.severity
                
                if not description:
                    description = disease_info.description
                
                if not recommendations:
                    recommendations = disease_info.prevention
                    
        except Exception as e:
            logger.warning(f"获取病害知识库信息失败：{e}，使用默认值")
            disease_name_en = ""
            symptoms = []
            causes = []
            treatment = []
            medicines = []
            severity = "medium"
        
        return FusionResult(
            disease_name=disease_name,
            disease_name_en=disease_name_en,
            confidence=confidence,
            visual_confidence=visual_confidence,
            textual_confidence=textual_confidence,
            knowledge_confidence=knowledge_confidence,
            description=description,
            symptoms=symptoms,
            causes=causes,
            recommendations=recommendations,
            treatment=treatment,
            medicines=medicines,
            knowledge_references=knowledge_references,
            reasoning_chain=reasoning_chain if reasoning_chain else None,
            roi_boxes=roi_boxes,
            annotated_image=annotated_image,
            inference_time_ms=inference_time_ms,
            kad_former_used=kad_former_used,
            severity=severity
        )
