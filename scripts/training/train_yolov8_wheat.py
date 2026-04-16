# -*- coding: utf-8 -*-
"""
YOLOv8 小麦病害检测模型训练脚本
针对 RTX 3050 Laptop (4GB 显存) 优化
"""
import os
import sys
from pathlib import Path

# 设置项目根目录 (scripts/training -> WheatAgent)
PROJECT_ROOT = Path(__file__).parent.parent.parent
os.chdir(PROJECT_ROOT)

import torch
from ultralytics import YOLO

def main():
    print("=" * 60)
    print("YOLOv8 小麦病害检测模型训练")
    print("=" * 60)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print("=" * 60)
    
    # 数据集配置文件
    data_config = str(PROJECT_ROOT / "configs" / "wheat_disease.yaml")
    
    # 输出目录
    project_dir = str(PROJECT_ROOT / "models")
    experiment_name = "wheat_disease_v10_yolov8s/phase1_warmup"
    
    # 加载预训练模型 (使用本地已下载的权重)
    pretrained_path = PROJECT_ROOT / "yolov8s.pt"
    print(f"\n检查预训练模型: {pretrained_path}")
    print(f"文件存在: {pretrained_path.exists()}")
    
    if pretrained_path.exists():
        print(f"\n加载本地 YOLOv8s 预训练模型...")
        model = YOLO(str(pretrained_path))
    else:
        print("\n加载 YOLOv8s 预训练模型 (从网络下载)...")
        model = YOLO("yolov8s.pt")
    
    # 自动检测设备
    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"\n使用设备: {device}")
    
    # 训练参数 (针对 4GB 显存优化)
    print("\n开始训练...")
    print(f"数据集: {data_config}")
    print(f"输出目录: {project_dir}/{experiment_name}")
    print(f"Epochs: 30")
    print(f"Batch Size: 4")
    print(f"Image Size: 640")
    print("-" * 60)
    
    try:
        results = model.train(
            data=data_config,
            epochs=30,
            imgsz=640,
            batch=4,
            device=device,
            workers=2,
            project=project_dir,
            name=experiment_name,
            exist_ok=True,
            patience=20,
            save=True,
            save_period=5,
            amp=True,
            optimizer="AdamW",
            lr0=0.0005,
            lrf=0.1,
            weight_decay=0.0005,
            warmup_epochs=3,
            mosaic=0.8,
            mixup=0.1,
            hsv_h=0.015,
            hsv_s=0.5,
            hsv_v=0.3,
            degrees=10.0,
            translate=0.1,
            scale=0.5,
            fliplr=0.5,
            verbose=True,
            freeze=10,
        )
        
        print("\n" + "=" * 60)
        print("训练完成!")
        print("=" * 60)
        
        # 打印最终指标
        if hasattr(results, "results_dict"):
            metrics = results.results_dict
            print(f"mAP@50: {metrics.get('metrics/mAP50(B)', 'N/A')}")
            print(f"mAP@50-95: {metrics.get('metrics/mAP50-95(B)', 'N/A')}")
            print(f"Precision: {metrics.get('metrics/precision(B)', 'N/A')}")
            print(f"Recall: {metrics.get('metrics/recall(B)', 'N/A')}")
        
        # 验证模型文件
        weights_dir = PROJECT_ROOT / "models" / "wheat_disease_v10_yolov8s" / "phase1_warmup" / "weights"
        best_pt = weights_dir / "best.pt"
        last_pt = weights_dir / "last.pt"
        
        print("\n模型文件检查:")
        print(f"  best.pt: {'存在' if best_pt.exists() else '不存在'}")
        print(f"  last.pt: {'存在' if last_pt.exists() else '不存在'}")
        
        if best_pt.exists():
            print(f"\n模型大小: {best_pt.stat().st_size / 1024 / 1024:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
