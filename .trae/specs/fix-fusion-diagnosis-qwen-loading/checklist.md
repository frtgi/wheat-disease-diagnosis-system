# 修复融合诊断和Qwen加载问题 Checklist

## GraphRAG 引擎

- [x] graphrag_engine.py 语法错误已修复
- [x] GraphRAG 引擎初始化成功
- [x] 后端启动无 GraphRAG 相关警告

## Qwen3-VL 模型

- [x] Qwen3-VL 模型加载到 GPU
- [x] GPU 显存占用 > 2GB
- [x] 模型使用 INT4 量化模式

## 融合诊断 API

- [x] POST /api/v1/diagnosis/fusion 返回正确结果
- [x] 返回结果包含 disease_name
- [x] 返回结果包含 confidence
- [x] 返回结果包含 knowledge_links

## 整体验证

- [x] 后端启动无错误
- [x] 所有 AI 模型加载成功
- [x] 前端融合诊断功能正常
