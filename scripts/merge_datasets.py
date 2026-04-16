# -*- coding: utf-8 -*-
"""
数据集合并脚本

合并多个数据集到统一目录，统一命名规范
"""
import os
import shutil
import random
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent

# 类别映射（统一命名）
CLASS_MAPPING = {
    'Aphid': 0,
    'Black Rust': 1,
    'Blast': 2,
    'Brown Rust': 3,
    'Common Root Rot': 4,
    'Fusarium Head Blight': 5,
    'Healthy': 6,
    'Leaf Blight': 7,
    'Mildew': 8,
    'Mite': 9,
    'Septoria': 10,
    'Smut': 11,
    'Stem fly': 12,
    'Tan spot': 13,
    'Yellow Rust': 14,
}

# 别名映射
ALIAS_MAPPING = {
    'aphid': 'Aphid',
    'black_rust': 'Black Rust',
    'black': 'Black Rust',
    'blast': 'Blast',
    'brown_rust': 'Brown Rust',
    'brown': 'Brown Rust',
    'common_root_rot': 'Common Root Rot',
    'common': 'Common Root Rot',
    'fusarium': 'Fusarium Head Blight',
    'fusarium_head_blight': 'Fusarium Head Blight',
    'healthy': 'Healthy',
    'leaf_blight': 'Leaf Blight',
    'leaf': 'Leaf Blight',
    'mildew': 'Mildew',
    'mite': 'Mite',
    'septoria': 'Septoria',
    'smut': 'Smut',
    'stem_fly': 'Stem fly',
    'stem': 'Stem fly',
    'tan_spot': 'Tan spot',
    'tan': 'Tan spot',
    'yellow_rust': 'Yellow Rust',
    'yellow': 'Yellow Rust',
    'stripe_rust': 'Yellow Rust',
}


def get_class_name(filename: str) -> str:
    """从文件名提取类别名"""
    parts = filename.split('_')
    if len(parts) >= 1:
        class_part = parts[0]
        return ALIAS_MAPPING.get(class_part.lower(), class_part)
    return 'Unknown'


def merge_datasets(
    source_dirs: List[str],
    output_dir: str,
    train_ratio: float = 0.8,
    copy_files: bool = True
):
    """
    合并多个数据集
    
    :param source_dirs: 源数据集目录列表
    :param output_dir: 输出目录
    :param train_ratio: 训练集比例
    :param copy_files: 是否复制文件（False则移动）
    """
    print("=" * 60)
    print("数据集合并工具")
    print("=" * 60)
    
    output_path = Path(output_dir)
    train_images = output_path / "images" / "train"
    train_labels = output_path / "labels" / "train"
    val_images = output_path / "images" / "val"
    val_labels = output_path / "labels" / "val"
    
    for d in [train_images, train_labels, val_images, val_labels]:
        d.mkdir(parents=True, exist_ok=True)
    
    # 收集所有图像
    all_images = defaultdict(list)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"  跳过不存在的目录: {source_dir}")
            continue
        
        # 搜索图像文件
        for ext in image_extensions:
            for img_path in source_path.rglob(f'*{ext}'):
                class_name = get_class_name(img_path.stem)
                if class_name in CLASS_MAPPING:
                    # 查找对应的标签文件
                    label_path = img_path.parent.parent / "labels" / (img_path.stem + '.txt')
                    if not label_path.exists():
                        label_path = img_path.parent / (img_path.stem + '.txt')
                    
                    all_images[class_name].append({
                        'image': img_path,
                        'label': label_path if label_path.exists() else None
                    })
    
    # 统计
    print(f"\n收集到的图像:")
    total = 0
    for class_name, images in sorted(all_images.items()):
        print(f"  {class_name}: {len(images)}")
        total += len(images)
    print(f"  总计: {total}")
    
    # 划分并复制
    print(f"\n划分数据集 (训练:{train_ratio*100:.0f}%, 验证:{(1-train_ratio)*100:.0f}%)...")
    
    train_count = 0
    val_count = 0
    class_id_map = {}
    
    for class_name, images in all_images.items():
        class_id = CLASS_MAPPING[class_name]
        class_id_map[class_name] = class_id
        
        random.shuffle(images)
        split_idx = int(len(images) * train_ratio)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]
        
        # 处理训练集
        for i, item in enumerate(train_imgs):
            img_src = item['image']
            label_src = item['label']
            
            # 复制图像
            img_dst = train_images / f"{class_name}_{i}{img_src.suffix}"
            if copy_files:
                shutil.copy(img_src, img_dst)
            else:
                shutil.move(img_src, img_dst)
            
            # 创建标签
            label_dst = train_labels / f"{class_name}_{i}.txt"
            if label_src and label_src.exists():
                if copy_files:
                    shutil.copy(label_src, label_dst)
                else:
                    shutil.move(label_src, label_dst)
            else:
                # 创建全图标注
                with open(label_dst, 'w') as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            train_count += 1
        
        # 处理验证集
        for i, item in enumerate(val_imgs):
            img_src = item['image']
            label_src = item['label']
            
            img_dst = val_images / f"{class_name}_{i}{img_src.suffix}"
            if copy_files:
                shutil.copy(img_src, img_dst)
            else:
                shutil.move(img_src, img_dst)
            
            label_dst = val_labels / f"{class_name}_{i}.txt"
            if label_src and label_src.exists():
                if copy_files:
                    shutil.copy(label_src, label_dst)
                else:
                    shutil.move(label_src, label_dst)
            else:
                with open(label_dst, 'w') as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            val_count += 1
        
        print(f"  {class_name}: 训练 {len(train_imgs)}, 验证 {len(val_imgs)}")
    
    print(f"\n总计: 训练 {train_count}, 验证 {val_count}")
    
    # 创建配置文件
    create_dataset_yaml(output_path, class_id_map)
    
    return train_count, val_count


def create_dataset_yaml(output_path: Path, class_id_map: Dict[str, int]):
    """创建数据集配置文件"""
    sorted_classes = sorted(class_id_map.items(), key=lambda x: x[1])
    
    yaml_content = f"""# Wheat Disease Unified Dataset Configuration
# Auto-generated by merge_datasets.py

path: {output_path.absolute()}
train: images/train
val: images/val
test: images/val

nc: {len(class_id_map)}

names:
"""
    for class_name, class_id in sorted_classes:
        yaml_content += f"  {class_id}: {class_name}\n"
    
    yaml_content += """
# Training parameters
box: 0.05
cls: 0.5
fliplr: 0.5
"""
    
    yaml_path = output_path / "dataset.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"\n配置文件已创建: {yaml_path}")


def main():
    """主函数"""
    source_dirs = [
        PROJECT_ROOT / "datasets" / "wheat_data",
        PROJECT_ROOT / "datasets" / "wheat_data_new",
    ]
    
    output_dir = PROJECT_ROOT / "datasets" / "wheat_data_unified"
    
    merge_datasets(
        source_dirs=[str(d) for d in source_dirs],
        output_dir=str(output_dir),
        train_ratio=0.8,
        copy_files=True
    )
    
    print("\n" + "=" * 60)
    print("数据集合并完成!")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
