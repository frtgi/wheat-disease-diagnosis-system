# -*- coding: utf-8 -*-
"""
IWDDA V10 模型验证脚本

验证模型加载、推理测试和输出格式
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_model_file(model_path):
    """
    验证模型文件是否存在并检查基本信息
    
    :param model_path: 模型文件路径
    :return: 验证结果字典
    """
    result = {
        "exists": False,
        "file_size_mb": 0,
        "error": None
    }
    
    model_path = Path(model_path)
    if model_path.exists():
        result["exists"] = True
        result["file_size_mb"] = round(model_path.stat().st_size / (1024 * 1024), 2)
    else:
        result["error"] = f"模型文件不存在: {model_path}"
    
    return result


def validate_model_loading(model_path):
    """
    验证模型能否正常加载
    
    :param model_path: 模型文件路径
    :return: 验证结果字典
    """
    result = {
        "loaded": False,
        "model_type": None,
        "num_classes": 0,
        "class_names": [],
        "num_parameters": 0,
        "device": None,
        "error": None
    }
    
    try:
        from ultralytics import YOLO
        
        print("  正在加载模型...")
        model = YOLO(str(model_path))
        
        result["loaded"] = True
        result["model_type"] = "YOLOv8"
        
        if hasattr(model, 'model') and hasattr(model.model, 'names'):
            result["class_names"] = list(model.model.names.values())
            result["num_classes"] = len(result["class_names"])
        
        num_params = sum(p.numel() for p in model.model.parameters())
        result["num_parameters"] = num_params
        
        result["device"] = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"  模型类型: {result['model_type']}")
        print(f"  类别数量: {result['num_classes']}")
        print(f"  参数量: {result['num_parameters']:,}")
        print(f"  设备: {result['device']}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  错误: {e}")
    
    return result


def validate_inference(model_path, test_images):
    """
    验证模型推理功能
    
    :param model_path: 模型文件路径
    :param test_images: 测试图像列表
    :return: 验证结果字典
    """
    result = {
        "success": False,
        "total_images": 0,
        "successful_inferences": 0,
        "avg_inference_time_ms": 0,
        "detection_results": [],
        "error": None
    }
    
    try:
        from ultralytics import YOLO
        
        print("  正在加载模型进行推理测试...")
        model = YOLO(str(model_path))
        
        inference_times = []
        
        for img_path in test_images:
            if not Path(img_path).exists():
                continue
            
            result["total_images"] += 1
            
            try:
                start_time = time.time()
                predictions = model.predict(
                    source=str(img_path),
                    conf=0.25,
                    iou=0.45,
                    verbose=False,
                    device='cuda' if torch.cuda.is_available() else 'cpu'
                )
                inference_time = (time.time() - start_time) * 1000
                inference_times.append(inference_time)
                
                if predictions and len(predictions) > 0:
                    pred = predictions[0]
                    detection_info = {
                        "image": Path(img_path).name,
                        "num_detections": len(pred.boxes) if hasattr(pred, 'boxes') else 0,
                        "inference_time_ms": round(inference_time, 2)
                    }
                    
                    if hasattr(pred, 'boxes') and len(pred.boxes) > 0:
                        boxes = pred.boxes
                        detection_info["detections"] = []
                        
                        for i in range(len(boxes)):
                            box = boxes[i]
                            cls_id = int(box.cls[0]) if hasattr(box, 'cls') else -1
                            conf = float(box.conf[0]) if hasattr(box, 'conf') else 0.0
                            xyxy = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else []
                            
                            detection_info["detections"].append({
                                "class_id": cls_id,
                                "class_name": model.model.names.get(cls_id, "unknown") if cls_id >= 0 else "unknown",
                                "confidence": round(conf, 4),
                                "bbox": [round(x, 2) for x in xyxy]
                            })
                    
                    result["detection_results"].append(detection_info)
                    result["successful_inferences"] += 1
                
            except Exception as e:
                print(f"    推理失败 {img_path}: {e}")
        
        if inference_times:
            result["avg_inference_time_ms"] = round(np.mean(inference_times), 2)
        
        result["success"] = result["successful_inferences"] > 0
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  错误: {e}")
    
    return result


def validate_output_format(detection_results):
    """
    验证检测输出格式是否正确
    
    :param detection_results: 检测结果列表
    :return: 验证结果字典
    """
    result = {
        "valid": False,
        "has_required_fields": False,
        "has_bbox": False,
        "has_confidence": False,
        "has_class_info": False,
        "issues": []
    }
    
    if not detection_results:
        result["issues"].append("没有检测结果")
        return result
    
    required_fields = ["image", "num_detections", "detections"]
    
    for det_result in detection_results:
        missing_fields = [f for f in required_fields if f not in det_result]
        if missing_fields:
            result["issues"].append(f"缺少字段: {missing_fields}")
            return result
    
    result["has_required_fields"] = True
    
    for det_result in detection_results:
        if det_result["num_detections"] > 0:
            for det in det_result.get("detections", []):
                if "bbox" not in det:
                    result["issues"].append("检测结果缺少bbox字段")
                    return result
                if "confidence" not in det:
                    result["issues"].append("检测结果缺少confidence字段")
                    return result
                if "class_id" not in det and "class_name" not in det:
                    result["issues"].append("检测结果缺少类别信息")
                    return result
    
    result["has_bbox"] = True
    result["has_confidence"] = True
    result["has_class_info"] = True
    result["valid"] = True
    
    return result


def validate_map_performance(results_csv_path):
    """
    验证模型mAP性能
    
    :param results_csv_path: 训练结果CSV文件路径
    :return: 验证结果字典
    """
    result = {
        "valid": False,
        "map50": 0,
        "map50_95": 0,
        "precision": 0,
        "recall": 0,
        "target_map50": 0.95,
        "meets_target": False,
        "error": None
    }
    
    try:
        import pandas as pd
        
        df = pd.read_csv(results_csv_path, skipinitialspace=True)
        
        last_row = df.iloc[-1]
        
        result["map50"] = float(last_row.get("metrics/mAP50(B)", 0))
        result["map50_95"] = float(last_row.get("metrics/mAP50-95(B)", 0))
        result["precision"] = float(last_row.get("metrics/precision(B)", 0))
        result["recall"] = float(last_row.get("metrics/recall(B)", 0))
        
        result["meets_target"] = result["map50"] >= result["target_map50"]
        result["valid"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main():
    """
    主验证函数
    """
    print("=" * 70)
    print(" IWDDA V10 视觉检测模块验证")
    print("=" * 70)
    print(f" 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    model_path = Path("D:/Project/WheatAgent/models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt")
    results_csv = Path("D:/Project/WheatAgent/models/wheat_disease_v10_yolov8s/phase1_warmup/results.csv")
    val_images_dir = Path("D:/Project/WheatAgent/datasets/wheat_data_unified/images/val")
    
    test_images = []
    if val_images_dir.exists():
        for ext in ["*.jpg", "*.png"]:
            test_images.extend(list(val_images_dir.glob(ext))[:5])
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "model_path": str(model_path),
        "validation_steps": {}
    }
    
    print("\n[1/4] 验证模型文件...")
    file_result = validate_model_file(model_path)
    validation_results["validation_steps"]["model_file"] = file_result
    
    if file_result["exists"]:
        print(f"  模型文件存在: {file_result['file_size_mb']} MB")
    else:
        print(f"  错误: {file_result['error']}")
    
    print("\n[2/4] 验证模型加载...")
    loading_result = validate_model_loading(model_path)
    validation_results["validation_steps"]["model_loading"] = loading_result
    
    if loading_result["loaded"]:
        print(f"  模型加载成功!")
    else:
        print(f"  错误: {loading_result['error']}")
    
    print("\n[3/4] 验证推理功能...")
    inference_result = validate_inference(model_path, test_images)
    validation_results["validation_steps"]["inference"] = inference_result
    
    print(f"  测试图像数: {inference_result['total_images']}")
    print(f"  成功推理数: {inference_result['successful_inferences']}")
    print(f"  平均推理时间: {inference_result['avg_inference_time_ms']} ms")
    
    if inference_result["detection_results"]:
        print("\n  检测结果示例:")
        for det in inference_result["detection_results"][:2]:
            print(f"    - {det['image']}: {det['num_detections']} 个检测")
            if det.get("detections"):
                for d in det["detections"][:3]:
                    print(f"      {d['class_name']}: {d['confidence']:.2%}")
    
    print("\n[4/4] 验证输出格式...")
    format_result = validate_output_format(inference_result.get("detection_results", []))
    validation_results["validation_steps"]["output_format"] = format_result
    
    if format_result["valid"]:
        print("  输出格式验证通过!")
    else:
        print(f"  问题: {format_result['issues']}")
    
    print("\n[额外] 验证mAP性能...")
    map_result = validate_map_performance(results_csv)
    validation_results["validation_steps"]["map_performance"] = map_result
    
    if map_result["valid"]:
        print(f"  mAP@50: {map_result['map50']:.2%}")
        print(f"  mAP@50-95: {map_result['map50_95']:.2%}")
        print(f"  Precision: {map_result['precision']:.2%}")
        print(f"  Recall: {map_result['recall']:.2%}")
        print(f"  达到目标: {'是' if map_result['meets_target'] else '否'}")
    
    validation_results["overall_status"] = (
        file_result["exists"] and 
        loading_result["loaded"] and 
        inference_result["success"] and 
        format_result["valid"]
    )
    
    output_path = Path("D:/Project/WheatAgent/logs/v10_validation_result.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(" 验证结果汇总")
    print("=" * 70)
    print(f" 模型文件: {'存在' if file_result['exists'] else '不存在'}")
    print(f" 模型加载: {'成功' if loading_result['loaded'] else '失败'}")
    print(f" 推理测试: {'成功' if inference_result['success'] else '失败'}")
    print(f" 输出格式: {'正确' if format_result['valid'] else '有问题'}")
    print(f" mAP@50: {map_result['map50']:.2%} {'(达标)' if map_result.get('meets_target') else ''}")
    print("-" * 70)
    print(f" 整体验证状态: {'通过' if validation_results['overall_status'] else '失败'}")
    print("=" * 70)
    print(f" 详细结果已保存: {output_path}")
    
    return validation_results


if __name__ == "__main__":
    main()
