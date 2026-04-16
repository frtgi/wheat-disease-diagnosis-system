# -*- coding: utf-8 -*-
"""
视觉感知引擎 (Vision Engine)

基于SerpensGate-YOLOv8的小麦病害视觉检测引擎：
- 动态蛇形卷积捕获细长病斑
- SPPELAN多尺度特征聚合
- 超级令牌注意力全局推理
- 批处理推理支持
- 性能监控集成
- 模型预热机制
- CIoU细长病斑优化
"""
import os
import glob
import time
import math
from typing import List, Dict, Optional, Tuple, Any
from ultralytics import YOLO
import requests
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()
os.environ['ULTRALYTICS_OFFLINE'] = 'true'
_original_get = requests.get
def patched_get(*args, **kwargs):
    kwargs['verify'] = False
    return _original_get(*args, **kwargs)
requests.get = patched_get


class BBoxOptimizer:
    """
    边界框优化器
    
    提供CIoU计算和细长病斑检测框优化功能
    """
    
    def __init__(self, aspect_ratio_threshold: float = 3.0):
        """
        初始化边界框优化器
        
        :param aspect_ratio_threshold: 长宽比阈值，超过此值视为细长目标
        """
        self.aspect_ratio_threshold = aspect_ratio_threshold
        self._optimization_stats = {
            "total_boxes": 0,
            "elongated_boxes": 0,
            "optimized_boxes": 0
        }
    
    def calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """
        计算两个边界框的IoU
        
        :param box1: [x1, y1, x2, y2]
        :param box2: [x1, y1, x2, y2]
        :return: IoU值
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def calculate_ciou(self, pred_box: List[float], true_box: List[float]) -> float:
        """
        计算CIoU (Complete Intersection over Union)
        
        CIoU考虑了：
        1. 重叠面积 (IoU)
        2. 中心点距离
        3. 长宽比一致性
        
        :param pred_box: 预测框 [x1, y1, x2, y2]
        :param true_box: 真实框 [x1, y1, x2, y2]
        :return: CIoU值 (范围0-1，越大越好)
        """
        iou = self.calculate_iou(pred_box, true_box)
        
        pred_cx = (pred_box[0] + pred_box[2]) / 2
        pred_cy = (pred_box[1] + pred_box[3]) / 2
        true_cx = (true_box[0] + true_box[2]) / 2
        true_cy = (true_box[1] + true_box[3]) / 2
        
        center_dist_sq = (pred_cx - true_cx) ** 2 + (pred_cy - true_cy) ** 2
        
        x1_min = min(pred_box[0], true_box[0])
        y1_min = min(pred_box[1], true_box[1])
        x2_max = max(pred_box[2], true_box[2])
        y2_max = max(pred_box[3], true_box[3])
        
        c_sq = (x2_max - x1_min) ** 2 + (y2_max - y1_min) ** 2
        
        if c_sq == 0:
            return iou
        
        pred_w = pred_box[2] - pred_box[0]
        pred_h = pred_box[3] - pred_box[1]
        true_w = true_box[2] - true_box[0]
        true_h = true_box[3] - true_box[1]
        
        if pred_w <= 0 or pred_h <= 0 or true_w <= 0 or true_h <= 0:
            return iou
        
        v = (4 / math.pi ** 2) * (math.atan(true_w / true_h) - math.atan(pred_w / pred_h)) ** 2
        
        alpha = v / (1 - iou + v + 1e-7)
        
        ciou = iou - (center_dist_sq / c_sq) - alpha * v
        
        return max(0.0, min(1.0, ciou))
    
    def is_elongated(self, bbox: List[float]) -> bool:
        """
        判断是否为细长目标
        
        :param bbox: 边界框 [x1, y1, x2, y2]
        :return: 是否为细长目标
        """
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        if w <= 0 or h <= 0:
            return False
        
        aspect_ratio = max(w, h) / min(w, h)
        return aspect_ratio > self.aspect_ratio_threshold
    
    def optimize_elongated_bbox(
        self,
        bbox: List[float],
        image_shape: Tuple[int, int],
        expand_ratio: float = 0.1
    ) -> List[float]:
        """
        优化细长目标边界框
        
        对于细长病斑（如条锈病条纹），适当扩展边界框以捕获完整病斑
        
        :param bbox: 原始边界框 [x1, y1, x2, y2]
        :param image_shape: 图像尺寸 (height, width)
        :param expand_ratio: 扩展比例
        :return: 优化后的边界框
        """
        if not self.is_elongated(bbox):
            return bbox
        
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        
        if w > h:
            expand = h * expand_ratio
            y1 = max(0, y1 - expand)
            y2 = min(image_shape[0], y2 + expand)
        else:
            expand = w * expand_ratio
            x1 = max(0, x1 - expand)
            x2 = min(image_shape[1], x2 + expand)
        
        self._optimization_stats["optimized_boxes"] += 1
        
        return [x1, y1, x2, y2]
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取优化统计信息
        
        :return: 统计信息字典
        """
        return self._optimization_stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._optimization_stats = {
            "total_boxes": 0,
            "elongated_boxes": 0,
            "optimized_boxes": 0
        }


class VisionAgent:
    """
    视觉感知智能体
    
    基于SerpensGate-YOLOv8实现小麦病害检测，支持：
    - 单图检测
    - 批处理推理
    - 性能监控
    - 模型预热
    - 推理缓存
    - CIoU细长病斑优化
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        enable_cache: bool = True,
        enable_monitoring: bool = True,
        auto_warmup: bool = True,
        enable_bbox_optimization: bool = True,
        ciou_threshold: float = 0.7
    ):
        """
        初始化视觉感知智能体
        
        :param model_path: 模型路径（可选）
        :param enable_cache: 是否启用推理缓存
        :param enable_monitoring: 是否启用性能监控
        :param auto_warmup: 是否自动预热模型
        :param enable_bbox_optimization: 是否启用边界框优化
        :param ciou_threshold: CIoU阈值，低于此值触发优化
        """
        print("👁️ [Vision Agent] 正在初始化...")
        
        self._is_warmed_up = False
        self._cache = None
        self._monitor = None
        self._bbox_optimizer = None
        
        self.enable_bbox_optimization = enable_bbox_optimization
        self.ciou_threshold = ciou_threshold
        
        if enable_bbox_optimization:
            self._bbox_optimizer = BBoxOptimizer(aspect_ratio_threshold=3.0)
            print("📐 边界框优化已启用 (CIoU优化)")
        
        final_model_path = self._find_model(model_path)
        
        print(f"🚀 加载模型: {os.path.basename(final_model_path)}")
        try:
            self.model = YOLO(final_model_path, task='detect')
            self.model_path = final_model_path
            print("✅ 视觉模型就绪！")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.model = YOLO('yolov8n.pt')
            self.model_path = 'yolov8n.pt'
        
        if enable_cache:
            self._init_cache()
        
        if enable_monitoring:
            self._init_monitor()
        
        if auto_warmup:
            self.warmup()
    
    def _find_model(self, model_path: Optional[str]) -> str:
        """
        查找模型文件
        
        :param model_path: 指定的模型路径
        :return: 最终模型路径
        """
        if model_path and os.path.exists(model_path):
            print(f"✅ 使用指定模型: {model_path}")
            return model_path
        
        search_candidates = [
            os.path.join(os.getcwd(), "models", "wheat_disease_v10_yolov8s", "phase1_warmup", "weights", "best.pt"),
            os.path.join(os.getcwd(), "models", "wheat_disease_v5_optimized_phase2", "weights", "best.pt"),
            os.path.join(os.getcwd(), "models", "wheat_disease_v3", "weights", "best.pt"),
            os.path.join(os.getcwd(), "models", "wheat_disease_v4", "weights", "best.pt"),
            os.path.join(os.getcwd(), "models", "yolov8_wheat.pt"),
            "D:/Project/WheatAgent/models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt",
            "D:/Project/WheatAgent/models/wheat_disease_v5_optimized_phase2/weights/best.pt",
            os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_evolution_v2", "weights", "best.pt"),
            os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_evolution", "weights", "best.pt"),
            os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_experiment2", "weights", "best.pt"),
            os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_experiment", "weights", "best.pt"),
        ]
        
        for candidate in search_candidates:
            if os.path.exists(candidate):
                print(f"✅ 找到小麦病害模型: {candidate}")
                return candidate
        
        search_patterns = [
            os.path.join(os.getcwd(), "runs", "**", "weights", "best.pt"),
        ]
        found_models = []
        for pattern in search_patterns:
            found_models.extend(glob.glob(pattern, recursive=True))
        
        if found_models:
            best_model = max(found_models, key=os.path.getmtime)
            print(f"✅ 自动定位最新模型: {best_model}")
            return best_model
        
        print("⚠️ 未找到小麦病害模型，使用官方 yolov8n.pt (检测精度将受限)")
        return "yolov8n.pt"
    
    def _init_cache(self) -> None:
        """初始化推理缓存"""
        try:
            from ..utils.inference_cache import InferenceCache
            self._cache = InferenceCache(
                max_size=500,
                ttl_seconds=1800
            )
            print("📦 推理缓存已启用")
        except ImportError:
            print("⚠️ 推理缓存模块不可用")
            self._cache = None
    
    def _init_monitor(self) -> None:
        """初始化性能监控"""
        try:
            from ..utils.performance_monitor import PerformanceMonitor
            self._monitor = PerformanceMonitor(name="VisionAgent")
            print("📊 性能监控已启用")
        except ImportError:
            print("⚠️ 性能监控模块不可用")
            self._monitor = None
    
    def warmup(self, num_runs: int = 3) -> Dict[str, Any]:
        """
        模型预热
        
        通过运行几次推理来预热模型，减少首次推理延迟
        
        :param num_runs: 预热次数
        :return: 预热结果
        """
        if self._is_warmed_up:
            print("🔥 模型已预热，跳过")
            return {"status": "already_warmed_up"}
        
        print(f"🔥 开始模型预热 ({num_runs} 次)...")
        
        import numpy as np
        
        warmup_times = []
        
        for i in range(num_runs):
            start = time.time()
            
            dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            try:
                _ = self.model.predict(
                    source=dummy_image,
                    conf=0.25,
                    verbose=False
                )
            except Exception:
                pass
            
            elapsed = time.time() - start
            warmup_times.append(elapsed)
            print(f"   预热 {i+1}/{num_runs}: {elapsed*1000:.1f}ms")
        
        self._is_warmed_up = True
        
        avg_time = sum(warmup_times) / len(warmup_times)
        print(f"✅ 模型预热完成，平均耗时: {avg_time*1000:.1f}ms")
        
        return {
            "status": "success",
            "warmup_runs": num_runs,
            "average_time_ms": avg_time * 1000,
            "times_ms": [t * 1000 for t in warmup_times]
        }
    
    def detect(
        self,
        image_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        save_result: bool = False,
        use_cache: bool = True,
        optimize_bbox: bool = True
    ) -> List[Dict[str, Any]]:
        """
        执行单图检测
        
        :param image_path: 图像路径
        :param conf_threshold: 置信度阈值
        :param iou_threshold: NMS IoU阈值
        :param save_result: 是否保存可视化结果
        :param use_cache: 是否使用缓存
        :param optimize_bbox: 是否优化边界框
        :return: 检测结果列表
        """
        if not os.path.exists(image_path):
            print(f"❌ 图片不存在: {image_path}")
            return []
        
        params = {
            "conf": conf_threshold,
            "iou": iou_threshold,
            "optimize": optimize_bbox
        }
        
        if use_cache and self._cache:
            cached = self._cache.get(image_path, params)
            if cached is not None:
                return cached
        
        if self._monitor:
            start_time = self._monitor.start_timer("detect")
        
        print(f"🔍 视觉扫描中... (图片: {os.path.basename(image_path)})")
        
        try:
            results = self.model.predict(
                source=image_path,
                conf=conf_threshold,
                iou=iou_threshold,
                save=save_result,
                verbose=False,
                augment=True,
                agnostic_nms=True
            )
            
            image_shape = None
            if optimize_bbox and self._bbox_optimizer:
                try:
                    from PIL import Image
                    with Image.open(image_path) as img:
                        image_shape = img.size[::-1]
                except Exception:
                    pass
            
            formatted_results = self._format_results(results, image_shape, optimize_bbox)
            
            if use_cache and self._cache and formatted_results:
                self._cache.put(image_path, formatted_results, params)
            
            if self._monitor:
                self._monitor.stop_timer("detect", start_time)
                self._monitor.record_fps()
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 推理过程出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def batch_detect(
        self,
        image_paths: List[str],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        batch_size: int = 4,
        save_results: bool = False,
        optimize_bbox: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量图像检测
        
        支持GPU并行处理多张图像，提高推理效率
        
        :param image_paths: 图像路径列表
        :param conf_threshold: 置信度阈值
        :param iou_threshold: NMS IoU阈值
        :param batch_size: 批大小
        :param save_results: 是否保存可视化结果
        :param optimize_bbox: 是否优化边界框
        :return: {图像路径: 检测结果} 字典
        """
        print(f"📦 批量检测: {len(image_paths)} 张图像, 批大小: {batch_size}")
        
        if self._monitor:
            start_time = self._monitor.start_timer("batch_detect")
        
        valid_paths = [p for p in image_paths if os.path.exists(p)]
        
        if len(valid_paths) < len(image_paths):
            invalid_count = len(image_paths) - len(valid_paths)
            print(f"⚠️ 跳过 {invalid_count} 张不存在的图像")
        
        all_results = {}
        total_detections = 0
        
        for i in range(0, len(valid_paths), batch_size):
            batch_paths = valid_paths[i:i + batch_size]
            
            print(f"🔄 处理批次 {i//batch_size + 1}/{(len(valid_paths)-1)//batch_size + 1}")
            
            batch_start = time.time()
            
            try:
                results_list = self.model.predict(
                    source=batch_paths,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    save=save_results,
                    verbose=False,
                    augment=True,
                    agnostic_nms=True
                )
                
                for path, results in zip(batch_paths, results_list):
                    image_shape = None
                    if optimize_bbox and self._bbox_optimizer:
                        try:
                            from PIL import Image
                            with Image.open(path) as img:
                                image_shape = img.size[::-1]
                        except Exception:
                            pass
                    
                    formatted = self._format_results([results], image_shape, optimize_bbox)
                    all_results[path] = formatted
                    total_detections += len(formatted)
                
            except Exception as e:
                print(f"❌ 批次处理失败: {e}")
                for path in batch_paths:
                    all_results[path] = []
            
            batch_time = time.time() - batch_start
            fps = len(batch_paths) / batch_time if batch_time > 0 else 0
            print(f"   批次耗时: {batch_time*1000:.1f}ms, FPS: {fps:.1f}")
        
        if self._monitor:
            self._monitor.stop_timer("batch_detect", start_time)
            for _ in range(len(valid_paths)):
                self._monitor.record_fps()
        
        print(f"✅ 批量检测完成: {total_detections} 个目标")
        
        return all_results
    
    def _format_results(
        self,
        results: List,
        image_shape: Optional[Tuple[int, int]] = None,
        optimize_bbox: bool = True
    ) -> List[Dict[str, Any]]:
        """
        格式化检测结果
        
        :param results: YOLO原始结果
        :param image_shape: 图像尺寸 (height, width)
        :param optimize_bbox: 是否优化边界框
        :return: 格式化结果列表
        """
        formatted_results = []
        
        if len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            if boxes is not None and len(boxes) > 0:
                print(f"📊 视觉捕获: {len(boxes)} 个目标")
                
                for i, box in enumerate(boxes):
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    class_name = self.model.names.get(cls_id, f'类别{cls_id}')
                    
                    xyxy = box.xyxy[0].cpu().numpy() if hasattr(box.xyxy, 'cpu') else box.xyxy[0]
                    bbox = [float(x) for x in xyxy]
                    
                    is_elongated = False
                    if self._bbox_optimizer:
                        self._bbox_optimizer._optimization_stats["total_boxes"] += 1
                        is_elongated = self._bbox_optimizer.is_elongated(bbox)
                        
                        if is_elongated:
                            self._bbox_optimizer._optimization_stats["elongated_boxes"] += 1
                        
                        if optimize_bbox and image_shape and is_elongated:
                            bbox = self._bbox_optimizer.optimize_elongated_bbox(
                                bbox, image_shape, expand_ratio=0.1
                            )
                    
                    formatted_result = {
                        'name': class_name,
                        'confidence': conf,
                        'bbox': bbox,
                        'class_id': cls_id,
                        'is_elongated': is_elongated
                    }
                    formatted_results.append(formatted_result)
                    
                    elongated_marker = " [细长]" if is_elongated else ""
                    print(f"   目标 {i+1}: {class_name}{elongated_marker} (置信度: {conf:.2f})")
            else:
                print(f"🍃 视觉未发现异常")
        else:
            print(f"🍃 视觉未发现异常 (无结果)")
        
        return formatted_results
    
    def detect_and_visualize(
        self,
        image_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        output_path: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        执行检测并生成可视化结果
        
        :param image_path: 输入图像路径
        :param conf_threshold: 置信度阈值
        :param iou_threshold: NMS IoU阈值
        :param output_path: 输出图像路径
        :return: (检测结果, 可视化图像路径)
        """
        from PIL import Image, ImageDraw, ImageFont
        
        results = self.detect(image_path, conf_threshold, iou_threshold, save_result=False)
        
        if not results:
            return results, None
        
        try:
            image = Image.open(image_path).convert('RGB')
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            for result in results:
                bbox = result['bbox']
                name = result['name']
                confidence = result['confidence']
                is_elongated = result.get('is_elongated', False)
                
                color = "orange" if is_elongated else "red"
                draw.rectangle(bbox, outline=color, width=3)
                
                label = f"{name} {confidence:.2%}"
                if is_elongated:
                    label += " [细长]"
                
                bbox_text = draw.textbbox((0, 0), label, font=font)
                text_width = bbox_text[2] - bbox_text[0]
                text_height = bbox_text[3] - bbox_text[1]
                
                draw.rectangle(
                    [bbox[0], bbox[1] - text_height - 4, bbox[0] + text_width + 4, bbox[1]],
                    fill=color
                )
                
                draw.text((bbox[0] + 2, bbox[1] - text_height - 2), label, fill="white", font=font)
            
            if output_path is None:
                output_path = image_path.replace('.jpg', '_result.jpg').replace('.png', '_result.png')
            
            image.save(output_path)
            print(f"📸 可视化结果已保存: {output_path}")
            
            return results, output_path
            
        except Exception as e:
            print(f"❌ 可视化生成失败: {e}")
            import traceback
            traceback.print_exc()
            return results, None
    
    def evaluate_ciou(
        self,
        predictions: List[Dict[str, Any]],
        ground_truths: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        评估检测结果的CIoU指标
        
        :param predictions: 预测结果列表
        :param ground_truths: 真实标注列表
        :return: 评估结果
        """
        if not self._bbox_optimizer:
            return {"error": "边界框优化器未启用"}
        
        ciou_scores = []
        matched_count = 0
        
        for pred in predictions:
            pred_bbox = pred.get('bbox', [])
            pred_class = pred.get('class_id', -1)
            
            best_ciou = 0.0
            for gt in ground_truths:
                gt_bbox = gt.get('bbox', [])
                gt_class = gt.get('class_id', -1)
                
                if pred_class == gt_class:
                    ciou = self._bbox_optimizer.calculate_ciou(pred_bbox, gt_bbox)
                    best_ciou = max(best_ciou, ciou)
            
            if best_ciou > 0:
                ciou_scores.append(best_ciou)
                matched_count += 1
        
        avg_ciou = sum(ciou_scores) / len(ciou_scores) if ciou_scores else 0.0
        
        return {
            "average_ciou": avg_ciou,
            "matched_predictions": matched_count,
            "total_predictions": len(predictions),
            "total_ground_truths": len(ground_truths),
            "ciou_scores": ciou_scores
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        :return: 性能统计字典
        """
        stats = {
            "model_path": self.model_path,
            "is_warmed_up": self._is_warmed_up,
            "bbox_optimization_enabled": self.enable_bbox_optimization,
            "ciou_threshold": self.ciou_threshold
        }
        
        if self._monitor:
            monitor_stats = self._monitor.get_latency_summary("detect")
            stats.update({
                "latency": monitor_stats,
                "fps": self._monitor.get_fps()
            })
        
        if self._cache:
            cache_stats = self._cache.get_stats()
            stats["cache"] = cache_stats
        
        if self._bbox_optimizer:
            stats["bbox_optimizer"] = self._bbox_optimizer.get_stats()
        
        return stats
    
    def print_performance_summary(self) -> None:
        """打印性能摘要"""
        print("\n📊 [Vision Agent] 性能摘要")
        print("=" * 50)
        print(f"   模型路径: {self.model_path}")
        print(f"   预热状态: {'已预热' if self._is_warmed_up else '未预热'}")
        print(f"   边界框优化: {'已启用' if self.enable_bbox_optimization else '未启用'}")
        
        if self._monitor:
            self._monitor.print_summary()
        
        if self._cache:
            self._cache.print_stats()
        
        if self._bbox_optimizer:
            opt_stats = self._bbox_optimizer.get_stats()
            print(f"\n📐 边界框优化统计:")
            print(f"   总边界框数: {opt_stats['total_boxes']}")
            print(f"   细长目标数: {opt_stats['elongated_boxes']}")
            print(f"   已优化数量: {opt_stats['optimized_boxes']}")
        
        print("=" * 50)
    
    def clear_cache(self) -> None:
        """清空推理缓存"""
        if self._cache:
            self._cache.clear()
            print("🗑️ 推理缓存已清空")
    
    def reset_optimization_stats(self) -> None:
        """重置优化统计信息"""
        if self._bbox_optimizer:
            self._bbox_optimizer.reset_stats()
            print("📊 边界框优化统计已重置")
