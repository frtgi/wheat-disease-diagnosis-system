# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/fix_label_filenames.py
"""
修复标签文件名格式
将 *.png.txt 重命名为 *.txt
"""

import os
import shutil

def fix_label_filenames(labels_dir):
    """
    修复标签文件名
    """
    print(f"🔧 正在修复标签文件名: {labels_dir}")
    
    # 获取所有标签文件
    label_files = [f for f in os.listdir(labels_dir) if f.endswith('.png.txt')]
    
    if not label_files:
        print("✅ 没有需要修复的标签文件")
        return
    
    print(f"📋 找到 {len(label_files)} 个需要修复的标签文件")
    
    # 重命名文件
    for old_name in label_files:
        old_path = os.path.join(labels_dir, old_name)
        new_name = old_name.replace('.png.txt', '.txt')
        new_path = os.path.join(labels_dir, new_name)
        
        # 检查新文件是否已存在
        if os.path.exists(new_path):
            print(f"⚠️ 文件已存在，跳过: {new_name}")
            continue
        
        # 重命名
        shutil.move(old_path, new_path)
        print(f"✅ 重命名: {old_name} -> {new_name}")
    
    print(f"✅ 标签文件名修复完成！")

def main():
    """
    主函数
    """
    # 修复训练集标签
    train_labels_dir = "datasets/wheat_data/labels/train"
    if os.path.exists(train_labels_dir):
        fix_label_filenames(train_labels_dir)
    
    # 修复验证集标签
    val_labels_dir = "datasets/wheat_data/labels/val"
    if os.path.exists(val_labels_dir):
        fix_label_filenames(val_labels_dir)

if __name__ == "__main__":
    main()
