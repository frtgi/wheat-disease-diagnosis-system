# 重新训练小麦病害检测模型规范

## Why

YOLOv8 小麦病害检测模型的权重文件（best.pt）已丢失，导致前端融合诊断功能的视觉检测完全失效。需要重新训练模型以恢复病害检测能力。

## What Changes

- 检查训练环境和数据集完整性
- 使用 YOLOv8s 预训练权重重新训练模型
- 采用多阶段训练策略优化性能
- 验证模型性能达到目标指标 (mAP@50 >= 95%)
- 将训练好的模型部署到正确路径

## Impact

- Affected specs: diagnose-fusion-issues (P0 问题解决)
- Affected code:
  - `models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt`
  - `src/web/backend/app/core/ai_config.py`
  - `src/web/backend/app/services/yolo_service.py`

## ADDED Requirements

### Requirement: 模型训练

系统应完成 YOLOv8 小麦病害检测模型的训练。

#### Scenario: 训练成功
- **WHEN** 训练脚本执行完成
- **THEN** 应生成 `weights/best.pt` 文件
- **AND** mAP@50 应 >= 95%
- **AND** 模型应能正确检测 15 种小麦病害类别

### Requirement: 模型部署

训练好的模型应正确部署到生产路径。

#### Scenario: 部署成功
- **WHEN** 训练完成
- **THEN** 权重文件应存在于 `models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt`
- **AND** YOLO 服务应能成功加载模型

## MODIFIED Requirements

无修改的需求。

## REMOVED Requirements

无移除的需求。

## 训练配置

### 硬件限制
- GPU: RTX 3050 Laptop (4GB 显存)
- 需要使用混合精度训练 (AMP)
- 批次大小建议: 4-8

### 数据集
- 路径: `datasets/wheat_data_unified`
- 类别数: 15 种小麦病害
- 训练集: images/train
- 验证集: images/val

### 训练策略
- 基础模型: YOLOv8s (预训练)
- 目标 mAP@50: >= 95%
- 预计训练时间: 2-4 小时
