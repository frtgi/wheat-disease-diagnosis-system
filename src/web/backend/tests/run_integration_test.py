"""
前后端集成测试脚本
测试 Qwen3-VL-4B INT4 量化后的系统功能
"""
import httpx
import json
import time

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_health_database():
    """测试数据库健康检查"""
    print("\n=== 测试 1: 数据库健康检查 ===")
    try:
        resp = httpx.get(f"{BASE_URL}{API_PREFIX}/health/database", timeout=10)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_health_startup():
    """测试启动状态"""
    print("\n=== 测试 2: 启动状态 ===")
    try:
        resp = httpx.get(f"{BASE_URL}{API_PREFIX}/health/startup", timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(f"状态: {data.get('status')}")
        print(f"进度: {data.get('progress')}%")
        print(f"阶段: {data.get('phase')}")
        return resp.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_health_ready():
    """测试就绪状态"""
    print("\n=== 测试 3: 就绪状态检查 ===")
    try:
        resp = httpx.get(f"{BASE_URL}{API_PREFIX}/health/ready", timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(f"就绪状态: {data.get('ready', data.get('status'))}")
        print(f"降级模式: {data.get('degraded', False)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_health_components():
    """测试组件状态"""
    print("\n=== 测试 4: 组件状态 ===")
    try:
        resp = httpx.get(f"{BASE_URL}{API_PREFIX}/health/components", timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        
        db_status = data.get("database", {}).get("status")
        yolo_loaded = data.get("yolo", {}).get("is_loaded")
        qwen_loaded = data.get("qwen", {}).get("is_loaded")
        
        print(f"数据库状态: {db_status}")
        print(f"YOLO 加载: {yolo_loaded}")
        print(f"Qwen 加载: {qwen_loaded}")
        
        return yolo_loaded and qwen_loaded
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_ai_health():
    """测试 AI 健康检查"""
    print("\n=== 测试 5: AI 健康检查 ===")
    try:
        resp = httpx.get(f"{BASE_URL}{API_PREFIX}/diagnosis/health/ai", timeout=10)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_user_register():
    """测试用户注册"""
    print("\n=== 测试 6: 用户注册 ===")
    try:
        username = f"testuser_{int(time.time())}"
        resp = httpx.post(
            f"{BASE_URL}{API_PREFIX}/users/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "Test123456"
            },
            timeout=10
        )
        print(f"状态码: {resp.status_code}")
        print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)[:500]}")
        return resp.status_code == 200, username
    except Exception as e:
        print(f"错误: {e}")
        return False, None

def test_user_login(username):
    """测试用户登录"""
    print("\n=== 测试 7: 用户登录 ===")
    try:
        resp = httpx.post(
            f"{BASE_URL}{API_PREFIX}/users/login",
            json={"username": username, "password": "Test123456"},
            timeout=10
        )
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        if "access_token" in data:
            print(f"登录成功，获取到 access_token")
            return True, data["access_token"]
        else:
            print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            return False, None
    except Exception as e:
        print(f"错误: {e}")
        return False, None

def main():
    """主测试函数"""
    print("=" * 60)
    print("WheatAgent 前后端集成测试")
    print("测试 Qwen3-VL-4B INT4 量化后的系统功能")
    print("=" * 60)
    
    results = []
    
    # 测试 1: 数据库健康检查
    results.append(("数据库健康检查", test_health_database()))
    
    # 测试 2: 启动状态
    results.append(("启动状态", test_health_startup()))
    
    # 测试 3: 就绪状态
    results.append(("就绪状态", test_health_ready()))
    
    # 测试 4: 组件状态
    results.append(("组件状态", test_health_components()))
    
    # 测试 5: AI 健康检查
    results.append(("AI 健康检查", test_ai_health()))
    
    # 测试 6: 用户注册
    success, username = test_user_register()
    results.append(("用户注册", success))
    
    # 测试 7: 用户登录
    if username:
        success, token = test_user_login(username)
        results.append(("用户登录", success))
    
    # 打印结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
