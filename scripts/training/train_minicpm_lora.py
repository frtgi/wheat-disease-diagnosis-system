# -*- coding: utf-8 -*-
"""
MiniCPM-V 4.5 LoRA 微调训练脚本

基于 LLaMA-Factory 的农业领域微调

用法:
    python scripts/training/train_minicpm_lora.py
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def setup_windows_environment():
    """
    配置 Windows 环境
    """
    if sys.platform != 'win32':
        return
    
    os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
    os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '0')
    os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN', '1')
    
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    os.environ['MODELSCOPE_CACHE'] = os.environ.get(
        'MODELSCOPE_CACHE',
        os.path.join(os.path.expanduser('~'), '.cache', 'modelscope')
    )


def check_dependencies():
    """
    检查依赖包
    """
    print("=" * 60)
    print("依赖检查")
    print("=" * 60)
    
    missing = []
    
    try:
        import torch
        print(f"[OK] PyTorch: {torch.__version__}")
    except ImportError:
        print("[缺失] PyTorch")
        missing.append("torch")
    
    try:
        import transformers
        print(f"[OK] Transformers: {transformers.__version__}")
    except ImportError:
        print("[缺失] Transformers")
        missing.append("transformers")
    
    try:
        import peft
        print(f"[OK] PEFT: {peft.__version__}")
    except ImportError:
        print("[缺失] PEFT")
        missing.append("peft")
    
    try:
        from modelscope import snapshot_download
        print("[OK] ModelScope")
    except ImportError:
        print("[缺失] ModelScope")
        missing.append("modelscope")
    
    if missing:
        print(f"\n[错误] 缺少依赖: {', '.join(missing)}")
        print("\n安装命令:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)
    
    print("\n[OK] 所有依赖已安装")
    print("=" * 60)


def create_training_config():
    """
    创建训练配置
    """
    from cognition.minicpm_trainer import MiniCPMTrainerConfig
    
    config = MiniCPMTrainerConfig(
        model_id="OpenBMB/MiniCPM-V-4_5",
        output_dir="models/agri_minicpm",
        
        use_lora=True,
        lora_r=4,
        lora_alpha=8,
        lora_dropout=0.05,
        
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_ratio=0.1,
        
        load_in_4bit=True,
        bf16=True,
        
        max_seq_length=2048,
        dataset_path="datasets/agroinstruct"
    )
    
    return config


def main():
    """
    主函数
    """
    setup_windows_environment()
    check_dependencies()
    
    print("\n" + "=" * 60)
    print("MiniCPM-V 4.5 LoRA 微调训练")
    print("=" * 60)
    
    config = create_training_config()
    
    print("\n训练配置:")
    print(f"  模型: {config.model_id}")
    print(f"  输出目录: {config.output_dir}")
    print(f"  LoRA rank: {config.lora_r}")
    print(f"  4bit量化: {config.load_in_4bit}")
    print(f"  训练轮数: {config.num_train_epochs}")
    print(f"  批次大小: {config.per_device_train_batch_size}")
    print(f"  梯度累积: {config.gradient_accumulation_steps}")
    print(f"  学习率: {config.learning_rate}")
    
    print("\n[提示] 完整训练需要使用 LLaMA-Factory")
    print("  参考: https://github.com/hiyouga/LLaMA-Factory")
    print("\n[提示] 训练配置已保存，可使用 LLaMA-Factory 进行训练")
    
    from cognition.minicpm_trainer import create_trainer
    
    trainer = create_trainer(
        model_id=config.model_id,
        output_dir=config.output_dir,
        lora_r=config.lora_r,
        load_in_4bit=config.load_in_4bit
    )
    
    trainer.train()
    
    print("\n" + "=" * 60)
    print("训练配置已生成")
    print("=" * 60)
    print(f"\n配置文件: {Path(config.output_dir) / 'trainer_config.json'}")
    print(f"\n使用 LLaMA-Factory 训练命令:")
    print(f"  llamafactory-cli train {Path(config.output_dir) / 'trainer_config.json'}")


if __name__ == "__main__":
    main()
