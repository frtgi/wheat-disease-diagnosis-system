#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复CUDA DLL加载错误

问题: [WinError 126] 找不到指定的模块。Error loading "caffe2_nvrtc.dll"
原因: 
1. 缺少NVIDIA GPU驱动
2. 缺少CUDA运行时库
3. 缺少Visual C++ Redistributable

解决方案:
1. 安装/更新NVIDIA驱动
2. 安装CUDA Toolkit
3. 安装Visual C++ Redistributable
"""
import os
import sys
import subprocess
import urllib.request

def check_nvidia_driver():
    """检查NVIDIA驱动"""
    print("=" * 70)
    print("🔍 检查NVIDIA驱动")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print("✅ NVIDIA驱动已安装")
            print(result.stdout[:500])
            return True
        else:
            print("❌ NVIDIA驱动未安装或未找到")
            return False
    except Exception as e:
        print(f"❌ 检查驱动失败: {e}")
        return False

def check_cuda_toolkit():
    """检查CUDA Toolkit"""
    print("\n" + "=" * 70)
    print("🔍 检查CUDA Toolkit")
    print("=" * 70)
    
    cuda_path = os.environ.get('CUDA_PATH', '')
    if cuda_path and os.path.exists(cuda_path):
        print(f"✅ CUDA Toolkit路径: {cuda_path}")
        
        # 检查版本
        version_file = os.path.join(cuda_path, 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                import json
                version_info = json.load(f)
                print(f"   CUDA版本: {version_info.get('cuda', {}).get('version', 'Unknown')}")
        
        return True
    else:
        print("❌ CUDA Toolkit未安装")
        print("   环境变量CUDA_PATH未设置")
        return False

def check_visual_cpp():
    """检查Visual C++ Redistributable"""
    print("\n" + "=" * 70)
    print("🔍 检查Visual C++ Redistributable")
    print("=" * 70)
    
    # 检查常见的VC++运行时DLL
    system32 = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
    
    required_dlls = [
        'msvcp140.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll',
    ]
    
    missing = []
    for dll in required_dlls:
        dll_path = os.path.join(system32, dll)
        if os.path.exists(dll_path):
            print(f"✅ {dll}")
        else:
            print(f"❌ {dll} - 缺失")
            missing.append(dll)
    
    if missing:
        print("\n⚠️ 缺少Visual C++ Redistributable")
        return False
    else:
        print("\n✅ Visual C++ Redistributable已安装")
        return True

def install_visual_cpp():
    """安装Visual C++ Redistributable"""
    print("\n" + "=" * 70)
    print("📦 安装Visual C++ Redistributable")
    print("=" * 70)
    
    vc_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    installer_path = "vc_redist.x64.exe"
    
    try:
        print(f"下载: {vc_url}")
        urllib.request.urlretrieve(vc_url, installer_path)
        print(f"✅ 下载完成: {installer_path}")
        print(f"\n请手动运行安装程序: {installer_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print("\n请手动下载安装:")
        print("https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return False

def fix_pytorch_cpu():
    """降级到PyTorch CPU版本作为临时解决方案"""
    print("\n" + "=" * 70)
    print("🔧 降级到PyTorch CPU版本（临时解决方案）")
    print("=" * 70)
    
    print("\n这将卸载PyTorch GPU版本，安装CPU版本")
    print("训练速度会变慢，但可以正常运行\n")
    
    commands = [
        "pip uninstall -y torch torchvision torchaudio",
        "pip install torch torchvision torchaudio",
    ]
    
    for cmd in commands:
        print(f"执行: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 成功")
        else:
            print(f"❌ 失败: {result.stderr[:200]}")
    
    print("\n✅ PyTorch CPU版本安装完成")
    print("现在可以正常运行训练脚本（CPU模式）")

def print_solutions():
    """打印解决方案"""
    print("\n" + "=" * 70)
    print("🔧 解决方案")
    print("=" * 70)
    
    print("\n方案1: 安装NVIDIA驱动（推荐）")
    print("-" * 50)
    print("1. 访问 https://www.nvidia.com/drivers")
    print("2. 选择您的GPU型号")
    print("3. 下载并安装最新驱动")
    
    print("\n方案2: 安装CUDA Toolkit")
    print("-" * 50)
    print("1. 访问 https://developer.nvidia.com/cuda-downloads")
    print("2. 选择CUDA 12.1版本")
    print("3. 下载并安装")
    
    print("\n方案3: 安装Visual C++ Redistributable")
    print("-" * 50)
    print("1. 访问 https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("2. 下载并安装")
    
    print("\n方案4: 使用CPU版本（临时）")
    print("-" * 50)
    print("运行: python fix_cuda_dll.py --cpu")
    print("这将安装PyTorch CPU版本，训练速度较慢但可正常运行")

def main():
    """主函数"""
    print("=" * 70)
    print("🔧 CUDA DLL错误修复工具")
    print("=" * 70)
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--cpu':
        fix_pytorch_cpu()
        return 0
    
    # 执行检查
    has_driver = check_nvidia_driver()
    has_cuda = check_cuda_toolkit()
    has_vc = check_visual_cpp()
    
    # 打印检查结果
    print("\n" + "=" * 70)
    print("📊 检查结果")
    print("=" * 70)
    print(f"NVIDIA驱动: {'✅' if has_driver else '❌'}")
    print(f"CUDA Toolkit: {'✅' if has_cuda else '❌'}")
    print(f"Visual C++: {'✅' if has_vc else '❌'}")
    
    # 如果都正常，可能是其他问题
    if has_driver and has_cuda and has_vc:
        print("\n✅ 所有组件都已安装")
        print("\n可能原因:")
        print("1. PyTorch版本与CUDA版本不匹配")
        print("2. 环境变量配置问题")
        print("3. 需要重启终端或系统")
        print("\n建议:")
        print("1. 重启终端")
        print("2. 重新安装PyTorch:")
        print("   pip uninstall -y torch torchvision torchaudio")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    else:
        print_solutions()
        
        # 如果缺少VC++，提供自动下载
        if not has_vc:
            print("\n是否自动下载Visual C++ Redistributable? (y/n)")
            response = input().strip().lower()
            if response == 'y':
                install_visual_cpp()
    
    print("\n" + "=" * 70)
    print("💡 临时解决方案")
    print("=" * 70)
    print("如果无法立即安装GPU驱动，可以使用CPU版本:")
    print("  python fix_cuda_dll.py --cpu")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
