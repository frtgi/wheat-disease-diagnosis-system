# 文件路径: WheatAgent/src/deploy/export.py
import os
import sys
import glob
from ultralytics import YOLO

def export_model():
    print("📦 [Deploy] 开始模型轻量化导出流程...")
    
    # 1. 自动寻找最佳模型
    search_pattern = os.path.join(os.getcwd(), "runs", "**", "wheat_evolution", "weights", "best.pt")
    models = glob.glob(search_pattern, recursive=True)
    
    if not models:
        # 降级搜索
        search_pattern = os.path.join(os.getcwd(), "runs", "**", "weights", "best.pt")
        models = glob.glob(search_pattern, recursive=True)
        
    if not models:
        print("❌ 未找到训练好的模型 (best.pt)")
        return

    model_path = max(models, key=os.path.getmtime)
    print(f"🎯 选中模型: {model_path}")
    
    try:
        # 2. 加载模型
        model = YOLO(model_path)
        
        # 3. 导出为 ONNX (通用格式)
        # opset=12 兼容性好，dynamic=False 适合 TensorRT 优化
        print("🔄 正在导出为 ONNX 格式...")
        onnx_path = model.export(format='onnx', opset=12, simplify=True)
        
        print(f"\n✅ 导出成功! 文件路径: {onnx_path}")
        print("💡 部署提示:")
        print("   - Web端: 可使用 ONNX Runtime Web 运行此模型")
        print("   - 边缘端: 可使用 TensorRT 将此 ONNX 转换为 .engine 文件")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")

if __name__ == "__main__":
    export_model()