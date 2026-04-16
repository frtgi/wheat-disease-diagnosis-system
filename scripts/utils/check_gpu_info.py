# -*- coding: utf-8 -*-
"""检查 GPU 和显存信息"""
import torch

print("=" * 60)
print("GPU 和显存信息检查")
print("=" * 60)

if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    gpu_mem_allocated = torch.cuda.memory_allocated(0) / 1024**3
    gpu_mem_free = torch.cuda.mem_get_info(0)[0] / 1024**3
    
    print(f"GPU 型号：{gpu_name}")
    print(f"显存总量：{gpu_mem_total:.2f} GB")
    print(f"显存已用：{gpu_mem_allocated:.2f} GB")
    print(f"显存可用：{gpu_mem_free:.2f} GB")
    print(f"CUDA 版本：{torch.version.cuda}")
    print(f"CUDA 计算能力：{torch.cuda.get_device_capability()[0]}.{torch.cuda.get_device_capability()[1]}")
else:
    print("❌ 未检测到 GPU")

print("=" * 60)

# 检查 bitsandbytes 是否安装
print("\n检查 INT4 量化依赖...")
try:
    import bitsandbytes as bnb
    print(f"✅ bitsandbytes 已安装，版本：{bnb.__version__}")
except ImportError:
    print("❌ bitsandbytes 未安装")

# 检查 transformers 是否安装
try:
    import transformers
    print(f"✅ transformers 已安装，版本：{transformers.__version__}")
except ImportError:
    print("❌ transformers 未安装")

print("=" * 60)

# INT4 量化需求分析
print("\nINT4 量化需求分析:")
print("-" * 60)
print("Qwen3.5-4B INT4 量化显存需求:")
print("  - 模型权重：~3 GB")
print("  - 激活值：~0.5-1 GB")
print("  - 缓存：~0.5 GB")
print("  - 总计：~4-4.5 GB")
print("-" * 60)

if torch.cuda.is_available():
    if gpu_mem_total >= 8:
        print(f"✅ 您的显存 ({gpu_mem_total:.2f} GB) 充足，可以流畅运行 INT4 量化")
        print("   建议：启用 INT4 量化，显存占用约 4GB")
    elif gpu_mem_total >= 6:
        print(f"⚠️ 您的显存 ({gpu_mem_total:.2f} GB) 勉强够用")
        print("   建议：可以运行 INT4 量化，但需要关闭其他 GPU 应用")
        print("   优化：使用 CPU offload 混合模式")
    elif gpu_mem_total >= 4:
        print(f"⚠️ 您的显存 ({gpu_mem_total:.2f} GB) 紧张")
        print("   建议：可以运行 INT4 量化，但需要启用 CPU offload")
        print("   注意：推理速度会降低，但保证可以运行")
    else:
        print(f"❌ 您的显存 ({gpu_mem_total:.2f} GB) 不足")
        print("   建议：使用 CPU 模式或升级 GPU")

print("=" * 60)
