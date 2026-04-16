# 优化启动逻辑 Spec

## Why
当前后端服务启动时不主动加载 AI 模型，导致诊断功能需要等待模型懒加载。需要优化启动逻辑，在应用启动时预加载 AI 模型和服务，提供启动进度反馈，确保服务完全就绪后再接受请求。

## What Changes
- 修改应用启动事件，添加 AI 服务预加载
- 实现模型加载进度监控和日志输出
- 添加启动健康检查端点（带加载状态）
- 优化服务就绪检测机制
- 添加模型加载超时和错误处理

## Impact
- **Affected specs**: validate-models-and-retest, ai-service-integration
- **Affected code**: 
  - `app/main.py` - 应用启动事件
  - `app/services/qwen_service.py` - 模型加载逻辑
  - `app/services/yolo_service.py` - 模型加载逻辑
  - `app/api/v1/health.py` - 健康检查端点
  - `app/core/ai_config.py` - 启动配置

## ADDED Requirements

### Requirement: 应用启动事件
系统 SHALL 在启动时预加载所有 AI 服务：
- 加载 Qwen3-VL-4B-Instruct 模型
- 加载 YOLOv8 模型
- 初始化缓存管理器
- 验证模型加载成功

#### Scenario: 启动流程
- **WHEN** 执行 `python -m uvicorn app.main:app --reload`
- **THEN** 按顺序加载数据库 → AI 模型 → 服务组件
- **THEN** 输出详细的加载进度日志
- **THEN** 所有组件加载完成后服务才就绪

### Requirement: 模型加载进度监控
系统 SHALL 提供模型加载进度反馈：
- 显示当前加载的模型名称
- 显示加载进度百分比
- 显示预计剩余时间
- 显示显存使用情况

#### Scenario: 加载进度
- **WHEN** 模型正在加载
- **THEN** 每 10% 输出一次进度日志
- **THEN** 加载完成后输出总结信息

### Requirement: 启动健康检查
系统 SHALL 提供增强的健康检查端点：
- `GET /health/startup` - 返回启动状态和加载进度
- `GET /health/ready` - 返回服务是否完全就绪
- `GET /health/components` - 返回各组件状态详情

#### Scenario: 健康检查
- **WHEN** 客户端访问健康检查端点
- **THEN** 返回详细的组件状态
- **THEN** 如果未就绪，返回预计就绪时间

### Requirement: 错误处理与降级
系统 SHALL 处理模型加载失败：
- 设置加载超时时间（默认 120 秒）
- 模型加载失败时提供降级方案
- 记录详细的错误日志
- 允许服务在无 AI 模型情况下启动（降级模式）

#### Scenario: 加载失败
- **WHEN** 模型加载超时或失败
- **THEN** 记录错误并继续启动
- **THEN** 服务以降级模式运行
- **THEN** 健康检查返回 degraded 状态

## MODIFIED Requirements

### Requirement: 应用启动事件
**原实现**:
```python
@app.on_event("startup")
async def startup_event():
    await init_db_async()
    logger.info("数据库初始化完成")
```

**修改后**:
```python
@app.on_event("startup")
async def startup_event():
    # 1. 初始化数据库
    await init_db_async()
    logger.info("✓ 数据库初始化完成")
    
    # 2. 预加载 AI 服务
    await preload_ai_services()
    
    # 3. 初始化其他组件
    initialize_cache()
    logger.info("✓ 所有组件加载完成")
    
    logger.info("应用启动完成，服务就绪")
```

### Requirement: 健康检查端点
**原实现**: 仅检查数据库连接

**修改后**: 增加 AI 服务状态检查
```python
@router.get("/startup")
async def startup_health():
    return {
        "status": "starting" | "ready" | "degraded",
        "startup_progress": 0-100,
        "components": {
            "database": {"status": "ready", ...},
            "yolo": {"status": "loading|ready|failed", "progress": 0-100},
            "qwen": {"status": "loading|ready|failed", "progress": 0-100},
            "cache": {"status": "ready", ...}
        },
        "estimated_ready_time": "30s"
    }
```

## REMOVED Requirements
无

## 启动流程设计

### 启动阶段

```
阶段 1: 基础服务初始化 (0-20%)
  ├─ 加载配置文件
  ├─ 初始化日志系统
  ├─ 创建 FastAPI 应用
  └─ 配置中间件

阶段 2: 数据库连接 (20-40%)
  ├─ 创建数据库连接池
  ├─ 验证数据库连接
  ├─ 创建表结构
  └─ 初始化基础数据

阶段 3: AI 模型加载 (40-90%)
  ├─ 加载 YOLOv8 模型 (40-60%)
  │   ├─ 验证模型文件
  │   ├─ 加载模型权重
  │   └─ 初始化推理引擎
  └─ 加载 Qwen3-VL 模型 (60-90%)
      ├─ 验证模型文件
      ├─ 加载模型权重
      ├─ 初始化 tokenizer
      ├─ 配置生成参数
      └─ 预热推理引擎

阶段 4: 服务组件初始化 (90-100%)
  ├─ 初始化缓存管理器
  ├─ 初始化日志记录器
  ├─ 注册 API 路由
  └─ 启动后台任务

完成: 服务就绪 (100%)
  └─ 输出启动总结
```

### 时间估算

| 阶段 | 预计时间 | 说明 |
|------|----------|------|
| 基础服务 | < 1s | 快速 |
| 数据库 | < 2s | 包含连接测试 |
| YOLOv8 | 5-10s | GPU 加速 |
| Qwen3-VL | 30-60s | 大模型加载 |
| 服务组件 | < 1s | 快速 |
| **总计** | **40-75s** | 取决于硬件 |

## 验收标准

### 启动验证
- [ ] 服务启动时自动加载 AI 模型
- [ ] 输出详细的加载进度日志
- [ ] 所有模型加载成功后服务才就绪
- [ ] 加载失败时有明确的错误提示

### 健康检查
- [ ] `GET /health/startup` 返回加载进度
- [ ] `GET /health/ready` 返回就绪状态
- [ ] `GET /health/components` 返回组件详情
- [ ] 状态准确反映实际情况

### 性能要求
- [ ] Qwen 模型加载时间 < 90s
- [ ] YOLO 模型加载时间 < 15s
- [ ] 总启动时间 < 120s
- [ ] 加载过程不阻塞主线程

### 错误处理
- [ ] 模型加载超时有明确提示
- [ ] 加载失败不影响服务启动（降级模式）
- [ ] 错误日志详细可追溯
- [ ] 提供故障排查建议

## 配置选项

### 新增环境变量

```bash
# 启动配置
AI_PRELOAD_ON_STARTUP=true          # 启动时预加载 AI 服务
AI_LOAD_TIMEOUT=120                 # 模型加载超时时间（秒）
AI_LOAD_PROGRESS_INTERVAL=10        # 进度更新间隔（秒）

# 模型配置
QWEN_LOAD_IN_4BIT=false             # INT4 量化（节省显存）
QWEN_DEVICE=cuda                    # 运行设备（cuda/cpu）
YOLO_DEVICE=cuda                    # YOLO 运行设备

# 降级配置
ENABLE_FALLBACK_MODE=true           # 启用降级模式
FALLBACK_TO_TEXT_DIAGNOSIS=true     # 降级为文本诊断
```

## 监控指标

### 启动指标
- `startup_duration_seconds` - 启动总耗时
- `model_load_duration_seconds{model="qwen"}` - 模型加载耗时
- `startup_progress_percent` - 启动进度百分比

### 运行时指标
- `ai_service_status{service="qwen"}` - AI 服务状态（0=未加载，1=就绪，2=失败）
- `model_memory_usage_bytes{model="qwen"}` - 模型显存占用
- `inference_request_total{model="qwen"}` - 推理请求总数
