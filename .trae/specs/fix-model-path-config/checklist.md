# 修复模型路径配置 Checklist

## 问题分析阶段

### 路径验证
- [x] 确认 ai_config.py 的位置：`app/core/ai_config.py`
- [x] 计算 parent.parent.parent 的实际路径
- [x] 验证 models 目录是否存在于计算结果
- [x] 检查实际模型位置：`d:\Project\WheatAgent\models\`
- [x] 列出模型子目录（Qwen3-VL-4B-Instruct, wheat_disease_v10_yolov8s）

### 原因分析
- [x] 记录当前配置路径
- [x] 记录实际模型路径
- [x] 分析路径差异原因（parent 层级错误）
- [x] 确定正确的 parent 层级（6 层）

## 代码修复阶段

### ai_config.py 修改
- [x] 修正 QWEN_MODEL_PATH 的 parent 层级（3层 → 6层）
- [x] 修正 YOLO_MODEL_PATH 的 parent 层级（3层 → 6层）
- [x] 添加路径存在性验证
- [x] 添加启动时路径信息输出
- [x] 验证修改后的路径指向正确位置

### ai_preloader.py 修改
- [x] 从 AIConfig 实例获取路径（避免导入错误）
- [x] 移除或修正模块级常量定义
- [x] 添加加载前路径验证
- [x] 改进错误信息输出
- [x] 启用 INT4 量化加载 Qwen 模型

### qwen_service.py 修改
- [x] 修正路径计算（5层 → 6层）
- [x] 使用 BitsAndBytesConfig 配置 4-bit 量化
- [x] 修复 load_in_4bit 参数传递方式

### yolo_service.py 修改
- [x] 添加 `_warmup()` 方法
- [x] 支持文件路径加载（不仅仅是目录）
- [x] 添加 Callable 类型导入

## 测试验证阶段

### 服务重启
- [x] 停止当前运行的服务
- [x] 重新启动 uvicorn 服务
- [x] 观察启动日志中的路径信息
- [x] 确认无路径相关错误

### 模型加载验证
- [x] 检查 Qwen 模型加载状态（is_loaded: true）
- [x] 检查 YOLO 模型加载状态（is_loaded: true）
- [x] 验证显存占用正常（INT4 量化约 2.6GB）
- [x] 确认模型文件被正确加载

### 健康检查测试
- [x] 测试 GET /api/v1/health/components
  - [x] 返回状态码 200
  - [x] yolo 组件 status: "ready"
  - [x] qwen 组件 status: "ready"
  - [x] 模型路径信息正确
- [x] 测试 GET /api/v1/diagnosis/health/ai
  - [x] 返回状态码 200
  - [x] 总体状态：healthy

### 功能测试
- [x] 运行 test_startup.py 测试脚本
  - [x] 所有测试用例通过（5/5）
  - [x] 生成测试结果 JSON
- [x] 测试多模态诊断功能
  - [x] 服务可接受请求
  - [x] 模型推理正常

## 文档更新阶段

### 配置文档
- [x] 记录路径修复方案
- [x] 记录 4-bit 量化配置方法
- [x] 更新 tasks.md 任务状态

### 问题记录
- [x] 记录本次修复的问题原因
- [x] 记录解决方案
- [x] 更新 spec 文档

## 最终验收

### 必须通过的检查点
- [x] QWEN_MODEL_PATH 存在且指向正确目录
- [x] YOLO_MODEL_PATH 存在且指向正确文件
- [x] Qwen 模型 is_loaded: true
- [x] YOLO 模型 is_loaded: true
- [x] /health/components 返回 AI 服务 ready
- [x] /diagnosis/health/ai 返回模型已加载
- [x] test_startup.py 全部通过（5/5）
- [x] 多模态诊断功能正常

### 性能检查
- [x] 模型加载时间正常（YOLO: 2.83秒, Qwen: 25.85秒）
- [x] 显存占用合理（INT4 量化约 2.6GB）
- [x] 无内存泄漏

### 稳定性检查
- [x] 服务可稳定运行
- [x] 多次请求无错误
- [x] 日志输出正常
- [x] 无异常崩溃

### 遗留问题修复
- [x] 无 `No module named 'src'` 警告
- [x] 无 `update_component_status() metadata` 参数错误
- [x] AI 健康检查返回正确的 is_loaded 状态

## 签署确认

**修复人**: AI Assistant  
**修复日期**: 2026-03-11  

**测试结果**: ☑ 通过  

**验收结果**: ☑ 通过  

**备注**:
- 模型路径配置已修复（从 3 层 parent 改为 6 层）
- Qwen 模型使用 INT4 量化加载，显存占用约 2.6GB
- 所有测试通过（5/5），服务运行正常
- 遗留问题已修复：模块导入警告和 metadata 参数错误
