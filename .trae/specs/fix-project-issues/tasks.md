# Tasks

## Phase 1: P0 级别问题修复

- [x] **任务 1: 修复 auth.py 模型导入**
  - [x] 子任务 1.1: 检查 models/user.py 中的模型定义
  - [x] 子任务 1.2: 修复 auth.py 中的模型导入语句
  - [x] 子任务 1.3: 验证认证功能正常

## Phase 2: P1 级别问题修复

- [x] **任务 2: 修复 GraphRAG 路径计算**
  - [x] 子任务 2.1: 修正 graphrag_service.py 中的路径计算逻辑
  - [x] 子任务 2.2: 验证 GraphRAGEngine 导入成功

- [x] **任务 3: 统一 GraphRAG 接口**
  - [x] 子任务 3.1: 检查 qwen_service.py 和 fusion_service.py 的调用方式
  - [x] 子任务 3.2: 统一使用 graphrag_service 接口

- [x] **任务 4: 验证 YOLO 权重文件**
  - [x] 子任务 4.1: 检查 YOLO 模型权重文件是否存在
  - [x] 子任务 4.2: 权重文件不存在，配置路径需要更新（已知问题）

- [x] **任务 5: 修复 User.vue 组件导入**
  - [x] 子任务 5.1: 添加 ElMessage 和 ElMessageBox 导入
  - [x] 子任务 5.2: 验证用户管理功能正常

## Phase 3: P2 级别问题修复

- [x] **任务 6: 修复前端类型定义重复**
  - [x] 子任务 6.1: 统一 DiagnosisResult 类型定义
  - [x] 子任务 6.2: 移除重复的类型定义

- [x] **任务 7: 统一前端 API 调用方式**
  - [x] 子任务 7.1: 修复 ForgotPassword.vue 使用封装的 http
  - [x] 子任务 7.2: 统一 Diagnosis.vue 的 http 导入方式

- [x] **任务 8: 添加 AI 诊断端点响应模型**
  - [x] 子任务 8.1: 在 schemas 中添加诊断响应模型
  - [x] 子任务 8.2: 更新 API 端点使用响应模型

# Task Dependencies

```
任务 1 (auth修复) ──┐
                   │
任务 2 (GraphRAG路径) ──┼──► 任务 3 (接口统一)
                   │
任务 4 (YOLO验证) ──┤
                   │
任务 5 (User.vue) ──┤
                   │
任务 6-8 (P2修复) ──┘
```

## 并行执行组

- **Group A (P0修复)**: 任务 1 ✅
- **Group B (P1修复)**: 任务 2、任务 3、任务 4、任务 5 ✅
- **Group C (P2修复)**: 任务 6、任务 7、任务 8 ✅

## 执行策略

1. **第一阶段**: 执行 Group A (P0) ✅
2. **第二阶段**: 并行执行 Group B (P1) ✅
3. **第三阶段**: 并行执行 Group C (P2) ✅

## 执行结果

所有任务已完成。

### 已修复的问题

| # | 问题 | 状态 |
|---|------|------|
| 1 | requirements.txt 缺少核心依赖 | ⏭️ 跳过（conda 环境已安装） |
| 2 | auth.py 模型导入为空占位符 | ✅ 已修复 |
| 3 | GraphRAG 路径计算错误 | ✅ 已修复 |
| 4 | GraphRAG 接口不统一 | ✅ 已修复 |
| 5 | YOLO 权重文件不存在 | ⚠️ 已知问题，需手动下载 |
| 6 | User.vue 缺少组件导入 | ✅ 已修复 |
| 7 | ForgotPassword 直接使用 axios | ✅ 已修复 |

### 待处理问题

- YOLO 权重文件 `best.pt` 不存在于配置路径，需要手动下载或训练
