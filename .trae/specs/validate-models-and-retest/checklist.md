# 模型验证与完整测试 Checklist

## 模型文件检查

### Qwen3-VL-4B-Instruct 模型
- [ ] config.json 存在
- [ ] configuration.json 存在
- [ ] generation_config.json 存在
- [ ] model-00001-of-00002.safetensors 存在
- [ ] model-00002-of-00002.safetensors 存在
- [ ] model.safetensors.index.json 存在
- [ ] tokenizer.json 存在
- [ ] tokenizer_config.json 存在
- [ ] vocab.json 存在
- [ ] merges.txt 存在
- [ ] chat_template.json 存在

### YOLOv8 模型
- [ ] phase1_warmup 目录存在
- [ ] args.yaml 配置文件存在
- [ ] 训练权重文件存在（best.pt 或 last.pt）
- [ ] 训练结果文件存在（results.png, results.csv）

## 配置验证

### AI 配置检查
- [ ] app/core/ai_config.py 中的模型路径正确
- [ ] QWEN_MODEL_PATH 指向 models/Qwen3-VL-4B-Instruct
- [ ] YOLO_MODEL_PATH 指向 models/wheat_disease_v10_yolov8s
- [ ] .env 文件存在且配置正确

## 服务启动

### 启动验证
- [ ] 服务成功启动在端口 8000
- [ ] 启动日志正常
- [ ] 无模型加载错误
- [ ] 数据库连接成功

### 健康检查
- [ ] GET /health 返回 200
- [ ] GET /api/v1/health 返回服务状态
- [ ] GET /api/v1/health/ai 返回 AI 服务状态

## 模型加载验证

### AI 健康状态
- [ ] Qwen 模型 is_loaded: true
- [ ] YOLO 模型 is_loaded: true
- [ ] 模型信息完整
- [ ] 无错误信息

### 显存使用（如有 GPU）
- [ ] nvidia-smi 显示 GPU 正常
- [ ] 显存占用在合理范围
- [ ] 无显存不足错误

## 端到端测试

### 测试执行
- [ ] python tests/test_e2e_simple.py 成功运行
- [ ] 执行至少 10 次诊断请求
- [ ] 生成测试结果 JSON

### API 功能测试
- [ ] GET /health - 通过
- [ ] GET /api/v1/health/ai - 通过
- [ ] POST /api/v1/diagnosis/multimodal - 通过
- [ ] GET /api/v1/diagnosis/cache/stats - 通过
- [ ] GET /api/v1/metrics/ - 通过
- [ ] GET /api/v1/metrics/alerts - 通过
- [ ] GET /api/v1/logs/statistics - 通过

### 性能测试
- [ ] 成功请求数 = 10/10
- [ ] 平均延迟 < 3000ms
- [ ] P50 延迟 < 2000ms
- [ ] P95 延迟 < 3000ms
- [ ] P99 延迟 < 5000ms

### 缓存测试
- [ ] 第一次请求缓存未命中
- [ ] 第二次请求缓存命中
- [ ] 缓存命中率 > 50%

## 详细功能测试

### 多模态诊断
- [ ] 图像 + 文本诊断成功
- [ ] 返回诊断结果完整
- [ ] 置信度合理
- [ ] 推理链完整（Thinking 模式）

### 缓存功能
- [ ] 图像哈希缓存正常
- [ ] 语义缓存正常
- [ ] 缓存统计准确

## 报告生成

### 模型验证报告
- [ ] docs/MODEL_VERIFICATION_REPORT.md 创建
- [ ] 模型文件清单完整
- [ ] 模型加载状态记录
- [ ] 问题和建议记录

### 最终测试报告
- [ ] docs/FINAL_E2E_TEST_REPORT.md 创建
- [ ] 测试结果汇总
- [ ] 性能指标分析
- [ ] 对比分析（修复前后）

### 测试结果文件
- [ ] tests/final_e2e_results.json 保存
- [ ] JSON 格式正确
- [ ] 包含所有测试用例结果

## 最终验收

### 验收标准
- [ ] 所有 Critical 检查项通过
- [ ] 所有 High 检查项通过
- [ ] API 通过率 100%
- [ ] 诊断成功率 > 95%
- [ ] 性能指标全部达标

### 签署确认
- [ ] 测试执行人签字
- [ ] 验证人签字
- [ ] 批准人签字

## 问题记录

### 发现的问题
| 问题 ID | 描述 | 严重级别 | 状态 |
|--------|------|----------|------|
| | | | |

### 解决方案
| 问题 ID | 解决方案 | 负责人 | 完成时间 |
|--------|----------|--------|----------|
| | | | |

---

**检查人**: ___________  
**检查日期**: ___________  
**检查结果**: ☐ 通过  ☐ 不通过

**备注**:
_________________________________
_________________________________
