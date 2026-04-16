# 前端融合诊断功能问题诊断报告

## 执行摘要

本报告详细分析了前端融合诊断功能中两个关键问题的根本原因：
1. **病灶区域无法正常显示**
2. **诊断结果不准确或错误**

经过全面检查，共发现 **7 个关键问题**，其中 **P0 级别 2 个**、**P1 级别 3 个**、**P2 级别 2 个**。

---

## 问题一：病灶区域无法正常显示

### 根本原因分析

#### 问题 1.1：YOLO 模型权重文件缺失 [P0 - 严重]

**问题描述**：
配置文件 `ai_config.py` 中指定的 YOLO 模型路径为：
```
models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt
```

**实际情况**：
- 目录 `d:\Project\wheatagent\models\wheat_disease_v10_yolov8s\phase1_warmup\` 存在
- 但该目录下 **没有 weights 子目录**
- 整个项目中 **没有任何 .pt 文件**

**影响**：
- YOLOv8 服务无法加载模型
- `yolo_service.py` 中 `is_loaded = False`
- 视觉检测功能完全失效
- 无法生成检测框和标注图像

**代码位置**：
- [ai_config.py:18](file:///d:/Project/wheatagent/src/web/backend/app/core/ai_config.py#L18)
- [yolo_service.py:56-61](file:///d:/Project/wheatagent/src/web/backend/app/services/yolo_service.py#L56-L61)

---

#### 问题 1.2：Mock 服务返回的边界框格式不兼容 [P1 - 高]

**问题描述**：
当 YOLO 模型不可用时，系统自动降级到 Mock 模式。但 Mock 服务返回的边界框格式与前端期望的格式不匹配。

**Mock 服务返回格式** ([mock_service.py:166-174](file:///d:/Project/wheatagent/src/web/backend/app/services/mock_service.py#L166-L174))：
```python
"bounding_boxes": [
    {
        "x": random.randint(50, 200),
        "y": random.randint(50, 200),
        "width": random.randint(100, 300),
        "height": random.randint(100, 300),
        "confidence": round(0.85 + random.uniform(0, 0.1), 3)
    }
]
```

**前端期望格式** ([AnnotatedImage.vue:90-94](file:///d:/Project/wheatagent/src/web/frontend/src/components/diagnosis/AnnotatedImage.vue#L90-L94))：
```typescript
interface Detection {
  class_name: string
  confidence: number
  box?: number[]  // [x1, y1, x2, y2] 格式
}
```

**问题**：
1. Mock 返回 `x, y, width, height` 格式，前端期望 `box: [x1, y1, x2, y2]` 格式
2. Mock 返回 `bounding_boxes` 字段名，前端期望 `roi_boxes` 字段名
3. Mock 返回缺少 `class_name` 字段

**影响**：
- 即使在 Mock 模式下，病灶区域也无法正确显示
- Canvas 绘制逻辑无法解析边界框坐标

---

#### 问题 1.3：fusion_service.py 中 bbox 格式转换问题 [P1 - 高]

**问题描述**：
在 `fusion_service.py` 中，roi_boxes 构建逻辑存在问题：

**代码位置** ([fusion_service.py:318-325](file:///d:/Project/wheatagent/src/web/backend/app/services/fusion_service.py#L318-L325))：
```python
roi_boxes = [
    {
        "box": det.get("bbox") or det.get("box"),
        "class_name": det.get("class_name"),
        "confidence": det.get("confidence")
    }
    for det in detections
]
```

**问题分析**：
1. YOLO 服务返回的 `bbox` 是一个字典：`{"x1": ..., "y1": ..., "x2": ..., "y2": ..., "width": ..., "height": ...}`
2. 前端期望 `box` 是一个数组：`[x1, y1, x2, y2]`
3. 当前代码直接将字典赋值给 `box`，导致格式不匹配

**影响**：
- 前端 AnnotatedImage.vue 无法正确解析边界框
- Canvas 绘制时 `det.box.length >= 4` 检查失败

---

#### 问题 1.4：标注图像 Base64 格式问题 [P2 - 中]

**问题描述**：
`fusion_service.py` 中生成的 Base64 图像缺少数据前缀。

**代码位置** ([fusion_service.py:504-506](file:///d:/Project/wheatagent/src/web/backend/app/services/fusion_service.py#L504-L506))：
```python
base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
return base64_str
```

**前端期望** ([AnnotatedImage.vue:5-10](file:///d:/Project/wheatagent/src/web/frontend/src/components/diagnosis/AnnotatedImage.vue#L5-L10))：
```html
<el-image
  v-if="annotatedImage"
  :src="annotatedImage"
  ...
/>
```

**问题**：
- 返回的 Base64 字符串缺少 `data:image/png;base64,` 前缀
- el-image 组件可能无法正确解析

**影响**：
- 标注图像可能无法正确显示
- 需要前端添加前缀或后端添加前缀

---

## 问题二：诊断结果不准确或错误

### 根本原因分析

#### 问题 2.1：Mock 模式下诊断结果随机生成 [P0 - 严重]

**问题描述**：
由于 YOLO 模型缺失，系统运行在 Mock 模式下，诊断结果完全随机生成。

**代码位置** ([mock_service.py:151-154](file:///d:/Project/wheatagent/src/web/backend/app/services/mock_service.py#L151-L154))：
```python
disease_key = random.choice(list(self.disease_database.keys()))
disease = self.disease_database[disease_key]
confidence = 0.90 + random.uniform(0, 0.08)
```

**影响**：
- 诊断结果与实际图像内容无关
- 置信度虚假偏高 (0.90-0.98)
- 无法提供准确的病害识别

---

#### 问题 2.2：Qwen3-VL 模型可能未正确加载 [P1 - 高]

**问题描述**：
配置文件中 Qwen 模型路径计算可能存在问题。

**代码位置** ([ai_config.py:17](file:///d:/Project/wheatagent/src/web/backend/app/core/ai_config.py#L17))：
```python
QWEN_MODEL_PATH: Path = Path(__file__).parent.parent.parent.parent.parent.parent / "models" / "Qwen3-VL-4B-Instruct"
```

**验证**：
- 当前文件路径：`app/core/ai_config.py`
- 需要 6 层 parent 才能到达项目根目录
- 实际模型目录：`d:\Project\wheatagent\models\Qwen3-VL-4B-Instruct` (存在)

**潜在问题**：
- 如果后端运行目录不是项目根目录，路径计算可能出错
- 需要验证实际运行时的路径是否正确

---

#### 问题 2.3：融合置信度计算逻辑问题 [P2 - 中]

**问题描述**：
融合置信度计算时，如果某个模态不可用，权重分配可能不合理。

**代码位置** ([fusion_service.py:384-425](file:///d:/Project/wheatagent/src/web/backend/app/services/fusion_service.py#L384-L425))：
```python
def _calculate_fused_confidence(
    self,
    visual_conf: float,
    textual_conf: float,
    knowledge_conf: float,
    has_visual: bool,
    has_textual: bool,
    has_knowledge: bool
) -> float:
    weights = {
        "visual": 0.4,
        "textual": 0.35,
        "knowledge": 0.25
    }
    ...
```

**问题**：
- 当视觉模态不可用时（YOLO 未加载），仅使用文本和知识模态
- 权重比例变为 0.35:0.25，可能导致置信度偏低
- 没有针对降级场景的置信度调整策略

---

## 数据流分析

### 完整数据流追踪

```
前端 Diagnosis.vue
    │
    │ FormData: image, symptoms, enable_thinking, use_graph_rag
    ▼
后端 API: POST /diagnosis/fusion
    │
    │ 检查 should_use_mock()
    │   ├── Qwen 服务未加载 → Mock 模式
    │   └── YOLO 服务未加载 → Mock 模式
    ▼
Mock 模式路径:
    │
    │ mock_service.diagnose_by_image()
    │   └── 返回随机诊断结果 + bounding_boxes (格式错误)
    ▼
正常模式路径 (当前不可用):
    │
    │ fusion_service.diagnose()
    │   ├── _extract_visual_features() → YOLO 检测 (模型未加载)
    │   ├── _extract_textual_features() → Qwen 分析
    │   ├── _retrieve_knowledge() → GraphRAG 检索
    │   └── _fuse_features() → 融合结果
    ▼
返回响应:
    {
        "success": true,
        "diagnosis": {
            "disease_name": "...",
            "confidence": 0.xx,
            "roi_boxes": [...],      // 格式可能错误
            "annotated_image": "..."  // 缺少前缀
        }
    }
    │
    ▼
前端 FusionResult.vue
    │
    │ 接收 diagnosis 对象
    │ hasVisualDetection = annotated_image || roi_boxes?.length > 0
    ▼
AnnotatedImage.vue
    │
    │ 尝试解析 roi_boxes
    │   └── det.box 格式不匹配 → 无法绘制
    │ 尝试显示 annotated_image
    │   └── 缺少 Base64 前缀 → 可能无法显示
    ▼
最终结果: 病灶区域无法显示
```

---

## 问题汇总表

| ID | 问题描述 | 严重程度 | 影响范围 | 根因分类 |
|----|---------|---------|---------|---------|
| 1.1 | YOLO 模型权重文件缺失 | P0 | 视觉检测完全失效 | 配置/资源 |
| 1.2 | Mock 服务边界框格式不兼容 | P1 | Mock 模式下病灶不显示 | 数据格式 |
| 1.3 | fusion_service bbox 格式转换错误 | P1 | 正常模式下病灶不显示 | 数据格式 |
| 1.4 | 标注图像 Base64 缺少前缀 | P2 | 标注图像可能不显示 | 数据格式 |
| 2.1 | Mock 模式诊断结果随机生成 | P0 | 诊断结果不准确 | 业务逻辑 |
| 2.2 | Qwen 模型路径可能不正确 | P1 | 文本分析可能失效 | 配置 |
| 2.3 | 融合置信度计算逻辑问题 | P2 | 置信度可能偏低 | 业务逻辑 |

---

## 修复建议

### 紧急修复 (P0)

#### 修复 1.1：获取 YOLO 模型权重

**方案 A - 训练模型**：
```bash
# 使用 vision-training-expert 技能训练 YOLOv8 模型
# 需要准备小麦病害图像数据集
```

**方案 B - 下载预训练模型**：
```bash
# 下载官方预训练权重
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
# 放置到 models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt
```

#### 修复 2.1：改进 Mock 服务

Mock 服务应返回与真实服务兼容的数据格式，并添加明确的 Mock 标识。

---

### 高优先级修复 (P1)

#### 修复 1.2 & 1.3：统一边界框格式

**后端修改** (`fusion_service.py`)：
```python
roi_boxes = [
    {
        "box": [
            det.get("bbox", {}).get("x1", 0),
            det.get("bbox", {}).get("y1", 0),
            det.get("bbox", {}).get("x2", 0),
            det.get("bbox", {}).get("y2", 0)
        ] if det.get("bbox") else det.get("box"),
        "class_name": det.get("class_name"),
        "confidence": det.get("confidence")
    }
    for det in detections
]
```

**Mock 服务修改** (`mock_service.py`)：
```python
"roi_boxes": [
    {
        "box": [x, y, x + width, y + height],
        "class_name": disease["disease_name"],
        "confidence": round(0.85 + random.uniform(0, 0.1), 3)
    }
]
```

---

### 中等优先级修复 (P2)

#### 修复 1.4：添加 Base64 前缀

**后端修改** (`fusion_service.py`)：
```python
return f"data:image/png;base64,{base64_str}"
```

---

## 验证检查清单

完成修复后，请验证以下检查点：

- [ ] YOLO 模型权重文件存在且可加载
- [ ] YOLO 服务 `is_loaded = True`
- [ ] 检测结果包含正确的 bbox 格式
- [ ] roi_boxes 包含 `box: [x1, y1, x2, y2]` 格式
- [ ] annotated_image 包含正确的 Base64 前缀
- [ ] 前端能正确显示标注图像
- [ ] 前端能正确绘制检测框
- [ ] 诊断结果与图像内容相关

---

## 结论

前端融合诊断功能的两个关键问题主要由以下根因导致：

1. **病灶区域无法显示**：YOLO 模型权重缺失导致视觉检测完全失效，同时数据格式不兼容导致即使有数据也无法正确渲染。

2. **诊断结果不准确**：系统运行在 Mock 模式下，诊断结果随机生成，与实际图像内容无关。

**建议优先级**：
1. 首先解决 YOLO 模型权重问题 (P0)
2. 然后修复数据格式兼容性问题 (P1)
3. 最后完善 Base64 前缀等细节问题 (P2)
