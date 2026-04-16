# -*- coding: utf-8 -*-
"""
Qwen3-VL-4B-Instruct 单元测试

测试新模型的各项功能：
1. 模型加载
2. 纯文本生成
3. 图像 + 文本联合输入
4. 病害诊断
"""
import os
import sys
from pathlib import Path
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

# 设置工作目录
os.chdir(project_root)

import torch
from PIL import Image


def test_model_loading():
    """
    测试 1: 模型加载
    """
    print("\n" + "=" * 60)
    print("测试 1: 模型加载")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        from src.cognition.qwen_engine import create_qwen_engine
        
        print("正在加载 Qwen3-VL-4B-Instruct 模型...")
        engine = create_qwen_engine(
            load_in_4bit=True,
            offline_mode=True
        )
        
        load_time = time.time() - start_time
        print(f"✅ 模型加载成功！用时：{load_time:.2f}秒")
        
        # 检查显存占用
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            print(f"📊 显存占用：{allocated:.2f} GB")
            
            if allocated < 3.5:
                print("✅ 显存占用符合要求 (< 3.5GB)")
            else:
                print("⚠️ 显存占用超出预期")
        
        return engine
        
    except Exception as e:
        print(f"❌ 模型加载失败：{e}")
        import traceback
        traceback.print_exc()
        return None


def test_text_generation(engine):
    """
    测试 2: 纯文本生成
    """
    print("\n" + "=" * 60)
    print("测试 2: 纯文本生成")
    print("=" * 60)
    
    if engine is None:
        print("⚠️ 引擎未加载，跳过测试")
        return
    
    try:
        prompt = "小麦条锈病的主要症状是什么？"
        print(f"问题：{prompt}")
        
        start_time = time.time()
        response = engine.generate(prompt)
        infer_time = time.time() - start_time
        
        print(f"回复：{response[:200]}...")
        print(f"⏱️  推理时间：{infer_time:.2f}秒")
        print("✅ 纯文本生成测试通过")
        
    except Exception as e:
        print(f"❌ 纯文本生成失败：{e}")
        import traceback
        traceback.print_exc()


def test_multimodal_input(engine):
    """
    测试 3: 图像 + 文本联合输入
    """
    print("\n" + "=" * 60)
    print("测试 3: 图像 + 文本联合输入")
    print("=" * 60)
    
    if engine is None:
        print("⚠️ 引擎未加载，跳过测试")
        return
    
    # 创建测试图像（红色方块）
    try:
        test_image = Image.new('RGB', (224, 224), color='red')
        
        prompt = "请描述这张图像"
        print(f"输入：图像 + '{prompt}'")
        
        start_time = time.time()
        response = engine.generate(prompt, image=test_image)
        infer_time = time.time() - start_time
        
        print(f"回复：{response[:200]}...")
        print(f"⏱️  推理时间：{infer_time:.2f}秒")
        print("✅ 多模态输入测试通过")
        
    except Exception as e:
        print(f"❌ 多模态输入失败：{e}")
        import traceback
        traceback.print_exc()


def test_disease_diagnosis(engine):
    """
    测试 4: 病害诊断
    """
    print("\n" + "=" * 60)
    print("测试 4: 病害诊断")
    print("=" * 60)
    
    if engine is None:
        print("⚠️ 引擎未加载，跳过测试")
        return
    
    try:
        # 测试文本诊断
        print("\n[文本诊断测试]")
        result = engine.diagnose("条锈病", symptoms=["黄色条纹", "叶片褪绿"])
        print(f"诊断结果：{result.get('diagnosis', 'N/A')[:200]}...")
        print("✅ 文本诊断测试通过")
        
        # 测试图像诊断（使用测试图像）
        print("\n[图像诊断测试]")
        test_image = Image.new('RGB', (224, 224), color='green')
        result = engine.diagnose_with_image(
            disease_name="条锈病",
            image=test_image,
            symptoms=["黄色条纹"]
        )
        print(f"图像诊断：{result.get('diagnosis', 'N/A')[:200]}...")
        print("✅ 图像诊断测试通过")
        
    except Exception as e:
        print(f"❌ 病害诊断失败：{e}")
        import traceback
        traceback.print_exc()


def test_memory_usage():
    """
    测试 5: 显存使用测试
    """
    print("\n" + "=" * 60)
    print("测试 5: 显存使用测试")
    print("=" * 60)
    
    if not torch.cuda.is_available():
        print("⚠️ CUDA 不可用，跳过显存测试")
        return
    
    try:
        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"总显存：{total:.2f} GB")
        print(f"已分配：{allocated:.2f} GB")
        print(f"已预留：{reserved:.2f} GB")
        print(f"可用显存：{total - allocated:.2f} GB")
        
        if allocated < 3.5:
            print("✅ 显存使用符合要求")
        else:
            print("⚠️ 显存使用超出预期")
        
    except Exception as e:
        print(f"❌ 显存测试失败：{e}")


def main():
    """
    主测试函数
    """
    print("\n" + "=" * 60)
    print("Qwen3-VL-4B-Instruct 单元测试套件")
    print("=" * 60)
    
    # 测试 1: 模型加载
    engine = test_model_loading()
    
    # 测试 2: 纯文本生成
    test_text_generation(engine)
    
    # 测试 3: 多模态输入
    test_multimodal_input(engine)
    
    # 测试 4: 病害诊断
    test_disease_diagnosis(engine)
    
    # 测试 5: 显存使用
    test_memory_usage()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
