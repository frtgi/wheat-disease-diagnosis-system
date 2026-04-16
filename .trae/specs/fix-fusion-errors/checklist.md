# Checklist

## 错误修复验证

- [x] GraphRAG 服务初始化成功，无 "No module named 'src'" 错误
- [x] Qwen3-VL 诊断方法调用成功，无 "'generate' attribute" 错误
- [x] 仅文本诊断成功，无 "buffer API" 错误

## 功能验证

- [x] 后端服务启动成功
- [x] AI 模型加载成功 (YOLOv8 + Qwen3-VL)
- [x] 融合诊断 API 正常响应
- [x] 仅文本诊断返回正确结果
- [x] 仅图像诊断返回正确结果
- [x] 图像+文本联合诊断返回正确结果

## 日志验证

- [x] 启动日志无 ERROR 级别错误
- [x] 启动日志无 WARNING 级别警告（除已知警告外）
- [x] 诊断请求日志正常
