# -*- coding: utf-8 -*-
"""
项目清理脚本

清理冗余文件和目录：
1. runs/detect下的重复训练/预测目录
2. datasets下的.npy缓存文件
3. __pycache__目录
"""
import os
import shutil
from pathlib import Path
from datetime import datetime


def get_dir_size(path: str) -> int:
    """计算目录大小"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def cleanup_redundant_runs(base_path: str = "runs/detect"):
    """
    清理runs/detect下的冗余目录
    
    保留：
    - high_perf (最新高性能训练)
    - serpensgate (SerpensGate模型)
    - runs (嵌套训练结果)
    
    删除：
    - predict* (重复预测)
    - train* (重复训练，保留最新)
    - val* (重复验证)
    - fast (旧训练)
    """
    runs_path = Path(base_path)
    if not runs_path.exists():
        print(f"目录不存在: {runs_path}")
        return 0
    
    # 要保留的目录
    keep_dirs = {'high_perf', 'serpensgate', 'runs'}
    
    # 要删除的目录模式
    delete_patterns = ['predict', 'train', 'val', 'fast']
    
    deleted_size = 0
    deleted_count = 0
    
    for item in runs_path.iterdir():
        if item.is_dir() and item.name not in keep_dirs:
            # 检查是否匹配删除模式
            should_delete = any(item.name.startswith(p) for p in delete_patterns)
            
            if should_delete:
                size = get_dir_size(str(item))
                print(f"  删除: {item.name} ({format_size(size)})")
                
                try:
                    shutil.rmtree(str(item))
                    deleted_size += size
                    deleted_count += 1
                except Exception as e:
                    print(f"    删除失败: {e}")
    
    print(f"\n清理runs/detect完成:")
    print(f"  删除目录: {deleted_count}个")
    print(f"  释放空间: {format_size(deleted_size)}")
    
    return deleted_size


def cleanup_npy_cache(dataset_path: str = "datasets/wheat_data"):
    """
    清理.npy缓存文件
    """
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        print(f"目录不存在: {dataset_path}")
        return 0
    
    deleted_size = 0
    deleted_count = 0
    
    for npy_file in dataset_path.rglob("*.npy"):
        size = npy_file.stat().st_size
        print(f"  删除: {npy_file.relative_to(dataset_path)} ({format_size(size)})")
        
        try:
            npy_file.unlink()
            deleted_size += size
            deleted_count += 1
        except Exception as e:
            print(f"    删除失败: {e}")
    
    print(f"\n清理.npy缓存完成:")
    print(f"  删除文件: {deleted_count}个")
    print(f"  释放空间: {format_size(deleted_size)}")
    
    return deleted_size


def cleanup_pycache(src_path: str = "src"):
    """
    清理__pycache__目录
    """
    src_path = Path(src_path)
    if not src_path.exists():
        print(f"目录不存在: {src_path}")
        return 0
    
    deleted_size = 0
    deleted_count = 0
    
    for pycache in src_path.rglob("__pycache__"):
        if pycache.is_dir():
            size = get_dir_size(str(pycache))
            print(f"  删除: {pycache.relative_to(src_path)} ({format_size(size)})")
            
            try:
                shutil.rmtree(str(pycache))
                deleted_size += size
                deleted_count += 1
            except Exception as e:
                print(f"    删除失败: {e}")
    
    print(f"\n清理__pycache__完成:")
    print(f"  删除目录: {deleted_count}个")
    print(f"  释放空间: {format_size(deleted_size)}")
    
    return deleted_size


def cleanup_temp_uploads():
    """
    清理临时上传目录
    """
    temp_dirs = ['temp_uploads', 'uploads']
    
    deleted_size = 0
    
    for temp_dir in temp_dirs:
        temp_path = Path(temp_dir)
        if temp_path.exists():
            size = get_dir_size(str(temp_path))
            print(f"  清理: {temp_dir} ({format_size(size)})")
            
            try:
                shutil.rmtree(str(temp_path))
                deleted_size += size
            except Exception as e:
                print(f"    删除失败: {e}")
    
    return deleted_size


def main():
    """主函数"""
    print("=" * 60)
    print("🧹 WheatAgent 项目清理工具")
    print("=" * 60)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_freed = 0
    
    # 1. 清理runs/detect冗余目录
    print("\n📁 清理runs/detect冗余目录...")
    print("-" * 40)
    total_freed += cleanup_redundant_runs()
    
    # 2. 清理.npy缓存
    print("\n📁 清理.npy缓存文件...")
    print("-" * 40)
    total_freed += cleanup_npy_cache()
    
    # 3. 清理__pycache__
    print("\n📁 清理__pycache__目录...")
    print("-" * 40)
    total_freed += cleanup_pycache()
    
    # 4. 清理临时上传
    print("\n📁 清理临时上传目录...")
    print("-" * 40)
    total_freed += cleanup_temp_uploads()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 清理完成!")
    print("=" * 60)
    print(f"总共释放空间: {format_size(total_freed)}")
    print()


if __name__ == "__main__":
    main()
