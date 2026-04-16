# -*- coding: utf-8 -*-
"""
模型训练流程验证脚本
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

print('=' * 70)
print('🔍 模型训练流程验证')
print('=' * 70)

# 1. 检查训练模块导入
print('\n📦 1. 检查训练模块导入...')
modules = [
    ('src.training.yolo_trainer', 'YOLO训练器'),
    ('src.training.agri_llava_trainer', 'Agri-LLaVA训练器'),
    ('src.training.memory_optimizer', '内存优化器'),
]

for module_path, desc in modules:
    try:
        __import__(module_path)
        print(f'   ✅ {desc} ({module_path})')
    except Exception as e:
        print(f'   ❌ {desc} ({module_path}): {str(e)[:50]}')

# 2. 检查训练配置
print('\n📋 2. 检查训练配置...')
try:
    from src.utils.config_manager import ConfigManager
    config = ConfigManager()
    print('   ✅ 配置管理器可用')
except Exception as e:
    print(f'   ⚠️ 配置管理器: {str(e)[:50]}')

# 3. 检查数据加载器
print('\n📂 3. 检查数据模块...')
try:
    from src.data.dataset_builder import DatasetBuilder
    print('   ✅ 数据集构建器可用')
except Exception as e:
    print(f'   ⚠️ 数据集构建器: {str(e)[:50]}')

try:
    from src.data.augmentation_engine import AugmentationEngine
    print('   ✅ 数据增强引擎可用')
except Exception as e:
    print(f'   ⚠️ 数据增强引擎: {str(e)[:50]}')

# 4. 检查增量学习
print('\n🔄 4. 检查增量学习模块...')
try:
    from src.evolution.incremental_learning import IncrementalLearner
    print('   ✅ 增量学习器可用')
except Exception as e:
    print(f'   ⚠️ 增量学习器: {str(e)[:50]}')

try:
    from src.evolution.experience_replay import ExperienceReplayBuffer
    print('   ✅ 经验回放缓冲区可用')
except Exception as e:
    print(f'   ⚠️ 经验回放缓冲区: {str(e)[:50]}')

print('\n' + '=' * 70)
print('✅ 模型训练流程验证完成')
print('=' * 70)
