# -*- coding: utf-8 -*-
"""
Qwen3-VL-4B-Instruct 模型下载脚本

使用 ModelScope 下载 Qwen3-VL-4B-Instruct 模型到本地
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

try:
    from modelscope import snapshot_download
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False
    print("⚠️  warnings: modelscope 库未安装，将尝试使用 HuggingFace")


def download_with_modelscope(model_id: str, cache_dir: str):
    """
    使用 ModelScope 下载模型
    
    :param model_id: 模型 ID
    :param cache_dir: 缓存目录
    :return: 下载路径
    """
    print(f"🚀 开始下载模型：{model_id}")
    print(f"📁 保存路径：{cache_dir}")
    
    try:
        model_dir = snapshot_download(
            model_id,
            cache_dir=cache_dir,
            revision='master'
        )
        print(f"✅ 模型下载完成！")
        print(f"📂 模型路径：{model_dir}")
        return model_dir
    except Exception as e:
        print(f"❌ ModelScope 下载失败：{e}")
        raise


def download_with_huggingface(model_id: str, cache_dir: str):
    """
    使用 HuggingFace 下载模型（备用方案）
    
    :param model_id: 模型 ID
    :param cache_dir: 缓存目录
    :return: 下载路径
    """
    print(f"🔄 尝试使用 HuggingFace 下载...")
    
    try:
        from huggingface_hub import snapshot_download as hf_snapshot_download
        
        model_dir = hf_snapshot_download(
            repo_id=model_id,
            cache_dir=cache_dir,
            local_dir=cache_dir
        )
        print(f"✅ HuggingFace 下载完成！")
        print(f"📂 模型路径：{model_dir}")
        return model_dir
    except Exception as e:
        print(f"❌ HuggingFace 下载失败：{e}")
        raise


def verify_model_files(model_path: str) -> bool:
    """
    验证模型文件完整性
    
    :param model_path: 模型路径
    :return: 是否完整
    """
    print(f"\n🔍 验证模型文件...")
    
    required_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json"
    ]
    
    model_path = Path(model_path)
    all_exist = True
    
    for file_name in required_files:
        file_path = model_path / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✅ {file_name} ({file_size:.2f} MB)")
        else:
            print(f"  ❌ {file_name} 不存在")
            all_exist = False
    
    # 检查模型权重文件
    weight_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("*.bin"))
    if weight_files:
        for wf in weight_files:
            file_size = wf.stat().st_size / (1024 * 1024 * 1024)  # GB
            print(f"  ✅ {wf.name} ({file_size:.2f} GB)")
    else:
        print(f"  ❌ 未找到模型权重文件")
        all_exist = False
    
    return all_exist


def main():
    """
    主函数
    """
    print("=" * 60)
    print("Qwen3-VL-4B-Instruct 模型下载工具")
    print("=" * 60)
    
    model_id = "Qwen/Qwen3-VL-4B-Instruct"
    
    # 设置模型保存路径
    model_save_dir = project_root / "models" / "Qwen3-VL-4B-Instruct"
    model_save_dir.mkdir(parents=True, exist_ok=True)
    
    cache_dir = str(project_root / "models" / "cache")
    
    print(f"\n📋 模型信息:")
    print(f"  模型 ID: {model_id}")
    print(f"  保存路径：{model_save_dir}")
    print(f"  缓存路径：{cache_dir}")
    
    try:
        # 优先使用 ModelScope
        if MODELSCOPE_AVAILABLE:
            print(f"\n使用 ModelScope 下载...")
            model_path = download_with_modelscope(model_id, cache_dir)
        else:
            print(f"\nModelScope 不可用，使用 HuggingFace...")
            model_path = download_with_huggingface(model_id, cache_dir)
        
        # 验证模型文件
        if verify_model_files(model_path):
            print(f"\n{'=' * 60}")
            print(f"✅ 模型下载并验证成功！")
            print(f"{'=' * 60}")
            
            # 如果需要，可以复制到最终目录
            if Path(model_path) != model_save_dir:
                print(f"\n📦 复制模型到最终目录...")
                import shutil
                if model_save_dir.exists():
                    shutil.rmtree(model_save_dir)
                shutil.copytree(model_path, model_save_dir)
                print(f"✅ 模型已复制到：{model_save_dir}")
            
            return True
        else:
            print(f"\n❌ 模型文件验证失败！")
            return False
            
    except Exception as e:
        print(f"\n❌ 下载失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
