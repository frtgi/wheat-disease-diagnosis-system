# -*- coding: utf-8 -*-
"""
验证 MiniCPM-V 4.5 模型文件完整性
"""
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

print("=" * 60)
print("验证 MiniCPM-V 4.5 模型文件")
print("=" * 60)

from pathlib import Path
model_dir = Path(r"D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5")

print("\n[1] 模型文件检查:")
model_files = list(model_dir.glob("model-*.safetensors"))
total_size = 0
for f in sorted(model_files):
    size_gb = f.stat().st_size / (1024**3)
    total_size += size_gb
    print(f"  {f.name}: {size_gb:.2f} GB")
print(f"  总大小: {total_size:.2f} GB")

print("\n[2] Safetensors 完整性验证:")
from safetensors import safe_open
all_ok = True
for f in sorted(model_files):
    try:
        with safe_open(f, framework="pt") as sf:
            keys = list(sf.keys())
            print(f"  {f.name}: OK ({len(keys)} tensors)")
    except Exception as e:
        print(f"  {f.name}: FAILED - {e}")
        all_ok = False

print("\n[3] Tokenizer 加载测试:")
try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
    print(f"  Tokenizer: {type(tokenizer).__name__}")
    print("  [OK] Tokenizer 加载成功")
except Exception as e:
    print(f"  [FAILED] {e}")
    all_ok = False

print("\n[4] 模型配置检查:")
config_file = model_dir / "config.json"
if config_file.exists():
    import json
    with open(config_file) as f:
        config = json.load(f)
    print(f"  模型类型: {config.get('model_type', 'unknown')}")
    print(f"  架构: {config.get('architectures', ['unknown'])[0]}")
    print("  [OK] 配置文件完整")
else:
    print("  [FAILED] 配置文件不存在")
    all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("所有验证通过! 模型文件完整。")
else:
    print("部分验证失败，请检查上述错误。")
print("=" * 60)
