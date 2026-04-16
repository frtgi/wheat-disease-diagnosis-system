"""
Qwen3-VL 4bit量化部署环境检查脚本
检查GPU、CUDA、bitsandbytes等依赖
"""
import sys
import subprocess

def check_environment():
    """检查部署环境"""
    results = {}
    
    # 1. Python版本
    results["python_version"] = sys.version
    print(f"Python版本: {sys.version}")
    
    # 2. PyTorch检查
    try:
        import torch
        results["torch_version"] = torch.__version__
        results["cuda_available"] = torch.cuda.is_available()
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            results["cuda_version"] = torch.version.cuda
            results["gpu_name"] = torch.cuda.get_device_name(0)
            results["gpu_memory"] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU显存: {results['gpu_memory']:.2f} GB")
        else:
            print("警告: CUDA不可用，当前使用CPU版本PyTorch")
    except ImportError:
        results["torch"] = "未安装"
        print("PyTorch: 未安装")
    
    # 3. transformers检查
    try:
        import transformers
        results["transformers_version"] = transformers.__version__
        print(f"Transformers版本: {transformers.__version__}")
        
        # 检查Qwen3VL支持
        try:
            from transformers import Qwen3VLForConditionalGeneration
            results["qwen3vl_support"] = True
            print("Qwen3VLForConditionalGeneration: 支持")
        except ImportError:
            results["qwen3vl_support"] = False
            print("Qwen3VLForConditionalGeneration: 不支持")
    except ImportError:
        results["transformers"] = "未安装"
        print("Transformers: 未安装")
    
    # 4. bitsandbytes检查
    try:
        import bitsandbytes as bnb
        results["bitsandbytes_version"] = bnb.__version__
        results["bitsandbytes_cuda"] = bnb.is_cuda_available()
        print(f"BitsAndBytes版本: {bnb.__version__}")
        print(f"BitsAndBytes CUDA: {bnb.is_cuda_available()}")
    except ImportError:
        results["bitsandbytes"] = "未安装"
        print("BitsAndBytes: 未安装 (4bit量化必需)")
    
    # 5. accelerate检查
    try:
        import accelerate
        results["accelerate_version"] = accelerate.__version__
        print(f"Accelerate版本: {accelerate.__version__}")
    except ImportError:
        results["accelerate"] = "未安装"
        print("Accelerate: 未安装")
    
    # 6. 模型路径检查
    from pathlib import Path
    model_path = Path("D:/Project/WheatAgent/models/Qwen3-VL-4B-Instruct")
    results["model_path_exists"] = model_path.exists()
    results["model_path"] = str(model_path)
    print(f"模型路径存在: {model_path.exists()}")
    print(f"模型路径: {model_path}")
    
    return results

def analyze_deployment_issues(results):
    """分析部署问题"""
    print("\n" + "=" * 60)
    print("部署问题分析")
    print("=" * 60)
    
    issues = []
    
    # 检查CUDA
    if not results.get("cuda_available", False):
        issues.append({
            "issue": "CUDA不可用",
            "reason": "当前PyTorch是CPU版本，不支持GPU加速",
            "impact": "无法使用GPU进行模型推理，推理速度较慢",
            "solution": "安装CUDA版本的PyTorch"
        })
    
    # 检查bitsandbytes
    if results.get("bitsandbytes") == "未安装":
        issues.append({
            "issue": "BitsAndBytes未安装",
            "reason": "4bit量化需要bitsandbytes库",
            "impact": "无法进行INT4量化，模型显存占用大",
            "solution": "pip install bitsandbytes"
        })
    
    # 检查GPU显存
    gpu_memory = results.get("gpu_memory", 0)
    if gpu_memory > 0 and gpu_memory < 6:
        issues.append({
            "issue": "GPU显存不足",
            "reason": f"GPU显存仅{gpu_memory:.1f}GB，Qwen3-VL-4B需要约4-6GB",
            "impact": "可能无法加载完整模型",
            "solution": "使用INT4量化或CPU offload"
        })
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"\n问题 {i}: {issue['issue']}")
            print(f"  原因: {issue['reason']}")
            print(f"  影响: {issue['impact']}")
            print(f"  解决方案: {issue['solution']}")
    else:
        print("\n未发现明显部署问题")
    
    return issues

def suggest_alternatives(results, issues):
    """提供替代部署方案"""
    print("\n" + "=" * 60)
    print("替代部署方案")
    print("=" * 60)
    
    cuda_available = results.get("cuda_available", False)
    bitsandbytes_installed = results.get("bitsandbytes") != "未安装"
    
    # 方案1: 安装CUDA版PyTorch + bitsandbytes
    print("\n【方案一】安装CUDA版PyTorch + BitsAndBytes")
    print("-" * 40)
    print("适用场景: 有NVIDIA GPU，需要GPU加速推理")
    print("\n实施步骤:")
    print("1. 卸载当前CPU版PyTorch:")
    print("   pip uninstall torch torchvision torchaudio")
    print("\n2. 安装CUDA版PyTorch (CUDA 12.1):")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    print("\n3. 安装bitsandbytes:")
    print("   pip install bitsandbytes")
    print("\n预期效果:")
    print("- GPU推理速度提升10-50倍")
    print("- INT4量化后显存占用约2.6GB")
    print("- 支持并发推理")
    print("\n资源需求:")
    print("- NVIDIA GPU (建议GTX 1060 6GB以上)")
    print("- CUDA 12.1支持")
    print("- 系统内存8GB以上")
    
    # 方案2: 使用ONNX Runtime
    print("\n【方案二】ONNX Runtime CPU优化部署")
    print("-" * 40)
    print("适用场景: 无GPU或GPU不可用，需要CPU优化推理")
    print("\n实施步骤:")
    print("1. 安装ONNX Runtime:")
    print("   pip install onnxruntime-optimum")
    print("\n2. 导出模型为ONNX格式:")
    print("   python -c \"from optimum.exporters.onnx import main; main()\"")
    print("\n3. 使用ONNX Runtime推理:")
    print("   from optimum.onnxruntime import ORTModelForCausalLM")
    print("   model = ORTModelForCausalLM.from_pretrained(model_path)")
    print("\n预期效果:")
    print("- CPU推理速度提升2-5倍")
    print("- 内存占用降低20-30%")
    print("- 跨平台兼容性好")
    print("\n资源需求:")
    print("- CPU支持AVX2指令集")
    print("- 系统内存16GB以上")
    
    # 方案3: vLLM推理引擎
    print("\n【方案三】vLLM高性能推理引擎")
    print("-" * 40)
    print("适用场景: 需要高吞吐量、低延迟的生产环境")
    print("\n实施步骤:")
    print("1. 安装vLLM:")
    print("   pip install vllm")
    print("\n2. 启动vLLM服务:")
    print("   python -m vllm.entrypoints.api_server \\")
    print("       --model D:/Project/WheatAgent/models/Qwen3-VL-4B-Instruct \\")
    print("       --quantization awq \\")
    print("       --port 8001")
    print("\n3. 调用API:")
    print("   curl http://localhost:8001/generate -d '{\"prompt\": \"...\"}'")
    print("\n预期效果:")
    print("- 推理吞吐量提升5-10倍")
    print("- 支持PagedAttention，显存利用率高")
    print("- 支持连续批处理")
    print("\n资源需求:")
    print("- NVIDIA GPU (建议RTX 3060 12GB以上)")
    print("- CUDA 12.0+")
    print("- 系统内存16GB以上")
    
    # 方案4: llama.cpp GGUF量化
    print("\n【方案四】llama.cpp GGUF量化部署")
    print("-" * 40)
    print("适用场景: 边缘设备、低资源环境")
    print("\n实施步骤:")
    print("1. 安装llama-cpp-python:")
    print("   pip install llama-cpp-python")
    print("\n2. 转换模型为GGUF格式:")
    print("   python convert-hf-to-gguf.py D:/Project/WheatAgent/models/Qwen3-VL-4B-Instruct")
    print("\n3. 加载GGUF模型:")
    print("   from llama_cpp import Llama")
    print("   llm = Llama(model_path='model.gguf', n_gpu_layers=35)")
    print("\n预期效果:")
    print("- 支持4bit/5bit/8bit量化")
    print("- 可在CPU上高效运行")
    print("- 内存占用最低可至2GB")
    print("\n资源需求:")
    print("- CPU支持AVX2")
    print("- 系统内存4-8GB")
    print("- 可选GPU加速")

if __name__ == "__main__":
    results = check_environment()
    issues = analyze_deployment_issues(results)
    suggest_alternatives(results, issues)
