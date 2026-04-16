# 多模态功能修复与架构一致性规范

## Why

前后端服务已启动，但系统存在三个关键问题影响核心业务流程：
1. 视觉模块未能正确识别并显示病灶区域，认知模块推理结果未同步展示
2. 知识库接口返回 422 错误，前后端参数格式不匹配
3. 系统架构存在不一致性，影响可维护性

## What Changes

- 修复视觉识别结果展示功能，确保病灶区域在前端正确渲染
- 整合认知模块实时推理结果展示（概率值、特征参数、结论判断）
- 修复知识库接口参数格式问题，解决 422 错误
- 统一前后端数据结构和 API 接口定义
- **BREAKING**: 知识库 API 参数从 `skip/limit` 改为 `page/page_size`

## Impact

- Affected specs: 诊断流程、知识库检索、多模态融合
- Affected code:
  - `src/web/backend/app/api/v1/knowledge.py`
  - `src/web/backend/app/services/fusion_service.py`
  - `src/web/backend/app/services/yolo_service.py`
  - `src/web/frontend/src/api/knowledge.ts`
  - `src/web/frontend/src/components/diagnosis/FusionResult.vue`
  - `src/web/frontend/src/components/diagnosis/MultiModalInput.vue`

## ADDED Requirements

### Requirement: 视觉识别结果展示

系统应在前端界面直观展示 YOLOv8 检测到的病灶区域，包括：
- 检测框坐标和尺寸
- 病害类别名称
- 检测置信度

#### Scenario: 图像上传后病灶区域展示
- **WHEN** 用户上传病害图像并点击诊断
- **THEN** 系统应在图像上绘制检测框
- **AND** 显示每个检测框对应的病害类别和置信度
- **AND** 在结果面板中展示视觉检测结果列表

### Requirement: 认知模块推理结果同步展示

系统应在视觉识别结果旁同步显示认知模块的推理分析数据。

#### Scenario: 推理结果展示
- **WHEN** 多模态融合诊断完成
- **THEN** 系统应展示以下推理数据：
  - 综合置信度（加权融合结果）
  - 视觉置信度（YOLOv8 检测置信度）
  - 文本置信度（Qwen3-VL 语义分析置信度）
  - 知识置信度（GraphRAG 检索置信度）
- **AND** 展示推理链（Thinking 模式）
- **AND** 展示知识引用溯源

### Requirement: 知识库接口参数规范化

知识库 API 应使用统一的分页参数格式。

#### Scenario: 知识库搜索请求
- **WHEN** 前端请求知识库数据
- **THEN** 使用 `page` 和 `page_size` 参数进行分页
- **AND** 后端正确计算 `skip` 值
- **AND** 返回符合 schema 的数据格式

## MODIFIED Requirements

### Requirement: 多模态融合诊断响应格式

融合诊断 API 响应应包含完整的视觉和认知分析结果。

修改点：
- 添加 `visual_detections` 字段，包含 YOLOv8 检测结果
- 添加 `annotated_image` 字段，包含标注后的图像（Base64）
- 确保 `roi_boxes` 字段格式正确

### Requirement: 前端知识库 API 调用

前端知识库 API 调用应与后端接口定义一致。

修改点：
- 将 `skip/limit` 参数改为 `page/page_size`
- 添加正确的类型定义
- 处理 422 错误响应

## REMOVED Requirements

无移除的需求。
