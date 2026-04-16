# -*- coding: utf-8 -*-
"""
Qwen3.5-4B 模型下载脚本

使用 ModelScope SDK 下载 Qwen3.5-4B 模型
"""
import os
import sys

def download_qwen():
    """下载Qwen3.5-4B模型"""
    print("=" * 60)
    print("Qwen3.5-4B 模型下载")
    print("=" * 60)
    
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("[错误] modelscope未安装，正在安装...")
        os.system("pip install modelscope")
        from modelscope import snapshot_download
    
    model_id = "Qwen/Qwen3.5-4B"
    local_dir = "D:/Project/WheatAgent/models/Qwen/Qwen3.5-4B"
    
    print(f"\n[下载] 模型: {model_id}")
    print(f"[目标] 路径: {local_dir}")
    print("\n开始下载...")
    
    try:
        snapshot_download(
            model_id=model_id,
            local_dir=local_dir
        )
        print("\n[OK] 下载完成!")
        
        # 验证文件
        import os
        required_files = [
            "config.json",
            "tokenizer.json",
            "model.safetensors.index.json"
        ]
        
        print("\n[验证] 检查必要文件...")
        for f in required_files:
            path = os.path.join(local_dir, f)
            if os.path.exists(path):
                size = os.path.getsize(path) / (1024 * 1024)
                print(f"  ✅ {f} ({size:.2f} MB)")
            else:
                print(f"  ❌ {f} 缺失")
        
        # 检查模型权重文件
        print("\n[验证] 检查模型权重...")
        index_file = os.path.join(local_dir, "model.safetensors.index.json")
        if os.path.exists(index_file):
            import json
            with open(index_file, 'r') as file:
                index = json.load(file)
            weight_files = set(index.get("weight_map", {}).values())
            print(f"  需要权重文件: {len(weight_files)} 个")
            for wf in sorted(weight_files):
                wf_path = os.path.join(local_dir, wf)
                if os.path.exists(wf_path):
                    size = os.path.getsize(wf_path) / (1024 * 1024 * 1024)
                    print(f"  ✅ {wf} ({size:.2f} GB)")
                else:
                    print(f"  ❌ {wf} 缺失")
        
        print("\n" + "=" * 60)
        print("[完成] Qwen3.5-4B 模型下载验证完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[错误] 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    download_qwen()
