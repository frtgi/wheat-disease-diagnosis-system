"""
MiniCPM-V 4.5 模型加载验证脚本 (低内存模式)

使用 float16 和低内存优化加载模型
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
    print("MiniCPM-V 4.5 模型加载验证 (低内存模式)")
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
        
        from transformers import AutoModel, AutoTokenizer
        print("    Transformers 导入成功")
    except ImportError as e:
        print(f"[错误] 依赖导入失败: {e}")
        return False
    
    print("\n[3] 检查模型文件...")
    try:
        model_files = os.listdir(model_path)
        print(f"    模型目录文件数: {len(model_files)}")
        
        safetensors_files = [f for f in model_files if f.endswith('.safetensors')]
        bin_files = [f for f in model_files if f.endswith('.bin')]
        print(f"    Safetensors 文件: {len(safetensors_files)}")
        print(f"    Bin 文件: {len(bin_files)}")
        
        config_file = [f for f in model_files if 'config.json' in f]
        print(f"    配置文件: {config_file}")
    except Exception as e:
        print(f"[警告] 无法列出模型文件: {e}")
    
    print("\n[4] 加载 Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print(f"    Tokenizer 加载成功")
        print(f"    词表大小: {len(tokenizer)}")
    except Exception as e:
        print(f"[错误] Tokenizer 加载失败: {e}")
        return False
    
    print("\n[5] 加载模型配置...")
    try:
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print(f"    配置类型: {type(config).__name__}")
        if hasattr(config, 'model_type'):
            print(f"    模型类型: {config.model_type}")
        if hasattr(config, 'hidden_size'):
            print(f"    隐藏层大小: {config.hidden_size}")
        if hasattr(config, 'num_hidden_layers'):
            print(f"    层数: {config.num_hidden_layers}")
        
        del config
        gc.collect()
    except Exception as e:
        print(f"[警告] 无法加载配置: {e}")
    
    print("\n[6] 加载模型 (CPU 模式, float16)...")
    print("    注意: 这可能需要几分钟时间和大量内存...")
    try:
        model = AutoModel.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        print("    模型加载成功!")
    except Exception as e:
        print(f"[错误] 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[7] 获取模型参数量...")
    try:
        total_params, trainable_params = count_parameters(model)
        print(f"    总参数量: {format_params(total_params)} ({total_params:,})")
        print(f"    可训练参数: {format_params(trainable_params)} ({trainable_params:,})")
    except Exception as e:
        print(f"[警告] 无法获取参数量: {e}")
    
    print("\n[8] 模型基本信息...")
    try:
        print(f"    模型类型: {type(model).__name__}")
        if hasattr(model, 'config'):
            config = model.config
            print(f"    配置类型: {type(config).__name__}")
            if hasattr(config, 'model_type'):
                print(f"    模型类型标识: {config.model_type}")
    except Exception as e:
        print(f"[警告] 无法获取模型信息: {e}")
    
    print("\n[9] 尝试简单推理测试...")
    try:
        test_text = "你好"
        print(f"    输入文本: {test_text}")
        
        if hasattr(model, 'chat'):
            print("    检测到 chat 方法，使用对话模式...")
            response = model.chat(
                tokenizer,
                query=test_text,
                history=[]
            )
            response_str = str(response)
            print(f"    模型回复: {response_str[:200]}..." if len(response_str) > 200 else f"    模型回复: {response_str}")
        elif hasattr(model, 'generate'):
            print("    使用 generate 方法...")
            inputs = tokenizer(test_text, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=30)
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"    模型输出: {response[:200]}..." if len(response) > 200 else f"    模型输出: {response}")
        else:
            print("    [警告] 模型没有 chat 或 generate 方法")
            methods = [m for m in dir(model) if not m.startswith('_') and callable(getattr(model, m))]
            print(f"    可用方法 (前15个): {methods[:15]}")
    except Exception as e:
        print(f"[警告] 推理测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[10] 清理内存...")
    del model
    del tokenizer
    gc.collect()
    
    print("\n" + "=" * 60)
    print("验证完成!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
