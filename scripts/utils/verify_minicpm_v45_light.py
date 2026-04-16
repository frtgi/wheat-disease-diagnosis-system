"""
MiniCPM-V 4.5 模型验证脚本 (轻量模式)

仅验证模型配置和基本可用性，不完整加载模型
"""
import sys
import os

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

def estimate_model_size(model_path):
    """
    估算模型大小
    
    Args:
        model_path: 模型路径
        
    Returns:
        tuple: (总大小字节, 格式化大小字符串)
    """
    total_size = 0
    for root, dirs, files in os.walk(model_path):
        for f in files:
            if f.endswith(('.safetensors', '.bin', '.pt', '.pth')):
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
    
    if total_size >= 1e9:
        size_str = f"{total_size / 1e9:.2f} GB"
    elif total_size >= 1e6:
        size_str = f"{total_size / 1e6:.2f} MB"
    else:
        size_str = f"{total_size / 1e3:.2f} KB"
    
    return total_size, size_str

def main():
    print("=" * 60)
    print("MiniCPM-V 4.5 模型验证 (轻量模式)")
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
            print(f"    GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        
        from transformers import AutoTokenizer, AutoConfig
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
        for f in safetensors_files:
            size_mb = os.path.getsize(os.path.join(model_path, f)) / 1e6
            print(f"      - {f}: {size_mb:.1f} MB")
        
        print(f"    Bin 文件: {len(bin_files)}")
        
        config_files = [f for f in model_files if 'config' in f.lower() and f.endswith('.json')]
        print(f"    配置文件: {config_files}")
    except Exception as e:
        print(f"[警告] 无法列出模型文件: {e}")
    
    print("\n[4] 估算模型大小...")
    try:
        total_size, size_str = estimate_model_size(model_path)
        print(f"    模型文件总大小: {size_str}")
        
        estimated_params = total_size / 2  # float16 = 2 bytes per param
        print(f"    估算参数量 (float16): {format_params(estimated_params)}")
    except Exception as e:
        print(f"[警告] 无法估算模型大小: {e}")
    
    print("\n[5] 加载 Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print(f"    Tokenizer 加载成功 ✓")
        print(f"    词表大小: {len(tokenizer)}")
        print(f"    Tokenizer 类型: {type(tokenizer).__name__}")
        
        test_tokens = tokenizer.encode("你好，小麦病害诊断")
        print(f"    测试编码: '你好，小麦病害诊断' -> {test_tokens[:10]}...")
        test_decode = tokenizer.decode(test_tokens)
        print(f"    测试解码: '{test_decode}'")
    except Exception as e:
        print(f"[错误] Tokenizer 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[6] 加载模型配置...")
    try:
        config = AutoConfig.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print(f"    配置加载成功 ✓")
        print(f"    配置类型: {type(config).__name__}")
        
        if hasattr(config, 'model_type'):
            print(f"    模型类型: {config.model_type}")
        if hasattr(config, 'hidden_size'):
            print(f"    隐藏层大小: {config.hidden_size}")
        if hasattr(config, 'num_hidden_layers'):
            print(f"    LLM 层数: {config.num_hidden_layers}")
        if hasattr(config, 'vocab_size'):
            print(f"    词表大小: {config.vocab_size}")
        
        if hasattr(config, 'vision_config'):
            print(f"    视觉编码器配置:")
            vision_config = config.vision_config
            if hasattr(vision_config, 'hidden_size'):
                print(f"      隐藏层大小: {vision_config.hidden_size}")
            if hasattr(vision_config, 'num_hidden_layers'):
                print(f"      层数: {vision_config.num_hidden_layers}")
        
        if hasattr(config, 'query_num'):
            print(f"    Query 数量: {config.query_num}")
        if hasattr(config, 'slice_config'):
            print(f"    切片配置: {config.slice_config}")
            
    except Exception as e:
        print(f"[错误] 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[7] 检查模型代码...")
    try:
        modeling_files = [f for f in os.listdir(model_path) if f.startswith('modeling') and f.endswith('.py')]
        print(f"    模型代码文件: {modeling_files}")
        
        if modeling_files:
            for mf in modeling_files:
                fp = os.path.join(model_path, mf)
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                    classes = [line.split('class ')[1].split('(')[0] 
                              for line in content.split('\n') 
                              if line.strip().startswith('class ')]
                    print(f"    {mf} 包含类: {classes[:5]}...")
    except Exception as e:
        print(f"[警告] 无法检查模型代码: {e}")
    
    print("\n[8] 内存需求分析...")
    try:
        import psutil
        mem = psutil.virtual_memory()
        print(f"    系统总内存: {mem.total / 1e9:.1f} GB")
        print(f"    可用内存: {mem.available / 1e9:.1f} GB")
        print(f"    内存使用率: {mem.percent}%")
        
        if total_size > mem.available:
            print(f"    ⚠️ 警告: 模型大小 ({size_str}) 大于可用内存 ({mem.available / 1e9:.1f} GB)")
            print(f"    建议: 使用 GPU 加载或增加系统内存")
        else:
            print(f"    ✓ 理论上可以在 CPU 上加载")
    except ImportError:
        print("    [跳过] psutil 未安装，无法检查内存")
    
    print("\n[9] GPU 加载建议...")
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory
        print(f"    GPU 显存: {gpu_memory / 1e9:.1f} GB")
        if total_size < gpu_memory * 0.8:
            print(f"    ✓ 建议使用 GPU 加载 (模型可放入显存)")
        else:
            print(f"    ⚠️ GPU 显存可能不足，建议使用 4-bit/8-bit 量化")
    else:
        print(f"    ⚠️ CUDA 不可用，只能使用 CPU 加载")
        print(f"    ⚠️ CPU 加载大型模型可能需要大量系统内存")
    
    print("\n" + "=" * 60)
    print("验证结果摘要")
    print("=" * 60)
    print("✓ 模型路径存在")
    print("✓ Tokenizer 加载成功")
    print("✓ 模型配置加载成功")
    print(f"✓ 模型类型: {config.model_type if hasattr(config, 'model_type') else '未知'}")
    print(f"✓ 模型大小: {size_str}")
    print(f"✓ 估算参数量: {format_params(estimated_params)}")
    print()
    print("注意: 由于模型较大，完整加载需要:")
    print("  - GPU 模式: 足够的显存 (推荐)")
    print("  - CPU 模式: 大量系统内存 (可能较慢)")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
