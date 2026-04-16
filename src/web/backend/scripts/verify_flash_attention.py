"""
验证 Flash Attention 2 安装和配置

该脚本用于验证 Flash Attention 2 是否正确安装并可用。
"""
import sys


def verify_flash_attention() -> bool:
    """
    验证 Flash Attention 2 是否正确安装
    
    返回:
        bool: Flash Attention 2 是否可用
    """
    print("=" * 60)
    print("Flash Attention 2 验证脚本")
    print("=" * 60)
    
    print("\n[1] 检查 flash-attn 包安装状态...")
    try:
        import flash_attn
        flash_attn_version = getattr(flash_attn, '__version__', 'unknown')
        print(f"    ✅ flash-attn 版本: {flash_attn_version}")
    except ImportError as e:
        print(f"    ❌ flash-attn 未安装: {e}")
        return False
    
    print("\n[2] 检查 PyTorch 和 CUDA 环境...")
    try:
        import torch
        print(f"    PyTorch 版本: {torch.__version__}")
        print(f"    CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"    CUDA 版本: {torch.version.cuda}")
            print(f"    GPU 设备: {torch.cuda.get_device_name(0)}")
            major, minor = torch.cuda.get_device_capability()
            print(f"    GPU 计算能力: {major}.{minor}")
            if major < 8:
                print(f"    ⚠️ Flash Attention 2 推荐 Ampere 架构 (SM 8.0+)，当前 SM {major}.{minor}")
            else:
                print(f"    ✅ GPU 架构支持 Flash Attention 2")
    except ImportError as e:
        print(f"    ❌ PyTorch 未安装: {e}")
        return False
    
    print("\n[3] 检查 Flash Attention 2 核心功能...")
    try:
        from flash_attn import flash_attn_func, flash_attn_qkvpacked_func, flash_attn_kvpacked_func
        print("    ✅ Flash Attention 核心函数可用")
    except ImportError as e:
        print(f"    ❌ Flash Attention 核心函数不可用: {e}")
        return False
    
    print("\n[4] 检查 Flash Attention CUDA 内核...")
    try:
        import flash_attn
        if hasattr(flash_attn, 'flash_attn_cuda'):
            print("    ✅ Flash Attention CUDA 内核已加载")
        else:
            print("    ⚠️ Flash Attention CUDA 内核未找到（可能是 CPU 回退模式）")
    except Exception as e:
        print(f"    ⚠️ 检查 CUDA 内核时出错: {e}")
    
    print("\n[5] 测试 Flash Attention 推理...")
    try:
        import torch
        from flash_attn import flash_attn_func
        
        batch_size = 2
        seq_len = 128
        num_heads = 8
        head_dim = 64
        
        q = torch.randn(batch_size, seq_len, num_heads, head_dim, dtype=torch.float16, device='cuda')
        k = torch.randn(batch_size, seq_len, num_heads, head_dim, dtype=torch.float16, device='cuda')
        v = torch.randn(batch_size, seq_len, num_heads, head_dim, dtype=torch.float16, device='cuda')
        
        output = flash_attn_func(q, k, v, softmax_scale=1.0 / (head_dim ** 0.5))
        print(f"    ✅ Flash Attention 推理测试成功")
        print(f"    输出形状: {output.shape}")
        
        del q, k, v, output
        torch.cuda.empty_cache()
        
    except Exception as e:
        print(f"    ❌ Flash Attention 推理测试失败: {e}")
        print("    注意: 这可能是因为安装的是 CPU 回退版本")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Flash Attention 2 验证完成 - 所有检查通过!")
    print("=" * 60)
    return True


def check_transformers_compatibility():
    """
    检查 transformers 库与 Flash Attention 的兼容性
    """
    print("\n[6] 检查 transformers 兼容性...")
    try:
        import transformers
        print(f"    transformers 版本: {transformers.__version__}")
        
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained("Qwen/Qwen2.5-0.5B")
        if hasattr(config, 'attn_implementation'):
            print("    ✅ transformers 支持 attn_implementation 参数")
        else:
            print("    ⚠️ transformers 可能不支持 attn_implementation 参数")
    except Exception as e:
        print(f"    ⚠️ 检查 transformers 兼容性时出错: {e}")


if __name__ == "__main__":
    success = verify_flash_attention()
    if success:
        check_transformers_compatibility()
    else:
        print("\n" + "=" * 60)
        print("❌ Flash Attention 2 验证失败")
        print("=" * 60)
        print("\n可能的原因:")
        print("1. flash-attn 未正确安装")
        print("2. CUDA 版本不兼容")
        print("3. GPU 架构不支持")
        print("\n建议:")
        print("- 确保已安装 CUDA Toolkit (nvcc 可用)")
        print("- 使用 pip install flash-attn --no-build-isolation 重新安装")
        sys.exit(1)
