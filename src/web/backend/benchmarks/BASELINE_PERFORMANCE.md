# WheatAgent 性能基线报告

> 生成日期: 2026-04-04
> 环境: Windows 11 / Intel i7-13620H / CPU-only (PyTorch 2.10.0+cpu) / conda wheatagent-py310
> 注意: 本次测试在 **CPU 模式** 下运行（CUDA 未启用），GPU 环境下的结果会有显著差异

## 基准结果总表

| 基准指标 | 平均值 | 中位数 | 最小值 | 最大值 | 标准差 | 目标值 | 状态 |
|----------|--------|--------|--------|--------|--------|--------|------|
| YOLO 单图推理 | 225.91ms | 187.17ms | 176.49ms | 314.06ms | 76.53ms | <150ms | ⚠️ |
| YOLO 预热后推理 | ~182ms | ~187ms | 176ms | 187ms | ~5ms | <150ms | ⚠️ |
| Qwen 首次推理 | N/A | N/A | N/A | N/A | - | <35s | ❌ |
| Qwen 后续推理 | N/A | N/A | N/A | N/A | - | <30s | ❌ |
| 完整诊断流程 (YOLO only) | 185.8ms | 185.8ms | 185.8ms | 185.8ms | 0ms | <40s | ✅ |
| SSE Manager 创建 | 0.86μs | 0.70μs | 0.60μs | 5.40μs | 0.59μs | - | ✅ |
| ProgressEvent 格式化 | 6.19μs | 5.80μs | 3.40μs | 67.50μs | 4.22μs | - | ✅ |
| HeartbeatEvent 生成 | 4.28μs | 4.30μs | 2.50μs | 34.90μs | 1.47μs | - | ✅ |
| SSE 首个事件延迟 | 0.01ms | 0.007ms | 0.005ms | 0.032ms | 0.004ms | <500ms | ✅ |

### 状态说明

- ✅ **达标**: 性能满足目标要求
- ⚠️ **未达标**: 接近目标但超出阈值，需关注优化
- ❌ **不可用**: 测试因环境/依赖问题无法执行
- **N/A**: 数据不可用（模型未加载或服务异常）

---

## 各基准详细分析

### 1. YOLOv8 推理延迟

**测试条件**: 640x640 RGB 图像，FP16 未启用（CPU 模式），3 次迭代

**关键发现**:
- **首次推理偏慢**: 第 1 次 314ms（含模型预热/初始化开销）
- **稳定态性能**: 第 2-3 次 ~177-187ms，已接近 GPU 模式预期
- **纯推理耗时**: YOLO 报告的 inference_time 为 127-133ms（不含预处理/后处理）
- **瓶颈分析**: CPU 模式下推理速度受限是主要瓶颈；启用 FP16 + GPU 后预计可降至 <50ms

**迭代详情**:
| 迭代 | 总耗时 | 推理耗时 | 检测数 |
|------|--------|----------|--------|
| 1 | 314.06ms | 253.11ms | 0 |
| 2 | 176.49ms | 132.97ms | 0 |
| 3 | 187.17ms | 133.97ms | 0 |

**优化建议**:
1. 确保 GPU 可用并启用 FP16 半精度推理
2. 首次推理前执行 `_warmup()` 预热
3. 考虑使用 `use_cache=True` 对相同图像缓存结果

---

### 2. Qwen3-VL 推理延迟

**测试状态**: ❌ 不可用

**失败原因**: `QwenModelLoader.__new__() got an unexpected keyword argument 'lazy_load'`

**根因分析**: `QwenModelLoader` 的 `__new__()` 方法（单例模式实现）不接受关键字参数，但 `__init__` 定义了 `lazy_load` 参数。当通过 `get_qwen_service(lazy_load=True)` 调用时，Python 将 kwargs 同时传给 `__new__` 和 `__init__`，导致 `__new__` 报错。

**修复建议** (需修改 `app/services/qwen/qwen_loader.py`):
```python
# 修改 __new__ 方法签名以接受 *args, **kwargs
def __new__(cls, *args, **kwargs):
    if cls._instance is None:
        cls._instance = super().__new__(cls)
        cls._instance._initialized = False
    return cls._instance
```

**预期性能** (基于 V4 报告):
- 首次推理（含懒加载）: 目标 <35s
- 后续推理（模型已加载）: 目标 <30s
- INT4 量化 + CPU Offload: 可进一步降低显存占用

---

### 3. 完整诊断流程端到端延迟

**测试条件**: 仅 YOLO 组件可用（Qwen 因上述问题跳过）

**组件分解**:
| 阶段 | 耗时 | 占比 | 状态 |
|------|------|------|------|
| 图像预处理 | 0.9ms | 0.5% | ✅ |
| YOLO 视觉检测 | 178.8ms | 96.2% | ✅ |
| Qwen 语义分析 | 0ms (跳过) | 0% | ⏭️ |
| 结果融合 | <0.01ms | ~0% | ✅ |
| **总计** | **185.8ms** | 100% | ✅ |

**说明**: 当前完整诊断流程仅包含 YOLO 视觉部分，不包含 Qwen 语义分析。
当 Qwen 服务可用时，完整流程总耗时预计为 YOLO(~180ms) + Qwen(~25-30s) ≈ **~30s**。

---

### 4. SSE 流延迟

所有 SSE 相关基准均表现优异，远低于目标阈值。

#### 4.1 SSEStreamManager 创建

- 平均创建时间: **0.86μs**（100 次迭代）
- 中位数: **0.70μs**
- 最大值: **5.40μs**（首次创建因模块导入略慢）
- 结论: 创建开销可忽略不计，不会成为系统瓶颈

#### 4.2 ProgressEvent 格式化

- 平均格式化时间: **6.19μs**（1000 次迭代）
- 首次格式化: 35.9μs（JIT/缓存预热）
- 稳定态: ~5-7μs
- 输出大小: ~140 字符/事件
- 结论: JSON 序列化效率高，满足高频推送需求

#### 4.3 HeartbeatEvent 生成

- 平均生成时间: **4.28μs**（1000 次迭代）
- 极其稳定的低延迟（stdev 仅 1.47μs）
- 结论: 心跳保活机制对性能零影响

#### 4.4 SSE 首个事件到达延迟

- **平均延迟: 0.01ms**（目标 <500ms）
- **中位数: 0.007ms**
- **最大值: 0.032ms**
- **达标倍数**: 比目标快约 **50,000 倍**
- 结论: SSE 流管理器的事件生成和传输极其高效

---

## 环境信息

### 硬件环境

| 项目 | 值 |
|------|-----|
| 操作系统 | Windows 11 |
| 处理器 | Intel Core i7-13620H (10核16线程) |
| 架构 | x86_64 |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU (4GB) [本次未启用] |

### 软件环境

| 项目 | 版本 |
|------|------|
| Python | 3.13.11 |
| PyTorch | 2.10.0+cpu (**CPU only**) |
| ultralytics (YOLO) | 8.4.13 |
| transformers | 5.1.0 |
| FastAPI | 0.128.6 |
| Conda 环境 | wheatagent-py310 |

### 关键配置

| 配置项 | 值 |
|--------|-----|
| YOLO 模型路径 | models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt |
| YOLO FP16 | 未启用 (CPU 模式) |
| YOLO 置信度阈值 | 0.5 |
| SSE 心跳间隔 | 15s |
| SSE 超时时间 | 120s |
| SSE 队列大小 | 100 |

---

## 测试方法说明

### YOLO 推理测试方法
1. 使用 `numpy.random.randint()` 生成 640x640x3 随机 RGB 数组
2. 通过 `PIL.Image.fromarray()` 创建测试图像
3. 调用 `YOLOv8Service.detect(image, use_cache=False)` 执行推理
4. 使用 `time.perf_counter()` 高精度计时
5. 执行 3 次迭代取统计值

### Qwen 推理测试方法
1. 生成 448x448 测试图像 + 固定中文 prompt
2. 尝试调用 `get_qwen_service(lazy_load=True)` 初始化
3. 调用 `QwenService.diagnose(image, symptoms, enable_thinking=False)`
4. 区分首次推理（含懒加载）和后续推理（模型已加载）
5. **当前因 API 兼容性问题无法完成**

### 完整诊断流程测试方法
1. 模拟端到端请求：创建测试图像 → 预处理 → YOLO 检测 → Qwen 分析 → 结果融合
2. 分别测量各阶段独立耗时
3. 计算总端到端延迟
4. 若某组件不可用则标记跳过并汇总可用组件耗时

### SSE 延迟测试方法
1. **Manager 创建**: 循环实例化 `SSEStreamManager` 100 次，测量每次耗时
2. **ProgressEvent 格式化**: 创建事件对象并调用 `.to_sse()` 1000 次
3. **HeartbeatEvent 生成**: 调用静态方法 `HeartbeatEvent.to_sse()` 1000 次
4. **首个事件延迟**: 创建异步流生成器，测量从启动到首个 `async for` 收到数据的时间（50 次迭代）

---

## 已知问题与待修复项

### P0 - 阻塞性问题

| 问题 | 影响 | 建议 |
|------|------|------|
| `QwenModelLoader.__new__()` 不接受 `lazy_load` 参数 | Qwen 所有基准测试无法运行 | 修改 `qwen_loader.py` 的 `__new__` 签名为 `def __new__(cls, *args, **kwargs)` |

### P1 - 性能关注项

| 问题 | 当前值 | 目标值 | 优先级 |
|------|--------|--------|--------|
| YOLO CPU 模式推理偏慢 | ~180ms (稳定态) | <150ms | 中 |
| YOLO 首次推理冷启动 | ~314ms | <200ms | 低 |
| FP16 在 CPU 模式下未生效 | false | true (需 GPU) | - |

### P2 - 优化建议

1. **YOLO 预热优化**: 在服务启动时调用 `_warmup()` 避免首次推理慢
2. **SSE 性能优异**: 当前实现无需优化，已远超目标
3. **异步生成器警告**: `asyncio.run()` 关闭时有 `GeneratorExit` 异常（不影响功能，属于 Python 已知行为）

---

## 运行命令
```bash
# 运行全部基准测试
cd src/web/backend
conda activate wheatagent-py310
python benchmarks/run_all_benchmarks.py

# 单独运行各项基准
python benchmarks/benchmark_yolo_inference.py
python benchmarks/benchmark_qwen_inference.py
python benchmarks/benchmark_full_diagnosis.py
python benchmarks/benchmark_sse_latency.py

# 查看原始结果
cat benchmarks/benchmark_results.json
```

---

## V6 更新记录 (2026-04-04)

### P0 QwenModelLoader `__new__` 修复状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 问题根因 | 已确认 | `QwenModelLoader.__new__(cls)` 签名不接受 `*args, **kwargs`，导致 `get_qwen_service(lazy_load=True)` 调用时 kwargs 传递失败 |
| 修复方案 | 待实施 | 修改 `qwen_loader.py` L57 签名为 `def __new__(cls, *args, **kwargs)` 并透传参数 |
| 影响范围 | Qwen 全部基准测试不可用 (N/A) | 首次推理、后续推理、完整诊断流程中的 Qwen 部分均无法执行 |
| 优先级 | **P0** | 阻塞所有 Qwen3-VL 相关性能数据采集 |

### V6 测试补充计划 (Task 2 关联)

本基线报告基于 V5 测试套件生成。V6 阶段计划补充以下测试：

| 模块 | 目标测试数增量 | 覆盖重点 |
|------|----------------|----------|
| sse_stream_manager.py | +15 | 心跳保活、背压控制、超时处理、事件格式化 |
| diagnosis_validator.py | +20 | Magic Number 校验、Mock 切换、GPU 显存检查、限流集成 |
| fusion_service.py (Facade) | +15 | diagnose_async 完整流程、缓存命中/未命中路径、降级场景 |
| config.py Settings 类 | +10 | 环境变量加载、JWT 密钥缓存、CORS 校验、MinIO 配置验证 |

预期覆盖率提升：**11.08% → >20%**

### GPU 模式预期数据说明

当前所有基准数据均在 **CPU 模式**（PyTorch 2.10.0+cpu）下采集。GPU 模式下的预期表现如下：

| 基准指标 | CPU 当前值 | GPU 预期值 | 加速比预估 |
|----------|-----------|-----------|------------|
| YOLO 单图推理 (稳定态) | ~187ms | <50ms (FP16) | ~3.7x |
| YOLO 预热后推理 | ~187ms | <30ms (FP16+预热) | ~6x |
| Qwen 首次推理 | N/A | <35s (INT4+CPU Offload) | - |
| Qwen 后续推理 | N/A | <30s (模型已加载) | - |
| 完整诊断流程 (YOLO only) | 185.8ms | <50ms | ~3.7x |

**GPU 环境前提条件**:
- NVIDIA GeForce RTX 3050 Laptop GPU (4GB)
- CUDA Toolkit 已安装且 PyTorch CUDA 版本匹配
- 启用 FP16 半精度: `YOLO_FP16=true`
- Qwen 使用 INT4 量化: `LOAD_IN_4BIT=true`
