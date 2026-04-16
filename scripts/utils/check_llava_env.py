# -*- coding: utf-8 -*-
"""
LLaVA 微调环境检查脚本
"""
import sys
import json
from pathlib import Path

def check_environment():
    """检查 LLaVA 微调环境"""
    print("=" * 60)
    print("🔍 IWDDA LLaVA 微调环境检查")
    print("=" * 60)
    
    print("\n[1] Python 版本")
    print(f"    {sys.version}")
    
    print("\n[2] 核心依赖检查")
    dependencies = {
        'transformers': None,
        'peft': None,
        'accelerate': None,
        'bitsandbytes': None,
        'torch': None
    }
    
    for pkg in dependencies:
        try:
            module = __import__(pkg)
            version = getattr(module, '__version__', 'unknown')
            dependencies[pkg] = version
            print(f"    ✅ {pkg}: {version}")
        except ImportError:
            print(f"    ❌ {pkg}: 未安装")
    
    print("\n[3] 数据集检查")
    data_dir = Path("D:/Project/WheatAgent/datasets/agroinstruct")
    train_file = data_dir / "agroinstruct_train.json"
    val_file = data_dir / "agroinstruct_val.json"
    
    if train_file.exists():
        with open(train_file, 'r', encoding='utf-8') as f:
            train_data = json.load(f)
        print(f"    ✅ 训练集: {len(train_data)} 条样本")
    else:
        print(f"    ❌ 训练集文件不存在")
    
    if val_file.exists():
        with open(val_file, 'r', encoding='utf-8') as f:
            val_data = json.load(f)
        print(f"    ✅ 验证集: {len(val_data)} 条样本")
    else:
        print(f"    ❌ 验证集文件不存在")
    
    print("\n[4] 模型文件检查")
    model_dir = Path("D:/Project/WheatAgent/models/agri_llava")
    model_files = ["adapter_config.json", "config.json", "model.pt", "projection_layer.pt"]
    
    for f in model_files:
        file_path = model_dir / f
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"    ✅ {f}: {size_mb:.2f} MB")
        else:
            print(f"    ❌ {f}: 不存在")
    
    print("\n[5] GPU 检查")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"    ✅ CUDA 可用")
            print(f"    GPU: {torch.cuda.get_device_name(0)}")
            print(f"    显存: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB")
        else:
            print(f"    ❌ CUDA 不可用")
    except Exception as e:
        print(f"    ❌ GPU 检查失败: {e}")
    
    print("\n" + "=" * 60)
    print("环境检查完成")
    print("=" * 60)

if __name__ == "__main__":
    check_environment()
