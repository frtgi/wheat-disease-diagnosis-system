"""
YOLOv8 病害检测服务
提供小麦病害图像检测功能
支持 FP16 半精度推理、结果缓存和批量检测
"""
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set
from collections import OrderedDict
from PIL import Image

logger = logging.getLogger(__name__)


class YOLOv8Service:
    """YOLOv8 病害检测服务类，支持 FP16 推理、结果缓存和批量检测"""
    
    EXPECTED_DISEASE_CLASSES: Set[str] = {
        "Aphid",
        "Black Rust",
        "Blast",
        "Brown Rust",
        "Common Root Rot",
        "Fusarium Head Blight",
        "Healthy",
        "Leaf Blight",
        "Mildew",
        "Mite",
        "Septoria",
        "Smut",
        "Stem fly",
        "Tan spot",
        "Yellow Rust"
    }
    
    DISEASE_NAME_MAPPING: Dict[str, str] = {
        "Aphid": "蚜虫",
        "Black Rust": "秆锈病",
        "Blast": "稻瘟病",
        "Brown Rust": "叶锈病",
        "Common Root Rot": "根腐病",
        "Fusarium Head Blight": "赤霉病",
        "Healthy": "健康",
        "Leaf Blight": "叶枯病",
        "Mildew": "白粉病",
        "Mite": "螨虫",
        "Septoria": "壳针孢叶斑病",
        "Smut": "黑粉病",
        "Stem fly": "茎蝇",
        "Tan spot": "褐斑病",
        "Yellow Rust": "条锈病"
    }

    model_path: Optional[Path]
    confidence_threshold: float
    model: Any
    is_loaded: bool
    _load_progress: int
    _use_fp16: bool
    _fp16_available: bool
    _inference_cache: OrderedDict
    _cache_max_size: int
    
    def __init__(self, model_path: Optional[Path] = None, confidence_threshold: float = 0.5,
                 auto_load: bool = True, use_fp16: bool = True, cache_size: int = 64) -> None:
        """
        初始化 YOLOv8 服务
        
        参数:
            model_path: YOLO 模型路径
            confidence_threshold: 置信度阈值
            auto_load: 是否自动加载模型
            use_fp16: 是否启用 FP16 半精度推理（GPU 可用时）
            cache_size: 推理缓存最大条目数
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.is_loaded = False
        self._load_progress = 0
        self._use_fp16 = use_fp16
        self._fp16_available = False
        self._cache_max_size = cache_size
        self._inference_cache = OrderedDict()
        
        if auto_load:
            self._load_model()
    
    def _load_model(self, progress_callback: Optional[Callable] = None) -> None:
        """
        加载 YOLOv8 模型
        
        参数:
            progress_callback: 进度回调函数，接收 (progress: int, message: str)
        """
        try:
            from ultralytics import YOLO
            import torch
            
            if progress_callback:
                progress_callback(10, "初始化 YOLO 服务")
            
            if self.model_path:
                if self.model_path.is_file():
                    model_file = self.model_path
                    if progress_callback:
                        progress_callback(30, f"加载模型：{model_file.name}")
                else:
                    model_files = list(self.model_path.glob("*.pt"))
                    if not model_files:
                        logger.warning(f"在 {self.model_path} 中未找到 .pt 模型文件")
                        if progress_callback:
                            progress_callback(0, "未找到模型文件")
                        return
                    model_file = max(model_files, key=lambda p: p.stat().st_mtime)
                    if progress_callback:
                        progress_callback(30, f"加载模型：{model_file.name}")
                
                self.model = YOLO(str(model_file))
                
                if progress_callback:
                    progress_callback(70, "验证模型")
                
                self.is_loaded = True
                
                if self._use_fp16 and torch.cuda.is_available():
                    try:
                        self.model.fuse()
                        self._fp16_available = True
                        logger.info("YOLOv8 FP16 半精度推理已启用（CUDA 可用）")
                    except Exception as fp16_err:
                        logger.warning(f"FP16 初始化失败: {fp16_err}，将使用 FP32")
                        self._fp16_available = False
                elif self._use_fp16:
                    logger.info("CUDA 不可用，YOLO 将使用 FP32 推理")
                
                if progress_callback:
                    progress_callback(100, "YOLO 模型加载完成")
                
                logger.info(f"YOLOv8 模型加载成功：{model_file} (FP16={self._fp16_available})")
                
                validation_result = self.validate_disease_classes()
                self._log_validation_result(validation_result)
            else:
                if progress_callback:
                    progress_callback(50, "加载预训练模型")
                
                self.model = YOLO("yolov8s.pt")
                self.is_loaded = True
                
                if self._use_fp16 and torch.cuda.is_available():
                    try:
                        self.model.fuse()
                        self._fp16_available = True
                    except Exception:
                        self._fp16_available = False
                
                if progress_callback:
                    progress_callback(100, "预训练模型加载完成")
                
                logger.info("YOLOv8 预训练模型加载成功")
                
                validation_result = self.validate_disease_classes()
                self._log_validation_result(validation_result)
                
        except Exception as e:
            logger.error(f"YOLOv8 模型加载失败：{e}")
            self.is_loaded = False
            if progress_callback:
                progress_callback(0, f"加载失败：{e}")
    
    def validate_disease_classes(self) -> Dict[str, Any]:
        """
        校验模型类别是否与预期病害类别匹配
        
        返回:
            包含校验结果的字典:
            - is_valid: 是否通过校验（匹配率100%）
            - match_rate: 匹配率（0-1之间）
            - matched_classes: 匹配的类别列表
            - missing_classes: 缺失的类别列表
            - extra_classes: 多余的类别列表
            - model_classes: 模型实际类别列表
            - expected_classes: 预期类别列表
        """
        if not self.is_loaded or self.model is None:
            return {
                "is_valid": False,
                "match_rate": 0.0,
                "matched_classes": [],
                "missing_classes": list(self.EXPECTED_DISEASE_CLASSES),
                "extra_classes": [],
                "model_classes": [],
                "expected_classes": list(self.EXPECTED_DISEASE_CLASSES)
            }
        
        model_classes = set(self.model.names.values())
        expected_classes = self.EXPECTED_DISEASE_CLASSES
        
        matched_classes = model_classes & expected_classes
        missing_classes = expected_classes - model_classes
        extra_classes = model_classes - expected_classes
        
        match_rate = len(matched_classes) / len(expected_classes) if expected_classes else 0.0
        is_valid = match_rate == 1.0 and len(extra_classes) == 0
        
        result = {
            "is_valid": is_valid,
            "match_rate": match_rate,
            "matched_classes": sorted(list(matched_classes)),
            "missing_classes": sorted(list(missing_classes)),
            "extra_classes": sorted(list(extra_classes)),
            "model_classes": sorted(list(model_classes)),
            "expected_classes": sorted(list(expected_classes))
        }
        
        return result
    
    def _log_validation_result(self, result: Dict[str, Any]) -> None:
        """
        记录病害类别校验结果日志
        
        参数:
            result: validate_disease_classes() 返回的校验结果
        """
        match_rate_percent = result["match_rate"] * 100
        
        if result["is_valid"]:
            logger.info(f"病害类别校验通过，匹配率：{match_rate_percent:.1f}%，共 {len(result['matched_classes'])} 个类别")
        else:
            logger.warning(f"病害类别校验未通过，匹配率：{match_rate_percent:.1f}%")
            
            if result["matched_classes"]:
                logger.info(f"匹配的类别 ({len(result['matched_classes'])}个)：{', '.join(result['matched_classes'])}")
            
            if result["missing_classes"]:
                logger.warning(f"缺失的类别 ({len(result['missing_classes'])}个)：{', '.join(result['missing_classes'])}")
            
            if result["extra_classes"]:
                logger.warning(f"多余的类别 ({len(result['extra_classes'])}个)：{', '.join(result['extra_classes'])}")
    
    def get_load_progress(self) -> int:
        """获取加载进度"""
        return self._load_progress if self.is_loaded else 0
    
    def _warmup(self) -> None:
        """
        模型预热
        
        执行一次推理以初始化 CUDA 内核，提高后续推理速度
        """
        if not self.is_loaded:
            return
        
        try:
            import numpy as np
            # 创建一个小的随机图像进行预热
            dummy_image = Image.fromarray(np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8))
            # 执行一次推理
            _ = self.model(dummy_image)
            logger.info("YOLOv8 模型预热完成")
        except Exception as e:
            logger.warning(f"模型预热失败：{e}")
    
    def detect(self, image: Image.Image, use_cache: bool = True) -> Dict[str, Any]:
        """
        检测图像中的病害
        
        参数:
            image: PIL Image 对象
            use_cache: 是否使用推理结果缓存
            
        返回:
            包含检测结果的字典，包括英文类别名和中文名称
        """
        if not self.is_loaded:
            return {
                "success": False,
                "error": "模型未加载",
                "detections": []
            }
        
        try:
            image_hash = self._compute_image_hash(image)
            
            if use_cache and image_hash:
                cached_result = self._get_cached_result(image_hash)
                if cached_result is not None:
                    logger.debug(f"YOLO 推理缓存命中: hash={image_hash[:16]}...")
                    cached_result["cache_hit"] = True
                    return cached_result
            
            start_time = time.time()
            
            inference_kwargs = {"conf": self.confidence_threshold}
            if self._fp16_available:
                inference_kwargs["half"] = True
            
            results = self.model(image, **inference_kwargs)
            result = results[0]
            
            detections = []
            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()
                for i in range(len(boxes)):
                    box = boxes[i]
                    class_name = self.model.names[int(box.cls[0])]
                    chinese_name = self.DISEASE_NAME_MAPPING.get(class_name, class_name)
                    
                    detection = {
                        "class_id": int(box.cls[0]),
                        "class_name": class_name,
                        "chinese_name": chinese_name,
                        "confidence": float(box.conf[0]),
                        "bbox": {
                            "x1": float(box.xyxy[0][0]),
                            "y1": float(box.xyxy[0][1]),
                            "x2": float(box.xyxy[0][2]),
                            "y2": float(box.xyxy[0][3]),
                            "width": float(box.xyxy[0][2] - box.xyxy[0][0]),
                            "height": float(box.xyxy[0][3] - box.xyxy[0][1])
                        }
                    }
                    detections.append(detection)
            
            inference_time_ms = (time.time() - start_time) * 1000
            
            response = {
                "success": True,
                "detections": detections,
                "count": len(detections),
                "image_size": {
                    "width": image.width,
                    "height": image.height
                },
                "inference_time_ms": round(inference_time_ms, 2),
                "fp16_used": self._fp16_available,
                "cache_hit": False
            }
            
            if use_cache and image_hash:
                self._set_cached_result(image_hash, response)
            
            logger.info(
                f"YOLOv8 检测完成: {len(detections)} 个目标, "
                f"耗时 {inference_time_ms:.2f}ms (FP16={self._fp16_available})"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"YOLOv8 检测失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "detections": []
            }
    
    def detect_from_file(self, image_path: Path) -> Dict[str, Any]:
        """
        从文件检测病害
        
        参数:
            image_path: 图像文件路径
            
        返回:
            包含检测结果的字典
        """
        try:
            image = Image.open(image_path)
            return self.detect(image)
        except Exception as e:
            logger.error(f"加载图像文件失败：{e}")
            return {
                "success": False,
                "error": f"加载图像失败：{str(e)}",
                "detections": []
            }

    def batch_detect(
        self,
        images: List[Image.Image],
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量检测多张图像中的病害
        
        参数:
            images: PIL Image 对象列表
            use_cache: 是否使用推理结果缓存
            
        返回:
            包含每张图像检测结果的字典列表
        """
        if not self.is_loaded:
            return [{"success": False, "error": "模型未加载", "detections": []}] * len(images)
        
        start_time = time.time()
        results = []
        
        for i, image in enumerate(images):
            try:
                result = self.detect(image, use_cache=use_cache)
                result["batch_index"] = i
                results.append(result)
            except Exception as e:
                logger.error(f"批量检测第 {i} 张图像失败: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "detections": [],
                    "batch_index": i
                })
        
        total_time_ms = (time.time() - start_time) * 1000
        success_count = sum(1 for r in results if r.get("success"))
        
        logger.info(
            f"批量 YOLO 检测完成: {len(images)} 张图像, "
            f"成功 {success_count} 张, "
            f"总耗时 {total_time_ms:.2f}ms"
        )
        
        return results

    def _compute_image_hash(self, image: Image.Image) -> Optional[str]:
        """
        计算图像的 MD5 哈希值用于缓存键
        
        Args:
            image: PIL Image 对象
            
        Returns:
            MD5 哈希字符串，失败返回 None
        """
        try:
            import io
            
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_data = buffer.getvalue()
            
            return hashlib.md5(image_data).hexdigest()
            
        except Exception as e:
            logger.debug(f"计算图像哈希失败: {e}")
            return None

    def _get_cached_result(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取推理结果
        
        Args:
            image_hash: 图像哈希值
            
        Returns:
            缓存的检测结果，未命中返回 None
        """
        if image_hash in self._inference_cache:
            self._inference_cache.move_to_end(image_hash)
            return self._inference_cache[image_hash]
        return None

    def _set_cached_result(self, image_hash: str, result: Dict[str, Any]) -> None:
        """
        将推理结果存入缓存
        
        使用 LRU 策略，超出容量时淘汰最旧的条目。
        
        Args:
            image_hash: 图像哈希值
            result: 检测结果字典
        """
        if image_hash in self._inference_cache:
            del self._inference_cache[image_hash]
        
        while len(self._inference_cache) >= self._cache_max_size:
            self._inference_cache.popitem(last=False)
        
        cache_entry = {
            "success": result.get("success", False),
            "detections": result.get("detections", []),
            "count": result.get("count", 0),
            "image_size": result.get("image_size"),
            "cache_hit": False,
            "fp16_used": result.get("fp16_used", False)
        }
        
        self._inference_cache[image_hash] = cache_entry

    def clear_inference_cache(self) -> int:
        """
        清空推理缓存
        
        Returns:
            清除的缓存条目数
        """
        count = len(self._inference_cache)
        self._inference_cache.clear()
        logger.info(f"YOLO 推理缓存已清空，共 {count} 条")
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计字典
        """
        return {
            "current_size": len(self._inference_cache),
            "max_size": self._cache_max_size,
            "utilization": round(len(self._inference_cache) / max(1, self._cache_max_size), 2),
            "fp16_enabled": self._fp16_available
        }
    
    def get_chinese_name(self, english_name: str) -> str:
        """
        获取病害的中文名称
        
        参数:
            english_name: 英文病害名称
            
        返回:
            中文病害名称，如果未找到映射则返回原英文名称
        """
        return self.DISEASE_NAME_MAPPING.get(english_name, english_name)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        返回:
            包含模型详细信息的字典
        """
        classes = list(self.model.names.values()) if self.model else []
        class_mapping = {cls: self.DISEASE_NAME_MAPPING.get(cls, cls) for cls in classes}
        
        return {
            "model_type": "YOLOv8",
            "model_path": str(self.model_path) if self.model_path else "pretrained",
            "is_loaded": self.is_loaded,
            "confidence_threshold": self.confidence_threshold,
            "classes": classes,
            "class_count": len(classes),
            "class_mapping": class_mapping,
            "fp16_enabled": self._fp16_available,
            "cache_stats": self.get_cache_stats()
        }


# 全局服务实例
_yolo_service: Optional[YOLOv8Service] = None


def get_yolo_service() -> YOLOv8Service:
    """获取 YOLOv8 服务单例"""
    global _yolo_service
    if _yolo_service is None:
        try:
            from app.core.ai_config import ai_config
            _yolo_service = YOLOv8Service(
                model_path=ai_config.YOLO_MODEL_PATH,
                confidence_threshold=ai_config.YOLO_CONFIDENCE_THRESHOLD
            )
        except Exception as e:
            logger.error(f"初始化 YOLO 服务失败：{e}")
            from app.core.ai_config import AIConfig
            ai_config = AIConfig()
            _yolo_service = YOLOv8Service(
                model_path=ai_config.YOLO_MODEL_PATH,
                confidence_threshold=ai_config.YOLO_CONFIDENCE_THRESHOLD
            )
    return _yolo_service
