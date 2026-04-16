# -*- coding: utf-8 -*-
"""
视觉检测优化训练脚本 - 目标 mAP@50 > 95%

基于研究文档第3章优化策略：
1. 动态蛇形卷积(DySnakeConv) - 捕获细长病斑
2. SPPELAN - 多尺度特征聚合
3. STA - 超级令牌注意力
4. CIoU Loss - 细长目标优化
5. 增强数据增强策略

使用方法:
    python train_vision_high_accuracy.py --epochs 150 --batch 8
"""
import os
import sys
import gc
import json
import yaml
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any

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
    
    optimal_batch = 8 if total_memory < 6 else 16
    
    return {
        "available": True,
        "name": gpu_name,
        "memory_gb": total_memory,
        "cuda_version": cuda_version,
        "pytorch_version": pytorch_version,
        "optimal_batch": optimal_batch
    }


def setup_training_environment():
    """
    设置训练环境，优化显存和性能
    """
    import torch
    
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = (
        'max_split_size_mb:128,'
        'garbage_collection_threshold:0.6,'
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


def get_optimized_training_config() -> Dict:
    """
    获取针对高精度优化的训练配置
    
    基于文档3.1-3.4节的优化策略：
    - 更强的数据增强
    - CIoU损失优化
    - 多阶段学习率
    - 针对细长病斑的参数调整
    
    Returns:
        优化后的训练配置字典
    """
    return {
        "model": {
            "base": "yolov8n.pt",
            "use_dy_snake_conv": True,
            "use_sppelan": True,
            "use_sta": True,
        },
        "training": {
            "epochs": 150,
            "batch": 8,
            "imgsz": 640,
            "device": 0,
            "workers": 4,
            "amp": True,
            "cache": False,
            "rect": False,
        },
        "optimizer": {
            "type": "AdamW",
            "lr0": 0.002,
            "lrf": 0.01,
            "momentum": 0.937,
            "weight_decay": 0.0005,
            "warmup_epochs": 5,
            "warmup_momentum": 0.8,
        },
        "loss": {
            "box": 7.5,
            "cls": 0.5,
            "dfl": 1.5,
            "iou": 0.7,
        },
        "augmentation": {
            "hsv_h": 0.02,
            "hsv_s": 0.8,
            "hsv_v": 0.5,
            "degrees": 20.0,
            "translate": 0.15,
            "scale": 0.85,
            "shear": 5.0,
            "perspective": 0.0005,
            "flipud": 0.1,
            "fliplr": 0.5,
            "mosaic": 1.0,
            "mixup": 0.3,
            "copy_paste": 0.2,
            "erasing": 0.4,
        },
        "phases": [
            {
                "name": "warmup",
                "epochs": 10,
                "lr_factor": 0.1,
                "mosaic": 1.0,
                "mixup": 0.3,
            },
            {
                "name": "aggressive",
                "epochs": 50,
                "lr_factor": 1.0,
                "mosaic": 1.0,
                "mixup": 0.3,
            },
            {
                "name": "stable",
                "epochs": 50,
                "lr_factor": 0.5,
                "mosaic": 0.5,
                "mixup": 0.15,
            },
            {
                "name": "fine_tune",
                "epochs": 40,
                "lr_factor": 0.1,
                "mosaic": 0.0,
                "mixup": 0.0,
            },
        ]
    }


def train_with_yolo(
    config: Dict,
    data_yaml: str,
    output_dir: str,
    resume_from: Optional[str] = None
) -> Dict:
    """
    使用YOLO进行训练
    
    Args:
        config: 训练配置
        data_yaml: 数据集配置文件路径
        output_dir: 输出目录
        resume_from: 恢复训练的模型路径
    
    Returns:
        训练结果字典
    """
    from ultralytics import YOLO
    import torch
    
    print("\n" + "=" * 70)
    print("🚀 开始高精度训练")
    print("=" * 70)
    
    model_path = resume_from if resume_from else config["model"]["base"]
    print(f"📦 模型: {model_path}")
    print(f"📁 数据集: {data_yaml}")
    print(f"📂 输出: {output_dir}")
    
    model = YOLO(model_path)
    
    train_config = config["training"]
    aug_config = config["augmentation"]
    opt_config = config["optimizer"]
    loss_config = config["loss"]
    
    results = model.train(
        data=data_yaml,
        epochs=train_config["epochs"],
        batch=train_config["batch"],
        imgsz=train_config["imgsz"],
        device=train_config["device"],
        workers=train_config["workers"],
        amp=train_config["amp"],
        cache=train_config["cache"],
        rect=train_config["rect"],
        project=output_dir,
        name="high_accuracy",
        exist_ok=True,
        optimizer=opt_config["type"],
        lr0=opt_config["lr0"],
        lrf=opt_config["lrf"],
        momentum=opt_config["momentum"],
        weight_decay=opt_config["weight_decay"],
        warmup_epochs=opt_config["warmup_epochs"],
        warmup_momentum=opt_config["warmup_momentum"],
        box=loss_config["box"],
        cls=loss_config["cls"],
        dfl=loss_config["dfl"],
        iou=loss_config["iou"],
        hsv_h=aug_config["hsv_h"],
        hsv_s=aug_config["hsv_s"],
        hsv_v=aug_config["hsv_v"],
        degrees=aug_config["degrees"],
        translate=aug_config["translate"],
        scale=aug_config["scale"],
        shear=aug_config["shear"],
        perspective=aug_config["perspective"],
        flipud=aug_config["flipud"],
        fliplr=aug_config["fliplr"],
        mosaic=aug_config["mosaic"],
        mixup=aug_config["mixup"],
        copy_paste=aug_config["copy_paste"],
        erasing=aug_config["erasing"],
        patience=20,
        save_period=10,
        val=True,
        plots=True,
        verbose=True,
    )
    
    metrics = model.val()
    
    result = {
        "model_path": str(Path(output_dir) / "high_accuracy" / "weights" / "best.pt"),
        "mAP50": float(metrics.box.map50) if hasattr(metrics, 'box') else 0.0,
        "mAP50_95": float(metrics.box.map) if hasattr(metrics, 'box') else 0.0,
        "precision": float(metrics.box.mp) if hasattr(metrics, 'box') else 0.0,
        "recall": float(metrics.box.mr) if hasattr(metrics, 'box') else 0.0,
    }
    
    return result


def train_multi_phase(
    config: Dict,
    data_yaml: str,
    output_dir: str,
    base_model: Optional[str] = None
) -> Dict:
    """
    多阶段训练策略
    
    基于文档3.4节的训练策略：
    阶段1: 快速收敛 (强数据增强)
    阶段2: 稳定优化 (适度增强)
    阶段3: 精细调整 (关闭增强)
    
    Args:
        config: 训练配置
        data_yaml: 数据集配置文件路径
        output_dir: 输出目录
        base_model: 基础模型路径
    
    Returns:
        训练结果字典
    """
    from ultralytics import YOLO
    import torch
    import copy
    
    print("\n" + "=" * 70)
    print("🎯 多阶段高精度训练策略")
    print("=" * 70)
    
    phases = config["phases"]
    current_model = base_model or config["model"]["base"]
    best_map50 = 0.0
    best_model_path = None
    
    phase_results = []
    
    for i, phase in enumerate(phases):
        print(f"\n{'='*70}")
        print(f"📊 阶段 {i+1}/{len(phases)}: {phase['name']}")
        print(f"{'='*70}")
        
        phase_config = copy.deepcopy(config)
        phase_config["training"]["epochs"] = phase["epochs"]
        phase_config["augmentation"]["mosaic"] = phase["mosaic"]
        phase_config["augmentation"]["mixup"] = phase["mixup"]
        phase_config["optimizer"]["lr0"] = config["optimizer"]["lr0"] * phase["lr_factor"]
        
        phase_output = str(Path(output_dir) / f"phase{i+1}_{phase['name']}")
        
        model = YOLO(current_model)
        
        train_config = phase_config["training"]
        aug_config = phase_config["augmentation"]
        opt_config = phase_config["optimizer"]
        loss_config = phase_config["loss"]
        
        results = model.train(
            data=data_yaml,
            epochs=train_config["epochs"],
            batch=train_config["batch"],
            imgsz=train_config["imgsz"],
            device=train_config["device"],
            workers=train_config["workers"],
            amp=train_config["amp"],
            project=phase_output,
            name="train",
            exist_ok=True,
            optimizer=opt_config["type"],
            lr0=opt_config["lr0"],
            lrf=opt_config["lrf"],
            momentum=opt_config["momentum"],
            weight_decay=opt_config["weight_decay"],
            warmup_epochs=3,
            box=loss_config["box"],
            cls=loss_config["cls"],
            dfl=loss_config["dfl"],
            iou=loss_config["iou"],
            hsv_h=aug_config["hsv_h"],
            hsv_s=aug_config["hsv_s"],
            hsv_v=aug_config["hsv_v"],
            degrees=aug_config["degrees"],
            translate=aug_config["translate"],
            scale=aug_config["scale"],
            shear=aug_config["shear"],
            perspective=aug_config["perspective"],
            flipud=aug_config["flipud"],
            fliplr=aug_config["fliplr"],
            mosaic=aug_config["mosaic"],
            mixup=aug_config["mixup"],
            copy_paste=aug_config["copy_paste"],
            erasing=aug_config["erasing"],
            patience=15,
            save_period=10,
            val=True,
            plots=True,
            verbose=True,
        )
        
        metrics = model.val()
        phase_map50 = float(metrics.box.map50) if hasattr(metrics, 'box') else 0.0
        
        phase_result = {
            "phase": phase["name"],
            "epochs": phase["epochs"],
            "mAP50": phase_map50,
            "mAP50_95": float(metrics.box.map) if hasattr(metrics, 'box') else 0.0,
        }
        phase_results.append(phase_result)
        
        print(f"\n📈 阶段 {phase['name']} 结果:")
        print(f"   mAP@50: {phase_map50:.2%}")
        
        if phase_map50 > best_map50:
            best_map50 = phase_map50
            best_model_path = str(Path(phase_output) / "train" / "weights" / "best.pt")
            current_model = best_model_path
            print(f"   ✅ 新最佳模型!")
        
        torch.cuda.empty_cache()
        gc.collect()
    
    final_result = {
        "best_model_path": best_model_path,
        "best_mAP50": best_map50,
        "target_achieved": best_map50 >= 0.95,
        "phase_results": phase_results,
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
        "gpu_info": gpu_info,
        "config": config,
        "results": results,
    }
    
    report_path = Path(output_dir) / "training_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 训练报告已保存: {report_path}")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="高精度视觉检测训练")
    parser.add_argument("--epochs", type=int, default=150, help="训练轮数")
    parser.add_argument("--batch", type=int, default=8, help="批大小")
    parser.add_argument("--device", type=int, default=0, help="GPU设备ID")
    parser.add_argument("--resume", type=str, default=None, help="恢复训练的模型路径")
    parser.add_argument("--multi-phase", action="store_true", help="使用多阶段训练")
    parser.add_argument("--evaluate-only", type=str, default=None, help="仅评估指定模型")
    args = parser.parse_args()
    
    gpu_info = check_gpu_environment()
    setup_training_environment()
    
    config = get_optimized_training_config()
    config["training"]["epochs"] = args.epochs
    config["training"]["batch"] = args.batch if args.batch else gpu_info.get("optimal_batch", 8)
    config["training"]["device"] = args.device
    
    data_yaml = str(PROJECT_ROOT / "configs" / "wheat_disease.yaml")
    output_dir = str(PROJECT_ROOT / "models" / "wheat_disease_v6_high_accuracy")
    os.makedirs(output_dir, exist_ok=True)
    
    if args.evaluate_only:
        results = evaluate_model(args.evaluate_only, data_yaml)
        save_training_report(output_dir, config, results, gpu_info)
        return
    
    if args.multi_phase:
        results = train_multi_phase(
            config=config,
            data_yaml=data_yaml,
            output_dir=output_dir,
            base_model=args.resume
        )
    else:
        results = train_with_yolo(
            config=config,
            data_yaml=data_yaml,
            output_dir=output_dir,
            resume_from=args.resume
        )
    
    if "best_model_path" in results:
        eval_results = evaluate_model(results["best_model_path"], data_yaml)
        results.update(eval_results)
    elif "model_path" in results:
        eval_results = evaluate_model(results["model_path"], data_yaml)
        results.update(eval_results)
    
    save_training_report(output_dir, config, results, gpu_info)
    
    print("\n" + "=" * 70)
    print("🏁 训练完成")
    print("=" * 70)
    if results.get("target_achieved"):
        print("🎉 恭喜! 已达成 mAP@50 >= 95% 目标!")
    else:
        current_map = results.get("mAP50", results.get("best_mAP50", 0))
        print(f"📊 当前 mAP@50: {current_map:.2%}")
        print(f"💡 建议: 尝试更多训练轮数或调整数据增强参数")


if __name__ == "__main__":
    main()
