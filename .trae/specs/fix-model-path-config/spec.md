# 修复模型路径配置 Spec

## Why

当前 AI 模型路径配置错误，导致模型无法加载：
- 配置路径：`D:\Project\WheatAgent\src\web\backend\models\`
- 实际路径：`d:\Project\WheatAgent\models\`

需要修正路径配置，使 AI 服务能够正确加载 YOLOv8 和 Qwen3-VL 模型。

## What Changes

- 修改 `app/core/ai_config.py` 中的模型路径配置
- 验证路径计算逻辑（从 ai_config.py 到 models 目录的相对路径）
- 确保启动时模型路径正确
- 验证模型加载成功

**无破坏性变更**

## Impact

- **影响的代码**: 
  - `app/core/ai_config.py` - 路径配置修正
  - `app/services/ai_preloader.py` - 可能需要调整路径获取方式
  - `app/services/yolo_service.py` - 使用修正后的路径
  - `app/services/qwen_service.py` - 使用修正后的路径

- **影响的功能**:
  - AI 模型预加载
  - 多模态诊断功能
  - 图像检测功能

## ADDED Requirements

### Requirement: 正确的模型路径配置
系统 SHALL 正确配置模型文件路径，确保能够找到实际的模型文件。

#### Scenario: 模型路径验证
- **WHEN** 应用启动时
- **THEN** AI 模型路径应该指向 `d:\Project\WheatAgent\models\` 目录
- **THEN** Qwen 模型路径应该是 `d:\Project\WheatAgent\models\Qwen3-VL-4B-Instruct`
- **THEN** YOLO 模型路径应该是 `d:\Project\WheatAgent\models\wheat_disease_v10_yolov8s\phase1_warmup\weights\best.pt`

### Requirement: 路径自动检测
系统 SHALL 支持基于项目根目录的相对路径配置，避免硬编码绝对路径。

#### Scenario: 相对路径计算
- **WHEN** ai_config.py 位于 `app/core/` 目录
- **THEN** 应该通过 `Path(__file__).parent.parent.parent / "models"` 计算项目根目录
- **THEN** 模型路径应该是相对路径加上 "models" 子目录

## MODIFIED Requirements

### Requirement: AI 配置类
`AIConfig` 类中的路径配置 SHALL 使用正确的相对路径计算。

**修改前**:
```python
QWEN_MODEL_PATH: Path = Path(__file__).parent.parent.parent / "models" / "Qwen3-VL-4B-Instruct"
YOLO_MODEL_PATH: Path = Path(__file__).parent.parent.parent / "models" / "wheat_disease_v10_yolov8s" / "phase1_warmup" / "weights" / "best.pt"
```

**修改后**:
- 需要验证实际的目录层级，确保 `parent.parent.parent` 正确指向项目根目录

### Requirement: AI 预加载模块
`ai_preloader.py` SHALL 从 `AIConfig` 实例获取路径，而不是模块级常量。

**原因**: 避免路径导入错误，确保使用统一的配置源。

## REMOVED Requirements

无

## 验收标准

1. **路径配置正确**
   - ai_config.py 中的路径计算逻辑正确
   - 模型文件路径指向实际存在的目录

2. **模型加载成功**
   - Qwen 模型 is_loaded: true
   - YOLO 模型 is_loaded: true

3. **健康检查通过**
   - /api/v1/health/components 返回 AI 服务状态为 ready
   - /api/v1/diagnosis/health/ai 返回模型已加载

4. **功能正常**
   - 多模态诊断 API 可用
   - 图像检测 API 可用
