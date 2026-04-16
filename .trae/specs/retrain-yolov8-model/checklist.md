# 验收检查清单

## 训练准备

- [ ] weights 目录已创建
- [ ] conda 环境 wheatagent-py310 可用
- [ ] CUDA/GPU 可用
- [ ] ultralytics 包已安装

## 模型训练

- [ ] YOLOv8 训练成功启动
- [ ] 训练完成 30 epochs
- [ ] 无 NaN/Inf 错误

## 训练输出

- [ ] best.pt 文件已生成
- [ ] last.pt 文件已生成
- [ ] results.csv 已更新

## 性能指标

- [ ] mAP@50 >= 95%
- [ ] mAP@50-95 >= 90%
- [ ] Precision >= 85%
- [ ] Recall >= 90%

## 集成验证

- [ ] YOLO 服务成功加载模型
- [ ] 检测功能正常工作
- [ ] 前端能正确显示检测结果
