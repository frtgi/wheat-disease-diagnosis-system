#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WheatAgent 测试运行脚本

运行所有集成测试并生成报告

用法:
    python run_tests.py                    # 运行所有测试
    python run_tests.py --category e2e     # 仅运行端到端测试
    python run_tests.py --category perf    # 仅运行性能测试
    python run_tests.py --category all     # 运行所有测试（默认）
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='WheatAgent 集成测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                    # 运行所有测试
  python run_tests.py -c e2e             # 仅运行端到端测试
  python run_tests.py -c module          # 仅运行模块集成测试
  python run_tests.py -c perf            # 仅运行性能测试
  python run_tests.py -c stability       # 仅运行稳定性测试
  python run_tests.py --html             # 生成HTML报告
        """
    )
    
    parser.add_argument(
        '-c', '--category',
        choices=['all', 'e2e', 'module', 'perf', 'stability'],
        default='all',
        help='选择要运行的测试类别 (默认: all)'
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help='生成HTML格式的报告'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='reports',
        help='报告输出目录 (默认: reports)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🌾 WheatAgent 测试运行器")
    print("=" * 70)
    
    # 导入测试套件
    try:
        from tests.integration import IntegrationTestSuite
    except ImportError as e:
        print(f"\n❌ 导入测试套件失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    
    # 创建测试套件
    suite = IntegrationTestSuite()
    
    # 映射类别名称
    category_map = {
        'all': None,
        'e2e': ['end_to_end'],
        'module': ['module_integration'],
        'perf': ['performance'],
        'stability': ['stability']
    }
    
    categories = category_map[args.category]
    
    # 运行测试
    try:
        results = suite.run_all_tests(test_categories=categories)
        
        # 生成报告
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        
        # JSON报告
        json_path = output_dir / f"test_report_{results['timestamp'][:19].replace(':', '-')}.json"
        suite.generate_report(str(json_path))
        
        # HTML报告
        if args.html:
            html_path = output_dir / f"test_report_{results['timestamp'][:19].replace(':', '-')}.html"
            suite.generate_html_report(str(html_path))
        
        # 返回码
        pass_rate = results.get('overall_pass_rate', 0)
        if pass_rate >= 0.8:
            print("\n✅ 测试通过！")
            return 0
        elif pass_rate >= 0.5:
            print("\n⚠️ 测试部分通过，存在一些问题")
            return 1
        else:
            print("\n❌ 测试失败")
            return 2
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
