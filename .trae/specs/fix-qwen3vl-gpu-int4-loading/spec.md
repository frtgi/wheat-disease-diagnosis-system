# Qwen3-VL GPU INT4量化加载修复 Spec

## Why
Qwen3-VL模型在INT4量化加载时使用了CPU offload模式而非完全GPU模式，导致推理性能下降。需要修复模型加载配置，确保模型完全加载到GPU上。

## What Changes
- 修复`qwen_service.py`中的模型加载参数
- 添加`torch_dtype=torch.float16`参数
- 移除不必要的CPU offload配置
- 确保与用户验证的正确加载方式一致

## Impact
- Affected specs: qwen3vl-int4-deployment-integration
- Affected code: `src/web/backend/app/services/qwen_service.py`

## 问题分析

### 当前问题
1. 模型加载时出现错误：`Params4bit.__new__() got an unexpected keyword argument '_is_hf_initialized'`
2. 加载后使用CPU offload模式，而非完全GPU模式
3. 缺少`torch_dtype=torch.float16`参数

### 正确的加载方式（已验证）
```python
from transformers import Qwen3VLForConditionalGeneration, BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)

model = Qwen3VLForConditionalGeneration.from_pretrained(
    "D:/Project/WheatAgent/models/Qwen3-VL-4B-Instruct",
    quantization_config=quantization_config,
    torch_dtype=torch.float16,
    device_map="cuda:0",
    trust_remote_code=True
)
```

### 硬件约束
- GPU: NVIDIA GeForce RTX 3050 Laptop GPU (4.00 GB)
- INT4量化后显存占用: ~2.71 GB
- YOLOv8模型显存占用: ~0.5 GB
- 总显存需求: ~3.2 GB (在4GB限制内)

## ADDED Requirements

### Requirement: GPU INT4量化加载
系统应使用正确的参数配置将Qwen3-VL模型完全加载到GPU上，使用INT4量化。

#### Scenario: 成功加载模型到GPU
- **WHEN** 系统启动并加载Qwen3-VL模型
- **THEN** 模型应完全加载到cuda:0设备
- **AND** 显存占用应约为2.6-2.7GB
- **AND** 日志应显示"GPU模式"而非"CPU offload"

## MODIFIED Requirements

### Requirement: 模型加载参数配置
修改`qwen_service.py`中的`_load_model`方法，添加正确的参数：

**修改前:**
```python
self.model = Qwen3VLForConditionalGeneration.from_pretrained(
    str(self.model_path),
    quantization_config=quantization_config,
    device_map="cuda:0",
    trust_remote_code=True,
    low_cpu_mem_usage=True
)
```

**修改后:**
```python
self.model = Qwen3VLForConditionalGeneration.from_pretrained(
    str(self.model_path),
    quantization_config=quantization_config,
    torch_dtype=torch.float16,
    device_map="cuda:0",
    trust_remote_code=True
)
```

## REMOVED Requirements

### Requirement: CPU offload配置
**Reason**: GPU显存足够支持INT4量化后的模型，无需CPU offload
**Migration**: 移除`low_cpu_mem_usage=True`参数，移除`llm_int8_enable_fp32_cpu_offload=True`配置
