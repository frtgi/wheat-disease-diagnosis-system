# -*- coding: utf-8 -*-
"""
集成测试主入口

整合所有集成测试，提供统一的测试执行接口
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入各个测试模块
from tests.integration.test_end_to_end import EndToEndTestSuite
from tests.integration.test_module_integration import ModuleIntegrationTest
from tests.integration.test_performance import PerformanceBenchmarkTest
from tests.integration.test_stability import SystemStabilityTest


class IntegrationTestSuite:
    """
    集成测试套件主类
    
    整合所有集成测试，提供统一的测试执行和报告生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化集成测试套件
        
        :param config: 测试配置
        """
        self.config = config or {}
        self.results: Dict[str, Any] = {}
        
        print("🧪 [IntegrationTestSuite] 集成测试套件初始化完成")
    
    def run_end_to_end_tests(self) -> Dict[str, Any]:
        """运行端到端测试"""
        print("\n" + "=" * 70)
        print("🚀 执行端到端测试")
        print("=" * 70)
        
        suite = EndToEndTestSuite(self.config)
        return suite.run_all_tests()
    
    def run_module_integration_tests(self) -> Dict[str, Any]:
        """运行模块集成测试"""
        print("\n" + "=" * 70)
        print("🔗 执行模块集成测试")
        print("=" * 70)
        
        tester = ModuleIntegrationTest(self.config)
        return tester.run_all_tests()
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """运行性能基准测试"""
        print("\n" + "=" * 70)
        print("⚡ 执行性能基准测试")
        print("=" * 70)
        
        tester = PerformanceBenchmarkTest(self.config)
        return tester.run_all_tests()
    
    def run_stability_tests(self) -> Dict[str, Any]:
        """运行稳定性测试"""
        print("\n" + "=" * 70)
        print("🛡️ 执行系统稳定性测试")
        print("=" * 70)
        
        tester = SystemStabilityTest(self.config)
        return tester.run_all_tests()
    
    def run_all_tests(self, test_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        运行所有集成测试
        
        :param test_categories: 指定要运行的测试类别，None表示运行所有
        :return: 完整测试结果
        """
        print("\n" + "=" * 70)
        print("🎯 WheatAgent 集成测试套件")
        print("=" * 70)
        
        start_time = time.time()
        
        # 定义测试类别
        all_categories = {
            'end_to_end': self.run_end_to_end_tests,
            'module_integration': self.run_module_integration_tests,
            'performance': self.run_performance_tests,
            'stability': self.run_stability_tests,
        }
        
        # 选择要运行的测试
        if test_categories is None:
            categories_to_run = all_categories
        else:
            categories_to_run = {
                k: v for k, v in all_categories.items() 
                if k in test_categories
            }
        
        # 运行测试
        results = {}
        for category, test_func in categories_to_run.items():
            try:
                results[category] = test_func()
            except Exception as e:
                print(f"\n❌ {category} 测试失败: {e}")
                results[category] = {
                    'error': str(e),
                    'passed': 0,
                    'total': 0
                }
        
        total_time = time.time() - start_time
        
        # 统计总体结果
        total_tests = sum(
            r.get('total_tests', 0) 
            for r in results.values() 
            if isinstance(r, dict)
        )
        total_passed = sum(
            r.get('passed', 0) 
            for r in results.values() 
            if isinstance(r, dict)
        )
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_time_s': total_time,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_tests - total_passed,
            'overall_pass_rate': total_passed / total_tests if total_tests > 0 else 0,
            'categories': results
        }
        
        self.results = summary
        
        # 打印总体摘要
        print("\n" + "=" * 70)
        print("📊 集成测试总体摘要")
        print("=" * 70)
        print(f"总测试数: {total_tests}")
        print(f"通过: {total_passed}")
        print(f"失败: {total_tests - total_passed}")
        print(f"通过率: {summary['overall_pass_rate']:.1%}")
        print(f"总耗时: {total_time:.2f}s")
        
        print("\n各分类结果:")
        for category, result in results.items():
            if isinstance(result, dict) and 'pass_rate' in result:
                status = "✅" if result['pass_rate'] >= 0.8 else "⚠️" if result['pass_rate'] >= 0.5 else "❌"
                print(f"   {status} {category}: {result.get('passed', 0)}/{result.get('total_tests', 0)}")
        
        print("=" * 70)
        
        return summary
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        生成完整测试报告
        
        :param output_path: 报告输出路径
        :return: 报告路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/integration_test_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 集成测试报告已保存: {output_path}")
        return output_path
    
    def generate_html_report(self, output_path: Optional[str] = None) -> str:
        """
        生成HTML格式的测试报告
        
        :param output_path: 报告输出路径
        :return: 报告路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/integration_test_report_{timestamp}.html"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 生成HTML报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WheatAgent 集成测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin-top: 0;
            color: #333;
        }}
        .metric {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .pass-rate {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .pass-rate.high {{ color: #4caf50; }}
        .pass-rate.medium {{ color: #ff9800; }}
        .pass-rate.low {{ color: #f44336; }}
        .category {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .category h3 {{
            margin-top: 0;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-pass {{ color: #4caf50; }}
        .status-fail {{ color: #f44336; }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌾 WheatAgent 集成测试报告</h1>
        <p class="timestamp">生成时间: {self.results.get('timestamp', 'N/A')}</p>
    </div>
    
    <div class="summary">
        <div class="card">
            <h3>总测试数</h3>
            <div class="metric">{self.results.get('total_tests', 0)}</div>
        </div>
        <div class="card">
            <h3>通过</h3>
            <div class="metric" style="color: #4caf50;">{self.results.get('total_passed', 0)}</div>
        </div>
        <div class="card">
            <h3>失败</h3>
            <div class="metric" style="color: #f44336;">{self.results.get('total_failed', 0)}</div>
        </div>
        <div class="card">
            <h3>通过率</h3>
            <div class="pass-rate {'high' if self.results.get('overall_pass_rate', 0) >= 0.8 else 'medium' if self.results.get('overall_pass_rate', 0) >= 0.5 else 'low'}">
                {self.results.get('overall_pass_rate', 0):.1%}
            </div>
        </div>
    </div>
"""
        
        # 添加各分类详情
        for category, result in self.results.get('categories', {}).items():
            if isinstance(result, dict):
                html_content += f"""
    <div class="category">
        <h3>{category.replace('_', ' ').title()}</h3>
        <p>通过率: {result.get('pass_rate', 0):.1%} | 
           通过: {result.get('passed', 0)} | 
           失败: {result.get('failed', 0)}</p>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML报告已保存: {output_path}")
        return output_path


def run_integration_tests():
    """运行所有集成测试"""
    print("=" * 70)
    print("🧪 WheatAgent 集成测试")
    print("=" * 70)
    
    # 创建测试套件
    suite = IntegrationTestSuite()
    
    # 运行所有测试
    results = suite.run_all_tests()
    
    # 生成报告
    json_report = suite.generate_report()
    html_report = suite.generate_html_report()
    
    print("\n" + "=" * 70)
    print("✅ 集成测试完成！")
    print(f"   JSON报告: {json_report}")
    print(f"   HTML报告: {html_report}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_integration_tests()
