# 问题修复计划

## 概述

基于全面系统检查报告，本计划将按优先级修复发现的 13 个问题。

---

## 第一阶段：高优先级问题修复

### 1. JWT 密钥硬编码风险
**文件**: `backend/app/core/config.py:51`

**当前问题**:
```python
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
```

**修复步骤**:
1. 检查 `.env` 文件是否存在
2. 运行 `scripts/generate_secrets.py` 生成安全密钥
3. 将生成的密钥添加到 `.env` 文件
4. 修改 `config.py` 移除默认值或使用更安全的默认行为

### 2. Element Plus chunk 过大
**文件**: `frontend/vite.config.ts`

**当前问题**: element-plus chunk 达到 1,008 kB

**修复步骤**:
1. 安装 `unplugin-vue-components` 和 `unplugin-auto-import`
2. 配置 Vite 插件实现按需导入
3. 修改 `main.ts` 移除全量导入
4. 验证构建产物大小

---

## 第二阶段：中优先级问题修复

### 3. 融合推理未记录推理时间
**文件**: `backend/app/services/fusion_service.py`

**修复步骤**:
1. 在 `diagnose()` 方法开始记录开始时间
2. 记录各阶段耗时（YOLO、Qwen、GraphRAG）
3. 计算总耗时并赋值给 `inference_time_ms`

### 4. 缺少请求日志追踪
**文件**: `backend/app/main.py`

**修复步骤**:
1. 创建请求 ID 中间件
2. 为每个请求生成唯一 ID
3. 将请求 ID 添加到响应头和日志上下文

### 5. 前端缺少错误边界
**文件**: `frontend/src/components/ErrorBoundary.vue`

**修复步骤**:
1. 创建 ErrorBoundary 组件
2. 在 App.vue 中包裹路由视图
3. 添加错误恢复机制

### 6. 数据库连接池配置
**文件**: `backend/app/core/database.py`

**修复步骤**:
1. 添加 `pool_size` 参数
2. 添加 `max_overflow` 参数
3. 添加 `pool_pre_ping` 参数
4. 添加 `pool_recycle` 参数

---

## 第三阶段：低优先级问题修复

### 7. 降级因子配置化
**文件**: `backend/app/services/fusion_service.py`

**修复步骤**:
1. 将降级因子移至配置文件
2. 支持动态调整

### 8. 模型预热机制
**文件**: `backend/app/services/yolo_service.py`, `backend/app/services/qwen_service.py`

**修复步骤**:
1. 添加 `_warmup()` 方法
2. 在应用启动时调用预热

### 9. CORS 配置优化
**文件**: `backend/app/core/config.py`

**修复步骤**:
1. 添加 `CORS_ORIGINS` 配置项
2. 生产环境限制允许的域名

---

## 实施顺序

```
第一阶段（高优先级）
├── 1. JWT 密钥配置
└── 2. Element Plus 按需导入

第二阶段（中优先级）
├── 3. 推理时间记录
├── 4. 请求 ID 追踪
├── 5. 前端错误边界
└── 6. 数据库连接池

第三阶段（低优先级）
├── 7. 降级因子配置化
├── 8. 模型预热机制
└── 9. CORS 配置优化
```

---

## 验证步骤

每个阶段完成后执行：
1. 运行前端构建 `npm run build`
2. 运行前端测试 `npm run test`
3. 运行后端语法检查 `python -m py_compile`
4. 验证功能正常

---

## 预期结果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| JWT 密钥安全 | 默认值 | 环境变量 |
| Element Plus chunk | 1,008 kB | < 200 kB |
| 推理时间记录 | 无 | 有 |
| 请求追踪 | 无 | 有 |
| 错误边界 | 无 | 有 |
| 数据库连接池 | 无 | 有 |
