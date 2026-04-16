# -*- coding: utf-8 -*-
"""
验证 LLaVA 微调环境

检查：
1. 图片路径是否正确
2. LLaVA 模型是否可用
3. 依赖是否完整
"""
import json
import os
import sys
from pathlib import Path

def verify_image_paths():
    """验证图片路径"""
    print("=" * 60)
    print("🔍 图片路径验证")
    print("=" * 60)
    
    project_root = Path("D:/Project/WheatAgent")
    
    train_json = project_root / "datasets/agroinstruct/agroinstruct_train.json"
    val_json = project_root / "datasets/agroinstruct/agroinstruct_val.json"
    
    def verify_json(json_path, name):
        if not json_path.exists():
            print(f"❌ {name} 不存在: {json_path}")
            return 0, 0, []
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        total = len(data)
        valid = 0
        missing = []
        
        for item in data:
            img_path = item.get("image_path", "")
            full_path = project_root / img_path
            if full_path.exists():
                valid += 1
            else:
                missing.append(img_path)
        
        print(f"\n📊 {name}:")
        print(f"   总条目: {total}")
        print(f"   有效路径: {valid}")
        print(f"   缺失图片: {len(missing)}")
        
        if missing and len(missing) <= 5:
            print(f"   缺失示例:")
            for m in missing[:5]:
                print(f"      - {m}")
        
        return total, valid, missing
    
    train_total, train_valid, train_missing = verify_json(train_json, "训练集")
    val_total, val_valid, val_missing = verify_json(val_json, "验证集")
    
    print("\n" + "=" * 60)
    print("📊 总结")
    print("=" * 60)
    print(f"训练集: {train_valid}/{train_total} 图片有效 ({100*train_valid/train_total:.1f}%)")
    print(f"验证集: {val_valid}/{val_total} 图片有效 ({100*val_valid/val_total:.1f}%)")
    
    if train_valid == train_total and val_valid == val_total:
        print("\n✅ 所有图片路径验证通过!")
        return True
    else:
        print(f"\n⚠️ 存在缺失图片: {len(train_missing) + len(val_missing)} 个")
        return False

def check_llava_model():
    """检查 LLaVA 模型状态"""
    print("\n" + "=" * 60)
    print("🔍 LLaVA 模型检查")
    print("=" * 60)
    
    model_id = "llava-hf/llava-1.5-7b-hf"
    
    cache_dir = os.environ.get("HF_HOME", None)
    if cache_dir is None:
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    
    model_cache_path = os.path.join(cache_dir, "hub", f"models--{model_id.replace('/', '--')}")
    
    print(f"模型ID: {model_id}")
    print(f"缓存目录: {cache_dir}")
    print(f"模型缓存路径: {model_cache_path}")
    
    if os.path.exists(model_cache_path):
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(model_cache_path):
            for f in files:
                file_path = os.path.join(root, f)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        size_mb = total_size / (1024 * 1024)
        size_gb = size_mb / 1024
        
        print(f"\n✅ 模型已缓存")
        print(f"   文件数量: {file_count}")
        print(f"   缓存大小: {size_mb:.1f} MB ({size_gb:.2f} GB)")
        
        if size_gb < 10:
            print(f"\n⚠️ 缓存大小偏小，可能下载不完整 (LLaVA-1.5-7b 约 13-15 GB)")
            return False
        
        return True
    else:
        print(f"\n❌ 模型未缓存")
        print(f"   需要下载模型 (约 13-15 GB)")
        return False

def check_dependencies():
    """检查依赖"""
    print("\n" + "=" * 60)
    print("🔍 依赖检查")
    print("=" * 60)
    
    dependencies = {
        "torch": "PyTorch",
        "transformers": "Transformers",
        "peft": "PEFT",
        "accelerate": "Accelerate",
        "bitsandbytes": "BitsAndBytes",
        "PIL": "Pillow"
    }
    
    all_ok = True
    
    for module, name in dependencies.items():
        try:
            if module == "PIL":
                import PIL
                print(f"✅ {name}: {PIL.__version__}")
            else:
                imported = __import__(module)
                version = getattr(imported, "__version__", "未知")
                print(f"✅ {name}: {version}")
        except ImportError:
            print(f"❌ {name}: 未安装")
            all_ok = False
    
    if all_ok:
        print("\n✅ 所有依赖已安装")
    else:
        print("\n⚠️ 部分依赖缺失")
    
    return all_ok

def check_gpu():
    """检查 GPU"""
    print("\n" + "=" * 60)
    print("🔍 GPU 检查")
    print("=" * 60)
    
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA 可用")
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB")
            print(f"   CUDA 版本: {torch.version.cuda}")
            
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            if vram < 8:
                print(f"\n⚠️ 显存不足 ({vram:.1f} GB)，推荐 16GB+ 用于 LLaVA 微调")
                return False
            return True
        else:
            print("❌ CUDA 不可用")
            return False
    except Exception as e:
        print(f"❌ GPU 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🌾 LLaVA LoRA 微调环境验证")
    print("=" * 60)
    
    results = {
        "图片路径": verify_image_paths(),
        "LLaVA模型": check_llava_model(),
        "依赖": check_dependencies(),
        "GPU": check_gpu()
    }
    
    print("\n" + "=" * 60)
    print("📋 验证结果汇总")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 未通过"
        print(f"   {name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查通过，可以启动微调训练！")
        print("\n启动命令:")
        print("  python scripts/training/train_llava_lora.py")
    else:
        print("⚠️ 存在问题，请先解决上述问题")
        
        if not results["LLaVA模型"]:
            print("\n📥 下载 LLaVA 模型:")
            print("  python -c \"from transformers import LlavaForConditionalGeneration; LlavaForConditionalGeneration.from_pretrained('llava-hf/llava-1.5-7b-hf')\"")
        
        if not results["GPU"]:
            print("\n💡 显存不足建议:")
            print("  1. 使用云端 GPU 服务 (如 Colab Pro)")
            print("  2. 减少训练数据量")
            print("  3. 使用更小的模型")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()
