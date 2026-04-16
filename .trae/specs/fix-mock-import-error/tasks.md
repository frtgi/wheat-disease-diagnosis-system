# Tasks

- [x] Task 1: 创建 Mock 服务模块
  - [x] 在 `src/web/backend/app/services/` 目录下创建 `mock_service.py`
  - [x] 将 `tests/mocks/diagnosis_mock.py` 的内容复制到新文件
  - [x] 添加中文注释

- [x] Task 2: 修改导入路径
  - [x] 修改 `ai_diagnosis.py` 中的导入路径
  - [x] 将 `from tests.mocks.diagnosis_mock import` 改为 `from app.services.mock_service import`

- [x] Task 3: 验证修复
  - [x] 重启后端服务
  - [x] 测试融合诊断 API

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
