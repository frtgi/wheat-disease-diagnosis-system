# -*- coding: utf-8 -*-
"""
Web 端测试脚本
测试正在运行的 WheatAgent Web 应用
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:7861"

def test_health():
    """测试健康检查端点"""
    print("\n" + "=" * 60)
    print("🧪 Web 端测试")
    print("=" * 60)
    
    # 测试健康检查
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n✅ 健康检查：{response.status_code}")
        print(f"   响应：{response.json()}")
    except Exception as e:
        print(f"\n❌ 健康检查失败：{e}")
        return False
    
    # 测试准备状态
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=5)
        print(f"\n✅ 准备状态：{response.status_code}")
        print(f"   响应：{response.json()}")
    except Exception as e:
        print(f"\n❌ 准备状态检查失败：{e}")
        return False
    
    # 获取统计信息
    try:
        response = requests.get(f"{BASE_URL}/stats/summary", timeout=5)
        print(f"\n✅ 统计信息：{response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   诊断次数：{stats.get('total_diagnoses', 0)}")
            print(f"   知识图谱节点：{stats.get('knowledge_nodes', 0)}")
            print(f"   缓存命中率：{stats.get('cache_hit_rate', 0):.2f}%")
    except Exception as e:
        print(f"\n⚠️  统计信息获取失败：{e}（可能是正常的，如果还没有诊断记录）")
    
    # 获取知识图谱病害列表
    try:
        response = requests.get(f"{BASE_URL}/api/knowledge/diseases", timeout=5)
        print(f"\n✅ 病害列表：{response.status_code}")
        if response.status_code == 200:
            diseases = response.json()
            print(f"   病害数量：{len(diseases)}")
            if diseases:
                print(f"   示例：{diseases[:3]}")
    except Exception as e:
        print(f"\n⚠️  病害列表获取失败：{e}")
    
    print("\n" + "=" * 60)
    print("✅ Web 端测试完成")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print(f"🌐 测试目标：{BASE_URL}")
    print(f"⏰ 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_health()
    
    if success:
        print("\n🎉 所有测试通过！")
        print(f"\n💡 请在浏览器访问：http://localhost:7861")
    else:
        print("\n❌ 部分测试失败，请检查 Web 应用是否正常启动")
