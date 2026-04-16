# CUDA版PyTorch + BitsAndBytes安装与INT4量化部署 Checklist

## 环境准备

### 当前环境检查
- [ ] PyTorch版本已确认
- [ ] CUDA支持状态已确认
- [ ] NVIDIA驱动版本已确认
- [ ] GPU设备状态正常

### PyTorch安装
- [ ] CPU版PyTorch已卸载
- [ ] GPU版PyTorch安装成功
- [ ] torchvision GPU版安装成功
- [ ] torchaudio GPU版安装成功
- [ ] `torch.cuda.is_available()` 返回 True

### BitsAndBytes安装
- [ ] bitsandbytes库安装成功
- [ ] 可成功导入 `import bitsandbytes`
- [ ] `BitsAndBytesConfig` 可用

## 模型配置

### 量化配置
- [ ] qwen_service.py配置正确
- [ ] BitsAndBytesConfig参数正确
  - [ ] load_in_4bit = True
  - [ ] bnb_4bit_quant_type = "nf4"
  - [ ] bnb_4bit_compute_dtype = torch.float16
  - [ ] bnb_4bit_use_double_quant = True
- [ ] 设备映射配置正确（device_map="auto"）

### 模型加载
- [ ] INT4量化加载成功
- [ ] 模型加载到GPU
- [ ] 显存占用 < 4GB
- [ ] 加载时间记录完整

## 服务部署

### 服务启动
- [ ] 后端服务启动成功
- [ ] 模型加载日志正常
- [ ] 无错误或警告信息
- [ ] 服务端口正常监听

### API测试
- [ ] 用户认证API正常
- [ ] 图像诊断API正常
- [ ] 文本诊断API正常
- [ ] 知识库API正常
- [ ] 统计API正常

### 功能验证
- [ ] 文本推理功能正常
- [ ] 图像理解功能正常
- [ ] 多模态诊断功能正常
- [ ] 输出质量符合预期

## 性能验证

### GPU性能
- [ ] 首次推理延迟已记录
- [ ] 平均推理延迟已记录
- [ ] GPU显存占用已记录
- [ ] GPU利用率已记录

### 性能对比
- [ ] CPU/GPU性能对比数据完整
- [ ] 性能提升百分比已计算
- [ ] 性能报告已生成

## 文档输出

### 部署报告
- [ ] 安装步骤记录完整
- [ ] 配置变更记录完整
- [ ] 测试结果记录完整
- [ ] 性能数据记录完整

### 项目文档更新
- [ ] 环境依赖文档更新
- [ ] 部署文档更新
- [ ] 配置文档更新
