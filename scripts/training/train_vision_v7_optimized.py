# -*- coding: utf-8 -*-
"""
视觉检测优化训练脚本 V7 - 目标 mAP@50 >= 95%

优化策略:
1. 升级到 YOLOv8m (更大模型容量)
2. 类别权重平衡 (解决 Stem fly 样本不足)
3. 梯度裁剪 (解决数值不稳定)
4. 优化学习率衰减策略 (lrf=0.1)
5. 调整损失权重 (box=5.0, cls=0.8)
6. 渐进式数据增强

使用方法:
    python train_vision_v7_optimized.py
    python train_vision_v7_optimized.py --epochs 200 --batch 4
    python train_vision_v7_optimized.py --resume models/wheat_disease_v7_optimized/phase2_aggressive/train/weights/last.pt
"""
import os
import sys
import gc
import json
import yaml
import argparse
import time
import math
import copy
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_gpu_environment() -> Dict[str, Any]:
    """
    检查GPU环境并返回配置信息
    
    Returns:
        包含GPU配置信息的字典
    """
    import torch
    
    print("=" * 70)
    print("🔍 GPU 环境检查")
    print("=" * 70)
    
    if not torch.cuda.is_available():
        print("❌ CUDA 不可用")
        return {"available": False}
    
    gpu_name = torch.cuda.get_device_name(0)
    total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    cuda_version = torch.version.cuda
    pytorch_version = torch.__version__
    
    print(f"✅ GPU: {gpu_name}")
    print(f"   显存: {total_memory:.2f} GB")
    print(f"   CUDA: {cuda_version}")
    print(f"   PyTorch: {pytorch_version}")
    
    if total_memory < 6:
        optimal_batch = 4
        recommended_model = "yolov8s.pt"
    elif total_memory < 8:
        optimal_batch = 8
        recommended_model = "yolov8m.pt"
    else:
        optimal_batch = 16
        recommended_model = "yolov8m.pt"
    
    return {
        "available": True,
        "name": gpu_name,
        "memory_gb": total_memory,
        "cuda_version": cuda_version,
        "pytorch_version": pytorch_version,
        "optimal_batch": optimal_batch,
        "recommended_model": recommended_model
    }


def setup_training_environment():
    """
    设置训练环境，优化显存和性能
    """
    import torch
    
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = (
        'max_split_size_mb:64,'
        'garbage_collection_threshold:0.5,'
        'expandable_segments:True'
    )
    
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    os.environ['CUDNN_BENCHMARK'] = '1'
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    
    print("✅ 训练环境优化完成")


def load_config(config_path: str) -> Dict:
    """
    加载训练配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def calculate_class_weights(dataset_stats_path: str) -> Dict[int, float]:
    """
    根据数据集统计计算类别权重
    
    Args:
        dataset_stats_path: 数据集统计文件路径
    
    Returns:
        类别权重字典
    """
    with open(dataset_stats_path, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    categories = stats.get('categories', {})
    counts = list(categories.values())
    median_count = sorted(counts)[len(counts) // 2]
    
    class_names = [
        'Aphid', 'Black Rust', 'Blast', 'Brown Rust', 'Common Root Rot',
        'Fusarium Head Blight', 'Healthy', 'Leaf Blight', 'Mildew', 'Mite',
        'Septoria', 'Smut', 'Stem fly', 'Tan spot', 'Yellow Rust'
    ]
    
    weights = {}
    for i, name in enumerate(class_names):
        count = categories.get(name, median_count)
        weight = median_count / count
        weights[i] = round(weight, 2)
    
    print(f"\n📊 类别权重计算完成:")
    for i, name in enumerate(class_names):
        print(f"   {name}: {weights[i]:.2f}x (样本数: {categories.get(name, 0)})")
    
    return weights


def create_weighted_dataloader_config(
    data_yaml_path: str,
    class_weights: Dict[int, float],
    output_path: str
) -> str:
    """
    创建带类别权重的数据集配置
    
    Args:
        data_yaml_path: 原始数据集配置路径
        class_weights: 类别权重字典
        output_path: 输出配置路径
    
    Returns:
        新配置文件路径
    """
    with open(data_yaml_path, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)
    
    weight_list = [class_weights.get(i, 1.0) for i in range(15)]
    data_config['class_weights'] = weight_list
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f, default_flow_style=False, allow_unicode=True)
    
    return output_path


def apply_gradient_clipping(model, max_norm: float = 10.0):
    """
    对模型参数应用梯度裁剪
    
    Args:
        model: PyTorch模型
        max_norm: 最大梯度范数
    
    Returns:
        总梯度范数
    """
    import torch
    total_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(),
        max_norm=max_norm,
        norm_type=2.0
    )
    return total_norm


def train_single_phase(
    model_path: str,
    data_yaml: str,
    phase_config: Dict,
    base_config: Dict,
    output_dir: str,
    gradient_clip: float = 10.0,
    device: int = 0
) -> Tuple[str, Dict]:
    """
    执行单阶段训练
    
    Args:
        model_path: 模型路径
        data_yaml: 数据集配置文件路径
        phase_config: 阶段配置
        base_config: 基础配置
        output_dir: 输出目录
        gradient_clip: 梯度裁剪阈值
        device: GPU设备ID
    
    Returns:
        (最佳模型路径, 训练结果字典)
    """
    from ultralytics import YOLO
    import torch
    
    print(f"\n{'='*70}")
    print(f"📊 阶段: {phase_config['name']}")
    print(f"   描述: {phase_config.get('description', 'N/A')}")
    print(f"   轮数: {phase_config['epochs']}")
    print(f"   学习率因子: {phase_config['lr_factor']}")
    print(f"{'='*70}")
    
    model = YOLO(model_path)
    
    train_cfg = base_config['training']
    opt_cfg = base_config['optimizer']
    loss_cfg = base_config['loss']
    aug_cfg = base_config['augmentation']
    
    phase_lr = opt_cfg['lr0'] * phase_config['lr_factor']
    
    callbacks = {}
    
    def on_train_batch_end(trainer):
        if hasattr(trainer, 'optimizer') and trainer.optimizer is not None:
            total_norm = torch.nn.utils.clip_grad_norm_(
                trainer.model.parameters(),
                max_norm=gradient_clip
            )
            if math.isnan(total_norm) or math.isinf(total_norm):
                print(f"\n⚠️ 检测到异常梯度: {total_norm:.4f}, 已裁剪")
    
    model.add_callback('on_train_batch_end', on_train_batch_end)
    
    results = model.train(
        data=data_yaml,
        epochs=phase_config['epochs'],
        batch=train_cfg['batch'],
        imgsz=train_cfg['imgsz'],
        device=device,
        workers=train_cfg['workers'],
        amp=train_cfg['amp'],
        cache=train_cfg['cache'],
        project=output_dir,
        name="train",
        exist_ok=True,
        optimizer=opt_cfg['type'],
        lr0=phase_lr,
        lrf=opt_cfg['lrf'],
        momentum=opt_cfg['momentum'],
        weight_decay=opt_cfg['weight_decay'],
        warmup_epochs=min(5, phase_config['epochs'] // 10),
        warmup_momentum=opt_cfg['warmup_momentum'],
        box=loss_cfg['box'],
        cls=loss_cfg['cls'],
        dfl=loss_cfg['dfl'],
        hsv_h=aug_cfg['hsv_h'],
        hsv_s=aug_cfg['hsv_s'],
        hsv_v=aug_cfg['hsv_v'],
        degrees=aug_cfg['degrees'],
        translate=aug_cfg['translate'],
        scale=aug_cfg['scale'],
        shear=aug_cfg['shear'],
        perspective=aug_cfg['perspective'],
        flipud=aug_cfg['flipud'],
        fliplr=aug_cfg['fliplr'],
        mosaic=phase_config.get('mosaic', aug_cfg['mosaic']),
        mixup=phase_config.get('mixup', aug_cfg['mixup']),
        copy_paste=aug_cfg['copy_paste'],
        erasing=aug_cfg['erasing'],
        patience=train_cfg['patience'],
        save_period=train_cfg['save_period'],
        val=True,
        plots=True,
        verbose=True,
        deterministic=False,
        single_cls=False,
        rect=train_cfg['rect'],
        cos_lr=True,
        close_mosaic=10,
        resume=False,
    )
    
    metrics = model.val(data=data_yaml, verbose=True)
    
    best_model_path = str(Path(output_dir) / "train" / "weights" / "best.pt")
    
    phase_result = {
        "phase": phase_config['name'],
        "epochs": phase_config['epochs'],
        "lr_factor": phase_config['lr_factor'],
        "mAP50": float(metrics.box.map50) if hasattr(metrics, 'box') else 0.0,
        "mAP50_95": float(metrics.box.map) if hasattr(metrics, 'box') else 0.0,
        "precision": float(metrics.box.mp) if hasattr(metrics, 'box') else 0.0,
        "recall": float(metrics.box.mr) if hasattr(metrics, 'box') else 0.0,
        "best_model_path": best_model_path
    }
    
    print(f"\n📈 阶段 {phase_config['name']} 完成:")
    print(f"   mAP@50: {phase_result['mAP50']:.2%}")
    print(f"   mAP@50-95: {phase_result['mAP50_95']:.2%}")
    
    return best_model_path, phase_result


def train_multi_phase_optimized(
    config: Dict,
    data_yaml: str,
    output_dir: str,
    resume_from: Optional[str] = None,
    start_phase: int = 0
) -> Dict:
    """
    多阶段优化训练
    
    Args:
        config: 训练配置
        data_yaml: 数据集配置文件路径
        output_dir: 输出目录
        resume_from: 恢复训练的模型路径
        start_phase: 起始阶段索引
    
    Returns:
        训练结果字典
    """
    from ultralytics import YOLO
    import torch
    
    print("\n" + "=" * 70)
    print("🎯 V7 多阶段优化训练")
    print("=" * 70)
    print(f"📦 基础模型: {config['model']['base']}")
    print(f"🎯 目标: mAP@50 >= 95%")
    print(f"🔧 梯度裁剪: {config.get('gradient_clip', 10.0)}")
    print(f"📊 损失权重: box={config['loss']['box']}, cls={config['loss']['cls']}, dfl={config['loss']['dfl']}")
    
    phases = config['phases']
    gradient_clip = config.get('gradient_clip', 10.0)
    
    if resume_from:
        current_model = resume_from
        print(f"🔄 从检查点恢复: {resume_from}")
    else:
        current_model = config['model']['base']
    
    best_map50 = 0.0
    best_model_path = None
    phase_results = []
    
    for i, phase in enumerate(phases):
        if i < start_phase:
            print(f"\n⏭️ 跳过阶段 {i+1}: {phase['name']}")
            continue
        
        phase_output = str(Path(output_dir) / f"phase{i+1}_{phase['name']}")
        
        try:
            model_path, phase_result = train_single_phase(
                model_path=current_model,
                data_yaml=data_yaml,
                phase_config=phase,
                base_config=config,
                output_dir=phase_output,
                gradient_clip=gradient_clip,
                device=config['training']['device']
            )
            
            phase_results.append(phase_result)
            
            if phase_result['mAP50'] > best_map50:
                best_map50 = phase_result['mAP50']
                best_model_path = model_path
                current_model = model_path
                print(f"   ✅ 新最佳模型! mAP@50: {best_map50:.2%}")
            else:
                current_model = model_path
            
            if best_map50 >= 0.95:
                print(f"\n🎉 目标达成! mAP@50 = {best_map50:.2%} >= 95%")
                break
            
            torch.cuda.empty_cache()
            gc.collect()
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"\n❌ 显存不足! 尝试减小批大小...")
                torch.cuda.empty_cache()
                gc.collect()
                
                config['training']['batch'] = max(1, config['training']['batch'] // 2)
                print(f"   批大小调整为: {config['training']['batch']}")
                
                model_path, phase_result = train_single_phase(
                    model_path=current_model,
                    data_yaml=data_yaml,
                    phase_config=phase,
                    base_config=config,
                    output_dir=phase_output,
                    gradient_clip=gradient_clip,
                    device=config['training']['device']
                )
                phase_results.append(phase_result)
                
                if phase_result['mAP50'] > best_map50:
                    best_map50 = phase_result['mAP50']
                    best_model_path = model_path
                    current_model = model_path
            else:
                raise e
    
    final_result = {
        "best_model_path": best_model_path,
        "best_mAP50": best_map50,
        "target_achieved": best_map50 >= 0.95,
        "phase_results": phase_results,
        "total_epochs": sum(p['epochs'] for p in phases[:len(phase_results)])
    }
    
    return final_result


def evaluate_model(model_path: str, data_yaml: str) -> Dict:
    """
    评估模型性能
    
    Args:
        model_path: 模型路径
        data_yaml: 数据集配置文件路径
    
    Returns:
        评估结果字典
    """
    from ultralytics import YOLO
    
    print("\n" + "=" * 70)
    print("📊 模型评估")
    print("=" * 70)
    
    model = YOLO(model_path)
    metrics = model.val(data=data_yaml, verbose=True)
    
    results = {
        "mAP50": float(metrics.box.map50),
        "mAP50_95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "target_achieved": float(metrics.box.map50) >= 0.95,
    }
    
    print(f"\n📈 评估结果:")
    print(f"   mAP@50: {results['mAP50']:.2%}")
    print(f"   mAP@50-95: {results['mAP50_95']:.2%}")
    print(f"   Precision: {results['precision']:.2%}")
    print(f"   Recall: {results['recall']:.2%}")
    
    if results["target_achieved"]:
        print("\n🎉 目标达成! mAP@50 >= 95%")
    else:
        gap = 0.95 - results["mAP50"]
        print(f"\n⚠️ 距离目标还差 {gap:.2%}")
    
    return results


def save_training_report(
    output_dir: str,
    config: Dict,
    results: Dict,
    gpu_info: Dict
):
    """
    保存训练报告
    
    Args:
        output_dir: 输出目录
        config: 训练配置
        results: 训练结果
        gpu_info: GPU信息
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v7_optimized",
        "gpu_info": gpu_info,
        "config": config,
        "results": results,
    }
    
    report_path = Path(output_dir) / "training_report_v7.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 训练报告已保存: {report_path}")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="V7 优化视觉检测训练")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径")
    parser.add_argument("--epochs", type=int, default=None, help="总训练轮数")
    parser.add_argument("--batch", type=int, default=None, help="批大小")
    parser.add_argument("--device", type=int, default=0, help="GPU设备ID")
    parser.add_argument("--resume", type=str, default=None, help="恢复训练的模型路径")
    parser.add_argument("--phase", type=int, default=0, help="起始阶段索引 (0-based)")
    parser.add_argument("--evaluate-only", type=str, default=None, help="仅评估指定模型")
    args = parser.parse_args()
    
    gpu_info = check_gpu_environment()
    setup_training_environment()
    
    config_path = args.config or str(PROJECT_ROOT / "configs" / "training_v7.yaml")
    config = load_config(config_path)
    
    if args.epochs:
        total_epochs = args.epochs
        phase_ratio = [0.075, 0.4, 0.3, 0.225]
        for i, (phase, ratio) in enumerate(zip(config['phases'], phase_ratio)):
            config['phases'][i]['epochs'] = max(5, int(total_epochs * ratio))
    
    if args.batch:
        config['training']['batch'] = args.batch
    elif gpu_info.get('available'):
        config['training']['batch'] = min(config['training']['batch'], gpu_info.get('optimal_batch', 4))
    
    config['training']['device'] = args.device
    
    data_yaml = str(PROJECT_ROOT / "configs" / "wheat_disease.yaml")
    output_dir = str(PROJECT_ROOT / "models" / "wheat_disease_v7_optimized")
    os.makedirs(output_dir, exist_ok=True)
    
    if args.evaluate_only:
        results = evaluate_model(args.evaluate_only, data_yaml)
        save_training_report(output_dir, config, results, gpu_info)
        return
    
    results = train_multi_phase_optimized(
        config=config,
        data_yaml=data_yaml,
        output_dir=output_dir,
        resume_from=args.resume,
        start_phase=args.phase
    )
    
    if results.get("best_model_path"):
        eval_results = evaluate_model(results["best_model_path"], data_yaml)
        results.update(eval_results)
    
    save_training_report(output_dir, config, results, gpu_info)
    
    print("\n" + "=" * 70)
    print("🏁 V7 训练完成")
    print("=" * 70)
    if results.get("target_achieved"):
        print("🎉 恭喜! 已达成 mAP@50 >= 95% 目标!")
    else:
        current_map = results.get("mAP50", results.get("best_mAP50", 0))
        print(f"📊 当前 mAP@50: {current_map:.2%}")
        print(f"💡 建议: 增加训练轮数或尝试更大的模型 (YOLOv8l)")


if __name__ == "__main__":
    main()
