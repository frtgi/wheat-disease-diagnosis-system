# -*- coding: utf-8 -*-
"""
IWDDA 模型评估脚本

评估模型性能指标:
- mAP@0.5
- mAP@0.5:0.95
- CIoU
- 推理速度
- 模型大小
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision.vision_engine import VisionAgent
from src.diagnosis.diagnosis_engine import create_diagnosis_engine


def evaluate_detection_metrics(model_path, data_path, conf_threshold=0.25):
    """
    评估检测指标
    
    :param model_path: 模型路径
    :param data_path: 数据路径
    :param conf_threshold: 置信度阈值
    :return: 评估结果
    """
    print("\n📊 评估检测指标...")
    
    results = {
        "mAP@0.5": 0.0,
        "mAP@0.5:0.95": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0
    }
    
    try:
        from ultralytics import YOLO
        
        model = YOLO(model_path)
        
        data_yaml = Path(data_path) / "dataset.yaml"
        if not data_yaml.exists():
            data_yaml = Path(data_path) / "wheat_disease.yaml"
        if not data_yaml.exists():
            data_yaml = Path("configs") / "wheat_disease.yaml"
        if not data_yaml.exists():
            data_yaml = Path(data_path)
        
        val_results = model.val(
            data=str(data_yaml),
            conf=conf_threshold,
            iou=0.45,
            device='cuda' if torch.cuda.is_available() else 'cpu',
            verbose=False
        )
        
        results["mAP@0.5"] = float(val_results.box.map50) if hasattr(val_results.box, 'map50') else 0.0
        results["mAP@0.5:0.95"] = float(val_results.box.map) if hasattr(val_results.box, 'map') else 0.0
        results["precision"] = float(val_results.box.mp) if hasattr(val_results.box, 'mp') else 0.0
        results["recall"] = float(val_results.box.mr) if hasattr(val_results.box, 'mr') else 0.0
        
        if results["precision"] + results["recall"] > 0:
            results["f1_score"] = 2 * results["precision"] * results["recall"] / (results["precision"] + results["recall"])
        
    except Exception as e:
        print(f"⚠️ 检测评估失败: {e}")
    
    return results


def evaluate_inference_speed(model_path, num_iterations=100):
    """
    评估推理速度
    
    :param model_path: 模型路径
    :param num_iterations: 迭代次数
    :return: 速度结果
    """
    print("\n⏱️ 评估推理速度...")
    
    results = {
        "avg_inference_time_ms": 0.0,
        "fps": 0.0,
        "min_time_ms": 0.0,
        "max_time_ms": 0.0
    }
    
    try:
        from ultralytics import YOLO
        
        model = YOLO(model_path)
        
        dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        for _ in range(10):
            model.predict(dummy_image, verbose=False)
        
        times = []
        for _ in range(num_iterations):
            start = time.time()
            model.predict(dummy_image, verbose=False)
            times.append((time.time() - start) * 1000)
        
        results["avg_inference_time_ms"] = float(np.mean(times))
        results["fps"] = 1000.0 / results["avg_inference_time_ms"]
        results["min_time_ms"] = float(np.min(times))
        results["max_time_ms"] = float(np.max(times))
        
    except Exception as e:
        print(f"⚠️ 速度评估失败: {e}")
    
    return results


def evaluate_model_size(model_path):
    """
    评估模型大小
    
    :param model_path: 模型路径
    :return: 大小结果
    """
    print("\n📦 评估模型大小...")
    
    results = {
        "model_size_mb": 0.0,
        "num_parameters": 0
    }
    
    try:
        model_path = Path(model_path)
        if model_path.exists():
            results["model_size_mb"] = model_path.stat().st_size / (1024 * 1024)
        
        from ultralytics import YOLO
        model = YOLO(str(model_path))
        
        num_params = sum(p.numel() for p in model.model.parameters())
        results["num_parameters"] = num_params
        
    except Exception as e:
        print(f"⚠️ 模型大小评估失败: {e}")
    
    return results


def evaluate_diagnosis_quality(test_images_dir):
    """
    评估诊断质量
    
    :param test_images_dir: 测试图像目录
    :return: 诊断质量结果
    """
    print("\n🏥 评估诊断质量...")
    
    results = {
        "total_images": 0,
        "successful_diagnoses": 0,
        "avg_confidence": 0.0,
        "disease_distribution": {}
    }
    
    try:
        engine = create_diagnosis_engine({
            "load_vision": True,
            "load_knowledge": False
        })
        
        test_dir = Path(test_images_dir)
        if not test_dir.exists():
            print(f"⚠️ 测试目录不存在: {test_images_dir}")
            return results
        
        image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
        
        confidences = []
        disease_counts = {}
        
        for image_path in image_files[:50]:
            try:
                result = engine.diagnose(str(image_path))
                
                results["total_images"] += 1
                results["successful_diagnoses"] += 1
                
                confidences.append(result.confidence)
                
                disease = result.disease_name
                disease_counts[disease] = disease_counts.get(disease, 0) + 1
                
            except Exception as e:
                results["total_images"] += 1
        
        if confidences:
            results["avg_confidence"] = float(np.mean(confidences))
        
        results["disease_distribution"] = disease_counts
        
    except Exception as e:
        print(f"⚠️ 诊断质量评估失败: {e}")
    
    return results


def generate_evaluation_report(output_path, results):
    """
    生成评估报告
    
    :param output_path: 输出路径
    :param results: 评估结果
    """
    report = f"""# IWDDA 模型评估报告

## 📊 评估概览

| 项目 | 内容 |
|------|------|
| 评估日期 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 评估环境 | {'GPU' if torch.cuda.is_available() else 'CPU'} |

---

## 🎯 检测性能

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| mAP@0.5 | {results['detection']['mAP@0.5']:.4f} | > 0.95 | {'✅' if results['detection']['mAP@0.5'] > 0.95 else '⚠️'} |
| mAP@0.5:0.95 | {results['detection']['mAP@0.5:0.95']:.4f} | > 0.70 | {'✅' if results['detection']['mAP@0.5:0.95'] > 0.70 else '⚠️'} |
| Precision | {results['detection']['precision']:.4f} | > 0.90 | {'✅' if results['detection']['precision'] > 0.90 else '⚠️'} |
| Recall | {results['detection']['recall']:.4f} | > 0.90 | {'✅' if results['detection']['recall'] > 0.90 else '⚠️'} |
| F1-Score | {results['detection']['f1_score']:.4f} | > 0.90 | {'✅' if results['detection']['f1_score'] > 0.90 else '⚠️'} |

---

## ⏱️ 推理速度

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| 平均推理时间 | {results['speed']['avg_inference_time_ms']:.2f} ms | < 100 ms | {'✅' if results['speed']['avg_inference_time_ms'] < 100 else '⚠️'} |
| FPS | {results['speed']['fps']:.1f} | > 10 | {'✅' if results['speed']['fps'] > 10 else '⚠️'} |
| 最小时间 | {results['speed']['min_time_ms']:.2f} ms | - | - |
| 最大时间 | {results['speed']['max_time_ms']:.2f} ms | - | - |

---

## 📦 模型大小

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| 模型大小 | {results['size']['model_size_mb']:.2f} MB | < 50 MB | {'✅' if results['size']['model_size_mb'] < 50 else '⚠️'} |
| 参数量 | {results['size']['num_parameters']:,} | - | - |

---

## 🏥 诊断质量

| 指标 | 当前值 |
|------|--------|
| 测试图像数 | {results['diagnosis']['total_images']} |
| 成功诊断数 | {results['diagnosis']['successful_diagnoses']} |
| 平均置信度 | {results['diagnosis']['avg_confidence']:.2%} |

### 病害分布

"""
    for disease, count in results['diagnosis']['disease_distribution'].items():
        report += f"- {disease}: {count}\n"
    
    report += f"""
---

## ✅ 结论

评估完成，详细结果见上表。

---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 评估报告已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='IWDDA模型评估')
    parser.add_argument('--model', type=str, default='models/wheat_disease_v3/weights/best.pt', help='模型路径')
    parser.add_argument('--data', type=str, default='datasets/wheat_data_unified', help='数据路径')
    parser.add_argument('--output', type=str, default='docs/EVALUATION_REPORT.md', help='输出报告路径')
    parser.add_argument('--iterations', type=int, default=100, help='推理速度测试迭代次数')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 IWDDA 模型评估")
    print("=" * 60)
    
    results = {
        "detection": evaluate_detection_metrics(args.model, args.data),
        "speed": evaluate_inference_speed(args.model, args.iterations),
        "size": evaluate_model_size(args.model),
        "diagnosis": evaluate_diagnosis_quality(Path(args.data) / "images" / "val")
    }
    
    generate_evaluation_report(args.output, results)
    
    print("\n" + "=" * 60)
    print("✅ 评估完成")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
