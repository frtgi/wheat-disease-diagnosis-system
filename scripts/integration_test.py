import asyncio
import httpx
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
TEST_RESULTS = []

async def test_api(client, name, method, endpoint, json_data=None, form_data=None, expected_status=200, headers=None):
    """测试API端点"""
    start_time = time.time()
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
        elif method == "POST" and form_data:
            response = await client.post(f"{BASE_URL}{endpoint}", data=form_data, headers=headers)
        else:
            response = await client.post(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
        
        elapsed = (time.time() - start_time) * 1000
        success = response.status_code == expected_status
        
        try:
            resp_data = response.json()
        except:
            resp_data = response.text[:200]
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "success": success,
            "elapsed_ms": round(elapsed, 2),
            "response": resp_data
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "status_code": 0,
            "expected_status": expected_status,
            "success": False,
            "elapsed_ms": round(elapsed, 2),
            "error": str(e)
        }
    
    TEST_RESULTS.append(result)
    status = "✓" if result["success"] else "✗"
    print(f"{status} {name}: {result['status_code']} ({result['elapsed_ms']}ms)")
    return result

async def main():
    """执行集成测试"""
    print("=" * 60)
    print(f"WheatAgent 集成测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. 健康检查
        print("\n[1] 健康检查测试")
        await test_api(client, "健康检查", "GET", "/api/v1/health")
        
        # 2. 用户认证测试
        print("\n[2] 用户认证测试")
        test_user = {
            "username": f"test_user_{int(time.time())}",
            "password": "Test@123456",
            "email": f"test_{int(time.time())}@test.com"
        }
        await test_api(client, "用户注册", "POST", "/api/v1/users/register", json_data=test_user)
        
        login_result = await test_api(client, "用户登录", "POST", "/api/v1/users/login", json_data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        token = None
        if login_result["success"] and isinstance(login_result["response"], dict):
            token = login_result["response"].get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # 3. 诊断服务测试
        print("\n[3] 诊断服务测试")
        await test_api(client, "文本诊断", "POST", "/api/v1/diagnosis/text", 
            form_data={"symptoms": "小麦叶片出现黄色条纹，叶片干枯"},
            headers=headers
        )
        
        # 4. 知识库测试
        print("\n[4] 知识库测试")
        await test_api(client, "知识库搜索", "GET", "/api/v1/knowledge/search?keyword=锈病", expected_status=200)
        await test_api(client, "知识库分类", "GET", "/api/v1/knowledge/categories", expected_status=200)
        
        # 5. AI诊断测试
        print("\n[5] AI诊断测试")
        await test_api(client, "AI文本诊断", "POST", "/api/v1/ai-diagnosis/text",
            json_data={"symptoms": "小麦叶片出现黄色条纹，叶片干枯"},
            headers=headers
        )
        
        # 6. 诊断记录查询
        print("\n[6] 诊断记录测试")
        await test_api(client, "诊断记录列表", "GET", "/api/v1/diagnosis/records", headers=headers)
        
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["success"])
    failed = total - passed
    
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\n失败的测试:")
        for r in TEST_RESULTS:
            if not r["success"]:
                error_msg = r.get('error', r.get('response', 'Unknown error'))
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get('detail', str(error_msg))
                print(f"  - {r['name']}: {error_msg}")
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed/total*100, 1),
        "results": TEST_RESULTS
    }

if __name__ == "__main__":
    results = asyncio.run(main())
    
    with open("integration_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n结果已保存到 integration_test_results.json")
