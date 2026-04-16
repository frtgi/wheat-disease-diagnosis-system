#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU环境配置脚本

用于安装PyTorch GPU版本和相关依赖
"""
import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并打印输出"""
    print(f"\n{'='*70}")
    print(f"🚀 {description}")
    print(f"{'='*70}")
    print(f"执行: {command}")
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ {description}成功")
        if result.stdout:
            print(result.stdout[-500:])  # 只显示最后500字符
        return True
    else:
        print(f"❌ {description}失败")
        print(f"错误: {result.stderr[-500:]}")
        return False

def install_pytorch_gpu():
    """安装PyTorch GPU版本"""
    print("\n" + "="*70)
    print("🔧 安装PyTorch GPU版本")
    print("="*70)
    
    # 先卸载CPU版本
    print("\n📦 卸载PyTorch CPU版本...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"], 
                   capture_output=True)
    
    # 安装GPU版本 (CUDA 12.1)
    print("\n📦 安装PyTorch GPU版本 (CUDA 12.1)...")
    command = "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    
    if run_command(command, "PyTorch GPU安装"):
        print("\n✅ PyTorch GPU版本安装完成")
        return True
    else:
        print("\n❌ PyTorch GPU版本安装失败")
        return False

def install_ultralytics():
    """安装/更新Ultralytics"""
    print("\n" + "="*70)
    print("🔧 安装Ultralytics")
    print("="*70)
    
    command = "pip install ultralytics"
    return run_command(command, "Ultralytics安装")

def verify_installation():
    """验证安装"""
    print("\n" + "="*70)
    print("🔍 验证GPU安装")
    print("="*70)
    
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA可用")
            print(f"   CUDA版本: {torch.version.cuda}")
            print(f"   GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("❌ CUDA仍不可用")
            return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("="*70)
    print("🚀 WheatAgent GPU环境配置")
    print("="*70)
    
    # 检查当前环境
    print("\n📊 当前环境检查...")
    try:
        import torch
        print(f"当前PyTorch版本: {torch.__version__}")
        if torch.cuda.is_available():
            print("✅ GPU已可用，无需重新安装")
            return 0
    except:
        pass
    
    # 安装PyTorch GPU
    if not install_pytorch_gpu():
        print("\n❌ PyTorch GPU安装失败，请手动安装")
        print("参考: https://pytorch.org/get-started/locally/")
        return 1
    
    # 安装Ultralytics
    install_ultralytics()
    
    # 验证安装
    if verify_installation():
        print("\n" + "="*70)
        print("🎉 GPU环境配置成功！")
        print("="*70)
        print("\n现在可以使用GPU加速训练了:")
        print("  python scripts/train_all_models.py --stage all")
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️ GPU环境配置可能有问题")
        print("="*70)
        print("\n可能原因:")
        print("1. 未安装NVIDIA GPU驱动")
        print("2. GPU不支持CUDA")
        print("3. 需要重启终端")
        return 1

if __name__ == "__main__":
    sys.exit(main())
