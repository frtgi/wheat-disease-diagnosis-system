# -*- coding: utf-8 -*-
"""
清理数据集冗余文件
删除.npy文件，仅保留.png图像文件
"""
import os
import shutil
from pathlib import Path
from datetime import datetime


def cleanup_npy_files(dataset_path: str, dry_run: bool = True):
    """
    清理数据集中的.npy冗余文件
    
    Args:
        dataset_path: 数据集根目录
        dry_run: 是否仅模拟运行（不实际删除）
    """
    print("=" * 70)
    print("🗑️ 数据集冗余文件清理工具")
    print("=" * 70)
    
    images_dir = Path(dataset_path) / "images"
    
    if not images_dir.exists():
        print(f"❌ 图像目录不存在: {images_dir}")
        return
    
    # 统计信息
    npy_files = list(images_dir.rglob("*.npy"))
    png_files = list(images_dir.rglob("*.png"))
    
    total_npy = len(npy_files)
    total_png = len(png_files)
    
    # 计算占用空间
    npy_size = sum(f.stat().st_size for f in npy_files) / (1024 ** 3)
    png_size = sum(f.stat().st_size for f in png_files) / (1024 ** 3)
    
    print(f"\n📊 数据集统计:")
    print(f"   PNG文件: {total_png} 个 ({png_size:.2f} GB)")
    print(f"   NPY文件: {total_npy} 个 ({npy_size:.2f} GB)")
    print(f"   可释放空间: {npy_size:.2f} GB")
    
    if total_npy == 0:
        print("\n✅ 没有发现.npy文件，数据集已清理")
        return
    
    if dry_run:
        print("\n⚠️ 模拟运行模式，不会实际删除文件")
        print("   使用 --execute 参数执行实际删除")
        return
    
    # 执行删除
    print(f"\n🗑️ 开始删除 {total_npy} 个.npy文件...")
    
    deleted = 0
    errors = 0
    
    for npy_file in npy_files:
        try:
            os.remove(npy_file)
            deleted += 1
            if deleted % 500 == 0:
                print(f"   已删除: {deleted}/{total_npy}")
        except Exception as e:
            errors += 1
            print(f"   ❌ 删除失败: {npy_file.name} - {e}")
    
    print(f"\n✅ 清理完成!")
    print(f"   成功删除: {deleted} 个文件")
    print(f"   失败: {errors} 个文件")
    print(f"   释放空间: {npy_size:.2f} GB")


def cleanup_label_npy_files(dataset_path: str, dry_run: bool = True):
    """
    清理labels目录下的.npy文件
    """
    labels_dir = Path(dataset_path) / "labels"
    
    if not labels_dir.exists():
        return
    
    npy_files = list(labels_dir.rglob("*.npy"))
    
    if not npy_files:
        return
    
    npy_size = sum(f.stat().st_size for f in npy_files) / (1024 ** 2)
    
    print(f"\n📊 Labels目录NPY文件: {len(npy_files)} 个 ({npy_size:.2f} MB)")
    
    if dry_run:
        return
    
    for f in npy_files:
        try:
            os.remove(f)
        except:
            pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理数据集冗余文件")
    parser.add_argument("--execute", action="store_true", help="执行实际删除")
    parser.add_argument("--path", type=str, default="D:/Project/WheatAgent/datasets/wheat_data",
                       help="数据集路径")
    
    args = parser.parse_args()
    
    cleanup_npy_files(args.path, dry_run=not args.execute)
    cleanup_label_npy_files(args.path, dry_run=not args.execute)
