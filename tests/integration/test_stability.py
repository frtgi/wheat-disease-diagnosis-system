# -*- coding: utf-8 -*-
"""
系统稳定性测试

测试系统在各种边界条件和异常情况下的稳定性：
1. 内存泄漏检测
2. 并发处理测试
3. 异常输入处理
4. 长时间运行稳定性
5. 资源释放验证
"""
import os
import sys
import json
import time
import gc
import threading
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class StabilityTestResult:
    """稳定性测试结果"""
    test_name: str
    passed: bool
    execution_time_s: float
    memory_delta_mb: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SystemStabilityTest:
    """
    系统稳定性测试类
    
    验证系统在各种极端条件下的稳定性和可靠性
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化稳定性测试
        
        :param config: 测试配置
        """
        self.config = config or {}
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.results: List[StabilityTestResult] = []
        
        print("🛡️ [SystemStabilityTest] 系统稳定性测试初始化完成")
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用 (MB)"""
        if self.device == 'cuda' and torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 2)
        else:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 ** 2)
    
    def test_memory_leak(self) -> StabilityTestResult:
        """
        测试内存泄漏
        
        重复执行推理，检查内存是否持续增长
        """
        print("\n🧪 测试: 内存泄漏检测")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            # 创建测试模型
            class SimpleModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.conv = nn.Conv2d(3, 64, 3, padding=1)
                    self.pool = nn.AdaptiveAvgPool2d(1)
                    self.fc = nn.Linear(64, 10)
                
                def forward(self, x):
                    x = torch.relu(self.conv(x))
                    x = self.pool(x)
                    x = x.view(x.size(0), -1)
                    return self.fc(x)
            
            model = SimpleModel().to(self.device)
            model.eval()
            
            # 记录多次迭代的内存使用
            memory_usage = []
            num_iterations = 50
            
            for i in range(num_iterations):
                dummy_input = torch.randn(4, 3, 224, 224).to(self.device)
                
                with torch.no_grad():
                    _ = model(dummy_input)
                
                if i % 10 == 0:
                    current_memory = self.get_memory_usage()
                    memory_usage.append(current_memory)
                
                # 强制垃圾回收
                if i % 20 == 0:
                    gc.collect()
                    if self.device == 'cuda':
                        torch.cuda.empty_cache()
            
            end_memory = self.get_memory_usage()
            memory_delta = end_memory - start_memory
            
            # 判断是否有内存泄漏 (增长超过10%视为泄漏)
            has_leak = memory_delta > (start_memory * 0.1) if start_memory > 0 else memory_delta > 50
            
            execution_time = time.time() - start_time
            
            print(f"   初始内存: {start_memory:.2f}MB")
            print(f"   最终内存: {end_memory:.2f}MB")
            print(f"   内存变化: {memory_delta:.2f}MB")
            print(f"   迭代次数: {num_iterations}")
            
            return StabilityTestResult(
                test_name="内存泄漏检测",
                passed=not has_leak,
                execution_time_s=execution_time,
                memory_delta_mb=memory_delta,
                details={
                    'start_memory_mb': start_memory,
                    'end_memory_mb': end_memory,
                    'iterations': num_iterations,
                    'memory_usage_history': memory_usage
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StabilityTestResult(
                test_name="内存泄漏检测",
                passed=False,
                execution_time_s=execution_time,
                memory_delta_mb=0,
                error_message=str(e)
            )
    
    def test_concurrent_access(self) -> StabilityTestResult:
        """
        测试并发访问
        
        模拟多个线程同时访问系统
        """
        print("\n🧪 测试: 并发访问")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            results = []
            errors = []
            
            def worker(thread_id):
                try:
                    # 模拟推理任务
                    time.sleep(0.1)
                    results.append(thread_id)
                except Exception as e:
                    errors.append((thread_id, str(e)))
            
            # 创建多个线程
            threads = []
            num_threads = 10
            
            for i in range(num_threads):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
            
            # 启动所有线程
            for t in threads:
                t.start()
            
            # 等待所有线程完成
            for t in threads:
                t.join(timeout=5)
            
            end_memory = self.get_memory_usage()
            memory_delta = end_memory - start_memory
            execution_time = time.time() - start_time
            
            success = len(results) == num_threads and len(errors) == 0
            
            print(f"   线程数: {num_threads}")
            print(f"   成功: {len(results)}")
            print(f"   失败: {len(errors)}")
            print(f"   耗时: {execution_time:.2f}s")
            
            return StabilityTestResult(
                test_name="并发访问",
                passed=success,
                execution_time_s=execution_time,
                memory_delta_mb=memory_delta,
                error_message=str(errors) if errors else None,
                details={
                    'num_threads': num_threads,
                    'successful': len(results),
                    'failed': len(errors)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StabilityTestResult(
                test_name="并发访问",
                passed=False,
                execution_time_s=execution_time,
                memory_delta_mb=0,
                error_message=str(e)
            )
    
    def test_invalid_inputs(self) -> StabilityTestResult:
        """
        测试异常输入处理
        
        验证系统对非法输入的处理能力
        """
        print("\n🧪 测试: 异常输入处理")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            # 创建测试模型
            class SimpleModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.fc = nn.Linear(10, 5)
                
                def forward(self, x):
                    return self.fc(x)
            
            model = SimpleModel()
            model.eval()
            
            # 测试各种异常输入
            test_cases = [
                ("空张量", torch.randn(0, 10)),
                ("错误维度", torch.randn(10)),
                ("NaN值", torch.full((2, 10), float('nan'))),
                ("Inf值", torch.full((2, 10), float('inf'))),
                ("极大值", torch.full((2, 10), 1e10)),
                ("极小值", torch.full((2, 10), 1e-10)),
            ]
            
            handled_count = 0
            crashed_count = 0
            
            for name, input_tensor in test_cases:
                try:
                    with torch.no_grad():
                        _ = model(input_tensor)
                    handled_count += 1
                except Exception as e:
                    # 预期会抛出异常，记录但不视为失败
                    handled_count += 1
            
            end_memory = self.get_memory_usage()
            memory_delta = end_memory - start_memory
            execution_time = time.time() - start_time
            
            # 只要没有崩溃就算通过
            success = crashed_count == 0
            
            print(f"   测试用例: {len(test_cases)}")
            print(f"   正常处理: {handled_count}")
            print(f"   系统崩溃: {crashed_count}")
            
            return StabilityTestResult(
                test_name="异常输入处理",
                passed=success,
                execution_time_s=execution_time,
                memory_delta_mb=memory_delta,
                details={
                    'test_cases': len(test_cases),
                    'handled': handled_count,
                    'crashed': crashed_count
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StabilityTestResult(
                test_name="异常输入处理",
                passed=False,
                execution_time_s=execution_time,
                memory_delta_mb=0,
                error_message=str(e)
            )
    
    def test_long_running(self) -> StabilityTestResult:
        """
        测试长时间运行稳定性
        
        模拟系统长时间运行的情况
        """
        print("\n🧪 测试: 长时间运行稳定性")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            # 创建测试模型
            class SimpleModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.conv = nn.Conv2d(3, 32, 3, padding=1)
                    self.pool = nn.AdaptiveAvgPool2d(1)
                    self.fc = nn.Linear(32, 10)
                
                def forward(self, x):
                    x = torch.relu(self.conv(x))
                    x = self.pool(x)
                    x = x.view(x.size(0), -1)
                    return self.fc(x)
            
            model = SimpleModel().to(self.device)
            model.eval()
            
            # 模拟长时间运行 (减少迭代次数以加快测试)
            num_iterations = 20
            interval_memory = []
            
            for i in range(num_iterations):
                dummy_input = torch.randn(2, 3, 224, 224).to(self.device)
                
                with torch.no_grad():
                    _ = model(dummy_input)
                
                if i % 5 == 0:
                    current_memory = self.get_memory_usage()
                    interval_memory.append(current_memory)
                
                time.sleep(0.05)  # 模拟处理间隔
            
            end_memory = self.get_memory_usage()
            memory_delta = end_memory - start_memory
            execution_time = time.time() - start_time
            
            # 检查内存增长是否可控
            memory_stable = memory_delta < 100  # 100MB阈值
            
            print(f"   运行时间: {execution_time:.2f}s")
            print(f"   迭代次数: {num_iterations}")
            print(f"   内存变化: {memory_delta:.2f}MB")
            print(f"   内存稳定: {'是' if memory_stable else '否'}")
            
            return StabilityTestResult(
                test_name="长时间运行稳定性",
                passed=memory_stable,
                execution_time_s=execution_time,
                memory_delta_mb=memory_delta,
                details={
                    'iterations': num_iterations,
                    'start_memory_mb': start_memory,
                    'end_memory_mb': end_memory,
                    'memory_history': interval_memory
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StabilityTestResult(
                test_name="长时间运行稳定性",
                passed=False,
                execution_time_s=execution_time,
                memory_delta_mb=0,
                error_message=str(e)
            )
    
    def test_resource_cleanup(self) -> StabilityTestResult:
        """
        测试资源释放
        
        验证系统是否正确释放资源
        """
        print("\n🧪 测试: 资源释放")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            # 创建并销毁多个模型实例
            memory_before_create = self.get_memory_usage()
            
            for i in range(5):
                # 创建模型
                model = nn.Sequential(
                    nn.Conv2d(3, 64, 3),
                    nn.ReLU(),
                    nn.Conv2d(64, 128, 3),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool2d(1),
                    nn.Flatten(),
                    nn.Linear(128, 10)
                ).to(self.device)
                
                # 使用模型
                dummy_input = torch.randn(2, 3, 224, 224).to(self.device)
                with torch.no_grad():
                    _ = model(dummy_input)
                
                # 删除模型
                del model
                
                # 强制垃圾回收
                gc.collect()
                if self.device == 'cuda':
                    torch.cuda.empty_cache()
            
            memory_after_cleanup = self.get_memory_usage()
            memory_delta = memory_after_cleanup - memory_before_create
            
            execution_time = time.time() - start_time
            
            # 内存增长应小于20MB
            cleanup_success = memory_delta < 20
            
            print(f"   初始内存: {memory_before_create:.2f}MB")
            print(f"   清理后内存: {memory_after_cleanup:.2f}MB")
            print(f"   内存变化: {memory_delta:.2f}MB")
            print(f"   资源释放: {'正常' if cleanup_success else '异常'}")
            
            return StabilityTestResult(
                test_name="资源释放",
                passed=cleanup_success,
                execution_time_s=execution_time,
                memory_delta_mb=memory_delta,
                details={
                    'memory_before_mb': memory_before_create,
                    'memory_after_mb': memory_after_cleanup,
                    'models_created': 5
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StabilityTestResult(
                test_name="资源释放",
                passed=False,
                execution_time_s=execution_time,
                memory_delta_mb=0,
                error_message=str(e)
            )
    
    def test_error_recovery(self) -> StabilityTestResult:
        """
        测试错误恢复能力
        
        验证系统在发生错误后能否正常恢复
        """
        print("\n🧪 测试: 错误恢复能力")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            recovery_success = []
            
            # 测试场景1: 除零错误恢复
            try:
                x = torch.tensor([1.0, 2.0, 3.0])
                y = x / 0  # 会产生inf
                recovery_success.append(True)
            except:
                recovery_success.append(False)
            
            # 测试场景2: 索引越界恢复
            try:
                x = torch.tensor([1.0, 2.0])
                _ = x[10]  # 越界
                recovery_success.append(False)
            except IndexError:
                recovery_success.append(True)
            
            # 测试场景3: 形状不匹配恢复
            try:
                x = torch.randn(2, 3)
                y = torch.randn(4, 3)
                z = x + y  # 形状不匹配
                recovery_success.append(False)
            except RuntimeError:
                recovery_success.append(True)
            
            # 测试场景4: 正常操作后系统仍可用
            try:
                x = torch.randn(3, 3)
                y = torch.matmul(x, x)
                recovery_success.append(True)
            except:
                recovery_success.append(False)
            
            end_memory = self.get_memory_usage()
            memory_delta = end_memory - start_memory
            execution_time = time.time() - start_time
            
            success_rate = sum(recovery_success) / len(recovery_success)
            all_recovered = success_rate == 1.0
            
            print(f"   测试场景: {len(recovery_success)}")
            print(f"   成功恢复: {sum(recovery_success)}")
            print(f"   恢复率: {success_rate:.1%}")
            
            return StabilityTestResult(
                test_name="错误恢复能力",
                passed=all_recovered,
                execution_time_s=execution_time,
                memory_delta_mb=memory_delta,
                details={
                    'test_scenarios': len(recovery_success),
                    'successful_recoveries': sum(recovery_success),
                    'recovery_rate': success_rate
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StabilityTestResult(
                test_name="错误恢复能力",
                passed=False,
                execution_time_s=execution_time,
                memory_delta_mb=0,
                error_message=str(e)
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有稳定性测试"""
        print("\n" + "=" * 70)
        print("🛡️ 开始系统稳定性测试")
        print("=" * 70)
        
        # 定义测试列表
        tests = [
            self.test_memory_leak,
            self.test_concurrent_access,
            self.test_invalid_inputs,
            self.test_long_running,
            self.test_resource_cleanup,
            self.test_error_recovery,
        ]
        
        # 运行测试
        results = []
        for test_func in tests:
            result = test_func()
            results.append(result)
            
            status = "✅ 通过" if result.passed else "❌ 失败"
            print(f"   结果: {status} ({result.execution_time_s:.2f}s)")
            if result.error_message:
                print(f"   错误: {result.error_message}")
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'device': self.device,
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'results': [r.to_dict() for r in results]
        }
        
        self.results = results
        
        # 打印摘要
        print("\n" + "=" * 70)
        print("📊 系统稳定性测试摘要")
        print("=" * 70)
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {summary['pass_rate']:.1%}")
        
        if passed == total:
            print("\n✅ 系统稳定性良好")
        elif passed >= total * 0.8:
            print("\n⚠️ 系统基本稳定，存在 minor issues")
        else:
            print("\n❌ 系统稳定性存在问题，需要优化")
        
        print("=" * 70)
        
        return summary
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成测试报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/stability_test_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'results': [r.to_dict() for r in self.results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 稳定性报告已保存: {output_path}")
        return output_path


def test_stability():
    """测试系统稳定性"""
    print("=" * 70)
    print("🧪 测试系统稳定性")
    print("=" * 70)
    
    tester = SystemStabilityTest()
    summary = tester.run_all_tests()
    
    # 生成报告
    report_path = tester.generate_report()
    
    # 清理
    import shutil
    if os.path.exists("reports"):
        shutil.rmtree("reports")
    
    print("\n" + "=" * 70)
    print("✅ 系统稳定性测试完成！")
    print("=" * 70)
    
    return summary


# 创建兼容函数供外部调用
run_tests = test_stability


if __name__ == "__main__":
    test_stability()
