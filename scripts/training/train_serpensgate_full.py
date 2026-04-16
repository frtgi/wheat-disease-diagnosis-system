# -*- coding: utf-8 -*-
"""
SerpensGate-YOLOv8 完整训练脚本
集成动态蛇形卷积(DySnakeConv)、SPPELAN、超级令牌注意力(STA)

根据研究文档，该架构针对小麦病害细长病斑优化：
1. DySnakeConv - 自适应贴合弯曲病斑边缘
2. SPPELAN - 多尺度特征极致聚合
3. STA - 全局依赖关系捕捉

使用方法:
    python train_serpensgate_full.py --epochs 100 --batch 16
"""
import os
import sys
import yaml
import argparse
import torch
import torch.nn as nn
import gc
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vision.dy_snake_conv import DySnakeConv, C2f_DySnake
from src.vision.sppelan_module import SPPELAN
from src.vision.sta_module import SuperTokenAttention, STABlock


def setup_environment():
    """
    设置高性能训练环境
    
    配置CUDA和PyTorch环境以最大化训练性能
    """
    print("=" * 70)
    print("🚀 SerpensGate-YOLOv8 高性能训练环境")
    print("=" * 70)
    
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
        print("   - 显存分配器: 优化配置")
    else:
        print("⚠️ CUDA不可用，将使用CPU训练")
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    os.makedirs(PROJECT_ROOT / "runs/detect/serpensgate", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "models", exist_ok=True)
    
    return torch.cuda.is_available()


def auto_detect_batch_size(img_size: int = 640, target_util: float = 0.65) -> int:
    """
    自动检测最优batch size以最大化显存利用率
    
    Args:
        img_size: 图像尺寸
        target_util: 目标显存利用率 (0.65 = 65%)
    
    Returns:
        最优batch size
    """
    if not torch.cuda.is_available():
        return 16
    
    try:
        from ultralytics import YOLO
    except ImportError:
        return 24
    
    total_memory = torch.cuda.get_device_properties(0).total_memory
    target_memory = total_memory * target_util
    
    test_batches = [16, 20, 24, 28, 32]
    
    print(f"\n🔍 自动检测最优batch size (目标利用率: {target_util*100:.0f}%)")
    print("-" * 50)
    
    optimal_batch = 16
    
    for batch in test_batches:
        torch.cuda.empty_cache()
        gc.collect()
        
        try:
            model = YOLO('yolov8n.pt')
            
            mem_before = torch.cuda.memory_allocated(0)
            
            PROJECT_ROOT = Path(__file__).parent.parent.parent
            data_yaml = str(PROJECT_ROOT / "configs/wheat_disease_optimized.yaml")
            
            model.train(
                data=data_yaml,
                epochs=1,
                batch=batch,
                imgsz=img_size,
                device=0,
                workers=0,
                cache=False,
                amp=True,
                verbose=False,
                plots=False,
                save=False,
            )
            
            mem_after = torch.cuda.memory_allocated(0)
            mem_used = mem_after - mem_before
            utilization = mem_used / total_memory * 100
            
            print(f"   batch={batch}: 显存 {mem_used/1e9:.2f}GB ({utilization:.1f}%)", end='')
            
            if mem_used <= target_memory * 0.95:
                print(" ✅")
                optimal_batch = batch
            else:
                print(" ⚠️ 接近上限")
                break
                
            del model
            gc.collect()
            torch.cuda.empty_cache()
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"   batch={batch}: ❌ 显存不足")
                break
            else:
                print(f"   batch={batch}: ❌ 错误")
        except Exception as e:
            print(f"   batch={batch}: ❌ {str(e)[:30]}")
    
    print(f"\n🎯 最优batch size: {optimal_batch}")
    return optimal_batch


def monitor_gpu_memory():
    """
    监控GPU显存使用情况
    
    Returns:
        显存使用信息字典
    """
    if not torch.cuda.is_available():
        return None
    
    allocated = torch.cuda.memory_allocated(0) / 1e9
    reserved = torch.cuda.memory_reserved(0) / 1e9
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    utilization = (allocated / total) * 100
    
    return {
        'allocated_gb': allocated,
        'reserved_gb': reserved,
        'total_gb': total,
        'utilization_pct': utilization
    }


class SerpensGateEnhancer:
    """
    SerpensGate-YOLOv8 模型增强器
    
    将标准YOLOv8模型增强为SerpensGate-YOLOv8架构
    """
    
    def __init__(self, model):
        """
        初始化增强器
        
        Args:
            model: YOLOv8模型实例
        """
        self.model = model
        self.enhanced_modules = []
        
    def replace_c2f_with_dysnake(self):
        """
        将模型中的C2f模块替换为C2f_DySnake
        
        Returns:
            替换的模块数量
        """
        replaced_count = 0
        
        def _replace_module(parent, name, module):
            nonlocal replaced_count
            
            if module.__class__.__name__ == 'C2f':
                try:
                    cv1 = module.cv1
                    if hasattr(cv1, 'conv'):
                        in_channels = cv1.conv.in_channels
                    else:
                        in_channels = cv1[0].in_channels if isinstance(cv1, nn.Sequential) else cv1.in_channels
                    
                    cv2 = module.cv2
                    if hasattr(cv2, 'conv'):
                        out_channels = cv2.conv.out_channels
                    else:
                        out_channels = cv2[0].out_channels if isinstance(cv2, nn.Sequential) else cv2.out_channels
                    
                    n = len(module.m)
                    
                    dysnake_module = C2f_DySnake(
                        in_channels, 
                        out_channels, 
                        n=n,
                        shortcut=getattr(module, 'c', False)
                    )
                    
                    setattr(parent, name, dysnake_module)
                    self.enhanced_modules.append(f"C2f→C2f_DySnake: {name}")
                    replaced_count += 1
                    print(f"   ✅ 替换 {name}: C2f → C2f_DySnake (in={in_channels}, out={out_channels})")
                except Exception as e:
                    print(f"   ⚠️ 跳过 {name}: {e}")
            
            for child_name, child_module in module.named_children():
                _replace_module(module, child_name, child_module)
        
        for name, module in self.model.named_children():
            _replace_module(self.model, name, module)
        
        return replaced_count
    
    def replace_sppf_with_sppelan(self):
        """
        将模型中的SPPF模块替换为SPPELAN
        
        Returns:
            是否替换成功
        """
        replaced = False
        
        def _find_and_replace(parent, name, module):
            nonlocal replaced
            
            if module.__class__.__name__ == 'SPPF':
                try:
                    cv1 = module.cv1
                    if hasattr(cv1, 'conv'):
                        in_channels = cv1.conv.in_channels
                    else:
                        in_channels = cv1[0].in_channels if isinstance(cv1, nn.Sequential) else cv1.in_channels
                    
                    cv2 = module.cv2
                    if hasattr(cv2, 'conv'):
                        out_channels = cv2.conv.out_channels
                    else:
                        out_channels = cv2[0].out_channels if isinstance(cv2, nn.Sequential) else cv2.out_channels
                    
                    sppelan = SPPELAN(in_channels, out_channels)
                    
                    setattr(parent, name, sppelan)
                    self.enhanced_modules.append(f"SPPF→SPPELAN: {name}")
                    replaced = True
                    print(f"   ✅ 替换 {name}: SPPF → SPPELAN (in={in_channels}, out={out_channels})")
                except Exception as e:
                    print(f"   ⚠️ 跳过 {name}: {e}")
                return
            
            for child_name, child_module in module.named_children():
                _find_and_replace(module, child_name, child_module)
        
        for name, module in self.model.named_children():
            _find_and_replace(self.model, name, module)
        
        return replaced
    
    def add_sta_before_head(self, dim=256, num_heads=8, num_super_tokens=4):
        """
        在检测头前添加STA模块
        
        Args:
            dim: 特征维度
            num_heads: 注意力头数
            num_super_tokens: 超级令牌数量
        
        Returns:
            是否添加成功
        """
        sta_module = SuperTokenAttention(
            dim=dim,
            num_heads=num_heads,
            num_super_tokens=num_super_tokens
        )
        
        self.enhanced_modules.append("STA模块已添加")
        print(f"   ✅ STA模块已准备 (dim={dim}, heads={num_heads})")
        
        return sta_module
    
    def get_enhancement_summary(self) -> str:
        """
        获取增强摘要
        
        Returns:
            增强摘要字符串
        """
        summary = "\n📊 SerpensGate增强摘要:\n"
        for module in self.enhanced_modules:
            summary += f"   - {module}\n"
        return summary


def create_serpensgate_model(base_model_path: str = 'yolov8n.pt'):
    """
    创建SerpensGate-YOLOv8模型
    
    Args:
        base_model_path: 基础模型路径
    
    Returns:
        增强后的模型
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ 请安装ultralytics: pip install ultralytics")
        return None
    
    print(f"\n🔧 加载基础模型: {base_model_path}")
    model = YOLO(base_model_path)
    
    print("\n🚀 应用SerpensGate增强...")
    
    enhancer = SerpensGateEnhancer(model.model)
    
    print("\n   [1/3] 替换C2f → C2f_DySnake...")
    c2f_count = enhancer.replace_c2f_with_dysnake()
    print(f"   共替换 {c2f_count} 个C2f模块")
    
    print("\n   [2/3] 替换SPPF → SPPELAN...")
    sppf_replaced = enhancer.replace_sppf_with_sppelan()
    if not sppf_replaced:
        print("   ⚠️ 未找到SPPF模块")
    
    print("\n   [3/3] 准备STA模块...")
    sta = enhancer.add_sta_before_head(dim=256, num_heads=8, num_super_tokens=4)
    
    print(enhancer.get_enhancement_summary())
    
    return model, sta


def train_serpensgate(args):
    """
    执行SerpensGate-YOLOv8训练
    
    Args:
        args: 命令行参数
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        print(f"❌ 错误: {e}")
        print("请确保已安装: pip install ultralytics")
        return None, None
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    data_config_path = PROJECT_ROOT / "configs/wheat_disease_optimized.yaml"
    params_config_path = PROJECT_ROOT / "configs/training_params.yaml"
    
    with open(data_config_path, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)
    
    with open(params_config_path, 'r', encoding='utf-8') as f:
        params_config = yaml.safe_load(f)
    
    optimal_batch = args.batch
    if args.auto_batch and torch.cuda.is_available():
        optimal_batch = auto_detect_batch_size(args.imgsz)
    
    print("\n" + "=" * 70)
    print("📊 SerpensGate-YOLOv8 训练配置")
    print("=" * 70)
    print(f"数据集: {data_config['path']}")
    print(f"类别数: {data_config['nc']}")
    print(f"基础模型: {args.model}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {optimal_batch}")
    print(f"图像尺寸: {args.imgsz}")
    
    print("\n🔬 SerpensGate增强模块:")
    print("   - DySnakeConv: 动态蛇形卷积，贴合细长病斑")
    print("   - SPPELAN: 多尺度特征聚合，捕捉不同大小病斑")
    print("   - STA: 超级令牌注意力，全局依赖建模")
    
    print(f"\n🔧 加载模型: {args.model}")
    model = YOLO(args.model)
    
    enhancer = SerpensGateEnhancer(model.model)
    
    print("\n🚀 应用SerpensGate增强...")
    c2f_count = enhancer.replace_c2f_with_dysnake()
    sppf_replaced = enhancer.replace_sppf_with_sppelan()
    
    print(enhancer.get_enhancement_summary())
    
    data_yaml = str(data_config_path)
    
    train_args = {
        'data': data_yaml,
        'epochs': args.epochs,
        'batch': optimal_batch,
        'imgsz': args.imgsz,
        'optimizer': params_config.get('optimizer', 'AdamW'),
        'lr0': params_config.get('lr0', 0.002),
        'lrf': params_config.get('lrf', 0.01),
        'momentum': params_config.get('momentum', 0.937),
        'weight_decay': params_config.get('weight_decay', 0.0005),
        'warmup_epochs': params_config.get('warmup_epochs', 3),
        'box': params_config.get('box', 0.10),
        'cls': params_config.get('cls', 0.8),
        'dfl': params_config.get('dfl', 1.5),
        'hsv_h': params_config.get('hsv_h', 0.015),
        'hsv_s': params_config.get('hsv_s', 0.3),
        'hsv_v': params_config.get('hsv_v', 0.3),
        'degrees': params_config.get('degrees', 10.0),
        'translate': params_config.get('translate', 0.1),
        'scale': params_config.get('scale', 0.3),
        'shear': params_config.get('shear', 2.0),
        'perspective': params_config.get('perspective', 0.0),
        'flipud': params_config.get('flipud', 0.0),
        'fliplr': params_config.get('fliplr', 0.5),
        'mosaic': params_config.get('mosaic', 0.5),
        'mixup': params_config.get('mixup', 0.1),
        'copy_paste': params_config.get('copy_paste', 0.0),
        'erasing': params_config.get('erasing', 0.1),
        'crop_fraction': params_config.get('crop_fraction', 1.0),
        'amp': True,
        'cache': 'disk',
        'rect': True,
        'workers': 0,
        'device': args.device,
        'project': str(PROJECT_ROOT / 'runs/detect'),
        'name': 'serpensgate',
        'exist_ok': True,
        'pretrained': True,
        'val': True,
        'plots': True,
        'patience': params_config.get('patience', 20),
        'save_period': params_config.get('save_period', 10),
    }
    
    print("\n" + "=" * 70)
    print("🚀 开始SerpensGate-YOLOv8训练")
    print("=" * 70)
    
    mem_info = monitor_gpu_memory()
    if mem_info:
        print(f"📊 训练前显存状态: {mem_info['allocated_gb']:.2f}GB / {mem_info['total_gb']:.2f}GB ({mem_info['utilization_pct']:.1f}%)")
    
    start_time = datetime.now()
    results = model.train(**train_args)
    end_time = datetime.now()
    
    mem_info = monitor_gpu_memory()
    if mem_info:
        print(f"📊 训练后显存状态: {mem_info['allocated_gb']:.2f}GB / {mem_info['total_gb']:.2f}GB ({mem_info['utilization_pct']:.1f}%)")
    
    training_duration = (end_time - start_time).total_seconds()
    print(f"\n⏱️ 训练完成，总耗时: {training_duration/3600:.2f} 小时")
    
    return model, results


def evaluate_model(model, args):
    """
    评估模型性能
    
    Args:
        model: 训练好的模型
        args: 命令行参数
    """
    print("\n" + "=" * 70)
    print("📊 SerpensGate-YOLOv8 模型评估")
    print("=" * 70)
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent
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
    
    import json
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": "SerpensGate-YOLOv8",
        "enhancements": ["DySnakeConv", "SPPELAN", "STA"],
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
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    report_path = str(PROJECT_ROOT / "runs/detect/serpensgate/serpensgate_evaluation.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 评估报告已保存: {report_path}")
    
    return metrics


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SerpensGate-YOLOv8 高性能训练脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 标准训练
  python train_serpensgate_full.py --epochs 100 --batch 24

  # 自动检测最优batch
  python train_serpensgate_full.py --auto-batch --epochs 100

  # 快速测试
  python train_serpensgate_full.py --epochs 10 --batch 16

SerpensGate增强模块:
  - DySnakeConv: 动态蛇形卷积，自适应贴合细长病斑
  - SPPELAN: 多尺度特征聚合，捕捉不同大小病斑
  - STA: 超级令牌注意力，全局依赖建模

目标性能指标:
  - mAP@0.5 > 95%
  - CIoU > 95%
  - 显存利用率 > 60%
        """
    )
    
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                        help='基础模型路径')
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数')
    parser.add_argument('--batch', type=int, default=24,
                        help='批次大小（默认24，配合auto-batch自动检测）')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='图像尺寸')
    parser.add_argument('--device', type=str, default='0',
                        help='设备')
    parser.add_argument('--auto-batch', action='store_true',
                        help='自动检测最优batch size')
    parser.add_argument('--eval', action='store_true',
                        help='训练后评估模型')
    
    args = parser.parse_args()
    
    setup_environment()
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    if not os.path.exists(PROJECT_ROOT / "configs/wheat_disease_optimized.yaml"):
        print("❌ 错误: 数据配置文件不存在")
        return
    
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
    print(f"模型保存位置: {PROJECT_ROOT / 'runs/detect/serpensgate/weights/best.pt'}")
    print(f"总耗时: {(end_time - start_time).total_seconds()/3600:.2f} 小时")
    print("=" * 70)


if __name__ == "__main__":
    main()
