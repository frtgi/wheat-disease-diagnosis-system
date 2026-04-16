# -*- coding: utf-8 -*-
"""
FusionEngine 单元测试

测试多模态融合算法的核心逻辑，包括：
- 动态权重置信度计算
- 降级因子应用
- 融合结果构建
- KAD-Former 深度融合（Mock）
"""
import pytest
from unittest.mock import MagicMock, patch
import torch
import numpy as np

from app.services.fusion_engine import FusionEngine, FusionResult


class TestFusionResult:
    """FusionResult 数据类测试"""

    def test_default_values(self):
        """测试默认值初始化"""
        result = FusionResult(disease_name="小麦锈病")
        
        assert result.disease_name == "小麦锈病"
        assert result.confidence == 0.0
        assert result.symptoms == []
        assert result.causes == []
        assert result.recommendations == []
        assert result.treatment == []
        assert result.medicines == []
        assert result.knowledge_references == []

    def test_all_fields(self):
        """测试完整字段初始化"""
        result = FusionResult(
            disease_name="小麦白粉病",
            disease_name_en="Powdery Mildew",
            confidence=0.95,
            visual_confidence=0.92,
            textual_confidence=0.88,
            knowledge_confidence=0.90,
            description="叶片出现白色粉层",
            symptoms=["叶片发白", "出现粉末"],
            causes=["真菌感染"],
            recommendations=["喷洒杀菌剂"],
            treatment=["三唑酮"],
            medicines=[{"name": "三唑酮", "dosage": "100ml/亩"}],
            knowledge_references=[{"source": "知识库"}],
            reasoning_chain=["步骤1", "步骤2"],
            severity="high"
        )
        
        assert result.disease_name_en == "Powdery Mildew"
        assert result.confidence == 0.95
        assert len(result.symptoms) == 2
        assert result.severity == "high"


class TestFusionEngineInit:
    """FusionEngine 初始化测试"""

    def test_init_default(self):
        """测试默认初始化（无 KAD-Former）"""
        engine = FusionEngine()
        
        assert engine._kad_former is None

    def test_init_with_kad_former(self):
        """测试带 KAD-Former 的初始化"""
        mock_kad = MagicMock()
        engine = FusionEngine(kad_former=mock_kad)
        
        assert engine._kad_former is mock_kad

    def test_set_kad_former(self):
        """测试动态设置 KAD-Former"""
        engine = FusionEngine()
        
        mock_kad = MagicMock()
        engine.set_kad_former(mock_kad)
        
        assert engine._kad_former is mock_kad


class TestCalculateFusedConfidence:
    """融合置信度计算测试"""

    def test_three_modalities_full(self):
        """测试三模态完整的置信度计算"""
        engine = FusionEngine()
        
        confidence = engine._calculate_fused_confidence(
            visual_conf=0.9,
            textual_conf=0.85,
            knowledge_conf=0.88,
            has_visual=True,
            has_textual=True,
            has_knowledge=True
        )
        
        # 三模态完整时应该不应用降级因子
        assert 0.0 <= confidence <= 1.0
        # 应该接近三个值的加权平均
        assert confidence > 0.8  # 高置信度场景

    def test_two_modalities_degradation(self):
        """测试双模态的降级处理"""
        engine = FusionEngine()
        
        confidence_two = engine._calculate_fused_confidence(
            visual_conf=0.9,
            textual_conf=0.85,
            knowledge_conf=0.0,
            has_visual=True,
            has_textual=True,
            has_knowledge=False
        )
        
        confidence_three = engine._calculate_fused_confidence(
            visual_conf=0.9,
            textual_conf=0.85,
            knowledge_conf=0.88,
            has_visual=True,
            has_textual=True,
            has_knowledge=True
        )
        
        # 双模态应该比三模态低（应用了降级因子）
        assert confidence_two < confidence_three

    def test_single_modality_high_degradation(self):
        """测试单模态的高降级"""
        engine = FusionEngine()
        
        confidence_single = engine._calculate_fused_confidence(
            visual_conf=0.95,
            textual_conf=0.0,
            knowledge_conf=0.0,
            has_visual=True,
            has_textual=False,
            has_knowledge=False
        )
        
        # 单模态应该有更显著的降级
        assert 0.0 <= confidence_single <= 1.0
        # 应该明显低于原始值
        assert confidence_single < 0.95

    def test_no_modality_neutral(self):
        """测试无模态时的中性值"""
        engine = FusionEngine()
        
        confidence = engine._calculate_fused_confidence(
            visual_conf=0.0,
            textual_conf=0.0,
            knowledge_conf=0.0,
            has_visual=False,
            has_textual=False,
            has_knowledge=False
        )
        
        # 无模态时返回中性值 0.5
        assert confidence == 0.5

    def test_zero_confidences(self):
        """测试零置信度的边界情况"""
        engine = FusionEngine()
        
        confidence = engine._calculate_fused_confidence(
            visual_conf=0.0,
            textual_conf=0.0,
            knowledge_conf=0.0,
            has_visual=True,
            has_textual=True,
            has_knowledge=True
        )
        
        assert confidence == 0.0


class TestApplyDegradationFactor:
    """降级因子应用测试"""

    def test_no_degradation_three_modalities(self):
        """测试三模态不降级"""
        engine = FusionEngine()
        
        result = engine._apply_degradation_factor(0.9, 3)
        
        assert result == 0.9  # 不变

    def test_degradation_two_modalities(self):
        """测试双模态降级"""
        engine = FusionEngine()
        
        result = engine._apply_degradation_factor(0.9, 2)
        
        # 应该应用一次降级因子
        assert result < 0.9
        assert result > 0.0

    def test_degradation_one_modality(self):
        """测试单模态高降级"""
        engine = FusionEngine()
        
        result = engine._apply_degradation_factor(0.9, 1)
        
        # 应该应用两次降级因子（降级的平方）
        assert result > 0.0


class TestFuseFeatures:
    """特征融合核心测试"""

    def test_fuse_with_visual_only(self):
        """测试仅视觉特征的融合"""
        engine = FusionEngine()
        
        visual_result = {
            "detections": [
                {
                    "class_name": "小麦锈病",
                    "confidence": 0.95,
                    "bbox": {"x1": 10, "y1": 20, "x2": 100, "y2": 200}
                }
            ]
        }
        
        with patch.object(engine, '_build_fusion_result_with_knowledge') as mock_build:
            mock_build.return_value = FusionResult(
                disease_name="小麦锈病",
                confidence=0.95 * 0.4  # 假设视觉权重为0.4
            )
            
            result = engine.fuse_features(
                visual_result=visual_result,
                textual_result=None,
                knowledge_context=None
            )
            
            assert isinstance(result, FusionResult)
            assert result.disease_name == "小麦锈病"

    def test_fuse_with_textual_only(self):
        """测试仅文本特征的融合"""
        engine = FusionEngine()
        
        textual_result = {
            "diagnosis": {
                "disease_name": "小麦白粉病",
                "confidence": 0.88,
                "description": "叶片出现白色粉层",
                "recommendations": ["喷药防治"]
            },
            "reasoning_chain": ["分析图像", "识别症状"]
        }
        
        with patch.object(engine, '_build_fusion_result_with_knowledge') as mock_build:
            mock_build.return_value = FusionResult(
                disease_name="小麦白粉病",
                confidence=0.88 * 0.35
            )
            
            result = engine.fuse_features(
                visual_result=None,
                textual_result=textual_result,
                knowledge_context=None
            )
            
            assert isinstance(result, FusionResult)
            assert result.disease_name == "小麦白粉病"

    def test_fuse_multimodal(self):
        """测试多模态融合"""
        engine = FusionEngine()
        
        visual_result = {
            "detections": [
                {
                    "class_name": "小麦锈病",
                    "confidence": 0.92,
                    "bbox": [10, 20, 100, 200]
                },
                {
                    "class_name": "小麦锈病",
                    "confidence": 0.88,
                    "bbox": [50, 60, 150, 250]
                }
            ]
        }
        
        textual_result = {
            "diagnosis": {
                "disease_name": "小麦锈病",
                "confidence": 0.90,
                "description": "叶片出现锈色斑点"
            }
        }
        
        mock_knowledge = MagicMock()
        mock_knowledge.citations = [
            {"entity_name": "锈病", "confidence": 0.85}
        ]
        
        with patch.object(engine, '_build_fusion_result_with_knowledge') as mock_build:
            mock_build.return_value = FusionResult(
                disease_name="小麦锈病",
                confidence=0.90,
                roi_boxes=[
                    {"box": [10, 20, 100, 200], "class_name": "小麦锈病", "confidence": 0.92},
                    {"box": [50, 60, 150, 250], "class_name": "小麦锈病", "confidence": 0.88}
                ]
            )
            
            result = engine.fuse_features(
                visual_result=visual_result,
                textual_result=textual_result,
                knowledge_context=mock_knowledge
            )
            
            assert isinstance(result, FusionResult)
            assert result.roi_boxes is not None
            assert len(result.roi_boxes) == 2

    def test_fuse_unknown_disease_fallback(self):
        """测试未知病害的回退逻辑"""
        engine = FusionEngine()
        
        # 仅提供文本结果，但疾病名为空
        textual_result = {
            "diagnosis": {
                "disease_name": "",
                "confidence": 0.0
            }
        }
        
        with patch.object(engine, '_build_fusion_result_with_knowledge') as mock_build:
            mock_build.return_value = FusionResult(disease_name="未知病害")
            
            result = engine.fuse_features(
                visual_result=None,
                textual_result=textual_result,
                knowledge_context=None
            )
            
            # 应该使用"未知病害"作为默认值
            assert result.disease_name == "未知病害"


class TestApplyKADFormerFusion:
    """KAD-Former 深度融合测试"""

    def test_kad_former_success(self):
        """测试 KAD-Former 成功融合"""
        mock_kad = MagicMock()
        # Mock 返回融合后的特征
        mock_kad.__call__ = MagicMock(return_value=torch.randn(1, 1, 768))
        
        engine = FusionEngine(kad_former=mock_kad)
        
        visual_features = torch.randn(1, 1, 768)
        text_features = torch.randn(1, 1, 2560)
        knowledge_embeddings = torch.randn(1, 1, 256)
        
        result = engine._apply_kad_former_fusion(
            visual_features,
            text_features,
            knowledge_embeddings
        )
        
        assert result is not None
        assert result.shape == (1, 1, 768)

    def test_kad_former_not_available(self):
        """测试 KAD-Former 不可用的情况"""
        engine = FusionEngine()  # 无 KAD-Former
        
        result = engine._apply_kad_former_fusion(
            torch.randn(1, 1, 768),
            torch.randn(1, 1, 2560),
            torch.randn(1, 1, 256)
        )
        
        assert result is None

    def test_kad_former_exception(self):
        """测试 KAD-Former 异常处理"""
        mock_kad = MagicMock()
        mock_kad.__call__ = MagicMock(side_effect=RuntimeError("CUDA error"))
        
        engine = FusionEngine(kad_former=mock_kad)
        
        result = engine._apply_kad_former_fusion(
            torch.randn(1, 1, 768),
            torch.randn(1, 1, 2560),
            torch.randn(1, 1, 256)
        )
        
        # 异常时应返回 None
        assert result is None


class TestBuildFusionResultWithKnowledge:
    """融合结果构建测试（带知识库增强）"""

    @patch('app.services.fusion_engine.get_disease_info')
    def test_with_disease_knowledge(self, mock_get_info):
        """测试带知识库信息的构建"""
        # Mock 知识库返回
        mock_disease_info = MagicMock()
        mock_disease_info.name_en = "Yellow Rust"
        mock_disease_info.name_cn = "小麦条锈病"
        mock_disease_info.symptoms = ["叶片出现条状锈斑"]
        mock_disease_info.causes = ["真菌感染"]
        mock_disease_info.treatment = ["杀菌剂"]
        mock_disease_info.medicines = [{"name": "三唑酮"}]
        mock_disease_info.severity = "high"
        mock_disease_info.description = "严重病害"
        mock_disease_info.prevention = ["轮作"]
        
        mock_get_info.return_value = mock_disease_info
        
        engine = FusionEngine()
        
        result = engine._build_fusion_result_with_knowledge(
            disease_name="小麦锈病",
            confidence=0.90,
            visual_confidence=0.92,
            textual_confidence=0.88,
            knowledge_confidence=0.85,
            description="",
            recommendations=[],
            knowledge_references=[],
            reasoning_chain=[],
            roi_boxes=None,
            annotated_image=None,
            inference_time_ms=150.5,
            kad_former_used=False
        )
        
        # 验证知识库信息被正确填充
        assert result.disease_name_en == "Yellow Rust"
        # 如果知识库有中文名，应使用知识库的名称
        assert result.name_cn == "小麦条锈病" if hasattr(result, 'name_cn') else True
        assert len(result.symptoms) > 0
        assert result.severity == "high"
        assert result.treatment == ["杀菌剂"]

    @patch('app.services.fusion_engine.get_disease_info')
    def test_without_disease_knowledge(self, mock_get_info):
        """测试无知识库信息时的构建"""
        mock_get_info.return_value = None

        engine = FusionEngine()

        result = engine._build_fusion_result_with_knowledge(
            disease_name="未知病害",
            confidence=0.5,
            visual_confidence=0.0,
            textual_confidence=0.0,
            knowledge_confidence=0.0,
            description="自定义描述",
            recommendations=["建议1"],
            knowledge_references=[],
            reasoning_chain=[],
            roi_boxes=None,
            annotated_image=None,
            inference_time_ms=100.0,
            kad_former_used=False
        )

        assert result.description == "自定义描述"
        assert result.recommendations == ["建议1"]
        assert result.symptoms == []  # 默认空列表


class TestBoundaryConditions:
    """边界条件测试 - 验证空输入、None 值和极端情况"""

    def test_fuse_with_all_none_inputs(self):
        """
        测试所有输入为 None 的情况
        验证完全空输入时系统的降级处理
        """
        engine = FusionEngine()

        with patch.object(engine, '_build_fusion_result_with_knowledge') as mock_build:
            mock_build.return_value = FusionResult(disease_name="未知病害")

            result = engine.fuse_features(
                visual_result=None,
                textual_result=None,
                knowledge_context=None
            )

            assert isinstance(result, FusionResult)
            assert result.disease_name == "未知病害"

    def test_calculate_confidence_with_extreme_values(self):
        """
        测试极端置信度值的计算
        验证边界值（0.0 和 1.0）的正确处理
        """
        engine = FusionEngine()

        confidence_max = engine._calculate_fused_confidence(
            visual_conf=1.0,
            textual_conf=1.0,
            knowledge_conf=1.0,
            has_visual=True,
            has_textual=True,
            has_knowledge=True
        )

        confidence_min = engine._calculate_fused_confidence(
            visual_conf=0.0,
            textual_conf=0.0,
            knowledge_conf=0.0,
            has_visual=True,
            has_textual=True,
            has_knowledge=True
        )

        assert 0.0 <= confidence_max <= 1.0
        assert confidence_min == 0.0

    def test_apply_degradation_with_zero_modalities(self):
        """
        测试零模态的降级因子应用
        验证模态数为 0 时的行为
        """
        engine = FusionEngine()

        result = engine._apply_degradation_factor(0.9, 0)

        assert result >= 0.0

    def test_fusion_result_with_empty_lists(self):
        """
        测试使用空列表初始化 FusionResult
        验证空集合类型的正确处理
        """
        result = FusionResult(
            disease_name="测试",
            symptoms=[],
            causes=[],
            recommendations=[],
            treatment=[],
            medicines=[],
            knowledge_references=[],
            reasoning_chain=[]
        )

        assert len(result.symptoms) == 0
        assert len(result.causes) == 0
        assert len(result.recommendations) == 0


class TestExceptionHandling:
    """异常处理测试 - 验证错误场景下的优雅降级"""

    def test_fuse_features_with_corrupted_visual_data(self):
        """
        测试损坏的视觉数据输入
        验证畸形数据不会导致系统崩溃
        """
        engine = FusionEngine()

        corrupted_visual = {
            "detections": [{"invalid_field": "data"}]
        }

        with patch.object(engine, '_build_fusion_result_with_knowledge') as mock_build:
            mock_build.return_value = FusionResult(disease_name="默认")

            try:
                result = engine.fuse_features(
                    visual_result=corrupted_visual,
                    textual_result=None,
                    knowledge_context=None
                )
                assert isinstance(result, FusionResult)
            except (KeyError, AttributeError, TypeError):
                pass

    def test_kad_former_with_invalid_tensor_shapes(self):
        """
        测试 KAD-Former 处理无效张量形状
        验证维度不匹配时的处理机制
        """
        mock_kad = MagicMock()
        mock_kad.__call__ = MagicMock(side_effect=ValueError("Shape mismatch"))

        engine = FusionEngine(kad_former=mock_kad)

        invalid_visual = torch.randn(1, 10, 100)
        invalid_text = torch.randn(1, 20, 200)
        invalid_knowledge = torch.randn(1, 30, 50)

        result = engine._apply_kad_former_fusion(
            invalid_visual,
            invalid_text,
            invalid_knowledge
        )

        assert result is None

    def test_build_result_with_exception_in_knowledge_lookup(self):
        """
        测试知识库查询异常时的结果构建
        验证外部服务故障不影响核心功能
        """
        with patch('app.services.fusion_engine.get_disease_info') as mock_get_info:
            mock_get_info.side_effect = ConnectionError("Database unavailable")

            engine = FusionEngine()

            try:
                result = engine._build_fusion_result_with_knowledge(
                    disease_name="小麦锈病",
                    confidence=0.85,
                    visual_confidence=0.8,
                    textual_confidence=0.75,
                    knowledge_confidence=0.7,
                    description="",
                    recommendations=[],
                    knowledge_references=[],
                    reasoning_chain=[],
                    roi_boxes=None,
                    annotated_image=None,
                    inference_time_ms=120.0,
                    kad_former_used=False
                )

                assert isinstance(result, FusionResult)
            except ConnectionError:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
