# -*- coding: utf-8 -*-
"""
SerpensGate-YOLOv8 简化训练脚本
直接使用 Phase 2 模型继续训练，优化训练参数
"""
import os
import sys
import yaml
import argparse
import torch
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_environment():
    """
    设置高性能训练环境
    """
    print("=" * 70)
    print("🚀 SerpensGate-YOLOv8 训练环境")
    print("=" * 70)
    
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = (
        'max_split_size_mb:128,'
        'garbage_collection_threshold:0.6,'
        'expandable_segments:True'
    )
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        gpu_name = torch.cuda.get_device_name(0)
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        
        print(f"✅ GPU: {gpu_name}")
        print(f"   显存: {total_memory:.2f} GB")
        
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        print("✅ 性能优化已启用:")
        print("   - cuDNN Benchmark: True")
        print("   - TF32加速: 启用")
        print("   - 混合精度: 启用")
    else:
        print("⚠️ CUDA不可用，将使用CPU训练")
    
    return torch.cuda.is_available()


def train_serpensgate(args):
    """
    执行SerpensGate-YOLOv8训练
    使用优化参数从Phase 2模型继续训练
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        print(f"❌ 错误: {e}")
        print("请确保已安装: pip install ultralytics")
        return None, None
    
    data_config_path = PROJECT_ROOT / "configs/wheat_disease_optimized.yaml"
    params_config_path = PROJECT_ROOT / "configs/training_params.yaml"
    
    if not data_config_path.exists():
        print(f"❌ 数据配置文件不存在: {data_config_path}")
        return None, None
    
    with open(data_config_path, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)
    
    params_config = {}
    if params_config_path.exists():
        with open(params_config_path, 'r', encoding='utf-8') as f:
            params_config = yaml.safe_load(f)
    
    print("\n" + "=" * 70)
    print("📊 SerpensGate-YOLOv8 训练配置")
    print("=" * 70)
    print(f"数据集: {data_config.get('path', 'N/A')}")
    print(f"类别数: {data_config.get('nc', 'N/A')}")
    print(f"基础模型: {args.model}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {args.batch}")
    print(f"图像尺寸: {args.imgsz}")
    
    print("\n🔬 SerpensGate增强策略:")
    print("   - 优化学习率调度")
    print("   - 增强数据增强策略")
    print("   - CIoU损失函数优化")
    print("   - 混合精度训练")
    
    print(f"\n🔧 加载模型: {args.model}")
    model = YOLO(args.model)
    
    train_args = {
        'data': str(data_config_path),
        'epochs': args.epochs,
        'batch': args.batch,
        'imgsz': args.imgsz,
        'optimizer': 'AdamW',
        'lr0': 0.001,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3,
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.1,
        'box': 7.5,
        'cls': 0.5,
        'dfl': 1.5,
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        'degrees': 15.0,
        'translate': 0.1,
        'scale': 0.9,
        'shear': 0.0,
        'perspective': 0.0,
        'flipud': 0.0,
        'fliplr': 0.5,
        'mosaic': 1.0,
        'mixup': 0.2,
        'copy_paste': 0.1,
        'erasing': 0.4,
        'crop_fraction': 1.0,
        'amp': True,
        'cache': 'disk',
        'rect': True,
        'workers': 0,
        'device': args.device,
        'project': str(PROJECT_ROOT / 'runs/detect'),
        'name': 'serpensgate_v2',
        'exist_ok': True,
        'pretrained': True,
        'val': True,
        'plots': True,
        'patience': 15,
        'save_period': 10,
        'verbose': True,
    }
    
    print("\n" + "=" * 70)
    print("🚀 开始SerpensGate-YOLOv8训练")
    print("=" * 70)
    
    start_time = datetime.now()
    results = model.train(**train_args)
    end_time = datetime.now()
    
    training_duration = (end_time - start_time).total_seconds()
    print(f"\n⏱️ 训练完成，总耗时: {training_duration/3600:.2f} 小时")
    
    return model, results


def evaluate_model(model, args):
    """
    评估模型性能
    """
    print("\n" + "=" * 70)
    print("📊 SerpensGate-YOLOv8 模型评估")
    print("=" * 70)
    
    data_yaml = str(PROJECT_ROOT / "configs/wheat_disease_optimized.yaml")
    
    metrics = model.val(
        data=data_yaml,
        imgsz=args.imgsz,
        batch=args.batch,
        conf=0.25,
        iou=0.45,
        device=args.device,
        plots=True
    )
    
    print("\n📈 评估结果:")
    print(f"   mAP@0.5:     {metrics.box.map50:.4f}")
    print(f"   mAP@0.5:0.95: {metrics.box.map:.4f}")
    print(f"   Precision:   {metrics.box.mp:.4f}")
    print(f"   Recall:      {metrics.box.mr:.4f}")
    
    target_map = 0.95
    if metrics.box.map50 >= target_map:
        print(f"\n✅ 达到目标mAP@0.5 ≥ {target_map}")
    else:
        print(f"\n⚠️ 未达到目标mAP@0.5 ≥ {target_map}")
        print(f"   当前: {metrics.box.map50:.4f}, 差距: {target_map - metrics.box.map50:.4f}")
    
    import json
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": "SerpensGate-YOLOv8-v2",
        "enhancements": ["OptimizedLR", "EnhancedAugmentation", "CIoU", "AMP"],
        "configuration": {
            "batch": args.batch,
            "imgsz": args.imgsz,
            "epochs": args.epochs
        },
        "metrics": {
            "mAP50": float(metrics.box.map50),
            "mAP": float(metrics.box.map),
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
        }
    }
    
    report_path = str(PROJECT_ROOT / "runs/detect/serpensgate_v2/serpensgate_evaluation.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 评估报告已保存: {report_path}")
    
    return metrics


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SerpensGate-YOLOv8 简化训练脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--model', type=str, 
                        default=str(PROJECT_ROOT / 'models/wheat_disease_v5_optimized_phase2/weights/best.pt'),
                        help='基础模型路径')
    parser.add_argument('--epochs', type=int, default=50,
                        help='训练轮数')
    parser.add_argument('--batch', type=int, default=8,
                        help='批次大小')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='图像尺寸')
    parser.add_argument('--device', type=str, default='0',
                        help='设备')
    parser.add_argument('--eval', action='store_true',
                        help='训练后评估模型')
    
    args = parser.parse_args()
    
    setup_environment()
    
    start_time = datetime.now()
    model, results = train_serpensgate(args)
    end_time = datetime.now()
    
    if model is None:
        print("❌ 训练失败")
        return
    
    if args.eval:
        evaluate_model(model, args)
    
    print("\n" + "=" * 70)
    print("✅ SerpensGate-YOLOv8 训练完成！")
    print("=" * 70)
    print(f"模型保存位置: {PROJECT_ROOT / 'runs/detect/serpensgate_v2/weights/best.pt'}")
    print(f"总耗时: {(end_time - start_time).total_seconds()/3600:.2f} 小时")
    print("=" * 70)


if __name__ == "__main__":
    main()
