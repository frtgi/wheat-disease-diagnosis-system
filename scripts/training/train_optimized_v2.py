# -*- coding: utf-8 -*-
"""
数字麦病专家 - 优化版训练脚本 V2
针对RTX 3050 4GB显存深度优化

优化目标:
1. 显存利用率: 16% -> 60-70%
2. 训练速度提升: 50%+
3. 保持/提升准确率

使用方法:
    python train_optimized_v2.py --auto-batch --epochs 100
"""

import os
import sys
import yaml
import argparse
import torch
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.training.memory_optimizer import MemoryOptimizer


def setup_optimized_environment():
    """
    设置优化的训练环境
    
    配置CUDA和PyTorch环境以最大化训练性能
    """
    print("=" * 70)
    print("🔧 数字麦病专家 - 优化训练环境设置")
    print("=" * 70)
    
    # 显存分配器优化
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = (
        'max_split_size_mb:128,'
        'garbage_collection_threshold:0.6,'
        'expandable_segments:True'
    )
    
    # CUDA优化
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    
    if torch.cuda.is_available():
        # 清空缓存
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # 打印GPU信息
        gpu_name = torch.cuda.get_device_name(0)
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ CUDA可用: {gpu_name}")
        print(f"   总显存: {total_memory:.2f} GB")
        
        # 启用优化选项
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        print("✅ CUDA优化已启用:")
        print("   - cudnn.benchmark: True")
        print("   - TF32加速: 启用")
    else:
        print("⚠️ CUDA不可用，将使用CPU训练")
    
    # 创建输出目录
    os.makedirs("runs/detect", exist_ok=True)
    os.makedirs("runs/detect/optimized_v2", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    return torch.cuda.is_available()


def load_configs():
    """
    加载数据集配置和训练参数配置
    
    Returns:
        data_config: 数据集配置
        params_config: 训练参数配置
    """
    # 优先使用优化版配置
    params_config_path = "configs/training_params_optimized.yaml"
    if not os.path.exists(params_config_path):
        params_config_path = "configs/training_params.yaml"
    
    data_config_path = "configs/wheat_disease_optimized.yaml"
    
    with open(data_config_path, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)
    
    with open(params_config_path, 'r', encoding='utf-8') as f:
        params_config = yaml.safe_load(f)
    
    return data_config, params_config


def train_phase(
    model,
    data_yaml: str,
    phase_config: Dict,
    phase_name: str,
    device: str = '0'
) -> None:
    """
    执行单个训练阶段
    
    分阶段训练策略，每个阶段使用不同的超参数
    
    Args:
        model: YOLO模型
        data_yaml: 数据配置文件路径
        phase_config: 阶段配置
        phase_name: 阶段名称
        device: 设备
    """
    print(f"\n{'='*70}")
    print(f"🚀 {phase_name}")
    print(f"{'='*70}")
    print(f"Epochs: {phase_config['epochs']}")
    print(f"Batch: {phase_config['batch']}")
    print(f"LR: {phase_config['lr0']}")
    print(f"Mosaic: {phase_config.get('mosaic', 1.0)}")
    print(f"Enhanced: {phase_config.get('enhanced', False)}")
    
    # 构建训练参数
    train_args = {
        'data': data_yaml,
        'epochs': phase_config['epochs'],
        'batch': phase_config['batch'],
        'imgsz': phase_config.get('imgsz', 640),
        'optimizer': phase_config.get('optimizer', 'AdamW'),
        'lr0': phase_config['lr0'],
        'lrf': phase_config.get('lrf', 0.01),
        'momentum': phase_config.get('momentum', 0.937),
        'weight_decay': phase_config.get('weight_decay', 0.0005),
        'warmup_epochs': phase_config.get('warmup_epochs', 2),
        'mosaic': phase_config.get('mosaic', 1.0),
        'mixup': phase_config.get('mixup', 0.2),
        'amp': True,
        'cache': True,
        'rect': True,
        'workers': 0,
        'device': device,
        'project': 'runs/detect',
        'name': 'optimized_v2',
        'exist_ok': True,
        'pretrained': True,
        'val': True,
        'plots': True,
        'patience': phase_config.get('patience', 20),
    }
    
    # 执行训练
    results = model.train(**train_args)
    
    return results


def train_with_phases(args):
    """
    执行分阶段训练
    
    三阶段训练策略:
    1. 快速收敛阶段: 大batch，高学习率，禁用增强模块
    2. 稳定优化阶段: 中等batch，启用增强模块
    3. 精细调整阶段: 小batch，低学习率，关闭高级增强
    
    Args:
        args: 命令行参数
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        print(f"❌ 错误: {e}")
        print("请确保已安装: pip install ultralytics")
        return None, None
    
    # 加载配置
    data_config, params_config = load_configs()
    
    print("\n" + "=" * 70)
    print("📊 训练配置")
    print("=" * 70)
    print(f"数据集: {data_config['path']}")
    print(f"类别数: {data_config['nc']}")
    print(f"基础模型: {args.model}")
    
    # 自动检测最优batch
    optimal_batch = args.batch
    if args.auto_batch and torch.cuda.is_available():
        optimizer = MemoryOptimizer(target_utilization=0.65)
        optimal_batch = optimizer.find_optimal_batch_size(
            YOLO, img_size=args.imgsz, start_batch=8, max_batch=48
        )
        print(f"\n🎯 自动检测最优batch: {optimal_batch}")
    
    # 加载模型
    print(f"\n🔧 加载模型: {args.model}")
    model = YOLO(args.model)
    
    # 构建数据配置路径
    data_yaml = os.path.abspath("configs/wheat_disease_optimized.yaml")
    
    # 获取阶段配置
    phases = params_config.get('phases', {})
    
    # 阶段1: 快速收敛
    if not args.skip_phase1:
        phase1_config = phases.get('phase1', {
            'epochs': 30,
            'batch': optimal_batch,
            'lr0': 0.002,
            'optimizer': 'AdamW',
            'mosaic': 1.0,
            'mixup': 0.2,
            'enhanced': False,
            'imgsz': args.imgsz
        })
        # 使用检测到的batch
        phase1_config['batch'] = min(optimal_batch + 8, 32)  # 阶段1使用更大batch
        
        train_phase(model, data_yaml, phase1_config, "阶段1: 快速收敛", args.device)
    
    # 阶段2: 稳定优化
    if not args.skip_phase2:
        phase2_config = phases.get('phase2', {
            'epochs': 50,
            'batch': optimal_batch,
            'lr0': 0.001,
            'optimizer': 'AdamW',
            'mosaic': 0.8,
            'mixup': 0.1,
            'enhanced': True,
            'imgsz': args.imgsz
        })
        phase2_config['batch'] = optimal_batch
        
        train_phase(model, data_yaml, phase2_config, "阶段2: 稳定优化", args.device)
    
    # 阶段3: 精细调整
    if not args.skip_phase3 and args.epochs > 80:
        phase3_config = phases.get('phase3', {
            'epochs': 20,
            'batch': max(optimal_batch - 8, 8),
            'lr0': 0.0005,
            'optimizer': 'AdamW',
            'mosaic': 0.0,
            'mixup': 0.0,
            'enhanced': True,
            'imgsz': args.imgsz
        })
        
        train_phase(model, data_yaml, phase3_config, "阶段3: 精细调整", args.device)
    
    return model


def evaluate_model(model, args):
    """
    评估模型性能
    
    Args:
        model: 训练好的模型
        args: 命令行参数
    """
    print("\n" + "=" * 70)
    print("📊 模型评估")
    print("=" * 70)
    
    data_yaml = os.path.abspath("configs/wheat_disease_optimized.yaml")
    
    metrics = model.val(
        data=data_yaml,
        imgsz=args.imgsz,
        batch=args.batch,
        conf=0.25,
        iou=0.45,
        device=args.device,
        plots=True
    )
    
    # 打印关键指标
    print("\n评估结果:")
    print(f"   mAP@0.5:     {metrics.box.map50:.4f}")
    print(f"   mAP@0.5:0.95: {metrics.box.map:.4f}")
    print(f"   Precision:   {metrics.box.mp:.4f}")
    print(f"   Recall:      {metrics.box.mr:.4f}")
    
    # 保存评估报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
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
    
    import json
    report_path = "runs/detect/optimized_v2/evaluation_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 评估报告已保存: {report_path}")
    
    return metrics


def export_model(model, formats=None):
    """
    导出模型到不同格式
    
    Args:
        model: 训练好的模型
        formats: 导出格式列表
    """
    if formats is None:
        formats = ['onnx']
    
    print("\n" + "=" * 70)
    print("📦 导出模型")
    print("=" * 70)
    
    for fmt in formats:
        try:
            print(f"\n导出 {fmt.upper()} 格式...")
            
            if fmt == 'onnx':
                model.export(format='onnx', dynamic=True, simplify=True)
            elif fmt == 'torchscript':
                model.export(format='torchscript')
            elif fmt == 'engine':
                model.export(format='engine', half=True)
            else:
                model.export(format=fmt)
            
            print(f"✅ {fmt.upper()} 导出成功")
        except Exception as e:
            print(f"⚠️ {fmt.upper()} 导出失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='数字麦病专家 - 优化版训练脚本 V2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 自动检测最优batch并训练
  python train_optimized_v2.py --auto-batch --epochs 100

  # 使用指定batch训练
  python train_optimized_v2.py --batch 24 --epochs 100

  # 仅执行特定阶段
  python train_optimized_v2.py --auto-batch --skip-phase2 --skip-phase3

  # 训练并导出模型
  python train_optimized_v2.py --auto-batch --export onnx,engine

优化特性:
  - 自动显存优化，目标利用率65%
  - 三阶段训练策略
  - 分阶段数据增强调整
  - Windows下workers=0优化
        """
    )
    
    # 模型参数
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                        help='基础模型路径 (默认: yolov8n.pt)')
    
    # 训练参数
    parser.add_argument('--epochs', type=int, default=100,
                        help='总训练轮数 (默认: 100)')
    parser.add_argument('--batch', type=int, default=16,
                        help='批次大小 (默认: 16，使用--auto-batch自动检测)')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='图像尺寸 (默认: 640)')
    parser.add_argument('--device', type=str, default='0',
                        help='设备 (默认: 0)')
    
    # 自动优化
    parser.add_argument('--auto-batch', action='store_true',
                        help='自动检测最优batch size')
    
    # 阶段控制
    parser.add_argument('--skip-phase1', action='store_true',
                        help='跳过阶段1 (快速收敛)')
    parser.add_argument('--skip-phase2', action='store_true',
                        help='跳过阶段2 (稳定优化)')
    parser.add_argument('--skip-phase3', action='store_true',
                        help='跳过阶段3 (精细调整)')
    
    # 评估和导出
    parser.add_argument('--eval', action='store_true',
                        help='训练后评估模型')
    parser.add_argument('--export', type=str,
                        help='导出格式，逗号分隔 (如: onnx,engine)')
    
    args = parser.parse_args()
    
    # 设置环境
    has_cuda = setup_optimized_environment()
    
    # 检查配置文件
    if not os.path.exists("configs/wheat_disease_optimized.yaml"):
        print("❌ 错误: 数据配置文件不存在")
        return
    
    # 开始训练
    start_time = datetime.now()
    model = train_with_phases(args)
    end_time = datetime.now()
    
    if model is None:
        print("❌ 训练失败")
        return
    
    # 计算训练时间
    training_duration = (end_time - start_time).total_seconds()
    hours = int(training_duration // 3600)
    minutes = int((training_duration % 3600) // 60)
    
    print(f"\n⏱️ 总训练时间: {hours}小时 {minutes}分钟")
    
    # 评估模型
    if args.eval:
        metrics = evaluate_model(model, args)
    
    # 导出模型
    if args.export:
        formats = args.export.split(',')
        export_model(model, formats)
    
    print("\n" + "=" * 70)
    print("✅ 数字麦病专家 - 优化训练完成！")
    print("=" * 70)
    print(f"模型保存位置: runs/detect/optimized_v2/weights/best.pt")
    print("=" * 70)


if __name__ == "__main__":
    main()
