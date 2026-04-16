# -*- coding: utf-8 -*-
"""
Qwen3.5-4B 认知模块验证脚本
"""
import os
import sys
import json
import time

print("=" * 60)
print("IWDDA 认知模块验证 - Qwen3.5-4B")
print("=" * 60)

results = {
    "model_files": {},
    "engine_module": {},
    "quantization": {},
    "agriculture_test": {},
    "memory_usage": {}
}

# 1. 检查模型文件
print("\n[1] 检查模型文件完整性...")
model_path = os.path.join(os.path.dirname(__file__), "models", "Qwen", "Qwen3.5-4B")
required_files = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "model.safetensors-00001-of-00002.safetensors",
    "model.safetensors-00002-of-00002.safetensors",
    "model.safetensors.index.json"
]

files_status = {}
all_exist = True
for f in required_files:
    file_path = os.path.join(model_path, f)
    exists = os.path.exists(file_path)
    files_status[f] = "OK" if exists else "MISSING"
    if not exists:
        all_exist = False
    print(f"  {f}: {files_status[f]}")

# 检查模型大小
if os.path.exists(model_path):
    total_size = 0
    for root, dirs, files in os.walk(model_path):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    print(f"  模型总大小: {total_size / (1024**3):.2f} GB")
    results["model_files"]["total_size_gb"] = round(total_size / (1024**3), 2)

results["model_files"]["status"] = "COMPLETE" if all_exist else "INCOMPLETE"
results["model_files"]["files"] = files_status

# 2. 检查引擎模块
print("\n[2] 检查引擎模块...")
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from src.cognition.qwen_engine import QwenEngine, QwenConfig, create_qwen_engine
    results["engine_module"]["status"] = "OK"
    results["engine_module"]["classes"] = ["QwenEngine", "QwenConfig", "create_qwen_engine"]
    print("  模块导入: OK")
    print("  类: QwenEngine, QwenConfig, create_qwen_engine")
except ImportError as e:
    results["engine_module"]["status"] = "ERROR"
    results["engine_module"]["error"] = str(e)
    print(f"  模块导入失败: {e}")

# 3. 检查PyTorch和CUDA
print("\n[3] 检查运行环境...")
try:
    import torch
    print(f"  PyTorch版本: {torch.__version__}")
    print(f"  CUDA可用: {torch.cuda.is_available()}")
    results["quantization"]["pytorch_version"] = torch.__version__
    results["quantization"]["cuda_available"] = torch.cuda.is_available()
    
    if torch.cuda.is_available():
        print(f"  GPU设备: {torch.cuda.get_device_name(0)}")
        total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"  显存总量: {total_mem:.1f} GB")
        results["quantization"]["gpu_name"] = torch.cuda.get_device_name(0)
        results["quantization"]["total_vram_gb"] = round(total_mem, 1)
        
        # 检查bitsandbytes
        try:
            import bitsandbytes as bnb
            print(f"  bitsandbytes: {bnb.__version__}")
            results["quantization"]["bitsandbytes"] = bnb.__version__
        except ImportError:
            print("  bitsandbytes: 未安装")
            results["quantization"]["bitsandbytes"] = "NOT_INSTALLED"
        
        # 检查transformers
        try:
            import transformers
            print(f"  transformers: {transformers.__version__}")
            results["quantization"]["transformers"] = transformers.__version__
        except ImportError:
            print("  transformers: 未安装")
            results["quantization"]["transformers"] = "NOT_INSTALLED"
            
except ImportError as e:
    print(f"  PyTorch导入失败: {e}")
    results["quantization"]["error"] = str(e)

# 4. 测试模型加载和农业提示词
print("\n[4] 测试4bit量化模型加载...")
try:
    import torch
    if torch.cuda.is_available():
        from src.cognition.qwen_engine import create_qwen_engine
        
        start_time = time.time()
        engine = create_qwen_engine(
            load_in_4bit=True,
            offline_mode=True
        )
        load_time = time.time() - start_time
        print(f"  模型加载时间: {load_time:.2f}秒")
        results["quantization"]["load_time_seconds"] = round(load_time, 2)
        results["quantization"]["4bit_enabled"] = True
        
        # 获取显存使用
        memory = engine.get_memory_usage()
        print(f"  显存已分配: {memory.get('allocated_gb', 0):.2f} GB")
        print(f"  显存已预留: {memory.get('reserved_gb', 0):.2f} GB")
        results["memory_usage"] = memory
        
        # 5. 测试农业提示词
        print("\n[5] 测试农业领域提示词响应...")
        test_prompts = [
            "小麦条锈病的主要症状是什么？",
            "如何防治小麦白粉病？"
        ]
        
        responses = []
        for prompt in test_prompts:
            print(f"\n  提问: {prompt}")
            response = engine.generate(prompt, max_new_tokens=200)
            print(f"  回复: {response[:150]}...")
            responses.append({"prompt": prompt, "response": response[:200]})
        
        results["agriculture_test"]["status"] = "OK"
        results["agriculture_test"]["responses"] = responses
    else:
        print("  CUDA不可用，跳过模型加载测试")
        results["quantization"]["4bit_enabled"] = False
        results["agriculture_test"]["status"] = "SKIPPED"
        results["agriculture_test"]["reason"] = "CUDA不可用"
except Exception as e:
    print(f"  模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    results["quantization"]["error"] = str(e)
    results["agriculture_test"]["status"] = "ERROR"
    results["agriculture_test"]["error"] = str(e)

# 输出结果摘要
print("\n" + "=" * 60)
print("验证结果摘要")
print("=" * 60)
print(f"模型文件: {results['model_files']['status']}")
print(f"引擎模块: {results['engine_module']['status']}")
print(f"4bit量化: {results['quantization'].get('4bit_enabled', 'N/A')}")
print(f"农业测试: {results['agriculture_test']['status']}")
if results.get("memory_usage"):
    print(f"显存占用: {results['memory_usage'].get('allocated_gb', 0):.2f} GB / {results['memory_usage'].get('total_gb', 0):.1f} GB")

# 保存结果
result_file = os.path.join(os.path.dirname(__file__), "qwen_validation_result.json")
with open(result_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n详细结果已保存到: {result_file}")
