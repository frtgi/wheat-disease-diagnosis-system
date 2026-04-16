# 验收检查清单

## 前端代码检查

- [x] Diagnosis.vue 图像上传处理正确
- [x] Diagnosis.vue API 调用参数正确
- [x] FusionResult.vue Props 数据接收正确
- [x] FusionResult.vue 病灶区域展示逻辑正确
- [x] AnnotatedImage.vue 图像加载正确
- [x] AnnotatedImage.vue Canvas 绘制正确

## 后端服务检查

- [x] fusion_service.py YOLO 调用正确
- [x] fusion_service.py 标注图像生成正确
- [x] fusion_service.py roi_boxes 格式正确
- [x] yolo_service.py 检测返回格式正确
- [x] API 端点响应格式正确

## 数据流检查

- [x] 请求参数传递正确
- [x] 检测结果传递正确
- [x] 标注图像传递正确
- [x] 前端展示正确

## 问题诊断报告

- [x] 问题根因已识别
- [x] 问题关联关系已分析
- [x] 修复建议已提供

## 发现的问题清单

### P0 级别问题 (严重)

- [ ] **问题 1.1**: YOLO 模型权重文件缺失
  - 路径：`models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt`
  - 影响：视觉检测完全失效
  - **状态**: 需要手动下载或训练模型

- [ ] **问题 2.1**: Mock 模式诊断结果随机生成
  - 影响：诊断结果与实际图像无关
  - **状态**: Mock 模式是降级方案，需加载真实模型解决

### P1 级别问题 (高)

- [x] **问题 1.2**: Mock 服务边界框格式不兼容
  - Mock 返回 `x, y, width, height`，前端期望 `box: [x1, y1, x2, y2]`
  - **修复**: 已添加 `roi_boxes` 字段，格式正确

- [x] **问题 1.3**: fusion_service.py bbox 格式转换错误
  - 直接将字典赋值给 box 字段
  - **修复**: 已正确转换字典格式为数组格式

- [x] **问题 2.2**: Qwen 模型路径验证
  - **状态**: 路径已验证正确，模型目录存在

### P2 级别问题 (中)

- [x] **问题 1.4**: 标注图像 Base64 缺少前缀
  - 缺少 `data:image/png;base64,` 前缀
  - **修复**: 已添加前缀

- [x] **问题 2.3**: 融合置信度计算逻辑问题
  - 降级场景下权重分配不合理
  - **修复**: 已添加降级因子 (degradation_factor)
