"""
修复 MiniCPM-V 4.5 模型兼容性问题

添加缺失的 all_tied_weights_keys 属性
"""
import os

model_path = r"D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5"
modeling_file = os.path.join(model_path, "modeling_minicpmv.py")

with open(modeling_file, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = "        self.terminators = ['<|im_end|>', '']"
new_text = "        self.terminators = ['<|im_end|>', '']\n        self.all_tied_weights_keys = []"

if 'all_tied_weights_keys' in content:
    print("all_tied_weights_keys 已存在，无需修改")
else:
    if old_text in content:
        content = content.replace(old_text, new_text)
        with open(modeling_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("修复成功！已添加 all_tied_weights_keys 属性")
    else:
        print("未找到目标文本，尝试其他方式...")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'self.terminators' in line and '<|im_end|>' in line:
                print(f"找到 terminators 行: {i+1}")
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + 'self.all_tied_weights_keys = []'
                lines.insert(i + 1, new_line)
                print(f"在第 {i+2} 行插入新属性")
                break
        
        content = '\n'.join(lines)
        with open(modeling_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("修复完成！")
