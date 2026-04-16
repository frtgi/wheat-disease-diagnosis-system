#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v10 YOLOv8s 训练脚本
目标: mAP@50 >= 95%
基础模型: YOLOv8s (预训练权重)
策略: 使用更大的模型提升检测精度
GPU限制: RTX 3050 Laptop (4GB显存)
"""

import os
import sys
import json
import yaml
import argparse
import gc
from pathlib import Path
from datetime import datetime

try:
    from ultralytics import YOLO
    import torch
except ImportError:
    print("请确保已安装 ultralytics 和 torch")
    sys.exit(1)


def get_project_root():
    """
    获取项目根目录
    
    Returns:
        str: 项目根目录路径
    """
    possible_paths = [
        "D:/Project/WheatAgent",
        "D:/Project/wheatagent",
        Path(__file__).parent.parent.parent.as_posix()
    ]
    for path in possible_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "configs")):
            return path
    return "D:/Project/WheatAgent"


def load_config(config_path):
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        dict: 配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def clear_gpu_memory():
    """
    清理GPU显存，防止显存溢出
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def run_training_phase(model, project_root, config, phase_name, phase_config, output_dir):
    """
    运行单个训练阶段
    
    Args:
        model: YOLO模型实例
        project_root: 项目根目录
        config: 完整配置字典
        phase_name: 阶段名称
        phase_config: 阶段配置
        output_dir: 输出目录
        
    Returns:
        dict: 训练结果字典
    """
    print(f"\n{'='*60}")
    print(f"开始训练阶段: {phase_name}")
    print(f"描述: {phase_config.get('description', 'N/A')}")
    print(f"{'='*60}")
    
    clear_gpu_memory()
    
    lr_factor = phase_config.get('lr_factor', 1.0)
    base_lr = config['optimizer']['lr0']
    phase_lr = base_lr * lr_factor
    
    freeze_backbone = phase_config.get('freeze_backbone', False)
    
    print(f"学习率: {phase_lr}")
    print(f"Epochs: {phase_config['epochs']}")
    print(f"Mosaic: {phase_config.get('mosaic', 0.5)}")
    print(f"Mixup: {phase_config.get('mixup', 0.1)}")
    print(f"冻结骨干网络: {freeze_backbone}")
    
    start_time = datetime.now()
    
    train_args = {
        'data': os.path.join(project_root, 'configs', 'wheat_disease.yaml'),
        'epochs': phase_config['epochs'],
        'batch': config['training']['batch'],
        'imgsz': config['model']['input_size'],
        'device': config['training']['device'],
        'workers': config['training']['workers'],
        'project': str(output_dir.parent),
        'name': f"{output_dir.name}/{phase_name}",
        'exist_ok': True,
        'optimizer': config['optimizer']['type'],
        'lr0': phase_lr,
        'lrf': config['optimizer']['lrf'],
        'weight_decay': config['optimizer']['weight_decay'],
        'warmup_epochs': config['optimizer']['warmup_epochs'],
        'box': config['loss']['box'],
        'cls': config['loss']['cls'],
        'dfl': config['loss']['dfl'],
        'mosaic': phase_config.get('mosaic', 0.5),
        'mixup': phase_config.get('mixup', 0.1),
        'hsv_h': config['augmentation']['hsv_h'],
        'hsv_s': config['augmentation']['hsv_s'],
        'hsv_v': config['augmentation']['hsv_v'],
        'degrees': config['augmentation']['degrees'],
        'translate': config['augmentation']['translate'],
        'scale': config['augmentation']['scale'],
        'fliplr': config['augmentation']['fliplr'],
        'amp': config['training']['amp'],
        'patience': config['training']['patience'],
        'save_period': config['training']['save_period'],
        'conf': config['evaluation']['conf_threshold'],
        'iou': config['evaluation']['iou_threshold'],
        'verbose': True,
    }
    
    if freeze_backbone:
        train_args['freeze'] = 10
    
    results = model.train(**train_args)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    phase_dir = output_dir / phase_name / "train"
    best_model_path = phase_dir / "weights" / "best.pt"
    
    metrics = {
        "mAP50": float(results.results_dict.get('metrics/mAP50(B)', 0)) if hasattr(results, 'results_dict') else 0,
        "mAP50_95": float(results.results_dict.get('metrics/mAP50-95(B)', 0)) if hasattr(results, 'results_dict') else 0,
        "precision": float(results.results_dict.get('metrics/precision(B)', 0)) if hasattr(results, 'results_dict') else 0,
        "recall": float(results.results_dict.get('metrics/recall(B)', 0)) if hasattr(results, 'results_dict') else 0,
    }
    
    clear_gpu_memory()
    
    return {
        "phase": phase_name,
        "epochs": phase_config['epochs'],
        "lr_factor": lr_factor,
        "freeze_backbone": freeze_backbone,
        "elapsed_seconds": elapsed,
        "best_model_path": str(best_model_path) if best_model_path.exists() else None,
        "metrics": metrics,
        "success": True
    }


def evaluate_model(model_path, project_root, config):
    """
    评估模型性能
    
    Args:
        model_path: 模型路径
        project_root: 项目根目录
        config: 配置字典
        
    Returns:
        dict: 评估结果字典
    """
    print(f"\n评估模型: {model_path}")
    
    clear_gpu_memory()
    
    model = YOLO(model_path)
    
    results = model.val(
        data=os.path.join(project_root, 'configs', 'wheat_disease.yaml'),
        imgsz=config['model']['input_size'],
        batch=config['training']['batch'],
        device=config['training']['device'],
        conf=config['evaluation']['conf_threshold'],
        iou=config['evaluation']['iou_threshold'],
    )
    
    clear_gpu_memory()
    
    return {
        "mAP50": results.box.map50,
        "mAP50_95": results.box.map,
        "precision": results.box.mp,
        "recall": results.box.mr,
    }


def check_gpu_memory():
    """
    检查GPU显存状态
    
    Returns:
        dict: GPU显存信息
    """
    if torch.cuda.is_available():
        gpu_info = {
            "device_name": torch.cuda.get_device_name(0),
            "total_memory": torch.cuda.get_device_properties(0).total_memory / (1024**3),
            "allocated": torch.cuda.memory_allocated(0) / (1024**3),
            "cached": torch.cuda.memory_reserved(0) / (1024**3),
        }
        return gpu_info
    return {"error": "CUDA不可用"}


def main():
    """
    主函数 - 执行YOLOv8s训练流程
    """
    parser = argparse.ArgumentParser(description="v10 YOLOv8s 训练")
    parser.add_argument("--config", type=str, default="configs/training_v10_yolov8s.yaml",
                        help="配置文件路径")
    parser.add_argument("--evaluate-only", type=str, default=None,
                        help="仅评估指定模型")
    parser.add_argument("--skip-phases", type=int, default=0,
                        help="跳过前N个训练阶段")
    args = parser.parse_args()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    config_path = os.path.join(project_root, args.config)
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        print("使用默认配置...")
        config = {
            "model": {"base": "yolov8s.pt", "input_size": 640},
            "training": {"epochs": 150, "batch": 2, "imgsz": 640, "device": 0, "workers": 2, "amp": True, "patience": 40, "save_period": 10},
            "optimizer": {"type": "AdamW", "lr0": 0.0005, "lrf": 0.1, "weight_decay": 0.0005, "warmup_epochs": 5},
            "loss": {"box": 7.5, "cls": 0.5, "dfl": 1.5},
            "augmentation": {"hsv_h": 0.015, "hsv_s": 0.5, "hsv_v": 0.3, "degrees": 10.0, "translate": 0.1, "scale": 0.5, "fliplr": 0.5},
            "evaluation": {"conf_threshold": 0.001, "iou_threshold": 0.7},
            "phases": [
                {"name": "phase1_warmup", "epochs": 30, "lr_factor": 1.0, "mosaic": 0.8, "mixup": 0.1, "freeze_backbone": True},
                {"name": "phase2_finetune", "epochs": 50, "lr_factor": 0.5, "mosaic": 0.5, "mixup": 0.05, "freeze_backbone": False},
                {"name": "phase3_stable", "epochs": 40, "lr_factor": 0.2, "mosaic": 0.2, "mixup": 0.0, "freeze_backbone": False},
                {"name": "phase4_final", "epochs": 30, "lr_factor": 0.1, "mosaic": 0.0, "mixup": 0.0, "freeze_backbone": False},
            ],
            "output": {"project": "models", "name": "wheat_disease_v10_yolov8s"}
        }
    else:
        config = load_config(config_path)
    
    output_dir = Path(project_root) / config['output']['project'] / config['output']['name']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_model = config['model']['base']
    
    if args.evaluate_only:
        results = evaluate_model(args.evaluate_only, project_root, config)
        print(f"\n评估结果:")
        print(f"  mAP@50: {results['mAP50']:.4f}")
        print(f"  mAP@50-95: {results['mAP50_95']:.4f}")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall: {results['recall']:.4f}")
        return
    
    print("="*60)
    print("v10 YOLOv8s 训练")
    print(f"目标: mAP@50 >= 95%")
    print(f"基础模型: {base_model}")
    print(f"输出目录: {output_dir}")
    print("="*60)
    
    gpu_info = check_gpu_memory()
    print(f"\nGPU信息:")
    print(f"  设备: {gpu_info.get('device_name', 'N/A')}")
    print(f"  总显存: {gpu_info.get('total_memory', 0):.2f} GB")
    print(f"  已分配: {gpu_info.get('allocated', 0):.2f} GB")
    
    training_report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v10_yolov8s",
        "base_model": base_model,
        "target_mAP50": 0.95,
        "gpu_info": gpu_info,
        "config": config,
        "phase_results": [],
        "final_results": None
    }
    
    model = YOLO(base_model)
    best_mAP50 = 0
    best_model_path = None
    
    phases = config['phases'][args.skip_phases:]
    
    for i, phase in enumerate(phases):
        if i > 0 and best_model_path:
            model = YOLO(best_model_path)
        
        result = run_training_phase(model, project_root, config, phase['name'], phase, output_dir)
        
        training_report['phase_results'].append(result)
        
        if result['best_model_path']:
            if result['metrics']['mAP50'] > best_mAP50:
                best_mAP50 = result['metrics']['mAP50']
                best_model_path = result['best_model_path']
        
        with open(output_dir / "training_report_v10.json", 'w', encoding='utf-8') as f:
            json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    training_report['final_results'] = {
        "best_mAP50": best_mAP50,
        "best_model_path": best_model_path,
        "target_achieved": best_mAP50 >= 0.95
    }
    
    with open(output_dir / "training_report_v10.json", 'w', encoding='utf-8') as f:
        json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("v10 YOLOv8s 训练完成!")
    print(f"最佳模型: {best_model_path}")
    print(f"最佳 mAP@50: {best_mAP50:.2%}")
    print(f"目标达成: {'是' if best_mAP50 >= 0.95 else '否'}")
    print("="*60)


if __name__ == "__main__":
    main()
