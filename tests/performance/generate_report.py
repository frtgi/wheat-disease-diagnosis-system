# -*- coding: utf-8 -*-
"""
IWDDA Agent 性能测试报告生成器

整合所有性能测试结果，生成综合性能报告
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PerformanceReportGenerator:
    """性能报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.report = {
            'metadata': {
                'title': 'IWDDA Agent 性能测试报告',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            },
            'summary': {},
            'modules': {}
        }
    
    def generate_latency_section(self, latency_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成延迟测试报告部分"""
        return {
            'title': '推理延迟测试',
            'targets': {
                'p50': '< 1s',
                'p95': '< 3s',
                'p99': '< 5s'
            },
            'results': latency_results,
            'status': '通过' if all(v.get('passed', True) for v in latency_results.values()) else '未通过'
        }
    
    def generate_concurrency_section(self, concurrency_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成并发测试报告部分"""
        return {
            'title': '并发性能测试',
            'test_levels': [10, 50, 100],
            'metrics': ['RPS', '成功率', '延迟'],
            'results': concurrency_results,
            'status': '通过' if all(v.get('success_rate', 0) > 0.85 for v in concurrency_results.values()) else '未通过'
        }
    
    def generate_resource_section(self, resource_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成资源占用测试报告部分"""
        return {
            'title': '资源占用测试',
            'targets': {
                'gpu_memory': '< 3GB (Qwen3-VL)',
                'process_memory': '< 2GB',
                'cpu_usage': '< 80%'
            },
            'results': resource_results,
            'status': '通过' if resource_results.get('all_targets_met', False) else '未通过'
        }
    
    def generate_full_report(
        self,
        latency_results: Dict[str, Any],
        concurrency_results: Dict[str, Any],
        resource_results: Dict[str, Any],
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        生成完整性能报告
        
        :param latency_results: 延迟测试结果
        :param concurrency_results: 并发测试结果
        :param resource_results: 资源占用测试结果
        :param output_path: 输出路径
        :return: 完整报告
        """
        # 生成各模块报告
        self.report['modules']['latency'] = self.generate_latency_section(latency_results)
        self.report['modules']['concurrency'] = self.generate_concurrency_section(concurrency_results)
        self.report['modules']['resource'] = self.generate_resource_section(resource_results)
        
        # 生成摘要
        total_tests = 15  # 5 latency + 5 concurrency + 5 resource
        passed_tests = (
            sum(1 for v in latency_results.values() if v.get('passed', True)) +
            sum(1 for v in concurrency_results.values() if v.get('success_rate', 0) > 0.85) +
            (5 if resource_results.get('all_targets_met', False) else 0)
        )
        
        self.report['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'pass_rate': f'{passed_tests/total_tests*100:.1f}%',
            'overall_status': '通过' if passed_tests == total_tests else '未通过'
        }
        
        # 保存报告
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'reports/performance_report_{timestamp}.json'
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        print(f'\n📄 性能报告已保存：{output_path}')
        return self.report
    
    def print_summary(self):
        """打印报告摘要"""
        print('\n' + '=' * 70)
        print('📊 IWDDA Agent 性能测试报告摘要')
        print('=' * 70)
        
        summary = self.report.get('summary', {})
        print(f'\n总体状态：{summary.get("overall_status", "未知")}')
        print(f'测试总数：{summary.get("total_tests", 0)}')
        print(f'通过测试：{summary.get("passed_tests", 0)}')
        print(f'失败测试：{summary.get("failed_tests", 0)}')
        print(f'通过率：{summary.get("pass_rate", "0%")}')
        
        print('\n各模块测试结果:')
        for module_name, module_data in self.report.get('modules', {}).items():
            status = '✅' if module_data.get('status') == '通过' else '❌'
            print(f'  {status} {module_data.get("title", module_name)}: {module_data.get("status", "未知")}')
        
        print('\n' + '=' * 70)


def run_performance_tests_and_generate_report():
    """运行所有性能测试并生成报告"""
    print('\n' + '=' * 70)
    print('🚀 开始运行 IWDDA Agent 性能测试套件')
    print('=' * 70)
    
    # 导入测试模块
    from tests.performance.test_latency import LatencyBenchmark, generate_latency_report
    from tests.performance.test_concurrency import ConcurrencyBenchmark, generate_concurrency_report
    from tests.performance.test_resource_usage import ResourceBenchmark, generate_resource_report
    
    # 运行延迟测试
    print('\n【1/3】推理延迟测试')
    latency_bench = LatencyBenchmark(num_iterations=50)
    latency_results = {
        'perception': latency_bench.benchmark_perception_inference().to_dict(),
        'cognition': latency_bench.benchmark_cognition_inference().to_dict(),
        'planning': latency_bench.benchmark_planning_inference().to_dict(),
        'end_to_end': latency_bench.benchmark_end_to_end().to_dict()
    }
    
    # 运行并发测试
    print('\n【2/3】并发性能测试')
    concurrency_bench = ConcurrencyBenchmark()
    concurrency_metrics = concurrency_bench.run_all_tests()
    concurrency_results = {
        level: metrics.to_dict() 
        for level, metrics in concurrency_metrics.items()
    }
    
    # 运行资源测试
    print('\n【3/3】资源占用测试')
    resource_bench = ResourceBenchmark()
    resource_results = resource_bench.run_all_tests()
    
    # 生成综合报告
    print('\n📊 生成性能测试报告...')
    generator = PerformanceReportGenerator()
    full_report = generator.generate_full_report(
        latency_results=latency_results,
        concurrency_results=concurrency_results,
        resource_results=resource_results
    )
    
    # 打印摘要
    generator.print_summary()
    
    return full_report


if __name__ == '__main__':
    run_performance_tests_and_generate_report()
