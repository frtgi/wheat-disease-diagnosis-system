# -*- coding: utf-8 -*-
"""
检查 API 路由
"""
import requests

BASE_URL = "http://localhost:8000"

def check_routes():
    """检查可用的 API 路由"""
    
    # 获取 OpenAPI 文档
    response = requests.get(f"{BASE_URL}/openapi.json")
    
    if response.status_code == 200:
        openapi = response.json()
        
        print("=" * 60)
        print("可用的 API 路由")
        print("=" * 60)
        
        paths = openapi.get("paths", {})
        
        for path, methods in sorted(paths.items()):
            if "diagnosis" in path or "fusion" in path:
                print(f"\n{path}")
                for method in methods.keys():
                    if method in ["get", "post", "put", "delete"]:
                        print(f"  {method.upper()}")
    else:
        print(f"获取 OpenAPI 失败: {response.status_code}")

if __name__ == "__main__":
    check_routes()
