# 文件路径: WheatAgent/src/vision/train.py
import os
import sys
import torch
from ultralytics import YOLO

# --- 路径修复 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

try:
    from action.evolve import EvolutionEngine
except ImportError:
    EvolutionEngine = None

def train_model(epochs=10):
    print("="*60)
    print("🚀 [Training System] 启动小麦病害模型增量训练任务")
    
    # --- 关键修改 1: 智能设备选择 ---
    # 优先检测 CUDA，其次 MPS (Mac), 最后 CPU
    if torch.cuda.is_available():
        device = 0
        device_name = torch.cuda.get_device_name(0)
        print(f"✅ 检测到 GPU: {device_name}")
    elif torch.backends.mps.is_available():
        device = 'mps'
        print("✅ 检测到 Apple MPS 加速")
    else:
        device = 'cpu'
        print("⚠️以此警告：正在使用 CPU 训练，速度将非常慢！")
    print("="*60)

    # Phase 1: 数据闭环 (保持不变)
    if EvolutionEngine:
        try:
            print("\nPhase 1: 数据闭环处理")
            engine = EvolutionEngine()
            new_samples = engine.digest_feedback()
            print(f"   -> 处理反馈样本: {new_samples} 个")
        except Exception as e:
            print(f"   -> (跳过闭环) {e}")
    
    # Phase 2: 加载模型
    last_best = 'runs/detect/runs/train/wheat_experiment2/weights/best.pt'
    if os.path.exists(last_best):
        print(f"\nPhase 2: 微调现有模型: {last_best}")
        model = YOLO(last_best)
    else:
        print(f"\nPhase 2: 加载 Nano 预训练模型 (速度最快)")
        model = YOLO('yolov8n.pt')

    # Phase 3: 训练配置优化
    print(f"\nPhase 3: 开始训练 (Device={device})...")
    
    # --- 关键修改 2: 参数调优 ---
    # imgsz: 640 -> 512 (提速约 30%)
    # workers: 设为 4 或 8，避免数据加载瓶颈
    # batch: 根据显存自动调整，-1 为自动模式，或者显式指定 16/32
    try:
        results = model.train(
            data='configs/wheat_disease.yaml', 
            epochs=epochs, 
            imgsz=512,           # [优化] 降低分辨率以大幅提速
            batch=16,            # [优化] 增大 Batch (CPU通常只能跑4，GPU可以跑16-64)
            workers=4,           # [优化] 数据加载线程数
            project='runs/detect/runs/train', 
            name='wheat_evolution', 
            exist_ok=True, 
            patience=5,
            device=device,       # [关键] 强制指定正确的设备
            verbose=True
        )
        print(f"\n✅ 训练完成！模型已保存: {results.save_dir}")
    except Exception as e:
        print(f"\n❌ 训练中断: {e}")
        if device != 'cpu':
            print("💡 如果遇到显存不足 (OOM)，请尝试将 batch 改为 8 或 4")

if __name__ == '__main__':
    # 建议先跑 3-5 轮测试速度
    train_model(epochs=5)