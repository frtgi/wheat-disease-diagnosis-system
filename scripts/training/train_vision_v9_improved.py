#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v9 最终优化训练脚本 (改进版)
目标: mAP@50 >= 95%
基础模型: wheat_disease_v5_optimized_phase2 (mAP@50 = 92.68%)
策略: 从最佳模型继续精细训练，添加详细日志输出
"""

import os
import sys
import json
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training_v9.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    import torch
except ImportError:
    logger.error("请确保已安装 ultralytics 和 torch")
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


def run_training_phase(model, project_root, config, phase_name, phase_config, output_dir):
    """运行单个训练阶段"""
    logger.info("="*60)
    logger.info(f"开始训练阶段: {phase_name}")
    logger.info("="*60)
    
    lr_factor = phase_config.get('lr_factor', 1.0)
    base_lr = config['optimizer']['lr0']
    phase_lr = base_lr * lr_factor
    
    logger.info(f"学习率: {phase_lr}")
    logger.info(f"Epochs: {phase_config['epochs']}")
    logger.info(f"Mosaic: {phase_config.get('mosaic', 0.5)}")
    logger.info(f"Mixup: {phase_config.get('mixup', 0.1)}")
    
    phase_dir = output_dir / phase_name / "train"
    phase_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = datetime.now()
    logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
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
            plots=True,
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"阶段完成，耗时: {elapsed:.2f} 秒")
        
        best_model_path = phase_dir / "weights" / "best.pt"
        
        metrics = {
            "mAP50": float(results.results_dict.get('metrics/mAP50(B)', 0)) if hasattr(results, 'results_dict') else 0,
            "mAP50_95": float(results.results_dict.get('metrics/mAP50-95(B)', 0)) if hasattr(results, 'results_dict') else 0,
            "precision": float(results.results_dict.get('metrics/precision(B)', 0)) if hasattr(results, 'results_dict') else 0,
            "recall": float(results.results_dict.get('metrics/recall(B)', 0)) if hasattr(results, 'results_dict') else 0,
        }
        
        logger.info(f"阶段结果 - mAP@50: {metrics['mAP50']:.4f}, mAP@50-95: {metrics['mAP50_95']:.4f}")
        
        return {
            "phase": phase_name,
            "epochs": phase_config['epochs'],
            "lr_factor": lr_factor,
            "elapsed_seconds": elapsed,
            "best_model_path": str(best_model_path) if best_model_path.exists() else None,
            "metrics": metrics,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"训练阶段 {phase_name} 失败: {e}")
        return {
            "phase": phase_name,
            "success": False,
            "error": str(e)
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="v9 最终优化训练")
    parser.add_argument("--config", type=str, default="configs/training_v9.yaml",
                        help="配置文件路径")
    parser.add_argument("--evaluate-only", type=str, default=None,
                        help="仅评估指定模型")
    args = parser.parse_args()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    config_path = os.path.join(project_root, args.config)
    if not os.path.exists(config_path):
        logger.warning(f"配置文件不存在: {config_path}")
        logger.info("使用默认配置...")
        config = {
            "model": {"base": "models/wheat_disease_v5_optimized_phase2/weights/best.pt", "input_size": 640},
            "training": {"epochs": 100, "batch": 4, "imgsz": 640, "device": 0, "workers": 4, "amp": True, "patience": 30, "save_period": 10},
            "optimizer": {"type": "AdamW", "lr0": 0.0001, "lrf": 0.1, "weight_decay": 0.0005, "warmup_epochs": 3},
            "loss": {"box": 7.5, "cls": 0.5, "dfl": 1.5},
            "augmentation": {"hsv_h": 0.01, "hsv_s": 0.3, "hsv_v": 0.2, "degrees": 5.0, "translate": 0.05, "scale": 0.3, "fliplr": 0.5},
            "evaluation": {"conf_threshold": 0.001, "iou_threshold": 0.7},
            "phases": [
                {"name": "fine_tune_1", "epochs": 30, "lr_factor": 1.0, "mosaic": 0.3, "mixup": 0.05},
                {"name": "fine_tune_2", "epochs": 30, "lr_factor": 0.5, "mosaic": 0.1, "mixup": 0.0},
                {"name": "final", "epochs": 40, "lr_factor": 0.1, "mosaic": 0.0, "mixup": 0.0},
            ],
            "output": {"project": "models", "name": "wheat_disease_v9_final"}
        }
    else:
        config = load_config(config_path)
    
    output_dir = Path(project_root) / config['output']['project'] / config['output']['name']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_model = os.path.join(project_root, config['model']['base'])
    
    if args.evaluate_only:
        logger.info(f"评估模型: {args.evaluate_only}")
        model = YOLO(args.evaluate_only)
        results = model.val(
            data=os.path.join(project_root, 'configs', 'wheat_disease.yaml'),
            imgsz=config['model']['input_size'],
            batch=config['training']['batch'],
            device=config['training']['device'],
        )
        logger.info(f"mAP@50: {results.box.map50:.4f}")
        logger.info(f"mAP@50-95: {results.box.map:.4f}")
        return
    
    logger.info("="*60)
    logger.info("v9 最终优化训练")
    logger.info(f"目标: mAP@50 >= 95%")
    logger.info(f"基础模型: {base_model}")
    logger.info(f"输出目录: {output_dir}")
    logger.info("="*60)
    
    if not os.path.exists(base_model):
        logger.error(f"基础模型不存在: {base_model}")
        return
    
    training_report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v9_final",
        "base_model": base_model,
        "target_mAP50": 0.95,
        "config": config,
        "phase_results": [],
        "final_results": None
    }
    
    model = YOLO(base_model)
    best_mAP50 = 0
    best_model_path = base_model
    
    for phase in config['phases']:
        result = run_training_phase(model, project_root, config, phase['name'], phase, output_dir)
        
        training_report['phase_results'].append(result)
        
        if result.get('success') and result.get('best_model_path'):
            if result['metrics']['mAP50'] > best_mAP50:
                best_mAP50 = result['metrics']['mAP50']
                best_model_path = result['best_model_path']
            
            model = YOLO(result['best_model_path'])
        
        with open(output_dir / "training_report_v9.json", 'w', encoding='utf-8') as f:
            json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    training_report['final_results'] = {
        "best_mAP50": best_mAP50,
        "best_model_path": best_model_path,
        "target_achieved": best_mAP50 >= 0.95
    }
    
    with open(output_dir / "training_report_v9.json", 'w', encoding='utf-8') as f:
        json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    logger.info("="*60)
    logger.info("v9 训练完成!")
    logger.info(f"最佳模型: {best_model_path}")
    logger.info(f"最佳 mAP@50: {best_mAP50:.2%}")
    logger.info(f"目标达成: {'是' if best_mAP50 >= 0.95 else '否'}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
