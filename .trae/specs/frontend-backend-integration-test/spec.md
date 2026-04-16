# 前后端集成测试与知识图谱功能验证 Spec

## Why
在完成 Qwen3-VL GPU INT4 量化修复后，需要验证整个系统的前后端集成功能，特别是知识图谱在诊断流程中的作用，确保所有功能正常执行。

## What Changes
- 验证后端所有 API 端点正常工作
- 验证前端所有页面和功能正常工作
- 验证知识图谱在诊断流程中的增强作用
- 验证 GraphRAG 服务与诊断服务的集成
- 生成完整的集成测试报告

## Impact
- Affected specs: integration-test, kad-former-graphrag-fusion, comprehensive-testing
- Affected code: 
  - 后端 API 端点 (user, diagnosis, knowledge, stats, health, ai_diagnosis, metrics, logs, reports)
  - 前端页面和组件
  - GraphRAG 服务
  - 知识库服务

## ADDED Requirements

### Requirement: 后端 API 完整性测试
系统 SHALL 提供完整的后端 API 测试覆盖。

#### Scenario: 用户认证 API 测试
- **WHEN** 调用用户注册、登录、令牌刷新等 API
- **THEN** 返回正确的状态码和数据格式

#### Scenario: 诊断 API 测试
- **WHEN** 调用文本诊断、图像诊断、融合诊断等 API
- **THEN** 返回正确的诊断结果和置信度

#### Scenario: 知识库 API 测试
- **WHEN** 调用知识搜索、知识详情、知识分类等 API
- **THEN** 返回正确的知识数据

#### Scenario: 统计 API 测试
- **WHEN** 调用统计信息、仪表盘数据等 API
- **THEN** 返回正确的统计数据

### Requirement: 知识图谱功能验证
系统 SHALL 在诊断流程中正确使用知识图谱增强功能。

#### Scenario: GraphRAG 服务初始化
- **WHEN** 系统启动时
- **THEN** GraphRAG 服务正确初始化或进入降级模式

#### Scenario: 知识检索增强
- **WHEN** 用户提交诊断请求
- **THEN** 系统从知识图谱检索相关知识并注入诊断上下文

#### Scenario: 知识引用溯源
- **WHEN** 返回诊断结果
- **THEN** 包含知识来源引用信息

### Requirement: 前后端数据一致性
系统 SHALL 保证前后端数据流转正确。

#### Scenario: 数据格式一致性
- **WHEN** 前端发送请求
- **THEN** 后端正确解析请求参数

#### Scenario: 响应数据一致性
- **WHEN** 后端返回响应
- **THEN** 前端正确解析并展示数据

### Requirement: 知识图谱可视化功能
系统 SHALL 提供知识图谱可视化接口。

#### Scenario: 知识图谱数据获取
- **WHEN** 前端请求知识图谱数据
- **THEN** 返回节点和关系数据

#### Scenario: 知识图谱渲染
- **WHEN** 前端接收知识图谱数据
- **THEN** 正确渲染知识图谱可视化界面

## MODIFIED Requirements

### Requirement: AI 诊断服务集成
诊断服务 SHALL 正确集成 YOLOv8 和 Qwen3-VL 模型。

#### Scenario: YOLOv8 检测
- **WHEN** 上传病害图像
- **THEN** YOLOv8 正确检测病害区域

#### Scenario: Qwen3-VL 多模态诊断
- **WHEN** 提交图像和文本
- **THEN** Qwen3-VL 正确生成诊断报告

## REMOVED Requirements
无
