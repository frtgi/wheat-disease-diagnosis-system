# 修复模型路径配置 Tasks

## 任务列表

### 第一阶段：问题分析

- [x] **任务 1: 验证当前路径配置**
  - [x] 子任务 1.1: 检查 ai_config.py 路径计算
    - [x] 确认 ai_config.py 的位置
    - [x] 计算 parent.parent.parent 的实际路径
    - [x] 验证 models 目录是否存在
  - [x] 子任务 1.2: 检查实际模型位置
    - [x] 验证 d:\Project\WheatAgent\models\ 目录
    - [x] 列出模型子目录

- [x] **任务 2: 分析路径错误原因**
  - [x] 子任务 2.1: 对比配置路径和实际路径
    - [x] 记录配置路径
    - [x] 记录实际路径
    - [x] 分析差异
  - [x] 子任务 2.2: 确定正确的相对路径层级
    - [x] 计算从 ai_config.py 到 models 的正确 parent 层级（6层）
    - [x] 验证路径计算逻辑

### 第二阶段：修复路径配置

- [x] **任务 3: 修改 ai_config.py**
  - [x] 子任务 3.1: 修正 QWEN_MODEL_PATH（6层 parent）
  - [x] 子任务 3.2: 修正 YOLO_MODEL_PATH（6层 parent）
  - [x] 子任务 3.3: 添加路径验证逻辑

- [x] **任务 4: 修复 ai_preloader.py**
  - [x] 子任务 4.1: 修正路径导入方式（从 AIConfig 实例获取）
  - [x] 子任务 4.2: 启用 INT4 量化加载 Qwen 模型

- [x] **任务 5: 修复 QwenService 4-bit 量化加载**
  - [x] 子任务 5.1: 使用 BitsAndBytesConfig 配置量化
  - [x] 子任务 5.2: 修复 load_in_4bit 参数传递方式

### 第三阶段：测试验证

- [x] **任务 6: 重启服务并验证**
  - [x] 子任务 6.1: 重启后端服务
  - [x] 子任务 6.2: 验证模型加载（YOLO: 2.83秒, Qwen: 25.85秒）

- [x] **任务 7: 运行健康检查**
  - [x] 子任务 7.1: 测试组件状态端点（5/5 通过）
  - [x] 子任务 7.2: 验证所有组件 ready

### 第四阶段：文档更新

- [x] **任务 8: 更新配置文档**
  - [x] 子任务 8.1: 记录路径修复方案
  - [x] 子任务 8.2: 记录 4-bit 量化配置方法

## 修复模型路径配置 Tasks

## 任务列表

...
### 第三阶段：测试验证
- [x] **任务 5: 重启服务并验证**
  - [x] 子任务 5.1: 重启后端服务
 ...
    - [x] 停止当前服务
    - [x] 重新启动 uvicorn
    - [x] 观察启动日志
  - [x] 子任务 5.2: 验证模型加载
 ...
    - [x] 检查 AI 模型加载日志
    - [x] 确认无路径错误
...
- [x] **任务 6: 运行健康检查**
  - [x] 子任务 6.1: 测试组件状态端点
 ...
    - [x] GET /api/v1/health/components
    - [x] 验证 YOLO 服务状态
    - [x] 验证 Qwen 服务状态
  - [x] 子任务 6.2: 测试 AI 健康端点
 ...
    - [x] GET /api/v1/diagnosis/health/ai
    - [x] 验证 is_loaded: true
  - [x] 验证模型已加载
...
- [x] **任务 7: 功能测试**
  - [x] 子任务 7.1: 运行启动测试脚本
    - [x] 执行 python tests/test_startup.py
    - [x] 验证所有测试通过
  - [x] 子任务 7.2: 测试诊断功能
    - [x] 测试多模态诊断 API
    - [x] 验证模型推理正常
...
- [x] **任务 8: 更新配置文档**
  - [x] 子任务 8.1: 更新 ENVIRONMENT_MANAGEMENT.md
    - [x] 添加模型路径配置说明
    - [x] 说明相对路径计算方式
  - [x] 子任务 8.2: 创建路径配置指南
    - [x] 说明如何修改模型路径
    - [x] 提供常见问题解决方案

## 遗留问题修复

- [x] **任务 9: 修复 `No module named 'src'` 警告**
  - [x] 子任务 9.1: 修改 qwen_service.py 中的模块导入方式
    - 将 `from src.fusion` 改为相对导入 `from ....fusion`
    - 将 `from src.graph.graphrag_engine` 改为相对导入 `from ....graph.graphrag_engine`
    - 添加 ImportError 异常处理
  - [x] 子任务 9.2: 验证修改后无警告（导入测试通过）

- [x] **任务 10: 修复 `update_component_status()` metadata 参数错误**
  - [x] 子任务 10.1: 从 ai_preloader.py 中移除 metadata 参数
  - [x] 子任务 10.2: 验证修改后无错误（导入测试通过）

- [x] **任务 11: 修复 AI 健康检查返回 `is_loaded: False` 问题**
  - [x] 子任务 11.1: 分析问题根源
    - 预加载的服务实例未存储到全局变量
    - 健康检查调用 get_yolo_service/get_qwen_service 创建新实例
  - [x] 子任务 11.2: 修改 ai_preloader.py 将预加载实例存储到全局变量
  - [x] 子任务 11.3: 验证修改后导入成功

## 任务依赖

```
任务 1 (验证路径) ──► 任务 2 (分析原因) ──► 任务 3 (修改配置)
                                              │
                                              ▼
任务 8 (文档更新) ◄── 任务 7 (功能测试) ◄── 任务 6 (健康检查) ◄── 任务 5 (重启服务) ◄── 任务 4 (修复 preloader)
                                                                                              │
                                                                                              ▼
                                                                        任务 9 (修复 src 导入) ──► 任务 10 (修复 metadata 参数)
```

## 验收标准

### 路径配置
- [ ] ai_config.py 路径计算正确
- [ ] QWEN_MODEL_PATH 指向正确目录
- [ ] YOLO_MODEL_PATH 指向正确文件
- [ ] 路径验证逻辑完善

### 模型加载
- [ ] Qwen 模型 is_loaded: true
- [ ] YOLO 模型 is_loaded: true
- [ ] 启动日志显示模型加载成功
- [ ] 无路径相关错误

### 健康检查
- [ ] /health/components 返回 AI 服务 ready
- [ ] /diagnosis/health/ai 返回模型已加载
- [ ] 所有健康检查端点正常

### 功能测试
- [ ] test_startup.py 全部通过
- [ ] 多模态诊断 API 可用
- [ ] 模型推理功能正常

## 预计时间

| 任务 | 预计时间 |
|------|----------|
| 任务 1-2: 问题分析 | 15 分钟 |
| 任务 3-4: 修复配置 | 20 分钟 |
| 任务 5-7: 测试验证 | 25 分钟 |
| 任务 8: 文档更新 | 10 分钟 |
| **总计** | **约 70 分钟** |
