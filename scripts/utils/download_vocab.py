# -*- coding: utf-8 -*-
"""
下载 MiniCPM-V 4.5 缺失文件

下载 vocab.json 文件
"""
from modelscope.hub.file_download import model_file_download
import os

os.environ['MODELSCOPE_CACHE'] = 'D:/Project/WheatAgent/models'

print("下载 vocab.json...")
f = model_file_download(
    model_id='OpenBMB/MiniCPM-V-4_5',
    file_path='vocab.json',
    cache_dir='D:/Project/WheatAgent/models'
)
print(f"下载完成: {f}")

import shutil
from pathlib import Path
target = Path("D:/Project/WheatAgent/models/OpenBMB/MiniCPM-V-4_5/vocab.json")
if Path(f) != target:
    shutil.copy(f, target)
    print(f"复制到: {target}")

print(f"文件大小: {target.stat().st_size / 1024:.1f} KB")
