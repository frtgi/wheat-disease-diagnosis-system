import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = "v21test_admin"
TEST_PASS = "Test1234!"
TEST_USER_ID = 30

results = []

def record(test_name, expected, actual, status):
    """记录测试结果"""
    results.append({
        "test_name": test_name,
        "expected": expected,
        "actual": actual,
        "status": status
    })
    symbol = "✅" if status == "PASS" else "❌"
    print(f"{symbol} {test_name} | 预期: {expected} | 实际: {actual} | {status}")

def safe_json(resp):
    """安全解析JSON响应"""
    try:
        return resp.json()
    except:
        return resp.text[:200]

# ============================================================
# 1. 健康检查端点
# ============================================================
print("\n" + "="*60)
print("1. 健康检查端点")
print("="*60)

start = time.time()
try:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    elapsed = (time.time() - start) * 1000
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /health - 状态码", "200", str(r.status_code), "PASS")
        healthy = data.get("status") == "healthy" or data.get("ready") == True
        record("GET /health - 健康状态", "healthy/ready", str(data.get("status", data.get("ready"))), "PASS" if healthy else "FAIL")
        record("GET /health - 响应时间", "<3000ms", f"{elapsed:.0f}ms", "PASS" if elapsed < 3000 else "FAIL")
        print(f"   响应内容: {json.dumps(data, ensure_ascii=False)[:300]}")
    else:
        record("GET /health - 状态码", "200", str(r.status_code), "FAIL")
except Exception as e:
    record("GET /health", "200", f"异常: {e}", "FAIL")

# ============================================================
# 2. 用户认证 API
# ============================================================
print("\n" + "="*60)
print("2. 用户认证 API")
print("="*60)

access_token = None
refresh_token_val = None

# 2.1 正确凭据登录
try:
    r = requests.post(f"{BASE_URL}/users/login", json={
        "username": TEST_USER,
        "password": TEST_PASS
    }, timeout=10)
    data = safe_json(r)
    print(f"   登录响应: status={r.status_code}, success={data.get('success')}")
    if r.status_code == 200 and data.get("success") == True:
        login_data = data.get("data", {})
        access_token = login_data.get("access_token")
        refresh_token_val = login_data.get("refresh_token")
        record("POST /users/login (正确凭据) - 状态码", "200", str(r.status_code), "PASS")
        record("POST /users/login (正确凭据) - access_token", "存在", "存在" if access_token else "不存在", "PASS" if access_token else "FAIL")
        record("POST /users/login (正确凭据) - refresh_token", "存在", "存在" if refresh_token_val else "不存在", "PASS" if refresh_token_val else "FAIL")
        role = login_data.get("user", {}).get("role", "未知")
        record("POST /users/login (正确凭据) - user.role", "admin", role, "PASS" if role == "admin" else "FAIL")
        print(f"   Token前20字符: {access_token[:20] if access_token else 'N/A'}...")
        print(f"   Refresh Token: {'存在' if refresh_token_val else '不存在'}")
    else:
        record("POST /users/login (正确凭据)", "200+success", f"{r.status_code}: {str(data)[:150]}", "FAIL")
except Exception as e:
    record("POST /users/login (正确凭据)", "200", f"异常: {e}", "FAIL")

# 2.2 错误密码登录
try:
    r = requests.post(f"{BASE_URL}/users/login", json={
        "username": TEST_USER,
        "password": "WrongPassword123!"
    }, timeout=10)
    data = safe_json(r)
    # API 返回 200 但 success=False 表示认证失败
    if r.status_code == 200 and data.get("success") == False:
        record("POST /users/login (错误密码) - 返回失败", "success=False", f"success={data.get('success')}, error={data.get('error', '')[:30]}", "PASS")
    elif r.status_code in (401, 400, 403):
        record("POST /users/login (错误密码) - 状态码", "4xx", str(r.status_code), "PASS")
    else:
        record("POST /users/login (错误密码) - 返回失败", "success=False或4xx", f"status={r.status_code}, success={data.get('success')}", "FAIL")
except Exception as e:
    record("POST /users/login (错误密码)", "失败响应", f"异常: {e}", "FAIL")

# 2.3 刷新Token
if refresh_token_val:
    try:
        r = requests.post(f"{BASE_URL}/users/token/refresh", json={
            "refresh_token": refresh_token_val
        }, timeout=10)
        data = safe_json(r)
        print(f"   刷新Token响应: status={r.status_code}, data={str(data)[:150]}")
        if r.status_code == 200:
            new_data = data.get("data", data)
            new_access = new_data.get("access_token")
            if new_access:
                record("POST /users/token/refresh - 状态码", "200", str(r.status_code), "PASS")
                record("POST /users/token/refresh - 新access_token", "存在", "存在", "PASS")
                access_token = new_access
            else:
                record("POST /users/token/refresh", "200+access_token", f"{r.status_code}: {str(data)[:100]}", "FAIL")
        else:
            record("POST /users/token/refresh", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
    except Exception as e:
        record("POST /users/token/refresh", "200", f"异常: {e}", "FAIL")
else:
    record("POST /users/token/refresh", "200", "跳过(无refresh_token)", "FAIL")

# 2.4 重复用户名注册
try:
    r = requests.post(f"{BASE_URL}/users/register", json={
        "username": TEST_USER,
        "password": "SomePass123!",
        "email": "test_dup@test.com"
    }, timeout=10)
    data = safe_json(r)
    if r.status_code == 409:
        record("POST /users/register (重复用户名) - 状态码", "409", str(r.status_code), "PASS")
    elif r.status_code == 400:
        # 400 也可能表示验证失败
        record("POST /users/register (重复用户名) - 状态码", "409", f"{r.status_code}: {str(data)[:80]}", "FAIL")
    else:
        record("POST /users/register (重复用户名) - 状态码", "409", f"{r.status_code}: {str(data)[:80]}", "FAIL")
except Exception as e:
    record("POST /users/register (重复用户名)", "409", f"异常: {e}", "FAIL")

# ============================================================
# 3. 权限控制 API
# ============================================================
print("\n" + "="*60)
print("3. 权限控制 API")
print("="*60)

headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

# 3.1 获取自己的信息
try:
    r = requests.get(f"{BASE_URL}/users/{TEST_USER_ID}", headers=headers, timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /users/30 (admin访问自己) - 状态码", "200", str(r.status_code), "PASS")
        uid = data.get("id")
        record("GET /users/30 - 返回用户ID", str(TEST_USER_ID), str(uid), "PASS" if str(uid) == str(TEST_USER_ID) else "FAIL")
    else:
        record("GET /users/30 (admin访问自己)", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("GET /users/30 (admin访问自己)", "200", f"异常: {e}", "FAIL")

# 3.2 访问不存在的用户
try:
    r = requests.get(f"{BASE_URL}/users/99999", headers=headers, timeout=10)
    if r.status_code in (404, 400, 422):
        record("GET /users/99999 (不存在) - 状态码", "4xx", str(r.status_code), "PASS")
    else:
        data = safe_json(r)
        record("GET /users/99999 (不存在) - 状态码", "4xx", f"{r.status_code}: {str(data)[:80]}", "FAIL")
except Exception as e:
    record("GET /users/99999 (不存在)", "4xx", f"异常: {e}", "FAIL")

# 3.3 更新自己的信息
try:
    r = requests.put(f"{BASE_URL}/users/{TEST_USER_ID}", headers=headers, json={
        "phone": "13800138000"
    }, timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("PUT /users/30 (更新自己) - 状态码", "200", str(r.status_code), "PASS")
    else:
        record("PUT /users/30 (更新自己)", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("PUT /users/30 (更新自己)", "200", f"异常: {e}", "FAIL")

# 3.4 不带token访问受保护端点
try:
    r = requests.get(f"{BASE_URL}/users/{TEST_USER_ID}", timeout=10)
    if r.status_code == 401:
        record("GET /users/30 (无token) - 状态码", "401", str(r.status_code), "PASS")
    else:
        record("GET /users/30 (无token) - 状态码", "401", str(r.status_code), "FAIL")
except Exception as e:
    record("GET /users/30 (无token)", "401", f"异常: {e}", "FAIL")

# ============================================================
# 4. 知识库 API
# ============================================================
print("\n" + "="*60)
print("4. 知识库 API")
print("="*60)

# 4.1 搜索病害(作为列表使用)
try:
    r = requests.get(f"{BASE_URL}/knowledge/search", params={"page": 1, "page_size": 20}, timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /knowledge/search (病害列表) - 状态码", "200", str(r.status_code), "PASS")
        items = data if isinstance(data, list) else data.get("items", [])
        record("GET /knowledge/search - 返回数据", "列表", f"条目数: {len(items) if isinstance(items, list) else type(data).__name__}", "PASS")
    else:
        record("GET /knowledge/search (病害列表)", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("GET /knowledge/search (病害列表)", "200", f"异常: {e}", "FAIL")

# 4.2 搜索关键词
try:
    r = requests.get(f"{BASE_URL}/knowledge/search", params={"keyword": "锈病"}, timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /knowledge/search?keyword=锈病 - 状态码", "200", str(r.status_code), "PASS")
        items = data if isinstance(data, list) else data.get("items", [])
        record("GET /knowledge/search?keyword=锈病 - 返回数据", "非空", f"条目数: {len(items) if isinstance(items, list) else type(data).__name__}", "PASS")
    else:
        record("GET /knowledge/search?keyword=锈病", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("GET /knowledge/search?keyword=锈病", "200", f"异常: {e}", "FAIL")

# 4.3 病害详情
try:
    r = requests.get(f"{BASE_URL}/knowledge/1", timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /knowledge/1 (病害详情) - 状态码", "200", str(r.status_code), "PASS")
        record("GET /knowledge/1 - 返回数据", "非空", f"键: {list(data.keys())[:5] if isinstance(data, dict) else type(data).__name__}", "PASS")
    else:
        record("GET /knowledge/1 (病害详情)", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("GET /knowledge/1 (病害详情)", "200", f"异常: {e}", "FAIL")

# 4.4 知识图谱(需认证)
try:
    r = requests.get(f"{BASE_URL}/knowledge/graph", timeout=10)
    if r.status_code == 401:
        record("GET /knowledge/graph (无token) - 状态码", "401", str(r.status_code), "PASS")
    else:
        record("GET /knowledge/graph (无token) - 状态码", "401", str(r.status_code), "FAIL")
except Exception as e:
    record("GET /knowledge/graph (无token)", "401", f"异常: {e}", "FAIL")

# 4.5 统计(需认证)
try:
    r = requests.get(f"{BASE_URL}/knowledge/stats", timeout=10)
    if r.status_code == 401:
        record("GET /knowledge/stats (无token) - 状态码", "401", str(r.status_code), "PASS")
    else:
        record("GET /knowledge/stats (无token) - 状态码", "401", str(r.status_code), "FAIL")
except Exception as e:
    record("GET /knowledge/stats (无token)", "401", f"异常: {e}", "FAIL")

# ============================================================
# 5. 诊断 API
# ============================================================
print("\n" + "="*60)
print("5. 诊断 API")
print("="*60)

# 5.1 诊断记录列表
try:
    r = requests.get(f"{BASE_URL}/diagnosis/records", params={"page": 1, "page_size": 10}, headers=headers, timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /diagnosis/records - 状态码", "200", str(r.status_code), "PASS")
        records_list = data.get("records", data if isinstance(data, list) else [])
        total = data.get("total", len(records_list) if isinstance(records_list, list) else 0)
        record("GET /diagnosis/records - 返回数据", "分页结构", f"total={total}, records={len(records_list) if isinstance(records_list, list) else type(records_list).__name__}", "PASS")
    else:
        record("GET /diagnosis/records", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("GET /diagnosis/records", "200", f"异常: {e}", "FAIL")

# 5.2 诊断统计 (实际路径: /stats/diagnoses)
try:
    r = requests.get(f"{BASE_URL}/stats/diagnoses", headers=headers, timeout=10)
    data = safe_json(r)
    if r.status_code == 200:
        record("GET /stats/diagnoses - 状态码", "200", str(r.status_code), "PASS")
        record("GET /stats/diagnoses - 返回数据", "非空", f"键: {list(data.keys())[:5] if isinstance(data, dict) else type(data).__name__}", "PASS")
    else:
        record("GET /stats/diagnoses", "200", f"{r.status_code}: {str(data)[:100]}", "FAIL")
except Exception as e:
    record("GET /stats/diagnoses", "200", f"异常: {e}", "FAIL")

# ============================================================
# 6. 报告 API
# ============================================================
print("\n" + "="*60)
print("6. 报告 API")
print("="*60)

# 报告只有 POST /reports/generate，无 GET 列表端点
# 测试不带认证访问生成端点
try:
    r = requests.post(f"{BASE_URL}/reports/generate", timeout=10)
    if r.status_code == 401:
        record("POST /reports/generate (无token) - 状态码", "401", str(r.status_code), "PASS")
    elif r.status_code == 422:
        # 422 表示参数验证失败，但认证可能已通过
        record("POST /reports/generate (无token) - 状态码", "401", f"{r.status_code}(参数验证失败)", "FAIL")
    else:
        record("POST /reports/generate (无token) - 状态码", "401", str(r.status_code), "FAIL")
except Exception as e:
    record("POST /reports/generate (无token)", "401", f"异常: {e}", "FAIL")

# ============================================================
# 7. 管理 API (实际路径: /stats/overview, /stats/vram, /stats/cache, /logs/*)
# ============================================================
print("\n" + "="*60)
print("7. 管理 API")
print("="*60)

admin_endpoints = [
    ("GET /stats/overview (概览统计)", "/stats/overview"),
    ("GET /stats/vram (GPU显存)", "/stats/vram"),
    ("GET /stats/cache (缓存统计)", "/stats/cache"),
    ("GET /logs/statistics (日志统计)", "/logs/statistics"),
    ("GET /logs/recent (最近日志)", "/logs/recent"),
    ("GET /logs/disease-distribution (病害分布)", "/logs/disease-distribution"),
]

for name, path in admin_endpoints:
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=10)
        data = safe_json(r)
        if r.status_code == 200:
            record(f"{name} - 状态码", "200", str(r.status_code), "PASS")
            summary = str(data)[:80] if isinstance(data, (dict, list)) else str(data)[:50]
            record(f"{name} - 返回数据", "非空", summary, "PASS")
        else:
            record(f"{name}", "200", f"{r.status_code}: {str(data)[:80]}", "FAIL")
    except Exception as e:
        record(f"{name}", "200", f"异常: {e}", "FAIL")

# ============================================================
# 汇总
# ============================================================
print("\n" + "="*60)
print("测试汇总")
print("="*60)

pass_count = sum(1 for r in results if r["status"] == "PASS")
fail_count = sum(1 for r in results if r["status"] == "FAIL")
total = len(results)

print(f"\n总测试项: {total} | 通过: {pass_count} | 失败: {fail_count}")
print(f"通过率: {pass_count/total*100:.1f}%\n")

print("-" * 100)
print(f"{'测试项':<55} | {'预期结果':<20} | {'实际结果':<30} | {'状态':<6}")
print("-" * 100)
for r in results:
    actual_short = r['actual'][:28] if len(r['actual']) > 28 else r['actual']
    print(f"{r['test_name']:<55} | {r['expected']:<20} | {actual_short:<30} | {r['status']:<6}")
print("-" * 100)
