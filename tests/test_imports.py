# -*- coding: utf-8 -*-
"""
模块导入测试脚本
验证所有新模块可正确导入
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('=== 模块导入测试 ===')

# 测试1: 推理缓存模块
print('\n1. 测试推理缓存模块...')
try:
    from src.utils.inference_cache import InferenceCache, CacheEntry, ImageHasher, create_inference_cache, get_global_cache
    print('   ✅ InferenceCache 导入成功')
    cache = create_inference_cache(max_size=100)
    print(f'   ✅ 缓存实例创建成功, max_size={cache.max_size}')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

# 测试2: 性能监控模块
print('\n2. 测试性能监控模块...')
try:
    from src.utils.performance_monitor import PerformanceMonitor, MetricType, timed, get_global_monitor
    print('   ✅ PerformanceMonitor 导入成功')
    monitor = get_global_monitor()
    print(f'   ✅ 监控实例创建成功, name={monitor.name}')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

# 测试3: 视觉引擎
print('\n3. 测试视觉引擎...')
try:
    from src.vision.vision_engine import VisionAgent
    print('   ✅ VisionAgent 导入成功')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

# 测试4: 融合引擎
print('\n4. 测试融合引擎...')
try:
    from src.fusion.fusion_engine import FusionAgent
    print('   ✅ FusionAgent 导入成功')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

# 测试5: utils模块导出
print('\n5. 测试utils模块导出...')
try:
    from src.utils import InferenceCache, PerformanceMonitor
    print('   ✅ utils模块导出正常')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

print('\n=== 模块导入测试完成 ===')
