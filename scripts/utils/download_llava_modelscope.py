# -*- coding: utf-8 -*-
"""
LLaVA模型下载脚本 (ModelScope)

使用魔塔社区ModelScope下载LLaVA模型
支持模型:
- llava-v1.6-mistral-7b-hf (推荐)
- llava-1.5-7b-hf
"""
import os
import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def download_llava_model(model_name: str = "llava-v1.6-mistral-7b-hf", local_dir: str = None):
    """
    使用ModelScope下载LLaVA模型
    
    Args:
        model_name: 模型名称
        local_dir: 本地保存目录
    
    Returns:
        模型保存路径
    """
    print("=" * 60)
    print(" LLaVA 模型下载 (ModelScope)")
    print("=" * 60)
    
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("[错误] ModelScope未安装，请运行: pip install modelscope")
        return None
    
    if local_dir is None:
        local_dir = str(project_root / "models" / model_name)
    
    model_id = f"llava-hf/{model_name}"
    
    print(f"\n模型ID: {model_id}")
    print(f"保存目录: {local_dir}")
    print(f"\n开始下载... (模型约14GB，请耐心等待)")
    print("-" * 60)
    
    try:
        model_dir = snapshot_download(
            model_id,
            cache_dir=str(project_root / "models")
        )
        
        print("\n" + "=" * 60)
        print("✅ 模型下载完成!")
        print(f"模型路径: {model_dir}")
        print("=" * 60)
        
        # 验证文件完整性
        verify_model_files(model_dir)
        
        return model_dir
        
    except Exception as e:
        print(f"\n[错误] 下载失败: {e}")
        return None


def verify_model_files(model_dir: str):
    """
    验证模型文件完整性
    
    Args:
        model_dir: 模型目录
    """
    print("\n验证模型文件...")
    
    required_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ]
    
    model_dir = Path(model_dir)
    
    all_ok = True
    for f in required_files:
        file_path = model_dir / f
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  ✅ {f}: {size_kb:.1f} KB")
        else:
            print(f"  ❌ {f}: 不存在")
            all_ok = False
    
    # 检查模型权重文件
    weight_files = list(model_dir.glob("*.safetensors")) + list(model_dir.glob("pytorch_model*.bin"))
    if weight_files:
        total_size = sum(f.stat().st_size for f in weight_files) / (1024**3)
        print(f"  ✅ 模型权重: {len(weight_files)} 个文件, 共 {total_size:.2f} GB")
    else:
        print("  ❌ 模型权重文件不存在")
        all_ok = False
    
    if all_ok:
        print("\n✅ 模型文件验证通过!")
    else:
        print("\n⚠️ 部分文件缺失，请重新下载")


def list_available_models():
    """列出可用的LLaVA模型"""
    print("\n可用的LLaVA模型:")
    print("-" * 40)
    models = [
        ("llava-v1.6-mistral-7b-hf", "~14GB", "推荐，基于Mistral-7B，性能更优"),
        ("llava-1.5-7b-hf", "~13GB", "LLaVA 1.5版本"),
        ("llava-1.5-13b-hf", "~25GB", "LLaVA 1.5 13B版本，需要更多显存"),
    ]
    for name, size, desc in models:
        print(f"  {name}")
        print(f"    大小: {size}")
        print(f"    说明: {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(description="LLaVA模型下载工具 (ModelScope)")
    parser.add_argument(
        "--model", 
        type=str, 
        default="llava-v1.6-mistral-7b-hf",
        help="模型名称 (默认: llava-v1.6-mistral-7b-hf)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="输出目录 (默认: models/<model_name>)"
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="列出可用模型"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_available_models()
        return
    
    download_llava_model(args.model, args.output)


if __name__ == "__main__":
    main()
