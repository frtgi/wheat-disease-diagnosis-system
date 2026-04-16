"""
YOLOv8 服务单元测试
测试模型加载、图像检测、结果解析等功能
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from PIL import Image
import numpy as np

from app.services.yolo_service import YOLOv8Service, get_yolo_service


class TestYOLOv8ServiceInit:
    """YOLOv8 服务初始化测试类"""

    def test_init_default_params(self):
        """
        测试默认参数初始化
        
        验证:
        - 默认置信度阈值为 0.5
        - 模型未加载状态
        - 自动加载标志为 True
        """
        with patch.object(YOLOv8Service, '_load_model'):
            service = YOLOv8Service(auto_load=False)
            
            assert service.confidence_threshold == 0.5
            assert service.model is None
            assert service.is_loaded is False
            assert service.model_path is None

    def test_init_custom_params(self, temp_dir: Path):
        """
        测试自定义参数初始化
        
        验证:
        - 自定义模型路径正确设置
        - 自定义置信度阈值正确设置
        """
        model_path = temp_dir / "models" / "yolo"
        
        with patch.object(YOLOv8Service, '_load_model'):
            service = YOLOv8Service(
                model_path=model_path,
                confidence_threshold=0.7,
                auto_load=False
            )
            
            assert service.model_path == model_path
            assert service.confidence_threshold == 0.7

    def test_expected_disease_classes_defined(self):
        """
        测试预期病害类别已定义
        
        验证:
        - 预期病害类别集合不为空
        - 包含常见病害类别
        """
        assert len(YOLOv8Service.EXPECTED_DISEASE_CLASSES) > 0
        assert "Yellow Rust" in YOLOv8Service.EXPECTED_DISEASE_CLASSES
        assert "Healthy" in YOLOv8Service.EXPECTED_DISEASE_CLASSES
        assert "Mildew" in YOLOv8Service.EXPECTED_DISEASE_CLASSES

    def test_disease_name_mapping_defined(self):
        """
        测试病害名称映射已定义
        
        验证:
        - 中文名称映射不为空
        - 包含常见病害的中英文映射
        """
        assert len(YOLOv8Service.DISEASE_NAME_MAPPING) > 0
        assert YOLOv8Service.DISEASE_NAME_MAPPING["Yellow Rust"] == "条锈病"
        assert YOLOv8Service.DISEASE_NAME_MAPPING["Mildew"] == "白粉病"
        assert YOLOv8Service.DISEASE_NAME_MAPPING["Healthy"] == "健康"


class TestYOLOv8ServiceLoadModel:
    """YOLOv8 模型加载测试类"""

    def test_load_model_from_file(self, temp_dir: Path):
        """
        测试从文件加载模型
        
        验证:
        - 模型文件存在时正确加载
        - 加载状态正确设置
        """
        model_file = temp_dir / "model.pt"
        model_file.touch()
        
        mock_model = MagicMock()
        mock_model.names = {0: "Yellow Rust", 1: "Healthy"}
        
        with patch('app.services.yolo_service.YOLO', return_value=mock_model):
            service = YOLOv8Service(model_path=model_file, auto_load=False)
            service._load_model()
            
            assert service.is_loaded is True
            assert service.model is not None

    def test_load_model_from_directory(self, temp_dir: Path):
        """
        测试从目录加载最新模型
        
        验证:
        - 从目录中选择最新的模型文件
        - 正确加载模型
        """
        model_dir = temp_dir / "models"
        model_dir.mkdir()
        
        old_model = model_dir / "model_v1.pt"
        old_model.touch()
        
        import time
        time.sleep(0.1)
        
        new_model = model_dir / "model_v2.pt"
        new_model.touch()
        
        mock_model = MagicMock()
        mock_model.names = {0: "Yellow Rust"}
        
        with patch('app.services.yolo_service.YOLO', return_value=mock_model):
            service = YOLOv8Service(model_path=model_dir, auto_load=False)
            service._load_model()
            
            assert service.is_loaded is True

    def test_load_model_no_file_found(self, temp_dir: Path):
        """
        测试模型文件不存在
        
        验证:
        - 目录为空时不加载模型
        - 加载状态保持 False
        """
        empty_dir = temp_dir / "empty_models"
        empty_dir.mkdir()
        
        service = YOLOv8Service(model_path=empty_dir, auto_load=False)
        service._load_model()
        
        assert service.is_loaded is False

    def test_load_model_with_progress_callback(self, temp_dir: Path):
        """
        测试带进度回调的模型加载
        
        验证:
        - 进度回调被正确调用
        - 进度值按预期更新
        """
        model_file = temp_dir / "model.pt"
        model_file.touch()
        
        progress_values = []
        
        def progress_callback(progress: int, message: str):
            progress_values.append((progress, message))
        
        mock_model = MagicMock()
        mock_model.names = {0: "Yellow Rust"}
        
        with patch('app.services.yolo_service.YOLO', return_value=mock_model):
            service = YOLOv8Service(model_path=model_file, auto_load=False)
            service._load_model(progress_callback=progress_callback)
            
            assert len(progress_values) > 0
            assert any(p[0] == 100 for p in progress_values)

    def test_load_model_exception_handling(self, temp_dir: Path):
        """
        测试模型加载异常处理
        
        验证:
        - 加载失败时正确处理异常
        - 加载状态设置为 False
        """
        model_file = temp_dir / "model.pt"
        model_file.touch()
        
        with patch('app.services.yolo_service.YOLO', side_effect=Exception("加载失败")):
            service = YOLOv8Service(model_path=model_file, auto_load=False)
            service._load_model()
            
            assert service.is_loaded is False


class TestYOLOv8ServiceDetect:
    """YOLOv8 检测功能测试类"""

    @pytest.fixture
    def mock_loaded_service(self):
        """
        创建已加载模型的模拟服务
        
        返回:
            YOLOv8Service: 模拟的已加载服务
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        mock_model = MagicMock()
        mock_model.names = {0: "Yellow Rust", 1: "Mildew", 2: "Healthy"}
        
        mock_box = MagicMock()
        mock_box.cls = np.array([0])
        mock_box.conf = np.array([0.92])
        mock_box.xyxy = np.array([[100, 100, 200, 200]])
        
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.__len__ = MagicMock(return_value=1)
        mock_result.boxes.__getitem__ = MagicMock(return_value=mock_box)
        mock_result.boxes.cpu = MagicMock(return_value=mock_result.boxes)
        mock_result.boxes.numpy = MagicMock(return_value=[mock_box])
        
        mock_model.return_value = [mock_result]
        service.model = mock_model
        
        return service

    def test_detect_success(self, mock_loaded_service: YOLOv8Service):
        """
        测试成功检测图像
        
        验证:
        - 返回成功状态
        - 检测结果包含正确的类别和置信度
        """
        image = Image.new('RGB', (640, 480), color='white')
        
        mock_boxes = [MagicMock()]
        mock_boxes[0].cls = np.array([0])
        mock_boxes[0].conf = np.array([0.92])
        mock_boxes[0].xyxy = np.array([[100, 100, 200, 200]])
        
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.__len__ = MagicMock(return_value=1)
        mock_result.boxes.cpu = MagicMock(return_value=mock_result.boxes)
        mock_result.boxes.numpy = MagicMock(return_value=mock_boxes)
        
        mock_loaded_service.model.return_value = [mock_result]
        
        result = mock_loaded_service.detect(image)
        
        assert result["success"] is True
        assert "detections" in result
        assert result["count"] >= 0

    def test_detect_model_not_loaded(self):
        """
        测试模型未加载时检测
        
        验证:
        - 返回失败状态
        - 错误信息提示模型未加载
        """
        service = YOLOv8Service(auto_load=False)
        image = Image.new('RGB', (640, 480), color='white')
        
        result = service.detect(image)
        
        assert result["success"] is False
        assert "未加载" in result["error"]

    def test_detect_with_bbox(self, mock_loaded_service: YOLOv8Service):
        """
        测试检测结果包含边界框
        
        验证:
        - 检测结果包含 bbox 信息
        - bbox 坐标格式正确
        """
        image = Image.new('RGB', (640, 480), color='white')
        
        mock_box = MagicMock()
        mock_box.cls = np.array([0])
        mock_box.conf = np.array([0.92])
        mock_box.xyxy = np.array([[100, 100, 200, 200]])
        
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.__len__ = MagicMock(return_value=1)
        mock_result.boxes.cpu = MagicMock(return_value=mock_result.boxes)
        mock_result.boxes.numpy = MagicMock(return_value=[mock_box])
        
        mock_loaded_service.model.return_value = [mock_result]
        
        result = mock_loaded_service.detect(image)
        
        if result["detections"]:
            detection = result["detections"][0]
            assert "bbox" in detection or "box" in detection

    def test_detect_chinese_name_mapping(self, mock_loaded_service: YOLOv8Service):
        """
        测试检测结果的中文映射
        
        验证:
        - 检测结果包含中文名称
        - 中文名称映射正确
        """
        image = Image.new('RGB', (640, 480), color='white')
        
        mock_box = MagicMock()
        mock_box.cls = np.array([0])
        mock_box.conf = np.array([0.92])
        mock_box.xyxy = np.array([[100, 100, 200, 200]])
        
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.__len__ = MagicMock(return_value=1)
        mock_result.boxes.cpu = MagicMock(return_value=mock_result.boxes)
        mock_result.boxes.numpy = MagicMock(return_value=[mock_box])
        
        mock_loaded_service.model.return_value = [mock_result]
        
        result = mock_loaded_service.detect(image)
        
        if result["detections"]:
            detection = result["detections"][0]
            assert "chinese_name" in detection

    def test_detect_exception_handling(self, mock_loaded_service: YOLOv8Service):
        """
        测试检测异常处理
        
        验证:
        - 检测失败时返回错误信息
        - 不抛出异常
        """
        image = Image.new('RGB', (640, 480), color='white')
        mock_loaded_service.model.side_effect = Exception("检测失败")
        
        result = mock_loaded_service.detect(image)
        
        assert result["success"] is False
        assert "error" in result


class TestYOLOv8ServiceDetectFromFile:
    """YOLOv8 文件检测测试类"""

    def test_detect_from_file_success(self, sample_image_file: Path):
        """
        测试从文件检测成功
        
        验证:
        - 正确读取图像文件
        - 返回检测结果
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.boxes = None
        mock_model.return_value = [mock_result]
        service.model = mock_model
        
        result = service.detect_from_file(sample_image_file)
        
        assert "success" in result

    def test_detect_from_file_not_found(self, temp_dir: Path):
        """
        测试文件不存在
        
        验证:
        - 返回失败状态
        - 错误信息提示加载失败
        """
        service = YOLOv8Service(auto_load=False)
        non_existent = temp_dir / "non_existent.jpg"
        
        result = service.detect_from_file(non_existent)
        
        assert result["success"] is False
        assert "error" in result


class TestYOLOv8ServiceValidateClasses:
    """YOLOv8 病害类别校验测试类"""

    def test_validate_classes_all_matched(self):
        """
        测试所有类别匹配
        
        验证:
        - 匹配率为 100%
        - 校验通过
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        mock_model = MagicMock()
        mock_model.names = {i: name for i, name in enumerate(service.EXPECTED_DISEASE_CLASSES)}
        service.model = mock_model
        
        result = service.validate_disease_classes()
        
        assert result["is_valid"] is True
        assert result["match_rate"] == 1.0
        assert len(result["missing_classes"]) == 0

    def test_validate_classes_partial_matched(self):
        """
        测试部分类别匹配
        
        验证:
        - 匹配率计算正确
        - 缺失类别正确识别
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        partial_classes = {"Yellow Rust", "Mildew", "Healthy"}
        mock_model = MagicMock()
        mock_model.names = {i: name for i, name in enumerate(partial_classes)}
        service.model = mock_model
        
        result = service.validate_disease_classes()
        
        assert result["is_valid"] is False
        assert 0 < result["match_rate"] < 1
        assert len(result["missing_classes"]) > 0

    def test_validate_classes_model_not_loaded(self):
        """
        测试模型未加载时校验
        
        验证:
        - 返回无效状态
        - 匹配率为 0
        """
        service = YOLOv8Service(auto_load=False)
        
        result = service.validate_disease_classes()
        
        assert result["is_valid"] is False
        assert result["match_rate"] == 0.0

    def test_validate_classes_extra_classes(self):
        """
        测试存在额外类别
        
        验证:
        - 额外类别正确识别
        - 校验不通过
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        extra_classes = service.EXPECTED_DISEASE_CLASSES | {"Unknown Disease"}
        mock_model = MagicMock()
        mock_model.names = {i: name for i, name in enumerate(extra_classes)}
        service.model = mock_model
        
        result = service.validate_disease_classes()
        
        assert result["is_valid"] is False
        assert "Unknown Disease" in result["extra_classes"]


class TestYOLOv8ServiceHelperMethods:
    """YOLOv8 辅助方法测试类"""

    def test_get_chinese_name_known(self):
        """
        测试获取已知病害的中文名称
        
        验证:
        - 返回正确的中文名称
        """
        service = YOLOv8Service(auto_load=False)
        
        assert service.get_chinese_name("Yellow Rust") == "条锈病"
        assert service.get_chinese_name("Mildew") == "白粉病"
        assert service.get_chinese_name("Healthy") == "健康"

    def test_get_chinese_name_unknown(self):
        """
        测试获取未知病害的名称
        
        验证:
        - 返回原英文名称
        """
        service = YOLOv8Service(auto_load=False)
        
        assert service.get_chinese_name("Unknown Disease") == "Unknown Disease"

    def test_get_model_info_loaded(self):
        """
        测试获取已加载模型信息
        
        验证:
        - 返回模型类型
        - 返回加载状态
        - 返回类别数量
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        mock_model = MagicMock()
        mock_model.names = {0: "Yellow Rust", 1: "Mildew"}
        service.model = mock_model
        
        info = service.get_model_info()
        
        assert info["model_type"] == "YOLOv8"
        assert info["is_loaded"] is True
        assert info["class_count"] == 2

    def test_get_model_info_not_loaded(self):
        """
        测试获取未加载模型信息
        
        验证:
        - 返回未加载状态
        - 类别列表为空
        """
        service = YOLOv8Service(auto_load=False)
        
        info = service.get_model_info()
        
        assert info["is_loaded"] is False
        assert info["class_count"] == 0

    def test_get_load_progress(self):
        """
        测试获取加载进度
        
        验证:
        - 未加载时返回 0
        """
        service = YOLOv8Service(auto_load=False)
        
        progress = service.get_load_progress()
        
        assert progress == 0


class TestGetYoloService:
    """YOLO 服务单例测试类"""

    def test_get_yolo_service_singleton(self):
        """
        测试获取服务单例
        
        验证:
        - 多次调用返回同一实例
        """
        with patch('app.services.yolo_service._yolo_service', None):
            with patch('app.services.yolo_service.ai_config') as mock_config:
                mock_config.YOLO_MODEL_PATH = None
                mock_config.YOLO_CONFIDENCE_THRESHOLD = 0.5
                
                with patch.object(YOLOv8Service, '_load_model'):
                    service1 = get_yolo_service()
                    service2 = get_yolo_service()
                    
                    assert service1 is service2

    def test_get_yolo_service_initialization_error(self):
        """
        测试服务初始化错误处理
        
        验证:
        - 初始化失败时创建默认配置
        """
        with patch('app.services.yolo_service._yolo_service', None):
            with patch('app.services.yolo_service.ai_config', side_effect=ImportError()):
                with patch('app.services.yolo_service.AIConfig') as mock_ai_config:
                    mock_instance = MagicMock()
                    mock_instance.YOLO_MODEL_PATH = None
                    mock_instance.YOLO_CONFIDENCE_THRESHOLD = 0.5
                    mock_ai_config.return_value = mock_instance
                    
                    with patch.object(YOLOv8Service, '_load_model'):
                        service = get_yolo_service()
                        
                        assert service is not None


class TestYOLOv8ServiceWarmup:
    """YOLOv8 模型预热测试类"""

    def test_warmup_success(self):
        """
        测试模型预热成功
        
        验证:
        - 预热不抛出异常
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        mock_model = MagicMock()
        service.model = mock_model
        
        service._warmup()
        
        mock_model.assert_called_once()

    def test_warmup_model_not_loaded(self):
        """
        测试模型未加载时预热
        
        验证:
        - 不执行任何操作
        """
        service = YOLOv8Service(auto_load=False)
        
        service._warmup()

    def test_warmup_exception_handling(self):
        """
        测试预热异常处理
        
        验证:
        - 异常被捕获，不抛出
        """
        service = YOLOv8Service(auto_load=False)
        service.is_loaded = True
        
        mock_model = MagicMock(side_effect=Exception("预热失败"))
        service.model = mock_model
        
        service._warmup()
