# -*- coding: utf-8 -*-
"""
数据集分析脚本
分析小麦病害数据集的类别分布、图像数量、标注质量等
"""
import os
import glob
import json
from collections import defaultdict, Counter
from pathlib import Path
import shutil


def analyze_dataset():
    """分析数据集现状"""
    print("=" * 70)
    print("📊 小麦病害数据集分析报告")
    print("=" * 70)
    
    dataset_root = os.path.join(os.getcwd(), "datasets", "wheat_data")
    images_dir = os.path.join(dataset_root, "images", "train")
    labels_dir = os.path.join(dataset_root, "labels", "train")
    
    # 1. 统计图像数量
    print("\n[1/5] 统计图像数量...")
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_files.extend(glob.glob(os.path.join(images_dir, ext)))
    
    print(f"   训练图像总数: {len(image_files)}")
    
    # 2. 分析类别分布
    print("\n[2/5] 分析类别分布...")
    class_counts = defaultdict(int)
    class_images = defaultdict(list)
    
    # 从文件名解析类别
    for img_path in image_files:
        filename = os.path.basename(img_path)
        # 文件名格式: ClassName_instance_id.png
        parts = filename.replace('.png', '').replace('.jpg', '').split('_')
        if len(parts) >= 2:
            class_name = parts[0]
            class_counts[class_name] += 1
            class_images[class_name].append(filename)
    
    print("\n   类别分布:")
    print("   " + "-" * 50)
    print(f"   {'类别':<20} {'数量':<10} {'占比':<10}")
    print("   " + "-" * 50)
    
    total = len(image_files)
    for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / total * 100
        print(f"   {class_name:<20} {count:<10} {percentage:>6.2f}%")
    
    print("   " + "-" * 50)
    print(f"   {'总计':<20} {total:<10} {'100.00%':>10}")
    
    # 3. 检查标注文件
    print("\n[3/5] 检查标注文件...")
    label_files = glob.glob(os.path.join(labels_dir, "*.txt"))
    print(f"   标注文件总数: {len(label_files)}")
    
    # 检查图像-标注对应关系
    images_with_labels = 0
    images_without_labels = 0
    
    for img_path in image_files:
        img_name = os.path.basename(img_path)
        base_name = img_name.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
        label_path = os.path.join(labels_dir, base_name + ".txt")
        
        if os.path.exists(label_path):
            images_with_labels += 1
        else:
            images_without_labels += 1
    
    print(f"   有标注的图像: {images_with_labels}")
    print(f"   无标注的图像: {images_without_labels}")
    
    # 4. 分析标注内容
    print("\n[4/5] 分析标注内容...")
    label_class_distribution = Counter()
    total_objects = 0
    
    for label_path in label_files:
        with open(label_path, 'r') as f:
            lines = f.readlines()
            total_objects += len(lines)
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    label_class_distribution[class_id] += 1
    
    print(f"   标注对象总数: {total_objects}")
    print(f"   平均每图对象数: {total_objects / len(label_files):.2f}")
    print("\n   标注类别分布:")
    for class_id, count in sorted(label_class_distribution.items()):
        print(f"     类别 {class_id}: {count} 个对象")
    
    # 5. 检查验证集
    print("\n[5/5] 检查验证集...")
    val_images_dir = os.path.join(dataset_root, "images", "val")
    val_labels_dir = os.path.join(dataset_root, "labels", "val")
    
    if os.path.exists(val_images_dir):
        val_images = glob.glob(os.path.join(val_images_dir, "*.png")) + \
                    glob.glob(os.path.join(val_images_dir, "*.jpg"))
        print(f"   验证集图像: {len(val_images)}")
    else:
        print("   ⚠️ 验证集不存在，需要从训练集划分")
    
    # 生成分析报告
    print("\n" + "=" * 70)
    print("📋 数据集问题总结")
    print("=" * 70)
    
    issues = []
    
    # 检查类别不平衡
    max_count = max(class_counts.values())
    min_count = min(class_counts.values())
    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
    
    if imbalance_ratio > 5:
        issues.append(f"⚠️ 类别严重不平衡: 最大/最小 = {imbalance_ratio:.1f}")
    
    if len(image_files) < 1000:
        issues.append(f"⚠️ 数据量不足: 仅 {len(image_files)} 张图像，建议至少1000张")
    
    if not os.path.exists(val_images_dir):
        issues.append("⚠️ 缺少验证集")
    
    if images_without_labels > 0:
        issues.append(f"⚠️ 有 {images_without_labels} 张图像缺少标注")
    
    if issues:
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ 数据集状态良好")
    
    # 保存分析报告
    report = {
        "total_images": len(image_files),
        "total_labels": len(label_files),
        "class_distribution": dict(class_counts),
        "issues": issues,
        "recommendations": [
            "收集更多数据，特别是数量较少的类别",
            "划分训练集和验证集（建议80/20比例）",
            "使用数据增强扩充数据集",
            "考虑使用生成式模型合成稀缺类别图像"
        ]
    }
    
    report_path = os.path.join(os.getcwd(), "dataset_analysis_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存: {report_path}")
    print("=" * 70)
    
    return class_counts, class_images


def split_train_val(class_images, val_ratio=0.2):
    """
    划分训练集和验证集
    
    Args:
        class_images: 类别到图像列表的映射
        val_ratio: 验证集比例
    """
    print("\n" + "=" * 70)
    print("🔄 划分训练集和验证集")
    print("=" * 70)
    
    dataset_root = os.path.join(os.getcwd(), "datasets", "wheat_data")
    train_images_dir = os.path.join(dataset_root, "images", "train")
    train_labels_dir = os.path.join(dataset_root, "labels", "train")
    val_images_dir = os.path.join(dataset_root, "images", "val")
    val_labels_dir = os.path.join(dataset_root, "labels", "val")
    
    # 创建验证集目录
    os.makedirs(val_images_dir, exist_ok=True)
    os.makedirs(val_labels_dir, exist_ok=True)
    
    import random
    random.seed(42)  # 保证可重复
    
    total_moved = 0
    
    for class_name, images in class_images.items():
        n_val = max(1, int(len(images) * val_ratio))  # 每类至少保留1张验证
        
        # 随机选择验证集
        val_images = random.sample(images, n_val)
        
        for img_name in val_images:
            # 移动图像
            src_img = os.path.join(train_images_dir, img_name)
            dst_img = os.path.join(val_images_dir, img_name)
            
            if os.path.exists(src_img):
                shutil.move(src_img, dst_img)
                
                # 移动对应的标注文件
                base_name = img_name.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
                src_label = os.path.join(train_labels_dir, base_name + ".txt")
                dst_label = os.path.join(val_labels_dir, base_name + ".txt")
                
                if os.path.exists(src_label):
                    shutil.move(src_label, dst_label)
                
                total_moved += 1
    
    print(f"✅ 已划分 {total_moved} 张图像到验证集")
    
    # 统计划分后的分布
    train_images = glob.glob(os.path.join(train_images_dir, "*.png")) + \
                   glob.glob(os.path.join(train_images_dir, "*.jpg"))
    val_images = glob.glob(os.path.join(val_images_dir, "*.png")) + \
                 glob.glob(os.path.join(val_images_dir, "*.jpg"))
    
    print(f"   训练集: {len(train_images)} 张")
    print(f"   验证集: {len(val_images)} 张")
    print("=" * 70)


if __name__ == "__main__":
    # 分析数据集
    class_counts, class_images = analyze_dataset()
    
    # 询问是否划分验证集
    val_images_dir = os.path.join(os.getcwd(), "datasets", "wheat_data", "images", "val")
    if not os.path.exists(val_images_dir) or len(os.listdir(val_images_dir)) == 0:
        response = input("\n是否现在划分训练集和验证集? (y/n): ")
        if response.lower() == 'y':
            split_train_val(class_images, val_ratio=0.2)
