# -*- coding: utf-8 -*-
"""
修复 HuggingFace 缓存符号链接问题 (Windows)

Windows 环境下 HuggingFace 缓存机制尝试创建符号链接时会导致错误：
[WinError 14007] 在活动的激活上下文中找不到任何查找密钥

解决方案：
1. 设置环境变量禁用符号链接警告
2. 使用文件复制替代符号链接
3. 配置自定义缓存路径

HuggingFace 缓存结构：
~/.cache/huggingface/hub/
├── models--org--model_name/
│   ├── blobs/           # 实际文件存储
│   ├── refs/            # 引用指针
│   │   └── main         # 当前版本的 commit hash
│   └── snapshots/       # 符号链接或复制的文件
│       └── <commit_hash>/
"""
import os
import sys
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, List, Any
import hashlib


def is_windows() -> bool:
    """
    检测是否为 Windows 系统
    
    :return: 是否为 Windows 系统
    """
    return platform.system() == "Windows"


def check_symlink_capability() -> Dict[str, Any]:
    """
    检测系统符号链接能力
    
    :return: 检测结果字典
    """
    result = {
        "is_windows": is_windows(),
        "can_create_symlink": False,
        "is_admin": False,
        "developer_mode": False,
        "recommendation": ""
    }
    
    if not result["is_windows"]:
        result["can_create_symlink"] = True
        result["recommendation"] = "非 Windows 系统，符号链接功能正常"
        return result
    
    try:
        import ctypes
        result["is_admin"] = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        pass
    
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock",
            0,
            winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AllowDevelopmentWithoutDevLicense")
            result["developer_mode"] = value == 1
    except Exception:
        pass
    
    if result["is_admin"] or result["developer_mode"]:
        result["can_create_symlink"] = True
        result["recommendation"] = "系统支持创建符号链接"
    else:
        result["recommendation"] = "建议启用开发者模式或以管理员身份运行"
    
    return result


def setup_windows_hf_environment(cache_dir: Optional[str] = None) -> Dict[str, str]:
    """
    配置 Windows 环境下的 HuggingFace 环境变量
    
    :param cache_dir: 自定义缓存目录
    :return: 设置的环境变量字典
    """
    env_vars = {}
    
    env_vars['HF_ENDPOINT'] = 'https://hf-mirror.com'
    env_vars['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    env_vars['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    env_vars['TOKENIZERS_PARALLELISM'] = 'false'
    
    if cache_dir:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        env_vars['HF_HOME'] = str(cache_path)
        env_vars['HF_HUB_CACHE'] = str(cache_path / "hub")
        env_vars['TRANSFORMERS_CACHE'] = str(cache_path)
        env_vars['HUGGINGFACE_HUB_CACHE'] = str(cache_path / "hub")
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   设置环境变量: {key}={value}")
    
    return env_vars


def get_hf_cache_dir() -> Path:
    """
    获取 HuggingFace 缓存目录
    
    :return: 缓存目录路径
    """
    cache_dir = os.environ.get('HF_HOME') or os.environ.get('HF_HUB_CACHE')
    if cache_dir:
        return Path(cache_dir)
    
    return Path.home() / ".cache" / "huggingface" / "hub"


def get_blob_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    计算文件的 SHA256 哈希值（HuggingFace 格式）
    
    :param file_path: 文件路径
    :param chunk_size: 读取块大小
    :return: 哈希值字符串
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def fix_model_cache(model_dir: Path, force_copy: bool = False) -> Dict[str, Any]:
    """
    修复单个模型的缓存问题
    
    :param model_dir: 模型缓存目录
    :param force_copy: 是否强制复制
    :return: 修复结果
    """
    result = {
        "model_name": model_dir.name,
        "fixed": False,
        "copied_files": 0,
        "skipped_files": 0,
        "errors": []
    }
    
    if not model_dir.is_dir() or not model_dir.name.startswith("models--"):
        result["errors"].append("不是有效的模型缓存目录")
        return result
    
    blobs_dir = model_dir / "blobs"
    snapshots_dir = model_dir / "snapshots"
    refs_dir = model_dir / "refs"
    
    if not blobs_dir.exists():
        result["errors"].append("blobs 目录不存在")
        return result
    
    commit_hash = None
    if refs_dir.exists():
        main_ref = refs_dir / "main"
        if main_ref.exists():
            commit_hash = main_ref.read_text().strip()
    
    if not commit_hash and snapshots_dir.exists():
        for snap in snapshots_dir.iterdir():
            if snap.is_dir() and len(snap.name) == 40:
                commit_hash = snap.name
                break
    
    if not commit_hash:
        result["errors"].append("无法找到 commit hash")
        return result
    
    target_snapshot_dir = snapshots_dir / commit_hash
    target_snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    for blob_file in blobs_dir.iterdir():
        if not blob_file.is_file():
            continue
        
        target_file = target_snapshot_dir / blob_file.name
        
        try:
            if target_file.exists() or target_file.is_symlink():
                if force_copy:
                    if target_file.is_symlink():
                        target_file.unlink()
                    else:
                        continue
                else:
                    result["skipped_files"] += 1
                    continue
            
            shutil.copy2(blob_file, target_file)
            result["copied_files"] += 1
            
        except Exception as e:
            result["errors"].append(f"复制 {blob_file.name[:20]}... 失败: {e}")
    
    result["fixed"] = result["copied_files"] > 0 or result["skipped_files"] > 0
    return result


def fix_hf_cache_symlinks(
    cache_dir: str = None,
    force_copy: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    修复 HuggingFace 缓存符号链接问题
    
    :param cache_dir: 缓存目录路径
    :param force_copy: 是否强制复制（覆盖现有文件）
    :param verbose: 是否输出详细信息
    :return: 修复结果汇总
    """
    if cache_dir is None:
        cache_dir = get_hf_cache_dir()
    else:
        cache_dir = Path(cache_dir)
    
    if verbose:
        print("=" * 60)
        print("🔧 修复 HuggingFace 缓存符号链接问题")
        print("=" * 60)
        print(f"📁 缓存目录: {cache_dir}")
    
    if not cache_dir.exists():
        if verbose:
            print("⚠️ 缓存目录不存在")
        return {"total_models": 0, "fixed_models": 0, "total_copied": 0}
    
    results = []
    total_copied = 0
    fixed_models = 0
    
    for model_dir in cache_dir.iterdir():
        if not model_dir.is_dir() or not model_dir.name.startswith("models--"):
            continue
        
        if verbose:
            print(f"\n📦 处理模型: {model_dir.name}")
        
        result = fix_model_cache(model_dir, force_copy=force_copy)
        results.append(result)
        
        if result["fixed"]:
            fixed_models += 1
            total_copied += result["copied_files"]
        
        if verbose:
            if result["copied_files"] > 0:
                print(f"   ✅ 复制了 {result['copied_files']} 个文件")
            if result["skipped_files"] > 0:
                print(f"   ⏭️ 跳过 {result['skipped_files']} 个已存在文件")
            if result["errors"]:
                for err in result["errors"]:
                    print(f"   ❌ {err}")
    
    summary = {
        "total_models": len(results),
        "fixed_models": fixed_models,
        "total_copied": total_copied,
        "results": results
    }
    
    if verbose:
        print("\n" + "=" * 60)
        print(f"✅ 修复完成")
        print(f"   处理模型: {summary['total_models']} 个")
        print(f"   修复模型: {summary['fixed_models']} 个")
        print(f"   复制文件: {summary['total_copied']} 个")
        print("=" * 60)
    
    return summary


def create_windows_compatible_loader():
    """
    创建 Windows 兼容的模型加载器装饰器
    
    使用示例:
        @create_windows_compatible_loader()
        def load_model(model_name, **kwargs):
            return AutoModel.from_pretrained(model_name, **kwargs)
    """
    def decorator(load_func):
        def wrapper(*args, **kwargs):
            if is_windows():
                setup_windows_hf_environment()
            return load_func(*args, **kwargs)
        return wrapper
    return decorator


def diagnose_hf_cache(cache_dir: str = None) -> Dict[str, Any]:
    """
    诊断 HuggingFace 缓存状态
    
    :param cache_dir: 缓存目录路径
    :return: 诊断结果
    """
    if cache_dir is None:
        cache_dir = get_hf_cache_dir()
    else:
        cache_dir = Path(cache_dir)
    
    diagnosis = {
        "cache_dir": str(cache_dir),
        "exists": cache_dir.exists(),
        "is_windows": is_windows(),
        "symlink_capability": check_symlink_capability(),
        "models": [],
        "total_size_mb": 0,
        "issues": []
    }
    
    if not cache_dir.exists():
        diagnosis["issues"].append("缓存目录不存在")
        return diagnosis
    
    for model_dir in cache_dir.iterdir():
        if not model_dir.is_dir() or not model_dir.name.startswith("models--"):
            continue
        
        model_info = {
            "name": model_dir.name,
            "path": str(model_dir),
            "size_mb": 0,
            "has_blobs": (model_dir / "blobs").exists(),
            "has_snapshots": (model_dir / "snapshots").exists(),
            "has_refs": (model_dir / "refs").exists(),
            "broken_symlinks": 0
        }
        
        total_size = 0
        for root, dirs, files in os.walk(model_dir):
            for f in files:
                file_path = Path(root) / f
                try:
                    if file_path.is_symlink():
                        if not file_path.exists():
                            model_info["broken_symlinks"] += 1
                    else:
                        total_size += file_path.stat().st_size
                except Exception:
                    pass
        
        model_info["size_mb"] = total_size / (1024 * 1024)
        diagnosis["models"].append(model_info)
        diagnosis["total_size_mb"] += model_info["size_mb"]
        
        if model_info["broken_symlinks"] > 0:
            diagnosis["issues"].append(
                f"{model_dir.name}: 发现 {model_info['broken_symlinks']} 个损坏的符号链接"
            )
    
    return diagnosis


def print_diagnosis(diagnosis: Dict[str, Any]):
    """
    打印诊断结果
    
    :param diagnosis: 诊断结果字典
    """
    print("\n" + "=" * 60)
    print("🔍 HuggingFace 缓存诊断报告")
    print("=" * 60)
    
    print(f"\n📁 缓存目录: {diagnosis['cache_dir']}")
    print(f"   存在: {'是' if diagnosis['exists'] else '否'}")
    print(f"   系统: {'Windows' if diagnosis['is_windows'] else '非 Windows'}")
    
    cap = diagnosis["symlink_capability"]
    print(f"\n🔗 符号链接能力:")
    print(f"   支持符号链接: {'是' if cap['can_create_symlink'] else '否'}")
    if diagnosis['is_windows']:
        print(f"   管理员权限: {'是' if cap['is_admin'] else '否'}")
        print(f"   开发者模式: {'是' if cap['developer_mode'] else '否'}")
    print(f"   建议: {cap['recommendation']}")
    
    print(f"\n📦 已缓存模型: {len(diagnosis['models'])} 个")
    print(f"   总大小: {diagnosis['total_size_mb']:.1f} MB")
    
    for model in diagnosis["models"]:
        print(f"\n   模型: {model['name']}")
        print(f"      大小: {model['size_mb']:.1f} MB")
        print(f"      blobs: {'✅' if model['has_blobs'] else '❌'}")
        print(f"      snapshots: {'✅' if model['has_snapshots'] else '❌'}")
        print(f"      refs: {'✅' if model['has_refs'] else '❌'}")
        if model['broken_symlinks'] > 0:
            print(f"      ⚠️ 损坏的符号链接: {model['broken_symlinks']}")
    
    if diagnosis["issues"]:
        print(f"\n⚠️ 发现的问题:")
        for issue in diagnosis["issues"]:
            print(f"   - {issue}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="修复 HuggingFace 缓存符号链接问题 (Windows)"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="自定义缓存目录路径"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制复制，覆盖已存在的文件"
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="仅诊断，不修复"
    )
    parser.add_argument(
        "--setup-env",
        action="store_true",
        help="仅设置环境变量"
    )
    
    args = parser.parse_args()
    
    print("\n🖥️ 系统信息:")
    print(f"   操作系统: {platform.system()} {platform.release()}")
    print(f"   Python: {platform.python_version()}")
    
    if args.setup_env:
        print("\n⚙️ 配置 HuggingFace 环境变量...")
        setup_windows_hf_environment(args.cache_dir)
        print("\n✅ 环境变量配置完成")
        return
    
    if args.diagnose:
        diagnosis = diagnose_hf_cache(args.cache_dir)
        print_diagnosis(diagnosis)
        return
    
    symlink_info = check_symlink_capability()
    print(f"\n🔗 符号链接状态:")
    print(f"   支持创建: {'是' if symlink_info['can_create_symlink'] else '否'}")
    print(f"   {symlink_info['recommendation']}")
    
    setup_windows_hf_environment(args.cache_dir)
    
    fix_hf_cache_symlinks(
        cache_dir=args.cache_dir,
        force_copy=args.force,
        verbose=True
    )


if __name__ == "__main__":
    main()
