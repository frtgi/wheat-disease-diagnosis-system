# -*- coding: utf-8 -*-
"""
IWDDA Agent 性能测试套件

包含以下测试模块：
1. 推理延迟测试 (test_latency.py)
2. 并发性能测试 (test_concurrency.py)
3. 资源占用测试 (test_resource_usage.py)

性能目标：
- p50 延迟 < 1s
- p95 延迟 < 3s
- p99 延迟 < 5s
- Qwen3-VL 显存占用 < 3GB
"""
