"""
检查 safetensors 文件完整性
"""
from safetensors import safe_open
import os

model_path = r'D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5'
files = [
    'model-00001-of-00004.safetensors',
    'model-00002-of-00004.safetensors',
    'model-00003-of-00004.safetensors',
    'model-00004-of-00004.safetensors'
]

print("=" * 60)
print("Safetensors 文件完整性检查")
print("=" * 60)

for f in files:
    filepath = os.path.join(model_path, f)
    print(f'\n检查: {f}')
    print(f'  大小: {os.path.getsize(filepath) / 1024**3:.2f} GB')
    try:
        with safe_open(filepath, framework='pt', device='cpu') as sf:
            keys = sf.keys()
            num_tensors = len(list(keys))
            print(f'  状态: OK (包含 {num_tensors} 个张量)')
    except Exception as e:
        print(f'  状态: 损坏')
        print(f'  错误: {e}')

print("\n" + "=" * 60)
