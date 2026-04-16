"""
调试 Knowledge API 脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_knowledge_api():
    """测试 Knowledge API"""
    print("\n=== 测试 Knowledge API ===\n")
    
    # 测试 1: 获取分类
    print("测试 1: GET /api/v1/knowledge/categories")
    try:
        response = client.get("/api/v1/knowledge/categories")
        print(f"状态码：{response.status_code}")
        print(f"响应内容：{response.text}")
        if response.status_code != 200:
            print(f"错误详情：{response.json() if response.content else 'No content'}")
    except Exception as e:
        print(f"异常：{e}")
    
    print("\n")
    
    # 测试 2: 搜索疾病
    print("测试 2: GET /api/v1/knowledge/search?keyword=白粉病")
    try:
        response = client.get("/api/v1/knowledge/search", params={"keyword": "白粉病"})
        print(f"状态码：{response.status_code}")
        print(f"响应内容：{response.text[:500] if response.content else 'No content'}")
        if response.status_code != 200:
            print(f"错误详情：{response.json() if response.content else 'No content'}")
    except Exception as e:
        print(f"异常：{e}")
    
    print("\n")
    
    # 测试 3: 获取统计信息
    print("测试 3: GET /api/v1/stats/dashboard")
    try:
        response = client.get("/api/v1/stats/dashboard")
        print(f"状态码：{response.status_code}")
        print(f"响应内容：{response.text[:500] if response.content else 'No content'}")
        if response.status_code != 200:
            print(f"错误详情：{response.json() if response.content else 'No content'}")
    except Exception as e:
        print(f"异常：{e}")

if __name__ == "__main__":
    test_knowledge_api()
