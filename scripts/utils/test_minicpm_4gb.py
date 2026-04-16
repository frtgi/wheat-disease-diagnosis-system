# -*- coding: utf-8 -*-
"""
MiniCPM-V 4.5 4GB显存测试脚本

测试项目:
1. 模型加载 (4bit量化)
2. 显存占用监控
3. 推理性能测试
4. 认知能力验证

适用于 4GB 显存环境 (如 RTX 3050 Laptop GPU)
"""
import os
import sys
import time
import platform
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


def check_gpu_memory():
    """
    检查GPU显存状态
    
    :return: 显存信息字典
    """
    try:
        import torch
        if torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            free = total - reserved
            
            return {
                "total_gb": round(total, 2),
                "reserved_gb": round(reserved, 2),
                "allocated_gb": round(allocated, 2),
                "free_gb": round(free, 2),
                "device_name": torch.cuda.get_device_name(0)
            }
    except Exception as e:
        print(f"[错误] GPU检测失败: {e}")
    return None


def test_model_loading():
    """
    测试模型加载
    
    :return: 加载是否成功
    """
    print("\n" + "=" * 60)
    print("[测试1] 模型加载测试 (4bit量化)")
    print("=" * 60)
    
    mem_before = check_gpu_memory()
    if mem_before:
        print(f"  加载前显存: {mem_before['free_gb']:.2f} GB / {mem_before['total_gb']:.2f} GB")
    
    try:
        from src.cognition import create_minicpm_engine
        
        print("\n[加载] 正在加载 MiniCPM-V 4.5 (4bit量化)...")
        start_time = time.time()
        
        engine = create_minicpm_engine(
            model_id="OpenBMB/MiniCPM-V-4_5",
            load_in_4bit=True,
            offline_mode=True,
            enable_thinking=False
        )
        
        load_time = time.time() - start_time
        print(f"[OK] 模型加载成功，耗时: {load_time:.2f}秒")
        
        mem_after = check_gpu_memory()
        if mem_after:
            print(f"  加载后显存: {mem_after['free_gb']:.2f} GB / {mem_after['total_gb']:.2f} GB")
            print(f"  显存占用: {mem_after['reserved_gb']:.2f} GB")
        
        return True, engine
        
    except Exception as e:
        print(f"[失败] 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_inference(engine):
    """
    测试推理性能
    
    :param engine: MiniCPM引擎实例
    :return: 推理是否成功
    """
    print("\n" + "=" * 60)
    print("[测试2] 推理性能测试")
    print("=" * 60)
    
    test_image_path = project_root / "datasets" / "wheat_data_unified" / "images" / "val"
    
    test_images = list(test_image_path.glob("*.jpg")) + list(test_image_path.glob("*.png"))
    
    if not test_images:
        print("[警告] 未找到测试图像，跳过推理测试")
        return False
    
    test_image = test_images[0]
    print(f"  测试图像: {test_image.name}")
    
    try:
        from PIL import Image
        image = Image.open(test_image).convert('RGB')
        
        question = "请分析这张小麦图像，识别可能的病害类型并给出诊断建议。"
        
        print(f"\n[推理] 正在分析图像...")
        start_time = time.time()
        
        result = engine.analyze_image(image, question)
        
        inference_time = time.time() - start_time
        
        print(f"[OK] 推理完成，耗时: {inference_time:.2f}秒")
        print(f"\n[结果预览]:")
        preview = result[:500] + "..." if len(result) > 500 else result
        print(preview)
        
        mem_after = check_gpu_memory()
        if mem_after:
            print(f"\n  推理后显存: {mem_after['free_gb']:.2f} GB / {mem_after['total_gb']:.2f} GB")
        
        return True
        
    except Exception as e:
        print(f"[失败] 推理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cognition_capability(engine):
    """
    测试认知能力
    
    :param engine: MiniCPM引擎实例
    :return: 测试是否成功
    """
    print("\n" + "=" * 60)
    print("[测试3] 认知能力验证")
    print("=" * 60)
    
    test_questions = [
        "小麦条锈病的典型症状是什么？",
        "如何区分小麦条锈病和叶锈病？",
        "小麦赤霉病的防治方法有哪些？"
    ]
    
    try:
        for i, question in enumerate(test_questions, 1):
            print(f"\n[问题{i}] {question}")
            
            messages = [{'role': 'user', 'content': question}]
            
            start_time = time.time()
            response = engine.chat(messages, stream=False)
            inference_time = time.time() - start_time
            
            preview = response[:200] + "..." if len(response) > 200 else response
            print(f"[回答] {preview}")
            print(f"[耗时] {inference_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"[失败] 认知能力测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_stability():
    """
    测试显存稳定性
    
    :return: 测试是否成功
    """
    print("\n" + "=" * 60)
    print("[测试4] 显存稳定性测试")
    print("=" * 60)
    
    try:
        import torch
        import gc
        
        mem_info = check_gpu_memory()
        if not mem_info:
            print("[跳过] 无可用GPU")
            return False
        
        print(f"  GPU: {mem_info['device_name']}")
        print(f"  总显存: {mem_info['total_gb']:.2f} GB")
        print(f"  可用显存: {mem_info['free_gb']:.2f} GB")
        
        if mem_info['total_gb'] < 4.0:
            print("[警告] 显存小于4GB，可能无法正常运行")
        elif mem_info['total_gb'] < 6.0:
            print("[提示] 4GB显存环境，建议使用4bit量化")
        else:
            print("[OK] 显存充足")
        
        torch.cuda.empty_cache()
        gc.collect()
        
        mem_after = check_gpu_memory()
        print(f"  清理后可用: {mem_after['free_gb']:.2f} GB")
        
        return True
        
    except Exception as e:
        print(f"[失败] 显存稳定性测试失败: {e}")
        return False


def main():
    """
    主测试函数
    """
    print("=" * 60)
    print("MiniCPM-V 4.5 4GB显存环境测试")
    print("=" * 60)
    print(f"  系统: {platform.system()} {platform.release()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  项目路径: {project_root}")
    
    results = {
        "显存稳定性": False,
        "模型加载": False,
        "推理性能": False,
        "认知能力": False
    }
    
    results["显存稳定性"] = test_memory_stability()
    
    load_success, engine = test_model_loading()
    results["模型加载"] = load_success
    
    if load_success and engine:
        results["推理性能"] = test_inference(engine)
        results["认知能力"] = test_cognition_capability(engine)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\n总计: {total_passed}/{total_tests} 测试通过")
    
    if total_passed == total_tests:
        print("\n[结论] MiniCPM-V 4.5 在4GB显存环境下运行正常！")
    else:
        print("\n[结论] 部分测试未通过，请检查配置。")
    
    return results


if __name__ == "__main__":
    main()
