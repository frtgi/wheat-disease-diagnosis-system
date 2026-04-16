# IWDDA Agent 性能测试套件

本目录包含 IWDDA Agent 的完整性能测试套件，用于验证系统的推理延迟、并发性能和资源占用。

## 测试模块

### 1. 推理延迟测试 (test_latency.py)

测试系统各模块的推理延迟，包括：

- **视觉感知模块延迟测试**
- **认知层 (Qwen3-VL) 延迟测试**
- **规划层延迟测试**
- **端到端延迟测试**
- **延迟稳定性测试**

**性能目标：**
- p50 延迟 < 1s
- p95 延迟 < 3s
- p99 延迟 < 5s

### 2. 并发性能测试 (test_concurrency.py)

测试系统在不同并发级别下的性能表现：

- **10 并发测试**
- **50 并发测试**
- **100 并发测试**
- **吞吐量扩展性测试**
- **高负载延迟测试**

**性能指标：**
- 每秒请求数 (RPS)
- 成功率
- 平均延迟
- p50/p95/p99 延迟

### 3. 资源占用测试 (test_resource_usage.py)

测试系统的资源占用情况：

- **Qwen3-VL 显存占用测试**
- **CPU 使用率测试**
- **进程内存占用测试**
- **GPU 利用率测试**
- **资源稳定性测试**

**性能目标：**
- Qwen3-VL 显存占用 < 3GB
- 进程内存占用 < 2GB
- CPU 使用率 < 80%

## 安装依赖

```bash
cd d:\Project\WheatAgent
pip install -r tests/requirements-test.txt
```

新增依赖：
- pytest-benchmark>=4.0.0
- psutil>=5.9.0

## 运行测试

### 运行所有性能测试

```bash
cd d:\Project\WheatAgent
pytest tests/performance/ -v
```

### 运行特定模块测试

```bash
# 仅运行延迟测试
pytest tests/performance/test_latency.py -v

# 仅运行并发测试
pytest tests/performance/test_concurrency.py -v

# 仅运行资源测试
pytest tests/performance/test_resource_usage.py -v
```

### 运行单个测试用例

```bash
# 运行特定测试
pytest tests/performance/test_latency.py::TestLatency::test_perception_latency -v
```

### 生成性能报告

```bash
cd d:\Project\WheatAgent
python tests/performance/generate_report.py
```

## 测试结果

所有测试通过后，将显示：

```
======================================= 15 passed in XXX.XXs =======================================
```

测试用例包括：

**延迟测试 (5 个):**
- test_perception_latency
- test_cognition_latency
- test_planning_latency
- test_end_to_end_latency
- test_latency_stability

**并发测试 (5 个):**
- test_10_concurrent_users
- test_50_concurrent_users
- test_100_concurrent_users
- test_throughput_scaling
- test_latency_under_load

**资源测试 (5 个):**
- test_qwen_vl_gpu_memory
- test_cpu_usage
- test_memory_usage
- test_gpu_utilization
- test_resource_stability

## 性能基准

测试使用模拟模型进行基准测试，实际性能可能因硬件配置而异。

**测试环境要求：**
- Python 3.10+
- PyTorch 2.0+
- CUDA 支持 (可选，用于 GPU 测试)
- 8GB+ 内存
- 4GB+ 显存 (可选)

## 输出指标

测试完成后会输出详细的性能指标：

1. **延迟指标**: p50, p95, p99, 平均值，标准差
2. **并发指标**: RPS, 成功率，延迟分布
3. **资源指标**: GPU 显存，CPU 使用率，内存占用

## 故障排除

如果测试失败：

1. 检查硬件资源是否充足
2. 关闭其他占用资源的应用程序
3. 确保 CUDA 驱动正确安装 (GPU 测试)
4. 降低测试迭代次数 (修改 num_iterations 参数)

## 贡献

如需添加新的性能测试，请遵循以下规范：

1. 测试函数以 `test_` 开头
2. 使用 pytest fixture 管理资源
3. 添加详细的中文注释
4. 定义明确的性能目标
5. 生成可序列化的测试报告
