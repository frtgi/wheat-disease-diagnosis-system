# -*- coding: utf-8 -*-
"""
认知模块验证脚本

验证Qwen3.5-4B认知引擎的完整功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("认知模块导入测试")
    print("=" * 60)
    
    results = []
    
    try:
        from src.cognition import QwenEngine, QwenConfig, create_qwen_engine
        print("[OK] QwenEngine 导入成功")
        results.append(("QwenEngine", True))
    except Exception as e:
        print(f"[ERROR] QwenEngine 导入失败: {e}")
        results.append(("QwenEngine", False))
    
    try:
        from src.cognition import CognitionEngine
        print("[OK] CognitionEngine 导入成功")
        results.append(("CognitionEngine", True))
    except Exception as e:
        print(f"[ERROR] CognitionEngine 导入失败: {e}")
        results.append(("CognitionEngine", False))
    
    try:
        from src.cognition import prompt_templates
        print("[OK] prompt_templates 导入成功")
        results.append(("prompt_templates", True))
    except Exception as e:
        print(f"[ERROR] prompt_templates 导入失败: {e}")
        results.append(("prompt_templates", False))
    
    return results


def test_environment():
    """测试环境配置"""
    print("\n" + "=" * 60)
    print("环境配置检查")
    print("=" * 60)
    
    import transformers
    print(f"[INFO] transformers 版本: {transformers.__version__}")
    
    import torch
    print(f"[INFO] PyTorch 版本: {torch.__version__}")
    print(f"[INFO] CUDA 可用: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
        total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[INFO] 显存: {total_mem:.1f} GB")
    
    try:
        import bitsandbytes
        print(f"[INFO] bitsandbytes 版本: {bitsandbytes.__version__}")
    except ImportError:
        print("[WARN] bitsandbytes 未安装，4bit量化不可用")
    
    try:
        import accelerate
        print(f"[INFO] accelerate 版本: {accelerate.__version__}")
    except ImportError:
        print("[WARN] accelerate 未安装")


def test_model_files():
    """测试模型文件"""
    print("\n" + "=" * 60)
    print("模型文件检查")
    print("=" * 60)
    
    from pathlib import Path
    
    model_path = Path("D:/Project/WheatAgent/models/Qwen/Qwen3.5-4B")
    
    if not model_path.exists():
        print(f"[ERROR] 模型目录不存在: {model_path}")
        return False
    
    required_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors.index.json"
    ]
    
    all_exist = True
    for f in required_files:
        file_path = model_path / f
        if file_path.exists():
            print(f"[OK] {f}")
        else:
            print(f"[ERROR] {f} 不存在")
            all_exist = False
    
    safetensors_files = list(model_path.glob("model.safetensors-*.safetensors"))
    if safetensors_files:
        total_size = sum(f.stat().st_size for f in safetensors_files) / (1024**3)
        print(f"[OK] 模型文件: {len(safetensors_files)} 个, 总大小: {total_size:.2f} GB")
    else:
        print("[ERROR] 未找到模型权重文件")
        all_exist = False
    
    return all_exist


def test_engine_init():
    """测试引擎初始化（不加载模型）"""
    print("\n" + "=" * 60)
    print("引擎配置测试")
    print("=" * 60)
    
    try:
        from src.cognition.qwen_engine import QwenConfig
        
        config = QwenConfig()
        print(f"[OK] QwenConfig 创建成功")
        print(f"  - model_id: {config.model_id}")
        print(f"  - load_in_4bit: {config.load_in_4bit}")
        print(f"  - max_new_tokens: {config.max_new_tokens}")
        print(f"  - temperature: {config.temperature}")
        
        return True
    except Exception as e:
        print(f"[ERROR] 配置测试失败: {e}")
        return False


def test_engine_load():
    """测试引擎加载"""
    print("\n" + "=" * 60)
    print("引擎加载测试")
    print("=" * 60)
    
    try:
        from src.cognition import create_qwen_engine
        import torch
        
        print("[INFO] 正在加载Qwen3.5-4B引擎...")
        
        engine = create_qwen_engine(
            load_in_4bit=True,
            offline_mode=True
        )
        
        print("[OK] 引擎加载成功")
        
        memory = engine.get_memory_usage()
        print(f"[INFO] 显存使用: {memory}")
        
        return engine
    except Exception as e:
        print(f"[ERROR] 引擎加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_generation(engine):
    """测试文本生成"""
    print("\n" + "=" * 60)
    print("文本生成测试")
    print("=" * 60)
    
    if engine is None:
        print("[SKIP] 引擎未加载，跳过测试")
        return False
    
    try:
        print("[INFO] 测试: 小麦条锈病的主要症状是什么？")
        response = engine.generate("小麦条锈病的主要症状是什么？", max_new_tokens=100)
        print(f"[OK] 生成成功")
        print(f"回复: {response[:200]}...")
        return True
    except Exception as e:
        print(f"[ERROR] 生成测试失败: {e}")
        return False


def test_diagnosis(engine):
    """测试诊断功能"""
    print("\n" + "=" * 60)
    print("诊断功能测试")
    print("=" * 60)
    
    if engine is None:
        print("[SKIP] 引擎未加载，跳过测试")
        return False
    
    try:
        print("[INFO] 测试: 条锈病诊断")
        result = engine.diagnose("条锈病", symptoms=["黄色条纹", "叶片褪绿"])
        print(f"[OK] 诊断成功")
        print(f"置信度: {result['confidence']}")
        print(f"诊断结果: {result['diagnosis'][:200]}...")
        return True
    except Exception as e:
        print(f"[ERROR] 诊断测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Qwen3.5-4B 认知模块完整验证")
    print("=" * 60)
    
    results = {}
    
    results["imports"] = test_imports()
    results["environment"] = test_environment()
    results["model_files"] = test_model_files()
    results["config"] = test_engine_init()
    
    engine = test_engine_load()
    results["engine_load"] = engine is not None
    
    if engine:
        results["generation"] = test_generation(engine)
        results["diagnosis"] = test_diagnosis(engine)
    
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    total = 0
    passed = 0
    
    for key, value in results.items():
        if isinstance(value, bool):
            status = "PASS" if value else "FAIL"
            total += 1
            if value:
                passed += 1
        elif isinstance(value, list):
            passed_count = sum(1 for _, v in value if v)
            total_count = len(value)
            status = f"{passed_count}/{total_count}"
            total += total_count
            passed += passed_count
        
        print(f"  {key}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n[OK] 认知模块验证通过!")
    else:
        print(f"\n[WARN] 部分测试未通过 ({total - passed} 个失败)")
    
    return passed == total


if __name__ == "__main__":
    main()
