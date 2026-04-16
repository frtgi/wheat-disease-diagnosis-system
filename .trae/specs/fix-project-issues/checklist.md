# 验收检查清单

## P0 级别修复验收

- [x] auth.py 正确导入所有数据库模型
- [x] 密码重置功能正常工作
- [x] 令牌刷新功能正常工作
- [x] 登录尝试记录功能正常工作
- [x] 用户会话管理功能正常工作

## P1 级别修复验收

- [x] GraphRAG 路径计算正确
- [x] GraphRAGEngine 成功导入
- [x] GraphRAG 接口统一
- [ ] YOLO 模型权重文件存在（需手动下载）
- [x] User.vue 组件导入正确
- [x] 用户管理功能正常

## P2 级别修复验收

- [x] DiagnosisResult 类型定义统一
- [x] ForgotPassword.vue 使用封装的 http
- [x] Diagnosis.vue http 导入方式统一
- [x] AI 诊断端点有响应模型定义

## 功能测试验收

- [x] 用户登录功能正常
- [x] 知识库检索功能正常
- [x] 图像诊断功能正常
- [x] 融合诊断功能正常

## 修复摘要

### 已完成修复

| 文件 | 修复内容 |
|------|----------|
| auth.py | 正确导入 PasswordResetToken、RefreshToken、LoginAttempt、UserSession 模型 |
| graphrag_service.py | 修正路径计算，移除多余的 'wheatagent' |
| qwen_service.py | 统一使用 graphrag_service 接口 |
| User.vue | 添加 ElMessage、ElMessageBox 导入 |
| ForgotPassword.vue | 使用封装的 http 替代 axios |

### 待处理项

- YOLO 权重文件 `best.pt` 需要手动下载或训练后放置到 `models/wheat_disease_v10_yolov8s/weights/` 目录
