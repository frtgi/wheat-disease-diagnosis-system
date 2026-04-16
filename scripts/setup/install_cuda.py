#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CUDA Toolkit 安装脚本 (Python版本)

自动下载并安装CUDA Toolkit 12.1
"""
import os
import sys
import subprocess
import urllib.request
import tempfile
import shutil
from pathlib import Path

def print_header(text):
    """打印标题"""
    print("\n" + "="*70)
    print(f"🚀 {text}")
    print("="*70)

def print_status(text, status="info"):
    """打印状态"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }
    print(f"{icons.get(status, 'ℹ️')} {text}")

def check_cuda_installed():
    """检查CUDA是否已安装"""
    cuda_path = os.environ.get('CUDA_PATH', '')
    if cuda_path and os.path.exists(cuda_path):
        print_status(f"CUDA Toolkit已安装: {cuda_path}", "success")
        
        # 检查版本
        version_file = os.path.join(cuda_path, 'version.json')
        if os.path.exists(version_file):
            import json
            with open(version_file, 'r') as f:
                version_info = json.load(f)
                version = version_info.get('cuda', {}).get('version', 'Unknown')
                print_status(f"版本: {version}", "info")
        return True
    return False

def download_file(url, dest_path, desc="下载文件"):
    """下载文件并显示进度"""
    print_status(f"开始{desc}...", "info")
    print(f"   URL: {url}")
    print(f"   目标: {dest_path}")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 / total_size)
        mb = downloaded / 1024 / 1024
        total_mb = total_size / 1024 / 1024
        print(f"\r   进度: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end='', flush=True)
    
    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print()  # 换行
        print_status(f"{desc}完成", "success")
        return True
    except Exception as e:
        print()
        print_status(f"{desc}失败: {e}", "error")
        return False

def install_cuda_toolkit():
    """安装CUDA Toolkit"""
    print_header("CUDA Toolkit 12.1 安装")
    
    # 检查是否已安装
    if check_cuda_installed():
        print_status("CUDA Toolkit已安装，跳过安装", "success")
        return True
    
    # CUDA 12.1 下载链接
    cuda_url = "https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_531.14_windows.exe"
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    installer_path = os.path.join(temp_dir, "cuda_installer.exe")
    
    try:
        # 下载安装程序
        if not download_file(cuda_url, installer_path, "下载CUDA Toolkit"):
            print_status("下载失败，尝试使用浏览器手动下载", "error")
            print("\n请手动下载并安装:")
            print(f"   {cuda_url}")
            return False
        
        # 运行安装程序
        print_header("运行CUDA Toolkit安装程序")
        print_status("启动安装程序...", "info")
        print("   安装参数: /s /nouninstall (静默安装)")
        print("   请耐心等待，安装过程约10-15分钟...")
        print()
        
        # 使用subprocess运行安装程序
        result = subprocess.run(
            [installer_path, "/s", "/nouninstall"],
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            print_status("CUDA Toolkit 12.1 安装成功!", "success")
            
            # 设置环境变量
            cuda_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1"
            if os.path.exists(cuda_path):
                os.environ['CUDA_PATH'] = cuda_path
                os.environ['PATH'] = f"{cuda_path}\bin;{os.environ.get('PATH', '')}"
                print_status(f"CUDA路径: {cuda_path}", "info")
            
            print("\n" + "="*70)
            print("🎉 安装完成!")
            print("="*70)
            print("\n请重启终端以应用环境变量更改")
            return True
        else:
            print_status(f"安装失败，退出代码: {result.returncode}", "error")
            if result.stderr:
                print(f"错误信息: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("安装超时(30分钟)", "error")
        return False
    except Exception as e:
        print_status(f"安装出错: {e}", "error")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print_status("清理临时文件", "info")

def install_conda_cuda():
    """使用conda安装CUDA（轻量级替代方案）"""
    print_header("使用Conda安装CUDA运行时")
    
    print_status("这将安装CUDA运行时库（不包含开发工具）", "info")
    print("   命令: conda install cuda -c nvidia")
    print()
    
    try:
        result = subprocess.run(
            ["conda", "install", "cuda", "-c", "nvidia", "-y"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            print_status("CUDA运行时安装成功!", "success")
            return True
        else:
            print_status("安装失败", "error")
            print(result.stderr[-500:])
            return False
    except Exception as e:
        print_status(f"安装出错: {e}", "error")
        return False

def use_cpu_version():
    """降级到CPU版本"""
    print_header("降级到PyTorch CPU版本")
    
    print_status("这将卸载PyTorch GPU版本，安装CPU版本", "warning")
    print("   训练速度会变慢，但可以正常运行\n")
    
    commands = [
        ("pip uninstall -y torch torchvision torchaudio", "卸载GPU版本"),
        ("pip install torch torchvision torchaudio", "安装CPU版本"),
    ]
    
    for cmd, desc in commands:
        print_status(f"{desc}...", "info")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"{desc}成功", "success")
        else:
            print_status(f"{desc}失败", "error")
    
    print("\n" + "="*70)
    print("✅ PyTorch CPU版本安装完成")
    print("="*70)
    print("\n现在可以正常运行训练脚本（CPU模式）")

def main():
    """主函数"""
    print("="*70)
    print("🔧 CUDA Toolkit 安装工具")
    print("="*70)
    
    # 显示菜单
    print("\n请选择操作:")
    print("  1. 安装CUDA Toolkit 12.1 (完整版, 推荐)")
    print("  2. 使用Conda安装CUDA运行时 (轻量级)")
    print("  3. 降级到PyTorch CPU版本 (临时方案)")
    print("  4. 退出")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == "1":
        if install_cuda_toolkit():
            print("\n✅ 安装成功!")
            print("\n下一步:")
            print("  1. 重启终端")
            print("  2. 运行: python check_gpu.py")
            print("  3. 运行: python scripts/train_all_models.py --stage all")
        else:
            print("\n❌ 安装失败")
            print("\n建议:")
            print("  1. 手动下载安装CUDA Toolkit")
            print("  2. 或使用选项3降级到CPU版本")
    
    elif choice == "2":
        if install_conda_cuda():
            print("\n✅ 安装成功!")
        else:
            print("\n❌ 安装失败")
    
    elif choice == "3":
        use_cpu_version()
    
    elif choice == "4":
        print("\n退出")
    
    else:
        print("\n❌ 无效选项")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
