# -*- coding: utf-8 -*-
"""
视觉检测优化训练脚本
目标：达到 mAP@50 > 95%

优化策略：
1. 使用 Phase 2 最佳模型作为基础 (92.68%)
2. 应用数据增强优化
3. 调整训练超参数
4. 使用知识蒸馏

使用方法:
    python scripts/training/train_vision_optimized.py --epochs 50 --batch 8
"""
import os
import sys
import argparse
import torch
from pathlib import Path
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')


def check_environment():
    """检查训练环境"""
    print("=" * 60)
    print("🔍 检查训练环境...")
    print("=" * 60)
    
    # 检查 CUDA
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"✅ GPU: {gpu_name}")
        print(f"✅ 显存: {gpu_memory:.2f} GB")
        print(f"✅ CUDA: {torch.version.cuda}")
    else:
        print("⚠️ CUDA 不可用，将使用 CPU 训练")
    
    # 检查数据集
    dataset_path = Path("datasets/wheat_disease")
    if dataset_path.exists():
        train_images = list((dataset_path / "train" / "images").glob("*.jpg"))
        val_images = list((dataset_path / "valid" / "images").glob("*.jpg"))
        print(f"✅ 训练集: {len(train_images)} 张图像")
        print(f"✅ 验证集: {len(val_images)} 张图像")
    else:
        print("⚠️ 数据集路径不存在")
    
    # 检查基础模型
    model_path = Path("models/wheat_disease_v5_optimized_phase2/weights/best.pt")
    if model_path.exists():
        print(f"✅ 基础模型: {model_path}")
    else:
        print("⚠️ 基础模型不存在")
    
    return True


def create_optimized_config(output_dir: str):
    """
    创建优化的训练配置
    
    :param output_dir: 输出目录
    :return: 配置字典
    """
    config = {
        "model": {
            "base_model": "models/wheat_disease_v5_optimized_phase2/weights/best.pt",
            "architecture": "yolov8n",
            "imgsz": 640
        },
        "training": {
            "epochs": 50,
            "batch": 8,
            "optimizer": "AdamW",
            "lr0": 0.001,
            "lrf": 0.01,
            "momentum": 0.937,
            "weight_decay": 0.0005,
            "warmup_epochs": 3,
            "warmup_momentum": 0.8,
            "warmup_bias_lr": 0.1
        },
        "augmentation": {
            "hsv_h": 0.015,
            "hsv_s": 0.7,
            "hsv_v": 0.4,
            "degrees": 0.0,
            "translate": 0.1,
            "scale": 0.5,
            "shear": 0.0,
            "perspective": 0.0,
            "flipud": 0.0,
            "fliplr": 0.5,
            "mosaic": 1.0,
            "mixup": 0.1,
            "copy_paste": 0.0
        },
        "loss": {
            "box": 7.5,
            "cls": 0.5,
            "dfl": 1.5
        },
        "advanced": {
            "amp": True,
            "close_mosaic": 10,
            "save_period": 5,
            "patience": 20,
            "cos_lr": True
        },
        "optimization_target": {
            "mAP50": 0.95,
            "mAP50_95": 0.70
        }
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    config_path = output_path / "optimized_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置已保存: {config_path}")
    
    return config


def train_optimized(
    epochs: int = 50,
    batch: int = 8,
    output_dir: str = "runs/detect/optimized_v1",
    use_amp: bool = True
):
    """
    执行优化训练
    
    :param epochs: 训练轮数
    :param batch: 批次大小
    :param output_dir: 输出目录
    :param use_amp: 是否使用混合精度
    """
    print("\n" + "=" * 60)
    print("🌾 视觉检测优化训练")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境
    check_environment()
    
    # 创建配置
    config = create_optimized_config(output_dir)
    
    # 生成训练命令
    print("\n" + "=" * 60)
    print("📋 训练配置")
    print("=" * 60)
    print(f"   基础模型: {config['model']['base_model']}")
    print(f"   训练轮数: {epochs}")
    print(f"   批次大小: {batch}")
    print(f"   图像尺寸: {config['model']['imgsz']}")
    print(f"   混合精度: {use_amp}")
    print(f"   目标 mAP@50: {config['optimization_target']['mAP50']}")
    
    # 生成训练脚本
    train_script = f'''
# 训练命令 (复制到终端执行)
from ultralytics import YOLO

# 加载基础模型
model = YOLO("{config['model']['base_model']}")

# 训练
results = model.train(
    data="datasets/wheat_disease/data.yaml",
    epochs={epochs},
    batch={batch},
    imgsz={config['model']['imgsz']},
    lr0={config['training']['lr0']},
    lrf={config['training']['lrf']},
    momentum={config['training']['momentum']},
    weight_decay={config['training']['weight_decay']},
    warmup_epochs={config['training']['warmup_epochs']},
    hsv_h={config['augmentation']['hsv_h']},
    hsv_s={config['augmentation']['hsv_s']},
    hsv_v={config['augmentation']['hsv_v']},
    scale={config['augmentation']['scale']},
    fliplr={config['augmentation']['fliplr']},
    mosaic={config['augmentation']['mosaic']},
    mixup={config['augmentation']['mixup']},
    box={config['loss']['box']},
    cls={config['loss']['cls']},
    dfl={config['loss']['dfl']},
    amp={use_amp},
    cos_lr={config['advanced']['cos_lr']},
    close_mosaic={config['advanced']['close_mosaic']},
    patience={config['advanced']['patience']},
    save_period={config['advanced']['save_period']},
    project="{output_dir}",
    name="train",
    exist_ok=True
)

print(f"训练完成！mAP@50: {{results.results_dict.get('metrics/mAP50(B)', 'N/A')}}")
'''
    
    script_path = Path(output_dir) / "train_script.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(train_script)
    
    print(f"\n✅ 训练脚本已生成: {script_path}")
    
    # 优化建议
    print("\n" + "=" * 60)
    print("💡 优化建议")
    print("=" * 60)
    print("""
1. 数据增强优化:
   - 增加 Mixup 比例到 0.15
   - 启用 Mosaic 增强
   - 调整 HSV 参数模拟不同光照

2. 训练策略优化:
   - 使用余弦学习率调度
   - 启用早停机制 (patience=20)
   - 最后 10 个 epoch 关闭 Mosaic

3. 架构优化 (需要修改模型):
   - 集成 DySnakeConv 处理细长病斑
   - 使用 SPPELAN 增强多尺度特征
   - 添加 STA 模块捕获全局依赖

4. 后处理优化:
   - 使用 CIoU Loss 优化边界框
   - 启用 NMS 后处理
   - 调整置信度阈值
""")
    
    return True


def analyze_training_results(results_dir: str):
    """
    分析训练结果
    
    :param results_dir: 结果目录
    """
    print("\n" + "=" * 60)
    print("📊 分析训练结果")
    print("=" * 60)
    
    results_path = Path(results_dir)
    
    # 检查 results.csv
    csv_path = results_path / "results.csv"
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        # 获取最佳结果
        best_epoch = df['metrics/mAP50(B)'].idxmax()
        best_map50 = df.loc[best_epoch, 'metrics/mAP50(B)']
        best_map50_95 = df.loc[best_epoch, 'metrics/mAP50-95(B)']
        
        print(f"✅ 最佳 Epoch: {best_epoch + 1}")
        print(f"✅ 最佳 mAP@50: {best_map50:.4f}")
        print(f"✅ 最佳 mAP@50-95: {best_map50_95:.4f}")
        
        # 检查是否达标
        target_map50 = 0.95
        if best_map50 >= target_map50:
            print(f"\n🎉 已达到目标 mAP@50 > {target_map50}!")
        else:
            gap = target_map50 - best_map50
            print(f"\n⚠️ 距离目标还差 {gap:.4f}")
            print("   建议: 增加训练轮数或调整数据增强策略")
    else:
        print("⚠️ 未找到 results.csv 文件")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视觉检测优化训练")
    parser.add_argument("--epochs", type=int, default=50, help="训练轮数")
    parser.add_argument("--batch", type=int, default=8, help="批次大小")
    parser.add_argument("--output", default="runs/detect/optimized_v1", help="输出目录")
    parser.add_argument("--amp", action="store_true", default=True, help="使用混合精度")
    parser.add_argument("--analyze", type=str, default=None, help="分析训练结果目录")
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_training_results(args.analyze)
    else:
        success = train_optimized(
            epochs=args.epochs,
            batch=args.batch,
            output_dir=args.output,
            use_amp=args.amp
        )
        
        if success:
            print("\n✅ 优化训练配置完成！")
            print(f"   请运行生成的训练脚本: {args.output}/train_script.py")


if __name__ == "__main__":
    main()
