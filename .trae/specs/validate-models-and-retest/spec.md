# 模型验证与完整测试 Spec

## Why
模型文件已存在（Qwen3-VL-4B-Instruct 和 YOLOv8），需要验证模型能否正确加载，并重新运行完整的端到端测试，确保所有功能正常工作。

## What Changes
- 检查模型文件完整性
- 验证模型路径配置
- 启动服务并验证模型加载
- 运行完整端到端测试
- 生成验证报告

## Impact
- **Affected specs**: e2e-testing-and-fixes（验证阶段）
- **Affected code**: 
  - `app/services/qwen_service.py` - Qwen 模型加载
  - `app/services/yolo_service.py` - YOLO 模型加载
  - `app/core/ai_config.py` - 模型路径配置
  - `tests/test_e2e_simple.py` - 测试脚本

## ADDED Requirements

### Requirement: 模型文件验证
系统 SHALL 验证模型文件完整性：
- 检查 Qwen3-VL-4B-Instruct 模型文件
- 检查 YOLOv8 模型文件
- 验证配置文件存在

#### Scenario: 模型验证成功
- **WHEN** 检查模型目录
- **THEN** 所有必需文件存在（config.json, model*.safetensors, tokenizer 等）

### Requirement: 模型加载验证
系统 SHALL 验证模型能够成功加载：
- 启动服务
- 检查 AI 健康状态
- 确认 `is_loaded: true`

#### Scenario: 模型加载成功
- **WHEN** 访问 `GET /api/v1/health/ai`
- **THEN** 返回 `is_loaded: true` 和模型信息

### Requirement: 完整测试执行
系统 SHALL 执行完整的端到端测试：
- 测试所有 API 端点
- 执行多模态诊断测试
- 测试缓存功能
- 验证性能指标

#### Scenario: 测试全部通过
- **WHEN** 运行 `python tests/test_e2e_simple.py`
- **THEN** 所有测试通过（通过率 100%）

## MODIFIED Requirements

### Requirement: 模型路径配置
**原配置**: 
```python
model_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "Qwen3-VL-4B-Instruct"
```

**修改后**: 
验证路径正确性，确保指向实际模型目录

## REMOVED Requirements
无

## 验收标准

### 模型验证
- [ ] Qwen3-VL-4B-Instruct 文件完整
- [ ] YOLOv8 模型文件存在
- [ ] 配置文件正确

### 模型加载
- [ ] Qwen 模型加载成功（is_loaded: true）
- [ ] YOLO 模型加载成功（is_loaded: true）
- [ ] 无启动错误

### 测试执行
- [ ] API 通过率 100%
- [ ] 诊断成功率 > 95%
- [ ] 性能指标达标（p95 < 3000ms）
- [ ] 缓存命中率 > 50%（重复请求）

### 交付物
1. `docs/MODEL_VERIFICATION_REPORT.md` - 模型验证报告
2. `docs/FINAL_E2E_TEST_REPORT.md` - 最终测试报告
3. `tests/final_e2e_results.json` - 测试结果
