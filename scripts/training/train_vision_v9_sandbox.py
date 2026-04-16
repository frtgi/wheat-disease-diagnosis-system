#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v9 最终优化训练脚本 (修复版)
目标: mAP@50 >= 95%
基础模型: wheat_disease_v5_optimized_phase2 (mAP@50 = 92.68%)
修复:
1. 解决阶段间模型传递逻辑错误 (KeyError: 'model')
2. 添加梯度裁剪 (max_norm=1.0) 防止数值溢出
3. 确保 best_model_path 正确返回
"""

import os
import sys
import json
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime

os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

if sys.stdout:
    sys.stdout.reconfigure(line_buffering=True)
if sys.stderr:
    sys.stderr.reconfigure(line_buffering=True)

project_root = Path(__file__).parent.parent.parent
log_file = project_root / "training_v9_sandbox.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file), encoding='utf-8', mode='w')
    ],
    force=True
)
logger = logging.getLogger(__name__)

for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.flush = lambda: sys.stdout.flush()


def print_flush(msg):
    """立即刷新的打印函数"""
    print(msg, flush=True)
    logger.info(msg)


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


class GradientClippingCallback:
    """
    自定义梯度裁剪回调类
    用于覆盖 Ultralytics 默认的 max_norm=10.0，改为 max_norm=1.0
    """
    
    def __init__(self, max_norm=1.0):
        """
        初始化梯度裁剪回调
        
        Args:
            max_norm (float): 梯度裁剪的最大范数，默认为 1.0
        """
        self.max_norm = max_norm
    
    def on_optimizer_step(self, trainer):
        """
        在优化器步骤前执行自定义梯度裁剪
        
        Args:
            trainer: YOLO 训练器实例
        """
        import torch
        trainer.scaler.unscale_(trainer.optimizer)
        torch.nn.utils.clip_grad_norm_(trainer.model.parameters(), max_norm=self.max_norm)
        trainer.scaler.step(trainer.optimizer)
        trainer.scaler.update()
        trainer.optimizer.zero_grad()
        if trainer.ema:
            trainer.ema.update(trainer.model)


class TrainingProgressCallback:
    """训练进度回调类"""
    
    def __init__(self):
        self.epoch_count = 0
        self.start_time = datetime.now()
    
    def on_train_epoch_start(self, trainer):
        """训练 epoch 开始回调"""
        self.epoch_count += 1
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print_flush(f"[Epoch {self.epoch_count}] 开始训练... (已运行: {elapsed:.1f}秒)")
    
    def on_train_epoch_end(self, trainer):
        """训练 epoch 结束回调"""
        metrics = trainer.metrics if hasattr(trainer, 'metrics') else {}
        loss = metrics.get('train/box_loss', 0)
        print_flush(f"[Epoch {self.epoch_count}] 训练完成, loss: {loss:.4f}")
    
    def on_val_epoch_end(self, trainer):
        """验证 epoch 结束回调"""
        metrics = trainer.metrics if hasattr(trainer, 'metrics') else {}
        map50 = metrics.get('metrics/mAP50(B)', 0)
        map50_95 = metrics.get('metrics/mAP50-95(B)', 0)
        print_flush(f"[Epoch {self.epoch_count}] 验证完成, mAP@50: {map50:.4f}, mAP@50-95: {map50_95:.4f}")


def run_training_phase(model, project_root, config, phase_name, phase_config, output_dir, progress_callback, gradient_clip_callback):
    """
    运行单个训练阶段
    
    Args:
        model: YOLO 模型实例
        project_root: 项目根目录
        config: 配置字典
        phase_name: 阶段名称
        phase_config: 阶段配置
        output_dir: 输出目录
        progress_callback: 进度回调实例
        gradient_clip_callback: 梯度裁剪回调实例
    
    Returns:
        dict: 包含阶段训练结果的字典
    """
    print_flush("=" * 60)
    print_flush(f"开始训练阶段: {phase_name}")
    print_flush("=" * 60)
    
    lr_factor = phase_config.get('lr_factor', 1.0)
    base_lr = config['optimizer']['lr0']
    phase_lr = base_lr * lr_factor
    
    print_flush(f"学习率: {phase_lr}")
    print_flush(f"Epochs: {phase_config['epochs']}")
    print_flush(f"Mosaic: {phase_config.get('mosaic', 0.5)}")
    print_flush(f"Mixup: {phase_config.get('mixup', 0.1)}")
    print_flush(f"梯度裁剪 max_norm: {gradient_clip_callback.max_norm}")
    
    start_time = datetime.now()
    print_flush(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        print_flush(f"阶段完成，耗时: {elapsed:.2f} 秒")
        
        trainer = model.trainer
        save_dir = Path(trainer.save_dir)
        best_model_path = save_dir / "weights" / "best.pt"
        last_model_path = save_dir / "weights" / "last.pt"
        
        if best_model_path.exists():
            final_model_path = str(best_model_path)
            print_flush(f"最佳模型路径: {final_model_path}")
        elif last_model_path.exists():
            final_model_path = str(last_model_path)
            print_flush(f"使用最后模型路径: {final_model_path}")
        else:
            final_model_path = None
            print_flush("警告: 未找到模型权重文件!")
        
        metrics = {}
        if hasattr(trainer, 'validator') and hasattr(trainer.validator, 'metrics'):
            val_metrics = trainer.validator.metrics
            if hasattr(val_metrics, 'results_dict'):
                metrics = {
                    "mAP50": float(val_metrics.results_dict.get('metrics/mAP50(B)', 0)),
                    "mAP50_95": float(val_metrics.results_dict.get('metrics/mAP50-95(B)', 0)),
                    "precision": float(val_metrics.results_dict.get('metrics/precision(B)', 0)),
                    "recall": float(val_metrics.results_dict.get('metrics/recall(B)', 0)),
                }
            elif hasattr(val_metrics, 'box'):
                metrics = {
                    "mAP50": float(val_metrics.box.map50),
                    "mAP50_95": float(val_metrics.box.map),
                    "precision": float(val_metrics.box.mp),
                    "recall": float(val_metrics.box.mr),
                }
        
        if not metrics:
            metrics = {
                "mAP50": 0.0,
                "mAP50_95": 0.0,
                "precision": 0.0,
                "recall": 0.0,
            }
        
        print_flush(f"阶段结果 - mAP@50: {metrics['mAP50']:.4f}, mAP@50-95: {metrics['mAP50_95']:.4f}")
        
        return {
            "phase": phase_name,
            "epochs": phase_config['epochs'],
            "lr_factor": lr_factor,
            "elapsed_seconds": elapsed,
            "best_model_path": final_model_path,
            "save_dir": str(save_dir),
            "metrics": metrics,
            "success": True
        }
        
    except Exception as e:
        import traceback
        print_flush(f"训练阶段 {phase_name} 失败: {e}")
        print_flush(traceback.format_exc())
        return {
            "phase": phase_name,
            "success": False,
            "error": str(e)
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="v9 最终优化训练 (修复版)")
    parser.add_argument("--config", type=str, default="configs/training_v9.yaml",
                        help="配置文件路径")
    parser.add_argument("--evaluate-only", type=str, default=None,
                        help="仅评估指定模型")
    args = parser.parse_args()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    print_flush("=" * 60)
    print_flush("v9 最终优化训练 (修复版)")
    print_flush(f"Python 版本: {sys.version}")
    print_flush(f"工作目录: {os.getcwd()}")
    print_flush(f"日志文件: {log_file}")
    print_flush("=" * 60)
    
    config_path = os.path.join(project_root, args.config)
    if not os.path.exists(config_path):
        print_flush(f"配置文件不存在: {config_path}")
        print_flush("使用默认配置...")
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
        print_flush(f"评估模型: {args.evaluate_only}")
        try:
            from ultralytics import YOLO
            model = YOLO(args.evaluate_only)
            results = model.val(
                data=os.path.join(project_root, 'configs', 'wheat_disease.yaml'),
                imgsz=config['model']['input_size'],
                batch=config['training']['batch'],
                device=config['training']['device'],
            )
            print_flush(f"mAP@50: {results.box.map50:.4f}")
            print_flush(f"mAP@50-95: {results.box.map:.4f}")
        except Exception as e:
            print_flush(f"评估失败: {e}")
        return
    
    print_flush("=" * 60)
    print_flush("v9 最终优化训练")
    print_flush(f"目标: mAP@50 >= 95%")
    print_flush(f"基础模型: {base_model}")
    print_flush(f"输出目录: {output_dir}")
    print_flush("=" * 60)
    
    if not os.path.exists(base_model):
        print_flush(f"基础模型不存在: {base_model}")
        return
    
    try:
        from ultralytics import YOLO
        import torch
        print_flush(f"PyTorch 版本: {torch.__version__}")
        print_flush(f"CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print_flush(f"CUDA 设备: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print_flush(f"导入失败: {e}")
        return
    
    training_report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v9_final_fixed",
        "base_model": base_model,
        "target_mAP50": 0.95,
        "config": config,
        "phase_results": [],
        "final_results": None
    }
    
    progress_callback = TrainingProgressCallback()
    gradient_clip_callback = GradientClippingCallback(max_norm=1.0)
    
    model = YOLO(base_model)
    model.add_callback("on_train_epoch_start", progress_callback.on_train_epoch_start)
    model.add_callback("on_train_epoch_end", progress_callback.on_train_epoch_end)
    model.add_callback("on_val_epoch_end", progress_callback.on_val_epoch_end)
    model.add_callback("on_optimizer_step", gradient_clip_callback.on_optimizer_step)
    
    best_mAP50 = 0
    best_model_path = base_model
    current_model_path = base_model
    
    for phase in config['phases']:
        if current_model_path and os.path.exists(current_model_path):
            print_flush(f"加载上一阶段模型: {current_model_path}")
            model = YOLO(current_model_path)
            model.add_callback("on_train_epoch_start", progress_callback.on_train_epoch_start)
            model.add_callback("on_train_epoch_end", progress_callback.on_train_epoch_end)
            model.add_callback("on_val_epoch_end", progress_callback.on_val_epoch_end)
            model.add_callback("on_optimizer_step", gradient_clip_callback.on_optimizer_step)
        
        result = run_training_phase(
            model, project_root, config, phase['name'], phase, output_dir, 
            progress_callback, gradient_clip_callback
        )
        
        training_report['phase_results'].append(result)
        
        if result.get('success') and result.get('best_model_path'):
            if result['metrics']['mAP50'] > best_mAP50:
                best_mAP50 = result['metrics']['mAP50']
                best_model_path = result['best_model_path']
            
            current_model_path = result['best_model_path']
        elif result.get('success'):
            print_flush(f"警告: 阶段 {phase['name']} 成功但未找到模型路径，继续使用当前模型")
        
        with open(output_dir / "training_report_v9.json", 'w', encoding='utf-8') as f:
            json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    training_report['final_results'] = {
        "best_mAP50": best_mAP50,
        "best_model_path": best_model_path,
        "target_achieved": best_mAP50 >= 0.95
    }
    
    with open(output_dir / "training_report_v9.json", 'w', encoding='utf-8') as f:
        json.dump(training_report, f, indent=2, ensure_ascii=False)
    
    print_flush("=" * 60)
    print_flush("v9 训练完成!")
    print_flush(f"最佳模型: {best_model_path}")
    print_flush(f"最佳 mAP@50: {best_mAP50:.2%}")
    print_flush(f"目标达成: {'是' if best_mAP50 >= 0.95 else '否'}")
    print_flush("=" * 60)


if __name__ == "__main__":
    main()
