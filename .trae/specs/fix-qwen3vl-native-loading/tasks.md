# Tasks

## Phase 1: 环境检查与依赖更新

- [x] Task 1.1: 检查 transformers 库版本
  - [x] 确认当前 transformers 版本 (5.1.0)
  - [x] 检查是否支持 `Qwen3VLForConditionalGeneration` (支持)
  - [x] 如不支持，从 GitHub 源码安装 (不需要，已支持)

- [x] Task 1.2: 验证 qwen-vl-utils 安装
  - [x] 检查 qwen-vl-utils 是否已安装 (已安装)
  - [x] 如未安装，执行安装 (不需要)

## Phase 2: 代码修改

- [x] Task 2.1: 修改模型加载逻辑
  - [x] 将 `Qwen2VLForConditionalGeneration` 替换为 `Qwen3VLForConditionalGeneration`
  - [x] 移除 `ignore_mismatched_sizes=True` 参数
  - [x] 更新模型加载参数（torch_dtype=bfloat16）

- [x] Task 2.2: 修改消息格式
  - [x] 更新 `_generate_multimodal` 方法使用官方推荐的消息格式
  - [x] 使用 `processor.apply_chat_template()` 处理输入
  - [x] 设置正确的参数：`tokenize=True`, `return_dict=True`, `return_tensors="pt"`

- [x] Task 2.3: 修改推理逻辑
  - [x] 更新生成 token 的截取方式
  - [x] 确保正确解码输出

- [x] Task 2.4: 更新降级模式
  - [x] 更新 `_load_model_fallback` 方法
  - [x] 确保降级模式仍能正常工作

## Phase 3: 验证测试

- [ ] Task 3.1: 重启服务验证
  - [ ] 重启后端服务
  - [ ] 检查模型加载日志
  - [ ] 确认无 ERROR 级别错误
  - [ ] 确认无架构不匹配警告

- [ ] Task 3.2: 功能测试
  - [ ] 测试文本诊断功能
  - [ ] 测试图像诊断功能
  - [ ] 测试多模态诊断功能（图像+文本）
  - [ ] 验证输出格式正确

# Task Dependencies
- [Task 1.1] 必须先完成，确认环境支持
- [Task 1.2] 与 [Task 1.1] 可并行
- [Task 2.1] depends on [Task 1.1]
- [Task 2.2] depends on [Task 2.1]
- [Task 2.3] depends on [Task 2.2]
- [Task 2.4] depends on [Task 2.1]
- [Task 3.1] depends on [Task 2.1, Task 2.2, Task 2.3, Task 2.4]
- [Task 3.2] depends on [Task 3.1]
