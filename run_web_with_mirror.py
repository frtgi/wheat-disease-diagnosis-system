#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用HF-Mirror镜像启动Web界面

用法:
    python run_web_with_mirror.py
"""
import os
import sys

# 在导入任何其他库之前设置HF-Mirror环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['TRANSFORMERS_OFFLINE'] = '0'

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

print("🌐 已配置HF-Mirror镜像源")
print(f"   HF_ENDPOINT: {os.environ.get('HF_ENDPOINT')}")

# 现在导入并运行web应用
from src.web.app import main

if __name__ == "__main__":
    main()
