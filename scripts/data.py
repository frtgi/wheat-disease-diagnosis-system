# -*- coding: utf-8 -*-
"""
WheatAgent 数据集下载和准备脚本

从Kaggle下载小麦病害数据集并转换为YOLO格式
"""
import os
import sys
import shutil
import random
import subprocess
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


def download_with_kagglehub() -> Optional[Path]:
    """使用kagglehub下载数据集"""
    try:
        import kagglehub
        print("=" * 60)
        print("使用kagglehub下载数据集...")
        print("=" * 60)
        
        path = kagglehub.dataset_download("kushagra3204/wheat-plant-diseases")
        print(f"数据集下载到: {path}")
        return Path(path)
    except ImportError:
        print("kagglehub未安装，尝试其他方式...")
        return None
    except Exception as e:
        print(f"kagglehub下载失败: {e}")
        return None


def download_with_kaggle_cli() -> Optional[Path]:
    """使用Kaggle CLI下载数据集"""
    print("=" * 60)
    print("使用Kaggle CLI下载数据集...")
    print("=" * 60)
    
    temp_dir = PROJECT_ROOT / "temp_kaggle_download"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        result = subprocess.run(
            ['kaggle', '--version'], 
            capture_output=True, 
            text=True
        )
        print(f"Kaggle CLI: {result.stdout.strip()}")
    except FileNotFoundError:
        print("Kaggle CLI未安装")
        print("安装方法: pip install kaggle")
        print("配置方法: https://www.kaggle.com/docs/api")
        return None
    
    dataset_name = "kushagra3204/wheat-plant-diseases"
    output_path = temp_dir / "wheat_diseases"
    
    print(f"\n下载 {dataset_name}...")
    result = subprocess.run(
        ['kaggle', 'datasets', 'download', '-d', dataset_name, 
         '-p', str(output_path), '--unzip'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"下载失败: {result.stderr}")
        return None
    
    print(f"下载完成: {output_path}")
    return output_path


def analyze_dataset(dataset_path: Path) -> Dict[str, List[Path]]:
    """分析数据集结构"""
    print("\n分析数据集结构...")
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.JPG', '.JPEG', '.PNG'}
    images = []
    for ext in image_extensions:
        images.extend(dataset_path.rglob(f'*{ext}'))
    
    print(f"找到 {len(images)} 张图像")
    
    if len(images) == 0:
        print("警告: 未找到图像文件!")
        return {}
    
    categories = {}
    for img in images:
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
    """创建YOLO格式标注文件"""
    print("\n生成YOLO标注文件...")
    
    train_images = output_path / "images" / "train"
    train_labels = output_path / "labels" / "train"
    val_images = output_path / "images" / "val"
    val_labels = output_path / "labels" / "val"
    
    for d in [train_images, train_labels, val_images, val_labels]:
        d.mkdir(parents=True, exist_ok=True)
    
    total_train = 0
    total_val = 0
    unknown_categories = set()
    
    for class_name, images in categories.items():
        if class_name not in class_mapping:
            unknown_categories.add(class_name)
            continue
        
        class_id = class_mapping[class_name]
        random.shuffle(images)
        split_idx = int(len(images) * train_ratio)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]
        
        for img_path in train_imgs:
            dst_img = train_images / f"{class_name}_{img_path.stem}.jpg"
            shutil.copy(img_path, dst_img)
            
            label_path = train_labels / f"{class_name}_{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            total_train += 1
        
        for img_path in val_imgs:
            dst_img = val_images / f"{class_name}_{img_path.stem}.jpg"
            shutil.copy(img_path, dst_img)
            
            label_path = val_labels / f"{class_name}_{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            total_val += 1
        
        print(f"  {class_name}: 训练 {len(train_imgs)}, 验证 {len(val_imgs)}")
    
    if unknown_categories:
        print(f"\n跳过的未知类别: {unknown_categories}")
    
    print(f"\n总计: 训练 {total_train}, 验证 {total_val}")
    return total_train, total_val


def create_dataset_yaml(output_path: Path, class_mapping: Dict[str, int]):
    """创建数据集配置文件"""
    sorted_classes = sorted(class_mapping.items(), key=lambda x: x[1])
    unique_classes = {}
    for name, idx in sorted_classes:
        if idx not in unique_classes.values():
            unique_classes[name] = idx
    
    yaml_content = f"""# Wheat Disease Dataset Configuration
# Auto-generated from Kaggle dataset

path: {output_path.absolute()}
train: images/train
val: images/val

nc: {len(unique_classes)}

names:
"""
    for class_name, class_id in sorted(unique_classes.items(), key=lambda x: x[1]):
        yaml_content += f"  {class_id}: {class_name}\n"
    
    yaml_path = output_path / "dataset.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"\n配置文件已创建: {yaml_path}")
    return yaml_path


def update_project_config(dataset_path: Path, class_mapping: Dict[str, int]):
    """更新项目配置文件"""
    config_path = PROJECT_ROOT / "configs" / "wheat_disease.yaml"
    
    sorted_classes = sorted(class_mapping.items(), key=lambda x: x[1])
    unique_classes = {}
    seen_ids = set()
    for name, idx in sorted_classes:
        if idx not in seen_ids:
            unique_classes[name] = idx
            seen_ids.add(idx)
    
    yaml_content = f"""# ============================================================
# WheatAgent 统一数据集配置文件
# 基于多模态特征融合的小麦病害诊断智能体
# ============================================================

# 数据集路径
path: {dataset_path.absolute()}
train: images/train
val: images/val
test: images/val

# 类别数量
nc: {len(unique_classes)}

# 类别名称
names:
"""
    for class_name, class_id in sorted(unique_classes.items(), key=lambda x: x[1]):
        yaml_content += f"  {class_id}: {class_name}\n"
    
    yaml_content += """
# 训练参数
box: 0.05
cls: 0.5
fliplr: 0.5
"""
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"项目配置已更新: {config_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("WheatAgent 数据集准备工具")
    print("=" * 60)
    
    # 类别映射
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
        # 别名映射
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
    
    # 尝试下载
    dataset_path = download_with_kagglehub()
    
    if dataset_path is None:
        dataset_path = download_with_kaggle_cli()
    
    if dataset_path is None:
        print("\n" + "=" * 60)
        print("自动下载失败，请手动下载数据集:")
        print("https://www.kaggle.com/datasets/kushagra3204/wheat-plant-diseases")
        print("=" * 60)
        return
    
    # 分析数据集
    categories = analyze_dataset(dataset_path)
    
    if not categories:
        print("未找到有效数据!")
        return
    
    # 输出路径
    output_path = PROJECT_ROOT / "datasets" / "wheat_data_new"
    
    # 创建YOLO标注
    create_yolo_labels(categories, output_path, class_mapping)
    
    # 创建配置文件
    create_dataset_yaml(output_path, class_mapping)
    
    # 更新项目配置
    update_project_config(output_path, class_mapping)
    
    print("\n" + "=" * 60)
    print("数据集准备完成!")
    print(f"数据集路径: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
