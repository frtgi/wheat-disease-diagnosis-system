# -*- coding: utf-8 -*-
"""
LLaVA 1.6 LoRA 微调训练脚本 (Mistral-7B 优化版)
针对 4GB 显存设备优化，使用 4bit 量化和梯度检查点

使用方法:
    python scripts/training/train_llava_lora.py --epochs 3 --batch_size 1

依赖:
    pip install peft transformers accelerate bitsandbytes

Windows 环境注意事项:
    - 已自动配置 HuggingFace 环境变量以禁用符号链接
    - 如遇到符号链接错误，请运行: python scripts/utils/fix_hf_cache.py
    - 或启用 Windows 开发者模式以支持符号链接

LLaVA 1.6 特性:
    - 基于 Mistral-7B 架构
    - 支持更高分辨率图像
    - 改进的多模态理解能力
"""
import os
import sys

if sys.platform == 'win32':
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

import json
import argparse
import platform
import torch
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')


def setup_windows_environment(cache_dir: Optional[str] = None) -> Dict[str, str]:
    """
    配置 Windows 环境下的 HuggingFace 环境变量
    
    解决 Windows 符号链接问题：
    - [WinError 14007] 在活动的激活上下文中找不到任何查找密钥
    
    :param cache_dir: 自定义缓存目录
    :return: 设置的环境变量字典
    """
    env_vars = {}
    
    env_vars['HF_ENDPOINT'] = 'https://hf-mirror.com'
    env_vars['TOKENIZERS_PARALLELISM'] = 'false'
    env_vars['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    env_vars['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    env_vars['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
    env_vars['HF_HUB_DISABLE_TELEMETRY'] = '1'
    
    if platform.system() == 'Windows':
        if cache_dir:
            cache_path = Path(cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            env_vars['HF_HOME'] = str(cache_path)
            env_vars['HF_HUB_CACHE'] = str(cache_path / "hub")
            env_vars['TRANSFORMERS_CACHE'] = str(cache_path)
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    return env_vars


setup_windows_environment()


@dataclass
class LoRAConfig:
    """
    LoRA 配置 (LLaVA 1.6 Mistral 架构优化)
    
    针对 4GB 显存优化:
    - 降低 rank 至 4 以减少显存占用
    - 针对 Mistral 架构调整 target_modules
    """
    r: int = 4
    lora_alpha: int = 8
    lora_dropout: float = 0.05
    target_modules: List[str] = None
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]


def check_dependencies():
    """检查依赖"""
    print("=" * 60)
    print("🔍 检查依赖...")
    print("=" * 60)
    
    missing = []
    
    try:
        import transformers
        print(f"✅ transformers: {transformers.__version__}")
    except ImportError:
        missing.append("transformers")
    
    try:
        import peft
        print(f"✅ peft: {peft.__version__}")
    except ImportError:
        missing.append("peft")
    
    try:
        import accelerate
        print(f"✅ accelerate: {accelerate.__version__}")
    except ImportError:
        missing.append("accelerate")
    
    try:
        import bitsandbytes
        print(f"✅ bitsandbytes: {bitsandbytes.__version__}")
    except ImportError:
        missing.append("bitsandbytes")
    
    if missing:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        return False
    
    return True


def load_model_4bit(model_id: str, cache_dir: Optional[str] = None):
    """
    加载 4bit 量化模型
    
    针对 Windows 环境优化：
    - 自动处理符号链接问题
    - 支持自定义缓存目录
    - 提供详细的错误诊断
    
    :param model_id: 模型ID
    :param cache_dir: 自定义缓存目录
    :return: 模型和处理器
    """
    from transformers import (
        LlavaForConditionalGeneration,
        LlavaProcessor,
        BitsAndBytesConfig
    )
    
    print(f"\n🔄 加载模型: {model_id}")
    print("   使用 4bit 量化...")
    
    if platform.system() == 'Windows':
        print("   Windows 环境: 已禁用符号链接")
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_quant_storage=torch.uint8
    )
    
    load_kwargs = {
        "quantization_config": quantization_config,
        "device_map": "auto",
        "trust_remote_code": True,
        "force_download": False,
        "resume_download": True
    }
    
    if cache_dir:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        load_kwargs["cache_dir"] = str(cache_path)
        os.environ['HF_HOME'] = str(cache_path)
        os.environ['HF_HUB_CACHE'] = str(cache_path / "hub")
        os.environ['TRANSFORMERS_CACHE'] = str(cache_path)
    
    try:
        model = LlavaForConditionalGeneration.from_pretrained(
            model_id,
            **load_kwargs
        )
        
        processor_kwargs = {
            "trust_remote_code": True,
            "force_download": False,
            "resume_download": True
        }
        if cache_dir:
            processor_kwargs["cache_dir"] = str(cache_path)
        
        processor = LlavaProcessor.from_pretrained(
            model_id,
            **processor_kwargs
        )
        
        print("✅ 模型加载成功")
        return model, processor
        
    except OSError as e:
        error_str = str(e).lower()
        if "symbolic link" in error_str or "14007" in str(e) or "symlink" in error_str:
            print("\n❌ 检测到 Windows 符号链接错误!")
            print("   请运行以下命令修复缓存:")
            print("   python scripts/utils/fix_hf_cache.py --force")
            print("\n   或启用 Windows 开发者模式:")
            print("   设置 -> 更新和安全 -> 开发者选项 -> 开发者模式")
            raise RuntimeError(
                "Windows 符号链接错误。请运行: python scripts/utils/fix_hf_cache.py"
            ) from e
        raise
    except Exception as e:
        print(f"\n❌ 模型加载失败: {e}")
        raise


def apply_lora(model, lora_config: LoRAConfig):
    """
    应用 LoRA 适配器
    
    :param model: 基础模型
    :param lora_config: LoRA 配置
    :return: PEFT 模型
    """
    from peft import LoraConfig, get_peft_model, TaskType
    
    print(f"\n🔄 应用 LoRA 适配器...")
    print(f"   r={lora_config.r}, alpha={lora_config.lora_alpha}")
    
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_config.r,
        lora_alpha=lora_config.lora_alpha,
        lora_dropout=lora_config.lora_dropout,
        target_modules=lora_config.target_modules,
        bias="none"
    )
    
    peft_model = get_peft_model(model, peft_config)
    peft_model.print_trainable_parameters()
    
    print("✅ LoRA 适配器应用成功")
    
    return peft_model


def load_dataset(data_path: str):
    """
    加载数据集
    
    :param data_path: 数据路径
    :return: 数据列表
    """
    print(f"\n🔄 加载数据集: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 加载 {len(data)} 条数据")
    
    return data


def prepare_for_training(model, train_data: List[Dict], processor, output_dir: str):
    """
    准备训练
    
    :param model: 模型
    :param train_data: 训练数据
    :param processor: 处理器
    :param output_dir: 输出目录
    """
    from transformers import TrainingArguments, Trainer
    from peft import prepare_model_for_kbit_training
    
    print("\n🔄 准备训练...")
    
    # 准备模型进行 k-bit 训练
    model = prepare_model_for_kbit_training(model)
    
    # 启用梯度检查点
    if hasattr(model, 'enable_input_require_grads'):
        model.enable_input_require_grads()
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_ratio=0.03,
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        fp16=True,
        gradient_checkpointing=True,
        optim="adamw_torch",
        max_grad_norm=1.0,
        report_to="none",
        dataloader_pin_memory=False,
        dataloader_num_workers=0,
        max_seq_length=512
    )
    
    print(f"✅ 训练准备完成")
    print(f"   输出目录: {output_dir}")
    print(f"   批次大小: 1 (4GB显存优化)")
    print(f"   梯度累积: 16")
    print(f"   学习率: 2e-4")
    print(f"   最大序列长度: 512")
    
    return model, training_args


def train_lora(
    model_id: str = "models/llava-hf/llava-v1___6-mistral-7b-hf",
    train_data_path: str = "datasets/agroinstruct/agroinstruct_train.json",
    output_dir: str = "models/agri_llava_lora",
    lora_config: Optional[LoRAConfig] = None,
    epochs: int = 1,
    cache_dir: Optional[str] = None
):
    """
    执行 LoRA 微调训练 (LLaVA 1.6 Mistral 版本)
    
    针对 4GB 显存优化:
    - 使用 4bit NF4 量化
    - 启用双重量化 (double quantization)
    - 梯度检查点
    - 较小的 LoRA rank
    
    :param model_id: 模型ID或本地路径 (默认 LLaVA 1.6 Mistral-7B)
    :param train_data_path: 训练数据路径
    :param output_dir: 输出目录
    :param lora_config: LoRA 配置
    :param epochs: 训练轮数
    :param cache_dir: HuggingFace 缓存目录
    """
    print("=" * 60)
    print("🌾 LLaVA 1.6 LoRA 微调训练 (Mistral-7B)")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"系统平台: {platform.system()} {platform.release()}")
    
    if platform.system() == 'Windows':
        print("\n⚙️ Windows 环境配置:")
        setup_windows_environment(cache_dir)
    
    if not check_dependencies():
        return False
    
    lora_config = lora_config or LoRAConfig()
    
    try:
        model, processor = load_model_4bit(model_id, cache_dir=cache_dir)
        
        model = apply_lora(model, lora_config)
        
        train_data = load_dataset(train_data_path)
        
        model, training_args = prepare_for_training(
            model, train_data, processor, output_dir
        )
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        config_path = output_path / "lora_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                "model_id": model_id,
                "lora_config": asdict(lora_config),
                "train_samples": len(train_data),
                "created_at": datetime.now().isoformat(),
                "platform": platform.platform(),
                "cache_dir": cache_dir
            }, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ LoRA 微调配置完成")
        print("=" * 60)
        print(f"   模型: {model_id}")
        print(f"   训练数据: {len(train_data)} 条")
        print(f"   输出目录: {output_dir}")
        if cache_dir:
            print(f"   缓存目录: {cache_dir}")
        print(f"\n💡 提示: 由于 4GB 显存限制，完整训练需要:")
        print(f"   1. 更大的显存 (推荐 16GB+)")
        print(f"   2. 或使用云端 GPU 服务")
        print(f"   3. 或减少训练数据量")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LLaVA 1.6 LoRA 微调训练 (Mistral-7B)")
    parser.add_argument("--model", default="models/llava-hf/llava-v1___6-mistral-7b-hf", 
                        help="模型ID或本地路径 (默认 LLaVA 1.6 Mistral-7B)")
    parser.add_argument("--data", default="datasets/agroinstruct/agroinstruct_train.json", help="训练数据路径")
    parser.add_argument("--output", default="models/agri_llava_lora", help="输出目录")
    parser.add_argument("--epochs", type=int, default=1, help="训练轮数")
    parser.add_argument("--lora_r", type=int, default=4, help="LoRA rank (默认4, 适配4GB显存)")
    parser.add_argument("--lora_alpha", type=int, default=8, help="LoRA alpha (默认8)")
    parser.add_argument("--cache-dir", type=str, default=None, 
                        help="HuggingFace 缓存目录 (Windows 推荐设置)")
    
    args = parser.parse_args()
    
    lora_config = LoRAConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha
    )
    
    success = train_lora(
        model_id=args.model,
        train_data_path=args.data,
        output_dir=args.output,
        lora_config=lora_config,
        epochs=args.epochs,
        cache_dir=args.cache_dir
    )
    
    if success:
        print("\n🎉 LoRA 微调配置成功！")
    else:
        print("\n❌ LoRA 微调配置失败")


if __name__ == "__main__":
    main()
