# 关键类与函数文档

## 视觉模块

### VisionEngine 类

**位置**：`src/vision/vision_engine.py`

**用途**：视觉引擎的核心类，负责图像处理和病害检测。

**主要方法**：
- `__init__(self, model_path)`：初始化视觉引擎，加载模型
  - **参数**：`model_path` - 模型文件路径
  - **返回值**：无

- `process_image(self, image)`：处理图像并检测病害
  - **参数**：`image` - 输入图像（PIL 图像或 numpy 数组）
  - **返回值**：检测结果，包含病害类型、位置和置信度

- `preprocess(self, image)`：图像预处理
  - **参数**：`image` - 输入图像
  - **返回值**：预处理后的图像

- `postprocess(self, results)`：检测结果后处理
  - **参数**：`results` - 原始检测结果
  - **返回值**：优化后的检测结果

### EnhancedYOLO 类

**位置**：`src/vision/enhanced_yolo.py`

**用途**：增强版 YOLO 模型，用于小麦病害检测。

**主要方法**：
- `__init__(self, model_path)`：初始化增强版 YOLO 模型
  - **参数**：`model_path` - 模型文件路径
  - **返回值**：无

- `predict(self, image)`：进行病害检测
  - **参数**：`image` - 输入图像
  - **返回值**：检测结果

- `get_anchors(self)`：获取锚框配置
  - **参数**：无
  - **返回值**：锚框配置

## 融合模块

### FusionEngine 类

**位置**：`src/fusion/fusion_engine.py`

**用途**：多模态融合引擎，整合图像和文本信息。

**主要方法**：
- `__init__(self)`：初始化融合引擎
  - **参数**：无
  - **返回值**：无

- `fuse(self, visual_features, text_features)`：融合视觉和文本特征
  - **参数**：
    - `visual_features` - 视觉特征
    - `text_features` - 文本特征
  - **返回值**：融合后的特征

- `get_attention_weights(self, visual_features, text_features)`：计算注意力权重
  - **参数**：
    - `visual_features` - 视觉特征
    - `text_features` - 文本特征
  - **返回值**：注意力权重

### KADFormer 类

**位置**：`src/fusion/kad_former.py`

**用途**：KAD-Former 融合模型，结合知识图谱进行多模态融合。

**主要方法**：
- `__init__(self, config)`：初始化 KAD-Former 模型
  - **参数**：`config` - 模型配置
  - **返回值**：无

- `forward(self, visual_features, text_features, graph_embeddings)`：前向传播
  - **参数**：
    - `visual_features` - 视觉特征
    - `text_features` - 文本特征
    - `graph_embeddings` - 知识图谱嵌入
  - **返回值**：融合特征

## 诊断模块

### DiagnosisEngine 类

**位置**：`src/diagnosis/diagnosis_engine.py`

**用途**：诊断引擎，基于融合信息进行病害诊断。

**主要方法**：
- `__init__(self)`：初始化诊断引擎
  - **参数**：无
  - **返回值**：无

- `diagnose(self, fused_features)`：进行病害诊断
  - **参数**：`fused_features` - 融合特征
  - **返回值**：诊断结果，包含病害类型、置信度和建议

- `generate_report(self, diagnosis_result)`：生成诊断报告
  - **参数**：`diagnosis_result` - 诊断结果
  - **返回值**：诊断报告

### ReportGenerator 类

**位置**：`src/diagnosis/report_generator.py`

**用途**：生成诊断报告。

**主要方法**：
- `__init__(self)`：初始化报告生成器
  - **参数**：无
  - **返回值**：无

- `generate(self, diagnosis_result)`：生成报告
  - **参数**：`diagnosis_result` - 诊断结果
  - **返回值**：格式化的诊断报告

## 认知模块

### CognitionEngine 类

**位置**：`src/cognition/cognition_engine.py`

**用途**：认知引擎，负责文本理解和推理。

**主要方法**：
- `__init__(self, model_name)`：初始化认知引擎
  - **参数**：`model_name` - 模型名称
  - **返回值**：无

- `process_text(self, text)`：处理文本
  - **参数**：`text` - 输入文本
  - **返回值**：处理后的文本表示

- `reason(self, context, query)`：基于上下文进行推理
  - **参数**：
    - `context` - 上下文信息
    - `query` - 查询
  - **返回值**：推理结果

### QwenEngine 类

**位置**：`src/cognition/qwen_engine.py`

**用途**：Qwen 大语言模型接口。

**主要方法**：
- `__init__(self, model_path)`：初始化 Qwen 模型
  - **参数**：`model_path` - 模型路径
  - **返回值**：无

- `generate(self, prompt)`：生成文本
  - **参数**：`prompt` - 提示文本
  - **返回值**：生成的文本

- `embed(self, text)`：生成文本嵌入
  - **参数**：`text` - 输入文本
  - **返回值**：文本嵌入

## 知识图谱模块

### GraphEngine 类

**位置**：`src/graph/graph_engine.py`

**用途**：知识图谱引擎，管理知识图谱数据。

**主要方法**：
- `__init__(self, neo4j_uri, username, password)`：初始化图谱引擎
  - **参数**：
    - `neo4j_uri` - Neo4j 数据库 URI
    - `username` - 用户名
    - `password` - 密码
  - **返回值**：无

- `query(self, cypher)`：执行 Cypher 查询
  - **参数**：`cypher` - Cypher 查询语句
  - **返回值**：查询结果

- `add_node(self, label, properties)`：添加节点
  - **参数**：
    - `label` - 节点标签
    - `properties` - 节点属性
  - **返回值**：节点 ID

- `add_relationship(self, start_node, end_node, relationship_type, properties)`：添加关系
  - **参数**：
    - `start_node` - 起始节点 ID
    - `end_node` - 结束节点 ID
    - `relationship_type` - 关系类型
    - `properties` - 关系属性
  - **返回值**：关系 ID

### KnowledgeGraphBuilder 类

**位置**：`src/graph/knowledge_graph_builder.py`

**用途**：知识图谱构建器，从数据中构建知识图谱。

**主要方法**：
- `__init__(self, graph_engine)`：初始化构建器
  - **参数**：`graph_engine` - 图谱引擎实例
  - **返回值**：无

- `build_from_csv(self, csv_file)`：从 CSV 文件构建知识图谱
  - **参数**：`csv_file` - CSV 文件路径
  - **返回值**：构建结果

- `build_from_text(self, text)`：从文本构建知识图谱
  - **参数**：`text` - 输入文本
  - **返回值**：构建结果

## Web 模块

### FastAPI 应用

**位置**：`src/web/backend/app/main.py`

**用途**：后端 API 服务的入口点。

**主要路由**：
- `POST /api/diagnosis`：进行病害诊断
  - **参数**：
    - `image` - 上传的图像文件
    - `description` - 病害描述（可选）
  - **返回值**：诊断结果

- `GET /api/knowledge/{disease_id}`：获取病害知识
  - **参数**：`disease_id` - 病害 ID
  - **返回值**：病害知识信息

- `POST /api/auth/login`：用户登录
  - **参数**：
    - `username` - 用户名
    - `password` - 密码
  - **返回值**：认证令牌

### Vue 组件

**位置**：`src/web/frontend/src/components/`

**主要组件**：
- `Diagnosis.vue`：诊断页面组件
- `Knowledge.vue`：知识图谱页面组件
- `Records.vue`：历史记录页面组件

## 数据模块

### DataLayers 类

**位置**：`src/data/data_layers.py`

**用途**：数据层，负责数据的加载和管理。

**主要方法**：
- `__init__(self, data_dir)`：初始化数据层
  - **参数**：`data_dir` - 数据目录
  - **返回值**：无

- `load_dataset(self, dataset_name)`：加载数据集
  - **参数**：`dataset_name` - 数据集名称
  - **返回值**：数据集对象

- `get_batch(self, batch_size)`：获取数据批次
  - **参数**：`batch_size` - 批次大小
  - **返回值**：数据批次

### AugmentationEngine 类

**位置**：`src/data/augmentation_engine.py`

**用途**：数据增强引擎，生成增强数据。

**主要方法**：
- `__init__(self, config)`：初始化增强引擎
  - **参数**：`config` - 增强配置
  - **返回值**：无

- `augment(self, image)`：增强图像
  - **参数**：`image` - 输入图像
  - **返回值**：增强后的图像

- `augment_batch(self, images)`：批量增强图像
  - **参数**：`images` - 图像批次
  - **返回值**：增强后的图像批次

## 输入模块

### InputParser 类

**位置**：`src/input/input_parser.py`

**用途**：输入解析器，解析和处理输入数据。

**主要方法**：
- `__init__(self)`：初始化输入解析器
  - **参数**：无
  - **返回值**：无

- `parse_image(self, image_file)`：解析图像输入
  - **参数**：`image_file` - 图像文件
  - **返回值**：解析后的图像

- `parse_text(self, text)`：解析文本输入
  - **参数**：`text` - 文本输入
  - **返回值**：解析后的文本

- `parse_json(self, json_data)`：解析 JSON 输入
  - **参数**：`json_data` - JSON 数据
  - **返回值**：解析后的数据结构

### InputValidator 类

**位置**：`src/input/input_validator.py`

**用途**：输入验证器，验证输入数据的有效性。

**主要方法**：
- `__init__(self)`：初始化输入验证器
  - **参数**：无
  - **返回值**：无

- `validate_image(self, image)`：验证图像输入
  - **参数**：`image` - 图像输入
  - **返回值**：验证结果（布尔值）

- `validate_text(self, text)`：验证文本输入
  - **参数**：`text` - 文本输入
  - **返回值**：验证结果（布尔值）

## 记忆模块

### CaseMemory 类

**位置**：`src/memory/case_memory.py`

**用途**：病例记忆管理，存储和检索病例记录。

**主要方法**：
- `__init__(self, storage_dir)`：初始化病例记忆
  - **参数**：`storage_dir` - 存储目录
  - **返回值**：无

- `store_case(self, case_data)`：存储病例记录
  - **参数**：`case_data` - 病例数据
  - **返回值**：病例 ID

- `retrieve_case(self, case_id)`：检索病例记录
  - **参数**：`case_id` - 病例 ID
  - **返回值**：病例数据

- `search_cases(self, query)`：搜索病例
  - **参数**：`query` - 搜索查询
  - **返回值**：匹配的病例列表

### FeedbackHandler 类

**位置**：`src/memory/feedback_handler.py`

**用途**：反馈处理器，处理用户反馈。

**主要方法**：
- `__init__(self)`：初始化反馈处理器
  - **参数**：无
  - **返回值**：无

- `process_feedback(self, feedback_data)`：处理反馈数据
  - **参数**：`feedback_data` - 反馈数据
  - **返回值**：处理结果

- `get_feedback_stats(self)`：获取反馈统计信息
  - **参数**：无
  - **返回值**：反馈统计信息

## 部署模块

### Quantization 类

**位置**：`src/deploy/quantization.py`

**用途**：模型量化，优化模型大小和推理速度。

**主要方法**：
- `__init__(self)`：初始化量化器
  - **参数**：无
  - **返回值**：无

- `quantize(self, model, quantization_type)`：量化模型
  - **参数**：
    - `model` - 原始模型
    - `quantization_type` - 量化类型（如 int8、int4）
  - **返回值**：量化后的模型

- `evaluate_quantization(self, original_model, quantized_model, test_data)`：评估量化效果
  - **参数**：
    - `original_model` - 原始模型
    - `quantized_model` - 量化后的模型
    - `test_data` - 测试数据
  - **返回值**：量化评估结果

### EdgeOptimizer 类

**位置**：`src/deploy/edge_optimizer.py`

**用途**：边缘部署优化，为边缘设备优化模型。

**主要方法**：
- `__init__(self)`：初始化边缘优化器
  - **参数**：无
  - **返回值**：无

- `optimize(self, model, device_type)`：优化模型
  - **参数**：
    - `model` - 原始模型
    - `device_type` - 设备类型
  - **返回值**：优化后的模型

- `export(self, model, export_path)`：导出优化后的模型
  - **参数**：
    - `model` - 优化后的模型
    - `export_path` - 导出路径
  - **返回值**：导出结果

## 工具函数

### ConfigManager 类

**位置**：`src/utils/config_manager.py`

**用途**：配置管理，加载和管理配置文件。

**主要方法**：
- `__init__(self, config_file)`：初始化配置管理器
  - **参数**：`config_file` - 配置文件路径
  - **返回值**：无

- `get_config(self, section, key)`：获取配置值
  - **参数**：
    - `section` - 配置 section
    - `key` - 配置键
  - **返回值**：配置值

- `update_config(self, section, key, value)`：更新配置
  - **参数**：
    - `section` - 配置 section
    - `key` - 配置键
    - `value` - 新值
  - **返回值**：更新结果

### Logger 类

**位置**：`src/utils/logger.py`

**用途**：日志管理，记录系统日志。

**主要方法**：
- `__init__(self, name, log_file)`：初始化日志器
  - **参数**：
    - `name` - 日志器名称
    - `log_file` - 日志文件路径
  - **返回值**：无

- `info(self, message)`：记录信息日志
  - **参数**：`message` - 日志消息
  - **返回值**：无

- `error(self, message, exc_info=False)`：记录错误日志
  - **参数**：
    - `message` - 错误消息
    - `exc_info` - 是否包含异常信息
  - **返回值**：无
