# -*- coding: utf-8 -*-
"""
数据集命名规范化脚本

统一验证集文件命名与训练集对齐
"""
import os
import shutil
from pathlib import Path
from collections import defaultdict

# 命名映射（验证集 -> 训练集格式）
NAME_MAPPING = {
    'aphid': 'Aphid',
    'black': 'Black Rust',
    'blast': 'Blast',
    'brown': 'Brown Rust',
    'common': 'Common Root Rot',
    'fusarium': 'Fusarium Head Blight',
    'healthy': 'Healthy',
    'leaf': 'Leaf Blight',
    'mildew': 'Mildew',
    'mite': 'Mite',
    'septoria': 'Septoria',
    'smut': 'Smut',
    'stem': 'Stem fly',
    'tan': 'Tan spot',
    'yellow': 'Yellow Rust',
}

def rename_files(base_path: str, dry_run: bool = True):
    """
    重命名文件
    
    :param base_path: 基础路径
    :param dry_run: 是否只预览不执行
    """
    base = Path(base_path)
    
    renamed_count = 0
    for file_path in base.glob('*'):
        if file_path.suffix not in ['.png', '.jpg', '.txt']:
            continue
        
        # 解析文件名
        parts = file_path.stem.split('_')
        if len(parts) < 2:
            continue
        
        category = parts[0]
        
        # 检查是否需要重命名
        if category in NAME_MAPPING:
            new_category = NAME_MAPPING[category]
            # 构建新文件名
            new_name = file_path.name.replace(f"{category}_", f"{new_category}_", 1)
            new_path = file_path.parent / new_name
            
            if dry_run:
                print(f"  {file_path.name} -> {new_name}")
            else:
                file_path.rename(new_path)
            
            renamed_count += 1
    
    return renamed_count

def main():
    """主函数"""
    print("=" * 60)
    print("数据集命名规范化")
    print("=" * 60)
    
    # 验证集图像目录
    val_images = Path("datasets/wheat_data/images/val")
    val_labels = Path("datasets/wheat_data/labels/val")
    
    # 先预览
    print("\n预览重命名（图像）:")
    print("-" * 40)
    count_images = rename_files(val_images, dry_run=True)
    
    print("\n预览重命名（标签）:")
    print("-" * 40)
    count_labels = rename_files(val_labels, dry_run=True)
    
    # 确认执行
    print("\n" + "=" * 60)
    response = input("是否执行重命名? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n执行重命名...")
        rename_files(val_images, dry_run=False)
        rename_files(val_labels, dry_run=False)
        print("完成!")
    else:
        print("已取消")

if __name__ == "__main__":
    main()
