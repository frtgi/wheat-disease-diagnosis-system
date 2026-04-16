# -*- coding: utf-8 -*-
"""
模型预下载脚本

用于批量下载IWDDA系统所需的所有模型权重，支持离线部署

文档参考: 8.2 软件技术栈 - 云边协同

使用方法:
    python scripts/download_models.py --all
    python scripts/download_models.py --vision
    python scripts/download_models.py --llm
"""
import os
import sys
import argparse
import time
from typing import List, Dict, Optional
from pathlib import Path

# 配置环境
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'

import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

# 模型列表
REQUIRED_MODELS = {
    "vision": [
        {
            "name": "openai/clip-vit-large-patch14",
            "description": "CLIP视觉编码器",
            "size": "~1.7GB"
        },
        {
            "name": "openai/clip-vit-base-patch32",
            "description": "CLIP视觉编码器(轻量版)",
            "size": "~600MB"
        }
    ],
    "llm": [
        {
            "name": "lmsys/vicuna-7b-v1.5",
            "description": "Vicuna-7B语言模型",
            "size": "~13GB"
        },
        {
            "name": "meta-llama/Llama-2-7b-hf",
            "description": "LLaMA-2-7B基础模型",
            "size": "~13GB"
        }
    ],
    "tokenizer": [
        {
            "name": "openai/clip-vit-large-patch14",
            "description": "CLIP Tokenizer",
            "size": "包含在视觉模型中"
        }
    ]
}


def check_dependencies():
    """检查依赖是否安装"""
    missing = []
    
    try:
        import torch
    except ImportError:
        missing.append("torch")
    
    try:
        from transformers import AutoModel, AutoTokenizer
    except ImportError:
        missing.append("transformers")
    
    try:
        from huggingface_hub import snapshot_download, hf_hub_download
    except ImportError:
        missing.append("huggingface_hub")
    
    if missing:
        print("❌ 缺少以下依赖:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n请运行: pip install " + " ".join(missing))
        return False
    
    return True


def get_cache_dir() -> str:
    """获取缓存目录"""
    cache_dir = os.environ.get('HF_HOME', None)
    if cache_dir is None:
        cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
    return cache_dir


def check_model_cached(model_name: str) -> bool:
    """检查模型是否已缓存"""
    cache_dir = get_cache_dir()
    model_cache_path = os.path.join(cache_dir, 'hub', f'models--{model_name.replace("/", "--")}')
    return os.path.exists(model_cache_path)


def download_model(model_name: str, description: str = "") -> bool:
    """
    下载单个模型
    
    :param model_name: 模型名称
    :param description: 模型描述
    :return: 是否成功
    """
    print(f"\n{'='*60}")
    print(f"📥 下载模型: {model_name}")
    if description:
        print(f"   描述: {description}")
    print(f"{'='*60}")
    
    # 检查是否已缓存
    if check_model_cached(model_name):
        print(f"✅ 模型已存在于本地缓存，跳过下载")
        return True
    
    try:
        from huggingface_hub import snapshot_download
        
        start_time = time.time()
        
        # 下载模型
        local_path = snapshot_download(
            repo_id=model_name,
            resume_download=True,
            local_files_only=False
        )
        
        elapsed = time.time() - start_time
        print(f"✅ 下载完成! 耗时: {elapsed:.1f}秒")
        print(f"   本地路径: {local_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False


def download_model_components(model_name: str) -> bool:
    """
    下载模型组件（分词器、配置等）
    
    :param model_name: 模型名称
    :return: 是否成功
    """
    try:
        from transformers import AutoTokenizer, AutoConfig
        
        print(f"\n📦 下载模型组件: {model_name}")
        
        # 下载分词器
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"   ✅ 分词器下载完成")
        except Exception as e:
            print(f"   ⚠️ 分词器下载跳过: {e}")
        
        # 下载配置
        try:
            config = AutoConfig.from_pretrained(model_name)
            print(f"   ✅ 配置下载完成")
        except Exception as e:
            print(f"   ⚠️ 配置下载跳过: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件下载失败: {e}")
        return False


def download_all(progress_callback=None) -> Dict[str, bool]:
    """
    下载所有模型
    
    :param progress_callback: 进度回调函数
    :return: 下载结果字典
    """
    results = {}
    total = sum(len(models) for models in REQUIRED_MODELS.values())
    current = 0
    
    for category, models in REQUIRED_MODELS.items():
        print(f"\n{'#'*60}")
        print(f"# 下载 {category.upper()} 模型")
        print(f"{'#'*60}")
        
        for model_info in models:
            current += 1
            model_name = model_info["name"]
            description = model_info.get("description", "")
            
            if progress_callback:
                progress_callback(current, total, model_name)
            
            success = download_model(model_name, description)
            results[model_name] = success
            
            # 下载组件
            if success:
                download_model_components(model_name)
    
    return results


def generate_offline_package(output_dir: str):
    """
    生成离线包
    
    :param output_dir: 输出目录
    """
    import shutil
    
    cache_dir = get_cache_dir()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 生成离线包到: {output_path}")
    
    # 复制缓存目录
    hub_cache = Path(cache_dir) / "hub"
    if hub_cache.exists():
        dest = output_path / "hub"
        if not dest.exists():
            shutil.copytree(hub_cache, dest)
            print(f"   ✅ 已复制模型缓存")
        else:
            print(f"   ⚠️ 目标目录已存在，跳过复制")
    
    # 生成配置文件
    config = {
        "cache_dir": str(output_path),
        "models": {}
    }
    
    for category, models in REQUIRED_MODELS.items():
        for model_info in models:
            model_name = model_info["name"]
            model_path = output_path / "hub" / f"models--{model_name.replace('/', '--')}"
            config["models"][model_name] = {
                "cached": model_path.exists(),
                "path": str(model_path)
            }
    
    config_path = output_path / "offline_config.json"
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 配置文件已生成: {config_path}")


def print_summary(results: Dict[str, bool]):
    """打印下载摘要"""
    print(f"\n{'='*60}")
    print("📊 下载摘要")
    print(f"{'='*60}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for model_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {model_name}: {status}")
    
    print(f"{'='*60}")
    print(f"总计: {success_count}/{total_count} 成功")
    print(f"{'='*60}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="IWDDA模型预下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/download_models.py --all          # 下载所有模型
    python scripts/download_models.py --vision       # 仅下载视觉模型
    python scripts/download_models.py --llm          # 仅下载语言模型
    python scripts/download_models.py --check        # 检查模型状态
    python scripts/download_models.py --package ./offline_models  # 生成离线包
        """
    )
    
    parser.add_argument('--all', action='store_true', help='下载所有模型')
    parser.add_argument('--vision', action='store_true', help='下载视觉模型')
    parser.add_argument('--llm', action='store_true', help='下载语言模型')
    parser.add_argument('--tokenizer', action='store_true', help='下载分词器')
    parser.add_argument('--check', action='store_true', help='检查模型缓存状态')
    parser.add_argument('--package', type=str, help='生成离线包到指定目录')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🌾 IWDDA 模型预下载工具")
    print("="*60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查模型状态
    if args.check:
        print("\n📊 模型缓存状态:")
        for category, models in REQUIRED_MODELS.items():
            print(f"\n[{category.upper()}]")
            for model_info in models:
                model_name = model_info["name"]
                cached = check_model_cached(model_name)
                status = "✅ 已缓存" if cached else "❌ 未缓存"
                print(f"   {model_name}: {status}")
        return
    
    # 生成离线包
    if args.package:
        generate_offline_package(args.package)
        return
    
    # 下载模型
    results = {}
    
    if args.all:
        results = download_all()
    else:
        if args.vision:
            for model_info in REQUIRED_MODELS["vision"]:
                model_name = model_info["name"]
                results[model_name] = download_model(
                    model_name, 
                    model_info.get("description", "")
                )
        
        if args.llm:
            for model_info in REQUIRED_MODELS["llm"]:
                model_name = model_info["name"]
                results[model_name] = download_model(
                    model_name,
                    model_info.get("description", "")
                )
        
        if args.tokenizer:
            for model_info in REQUIRED_MODELS["tokenizer"]:
                model_name = model_info["name"]
                results[model_name] = download_model_components(model_name)
    
    # 如果没有指定任何选项，显示帮助
    if not results:
        parser.print_help()
        return
    
    # 打印摘要
    print_summary(results)


if __name__ == "__main__":
    main()
