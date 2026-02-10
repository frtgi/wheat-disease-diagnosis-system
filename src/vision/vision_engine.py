# 文件路径: WheatAgent/src/vision/vision_engine.py
import os
import glob
from ultralytics import YOLO
import requests
import ssl

# --- SSL 补丁区 ---
ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()
os.environ['ULTRALYTICS_OFFLINE'] = 'true'
_original_get = requests.get
def patched_get(*args, **kwargs):
    kwargs['verify'] = False
    return _original_get(*args, **kwargs)
requests.get = patched_get
# ------------------

class VisionAgent:
    def __init__(self, model_path=None):
        print("👁️ [Vision Agent] 正在初始化...")
        
        # 1. 优先使用传入的路径
        final_model_path = None
        if model_path and os.path.exists(model_path):
            final_model_path = model_path
            print(f"✅ 使用指定模型: {model_path}")
        else:
            # 2. 按优先级搜索模型
            # 优先级1: models/yolov8_wheat.pt (小麦病害专用模型)
            # 优先级2: 最新训练的最佳模型
            # 优先级3: yolov8n.pt (fallback)
            
            search_candidates = [
                # 优先级1: 专用模型目录
                os.path.join(os.getcwd(), "models", "yolov8_wheat.pt"),
                # 优先级2: 进化训练模型
                os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_evolution_v2", "weights", "best.pt"),
                os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_evolution", "weights", "best.pt"),
                os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_experiment2", "weights", "best.pt"),
                os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_experiment", "weights", "best.pt"),
                # 优先级3: 快速测试模型
                os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_quick_test", "weights", "best.pt"),
            ]
            
            # 检查候选模型
            for candidate in search_candidates:
                if os.path.exists(candidate):
                    final_model_path = candidate
                    print(f"✅ 找到小麦病害模型: {candidate}")
                    break
            
            # 如果没有找到，搜索所有best.pt
            if final_model_path is None:
                search_patterns = [
                    os.path.join(os.getcwd(), "runs", "**", "weights", "best.pt"),
                ]
                found_models = []
                for pattern in search_patterns:
                    found_models.extend(glob.glob(pattern, recursive=True))
                
                if found_models:
                    # 按时间排序取最新的
                    best_model = max(found_models, key=os.path.getmtime)
                    print(f"✅ 自动定位最新模型: {best_model}")
                    final_model_path = best_model
            
            # Fallback到官方模型
            if final_model_path is None:
                final_model_path = "yolov8n.pt"
                print("⚠️ 未找到小麦病害模型，使用官方 yolov8n.pt (检测精度将受限)")

        print(f"🚀 加载模型: {os.path.basename(final_model_path)}")
        try:
            self.model = YOLO(final_model_path, task='detect')
            print("✅ 视觉模型就绪！")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.model = YOLO('yolov8n.pt')

    def detect(self, image_path, conf_threshold=0.25, iou_threshold=0.45, save_result=False):
        """
        执行检测，返回格式化的结果列表
        
        根据文档3.1-3.3节，使用改进的YOLOv8进行检测：
        - 动态蛇形卷积捕获细长病斑
        - SPPELAN多尺度特征聚合
        - 超级令牌注意力全局推理
        
        :param image_path: 图像路径
        :param conf_threshold: 置信度阈值 (默认0.25，提高精度)
        :param iou_threshold: NMS IoU阈值 (默认0.45)
        :param save_result: 是否保存可视化结果
        :return: 格式化的检测结果列表 [{name, confidence, bbox, class_id}, ...]
        """
        if not os.path.exists(image_path):
            print(f"❌ 图片不存在: {image_path}")
            return []

        print(f"🔍 视觉扫描中... (图片: {os.path.basename(image_path)}, 置信度阈值: {conf_threshold}, IoU阈值: {iou_threshold})")
        try:
            # 运行推理（使用优化参数）
            results = self.model.predict(
                source=image_path, 
                conf=conf_threshold, 
                iou=iou_threshold,
                save=save_result, 
                verbose=False,
                augment=True,  # 使用TTA增强
                agnostic_nms=True  # 类别无关NMS
            )
            
            # 格式化结果
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
                        
                        # 获取边界框坐标
                        xyxy = box.xyxy[0].cpu().numpy() if hasattr(box.xyxy, 'cpu') else box.xyxy[0]
                        bbox = [float(x) for x in xyxy]
                        
                        # 构建格式化结果
                        formatted_result = {
                            'name': class_name,
                            'confidence': conf,
                            'bbox': bbox,
                            'class_id': cls_id
                        }
                        formatted_results.append(formatted_result)
                        
                        print(f"   目标 {i+1}: {class_name} (置信度: {conf:.2f})")
                else:
                    print(f"🍃 视觉未发现异常")
            else:
                print(f"🍃 视觉未发现异常 (无结果)")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 推理过程出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def detect_and_visualize(self, image_path, conf_threshold=0.25, iou_threshold=0.45, output_path=None):
        """
        执行检测并生成可视化结果（带检测框的图像）
        
        :param image_path: 输入图像路径
        :param conf_threshold: 置信度阈值 (默认0.25)
        :param iou_threshold: NMS IoU阈值 (默认0.45)
        :param output_path: 输出图像路径（可选）
        :return: (检测结果列表, 可视化图像路径)
        """
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # 执行检测
        results = self.detect(image_path, conf_threshold, iou_threshold, save_result=False)
        
        if not results:
            return results, None
        
        try:
            # 打开原始图像
            image = Image.open(image_path).convert('RGB')
            draw = ImageDraw.Draw(image)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # 绘制检测框
            for i, result in enumerate(results):
                bbox = result['bbox']
                name = result['name']
                confidence = result['confidence']
                
                # 绘制矩形框
                draw.rectangle(bbox, outline="red", width=3)
                
                # 绘制标签背景
                label = f"{name} {confidence:.2%}"
                bbox_text = draw.textbbox((0, 0), label, font=font)
                text_width = bbox_text[2] - bbox_text[0]
                text_height = bbox_text[3] - bbox_text[1]
                
                draw.rectangle(
                    [bbox[0], bbox[1] - text_height - 4, bbox[0] + text_width + 4, bbox[1]],
                    fill="red"
                )
                
                # 绘制标签文字
                draw.text((bbox[0] + 2, bbox[1] - text_height - 2), label, fill="white", font=font)
            
            # 保存可视化结果
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