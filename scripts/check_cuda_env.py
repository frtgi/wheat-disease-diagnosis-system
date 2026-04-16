"""
检查当前环境状态脚本
"""
import sys

def check_environment():
    print("=" * 60)
    print("环境检查报告")
    print("=" * 60)
    
    print(f"\nPython版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    print("\n" + "-" * 40)
    print("PyTorch 检查")
    print("-" * 40)
    
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"cuDNN版本: {torch.backends.cudnn.version()}")
            print(f"GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("CUDA不可用 - PyTorch为CPU版本")
    except ImportError:
        print("PyTorch未安装")
    
    print("\n" + "-" * 40)
    print("BitsAndBytes 检查")
    print("-" * 40)
    
    try:
        import bitsandbytes as bnb
        print(f"BitsAndBytes版本: {bnb.__version__}")
    except ImportError:
        print("BitsAndBytes未安装")
    
    print("\n" + "-" * 40)
    print("Transformers 检查")
    print("-" * 40)
    
    try:
        import transformers
        print(f"Transformers版本: {transformers.__version__}")
    except ImportError:
        print("Transformers未安装")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_environment()
