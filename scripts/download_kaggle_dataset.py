# -*- coding: utf-8 -*-
"""
Kaggle数据集下载和YOLO标注生成脚本

下载小麦病害数据集并转换为YOLO格式
"""
import os
import sys
import shutil
import random
import zipfile
import subprocess
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


def download_dataset_kaggle_api():
    """使用Kaggle API下载数据集"""
    print("=" * 60)
    print("使用Kaggle API下载数据集")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = Path("temp_kaggle_download")
    temp_dir.mkdir(exist_ok=True)
    
    # 使用kaggle命令行下载
    try:
        # 检查kaggle是否安装
        result = subprocess.run(['kaggle', '--version'], capture_output=True, text=True)
        print(f"Kaggle CLI version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("请安装Kaggle CLI: pip install kaggle")
        print("并配置API密钥: https://www.kaggle.com/docs/api")
        return None
    
    # 下载数据集
    dataset_name = "kushagra3204/wheat-plant-diseases"
    output_path = temp_dir / "wheat_diseases"
    
    print(f"\n下载 {dataset_name}...")
    result = subprocess.run(
        ['kaggle', 'datasets', 'download', '-d', dataset_name, '-p', str(output_path), '--unzip'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"下载失败: {result.stderr}")
        return None
    
    print(f"下载完成: {output_path}")
    return output_path


def download_dataset_kagglehub():
    """使用kagglehub下载数据集"""
    try:
        import kagglehub
    except ImportError:
        print("请安装kagglehub: pip install kagglehub")
        return None
    
    print("=" * 60)
    print("使用kagglehub下载数据集")
    print("=" * 60)
    
    try:
        path = kagglehub.dataset_download("kushagra3204/wheat-plant-diseases")
        print(f"数据集下载到: {path}")
        return Path(path)
    except Exception as e:
        print(f"下载失败: {e}")
        return None


def analyze_dataset(dataset_path: Path):
    """分析数据集结构"""
    print("\n分析数据集结构...")
    
    # 查找所有图像文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    images = []
    for ext in image_extensions:
        images.extend(dataset_path.rglob(f'*{ext}'))
        images.extend(dataset_path.rglob(f'*{ext.upper()}'))
    
    print(f"找到 {len(images)} 张图像")
    
    if len(images) == 0:
        print("警告: 未找到图像文件!")
        return {}
    
    # 按目录分类
    categories = {}
    for img in images:
        # 获取父目录名作为类别
        parent = img.parent.name
        if parent not in categories:
            categories[parent] = []
        categories[parent].append(img)
    
    print(f"\n发现 {len(categories)} 个类别:")
    for cat, imgs in sorted(categories.items()):
        print(f"  {cat}: {len(imgs)} 张图像")
    
    return categories


def create_yolo_labels(
    categories: Dict[str, List[Path]],
    output_path: Path,
    class_mapping: Dict[str, int],
    train_ratio: float = 0.8
):
    """
    创建YOLO格式标注文件
    
    对于分类数据集，生成全图标注（边界框覆盖整个图像）
    """
    print("\n生成YOLO标注文件...")
    
    # 创建目录结构
    train_images = output_path / "images" / "train"
    train_labels = output_path / "labels" / "train"
    val_images = output_path / "images" / "val"
    val_labels = output_path / "labels" / "val"
    
    for d in [train_images, train_labels, val_images, val_labels]:
        d.mkdir(parents=True, exist_ok=True)
    
    total_train = 0
    total_val = 0
    
    for class_name, images in categories.items():
        if class_name not in class_mapping:
            print(f"  跳过未知类别: {class_name}")
            continue
        
        class_id = class_mapping[class_name]
        
        # 随机划分训练集和验证集
        random.shuffle(images)
        split_idx = int(len(images) * train_ratio)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]
        
        # 处理训练集
        for img_path in train_imgs:
            # 复制图像
            dst_img = train_images / f"{class_name}_{img_path.stem}.jpg"
            shutil.copy(img_path, dst_img)
            
            # 创建标注文件（全图标注）
            label_path = train_labels / f"{class_name}_{img_path.stem}.txt"
            # YOLO格式: class_id x_center y_center width height (归一化)
            # 全图标注: 0.5 0.5 1.0 1.0
            with open(label_path, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            total_train += 1
        
        # 处理验证集
        for img_path in val_imgs:
            dst_img = val_images / f"{class_name}_{img_path.stem}.jpg"
            shutil.copy(img_path, dst_img)
            
            label_path = val_labels / f"{class_name}_{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            total_val += 1
        
        print(f"  {class_name}: 训练 {len(train_imgs)}, 验证 {len(val_imgs)}")
    
    print(f"\n总计: 训练 {total_train}, 验证 {total_val}")
    return total_train, total_val


def create_dataset_yaml(output_path: Path, class_mapping: Dict[str, int]):
    """创建数据集配置文件"""
    yaml_content = f"""# Wheat Disease Dataset Configuration
# Auto-generated from Kaggle dataset

path: {output_path.absolute()}
train: images/train
val: images/val

nc: {len(class_mapping)}

names:
"""
    for class_name, class_id in sorted(class_mapping.items(), key=lambda x: x[1]):
        yaml_content += f"  {class_id}: {class_name}\n"
    
    yaml_path = output_path / "dataset.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"\n配置文件已创建: {yaml_path}")
    return yaml_path


def main():
    """主函数"""
    # 定义类别映射（根据数据集调整）
    class_mapping = {
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
        # 可能的其他类别名称
        'aphid': 0,
        'black_rust': 1,
        'blast': 2,
        'brown_rust': 3,
        'common_root_rot': 4,
        'fusarium': 5,
        'healthy': 6,
        'leaf_blight': 7,
        'mildew': 8,
        'mite': 9,
        'septoria': 10,
        'smut': 11,
        'stem_fly': 12,
        'tan_spot': 13,
        'yellow_rust': 14,
        'stripe_rust': 14,
        'leaf_rust': 3,
        'stem_rust': 1,
        'powdery_mildew': 8,
    }
    
    # 尝试使用Kaggle API下载
    dataset_path = download_dataset_kaggle_api()
    
    # 如果失败，尝试kagglehub
    if dataset_path is None or not list(dataset_path.rglob('*.jpg')):
        print("\n尝试使用kagglehub...")
        dataset_path = download_dataset_kagglehub()
    
    if dataset_path is None:
        print("\n下载失败，请检查网络连接或手动下载数据集")
        return
    
    # 分析数据集
    categories = analyze_dataset(dataset_path)
    
    if not categories:
        print("未找到有效数据，退出")
        return
    
    # 输出路径
    output_path = Path("datasets/wheat_data_new")
    
    # 创建YOLO标注
    create_yolo_labels(categories, output_path, class_mapping)
    
    # 创建配置文件
    create_dataset_yaml(output_path, class_mapping)
    
    print("\n" + "=" * 60)
    print("数据集准备完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
