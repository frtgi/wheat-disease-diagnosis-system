# -*- coding: utf-8 -*-
"""
显存优化器模块
自动检测最优batch size，实时监控显存使用
针对RTX 3050 4GB显存优化
"""
import os
import sys
import torch
import yaml
import time
from pathlib import Path
from typing import Dict, Tuple, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MemoryOptimizer:
    """
    显存优化器
    
    功能:
    1. 自动检测最优batch size
    2. 实时监控显存使用
    3. 动态调整训练参数
    4. OOM预防和恢复
    """
    
    def __init__(self, target_utilization: float = 0.65, safety_margin: float = 0.9):
        """
        初始化显存优化器
        
        Args:
            target_utilization: 目标显存利用率 (默认65%)
            safety_margin: 安全余量 (默认90%，即使用90%的可用显存)
        """
        self.target_utilization = target_utilization
        self.safety_margin = safety_margin
        self.gpu_info = self._get_gpu_info()
        self.optimal_config = None
        
    def _get_gpu_info(self) -> Dict:
        """获取GPU信息"""
        if not torch.cuda.is_available():
            return None
        
        gpu_name = torch.cuda.get_device_name(0)
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        # 系统保留显存
        reserved_memory = 0.3  # GB
        available_memory = total_memory - reserved_memory
        
        return {
            'name': gpu_name,
            'total': total_memory,
            'available': available_memory,
            'target': available_memory * self.target_utilization,
            'max_safe': available_memory * self.safety_margin
        }
    
    def test_batch_size(self, batch_size: int, img_size: int = 640, 
                       model_name: str = 'yolov8n.pt') -> Tuple[bool, float, str]:
        """
        测试特定batch size是否可行
        
        Args:
            batch_size: 批次大小
            img_size: 图像尺寸
            model_name: 模型名称
        
        Returns:
            (success, memory_used_gb, error_msg)
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            return False, 0.0, "未安装ultralytics"
        
        # 清空缓存
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        mem_before = torch.cuda.memory_allocated(0) / 1024**3
        
        try:
            # 加载模型
            model = YOLO(model_name)
            
            # 尝试训练一个batch
            data_yaml = os.path.abspath("configs/wheat_disease.yaml")
            
            model.train(
                data=data_yaml,
                epochs=1,
                batch=batch_size,
                imgsz=img_size,
                device=0,
                workers=0,
                cache=False,
                amp=True,
                optimizer='AdamW',
                lr0=0.001,
                verbose=False,
                plots=False,
                save=False,
            )
            
            # 获取显存使用
            mem_after = torch.cuda.memory_allocated(0) / 1024**3
            mem_used = mem_after - mem_before
            
            return True, mem_used, None
            
        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str or "cuda" in error_str:
                return False, 0.0, f"显存不足"
            return False, 0.0, f"错误: {str(e)[:50]}"
        except Exception as e:
            return False, 0.0, f"未知错误: {str(e)[:50]}"
        finally:
            # 清理
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def find_optimal_batch_size(self, img_size: int = 640, 
                                test_batches: list = None) -> Dict:
        """
        自动寻找最优batch size
        
        Args:
            img_size: 图像尺寸
            test_batches: 测试的batch size列表
        
        Returns:
            最优配置字典
        """
        if self.gpu_info is None:
            return {'batch': 16, 'img_size': img_size, 'memory': 0}
        
        if test_batches is None:
            # 根据GPU显存确定测试范围
            if self.gpu_info['total'] >= 8:
                test_batches = [16, 24, 32, 48, 64]
            elif self.gpu_info['total'] >= 6:
                test_batches = [16, 24, 32, 40]
            else:  # 4GB
                test_batches = [16, 20, 24, 28, 32]
        
        print(f"\n🔍 自动检测最优batch size (目标显存: {self.gpu_info['target']:.2f}GB)")
        print("=" * 70)
        
        results = []
        
        for batch in test_batches:
            print(f"测试 batch={batch}, imgsz={img_size}...", end=' ')
            
            success, mem_used, error = self.test_batch_size(batch, img_size)
            
            if success:
                utilization = mem_used / self.gpu_info['total'] * 100
                print(f"✅ 成功 (显存: {mem_used:.2f}GB, 利用率: {utilization:.1f}%)")
                results.append({
                    'batch': batch,
                    'img_size': img_size,
                    'memory': mem_used,
                    'utilization': utilization,
                    'feasible': True
                })
            else:
                print(f"❌ 失败 ({error})")
                results.append({
                    'batch': batch,
                    'img_size': img_size,
                    'memory': 0,
                    'utilization': 0,
                    'feasible': False,
                    'error': error
                })
        
        # 选择最优配置
        feasible_results = [r for r in results if r['feasible']]
        
        if not feasible_results:
            print("⚠️  没有可行的配置，使用默认batch=16")
            return {'batch': 16, 'img_size': img_size, 'memory': 0}
        
        # 选择最接近目标利用率的配置
        optimal = min(feasible_results, 
                     key=lambda x: abs(x['utilization'] - self.target_utilization * 100))
        
        print("\n" + "=" * 70)
        print(f"🎯 最优配置: batch={optimal['batch']}, imgsz={optimal['img_size']}")
        print(f"   显存占用: {optimal['memory']:.2f}GB / {self.gpu_info['total']:.2f}GB")
        print(f"   利用率: {optimal['utilization']:.1f}%")
        print("=" * 70)
        
        self.optimal_config = optimal
        return optimal
    
    def monitor_memory(self, interval: int = 5):
        """
        实时监控显存使用
        
        Args:
            interval: 监控间隔（秒）
        """
        if self.gpu_info is None:
            print("❌ CUDA不可用，无法监控")
            return
        
        print(f"\n📊 开始监控显存使用 (间隔: {interval}s)")
        print("按 Ctrl+C 停止监控")
        print("-" * 70)
        
        try:
            while True:
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                reserved = torch.cuda.memory_reserved(0) / 1024**3
                utilization = allocated / self.gpu_info['total'] * 100
                
                # 状态指示
                if utilization < 50:
                    status = "🟢 正常"
                elif utilization < 75:
                    status = "🟡 注意"
                elif utilization < 90:
                    status = "🟠 警告"
                else:
                    status = "🔴 危险"
                
                print(f"\r[{time.strftime('%H:%M:%S')}] "
                      f"已分配: {allocated:.2f}GB | "
                      f"保留: {reserved:.2f}GB | "
                      f"利用率: {utilization:.1f}% {status}", end='')
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✅ 监控已停止")
    
    def get_training_config(self) -> Dict:
        """
        获取训练配置
        
        Returns:
            训练参数字典
        """
        if self.optimal_config is None:
            self.find_optimal_batch_size()
        
        return self.optimal_config
    
    def print_gpu_info(self):
        """打印GPU信息"""
        if self.gpu_info is None:
            print("❌ CUDA不可用")
            return
        
        print("=" * 70)
        print("🔧 GPU信息")
        print("=" * 70)
        print(f"型号: {self.gpu_info['name']}")
        print(f"总显存: {self.gpu_info['total']:.2f} GB")
        print(f"可用显存: {self.gpu_info['available']:.2f} GB")
        print(f"目标使用: {self.gpu_info['target']:.2f} GB ({self.target_utilization*100:.0f}%)")
        print(f"安全上限: {self.gpu_info['max_safe']:.2f} GB ({self.safety_margin*100:.0f}%)")
        print("=" * 70)


def main():
    """测试显存优化器"""
    print("\n" + "=" * 70)
    print("🚀 显存优化器测试")
    print("=" * 70)
    
    # 创建优化器
    optimizer = MemoryOptimizer(target_utilization=0.65)
    
    # 打印GPU信息
    optimizer.print_gpu_info()
    
    # 寻找最优配置
    config = optimizer.find_optimal_batch_size()
    
    # 询问是否监控
    response = input("\n是否开始监控显存使用? (y/n): ")
    if response.lower() == 'y':
        optimizer.monitor_memory(interval=2)
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
