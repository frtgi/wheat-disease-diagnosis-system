# -*- coding: utf-8 -*-
"""
验证模型修复测试脚本

测试内容:
1. 视觉模型路径解析
2. Qwen3.5-4B模型加载
3. 模型推理功能
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

print("=" * 60)
print("IWDDA 模型修复验证测试")
print("=" * 60)

print("\n[1] 测试视觉模型路径解析...")
try:
    from src.vision.vision_engine import VisionAgent
    vision = VisionAgent(auto_warmup=False)
    print(f"   ✅ 视觉模型路径: {vision.model_path}")
    
    if "v10" in vision.model_path:
        print("   ✅ 正确加载v10模型 (mAP@50=95.39%)")
    elif "yolov8n" in vision.model_path:
        print("   ⚠️ 使用了备用模型 yolov8n.pt")
    else:
        print(f"   ℹ️ 使用模型: {vision.model_path}")
except Exception as e:
    print(f"   ❌ 视觉模型加载失败: {e}")

print("\n[2] 测试Qwen3.5-4B模型路径...")
local_model_path = project_root / "models" / "Qwen" / "Qwen3.5-4B"
print(f"   项目根目录: {project_root}")
print(f"   本地模型路径: {local_model_path}")
print(f"   模型存在: {local_model_path.exists()}")

config_file = local_model_path / "config.json"
if config_file.exists():
    import json
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"   配置文件存在: True")
    print(f"   模型类型: {config.get('model_type', 'unknown')}")
    print(f"   架构: {config.get('architectures', ['Unknown'])[0]}")
else:
    print(f"   配置文件存在: False")

print("\n[3] 测试Qwen引擎初始化...")
try:
    from src.cognition.qwen_engine import QwenEngine
    engine = QwenEngine(offline_mode=True, load_in_4bit=True)
    print("   ✅ Qwen引擎初始化成功!")
    
    print("\n[4] 测试文本生成...")
    response = engine.generate("小麦条锈病的主要症状是什么？", max_new_tokens=100)
    print(f"   回复: {response[:150]}...")
    
    print("\n[5] 测试显存使用...")
    memory = engine.get_memory_usage()
    print(f"   显存: {memory}")
    
except Exception as e:
    print(f"   ❌ Qwen引擎初始化失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
