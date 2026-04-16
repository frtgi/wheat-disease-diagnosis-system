# -*- coding: utf-8 -*-
"""
测试启动脚本

解决Windows PowerShell管道编码问题
"""
import os
import sys
import subprocess

def main():
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    
    # Windows下设置控制台代码页
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    
    # 运行测试
    test_script = os.path.join(os.path.dirname(__file__), 'tests', 'test_system_integration.py')
    result = subprocess.run(
        [sys.executable, test_script],
        env=env,
        cwd=os.path.dirname(__file__)
    )
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
