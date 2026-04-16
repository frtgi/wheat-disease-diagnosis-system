"""
MiniCPM-V 4.5 模型加载验证脚本 (GPU 模式)

尝试使用 GPU 加载模型，如果显存不足则使用 CPU offload
"""
import sys
import os
import gc

def count_parameters(model):
    """
    计算模型参数量
    
    Args:
        model: 加载的模型对象
        
    Returns:
        tuple: (总参数量, 可训练参数量)
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total_params, trainable_params

def format_params(num_params):
    """
    格式化参数数量显示
    
    Args:
        num_params: 参数数量
        
    Returns:
        str: 格式化后的字符串
    """
    if num_params >= 1e9:
        return f"{num_params / 1e9:.2f}B"
    elif num_params >= 1e6:
        return f"{num_params / 1e6:.2f}M"
    elif num_params >= 1e3:
        return f"{num_params / 1e3:.2f}K"
    else:
        return str(num_params)

def main():
    print("=" * 60)
    print("MiniCPM-V 4.5 模型加载验证 (GPU 模式)")
    print("=" * 60)
    
    model_path = r"D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5"
    
    if not os.path.exists(model_path):
        print(f"[错误] 模型路径不存在: {model_path}")
        return False
    
    print(f"\n[1] 模型路径: {model_path}")
    print(f"    路径存在: ✓")
    
    print("\n[2] 导入依赖库...")
    try:
        import torch
        print(f"    PyTorch 版本: {torch.__version__}")
        print(f"    CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"    GPU 设备: {torch.cuda.get_device_name(0)}")
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            print(f"    GPU 显存: {gpu_memory / 1e9:.1f} GB")
        
        from transformers import AutoModel, AutoTokenizer
        print("    Transformers 导入成功")
    except ImportError as e:
        print(f"[错误] 依赖导入失败: {e}")
        return False
    
    print("\n[3] 加载 Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print(f"    Tokenizer 加载成功 ✓")
        print(f"    词表大小: {len(tokenizer)}")
    except Exception as e:
        print(f"[错误] Tokenizer 加载失败: {e}")
        return False
    
    print("\n[4] 加载模型 (GPU 模式, float16)...")
    print("    注意: 这可能需要几分钟...")
    
    model = None
    
    try:
        print("    尝试方法 1: 自动设备映射...")
        model = AutoModel.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        print("    模型加载成功! (自动设备映射)")
    except Exception as e1:
        print(f"    方法 1 失败: {e1}")
        gc.collect()
        
        try:
            print("    尝试方法 2: GPU 优先...")
            model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="cuda:0",
                low_cpu_mem_usage=True
            )
            print("    模型加载成功! (GPU)")
        except Exception as e2:
            print(f"    方法 2 失败: {e2}")
            gc.collect()
            
            try:
                print("    尝试方法 3: CPU 模式...")
                model = AutoModel.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    device_map="cpu",
                    low_cpu_mem_usage=True
                )
                print("    模型加载成功! (CPU)")
            except Exception as e3:
                print(f"    方法 3 失败: {e3}")
                print("[错误] 所有加载方法都失败了")
                return False
    
    if model is None:
        print("[错误] 模型加载失败")
        return False
    
    print("\n[5] 获取模型参数量...")
    try:
        total_params, trainable_params = count_parameters(model)
        print(f"    总参数量: {format_params(total_params)} ({total_params:,})")
        print(f"    可训练参数: {format_params(trainable_params)} ({trainable_params:,})")
    except Exception as e:
        print(f"[警告] 无法获取参数量: {e}")
    
    print("\n[6] 模型设备信息...")
    try:
        if hasattr(model, 'hf_device_map'):
            print(f"    设备映射: {model.hf_device_map}")
        else:
            print("    设备映射: 未使用设备映射")
        
        first_param_device = next(model.parameters()).device
        print(f"    第一个参数设备: {first_param_device}")
    except Exception as e:
        print(f"[警告] 无法获取设备信息: {e}")
    
    print("\n[7] 尝试简单推理测试...")
    try:
        test_text = "你好"
        print(f"    输入文本: '{test_text}'")
        
        if hasattr(model, 'chat'):
            print("    检测到 chat 方法，使用对话模式...")
            response = model.chat(
                tokenizer,
                query=test_text,
                history=[]
            )
            response_str = str(response)
            print(f"    模型回复: {response_str[:300]}..." if len(response_str) > 300 else f"    模型回复: {response_str}")
        elif hasattr(model, 'generate'):
            print("    使用 generate 方法...")
            inputs = tokenizer(test_text, return_tensors="pt")
            inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=30)
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"    模型输出: {response[:300]}..." if len(response) > 300 else f"    模型输出: {response}")
        else:
            print("    [警告] 模型没有 chat 或 generate 方法")
            methods = [m for m in dir(model) if not m.startswith('_') and callable(getattr(model, m))]
            print(f"    可用方法 (前15个): {methods[:15]}")
    except Exception as e:
        print(f"[警告] 推理测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[8] 清理内存...")
    del model
    del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    
    print("\n" + "=" * 60)
    print("验证完成!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
