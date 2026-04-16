"""
LLaVA 1.6 模型验证脚本

验证模型加载和推理功能
"""
import os
import sys
import time
import traceback

def get_gpu_memory():
    """获取GPU显存使用情况"""
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            return allocated, reserved
    except:
        pass
    return 0, 0

def verify_llava_model():
    """验证LLaVA模型加载和推理"""
    print("=" * 60)
    print("LLaVA 1.6 模型验证")
    print("=" * 60)
    
    model_path = r"D:\Project\WheatAgent\models\llava-hf\llava-v1___6-mistral-7b-hf"
    
    if not os.path.exists(model_path):
        print(f"[错误] 模型路径不存在: {model_path}")
        return False
    
    print(f"\n[1] 模型路径: {model_path}")
    
    print("\n[2] 检查依赖...")
    try:
        import torch
        print(f"    PyTorch 版本: {torch.__version__}")
        print(f"    CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"    GPU 设备: {torch.cuda.get_device_name(0)}")
            print(f"    GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    except ImportError as e:
        print(f"[错误] PyTorch 未安装: {e}")
        return False
    
    try:
        import transformers
        print(f"    Transformers 版本: {transformers.__version__}")
    except ImportError as e:
        print(f"[错误] Transformers 未安装: {e}")
        return False
    
    try:
        import accelerate
        print(f"    Accelerate 版本: {accelerate.__version__}")
    except ImportError:
        print("[警告] Accelerate 未安装")
    
    try:
        import bitsandbytes
        print(f"    BitsAndBytes 版本: {bitsandbytes.__version__}")
    except ImportError:
        print("[警告] BitsAndBytes 未安装，无法使用量化")
    
    try:
        from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration, BitsAndBytesConfig
        print("    LlavaNext 模块导入成功")
    except ImportError as e:
        print(f"[错误] 无法导入 LlavaNext 模块: {e}")
        print("    请确保 transformers 版本 >= 4.39.0")
        return False
    
    try:
        from PIL import Image
        print("    PIL 导入成功")
    except ImportError:
        print("[警告] PIL 未安装，将使用纯文本测试")
    
    load_time = 0
    inference_time = 0
    reserved = 0
    
    print("\n[3] 加载模型...")
    start_time = time.time()
    
    try:
        print("    正在加载 Processor...")
        processor = LlavaNextProcessor.from_pretrained(model_path)
        
        print("    正在加载模型 (4bit量化)...")
        print("    注意: GPU显存4GB较小，将尝试优化加载...")
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        model = LlavaNextForConditionalGeneration.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            torch_dtype=torch.float16,
            device_map="cuda:0",
            low_cpu_mem_usage=True,
        )
        
        load_time = time.time() - start_time
        print(f"    模型加载完成! 耗时: {load_time:.2f} 秒")
        
        allocated, reserved = get_gpu_memory()
        print(f"    GPU 显存已分配: {allocated:.2f} GB")
        print(f"    GPU 显存已预留: {reserved:.2f} GB")
        
    except Exception as e:
        print(f"[警告] 4bit量化加载失败: {e}")
        print("    尝试使用CPU加载...")
        
        try:
            start_time = time.time()
            model = LlavaNextForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True,
            )
            load_time = time.time() - start_time
            print(f"    模型加载完成 (CPU模式)! 耗时: {load_time:.2f} 秒")
        except Exception as e2:
            print(f"[错误] 模型加载失败: {e2}")
            traceback.print_exc()
            return False
    
    print("\n[4] 测试推理...")
    try:
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "你好，请用中文简单介绍一下你自己。"},
                ],
            },
        ]
        
        prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
        inputs = processor(text=prompt, return_tensors="pt")
        
        if hasattr(model, 'device'):
            inputs = inputs.to(model.device)
        
        print("    开始生成...")
        inference_start = time.time()
        
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=False,
            )
        
        inference_time = time.time() - inference_start
        generated_text = processor.decode(output[0], skip_special_tokens=True)
        
        print(f"    推理完成! 耗时: {inference_time:.2f} 秒")
        
        allocated, reserved = get_gpu_memory()
        print(f"    GPU 显存已分配: {allocated:.2f} GB")
        print(f"    GPU 显存已预留: {reserved:.2f} GB")
        
        print("\n[5] 生成结果:")
        print("-" * 50)
        print(generated_text[-500:] if len(generated_text) > 500 else generated_text)
        print("-" * 50)
        
    except Exception as e:
        print(f"[错误] 推理测试失败: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    print(f"模型加载: 成功")
    print(f"加载时间: {load_time:.2f} 秒")
    print(f"推理时间: {inference_time:.2f} 秒")
    print(f"显存占用: {reserved:.2f} GB")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = verify_llava_model()
    sys.exit(0 if success else 1)
