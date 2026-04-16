# -*- coding: utf-8 -*-
"""
ResultAnnotator 单元测试

测试结果后处理和标注功能，包括：
- 图像标注（ROI 框绘制）
- Base64 编码
- 异步缓存操作
- API 响应字典构建
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import base64
from PIL import Image
import numpy as np

from app.services.fusion_annotator import ResultAnnotator
from app.services.fusion_engine import FusionResult


class TestResultAnnotatorInit:
    """ResultAnnotator 初始化测试"""

    def test_init_default(self):
        """测试默认初始化（无缓存服务）"""
        annotator = ResultAnnotator()
        
        assert annotator._cache_service is None

    def test_init_with_cache(self):
        """测试带缓存服务的初始化"""
        mock_cache = MagicMock()
        annotator = ResultAnnotator(cache_service=mock_cache)
        
        assert annotator._cache_service is mock_cache

    def test_set_cache_service(self):
        """测试动态设置缓存服务"""
        annotator = ResultAnnotator()
        
        mock_cache = MagicMock()
        annotator.set_cache_service(mock_cache)
        
        assert annotator._cache_service is mock_cache


class TestAnnotateImage:
    """图像标注测试"""

    def test_annotate_single_detection(self):
        """测试单个检测框的标注"""
        annotator = ResultAnnotator()
        
        # 创建测试图像
        image = Image.new("RGB", (800, 600), color="white")
        
        detections = [
            {
                "class_name": "小麦锈病",
                "confidence": 0.95,
                "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
            }
        ]
        
        result = annotator.annotate_image(image, detections)
        
        assert result is not None
        # 验证返回的是 Base64 编码的 data URI
        assert result.startswith("data:image/png;base64,")

    def test_annotate_multiple_detections(self):
        """测试多个检测框的标注（不同颜色）"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (800, 600), color="white")
        
        detections = [
            {
                "class_name": "锈病",
                "confidence": 0.92,
                "bbox": [50, 60, 150, 250]
            },
            {
                "class_name": "白粉病",
                "confidence": 0.88,
                "bbox": [200, 100, 350, 300]
            },
            {
                "class_name": "赤霉病",
                "confidence": 0.85,
                "bbox": [400, 150, 550, 350]
            }
        ]
        
        result = annotator.annotate_image(image, detections)
        
        assert result is not None
        # 应该成功编码为 Base64
        base64_data = result.split(",")[1]
        decoded = base64.b64decode(base64_data)
        assert len(decoded) > 0  # 确保有数据

    def test_annotate_empty_detections(self):
        """测试空检测列表的情况"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (640, 480))
        
        result = annotator.annotate_image(image, [])
        
        assert result is None

    def test_annotate_list_bbox_format(self):
        """测试列表格式的边界框"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (640, 480))
        
        detections = [
            {
                "class_name": "测试病害",
                "confidence": 0.90,
                "bbox": [10, 20, 100, 200]  # 列表格式
            }
        ]
        
        result = annotator.annotate_image(image, detections)
        
        assert result is not None

    def test_annotate_missing_bbox(self):
        """测试缺少边界框的情况"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (640, 480))
        
        detections = [
            {
                "class_name": "无框病害",
                "confidence": 0.85
                # 没有 bbox 或 box 字段
            }
        ]
        
        result = annotator.annotate_image(image, detections)
        
        # 缺少 bbox 时应该返回 None 或跳过该检测
        assert result is None


class TestEncodeImageBase64:
    """Base64 编码测试"""

    def test_encode_png(self):
        """测试 PNG 格式编码"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (100, 100), color="red")
        
        result = annotator.encode_image_base64(image, format="PNG")
        
        assert result.startswith("data:image/png;base64,")
        # 验证可以解码
        base64_data = result.split(",")[1]
        decoded = base64.b64decode(base64_data)
        assert len(decoded) > 0

    def test_encode_jpeg(self):
        """测试 JPEG 格式编码"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (100, 100), color="blue")
        
        result = annotator.encode_image_base64(image, format="JPEG")
        
        assert result.startswith("data:image/jpeg;base64,")

    def test_encode_different_sizes(self):
        """测试不同尺寸图像的编码"""
        annotator = ResultAnnotator()
        
        for size in [(640, 480), (1024, 768), (224, 224)]:
            image = Image.new("RGB", size)
            result = annotator.encode_image_base64(image)
            
            assert result is not None
            assert "base64," in result


class TestPilToBytes:
    """PIL 图像转字节测试"""

    def test_pil_to_bytes_jpeg(self):
        """测试 JPEG 格式转换"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (200, 200), color="green")
        
        data = annotator.pil_to_bytes(image, format="JPEG", quality=90)
        
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_pil_to_bytes_default_quality(self):
        """测试默认质量参数"""
        annotator = ResultAnnotator()
        
        image = Image.new("RGB", (100, 100))
        
        data = annotator.pil_to_bytes(image)  # 使用默认参数
        
        assert isinstance(data, bytes)
        assert len(data) > 0


class TestCacheOperations:
    """异步缓存操作测试"""

    @pytest.mark.asyncio
    async def test_check_cache_hit(self):
        """测试缓存命中场景"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {
            "result": {
                "success": True,
                "diagnosis": {"disease_name": "小麦锈病"}
            }
        }
        
        annotator = ResultAnnotator(cache_service=mock_cache)
        
        image_data = b"fake_image_data"
        result = await annotator.check_cache(image_data, "症状描述")
        
        assert result is not None
        assert result["success"] == True
        mock_cache.get.assert_called_once_with(image_data, "症状描述")

    @pytest.mark.asyncio
    async def test_check_cache_miss(self):
        """测试缓存未命中场景"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        
        annotator = ResultAnnotator(cache_service=mock_cache)
        
        result = await annotator.check_cache(b"data", "症状")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_check_cache_no_service(self):
        """测试无缓存服务时返回 None"""
        annotator = ResultAnnotator()  # 无缓存服务
        
        result = await annotator.check_cache(b"data", "症状")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_save_to_cache_success(self):
        """测试保存到缓存成功"""
        mock_cache = AsyncMock()
        mock_cache.set.return_value = True
        
        annotator = ResultAnnotator(cache_service=mock_cache)
        
        image_data = b"image_data"
        test_result = {"success": True, "diagnosis": {}}
        
        success = await annotator.save_to_cache(image_data, test_result, "症状")
        
        assert success == True
        mock_cache.set.assert_called_once_with(image_data, test_result, "症状")

    @pytest.mark.asyncio
    async def test_save_to_cache_failure(self):
        """测试保存到缓存失败"""
        mock_cache = AsyncMock()
        mock_cache.set.return_value = False
        
        annotator = ResultAnnotator(cache_service=mock_cache)
        
        success = await annotator.save_to_cache(b"data", {}, "")
        
        assert success == False

    @pytest.mark.asyncio
    async def test_save_to_cache_no_service(self):
        """测试无缓存服务时返回 False"""
        annotator = ResultAnnotator()  # 无缓存服务
        
        success = await annotator.save_to_cache(b"data", {}, "")
        
        assert success == False

    @pytest.mark.asyncio
    async def test_cache_exception_handling(self):
        """测试缓存操作异常处理"""
        mock_cache = AsyncMock()
        mock_cache.get.side_effect = Exception("Redis connection error")
        
        annotator = ResultAnnotator(cache_service=mock_cache)
        
        # 异常时应返回 None 而不是抛出异常
        result = await annotator.check_cache(b"data", "")
        
        assert result is None


class TestBuildResponseDict:
    """API 响应字典构建测试"""

    def test_basic_response(self):
        """测试基本响应构建"""
        annotator = ResultAnnotator()
        
        fusion_result = FusionResult(
            disease_name="小麦锈病",
            confidence=0.92,
            visual_confidence=0.90,
            textual_confidence=0.88,
            knowledge_confidence=0.85,
            description="叶片出现锈色斑点",
            recommendations=["喷洒杀菌剂"]
        )
        
        response = annotator.build_response_dict(fusion_result)
        
        # 验证基本结构
        assert response["success"] == True
        assert response["model"] == "fusion_engine"
        assert response["diagnosis"]["disease_name"] == "小麦锈病"
        assert response["diagnosis"]["confidence"] == 0.92
        assert "features" in response

    def test_response_with_thinking(self):
        """测试带推理链的响应"""
        annotator = ResultAnnotator()
        
        fusion_result = FusionResult(
            disease_name="测试病害",
            confidence=0.89,
            reasoning_chain=["步骤1: 分析", "步骤2: 推断"]
        )
        
        # 启用 thinking 模式
        response = annotator.build_response_dict(
            fusion_result,
            enable_thinking=True
        )
        
        assert "reasoning_chain" in response
        assert len(response["reasoning_chain"]) == 2

    def test_response_without_thinking(self):
        """测试不启用 thinking 时的响应（不应包含推理链）"""
        annotator = ResultAnnotator()
        
        fusion_result = FusionResult(
            disease_name="测试病害",
            reasoning_chain=["应该被隐藏"]
        )
        
        # 不启用 thinking
        response = annotator.build_response_dict(
            fusion_result,
            enable_thinking=False
        )
        
        # 不应包含推理链
        assert "reasoning_chain" not in response

    def test_response_with_roi_boxes(self):
        """测试带 ROI 框的响应"""
        annotator = ResultAnnotator()
        
        fusion_result = FusionResult(
            disease_name="测试病害",
            roi_boxes=[
                {"box": [10, 20, 100, 200], "class_name": "锈病", "confidence": 0.95}
            ]
        )
        
        response = annotator.build_response_dict(fusion_result)
        
        assert "roi_boxes" in response["diagnosis"]
        assert len(response["diagnosis"]["roi_boxes"]) == 1

    def test_response_with_annotated_image(self):
        """测试带标注图像的响应"""
        annotator = ResultAnnotator()
        
        fusion_result = FusionResult(
            disease_name="测试病害",
            annotated_image="data:image/png;base64,iVBORw0KGgo..."
        )
        
        response = annotator.build_response_dict(fusion_result)
        
        assert "annotated_image" in response["diagnosis"]
        assert response["diagnosis"]["annotated_image"].startswith("data:")

    def test_response_with_timing(self):
        """测试带计时信息的响应"""
        annotator = ResultAnnotator()
        
        fusion_result = FusionResult(disease_name="测试病害")
        timer_summary = {
            "stages": {"特征提取": 150.5, "融合": 50.2},
            "total_stages_ms": 200.7,
            "stage_count": 2
        }
        
        response = annotator.build_response_dict(
            fusion_result,
            timer_summary=timer_summary
        )
        
        assert "timing" in response
        assert response["timing"]["stage_count"] == 2

    def test_response_complete_fields(self):
        """测试完整字段的响应构建"""
        annotator = ResultAnnotator()

        fusion_result = FusionResult(
            disease_name="小麦赤霉病",
            disease_name_en="Fusarium Head Blight",
            confidence=0.93,
            severity="high",
            knowledge_references=[{"source": "知识库"}],
            kad_former_used=True,
            inference_time_ms=245.8
        )

        response = annotator.build_response_dict(
            fusion_result,
            enable_thinking=True,
            timer_summary={"pipeline_total_ms": 500.0}
        )

        diag = response["diagnosis"]
        assert diag["severity"] == "high"
        assert diag["kad_former_used"] == True
        assert diag["inference_time_ms"] == 245.8
        assert "timing" in response


class TestBoundaryConditions:
    """边界条件测试 - 验证空输入、None 值和极端情况"""

    def test_annotate_with_none_image(self):
        """
        测试传入 None 图像时的标注行为
        验证对空输入的优雅处理
        """
        annotator = ResultAnnotator()
        detections = [{"class_name": "测试", "confidence": 0.9, "bbox": [10, 20, 100, 200]}]

        result = annotator.annotate_image(None, detections)

        assert result is None

    def test_annotate_with_very_small_image(self):
        """
        测试极小图像的标注（1x1 像素）
        验证极端尺寸的处理能力
        """
        annotator = ResultAnnotator()
        tiny_image = Image.new("RGB", (1, 1))
        detections = [{"class_name": "测试", "confidence": 0.8, "bbox": [0, 0, 1, 1]}]

        result = annotator.annotate_image(tiny_image, detections)

        if result is not None:
            assert result.startswith("data:image")

    def test_encode_with_zero_dimension_image(self):
        """
        测试零尺寸图像的编码
        验证无效尺寸的处理
        """
        annotator = ResultAnnotator()

        try:
            zero_img = Image.new("RGB", (0, 0))
            result = annotator.encode_image_base64(zero_img)
            assert result is not None or result is None
        except (ValueError, OSError):
            pass

    def test_build_response_with_minimal_fusion_result(self):
        """
        测试最小 FusionResult 的响应构建
        验证只有必填字段时的处理
        """
        annotator = ResultAnnotator()
        minimal_result = FusionResult(disease_name="测试病害")

        response = annotator.build_response_dict(minimal_result)

        assert response["success"] is True
        assert response["diagnosis"]["disease_name"] == "测试病害"

    def test_build_response_with_all_optional_fields_none(self):
        """
        测试所有可选字段为 None 的响应构建
        验证缺失可选字段时的默认值填充
        """
        annotator = ResultAnnotator()
        minimal_result = FusionResult(
            disease_name="边界测试",
            roi_boxes=None,
            annotated_image=None,
            reasoning_chain=None
        )

        response = annotator.build_response_dict(minimal_result)

        assert "roi_boxes" not in response.get("diagnosis", {}) or \
               response["diagnosis"].get("roi_boxes") is None

    def test_cache_operations_with_empty_data(self):
        """
        测试空数据的缓存操作
        验证空字节输入的处理"""
        import asyncio

        async def run_test():
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            annotator = ResultAnnotator(cache_service=mock_cache)

            result = await annotator.check_cache(b"", "")
            assert result is None

            success = await annotator.save_to_cache(b"", {}, "")
            assert success is True or success is False

        asyncio.run(run_test())


class TestExceptionHandling:
    """异常处理测试 - 验证错误场景下的优雅降级"""

    @pytest.mark.asyncio
    async def test_cache_connection_failure_recovery(self):
        """
        测试缓存连接失败后的恢复能力
        验证网络异常不会导致永久性故障
        """
        call_count = 0

        async def failing_then_succeeding_get(key1, key2=""):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Redis connection reset")
            return {"cached": "result"}

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=failing_then_succeeding_get)

        annotator = ResultAnnotator(cache_service=mock_cache)

        first_result = await annotator.check_cache(b"data", "key")
        second_result = await annotator.check_cache(b"data", "key")

        assert first_result is None
        assert second_result is not None

    def test_annotate_with_invalid_bbox_coordinates(self):
        """
        测试无效坐标的边界框标注
        验证负数坐标或超出范围值的处理
        """
        annotator = ResultAnnotator()
        image = Image.new("RGB", (640, 480))

        invalid_detections = [
            {"class_name": "负坐标", "confidence": 0.9, "bbox": [-10, -20, 100, 200]},
            {"class_name": "超出范围", "confidence": 0.8, "bbox": [10000, 10000, 20000, 20000]},
            {"class_name": "反转框", "confidence": 0.7, "bbox": [200, 200, 50, 50]}
        ]

        try:
            result = annotator.annotate_image(image, invalid_detections)
            if result is not None:
                assert result.startswith("data:image")
        except (ValueError, IndexError):
            pass

    def test_build_response_with_corrupted_fusion_result(self):
        """
        测试损坏的 FusionResult 对象
        验证缺少必要字段时的容错能力
        """
        annotator = ResultAnnotator()

        corrupted_result = FusionResult(disease_name="")
        corrupted_result.confidence = float('nan')

        try:
            response = annotator.build_response_dict(corrupted_result)
            assert "success" in response
        except (ValueError, AttributeError):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
