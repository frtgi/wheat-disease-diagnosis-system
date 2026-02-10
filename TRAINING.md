# 🎓 IWDDA 模型训练指南

本文档详细说明如何训练 IWDDA 的视觉检测模型和增量学习。

## 📋 目录

- [训练概述](#训练概述)
- [环境准备](#环境准备)
- [基础训练](#基础训练)
- [增量训练](#增量训练)
- [模型评估](#模型评估)
- [模型导出](#模型导出)
- [训练优化](#训练优化)

---

## 🎯 训练概述

### 训练流程

```
数据准备
  ↓
模型初始化
  ↓
训练配置
  ↓
开始训练
  ↓
监控训练
  ↓
模型评估
  ↓
模型导出
```

### 训练目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| mAP@0.5 | > 95% | 平均精度均值 |
| CIoU | > 0.85 | 完整交并比 |
| Precision | > 90% | 精确率 |
| Recall | > 85% | 召回率 |
| FPS | > 30 | 推理速度 |

---

## 🔧 环境准备

### 检查硬件

```python
import torch

print("=" * 50)
print("硬件检查")
print("=" * 50)

# 检查 CUDA
if torch.cuda.is_available():
    print(f"✅ CUDA 可用")
    print(f"   GPU 数量: {torch.cuda.device_count()}")
    print(f"   GPU 名称: {torch.cuda.get_device_name(0)}")
    print(f"   显存总量: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
else:
    print("❌ CUDA 不可用，将使用 CPU 训练")

# 检查 MPS (Apple Silicon)
if torch.backends.mps.is_available():
    print("✅ MPS 可用 (Apple Silicon)")

print("=" * 50)
```

### 检查数据集

```python
from pathlib import Path

def check_dataset():
    data_root = Path('datasets/wheat_data')
    
    print("=" * 50)
    print("数据集检查")
    print("=" * 50)
    
    # 检查目录结构
    dirs_to_check = [
        'images/train',
        'images/val',
        'labels/train',
        'labels/val'
    ]
    
    for dir_path in dirs_to_check:
        full_path = data_root / dir_path
        if full_path.exists():
            count = len(list(full_path.glob('*')))
            print(f"✅ {dir_path}: {count} 个文件")
        else:
            print(f"❌ {dir_path}: 目录不存在")
    
    # 检查一一对应
    img_train = list((data_root / 'images/train').glob('*.jpg'))
    lbl_train = list((data_root / 'labels/train').glob('*.txt'))
    
    img_val = list((data_root / 'images/val').glob('*.jpg'))
    lbl_val = list((data_root / 'labels/val').glob('*.txt'))
    
    print()
    print(f"训练集图像: {len(img_train)}")
    print(f"训练集标签: {len(lbl_train)}")
    print(f"验证集图像: {len(img_val)}")
    print(f"验证集标签: {len(lbl_val)}")
    
    if len(img_train) == len(lbl_train) and len(img_val) == len(lbl_val):
        print("\n✅ 数据集完整性检查通过")
    else:
        print("\n❌ 数据集完整性检查失败")
    
    print("=" * 50)

check_dataset()
```

---

## 🚀 基础训练

### 训练脚本

使用 `src/vision/train.py` 进行训练：

```python
import os
import sys
import torch
from ultralytics import YOLO

def train_model(epochs=10):
    print("=" * 60)
    print("🚀 [Training System] 启动小麦病害模型训练任务")
    print("=" * 60)
    
    # --- 设备选择 ---
    if torch.cuda.is_available():
        device = 0
        device_name = torch.cuda.get_device_name(0)
        print(f"✅ 检测到 GPU: {device_name}")
    elif torch.backends.mps.is_available():
        device = 'mps'
        print("✅ 检测到 Apple MPS 加速")
    else:
        device = 'cpu'
        print("⚠️ 警告：正在使用 CPU 训练，速度将非常慢！")
    
    # --- 加载模型 ---
    # 优先加载已训练的模型
    last_best = 'runs/detect/runs/train/wheat_evolution/weights/best.pt'
    if os.path.exists(last_best):
        print(f"\n✅ 微调现有模型: {last_best}")
        model = YOLO(last_best)
    else:
        print(f"\n📥 加载预训练模型: yolov8n.pt")
        model = YOLO('yolov8n.pt')
    
    # --- 开始训练 ---
    print(f"\n🎯 开始训练 (Device={device})...")
    
    try:
        results = model.train(
            data='configs/wheat_disease.yaml',  # 数据集配置
            epochs=epochs,                      # 训练轮数
            imgsz=512,                        # 输入图像尺寸
            batch=16,                          # 批次大小
            workers=4,                          # 数据加载线程数
            project='runs/detect/runs/train',   # 项目目录
            name='wheat_evolution',             # 实验名称
            exist_ok=True,                      # 允许覆盖
            patience=5,                         # 早停耐心值
            device=device,                       # 训练设备
            verbose=True                        # 详细输出
        )
        
        print(f"\n✅ 训练完成！模型已保存: {results.save_dir}")
        
    except Exception as e:
        print(f"\n❌ 训练中断: {e}")
        if device != 'cpu':
            print("💡 如果遇到显存不足 (OOM)，请尝试将 batch 改为 8 或 4")

if __name__ == '__main__':
    # 建议先跑 3-5 轮测试速度
    train_model(epochs=5)
```

### 快速开始

```bash
# 进入项目目录
cd WheatAgent

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 开始训练（5 轮测试）
python src/vision/train.py
```

### 训练参数说明

| 参数 | 默认值 | 说明 | 推荐范围 |
|------|--------|------|---------|
| data | - | 数据集配置文件 | configs/wheat_disease.yaml |
| epochs | 10 | 训练轮数 | 50-200 |
| imgsz | 512 | 输入图像尺寸 | 416-640 |
| batch | 16 | 批次大小 | 8-64 (根据显存调整） |
| workers | 4 | 数据加载线程数 | 4-8 |
| patience | 5 | 早停耐心值 | 5-10 |
| device | auto | 训练设备 | 0 (GPU), cpu, mps |
| lr0 | 0.01 | 初始学习率 | 0.001-0.01 |
| weight_decay | 0.0005 | 权重衰减 | 0.0001-0.001 |

### 训练监控

训练过程中，YOLOv8 会自动生成以下监控内容：

1. **TensorBoard 日志**
```bash
# 启动 TensorBoard
tensorboard --logdir runs/detect/runs/train/wheat_evolution

# 浏览器访问
# http://localhost:6006
```

2. **实时进度**
```
Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
  1/10      2.38G      1.234      0.567      0.891        256         512
  2/10      2.41G      1.123      0.534      0.823        256         512
  ...
```

3. **验证指标**
```
      Class     Images  Instances      Box(P          R      mAP50  mAP50-95)
        all       1000       5000      0.923      0.876      0.912      0.856
```

---

## 🔄 增量训练

### 为什么需要增量训练？

农业环境是动态变化的：
- 病原菌产生抗药性变异
- 新病害类型出现
- 新作物品种带来新表型特征
- 用户反馈的困难样本

### 增量训练流程

```
收集反馈数据
  ↓
消化反馈数据
  ↓
加载基础模型
  ↓
增量训练
  ↓
模型评估
  ↓
模型更新
```

### 反馈数据收集

系统会自动收集用户反馈到 `datasets/feedback_data/`：

```
datasets/feedback_data/
├── 条锈病/
│   ├── 20240110_143022_confirmed_条锈病.jpg
│   ├── 20240110_143523_err_白粉病_corr_条锈病.jpg
│   └── feedback_log.txt
├── 赤霉病/
│   └── ...
```

### 消化反馈数据

```python
from src.action.evolve import EvolutionEngine

# 创建进化引擎
engine = EvolutionEngine()

# 消化反馈数据
processed_count = engine.digest_feedback()

print(f"✅ 处理了 {processed_count} 个反馈样本")
```

**处理流程**：
1. 扫描反馈数据池
2. 将图像移动到训练集 `images/train/`
3. 生成 YOLO 格式标签（默认中心框）
4. 归档到 `archived/` 目录

### 增量训练脚本

```python
def incremental_train(epochs=10):
    """
    增量训练：在已有模型基础上继续训练
    """
    print("=" * 60)
    print("🔄 [Incremental Training] 启动增量训练任务")
    print("=" * 60)
    
    # --- Phase 1: 数据闭环 ---
    try:
        from src.action.evolve import EvolutionEngine
        print("\nPhase 1: 数据闭环处理")
        engine = EvolutionEngine()
        new_samples = engine.digest_feedback()
        print(f"   -> 处理反馈样本: {new_samples} 个")
    except Exception as e:
        print(f"   -> (跳过闭环) {e}")
    
    # --- Phase 2: 加载基础模型 ---
    base_model = 'runs/detect/runs/train/wheat_evolution/weights/best.pt'
    if os.path.exists(base_model):
        print(f"\nPhase 2: 加载基础模型: {base_model}")
        model = YOLO(base_model)
    else:
        print(f"\nPhase 2: 使用预训练模型")
        model = YOLO('yolov8n.pt')
    
    # --- Phase 3: 增量训练 ---
    print(f"\nPhase 3: 开始增量训练...")
    
    # 使用较小的学习率
    results = model.train(
        data='configs/wheat_disease.yaml',
        epochs=epochs,
        imgsz=512,
        batch=16,
        workers=4,
        project='runs/detect/runs/train',
        name='wheat_evolution_v2',  # 新版本名称
        exist_ok=True,
        patience=5,
        device='auto',
        lr0=0.001,  # 较小的学习率
        verbose=True
    )
    
    print(f"\n✅ 增量训练完成！新模型: {results.save_dir}")

if __name__ == '__main__':
    incremental_train(epochs=10)
```

### LoRA 微调（高级）

对于大规模模型，可以使用 LoRA (Low-Rank Adaptation) 进行高效微调：

```python
from peft import get_peft_model, LoraConfig, TaskType

def train_with_lora():
    """
    使用 LoRA 进行高效微调
    """
    # 加载基础模型
    model = YOLO('runs/detect/runs/train/wheat_evolution/weights/best.pt')
    
    # 配置 LoRA
    lora_config = LoraConfig(
        r=16,              # LoRA 秩
        lora_alpha=32,      # LoRA alpha
        target_modules=["q_proj", "v_proj"],  # 目标模块
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    
    # 应用 LoRA
    model = get_peft_model(model, lora_config)
    
    # 训练（只训练 LoRA 参数）
    results = model.train(
        data='configs/wheat_disease.yaml',
        epochs=10,
        imgsz=512,
        batch=16,
        ...
    )
    
    # 保存 LoRA 权重
    model.save_pretrained("models/lora_weights")

if __name__ == '__main__':
    train_with_lora()
```

**优势**：
- 只需训练约 0.2% 的参数
- 减少训练时间和显存占用
- 避免灾难性遗忘

---

## 📊 模型评估

### 验证集评估

```python
from ultralytics import YOLO

# 加载训练好的模型
model = YOLO('runs/detect/runs/train/wheat_evolution/weights/best.pt')

# 在验证集上评估
metrics = model.val()

# 打印结果
print("=" * 50)
print("模型评估结果")
print("=" * 50)
print(f"mAP@0.5: {metrics.box.map50:.4f}")
print(f"mAP@0.5:0.95: {metrics.box.map:.4f}")
print(f"Precision: {metrics.box.mp:.4f}")
print(f"Recall: {metrics.box.mr:.4f}")
print("=" * 50)
```

### 各类别性能分析

```python
# 获取各类别详细指标
class_metrics = metrics.box.maps  # 各类别 mAP

print("\n各类别 mAP@0.5:")
print("-" * 40)
class_names = model.names
for class_id, map_score in enumerate(class_metrics):
    if class_id < len(class_names):
        print(f"{class_names[class_id]:20s}: {map_score:.4f}")
```

### 混淆矩阵

```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 预测验证集
results = model('datasets/wheat_data/images/val', save=False)

# 计算混淆矩阵
confusion_matrix = np.zeros((17, 17))
for result in results:
    if result.boxes is not None:
        for box in result.boxes:
            pred_class = int(box.cls[0])
            # 假设真实标签从文件名或标签文件获取
            # true_class = get_true_class(result.path)
            # confusion_matrix[true_class][pred_class] += 1

# 绘制混淆矩阵
plt.figure(figsize=(12, 10))
sns.heatmap(confusion_matrix, annot=True, fmt='g', cmap='Blues')
plt.xlabel('预测类别')
plt.ylabel('真实类别')
plt.title('混淆矩阵')
plt.savefig('confusion_matrix.png')
plt.show()
```

### 可视化预测结果

```python
# 在测试图像上运行推理
results = model.predict('data/images/test_wheat.jpg', conf=0.5)

# 显示结果
for r in results:
    im_bgr = r.plot()  # BGR 格式
    im_rgb = im_bgr[..., ::-1]  # 转换为 RGB
    
    import cv2
    cv2.imshow('Prediction', im_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

---

## 💾 模型导出

### 导出 ONNX 格式

```python
# 导出为 ONNX 格式（跨平台）
model.export(format='onnx', dynamic=True, simplify=True)
```

### 导出 TensorRT 格式

```python
# 导出为 TensorRT 格式（NVIDIA GPU 加速）
model.export(format='engine', device=0, half=True)
```

### 导出 CoreML 格式

```python
# 导出为 CoreML 格式（Apple 设备）
model.export(format='coreml')
```

### 模型压缩

```python
# 模型量化（减少模型大小）
model.export(format='onnx', int8=True)

# 模型剪枝（减少计算量）
model.prune()
```

---

## ⚡ 训练优化

### GPU 内存优化

如果遇到 OOM (Out of Memory) 错误：

1. **减小 batch size**
```python
results = model.train(
    batch=8,  # 从 16 改为 8 或 4
    ...
)
```

2. **减小图像尺寸**
```python
results = model.train(
    imgsz=416,  # 从 512 改为 416
    ...
)
```

3. **使用梯度累积**
```python
results = model.train(
    batch=8,
    accumulate=2,  # 累积 2 个 batch 再更新
    ...
)
```

4. **使用混合精度训练**
```python
results = model.train(
    amp=True,  # 自动混合精度
    ...
)
```

### 训练速度优化

1. **增加 workers**
```python
results = model.train(
    workers=8,  # 增加数据加载线程
    ...
)
```

2. **使用缓存**
```python
results = model.train(
    cache=True,  # 缓存数据集
    ...
)
```

3. **使用多 GPU**
```python
results = model.train(
    device=[0, 1],  # 使用 2 个 GPU
    ...
)
```

### 训练稳定性优化

1. **学习率调度**
```python
results = model.train(
    lr0=0.001,           # 初始学习率
    lrf=0.01,            # 最终学习率因子
    momentum=0.937,       # SGD 动量
    weight_decay=0.0005,   # 权重衰减
    ...
)
```

2. **数据增强调整**
```python
results = model.train(
    fliplr=0.5,      # 水平翻转概率
    mosaic=1.0,      # Mosaic 增强
    mixup=0.0,       # Mixup 增强
    ...
)
```

3. **早停策略**
```python
results = model.train(
    patience=10,  # 增加耐心值
    ...
)
```

---

## 📚 训练最佳实践

### 1. 数据质量优先

- ✅ 确保标注准确
- ✅ 平衡各类别数量
- ✅ 使用高质量图像
- ❌ 避免模糊、过暗的图像

### 2. 渐进式训练

```python
# 第一阶段：快速收敛
train_model(epochs=10, lr0=0.01)

# 第二阶段：精细调优
train_model(epochs=20, lr0=0.001)

# 第三阶段：最终优化
train_model(epochs=30, lr0=0.0001)
```

### 3. 定期验证

```python
# 每 5 轮验证一次
for epoch in range(0, 100, 5):
    train_model(epochs=5)
    metrics = model.val()
    print(f"Epoch {epoch}: mAP@0.5 = {metrics.box.map50:.4f}")
```

### 4. 保存检查点

```python
results = model.train(
    save=True,          # 保存检查点
    save_period=5,      # 每 5 轮保存一次
    ...
)
```

### 5. 日志记录

```python
import logging

logging.basicConfig(
    filename='training.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 训练时自动记录
```

---

## 🐛 常见问题

### Q1: 训练速度很慢怎么办？

**A**: 检查以下几点：
1. 是否使用 GPU？`torch.cuda.is_available()`
2. batch size 是否太小？
3. workers 数量是否足够？
4. 是否启用了数据缓存？

### Q2: mAP 不上升怎么办？

**A**: 可能的原因和解决方案：
1. **学习率太大**：降低 `lr0`
2. **数据质量问题**：检查标注准确性
3. **类别不平衡**：使用类别权重或过采样
4. **模型容量不足**：使用更大的模型（yolov8s/m/l）

### Q3: 如何选择 YOLOv8 模型大小？

**A**: 根据硬件和需求选择：

| 模型 | 参数量 | 速度 | 精度 | 适用场景 |
|------|--------|------|------|---------|
| yolov8n | 3.2M | 最快 | 中等 | 移动端、边缘设备 |
| yolov8s | 11.2M | 快 | 高 | 桌面应用 |
| yolov8m | 25.9M | 中等 | 很高 | 服务器部署 |
| yolov8l | 43.7M | 慢 | 最高 | 高精度要求 |

### Q4: 如何处理类别不平衡？

**A**: 使用以下方法：
1. **类别权重**：在损失函数中给少数类更高权重
2. **过采样**：复制少数类样本
3. **数据增强**：对少数类进行更多增强
4. **Focal Loss**：使用 Focal Loss 替代标准交叉熵

### Q5: 如何迁移到新作物？

**A**: 迁移学习步骤：
1. 收集新作物数据集
2. 使用预训练模型作为初始化
3. 冻结骨干网络，只训练检测头
4. 逐步解冻更多层进行微调

---

<div align="center">

**训练完成后，请阅读 [API使用指南](API_USAGE.md) 开始使用模型！**

</div>
