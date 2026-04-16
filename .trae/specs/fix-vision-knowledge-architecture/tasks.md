# Tasks

## 优先级1: 视觉模块功能修复

- [x] Task 1: 诊断视觉识别问题根因
  - [x] SubTask 1.1: 检查后端YOLO服务调用流程
  - [x] SubTask 1.2: 验证图像预处理是否正确
  - [x] SubTask 1.3: 检查检测结果返回格式
  - [x] SubTask 1.4: 验证前端是否正确接收和解析检测结果
  
  **诊断结果**：
  1. YOLO服务返回`bbox`键，但fusion_service期望`box`键
  2. 前端调用`/diagnosis/fusion`但结果未正确传递给组件
  3. 知识库API路径不匹配：前端调用`/knowledge/diseases`，后端是`/knowledge/`

- [x] Task 2: 修复病灶区域展示功能
  - [x] SubTask 2.1: 确保边界框坐标正确传递到前端
  - [x] SubTask 2.2: 修复前端边界框渲染逻辑
  - [x] SubTask 2.3: 添加置信度显示功能
  - [x] SubTask 2.4: 整合认知模块推理结果展示

## 优先级2: 知识库接口修复

- [x] Task 3: 诊断知识库422错误
  - [x] SubTask 3.1: 检查前端请求参数格式
  - [x] SubTask 3.2: 检查后端API参数验证逻辑
  - [x] SubTask 3.3: 验证请求Content-Type是否正确
  - [x] SubTask 3.4: 检查Pydantic模型定义

- [x] Task 4: 修复知识库接口
  - [x] SubTask 4.1: 修正前端请求参数格式
  - [x] SubTask 4.2: 修正后端参数验证逻辑
  - [x] SubTask 4.3: 添加详细的错误响应信息
  - [x] SubTask 4.4: 验证知识库返回数据结构

## 优先级3: 架构一致性检查

- [ ] Task 5: 检查多模态融合架构实现
  - [ ] SubTask 5.1: 验证DeepStack多层特征注入是否实现
  - [ ] SubTask 5.2: 验证SE跨模态注意力是否实现
  - [ ] SubTask 5.3: 验证环境数据嵌入是否实现
  - [ ] SubTask 5.4: 验证不确定性量化是否实现

- [ ] Task 6: 端到端测试验证
  - [ ] SubTask 6.1: 运行视觉模块测试
  - [ ] SubTask 6.2: 运行知识库接口测试
  - [ ] SubTask 6.3: 运行完整诊断流程测试
  - [ ] SubTask 6.4: 验证前端展示功能

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 4] depends on [Task 3]
- [Task 6] depends on [Task 2, Task 4, Task 5]
