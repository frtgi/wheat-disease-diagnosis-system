#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v8 最终优化训练脚本
目标: mAP@50 >= 95%
基础模型: wheat_disease_v5_optimized_phase2 (mAP@50 = 92.68%)
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime

try:
    from ultralytics import YOLO
    import torch
except ImportError:
    print("请确保已安装 ultralytics 和 torch")
    sys.exit(1)


def get_project_root():
    """获取项目根目录"""
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
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_training_phase(project_root, config, phase_name, phase_config, 
                       base_model, output_dir, prev_model=None):
    """运行单个训练阶段"""
    print(f"\n{'='*60}")
    print(f"开始训练阶段: {phase_name}")
    print(f"{'='*60}")
    
    phase_dir = output_dir / phase_name / "train"
    phase_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = prev_model if prev_model else base_model
    
    lr_factor = phase_config.get('lr_factor', 1.0)
    base_lr = config['optimizer']['lr0']
    phase_lr = base_lr * lr_factor
    
    print(f"基础模型: {model_path}")
    print(f"学习率: {phase_lr}")
    print(f"Epochs: {phase_config['epochs']}")
    print(f"Mosaic: {phase_config.get('mosaic', 0.5)}")
    
    model = YOLO(model_path)
    
    start_time = datetime.now()
    
    results = model.train(
        data=os.path.join(project_root, 'configs', 'wheat_disease.yaml'),
        epochs=phase_config['epochs'],
        batch=config['training']['batch'],
        imgsz=config['model']['input_size'],
        device=config['training']['device'],
        workers=config['training']['workers'],
        project=str(output_dir.parent),
        name=f"{output_dir.name}/{phase_name}",
        exist_ok=True,
        optimizer=config['optimizer']['type'],
        lr0=phase_lr,
        lrf=config['optimizer']['lrf'],
        weight_decay=config['optimizer']['weight_decay'],
        warmup_epochs=config['optimizer']['warmup_epochs'],
        box=config['loss']['box'],
        cls=config['loss']['cls'],
        dfl=config['loss']['dfl'],
        mosaic=phase_config.get('mosaic', 0.5),
        mixup=phase_config.get('mixup', 0.1),
        hsv_h=config['augmentation']['hsv_h'],
        hsv_s=config['augmentation']['hsv_s'],
        hsv_v=config['augmentation']['hsv_v'],
        degrees=config['augmentation']['degrees'],
        translate=config['augmentation']['translate'],
        scale=config['augmentation']['scale'],
        fliplr=config['augmentation']['fliplr'],
        amp=config['training']['amp'],
        patience=config['training']['patience'],
        save_period=config['training']['save_period'],
        conf=config['evaluation']['conf_threshold'],
        iou=config['evaluation']['iou_threshold'],
        verbose=True,
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    best_model_path = phase_dir / "weights" / "best.pt"
    
    metrics = {
        "mAP50": float(results.results_dict.get('metrics/mAP50(B)', 0)) if hasattr(results, 'results_dict') else 0,
        "mAP50_95": float(results.results_dict.get('metrics/mAP50-95(B)', 0)) if hasattr(results, 'results_dict') else 0,
        "precision": float(results.results_dict.get('metrics/precision(B)', 0)) if hasattr(results, 'results_dict') else 0,
        "recall": float(results.results_dict.get('metrics/recall(B)', 0)) if hasattr(results, 'results_dict') else 0,
    }
    
    return {
        "phase": phase_name,
        "epochs": phase_config['epochs'],
        "lr_factor": lr_factor,
        "elapsed_seconds": elapsed,
        "best_model_path": str(best_model_path) if best_model_path.exists() else None,
        "metrics": metrics,
        "success": True
    }


def evaluate_model(model_path, project_root, config):
    """评估模型性能"""
    print(f"\n评估模型: {model_path}")
    
    model = YOLO(model_path)
    
    results = model.val(
        data=os.path.join(project_root, 'configs', 'wheat_disease.yaml'),
        imgsz=config['model']['input_size'],
        batch=config['training']['batch'],
        device=config['training']['device'],
        conf=config['evaluation']['conf_threshold'],
        iou=config['evaluation']['iou_threshold'],
    )
    
    return {
        "mAP50": results.box.map50,
        "mAP50_95": results.box.map,
        "precision": results.box.mp,
        "recall": results.box.mr,
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="v8 最终优化训练")
    parser.add_argument("--config", type=str, default="configs/training_v8.yaml",
                        help="配置文件路径")
    parser.add_argument("--evaluate-only", type=str, default=None,
                        help="仅评估指定模型")
    args = parser.parse_args()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    config_path = os.path.join(project_root, args.config)
    config = load_config(config_path)
    
    output_dir = Path(project_root) / config['output']['project'] / config['output']['name']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_model = os.path.join(project_root, config['model']['base'])
    
    if args.evaluate_only:
        results = evaluate_model(args.evaluate_only, project_root, config)
        print(f"\n评估结果:")
        print(f"  mAP@50: {results['mAP50']:.4f}")
        print(f"  mAP@50-95: {results['mAP50_95']:.4f}")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall: {results['recall']:.4f}")
        return
    
    print("="*60)
    print("v8 最终优化训练")
    print(f"目标: mAP@50 >= 95%")
    print(f"基础模型: {base_model}")
    print(f"输出目录: {output_dir}")
    print("="*60)
    
    if not os.path.exists(base_model):
        print(f"错误: 基础模型不存在: {base_model}")
        return
    
    training_report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v8_final",
        "base_model": base_model,
        "target_mAP50": 0.95,
        "config": config,
        "phase_results": [],
        "final_results": None
    }
    
    prev_model = None
    best_mAP50 = 0
    best_model_path = None
    
    for phase in config['phases']:
        result = run_training_phase(
            project_root, config,
            phase['name'], phase,
            base_model, output_dir, prev_model
        )
        
        training_report['phase_results'].append(result)
        
        if result['best_model_path']:
            prev_model = result['best_model_path']
            
            if result['metrics']['mAP50'] > best_mAP50:
                best_mAP50 = result['metrics']['mAP50']
                best_model_path = result['best_model_path']
        
        with open(output_dir / "training_report_v8.json", 'w', encoding='utf-8') as f:
            json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    training_report['final_results'] = {
        "best_mAP50": best_mAP50,
        "best_model_path": best_model_path,
        "target_achieved": best_mAP50 >= 0.95
    }
    
    with open(output_dir / "training_report_v8.json", 'w', encoding='utf-8') as f:
        json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("v8 训练完成!")
    print(f"最佳模型: {best_model_path}")
    print(f"最佳 mAP@50: {best_mAP50:.2%}")
    print(f"目标达成: {'是' if best_mAP50 >= 0.95 else '否'}")
    print("="*60)


if __name__ == "__main__":
    main()
