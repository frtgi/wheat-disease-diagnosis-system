# 前端融合诊断功能问题诊断规范

## Why

前端融合诊断功能存在两个关键问题：1) 病灶区域无法正常显示；2) 诊断结果不准确或错误。需要全面检查项目文件以识别根本原因。

## What Changes

- 检查前端代码文件（Vue 组件、TypeScript 类型定义）
- 检查 API 接口调用逻辑
- 检查数据处理模块
- 检查状态管理机制
- 检查相关配置文件
- 分析问题与功能异常的关联关系

## Impact

- Affected specs: 融合诊断功能、视觉检测模块、结果展示模块
- Affected code:
  - `src/web/frontend/src/views/Diagnosis.vue`
  - `src/web/frontend/src/components/diagnosis/FusionResult.vue`
  - `src/web/frontend/src/components/diagnosis/AnnotatedImage.vue`
  - `src/web/backend/app/services/fusion_service.py`
  - `src/web/backend/app/services/yolo_service.py`
  - `src/web/backend/app/api/v1/ai_diagnosis.py`

## ADDED Requirements

### Requirement: 病灶区域显示诊断

系统应正确识别并显示病灶区域。

#### Scenario: 图像上传后病灶区域显示
- **WHEN** 用户上传病害图像并点击诊断
- **THEN** YOLOv8 应正确检测病灶区域
- **AND** 检测框应在图像上正确绘制
- **AND** 标注图像应正确返回给前端
- **AND** 前端应正确显示标注图像

### Requirement: 诊断结果准确性

系统应返回准确的诊断结果。

#### Scenario: 融合诊断结果返回
- **WHEN** 融合诊断完成
- **THEN** 应返回正确的病害名称
- **AND** 应返回合理的置信度
- **AND** 应返回有效的建议

## MODIFIED Requirements

无修改的需求。

## REMOVED Requirements

无移除的需求。
