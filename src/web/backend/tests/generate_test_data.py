"""
测试图像生成脚本
运行此脚本生成测试所需的图像文件
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_data import TestDataGenerator


def main():
    """
    主函数：生成所有测试数据
    """
    test_data_dir = Path(__file__).parent / "test_data"
    
    print(f"正在生成测试数据到: {test_data_dir}")
    
    generator = TestDataGenerator(test_data_dir)
    files = generator.generate_all_test_data()
    
    print("\n生成的文件:")
    for name, path in files.items():
        print(f"  - {name}: {path}")
    
    print("\n测试数据生成完成!")


if __name__ == "__main__":
    main()
