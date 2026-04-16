# -*- coding: utf-8 -*-
"""
INT4量化模型加载测试脚本

测试Qwen3-VL-4B-Instruct模型的INT4量化加载和GPU推理
"""
import os
import sys
import torch
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_int4_quantization():
    """
    测试INT4量化模型加载
    
    验证BitsAndBytes INT4量化配置和GPU推理功能
    """
    print("=" * 60)
    print("INT4量化模型加载测试")
    print("=" * 60)
    
    print("\n[1/5] 检查CUDA环境...")
    print(f"   PyTorch版本: {torch.__version__}")
    print(f"   CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU设备: {torch.cuda.get_device_name(0)}")
        print(f"   显存总量: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    print("\n[2/5] 导入依赖库...")
    try:
        from transformers import AutoTokenizer, AutoProcessor, BitsAndBytesConfig
        from transformers import Qwen3VLForConditionalGeneration
        import bitsandbytes as bnb
        print(f"   Transformers: OK")
        print(f"   BitsAndBytes: v{bnb.__version__}")
    except ImportError as e:
        print(f"   导入失败: {e}")
        return False
    
    print("\n[3/5] 配置INT4量化...")
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )
    print("   量化类型: NF4")
    print("   计算精度: float16")
    print("   双重量化: 启用")
    
    print("\n[4/5] 加载模型...")
    model_path = "D:/Project/WheatAgent/models/Qwen3-VL-4B-Instruct"
    if not os.path.exists(model_path):
        print(f"   模型路径不存在: {model_path}")
        return False
    
    try:
        print(f"   加载路径: {model_path}")
        
        processor = AutoProcessor.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print("   Processor加载成功")
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print("   Tokenizer加载成功")
        
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            torch_dtype=torch.float16,
            device_map="cuda:0",
            trust_remote_code=True
        )
        print("   模型加载成功 (INT4量化)")
        
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            print(f"   显存占用: {allocated:.2f} GB (已分配) / {reserved:.2f} GB (已预留)")
        
    except Exception as e:
        print(f"   模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[5/5] 测试GPU推理...")
    try:
        test_prompt = "你好，请介绍一下你自己。"
        inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)
        
        print(f"   输入: {test_prompt}")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0][len(inputs['input_ids'][0]):], skip_special_tokens=True)
        print(f"   输出: {response[:100]}...")
        
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            print(f"   推理后显存: {allocated:.2f} GB")
        
        print("\n" + "=" * 60)
        print("INT4量化测试成功!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"   推理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_int4_quantization()
    sys.exit(0 if success else 1)
