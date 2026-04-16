# Qwen3-VL 专用模型加载方式 Spec

## Why
当前使用 `Qwen2VLForConditionalGeneration` 加载 `Qwen3-VL-4B-Instruct` 模型，导致推理时张量维度不匹配错误（`The size of tensor a (80) must match the size of tensor b (128)`）。Qwen3-VL 是独立架构，需要使用专用的 `Qwen3VLForConditionalGeneration` 类进行加载。

## What Changes
- 使用 `Qwen3VLForConditionalGeneration` 替代 `Qwen2VLForConditionalGeneration`
- 更新 transformers 库到支持 Qwen3-VL 的版本（需要 >= 4.57.0 或从 GitHub 源码安装）
- 修改消息格式以符合 Qwen3-VL 官方文档要求
- 更新推理代码使用正确的 `apply_chat_template` 方式
- **BREAKING**: 移除 `ignore_mismatched_sizes=True` 参数，改用正确的模型类

## Impact
- Affected specs: AI 模型加载、多模态诊断服务
- Affected code: `src/web/backend/app/services/qwen_service.py`
- Dependencies: transformers >= 4.57.0 或从 GitHub 源码安装

## ADDED Requirements

### Requirement: Qwen3-VL 专用模型加载
系统 SHALL 使用 `Qwen3VLForConditionalGeneration` 类加载 Qwen3-VL-4B-Instruct 模型。

#### Scenario: 模型加载成功
- **WHEN** 系统启动并加载 Qwen3-VL 模型
- **THEN** 应使用 `Qwen3VLForConditionalGeneration.from_pretrained()` 加载模型
- **AND** 无需 `ignore_mismatched_sizes=True` 参数
- **AND** 模型应正确加载，无架构不匹配警告

#### Scenario: 多模态推理成功
- **WHEN** 用户上传图像并请求诊断
- **THEN** 模型应正确处理图像输入
- **AND** 输出符合预期格式的诊断结果
- **AND** 无张量维度不匹配错误

### Requirement: 正确的消息格式
系统 SHALL 使用 Qwen3-VL 官方推荐的消息格式进行多模态输入。

#### Scenario: 图像+文本输入
- **WHEN** 用户上传图像并提供症状描述
- **THEN** 消息格式应为：
  ```python
  messages = [
      {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
      {"role": "user", "content": [
          {"type": "image", "image": image_path_or_pil_image},
          {"type": "text", "text": user_prompt}
      ]}
  ]
  ```

### Requirement: 正确的推理方式
系统 SHALL 使用 `apply_chat_template` 方法进行推理。

#### Scenario: 推理流程
- **WHEN** 执行多模态推理
- **THEN** 应使用 `processor.apply_chat_template()` 处理输入
- **AND** 设置 `tokenize=True`, `return_dict=True`, `return_tensors="pt"`
- **AND** 正确截取生成的 token 序列

## MODIFIED Requirements

### Requirement: 模型加载参数
原使用 `Qwen2VLForConditionalGeneration` 和 `ignore_mismatched_sizes=True`，现改为：

```python
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor

model = Qwen3VLForConditionalGeneration.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,  # 或 "auto"
    device_map="auto"
)
processor = AutoProcessor.from_pretrained(model_path)
```

## 技术细节

### Qwen3-VL 架构特性
根据 `config.json`：
- `architectures`: ["Qwen3VLForConditionalGeneration"]
- `model_type`: "qwen3_vl"
- `vision_config.hidden_size`: 1024
- `vision_config.deepstack_visual_indexes`: [5, 11, 17]
- `text_config.hidden_size`: 2560
- `text_config.num_hidden_layers`: 36

### 与 Qwen2-VL 的差异
- Qwen3-VL 使用 DeepStack 多层视觉特征注入
- 视觉编码器维度不同
- 使用 Interleaved-MRoPE 位置编码

### 依赖要求
- transformers >= 4.57.0 或从 GitHub 源码安装：
  ```bash
  pip install git+https://github.com/huggingface/transformers
  ```
- torch >= 2.1.0
- accelerate >= 0.26.0
- qwen-vl-utils（用于图像处理）

## 错误详情

### 当前错误
```
The size of tensor a (80) must match the size of tensor b (128) at non-singleton dimension 3
```

### 错误原因
使用 `Qwen2VLForConditionalGeneration` 加载 Qwen3-VL 模型时，虽然 `ignore_mismatched_sizes=True` 允许模型加载，但推理时视觉编码器输出维度与语言模型期望维度不匹配。

### 解决方案
使用专用的 `Qwen3VLForConditionalGeneration` 类，该类正确实现了 Qwen3-VL 的架构。
