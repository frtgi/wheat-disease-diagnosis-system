#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查GPU环境配置
"""
import sys

def check_gpu_environment():
    """检查GPU环境"""
    print("=" * 70)
    print("🔍 GPU环境检查")
    print("=" * 70)
    
    # 检查PyTorch
    try:
        import torch
        print(f"✅ PyTorch已安装")
        print(f"   版本: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch未安装")
        return False
    
    # 检查CUDA可用性
    print("\n📊 CUDA信息:")
    if torch.cuda.is_available():
        print(f"✅ CUDA可用")
        print(f"   CUDA版本: {torch.version.cuda}")
        print(f"   cuDNN版本: {torch.backends.cudnn.version()}")
        print(f"   GPU数量: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"\n   GPU {i}:")
            print(f"   名称: {torch.cuda.get_device_name(i)}")
            print(f"   显存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
    else:
        print("❌ CUDA不可用")
        print("   可能原因:")
        print("   1. 未安装GPU驱动")
        print("   2. 未安装CUDA工具包")
        print("   3. PyTorch是CPU版本")
        return False
    
    # 检查Ultralytics
    print("\n📊 Ultralytics信息:")
    try:
        import ultralytics
        print(f"✅ Ultralytics已安装")
        print(f"   版本: {ultralytics.__version__}")
    except ImportError:
        print("❌ Ultralytics未安装")
    
    print("\n" + "=" * 70)
    return torch.cuda.is_available()

if __name__ == "__main__":
    has_gpu = check_gpu_environment()
    sys.exit(0 if has_gpu else 1)
