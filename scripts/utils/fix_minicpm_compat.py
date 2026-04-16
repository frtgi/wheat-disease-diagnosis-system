# -*- coding: utf-8 -*-
"""修复 MiniCPM-V 4.5 模型代码兼容性问题"""

import os

file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'OpenBMB', 'MiniCPM-V-4_5', 'modeling_minicpmv.py')
file_path = os.path.abspath(file_path)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
content = content.replace('self.all_tied_weights_keys = []', 'self.all_tied_weights_keys = {}')

if content != original:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed: all_tied_weights_keys changed from [] to {}')
else:
    print('No changes needed')
