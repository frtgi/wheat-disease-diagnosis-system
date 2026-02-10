# -*- coding: utf-8 -*-
"""
小麦病害检测模型训练脚本
使用YOLOv8训练专用的小麦病害检测模型
"""
import os
import sys
import torch
from ultralytics import YOLO

def train_wheat_disease_model():
    """训练小麦病害检测模型"""
    print("=" * 70)
    print("🌾 小麦病害检测模型训练")
    print("=" * 70)
    
    # 1. 检查设备
    print("\n[1/4] 检查训练设备...")
    if torch.cuda.is_available():
        device = 0
        device_name = torch.cuda.get_device_name(0)
        print(f"   ✅ 使用GPU: {device_name}")
        print(f"   📊 GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        device = 'cpu'
        print("   ⚠️ 使用CPU训练（速度较慢）")
    
    # 2. 检查数据集
    print("\n[2/4] 检查数据集...")
    dataset_path = os.path.join(os.getcwd(), "datasets", "wheat_data")
    if not os.path.exists(dataset_path):
        print(f"   ❌ 数据集不存在: {dataset_path}")
        print("   💡 请先准备数据集")
        return False
    
    # 统计图像数量
    train_images = os.path.join(dataset_path, "images", "train")
    if os.path.exists(train_images):
        num_images = len([f for f in os.listdir(train_images) if f.endswith(('.png', '.jpg', '.jpeg'))])
        print(f"   ✅ 找到 {num_images} 张训练图像")
    else:
        print(f"   ❌ 训练图像目录不存在")
        return False
    
    # 3. 加载模型
    print("\n[3/4] 加载预训练模型...")
    
    # 检查是否有之前的训练结果
    existing_models = [
        os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_evolution_v2", "weights", "best.pt"),
        os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_evolution", "weights", "best.pt"),
        os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_experiment2", "weights", "best.pt"),
    ]
    
    model_loaded = False
    for model_path in existing_models:
        if os.path.exists(model_path):
            print(f"   ✅ 加载已有模型: {model_path}")
            model = YOLO(model_path)
            model_loaded = True
            break
    
    if not model_loaded:
        print("   📝 加载YOLOv8n预训练模型（从头训练）")
        model = YOLO('yolov8n.pt')
    
    # 4. 开始训练
    print("\n[4/4] 开始训练...")
    print("   配置:")
    print("   - 数据配置: configs/wheat_disease.yaml")
    print("   - 图像尺寸: 640")
    print("   - 训练轮数: 50")
    print("   - Batch大小: 16")
    print("   - 设备:", device)
    
    try:
        results = model.train(
            data='configs/wheat_disease.yaml',
            epochs=50,
            imgsz=640,
            batch=16,
            workers=4,
            project='runs/detect/runs/train',
            name='wheat_final',
            exist_ok=True,
            patience=10,
            device=device,
            verbose=True,
            # 优化参数
            lr0=0.01,           # 初始学习率
            lrf=0.01,           # 最终学习率
            momentum=0.937,     # 动量
            weight_decay=0.0005, # 权重衰减
            # 数据增强
            hsv_h=0.015,        # HSV色调增强
            hsv_s=0.7,          # HSV饱和度增强
            hsv_v=0.4,          # HSV亮度增强
            degrees=0.0,        # 旋转角度
            translate=0.1,      # 平移
            scale=0.5,          # 缩放
            shear=0.0,          # 剪切
            perspective=0.0,    # 透视
            flipud=0.0,         # 上下翻转
            fliplr=0.5,         # 左右翻转
            mosaic=1.0,         # Mosaic增强
            mixup=0.0,          # Mixup增强
            copy_paste=0.0,     # Copy-paste增强
        )
        
        print("\n" + "=" * 70)
        print("✅ 训练完成！")
        print(f"   模型保存路径: {results.save_dir}")
        print(f"   最佳模型: {os.path.join(results.save_dir, 'weights', 'best.pt')}")
        print("=" * 70)
        
        # 复制模型到models目录
        import shutil
        best_model = os.path.join(results.save_dir, 'weights', 'best.pt')
        target_path = os.path.join(os.getcwd(), 'models', 'yolov8_wheat.pt')
        
        if os.path.exists(best_model):
            shutil.copy2(best_model, target_path)
            print(f"\n📦 模型已复制到: {target_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = train_wheat_disease_model()
    sys.exit(0 if success else 1)
