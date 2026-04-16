# -*- coding: utf-8 -*-
"""
控制台编码配置工具

统一处理 Windows 控制台编码问题
"""
import os
import sys


def setup_console_encoding():
    """
    设置控制台编码为 UTF-8
    
    解决 Windows 控制台中文乱码问题
    """
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            os.system('chcp 65001 >nul 2>&1')
            return True
        except Exception:
            return False
    return True


def safe_print(text: str):
    """
    安全打印文本
    
    :param text: 要打印的文本
    """
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))


if __name__ == "__main__":
    setup_console_encoding()
    print("控制台编码配置完成")
    print("测试中文输出：你好，世界！")
