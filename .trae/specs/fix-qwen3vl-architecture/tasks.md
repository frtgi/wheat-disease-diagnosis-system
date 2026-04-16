# Tasks

## Phase 0: P0 紧急修复

- [x] **P0-V6-01: QwenModelLoader.__new__() API 兼容性修复**
  - [x] 修改 __new__ 签名：`def __new__(cls)` → `def __new__(cls, *args, **kwargs)`
  - [x] 添加中文函数级注释说明参数透传机制
  - [x] 编写单元测试 test_qwen_loader_fix.py（8 个测试用例全部通过）
  - [x] 验证单例模式、lazy_load 参数、get_model_loader() 均正常工作

## Phase 1: 错误分析

- [x] Task 1.1: 分析 Qwen3-VL 模型架构差异
  - [x] 确认 Qwen3-VL 与 Qwen2-VL 的架构差异
  - [x] 检查 transformers 库版本支持
  - [x] 确定正确的模型加载方式

## Phase 2: 代码修复

- [x] Task 2.1: 修改模型加载逻辑
  - [x] 添加 `ignore_mismatched_sizes=True` 参数
  - [x] 或使用 `AutoModelForCausalLM` 作为备选
  - [x] 优化错误处理和降级逻辑

- [x] Task 2.2: 优化降级模式
  - [x] 确保降级模式正常工作
  - [x] 添加更详细的错误日志
  - [x] 验证文本诊断功能

## Phase 3: 验证测试

- [ ] Task 3.1: 重启服务验证
  - [ ] 重启后端服务
  - [ ] 检查模型加载日志
  - [ ] 确认无 ERROR 级别错误

- [ ] Task 3.2: 功能测试
  - [ ] 测试文本诊断功能
  - [ ] 测试图像诊断功能（如果模型加载成功）
  - [ ] 验证降级模式正常工作

# Task Dependencies
- [Task 2.1] depends on [Task 1.1]
- [Task 2.2] depends on [Task 2.1]
- [Task 3.1] depends on [Task 2.1, Task 2.2]
- [Task 3.2] depends on [Task 3.1]
