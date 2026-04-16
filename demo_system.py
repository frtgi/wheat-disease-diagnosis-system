"""
WheatAgent 系统启动与功能演示脚本
用于启动所有服务并进行完整的功能演示
"""
import subprocess
import sys
import time
import requests
from pathlib import Path
import webbrowser


class Colors:
    """颜色输出类"""
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
    """打印标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_step(step_num, text):
    """打印步骤信息"""
    print(f"\n{Colors.BOLD}[步骤 {step_num}]{Colors.ENDC} {text}")


def check_prerequisites():
    """检查前置条件"""
    print_header("检查系统前置条件")
    
    # 检查 Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print_success(f"Python: {result.stdout.strip()}")
    except:
        print_error("Python 未安装")
        return False
    
    # 检查 Node.js
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print_success(f"Node.js/npm: {result.stdout.strip()}")
    except:
        print_info("Node.js/npm 未安装（前端功能将受限）")
    
    # 检查数据库
    try:
        from src.web.backend.app.core.database import SyncSessionLocal
        from sqlalchemy import text
        db = SyncSessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print_success("数据库连接正常")
    except Exception as e:
        print_error(f"数据库连接失败：{e}")
        print_info("请确保 MySQL 数据库已启动并正确配置")
        return False
    
    return True


def init_database():
    """初始化数据库"""
    print_step(1, "初始化数据库")
    
    try:
        script_path = Path(__file__).parent / "src" / "web" / "backend" / "scripts" / "init_db.py"
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("数据库初始化成功")
            print(result.stdout)
            return True
        else:
            print_error(f"数据库初始化失败：{result.stderr}")
            return False
    except Exception as e:
        print_error(f"数据库初始化异常：{e}")
        return False


def start_backend():
    """启动后端服务"""
    print_step(2, "启动后端服务")
    
    try:
        backend_dir = Path(__file__).parent / "src" / "web" / "backend"
        
        # 使用新终端启动后端
        process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--workers", "2",  # 使用 2 个 worker
                "--reload"  # 开发模式启用热重载
            ],
            cwd=str(backend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        
        print_info("等待后端服务启动...")
        time.sleep(8)  # 等待服务启动
        
        # 检查后端服务
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print_success("后端服务启动成功 (http://localhost:8000)")
                print_info(f"API 文档：http://localhost:8000/docs")
                return process
            else:
                print_error("后端服务响应异常")
                return None
        except requests.exceptions.RequestException as e:
            print_error(f"后端服务启动超时：{e}")
            return None
            
    except Exception as e:
        print_error(f"启动后端服务失败：{e}")
        return None


def start_frontend():
    """启动前端服务"""
    print_step(3, "启动前端服务")
    
    try:
        frontend_dir = Path(__file__).parent / "src" / "web" / "frontend"
        
        # 检查 node_modules
        if not (frontend_dir / "node_modules").exists():
            print_info("安装前端依赖...")
            subprocess.run(["npm", "install"], cwd=str(frontend_dir), check=True)
        
        # 启动前端
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        
        print_info("等待前端服务启动...")
        time.sleep(12)  # 前端启动较慢
        
        # 检查前端服务
        try:
            response = requests.get("http://localhost:5173", timeout=5)
            if response.status_code == 200:
                print_success("前端服务启动成功 (http://localhost:5173)")
                return process
            else:
                print_info("前端服务可能未完全启动，继续演示")
                return process
        except:
            print_info("前端服务可能未完全启动，继续演示")
            return process
            
    except Exception as e:
        print_error(f"启动前端服务失败：{e}")
        print_info("前端服务可选，继续后端功能演示")
        return None


def demo_user_registration():
    """演示用户注册"""
    print_step(4, "演示用户注册功能")
    
    try:
        # 注册新用户
        test_user = {
            "username": f"demo_user_{int(time.time())}",
            "email": f"demo_{int(time.time())}@example.com",
            "password": "demo123456",
            "role": "farmer"
        }
        
        print_info(f"注册用户：{test_user['username']}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/users/register",
            json=test_user,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print_success(f"用户注册成功！ID: {user_data.get('id', 'N/A')}")
            return test_user
        elif response.status_code == 409:
            print_info("用户已存在，使用现有用户")
            return test_user
        else:
            print_error(f"注册失败：{response.text}")
            return None
            
    except Exception as e:
        print_error(f"注册异常：{e}")
        return None


def demo_user_login(username: str, password: str):
    """演示用户登录"""
    print_step(5, "演示用户登录功能")
    
    try:
        print_info(f"登录用户：{username}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/users/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print_success(f"登录成功！Token: {access_token[:50]}...")
            return access_token
        else:
            print_error(f"登录失败：{response.text}")
            return None
            
    except Exception as e:
        print_error(f"登录异常：{e}")
        return None


def demo_knowledge_search():
    """演示知识库搜索"""
    print_step(6, "演示知识库搜索功能")
    
    try:
        print_info("搜索：白粉病")
        
        response = requests.get(
            "http://localhost:8000/api/v1/knowledge/search",
            params={"keyword": "白粉病", "limit": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("data", {}).get("items", [])
            print_success(f"搜索到 {len(items)} 条结果")
            for item in items[:3]:
                print(f"   - {item.get('entity', 'N/A')} ({item.get('entity_type', 'N/A')})")
            return True
        else:
            print_error(f"搜索失败：{response.text}")
            return False
            
    except Exception as e:
        print_error(f"搜索异常：{e}")
        return False


def demo_knowledge_categories():
    """演示知识分类"""
    print_step(7, "演示知识分类功能")
    
    try:
        print_info("获取知识分类")
        
        response = requests.get(
            "http://localhost:8000/api/v1/knowledge/categories",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("获取知识分类成功")
            # 可以显示分类信息
            return True
        else:
            print_error(f"获取分类失败：{response.text}")
            return False
            
    except Exception as e:
        print_error(f"获取分类异常：{e}")
        return False


def demo_statistics(token: str):
    """演示统计功能"""
    print_step(8, "演示统计功能")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Dashboard 统计
        print_info("获取 Dashboard 统计")
        response = requests.get(
            "http://localhost:8000/api/v1/stats/dashboard",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Dashboard 统计获取成功")
        else:
            print_error(f"Dashboard 统计失败：{response.text}")
        
        # 病害统计
        print_info("获取病害统计")
        response = requests.get(
            "http://localhost:8000/api/v1/stats/diagnoses",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("病害统计获取成功")
        else:
            print_error(f"病害统计失败：{response.text}")
        
        return True
        
    except Exception as e:
        print_error(f"统计功能异常：{e}")
        return False


def demo_diagnosis(token: str):
    """演示诊断功能"""
    print_step(9, "演示文本诊断功能")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 文本诊断
        print_info("进行文本诊断：叶片出现黄色条状病斑")
        response = requests.post(
            "http://localhost:8000/api/v1/diagnosis/text",
            headers=headers,
            json={"symptoms": "叶片出现黄色条状病斑，沿叶脉平行排列"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"诊断结果：{data.get('data', {}).get('disease_name', 'N/A')}")
            print(f"   置信度：{data.get('data', {}).get('confidence', 0):.1%}")
            return True
        elif response.status_code == 503:
            print_info("诊断服务暂时不可用（需要启动 AI 服务）")
            return False
        else:
            print_error(f"诊断失败：{response.text}")
            return False
            
    except Exception as e:
        print_error(f"诊断异常：{e}")
        return False


def run_automated_tests():
    """运行自动化测试"""
    print_step(10, "运行自动化测试")
    
    try:
        test_dir = Path(__file__).parent / "src" / "web" / "tests"
        
        # 运行单元测试
        print_info("运行单元测试...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir / "test_unit_api.py"), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print_success("单元测试通过")
        else:
            print_error("单元测试失败")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print_error("测试超时")
        return False
    except Exception as e:
        print_error(f"运行测试异常：{e}")
        return False


def open_browser():
    """打开浏览器"""
    print_info("打开浏览器查看系统...")
    
    # 打开 API 文档
    webbrowser.open("http://localhost:8000/docs")
    time.sleep(1)
    
    # 打开前端
    webbrowser.open("http://localhost:5173")
    
    print_success("已在浏览器中打开系统界面")


def main():
    """主函数"""
    print_header("WheatAgent 系统启动与功能演示")
    
    processes = []
    
    try:
        # 1. 检查前置条件
        if not check_prerequisites():
            print_error("前置条件检查失败，请修复后重试")
            return False
        
        # 2. 初始化数据库
        init_database()
        
        # 3. 启动后端服务
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
        else:
            print_error("后端服务启动失败")
            return False
        
        # 4. 启动前端服务（可选）
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
        
        # 5. 功能演示
        print_header("功能演示")
        
        # 用户注册
        user = demo_user_registration()
        if not user:
            print_info("使用测试用户继续演示")
            user = {"username": "test_admin", "password": "test123"}
        
        # 用户登录
        token = demo_user_login(user["username"], user["password"])
        if not token:
            print_error("登录失败，跳过后续需要认证的演示")
            token = None
        
        # 知识库搜索
        demo_knowledge_search()
        
        # 知识分类
        demo_knowledge_categories()
        
        # 统计功能（需要 token）
        if token:
            demo_statistics(token)
        
        # 诊断功能（需要 token 和 AI 服务）
        if token:
            demo_diagnosis(token)
        
        # 6. 自动化测试
        run_automated_tests()
        
        # 7. 打开浏览器
        open_browser()
        
        # 8. 显示总结
        print_header("功能演示完成")
        print_success("所有核心功能演示完成！")
        print("\n服务访问地址:")
        print(f"  后端服务：http://localhost:8000")
        print(f"  API 文档：http://localhost:8000/docs")
        print(f"  前端服务：http://localhost:5173")
        print("\n按 Ctrl+C 停止所有服务")
        
        # 保持服务运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print_info("\n正在停止服务...")
        for process in processes:
            try:
                process.terminate()
            except:
                pass
        print_success("所有服务已停止")
        
        print_header("演示结束")
        print_success("感谢使用 WheatAgent 系统！")
        
    except Exception as e:
        print_error(f"演示异常：{e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
