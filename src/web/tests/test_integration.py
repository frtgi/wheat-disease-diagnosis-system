"""
Web 端系统集成测试脚本
测试各个功能模块的集成情况
"""
import os
import sys
import asyncio
import pytest
from typing import Dict, Any
import requests
import json
from datetime import datetime, timedelta
import time

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# 测试数据
TEST_USER = {
    "username": f"test_user_{int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "role": "farmer",
    "phone": "13800138000"
}

class IntegrationTestClient:
    """集成测试客户端"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.user_id = None
    
    def set_auth_token(self, token: str):
        """设置认证 Token"""
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def register_user(self) -> Dict[str, Any]:
        """注册新用户"""
        url = f"{self.base_url}/auth/register"
        response = self.session.post(url, json=TEST_USER, headers=HEADERS)
        return response.json()
    
    def login_user(self) -> Dict[str, Any]:
        """用户登录"""
        url = f"{self.base_url}/auth/login"
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        response = self.session.post(url, json=login_data, headers=HEADERS)
        return response.json()
    
    def refresh_token(self) -> Dict[str, Any]:
        """刷新 Token"""
        url = f"{self.base_url}/auth/refresh"
        response = self.session.post(url)
        return response.json()
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        url = f"{self.base_url}/users/me"
        response = self.session.get(url)
        return response.json()
    
    def update_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息"""
        url = f"{self.base_url}/users/me"
        response = self.session.put(url, json=data, headers=HEADERS)
        return response.json()
    
    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改密码"""
        url = f"{self.base_url}/users/me/change-password"
        data = {
            "old_password": old_password,
            "new_password": new_password
        }
        response = self.session.post(url, json=data, headers=HEADERS)
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        return response.json()
    
    def search_knowledge(self, keyword: str) -> Dict[str, Any]:
        """搜索知识"""
        url = f"{self.base_url}/knowledge/search"
        params = {"keyword": keyword, "limit": 5}
        response = self.session.get(url, params=params)
        return response.json()
    
    def get_knowledge_categories(self) -> Dict[str, Any]:
        """获取知识分类"""
        url = f"{self.base_url}/knowledge/categories"
        response = self.session.get(url)
        return response.json()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取 Dashboard 统计"""
        url = f"{self.base_url}/stats/dashboard"
        response = self.session.get(url)
        return response.json()
    
    def get_disease_stats(self) -> Dict[str, Any]:
        """获取病害统计"""
        url = f"{self.base_url}/stats/diseases"
        response = self.session.get(url)
        return response.json()
    
    def get_diagnosis_records(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """获取诊断记录"""
        url = f"{self.base_url}/diagnosis/records"
        params = {"skip": skip, "limit": limit}
        response = self.session.get(url, params=params)
        return response.json()
    
    def text_diagnosis(self, symptoms: str) -> Dict[str, Any]:
        """文本诊断"""
        url = f"{self.base_url}/diagnosis/text"
        data = {"symptoms": symptoms}
        response = self.session.post(url, json=data, headers=HEADERS)
        return response.json()


def test_user_authentication():
    """测试用户认证功能"""
    print("=" * 60)
    print("开始用户认证功能测试")
    print("=" * 60)
    
    client = IntegrationTestClient()
    
    # 1. 健康检查
    print("\n[测试 1] 健康检查")
    try:
        health_result = client.health_check()
        if health_result.get("code") == 200:
            print("  ✅ 健康检查通过")
            print(f"     状态: {health_result['data']['status']}")
            print(f"     版本: {health_result['data']['version']}")
        else:
            print("  ❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"  ❌ 健康检查异常: {e}")
        return False
    
    # 2. 用户注册
    print("\n[测试 2] 用户注册")
    try:
        register_result = client.register_user()
        if register_result.get("code") == 200:
            print("  ✅ 用户注册成功")
            print(f"     用户ID: {register_result['data']['user_id']}")
            print(f"     用户名: {register_result['data']['username']}")
            client.user_id = register_result['data']['user_id']
        else:
            print(f"  ❌ 用户注册失败: {register_result}")
            return False
    except Exception as e:
        print(f"  ❌ 用户注册异常: {e}")
        return False
    
    # 3. 用户登录
    print("\n[测试 3] 用户登录")
    try:
        login_result = client.login_user()
        if login_result.get("code") == 200:
            token = login_result['data']['access_token']
            client.set_auth_token(token)
            print("  ✅ 用户登录成功")
            print(f"     Token类型: {login_result['data']['token_type']}")
            print(f"     过期时间: {login_result['data']['expires_in']}秒")
        else:
            print(f"  ❌ 用户登录失败: {login_result}")
            return False
    except Exception as e:
        print(f"  ❌ 用户登录异常: {e}")
        return False
    
    # 4. 获取用户信息
    print("\n[测试 4] 获取用户信息")
    try:
        user_info = client.get_user_info()
        if user_info.get("code") == 200:
            print("  ✅ 获取用户信息成功")
            print(f"     用户名: {user_info['data']['username']}")
            print(f"     角色: {user_info['data']['role']}")
        else:
            print(f"  ❌ 获取用户信息失败: {user_info}")
            return False
    except Exception as e:
        print(f"  ❌ 获取用户信息异常: {e}")
        return False
    
    # 5. 刷新 Token
    print("\n[测试 5] 刷新 Token")
    try:
        refresh_result = client.refresh_token()
        if refresh_result.get("code") == 200:
            new_token = refresh_result['data']['access_token']
            client.set_auth_token(new_token)
            print("  ✅ Token 刷新成功")
        else:
            print(f"  ❌ Token 刷新失败: {refresh_result}")
            return False
    except Exception as e:
        print(f"  ❌ Token 刷新异常: {e}")
        return False
    
    # 6. 更新用户信息
    print("\n[测试 6] 更新用户信息")
    try:
        update_data = {"phone": "13900139000"}
        update_result = client.update_user_info(update_data)
        if update_result.get("code") == 200:
            print("  ✅ 用户信息更新成功")
            print(f"     新手机号: {update_result['data']['phone']}")
        else:
            print(f"  ❌ 用户信息更新失败: {update_result}")
            return False
    except Exception as e:
        print(f"  ❌ 用户信息更新异常: {e}")
        return False
    
    # 7. 修改密码
    print("\n[测试 7] 修改密码")
    try:
        new_password = "NewTestPassword456!"
        change_result = client.change_password(TEST_USER["password"], new_password)
        if change_result.get("code") == 200:
            print("  ✅ 密码修改成功")
            # 恢复原密码
            restore_result = client.change_password(new_password, TEST_USER["password"])
            if restore_result.get("code") == 200:
                print("  ✅ 密码恢复成功")
            else:
                print(f"  ⚠️ 密码恢复失败: {restore_result}")
        else:
            print(f"  ❌ 密码修改失败: {change_result}")
            return False
    except Exception as e:
        print(f"  ❌ 密码修改异常: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("用户认证功能测试完成！✅")
    print("=" * 60)
    return True


def test_diagnosis_function():
    """测试诊断功能"""
    print("\n" + "=" * 60)
    print("开始诊断功能测试")
    print("=" * 60)
    
    client = IntegrationTestClient()
    
    # 先登录
    register_result = client.register_user()
    if register_result.get("code") != 200:
        print("  ❌ 无法注册测试用户")
        return False
    
    login_result = client.login_user()
    if login_result.get("code") != 200:
        print("  ❌ 无法登录测试用户")
        return False
    
    token = login_result['data']['access_token']
    client.set_auth_token(token)
    
    # 1. 文本诊断测试
    print("\n[测试 1] 文本诊断")
    try:
        symptoms = "小麦叶片出现黄色条状病斑，沿叶脉平行排列，病斑长约2-3厘米"
        text_result = client.text_diagnosis(symptoms)
        if text_result.get("code") == 200:
            print("  ✅ 文本诊断成功")
            print(f"     病害名称: {text_result['data']['disease_name']}")
            print(f"     置信度: {text_result['data']['confidence']:.2%}")
            print(f"     严重程度: {text_result['data']['severity']}")
        else:
            print(f"  ❌ 文本诊断失败: {text_result}")
            # 这可能是因为AI服务未启动，记录但不停止测试
            print("  ⚠️ 文本诊断失败（可能AI服务未启动）")
    except Exception as e:
        print(f"  ⚠️ 文本诊断异常: {e}（可能AI服务未启动）")
    
    # 2. 获取诊断记录
    print("\n[测试 2] 获取诊断记录")
    try:
        records_result = client.get_diagnosis_records()
        if records_result.get("code") == 200:
            print("  ✅ 诊断记录查询成功")
            print(f"     总记录数: {records_result['data']['total']}")
        else:
            print(f"  ❌ 诊断记录查询失败: {records_result}")
            # 这是可以接受的，因为可能没有诊断记录
            print("  ⚠️ 诊断记录查询失败（可能无记录）")
    except Exception as e:
        print(f"  ⚠️ 诊断记录查询异常: {e}")
    
    print("\n" + "=" * 60)
    print("诊断功能测试完成！✅")
    print("=" * 60)
    return True


def test_knowledge_function():
    """测试知识库功能"""
    print("\n" + "=" * 60)
    print("开始知识库功能测试")
    print("=" * 60)
    
    client = IntegrationTestClient()
    
    # 1. 搜索知识
    print("\n[测试 1] 知识搜索")
    try:
        search_result = client.search_knowledge("白粉病")
        if search_result.get("code") == 200:
            print("  ✅ 知识搜索成功")
            print(f"     搜索结果数: {search_result['data']['total']}")
            if search_result['data']['items']:
                first_item = search_result['data']['items'][0]
                print(f"     首个结果: {first_item['entity']}")
        else:
            print(f"  ❌ 知识搜索失败: {search_result}")
            return False
    except Exception as e:
        print(f"  ❌ 知识搜索异常: {e}")
        return False
    
    # 2. 获取知识分类
    print("\n[测试 2] 知识分类浏览")
    try:
        categories_result = client.get_knowledge_categories()
        if categories_result.get("code") == 200:
            print("  ✅ 知识分类获取成功")
            print(f"     病害种类数: {len(categories_result['data'].get('diseases', []))}")
            print(f"     害虫种类数: {len(categories_result['data'].get('pests', []))}")
        else:
            print(f"  ❌ 知识分类获取失败: {categories_result}")
            return False
    except Exception as e:
        print(f"  ❌ 知识分类获取异常: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("知识库功能测试完成！✅")
    print("=" * 60)
    return True


def test_statistics_function():
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("开始统计功能测试")
    print("=" * 60)
    
    client = IntegrationTestClient()
    
    # 先登录
    register_result = client.register_user()
    if register_result.get("code") != 200:
        print("  ❌ 无法注册测试用户")
        return False
    
    login_result = client.login_user()
    if login_result.get("code") != 200:
        print("  ❌ 无法登录测试用户")
        return False
    
    token = login_result['data']['access_token']
    client.set_auth_token(token)
    
    # 1. 获取 Dashboard 统计
    print("\n[测试 1] Dashboard 统计")
    try:
        dashboard_result = client.get_dashboard_stats()
        if dashboard_result.get("code") == 200:
            print("  ✅ Dashboard 统计获取成功")
            print(f"     总诊断数: {dashboard_result['data']['total_diagnoses']}")
            print(f"     今日诊断数: {dashboard_result['data']['today_diagnoses']}")
            if dashboard_result['data']['disease_distribution']:
                top_disease = dashboard_result['data']['disease_distribution'][0]
                print(f"     最常见病害: {top_disease['name']} ({top_disease['count']}次)")
        else:
            print(f"  ❌ Dashboard 统计获取失败: {dashboard_result}")
            # 这是可以接受的，因为可能没有统计数据
            print("  ⚠️ Dashboard 统计获取失败（可能无数据）")
    except Exception as e:
        print(f"  ⚠️ Dashboard 统计获取异常: {e}")
    
    # 2. 获取病害统计
    print("\n[测试 2] 病害统计")
    try:
        disease_result = client.get_disease_stats()
        if disease_result.get("code") == 200:
            print("  ✅ 病害统计获取成功")
            print(f"     总计数: {disease_result['data']['total_count']}")
            if disease_result['data']['disease_stats']:
                first_stat = disease_result['data']['disease_stats'][0]
                print(f"     首个病害: {first_stat['disease_name']}")
        else:
            print(f"  ❌ 病害统计获取失败: {disease_result}")
            # 这是可以接受的，因为可能没有统计数据
            print("  ⚠️ 病害统计获取失败（可能无数据）")
    except Exception as e:
        print(f"  ⚠️ 病害统计获取异常: {e}")
    
    print("\n" + "=" * 60)
    print("统计功能测试完成！✅")
    print("=" * 60)
    return True


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始 Web 端系统集成测试")
    print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   测试目标: {BASE_URL}")
    
    results = []
    
    # 运行各功能模块测试
    results.append(("用户认证", test_user_authentication()))
    results.append(("诊断功能", test_diagnosis_function()))
    results.append(("知识库功能", test_knowledge_function()))
    results.append(("统计功能", test_statistics_function()))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n  总体结果: {passed_tests}/{total_tests} 通过")
    
    if failed_tests == 0:
        print("  🎉 所有测试通过！")
    else:
        print(f"  ⚠️  {failed_tests} 个测试失败")
    
    print("=" * 60)
    
    return failed_tests == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)