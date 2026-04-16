# -*- coding: utf-8 -*-
"""
GPU显存利用率优化脚本
自动测试并找到最优训练配置，充分利用RTX 3050 4GB显存

使用方法:
    python scripts/optimize_gpu_utilization.py
"""
import os
import sys
import torch
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_gpu_status():
    """检查GPU当前状态"""
    print("=" * 70)
    print("🔍 GPU状态检查")
    print("=" * 70)
    
    if not torch.cuda.is_available():
        print("❌ CUDA不可用")
        return None
    
    gpu_name = torch.cuda.get_device_name(0)
    total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
    reserved_memory = torch.cuda.memory_reserved(0) / 1024**3
    
    print(f"GPU型号: {gpu_name}")
    print(f"总显存: {total_memory:.2f} GB")
    print(f"已分配: {allocated_memory:.2f} GB ({allocated_memory/total_memory*100:.1f}%)")
    print(f"已保留: {reserved_memory:.2f} GB ({reserved_memory/total_memory*100:.1f}%)")
    print(f"可用显存: {total_memory - reserved_memory:.2f} GB")
    
    return {
        'name': gpu_name,
        'total': total_memory,
        'allocated': allocated_memory,
        'reserved': reserved_memory,
        'available': total_memory - reserved_memory
    }


def test_training_config(batch_size, img_size, max_test_batches=5):
    """
    测试特定配置是否可行
    
    Args:
        batch_size: 批次大小
        img_size: 图像尺寸
        max_test_batches: 最大测试batch数
    
    Returns:
        (success, memory_used, error_msg)
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        return False, 0, "未安装ultralytics"
    
    # 清空缓存
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    
    mem_before = torch.cuda.memory_allocated(0) / 1024**3
    
    try:
        # 加载模型
        model = YOLO('yolov8n.pt')
        
        # 尝试训练几个batch
        data_yaml = os.path.abspath("configs/wheat_disease_optimized.yaml")
        
        # 使用训练参数配置
        import yaml
        with open("configs/training_params.yaml", 'r') as f:
            params = yaml.safe_load(f)
        
        model.train(
            data=data_yaml,
            epochs=1,
            batch=batch_size,
            imgsz=img_size,
            device=0,
            workers=0,
            cache=False,  # 测试时不缓存
            amp=True,
            optimizer='SGD',
            lr0=0.01,
            verbose=False,
            plots=False,
            save=False,
        )
        
        # 获取显存使用情况
        mem_after = torch.cuda.memory_allocated(0) / 1024**3
        mem_used = mem_after - mem_before
        
        return True, mem_used, None
        
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
            return False, 0, f"显存不足: {str(e)[:100]}"
        return False, 0, f"其他错误: {str(e)[:100]}"
    except Exception as e:
        return False, 0, f"未知错误: {str(e)[:100]}"
    finally:
        # 清理
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def find_optimal_config():
    """自动寻找最优配置"""
    print("\n" + "=" * 70)
    print("🧪 自动寻找最优训练配置")
    print("=" * 70)
    
    # 测试配置列表 (batch_size, img_size)
    test_configs = [
        # 低显存配置
        (4, 480),
        (8, 480),
        # 中等配置
        (16, 480),
        (8, 640),
        # 高配置
        (16, 640),
        (32, 480),
        # 极限配置
        (32, 640),
        (64, 480),
    ]
    
    results = []
    
    for batch, imgsz in test_configs:
        print(f"\n测试配置: batch={batch}, imgsz={imgsz}...", end=' ')
        
        success, mem_used, error = test_training_config(batch, imgsz)
        
        if success:
            print(f"✅ 成功 (显存占用: {mem_used:.2f}GB)")
            results.append({
                'batch': batch,
                'imgsz': imgsz,
                'memory': mem_used,
                'feasible': True
            })
        else:
            print(f"❌ 失败 ({error})")
            results.append({
                'batch': batch,
                'imgsz': imgsz,
                'memory': 0,
                'feasible': False,
                'error': error
            })
    
    return results


def recommend_config(results, gpu_info):
    """推荐最优配置"""
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    
    feasible_configs = [r for r in results if r['feasible']]
    
    if not feasible_configs:
        print("❌ 没有可行的配置，请检查GPU状态")
        return None
    
    # 按显存使用排序
    feasible_configs.sort(key=lambda x: x['memory'], reverse=True)
    
    print("\n可行配置（按显存使用排序）:")
    print("-" * 70)
    print(f"{'Batch':<10} {'ImgSize':<10} {'显存占用':<15} {'利用率':<10}")
    print("-" * 70)
    
    for cfg in feasible_configs:
        utilization = cfg['memory'] / gpu_info['total'] * 100
        print(f"{cfg['batch']:<10} {cfg['imgsz']:<10} {cfg['memory']:.2f} GB{'':<8} {utilization:.1f}%")
    
    # 推荐配置：显存使用在60-80%之间
    target_memory = gpu_info['total'] * 0.7  # 目标70%利用率
    
    recommended = None
    for cfg in feasible_configs:
        if cfg['memory'] <= target_memory:
            recommended = cfg
            break
    
    if not recommended:
        recommended = feasible_configs[0]  # 使用最大可行配置
    
    print("\n" + "=" * 70)
    print("🎯 推荐配置")
    print("=" * 70)
    print(f"Batch Size: {recommended['batch']}")
    print(f"Image Size: {recommended['imgsz']}")
    print(f"预计显存占用: {recommended['memory']:.2f} GB")
    print(f"显存利用率: {recommended['memory']/gpu_info['total']*100:.1f}%")
    print("=" * 70)
    
    return recommended


def generate_training_command(config):
    """生成训练命令"""
    print("\n🚀 生成的训练命令:")
    print("-" * 70)
    
    cmd = f"""python train_fast.py \\
    --epochs 50 \\
    --batch {config['batch']} \\
    --imgsz {config['imgsz']} \\
    --eval"""
    
    print(cmd)
    print("-" * 70)
    
    # 保存到文件
    with open("optimized_training_command.txt", "w") as f:
        f.write(cmd)
    
    print("\n💡 提示: 命令已保存到 optimized_training_command.txt")


def update_config_file(config):
    """更新配置文件"""
    print("\n📝 更新配置文件...")
    
    import yaml
    
    config_path = "configs/training_params.yaml"
    
    with open(config_path, 'r') as f:
        params = yaml.safe_load(f)
    
    # 更新参数
    params['batch'] = config['batch']
    params['imgsz'] = config['imgsz']
    
    with open(config_path, 'w') as f:
        yaml.dump(params, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ 已更新 {config_path}")
    print(f"   batch: {config['batch']}")
    print(f"   imgsz: {config['imgsz']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GPU显存利用率优化')
    parser.add_argument('--test-only', action='store_true', 
                        help='仅测试，不更新配置')
    parser.add_argument('--auto-run', action='store_true',
                        help='自动运行推荐配置的训练')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🚀 GPU显存利用率优化工具")
    print("=" * 70)
    print("自动测试不同配置，找到最优训练参数")
    print("=" * 70)
    
    # 检查GPU状态
    gpu_info = check_gpu_status()
    if not gpu_info:
        return
    
    # 检查当前利用率
    current_utilization = gpu_info['allocated'] / gpu_info['total'] * 100
    print(f"\n当前显存利用率: {current_utilization:.1f}%")
    
    if current_utilization < 10:
        print("⚠️  显存利用率过低，建议优化配置")
    elif current_utilization > 80:
        print("⚠️  显存利用率过高，存在OOM风险")
    else:
        print("✅ 显存利用率正常")
    
    # 询问是否继续测试
    response = input("\n是否开始自动测试最优配置? (y/n): ")
    if response.lower() != 'y':
        print("已取消测试")
        return
    
    # 寻找最优配置
    results = find_optimal_config()
    
    # 推荐配置
    recommended = recommend_config(results, gpu_info)
    
    if not recommended:
        return
    
    # 生成训练命令
    generate_training_command(recommended)
    
    # 更新配置文件
    if not args.test_only:
        update_config_file(recommended)
        
        # 询问是否立即运行
        if args.auto_run:
            response = 'y'
        else:
            response = input("\n是否立即使用推荐配置开始训练? (y/n): ")
        
        if response.lower() == 'y':
            print("\n🚀 开始训练...")
            os.system(f"python train_fast.py --epochs 50 --batch {recommended['batch']} --imgsz {recommended['imgsz']} --eval")
    
    print("\n" + "=" * 70)
    print("✅ GPU优化完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
