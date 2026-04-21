# -*- coding: utf-8 -*-
"""
结果标注器 (Result Annotator)

负责融合诊断结果的后处理和可视化：
1. ROI 检测框标注图像生成
2. 图像 Base64 编码
3. 推理结果缓存写入（异步）
4. API 响应字典构建

提供统一的结果处理接口，支持同步和异步两种模式。
"""
import logging
import base64
import io
from typing import Dict, List, Optional, Any
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class ResultAnnotator:
    """
    结果标注器
    
    处理融合诊断结果的可视化和存储：
    - 在原图上绘制检测框和标签
    - 将标注图像编码为 Base64 格式
    - 异步写入推理缓存
    - 构建标准化的 API 响应字典
    
    Attributes:
        cache_service: 推理缓存服务实例（可选）
    """

    def __init__(self, cache_service: Optional[Any] = None) -> None:
        """
        初始化结果标注器
        
        Args:
            cache_service: 推理缓存服务实例（可选，不提供则禁用缓存功能）
        """
        self._cache_service = cache_service

    def set_cache_service(self, cache_service: Optional[Any]) -> None:
        """
        设置或更新缓存服务实例
        
        Args:
            cache_service: 缓存服务实例
        """
        self._cache_service = cache_service

    def annotate_image(
        self,
        image: Image.Image,
        detections: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        在图像上标注检测框和标签
        
        在原始图像上绘制彩色边界框、类别名称和置信度标签，
        支持多个检测目标的不同颜色区分。
        
        Args:
            image: 原始 PIL 图像对象
            detections: 检测结果列表，每个元素包含：
                - bbox/box: 边界框坐标 [x1, y1, x2, y2] 或 {"x1":..., "y1":..., ...}
                - class_name: 类别名称
                - confidence: 置信度 [0, 1]
                
        Returns:
            str: Base64 编码的标注图像字符串（data:image/png;base64,...格式）
            失败或无检测结果返回 None
        """
        if not detections:
            return None
        
        try:
            annotated = image.copy()
            draw = ImageDraw.Draw(annotated)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                try:
                    font = ImageFont.load_default()
                except Exception:
                    font = None
            
            # 定义颜色列表（循环使用）
            colors = [
                (255, 0, 0),      # 红
                (0, 255, 0),      # 绿
                (0, 0, 255),      # 蓝
                (255, 255, 0),    # 黄
                (255, 0, 255),    # 品红
                (0, 255, 255)     # 青
            ]
            
            for idx, detection in enumerate(detections):
                bbox = detection.get("bbox") or detection.get("box")
                if not bbox:
                    continue
                
                # 解析边界框坐标
                if isinstance(bbox, dict):
                    x1 = int(bbox.get("x1", 0))
                    y1 = int(bbox.get("y1", 0))
                    x2 = int(bbox.get("x2", 0))
                    y2 = int(bbox.get("y2", 0))
                elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
                else:
                    continue
                
                # 获取类别和置信度
                class_name = detection.get("class_name", "未知")
                confidence = detection.get("confidence", 0.0)
                
                # 选择颜色
                color = colors[idx % len(colors)]
                
                # 绘制边界框
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                # 构建标签文本
                label = f"{class_name} {confidence:.2f}"
                
                # 计算文本背景框
                if font:
                    try:
                        bbox_text = draw.textbbox((x1, y1), label, font=font)
                    except Exception:
                        bbox_text = (x1, y1, x1 + 100, y1 + 20)
                else:
                    bbox_text = (x1, y1, x1 + 100, y1 + 20)
                
                # 绘制背景和文本
                draw.rectangle(bbox_text, fill=color)
                
                if font:
                    draw.text((x1, y1), label, fill=(255, 255, 255), font=font)
                else:
                    draw.text((x1, y1), label, fill=(255, 255, 255))
            
            # 编码为 Base64
            return self.encode_image_base64(annotated)
            
        except Exception as e:
            logger.error(f"图像标注失败：{e}")
            return None

    def encode_image_base64(self, image: Image.Image, format: str = "PNG") -> str:
        """
        将 PIL 图像编码为 Base64 字符串
        
        将图像对象转换为 Base64 编码的 data URI 字符串，
        可直接用于 HTML img 标签或 JSON 响应。
        
        Args:
            image: PIL 图像对象
            format: 图像格式（PNG/JPEG 等），默认 PNG
            
        Returns:
            str: Base64 编码的 data URI 字符串（data:image/<format>;base64,...）
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return f"data:image/{format.lower()};base64,{base64_str}"

    def pil_to_bytes(self, image: Image.Image, format: str = "JPEG", quality: int = 85) -> bytes:
        """
        将 PIL Image 转换为字节数据
        
        优化版本：使用 JPEG 格式减少数据量，
        可配置质量和优化级别。
        
        Args:
            image: PIL Image 对象
            format: 图像格式（JPEG/PNG），默认 JPEG
            quality: JPEG 质量 (1-100)，默认 85
            
        Returns:
            bytes: 图像二进制数据
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format, quality=quality, optimize=True)
        return buffer.getvalue()

    async def check_cache(
        self,
        image_data: bytes,
        symptoms: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        异步检查缓存中是否存在诊断结果
        
        根据图像数据和症状查询缓存，
        命中则返回缓存的诊断结果。
        
        Args:
            image_data: 图像二进制数据
            symptoms: 症状描述文本
            
        Returns:
            Dict: 缓存的诊断结果字典
            未命中或缓存不可用返回 None
        """
        if not self._cache_service:
            return None
        
        try:
            cached = await self._cache_service.get(image_data, symptoms)
            if cached and "result" in cached:
                return cached["result"]
            return cached
        except Exception as e:
            logger.error(f"缓存检查异常: {e}")
            return None

    async def save_to_cache(
        self,
        image_data: bytes,
        result: Dict[str, Any],
        symptoms: str = ""
    ) -> bool:
        """
        异步保存诊断结果到缓存
        
        将完整的诊断结果写入 Redis 缓存，
        支持后续的快速查询。
        
        Args:
            image_data: 图像二进制数据（作为缓存键的一部分）
            result: 完整的诊断结果字典
            symptoms: 症状描述文本（作为缓存键的一部分）
            
        Returns:
            bool: 是否保存成功
        """
        if not self._cache_service:
            return False
        
        try:
            success = await self._cache_service.set(image_data, result, symptoms)
            if success:
                logger.info("诊断结果已保存到缓存")
            return success
        except Exception as e:
            logger.error(f"保存缓存异常: {e}")
            return False

    def build_response_dict(
        self,
        fusion_result: Any,
        enable_thinking: bool = False,
        timer_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建 API 响应字典
        
        将 FusionResult 对象转换为标准化的 API 响应格式，
        包含诊断信息、特征标记、计时数据等。
        
        Args:
            fusion_result: FusionResult 融合结果对象
            enable_thinking: 是否包含推理链
            timer_summary: PipelineTimer 计时摘要（可选）
            
        Returns:
            Dict: 标准 API 响应字典，包含以下字段：
                - success: 是否成功
                - diagnosis: 诊断信息字典
                - model: 模型标识
                - features: 特征提取标记
                - reasoning_chain: 推理链（如果启用）
                - timing: 计时信息（如果提供）
        """
        
        response = {
            "success": True,
            "diagnosis": {
                "disease_name": fusion_result.disease_name,
                "confidence": fusion_result.confidence,
                "visual_confidence": fusion_result.visual_confidence,
                "textual_confidence": fusion_result.textual_confidence,
                "knowledge_confidence": fusion_result.knowledge_confidence,
                "description": fusion_result.description,
                "recommendations": fusion_result.recommendations,
                "knowledge_references": fusion_result.knowledge_references,
                "kad_former_used": fusion_result.kad_former_used,
                "inference_time_ms": fusion_result.inference_time_ms,
                "severity": fusion_result.severity
            },
            "model": fusion_result.model_used,
            "features": {}
        }
        
        # 添加可选字段
        if enable_thinking and fusion_result.reasoning_chain:
            response["reasoning_chain"] = fusion_result.reasoning_chain
        
        if fusion_result.roi_boxes:
            response["diagnosis"]["roi_boxes"] = fusion_result.roi_boxes
        
        if fusion_result.annotated_image:
            response["diagnosis"]["annotated_image"] = fusion_result.annotated_image
        
        # 添加计时信息
        if timer_summary:
            response["timing"] = timer_summary
        
        return response
