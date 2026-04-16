# -*- coding: utf-8 -*-
"""
MiniCPM-V 4.5 模型下载脚本

使用 ModelScope SDK 下载 OpenBMB/MiniCPM-V-4_5 模型

用法:
    python scripts/utils/download_minicpm_modelscope.py
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def download_minicpm_model():
    """
    下载 MiniCPM-V 4.5 模型
    
    模型信息:
    - 模型ID: OpenBMB/MiniCPM-V-4_5
    - 参数量: 8B (8.7B 总参数)
    - 基础模型: Qwen3-8B + SigLIP2-400M
    - 预计大小: 约 16-18GB
    """
    print("=" * 60)
    print("MiniCPM-V 4.5 模型下载")
    print("=" * 60)
    
    try:
        from modelscope import snapshot_download
        print("[OK] ModelScope SDK 已安装")
    except ImportError:
        print("[安装] 正在安装 ModelScope SDK...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "modelscope", "-q"])
        from modelscope import snapshot_download
        print("[OK] ModelScope SDK 安装完成")
    
    model_id = "OpenBMB/MiniCPM-V-4_5"
    cache_dir = project_root / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[配置]")
    print(f"  模型ID: {model_id}")
    print(f"  缓存目录: {cache_dir}")
    print(f"\n[下载] 开始下载模型...")
    print("  提示: 模型大小约 16-18GB，请耐心等待")
    print("-" * 60)
    
    try:
        model_dir = snapshot_download(
            model_id,
            cache_dir=str(cache_dir)
        )
        print("-" * 60)
        print(f"\n[成功] 模型下载完成!")
        print(f"  模型路径: {model_dir}")
        
        model_size = 0
        for root, dirs, files in os.walk(model_dir):
            for f in files:
                model_size += os.path.getsize(os.path.join(root, f))
        print(f"  模型大小: {model_size / (1024**3):.2f} GB")
        
        return model_dir
        
    except Exception as e:
        print(f"\n[错误] 下载失败: {e}")
        raise


def verify_model(model_dir: str):
    """
    验证模型文件完整性
    
    :param model_dir: 模型目录
    """
    print("\n[验证] 检查模型文件...")
    
    required_files = [
        "config.json",
        "model.safetensors.index.json",
    ]
    
    model_path = Path(model_dir)
    missing_files = []
    
    for f in required_files:
        if not (model_path / f).exists():
            missing_files.append(f)
    
    if missing_files:
        print(f"[警告] 缺少文件: {missing_files}")
        return False
    
    safetensors_files = list(model_path.glob("*.safetensors"))
    if not safetensors_files:
        print("[警告] 未找到 safetensors 文件")
        return False
    
    print(f"[OK] 找到 {len(safetensors_files)} 个模型文件")
    
    for f in safetensors_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name}: {size_mb:.1f} MB")
    
    print("[OK] 模型验证通过")
    return True


if __name__ == "__main__":
    model_dir = download_minicpm_model()
    verify_model(model_dir)
    
    print("\n" + "=" * 60)
    print("下载完成! 可以使用以下代码加载模型:")
    print("=" * 60)
    print("""
from modelscope import AutoModel, AutoTokenizer

model = AutoModel.from_pretrained(
    'OpenBMB/MiniCPM-V-4_5',
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained(
    'OpenBMB/MiniCPM-V-4_5',
    trust_remote_code=True
)
""")
