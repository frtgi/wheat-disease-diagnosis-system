# -*- coding: utf-8 -*-
"""
测试 MiniCPM-V 4.5 模型加载 (兼容模式)

验证模型是否可以正常加载
"""
import os
import sys
import time

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("=" * 60)
print("测试 MiniCPM-V 4.5 模型加载")
print("=" * 60)

try:
    import torch
    print(f"\n[1] PyTorch: {torch.__version__}")
    print(f"    CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"    GPU: {torch.cuda.get_device_name(0)}")
        print(f"    显存: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB")
except ImportError as e:
    print(f"[错误] PyTorch 未安装: {e}")
    sys.exit(1)

try:
    from transformers import AutoTokenizer, AutoModel
    print(f"[2] Transformers: 已安装")
except ImportError as e:
    print(f"[错误] Transformers 未安装: {e}")
    sys.exit(1)

model_path = "D:/Project/WheatAgent/models/OpenBMB/MiniCPM-V-4_5"
print(f"\n[3] 模型路径: {model_path}")

if not os.path.exists(model_path):
    print("[错误] 模型路径不存在")
    sys.exit(1)

import os
files = os.listdir(model_path)
model_files = [f for f in files if f.startswith("model-") and f.endswith(".safetensors")]
print(f"    模型文件: {len(model_files)} 个")
total_size = 0
for f in sorted(model_files):
    size = os.path.getsize(os.path.join(model_path, f)) / (1024**3)
    total_size += size
    print(f"      - {f}: {size:.2f} GB")
print(f"    总大小: {total_size:.2f} GB")

print("\n[4] 加载模型 (CPU 模式)...")
start_time = time.time()

try:
    model = AutoModel.from_pretrained(
        model_path,
        trust_remote_code=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    
    model = model.eval()
    
    load_time = time.time() - start_time
    print(f"    加载时间: {load_time:.2f} 秒")
    print("[OK] 模型加载成功!")
    
except Exception as e:
    print(f"[错误] 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[5] 加载 Tokenizer...")
try:
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )
    print("[OK] Tokenizer 加载成功!")
except Exception as e:
    print(f"[错误] Tokenizer 加载失败: {e}")
    sys.exit(1)

print("\n[6] 模型信息...")
try:
    print(f"    模型类型: {type(model).__name__}")
    print(f"    参数量: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B")
    print("[OK] 模型信息获取成功!")
except Exception as e:
    print(f"[警告] 无法获取模型信息: {e}")

print("\n" + "=" * 60)
print("MiniCPM-V 4.5 模型验证完成!")
print("=" * 60)
print("\n注意: 由于 4GB 显存限制，模型以 CPU 模式加载")
print("推理时将自动使用 CPU 或部分 GPU 加速")
