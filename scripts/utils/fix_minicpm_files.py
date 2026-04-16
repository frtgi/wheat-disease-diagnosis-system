# -*- coding: utf-8 -*-
"""
修复 MiniCPM-V 4.5 模型文件

将临时目录中的部分下载文件移动到正确位置
"""
import shutil
from pathlib import Path

temp_dir = Path(r"D:\Project\WheatAgent\models\._____temp\OpenBMB\MiniCPM-V-4_5")
target_dir = Path(r"D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5")

print("=" * 60)
print("修复 MiniCPM-V 4.5 模型文件")
print("=" * 60)

# 检查临时目录
if temp_dir.exists():
    print(f"\n临时目录: {temp_dir}")
    
    for f in temp_dir.iterdir():
        if f.is_file():
            target_file = target_dir / f.name
            if not target_file.exists():
                print(f"  复制: {f.name} ({f.stat().st_size / (1024**3):.2f} GB)")
                shutil.copy(f, target_file)
            else:
                print(f"  已存在: {f.name}")
else:
    print("临时目录不存在")

# 检查目标目录
print(f"\n目标目录: {target_dir}")
print("\n模型文件状态:")

model_files = list(target_dir.glob("model-*.safetensors"))
for f in sorted(model_files):
    size_gb = f.stat().st_size / (1024**3)
    print(f"  {f.name}: {size_gb:.2f} GB")

# 检查是否所有文件都存在
expected_files = [
    "model-00001-of-00004.safetensors",
    "model-00002-of-00004.safetensors",
    "model-00003-of-00004.safetensors",
    "model-00004-of-00004.safetensors",
]

missing = []
for f in expected_files:
    if not (target_dir / f).exists():
        missing.append(f)

if missing:
    print(f"\n缺失文件: {missing}")
    print("需要重新下载")
else:
    print("\n所有模型文件已完整!")

# 检查 vocab.json
vocab_file = target_dir / "vocab.json"
if not vocab_file.exists():
    print("\n缺失 vocab.json，需要下载")
else:
    print(f"\nvocab.json: {vocab_file.stat().st_size / 1024:.1f} KB")

print("\n" + "=" * 60)
