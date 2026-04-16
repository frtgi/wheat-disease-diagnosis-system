# -*- coding: utf-8 -*-
"""
Qwen3.5-4B 模型下载脚本

使用ModelScope SDK下载Qwen3.5-4B模型到本地目录
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

def download_qwen_model():
    """
    下载Qwen3.5-4B模型
    
    模型规格:
    - 参数量: 4B
    - 模型大小: ~8GB
    - 上下文长度: 32K
    """
    print("=" * 60)
    print("Qwen3.5-4B 模型下载")
    print("=" * 60)
    
    try:
        from modelscope import snapshot_download
        
        model_id = "Qwen/Qwen3.5-4B"
        local_dir = project_root / "models" / "Qwen" / "Qwen3.5-4B"
        local_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n模型ID: {model_id}")
        print(f"目标路径: {local_dir}")
        print("\n开始下载...")
        
        model_path = snapshot_download(
            model_id=model_id,
            local_dir=str(local_dir),
            revision="master"
        )
        
        print(f"\n[OK] 模型下载完成!")
        print(f"模型路径: {model_path}")
        
        return str(local_dir)
        
    except ImportError:
        print("[错误] modelscope未安装，尝试使用HuggingFace...")
        return download_with_huggingface()
    except Exception as e:
        print(f"[错误] 下载失败: {e}")
        return None


def download_with_huggingface():
    """
    使用HuggingFace下载模型
    """
    try:
        from huggingface_hub import snapshot_download
        
        model_id = "Qwen/Qwen3.5-4B"
        local_dir = project_root / "models" / "Qwen" / "Qwen3.5-4B"
        local_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n使用HuggingFace下载...")
        print(f"模型ID: {model_id}")
        print(f"目标路径: {local_dir}")
        
        model_path = snapshot_download(
            repo_id=model_id,
            local_dir=str(local_dir),
            resume_download=True
        )
        
        print(f"\n[OK] 模型下载完成!")
        print(f"模型路径: {model_path}")
        
        return str(local_dir)
        
    except Exception as e:
        print(f"[错误] HuggingFace下载失败: {e}")
        return None


def verify_model(model_path: str):
    """
    验证模型文件完整性
    
    :param model_path: 模型路径
    """
    print("\n" + "=" * 60)
    print("验证模型文件")
    print("=" * 60)
    
    model_dir = Path(model_path)
    
    required_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ]
    
    safetensors_files = list(model_dir.glob("*.safetensors"))
    
    print(f"\n模型目录: {model_dir}")
    
    missing_files = []
    for f in required_files:
        file_path = model_dir / f
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {f}: {size_mb:.2f} MB")
        else:
            missing_files.append(f)
            print(f"  [缺失] {f}")
    
    if safetensors_files:
        total_size = 0
        for sf in safetensors_files:
            size_gb = sf.stat().st_size / (1024 * 1024 * 1024)
            total_size += size_gb
            print(f"  [OK] {sf.name}: {size_gb:.2f} GB")
        print(f"\n  模型权重总大小: {total_size:.2f} GB")
    else:
        print("  [警告] 未找到safetensors文件")
    
    if missing_files:
        print(f"\n[警告] 缺少文件: {missing_files}")
        return False
    
    print("\n[OK] 模型验证通过!")
    return True


if __name__ == "__main__":
    model_path = download_qwen_model()
    
    if model_path:
        verify_model(model_path)
