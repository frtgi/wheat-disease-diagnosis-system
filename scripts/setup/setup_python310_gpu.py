#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python 3.10 + GPU 环境配置脚本

完整流程：
1. 创建Python 3.10 conda环境
2. 安装PyTorch GPU版本
3. 安装项目依赖
4. 验证GPU可用性
"""
import subprocess
import sys
import os

def run_command(command, description, shell=True):
    """运行命令并打印输出"""
    print(f"\n{'='*70}")
    print(f"🚀 {description}")
    print(f"{'='*70}")
    print(f"执行: {command}\n")
    
    result = subprocess.run(
        command,
        shell=shell,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout[-1000:])  # 显示最后1000字符
    
    if result.returncode == 0:
        print(f"\n✅ {description}成功")
        return True
    else:
        print(f"\n❌ {description}失败")
        if result.stderr:
            print(f"错误: {result.stderr[-500:]}")
        return False

def check_conda():
    """检查conda是否安装"""
    result = subprocess.run("conda --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Conda已安装: {result.stdout.strip()}")
        return True
    else:
        print("❌ Conda未安装")
        print("请先安装Anaconda或Miniconda:")
        print("  https://docs.conda.io/en/latest/miniconda.html")
        return False

def create_python310_env():
    """创建Python 3.10环境"""
    print("\n" + "="*70)
    print("🔧 创建Python 3.10环境")
    print("="*70)
    
    env_name = "wheatagent-py310"
    
    # 删除已存在的环境
    print(f"\n📦 删除已存在的环境 {env_name}...")
    subprocess.run(f"conda env remove -n {env_name} -y", shell=True, capture_output=True)
    
    # 创建新环境
    print(f"\n📦 创建Python 3.10环境...")
    command = f"conda create -n {env_name} python=3.10 -y"
    
    if run_command(command, "创建Python 3.10环境"):
        print(f"\n✅ 环境 {env_name} 创建成功")
        return env_name
    else:
        print(f"\n❌ 环境创建失败")
        return None

def install_pytorch_gpu(env_name):
    """安装PyTorch GPU版本"""
    print("\n" + "="*70)
    print("🔧 安装PyTorch GPU版本")
    print("="*70)
    
    # 使用conda安装PyTorch GPU
    command = f"conda run -n {env_name} pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    
    return run_command(command, "PyTorch GPU安装")

def install_dependencies(env_name):
    """安装项目依赖"""
    print("\n" + "="*70)
    print("🔧 安装项目依赖")
    print("="*70)
    
    # 基础依赖
    base_packages = [
        "ultralytics",
        "transformers",
        "datasets",
        "accelerate",
        "peft",
        "neo4j",
        "torch-geometric",
        "pillow",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "tqdm",
        "pyyaml",
        "requests",
        "gradio",
        "fastapi",
        "uvicorn",
        "pydantic",
        "scikit-learn",
        "opencv-python",
        "albumentations",
        "tensorboard",
        "wandb",
    ]
    
    command = f"conda run -n {env_name} pip install {' '.join(base_packages)}"
    
    return run_command(command, "安装基础依赖")

def verify_gpu(env_name):
    """验证GPU可用性"""
    print("\n" + "="*70)
    print("🔍 验证GPU环境")
    print("="*70)
    
    verify_script = """
import torch
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"cuDNN版本: {torch.backends.cudnn.version()}")
    print(f"GPU数量: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"显存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
else:
    print("❌ CUDA不可用")
    exit(1)
"""
    
    command = f"conda run -n {env_name} python -c \"{verify_script}\""
    
    return run_command(command, "GPU验证")

def create_activation_script(env_name):
    """创建环境激活脚本"""
    script_content = f"""@echo off
echo ============================================
echo 激活WheatAgent Python 3.10 GPU环境
echo ============================================
echo.
conda activate {env_name}
echo.
echo 环境已激活！
echo 现在可以运行训练脚本:
echo   python scripts/train_all_models.py --stage all
echo.
cmd /k
"""
    
    with open("activate_env.bat", "w") as f:
        f.write(script_content)
    
    print(f"\n✅ 创建激活脚本: activate_env.bat")

def update_requirements():
    """更新requirements.txt指定Python 3.10"""
    req_file = "requirements.txt"
    
    if os.path.exists(req_file):
        with open(req_file, "r") as f:
            content = f.read()
        
        # 添加Python版本说明
        if "# Python 3.10" not in content:
            content = "# Python 3.10+ required for GPU support\n" + content
            
            with open(req_file, "w") as f:
                f.write(content)
            
            print(f"\n✅ 更新 {req_file}")

def main():
    """主函数"""
    print("="*70)
    print("🚀 WheatAgent Python 3.10 + GPU 环境配置")
    print("="*70)
    
    # 检查conda
    if not check_conda():
        return 1
    
    # 创建Python 3.10环境
    env_name = create_python310_env()
    if not env_name:
        return 1
    
    # 安装PyTorch GPU
    if not install_pytorch_gpu(env_name):
        print("\n⚠️ PyTorch GPU安装失败，尝试CPU版本...")
        command = f"conda run -n {env_name} pip install torch torchvision torchaudio"
        run_command(command, "PyTorch CPU安装")
    
    # 安装依赖
    if not install_dependencies(env_name):
        print("\n⚠️ 部分依赖安装失败")
    
    # 验证GPU
    if verify_gpu(env_name):
        print("\n" + "="*70)
        print("🎉 Python 3.10 + GPU 环境配置成功！")
        print("="*70)
        
        # 创建激活脚本
        create_activation_script(env_name)
        
        # 更新requirements
        update_requirements()
        
        print(f"\n环境名称: {env_name}")
        print("\n使用方法:")
        print("1. 激活环境:")
        print(f"   conda activate {env_name}")
        print("\n2. 运行训练:")
        print("   python scripts/train_all_models.py --stage all")
        print("\n3. 或使用激活脚本:")
        print("   双击运行 activate_env.bat")
        
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️ GPU验证失败")
        print("="*70)
        print("\n可能原因:")
        print("1. 未安装NVIDIA GPU驱动")
        print("2. GPU不支持CUDA")
        print("3. 需要重启终端")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
