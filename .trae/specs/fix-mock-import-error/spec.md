# 修复 Mock 模块导入错误 Spec

## Why
后端服务运行时无法导入 `tests.mocks.diagnosis_mock` 模块，因为 `tests` 目录在项目根目录下，而后端服务的工作目录是 `src/web/backend`。这导致 Mock 模式诊断失败，返回 500 错误。

## What Changes
- 在 `src/web/backend/app/services/` 目录下创建 `mock_service.py` 文件
- 修改 `ai_diagnosis.py` 中的导入路径，- 移除对 `tests.mocks` 的依赖

## Impact
- Affected code: `src/web/backend/app/api/v1/ai_diagnosis.py`
- New file: `src/web/backend/app/services/mock_service.py`

## ADDED Requirements

### Requirement: Mock 服务模块
系统 SHALL 在 backend 目录下提供独立的 Mock 服务模块，无需依赖外部 tests 目录。

#### Scenario: Mock 模式诊断成功
- **WHEN** 后端服务启用 Mock 模式
- **THEN** 应能正确导入 MockDiagnosisService
- **AND** 诊断请求返回正确的模拟结果

## MODIFIED Requirements

### Requirement: 导入路径修改
原导入路径：
```python
from tests.mocks.diagnosis_mock import MockDiagnosisService
```

新导入路径：
```python
from app.services.mock_service import MockDiagnosisService
```
