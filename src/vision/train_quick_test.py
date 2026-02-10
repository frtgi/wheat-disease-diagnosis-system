# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/src/vision/train_quick_test.py
"""
快速测试训练脚本
使用更少的 epochs 和更小的 batch size 进行快速测试
"""

import os
import sys
from ultralytics import YOLO

def train_quick_test(epochs=5, batch=8, imgsz=256, device='auto'):
    """
    快速测试训练
    :param epochs: 训练轮数（默认 5）
    :param batch: 批次大小（默认 8）
    :param imgsz: 图像大小（默认 256）
    :param device: 设备（默认 auto）
    """
    print("=" * 60)
    print("🚀 [IWDDA Quick Test Training] 启动快速测试训练")
    print("=" * 60)
    
    # 检查设备
    if device == 'auto':
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        if device == 'cpu':
            print("⚠️ 警告：正在使用 CPU 训练，速度将非常慢！")
    
    # 加载预训练模型
    model_path = "yolov8n.pt"
    print(f"📥 加载预训练模型: {model_path}")
    
    model = YOLO(model_path)
    
    # 训练配置
    print(f"🎯 开始训练 (Device={device})...")
    print(f"   Epochs: {epochs}")
    print(f"   Batch Size: {batch}")
    print(f"   Image Size: {imgsz}")
    print(f"   Data: configs/wheat_disease.yaml")
    
    results = model.train(
        data='configs/wheat_disease.yaml',
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=5,
        device=device,
        project='runs/detect/runs/train',
        name='wheat_quick_test',
        exist_ok=True,
        pretrained=True,
        optimizer='SGD',
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=1.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.15,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.0,
        flipud=0.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        erasing=0.4,
        crop_fraction=1.0,
        close_mosaic=10,
        plots=True,
        save=True,
        save_period=5,
        val=True,
        workers=2
    )
    
    print("\n✅ 训练完成！")
    print(f"📊 最佳模型保存在: {results.save_dir}")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="快速测试训练")
    parser.add_argument('--epochs', type=int, default=5, help='训练轮数')
    parser.add_argument('--batch', type=int, default=8, help='批次大小')
    parser.add_argument('--imgsz', type=int, default=256, help='图像大小')
    parser.add_argument('--device', type=str, default='auto', help='设备')
    
    args = parser.parse_args()
    
    train_quick_test(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device
    )
