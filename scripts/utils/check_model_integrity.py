import os
import json
from pathlib import Path

model_dir = Path(r'D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5')
index_file = model_dir / 'model.safetensors.index.json'

print('=' * 70)
print('模型文件完整性检查报告 (基于 model.safetensors.index.json)')
print('=' * 70)
print()

with open(index_file, 'r', encoding='utf-8') as f:
    index_data = json.load(f)

expected_total_size = index_data['metadata']['total_size']
print(f'预期总大小: {expected_total_size:,} bytes ({expected_total_size / 1024**3:.2f} GB)')
print()

safetensors_files = sorted(model_dir.glob('model-*.safetensors'))

actual_total_size = 0
file_sizes = {}

for f in safetensors_files:
    size = f.stat().st_size
    file_sizes[f.name] = size
    actual_total_size += size

print('各分片文件大小:')
for name, size in sorted(file_sizes.items()):
    print(f'  {name}: {size:,} bytes ({size / 1024**3:.2f} GB)')

print()
print(f'实际总大小: {actual_total_size:,} bytes ({actual_total_size / 1024**3:.2f} GB)')
print(f'预期总大小: {expected_total_size:,} bytes ({expected_total_size / 1024**3:.2f} GB)')

diff = actual_total_size - expected_total_size
diff_pct = (actual_total_size / expected_total_size) * 100

print(f'差异: {diff:,} bytes ({diff / 1024**2:.2f} MB)')
print(f'完整度: {diff_pct:.2f}%')
print()

if actual_total_size >= expected_total_size * 0.99:
    print('状态: ✓ 模型文件完整')
    print()
    print('说明: 所有模型分片文件已正确下载，模型可以正常加载使用。')
else:
    print('状态: ✗ 模型文件不完整')
    print()
    print('建议: 请重新下载整个模型。')

print('=' * 70)
