"""
端到端集成测试脚本
测试 Web 系统的完整功能流程

测试内容：
1. 用户注册和登录
2. 图像诊断
3. 诊断记录查询
4. 知识库浏览
5. Dashboard 统计
"""
import requests
import time
import sys
from pathlib import Path

# 后端 API 地址
BASE_URL = "http://localhost:8000/api/v1"

# 测试颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0
}

def test_result(name, success, message=""):
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
        print_success(f"{name}: {message if message else '通过'}")
    else:
        test_results["failed"] += 1
        print_error(f"{name}: {message if message else '失败'}")

# 1. 测试用户注册
def test_user_register():
    print_header("测试 1: 用户注册")
    
    try:
        # 生成唯一用户名
        timestamp = int(time.time())
        username = f"test_user_{timestamp}"
        email = f"{username}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "test123456",
                "role": "farmer"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            test_result("用户注册", True, f"用户名：{username}")
            return username, "test123456"
        else:
            test_result("用户注册", False, f"状态码：{response.status_code}")
            return None, None
            
    except Exception as e:
        test_result("用户注册", False, str(e))
        return None, None

# 2. 测试用户登录
def test_user_login(username, password):
    print_header("测试 2: 用户登录")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": username,
                "password": password
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                test_result("用户登录", True, f"获取 Token 成功")
                return token
            else:
                test_result("用户登录", False, "Token 不存在")
                return None
        else:
            test_result("用户登录", False, f"状态码：{response.status_code}")
            return None
            
    except Exception as e:
        test_result("用户登录", False, str(e))
        return None

# 3. 测试图像诊断
def test_image_diagnosis(token):
    print_header("测试 3: 图像诊断")
    
    try:
        # 查找测试图像
        test_image_path = Path(__file__).parent.parent.parent.parent / "datasets" / "test" / "test_e2e_0.jpg"
        
        if not test_image_path.exists():
            # 尝试其他路径
            test_image_path = Path(__file__).parent.parent.parent.parent / "test_images" / "test_e2e_0.jpg"
        
        if not test_image_path.exists():
            test_result("图像诊断", False, "测试图像不存在")
            return None
        
        # 上传并诊断
        with open(test_image_path, 'rb') as f:
            files = {'image': (test_image_path.name, f, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(
                f"{BASE_URL}/diagnosis/image",
                files=files,
                headers=headers,
                timeout=60  # AI 推理可能需要较长时间
            )
        
        if response.status_code == 200:
            data = response.json()
            disease_name = data.get("disease_name", "未知")
            confidence = data.get("confidence", 0)
            
            if confidence > 0.5:
                test_result("图像诊断", True, f"病害：{disease_name}, 置信度：{confidence:.2%}")
                return data
            else:
                test_result("图像诊断", False, f"置信度过低：{confidence:.2%}")
                return None
        else:
            test_result("图像诊断", False, f"状态码：{response.status_code}")
            return None
            
    except Exception as e:
        test_result("图像诊断", False, str(e))
        return None

# 4. 测试诊断记录查询
def test_diagnosis_records(token):
    print_header("测试 4: 诊断记录查询")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f"{BASE_URL}/diagnosis/records",
            headers=headers,
            params={"skip": 0, "limit": 10},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data)
            test_result("诊断记录查询", True, f"查询到 {count} 条记录")
            return count > 0
        else:
            test_result("诊断记录查询", False, f"状态码：{response.status_code}")
            return False
            
    except Exception as e:
        test_result("诊断记录查询", False, str(e))
        return False

# 5. 测试知识库查询
def test_knowledge_base(token):
    print_header("测试 5: 知识库查询")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试搜索
        response = requests.get(
            f"{BASE_URL}/knowledge/search",
            headers=headers,
            params={"keyword": "锈病", "page": 1, "page_size": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data)
            test_result("知识库查询", True, f"查询到 {count} 条知识")
            return count > 0
        else:
            test_result("知识库查询", False, f"状态码：{response.status_code}")
            return False
            
    except Exception as e:
        test_result("知识库查询", False, str(e))
        return False

# 6. 测试统计 API
def test_stats_api(token):
    print_header("测试 6: 统计 API")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试概览统计
        response = requests.get(
            f"{BASE_URL}/stats/overview",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            test_result("统计 API", True, f"用户数：{data.get('total_users', 0)}, 诊断数：{data.get('total_diagnoses', 0)}")
            return True
        else:
            test_result("统计 API", False, f"状态码：{response.status_code}")
            return False
            
    except Exception as e:
        test_result("统计 API", False, str(e))
        return False

# 7. 测试文本诊断
def test_text_diagnosis(token):
    print_header("测试 7: 文本诊断")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            f"{BASE_URL}/diagnosis/text",
            headers=headers,
            json={
                "text": "小麦叶片出现黄色条纹，逐渐变成铁锈色粉末"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            disease_name = data.get("disease_name", "未知")
            confidence = data.get("confidence", 0)
            test_result("文本诊断", True, f"病害：{disease_name}, 置信度：{confidence:.2%}")
            return True
        else:
            test_result("文本诊断", False, f"状态码：{response.status_code}")
            return False
            
    except Exception as e:
        test_result("文本诊断", False, str(e))
        return False

# 主测试流程
def run_all_tests():
    print_header("小麦病害诊断系统 - 端到端集成测试")
    print_info(f"API 地址：{BASE_URL}")
    print_info(f"测试开始时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试 1: 用户注册
    username, password = test_user_register()
    if not username:
        print_error("用户注册失败，无法继续测试")
        return
    
    # 测试 2: 用户登录
    token = test_user_login(username, password)
    if not token:
        print_error("用户登录失败，无法继续测试")
        return
    
    # 测试 3: 图像诊断
    diagnosis_result = test_image_diagnosis(token)
    
    # 测试 4: 诊断记录查询
    test_diagnosis_records(token)
    
    # 测试 5: 知识库查询
    test_knowledge_base(token)
    
    # 测试 6: 统计 API
    test_stats_api(token)
    
    # 测试 7: 文本诊断
    test_text_diagnosis(token)
    
    # 输出测试结果
    print_header("测试结果汇总")
    print_info(f"总测试数：{test_results['total']}")
    print_success(f"通过：{test_results['passed']}")
    if test_results['failed'] > 0:
        print_error(f"失败：{test_results['failed']}")
    
    pass_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print_info(f"通过率：{pass_rate:.1f}%")
    
    if pass_rate >= 90:
        print_success("\n🎉 测试通过！系统功能正常")
        return 0
    else:
        print_error("\n⚠️ 测试失败！请检查系统功能")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\n测试异常：{e}")
        sys.exit(1)
