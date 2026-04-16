"""
MiniCPM-V 4.5 模型加载测试脚本

测试使用 transformers 加载 MiniCPM-V 4.5 多模态模型
"""
import sys
import os
import time
from pathlib import Path


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


def test_model_loading():
    """
    测试 MiniCPM-V 4.5 模型加载
    
    尝试使用 transformers 的 AutoModel 和 AutoTokenizer 加载模型
    """
    print("=" * 60)
    print("MiniCPM-V 4.5 模型加载测试")
    print("=" * 60)
    
    model_path = r"D:\Project\WheatAgent\models\OpenBMB\MiniCPM-V-4_5"
    
    if not os.path.exists(model_path):
        print(f"[错误] 模型路径不存在: {model_path}")
        return False
    
    print(f"\n[1] 模型路径: {model_path}")
    print(f"[2] 检查模型文件...")
    
    required_files = ["config.json", "model.safetensors.index.json"]
    model_files = list(Path(model_path).glob("*"))
    print(f"    模型目录文件数: {len(model_files)}")
    
    for f in required_files:
        if (Path(model_path) / f).exists():
            print(f"    ✓ {f} 存在")
        else:
            print(f"    ✗ {f} 不存在")
    
    print(f"\n[3] Python 版本: {sys.version}")
    print(f"[4] 工作目录: {os.getcwd()}")
    
    print("\n[5] 导入 transformers...")
    try:
        import transformers
        print(f"    transformers 版本: {transformers.__version__}")
    except ImportError as e:
        print(f"    [错误] transformers 导入失败: {e}")
        return False
    
    print("\n[6] 导入 torch...")
    try:
        import torch
        print(f"    torch 版本: {torch.__version__}")
        print(f"    CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"    GPU 设备: {torch.cuda.get_device_name(0)}")
            print(f"    GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    except ImportError as e:
        print(f"    [错误] torch 导入失败: {e}")
        return False
    
    print("\n[7] 加载模型 (CPU 模式)...")
    print("    使用 trust_remote_code=True")
    
    try:
        from transformers import AutoModel, AutoTokenizer
        
        start_time = time.time()
        
        print("\n    加载 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print(f"    ✓ Tokenizer 加载成功")
        print(f"    Tokenizer 类型: {type(tokenizer).__name__}")
        
        print("\n    加载 Model (这可能需要几分钟)...")
        model = AutoModel.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        
        load_time = time.time() - start_time
        print(f"    ✓ Model 加载成功")
        print(f"    加载耗时: {load_time:.2f} 秒")
        print(f"    Model 类型: {type(model).__name__}")
        
        print("\n[8] 模型参数信息...")
        total_params, trainable_params = count_parameters(model)
        print(f"    总参数量: {format_params(total_params)} ({total_params:,})")
        print(f"    可训练参数: {format_params(trainable_params)} ({trainable_params:,})")
        
        print("\n[9] 模型配置信息...")
        if hasattr(model, 'config'):
            config = model.config
            print(f"    配置类型: {type(config).__name__}")
            if hasattr(config, 'hidden_size'):
                print(f"    隐藏层大小: {config.hidden_size}")
            if hasattr(config, 'num_hidden_layers'):
                print(f"    层数: {config.num_hidden_layers}")
            if hasattr(config, 'vocab_size'):
                print(f"    词表大小: {config.vocab_size}")
        
        print("\n[10] 测试简单推理...")
        try:
            test_text = "你好"
            print(f"    输入文本: '{test_text}'")
            
            if hasattr(tokenizer, 'encode'):
                inputs = tokenizer(test_text, return_tensors="pt")
                print(f"    编码成功, input_ids shape: {inputs['input_ids'].shape}")
            else:
                print("    Tokenizer 没有 encode 方法")
        except Exception as e:
            print(f"    [警告] 推理测试失败: {e}")
        
        print("\n" + "=" * 60)
        print("测试结果: 成功 ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[错误] 模型加载失败!")
        print(f"    错误类型: {type(e).__name__}")
        print(f"    错误信息: {str(e)}")
        
        import traceback
        print("\n完整错误堆栈:")
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("测试结果: 失败 ✗")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_model_loading()
    sys.exit(0 if success else 1)
