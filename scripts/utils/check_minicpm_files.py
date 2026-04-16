# -*- coding: utf-8 -*-
"""
检查并修复 MiniCPM-V 4.5 模型文件

验证模型文件完整性并重新下载损坏的文件
"""
import os
import sys
from pathlib import Path

model_dir = Path(r"D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5")

print("=" * 60)
print("检查 MiniCPM-V 4.5 模型文件完整性")
print("=" * 60)

# 预期的模型文件大小 (GB)
expected_sizes = {
    "model-00001-of-00004.safetensors": 4.92,
    "model-00002-of-00004.safetensors": 4.92,
    "model-00003-of-00004.safetensors": 4.92,
    "model-00004-of-00004.safetensors": 2.10,
}

print("\n模型文件检查:")
incomplete_files = []

for filename, expected_size in expected_sizes.items():
    filepath = model_dir / filename
    if filepath.exists():
        actual_size = filepath.stat().st_size / (1024**3)
        status = "OK" if actual_size >= expected_size * 0.95 else "INCOMPLETE"
        print(f"  {filename}: {actual_size:.2f} GB (预期: {expected_size:.2f} GB) [{status}]")
        if status == "INCOMPLETE":
            incomplete_files.append(filename)
    else:
        print(f"  {filename}: NOT FOUND")
        incomplete_files.append(filename)

if incomplete_files:
    print(f"\n需要重新下载: {incomplete_files}")
    
    print("\n正在下载缺失文件...")
    from modelscope.hub.file_download import model_file_download
    
    for filename in incomplete_files:
        print(f"\n下载 {filename}...")
        try:
            f = model_file_download(
                model_id='OpenBMB/MiniCPM-V-4_5',
                file_path=filename,
                cache_dir='D:/Project/WheatAgent/models'
            )
            print(f"下载完成: {f}")
            
            import shutil
            target = model_dir / filename
            if Path(f) != target:
                shutil.copy(f, target)
                print(f"复制到: {target}")
            
            actual_size = target.stat().st_size / (1024**3)
            print(f"文件大小: {actual_size:.2f} GB")
            
        except Exception as e:
            print(f"下载失败: {e}")
else:
    print("\n所有模型文件完整!")

# 检查 vocab.json
vocab_file = model_dir / "vocab.json"
if vocab_file.exists():
    vocab_size = vocab_file.stat().st_size / 1024
    print(f"\nvocab.json: {vocab_size:.1f} KB")
else:
    print("\nvocab.json: NOT FOUND")

print("\n" + "=" * 60)
