# 重新训练小麦病害检测模型任务

## Phase 1: 训练准备

- [ ] **任务 1.1: 创建 weights 目录**
  - [ ] 在 models/wheat_disease_v10_yolov8s/phase1_warmup/ 下创建 weights 目录

- [ ] **任务 1.2: 验证训练环境**
  - [ ] 验证 conda 环境 wheatagent-py310 可用
  - [ ] 验证 CUDA/GPU 可用
  - [ ] 验证 ultralytics 包已安装

## Phase 2: 模型训练

- [ ] **任务 2.1: 执行 YOLOv8 训练**
  - [ ] 使用 YOLOv8s 预训练权重
  - [ ] 训练 30 epochs (phase1_warmup)
  - [ ] 监控训练进度

- [ ] **任务 2.2: 训练后处理**
  - [ ] 验证 best.pt 生成
  - [ ] 验证 last.pt 生成

## Phase 3: 模型验证

- [ ] **任务 3.1: 性能验证**
  - [ ] 检查 mAP@50 >= 95%
  - [ ] 验证 15 种病害类别正确

- [ ] **任务 3.2: 集成验证**
  - [ ] 验证 YOLO 服务能加载模型
  - [ ] 测试实际检测功能

# Task Dependencies

```
任务 1.1 ──┬──► 任务 2.1 ──► 任务 2.2
           │          │
任务 1.2 ──┘          │
                      ▼
               任务 3.1 ──► 任务 3.2
```

## 训练配置

- 基础模型: YOLOv8s (yolov8s.pt)
- 数据集: wheat_data_unified
- 类别数: 15
- Epochs: 30 (phase1)
- Batch Size: 4-8 (根据显存调整)
- 目标 mAP@50: >= 95%
