# -*- coding: utf-8 -*-
"""
数据预处理脚本

验证数据集完整性，生成统计报告
"""
import os
import json
from pathlib import Path
from collections import Counter

def main():
    print("=" * 60)
    print("数据预处理：验证数据集完整性")
    print("=" * 60)
    
    dataset_path = Path("datasets/wheat_data_unified")
    
    # 检查目录是否存在
    if not dataset_path.exists():
        print(f"错误: 数据集目录不存在: {dataset_path}")
        return
    
    # 统计图像文件
    train_images = []
    val_images = []
    
    train_img_dir = dataset_path / "images" / "train"
    val_img_dir = dataset_path / "images" / "val"
    
    if train_img_dir.exists():
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            train_images.extend(train_img_dir.glob(f"*{ext}"))
    
    if val_img_dir.exists():
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            val_images.extend(val_img_dir.glob(f"*{ext}"))
    
    # 统计标签文件
    train_labels = []
    val_labels = []
    
    train_lbl_dir = dataset_path / "labels" / "train"
    val_lbl_dir = dataset_path / "labels" / "val"
    
    if train_lbl_dir.exists():
        train_labels.extend(train_lbl_dir.glob("*.txt"))
    
    if val_lbl_dir.exists():
        val_labels.extend(val_lbl_dir.glob("*.txt"))
    
    print(f"\n数据集统计:")
    print(f"  训练图像: {len(train_images)}")
    print(f"  训练标签: {len(train_labels)}")
    print(f"  验证图像: {len(val_images)}")
    print(f"  验证标签: {len(val_labels)}")
    
    # 检查图像-标签匹配
    train_img_stems = {f.stem for f in train_images}
    train_lbl_stems = {f.stem for f in train_labels}
    val_img_stems = {f.stem for f in val_images}
    val_lbl_stems = {f.stem for f in val_labels}
    
    train_match = train_img_stems == train_lbl_stems
    val_match = val_img_stems == val_lbl_stems
    
    print(f"\n图像-标签匹配:")
    print(f"  训练集: {'匹配' if train_match else '不匹配'}")
    print(f"  验证集: {'匹配' if val_match else '不匹配'}")
    
    # 统计类别分布
    categories = Counter()
    for img in train_images + val_images:
        cat = img.stem.split("_")[0]
        categories[cat] += 1
    
    print(f"\n类别分布 ({len(categories)}类):")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    # 保存统计报告
    report = {
        "train_images": len(train_images),
        "train_labels": len(train_labels),
        "val_images": len(val_images),
        "val_labels": len(val_labels),
        "categories": dict(categories),
        "train_match": train_match,
        "val_match": val_match,
        "total_images": len(train_images) + len(val_images)
    }
    
    os.makedirs("logs", exist_ok=True)
    with open("logs/dataset_stats.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n统计报告已保存: logs/dataset_stats.json")
    print("=" * 60)
    
    return train_match and val_match


if __name__ == "__main__":
    main()
