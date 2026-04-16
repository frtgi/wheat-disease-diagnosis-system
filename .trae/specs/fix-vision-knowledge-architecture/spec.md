# 视觉模块与知识库功能修复 Spec

## Why
前后端服务已成功启动，但系统未按照多模态特征融合修改文档正确展示功能。存在三个紧急问题：
1. 视觉模块功能异常 - 图片上传后未能正确识别并显示病灶区域
2. 知识库功能错误 - 前端调用知识库接口返回422 Unprocessable Entity错误
3. 架构一致性 - 需要确保所有文件严格遵循当前项目架构规范

## What Changes
- 修复视觉识别算法调用流程，确保病灶区域能够被准确识别并在前端界面直观展示
- 整合认知模块的实时推理结果展示功能（概率值、特征参数、结论性判断）
- 修复知识库接口422错误，检查前端请求参数格式和后端参数验证逻辑
- 全面检查项目架构一致性，重构不符合规范的实现

## Impact
- Affected specs: 视觉检测模块、知识图谱模块、前端展示组件
- Affected code: 
  - src/web/backend/services/yolo_service.py
  - src/web/backend/services/qwen_service.py
  - src/web/backend/api/v1/knowledge.py
  - src/web/frontend/src/views/Diagnosis.vue
  - src/web/frontend/src/components/DiagnosisResult.vue

## ADDED Requirements

### Requirement: 视觉模块病灶区域展示
系统 SHALL 在前端界面正确展示视觉识别的病灶区域，包括边界框标注和置信度显示。

#### Scenario: 图片上传诊断成功
- **WHEN** 用户上传小麦病害图片并点击诊断
- **THEN** 系统应正确识别病灶区域
- **AND** 在前端界面显示边界框标注
- **AND** 显示病害名称和置信度
- **AND** 同步显示认知模块的推理分析数据

### Requirement: 知识库接口正常响应
系统 SHALL 正确处理知识库查询请求，返回200状态码和预期数据。

#### Scenario: 知识库查询成功
- **WHEN** 前端调用知识库接口
- **THEN** 系统应返回200状态码
- **AND** 返回正确的知识数据结构

### Requirement: 架构一致性
系统 SHALL 严格遵循当前项目架构规范，包括代码组织结构、模块间依赖关系、接口定义标准及数据流转流程。

## MODIFIED Requirements

### Requirement: 多模态诊断流程
诊断流程 SHALL 按照多模态特征融合修改文档实现：
1. 图像预处理
2. YOLOv8模型推理
3. 环境数据编码
4. DeepStack多层特征注入
5. SE跨模态注意力融合
6. 不确定性量化
7. 知识图谱查询
8. 生成诊断报告

## REMOVED Requirements
无
