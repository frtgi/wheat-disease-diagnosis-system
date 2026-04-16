# -*- coding: utf-8 -*-
"""
Qwen3-VL-4B-Instruct 4bit量化训练配置

用于低显存环境下的模型微调（原生多模态支持）
"""
from dataclasses import dataclass, field
from typing import Optional, List
import os


@dataclass
class Qwen4bitTrainingConfig:
    """
    Qwen3-VL-4B-Instruct 4bit量化训练配置
    
    适用于3GB显存设备的微调配置（原生多模态支持）
    """
    
    # 模型配置
    model_id: str = "Qwen/Qwen3-VL-4B-Instruct"
    local_path: str = "models/Qwen3-VL-4B-Instruct"
    use_local: bool = True
    
    # 量化配置
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"
    
    # LoRA配置
    use_lora: bool = True
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "v_proj", "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    
    # 训练配置
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    lr_scheduler_type: str = "cosine"
    
    # 优化配置
    fp16: bool = False
    bf16: bool = True
    gradient_checkpointing: bool = True
    optim: str = "adamw_torch"
    max_grad_norm: float = 1.0
    
    # 显存优化
    max_memory: str = "3GiB"
    cpu_offload: bool = True
    
    # 数据配置
    max_seq_length: int = 512
    train_data_path: str = "datasets/agroinstruct/agroinstruct_train.json"
    eval_data_path: str = "datasets/agroinstruct/agroinstruct_val.json"
    
    # 输出配置
    output_dir: str = "models/qwen_lora_4bit"
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 3
    
    def get_bitsandbytes_config(self):
        """获取BitsAndBytes配置"""
        from transformers import BitsAndBytesConfig
        import torch
        
        compute_dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32
        }
        
        return BitsAndBytesConfig(
            load_in_4bit=self.load_in_4bit,
            load_in_8bit=self.load_in_8bit,
            bnb_4bit_compute_dtype=compute_dtype_map.get(
                self.bnb_4bit_compute_dtype, torch.bfloat16
            ),
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type
        )
    
    def get_lora_config(self):
        """获取LoRA配置"""
        from peft import LoraConfig
        
        return LoraConfig(
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.lora_target_modules,
            bias="none",
            task_type="CAUSAL_LM"
        )
    
    def get_training_arguments(self):
        """获取训练参数"""
        from transformers import TrainingArguments
        
        return TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.num_train_epochs,
            per_device_train_batch_size=self.per_device_train_batch_size,
            per_device_eval_batch_size=self.per_device_eval_batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            learning_rate=self.learning_rate,
            weight_decay=self.weight_decay,
            warmup_ratio=self.warmup_ratio,
            lr_scheduler_type=self.lr_scheduler_type,
            fp16=self.fp16,
            bf16=self.bf16,
            gradient_checkpointing=self.gradient_checkpointing,
            optim=self.optim,
            max_grad_norm=self.max_grad_norm,
            logging_steps=self.logging_steps,
            save_steps=self.save_steps,
            eval_steps=self.eval_steps,
            save_total_limit=self.save_total_limit,
            report_to="none",
            remove_unused_columns=False
        )


def create_4bit_training_config(**kwargs) -> Qwen4bitTrainingConfig:
    """
    创建4bit训练配置
    
    :param kwargs: 配置参数覆盖
    :return: 配置实例
    """
    return Qwen4bitTrainingConfig(**kwargs)


def verify_4bit_environment():
    """
    验证4bit训练环境
    
    :return: 验证结果
    """
    import sys
    
    print("=" * 60)
    print("4bit量化训练环境验证")
    print("=" * 60)
    
    results = {
        "python_version": sys.version,
        "checks": [],
        "passed": True
    }
    
    # 检查PyTorch
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3) if cuda_available else 0
        
        check = {
            "name": "PyTorch",
            "status": "✅" if cuda_available else "❌",
            "info": f"v{torch.__version__}, CUDA={cuda_available}, GPU={gpu_name} ({gpu_memory:.1f}GB)"
        }
        results["checks"].append(check)
        
        if gpu_memory < 3.5:
            print(f"⚠️ 显存不足: {gpu_memory:.1f}GB < 3.5GB")
            results["passed"] = False
            
    except ImportError as e:
        results["checks"].append({"name": "PyTorch", "status": "❌", "info": str(e)})
        results["passed"] = False
    
    # 检查transformers
    try:
        import transformers
        results["checks"].append({
            "name": "Transformers",
            "status": "✅",
            "info": f"v{transformers.__version__}"
        })
    except ImportError as e:
        results["checks"].append({"name": "Transformers", "status": "❌", "info": str(e)})
        results["passed"] = False
    
    # 检查bitsandbytes
    try:
        import bitsandbytes
        results["checks"].append({
            "name": "BitsAndBytes",
            "status": "✅",
            "info": f"v{bitsandbytes.__version__}"
        })
    except ImportError as e:
        results["checks"].append({"name": "BitsAndBytes", "status": "❌", "info": str(e)})
        results["passed"] = False
    
    # 检查peft
    try:
        import peft
        results["checks"].append({
            "name": "PEFT",
            "status": "✅",
            "info": f"v{peft.__version__}"
        })
    except ImportError as e:
        results["checks"].append({"name": "PEFT", "status": "❌", "info": str(e)})
        results["passed"] = False
    
    # 检查accelerate
    try:
        import accelerate
        results["checks"].append({
            "name": "Accelerate",
            "status": "✅",
            "info": f"v{accelerate.__version__}"
        })
    except ImportError as e:
        results["checks"].append({"name": "Accelerate", "status": "❌", "info": str(e)})
        results["passed"] = False
    
    # 检查模型文件
    model_path = "D:/Project/WheatAgent/models/Qwen3-VL-4B-Instruct"
    config_file = os.path.join(model_path, "config.json")
    if os.path.exists(config_file):
        results["checks"].append({
            "name": "Qwen-VL模型",
            "status": "✅",
            "info": f"路径: {model_path}"
        })
    else:
        results["checks"].append({
            "name": "Qwen-VL模型",
            "status": "⚠️",
            "info": "模型未下载"
        })
    
    # 打印结果
    print("\n检查结果:")
    for check in results["checks"]:
        print(f"  {check['status']} {check['name']}: {check['info']}")
    
    print("\n" + "=" * 60)
    if results["passed"]:
        print("✅ 环境验证通过，可以进行4bit量化训练")
    else:
        print("❌ 环境验证失败，请安装缺失的依赖")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    verify_4bit_environment()
