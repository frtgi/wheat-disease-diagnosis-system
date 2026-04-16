# Checklist

## 环境验证

- [ ] transformers 库版本 >= 4.57.0 或已从 GitHub 源码安装
- [ ] `Qwen3VLForConditionalGeneration` 类可正常导入
- [ ] qwen-vl-utils 已安装

## 模型加载验证

- [ ] 使用 `Qwen3VLForConditionalGeneration` 加载模型成功
- [ ] 无 `ignore_mismatched_sizes` 参数
- [ ] 无架构不匹配警告（"You are using a model of type qwen3_vl to instantiate a model of type qwen2_vl"）
- [ ] 模型加载日志显示 "Qwen3VLForConditionalGeneration" 或类似信息

## 多模态推理验证

- [ ] 图像诊断功能正常工作
- [ ] 多模态诊断（图像+文本）功能正常工作
- [ ] 无张量维度不匹配错误
- [ ] 输出格式符合预期（包含 disease_name, confidence, symptoms 等字段）

## 文本诊断验证

- [ ] 文本诊断功能正常工作
- [ ] 降级模式正常工作（如果多模态加载失败）

## 代码质量

- [ ] 添加了函数级中文注释
- [ ] 错误处理逻辑完善
- [ ] 日志输出清晰
- [ ] 代码符合项目规范

## API 测试

- [ ] POST /api/v1/diagnosis/text 返回正确结果
- [ ] POST /api/v1/diagnosis/image 返回正确结果
- [ ] POST /api/v1/diagnosis/multimodal 返回正确结果
