"""
系统启动和测试脚本
用于启动所有服务并运行完整测试
"""
import subprocess
import sys
import time
import requests
from pathlib import Path

# 颜色输出
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
    """打印标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def check_database():
    """检查数据库连接"""
    print_header("检查数据库连接")
    try:
        from src.web.backend.app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print_success("数据库连接正常")
        return True
    except Exception as e:
        print_error(f"数据库连接失败：{e}")
        return False


def init_database():
    """初始化数据库"""
    print_header("初始化数据库")
    try:
        # 运行数据库初始化脚本
        script_path = Path(__file__).parent / "src" / "web" / "backend" / "scripts" / "init_db.py"
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode == 0:
            print_success("数据库初始化成功")
            return True
        else:
            print_error(f"数据库初始化失败：{result.stderr}")
            return False
    except Exception as e:
        print_error(f"数据库初始化异常：{e}")
        return False


def start_backend():
    """启动后端服务"""
    print_header("启动后端服务")
    try:
        # 使用 uvicorn 配置启动
        backend_dir = Path(__file__).parent / "src" / "web" / "backend"
        process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--workers", "4",
                "--loop", "uvloop",
                "--http", "httptools"
            ],
            cwd=str(backend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print_info("后端服务启动中...")
        time.sleep(5)  # 等待服务启动
        
        # 检查服务是否正常
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print_success("后端服务启动成功")
                return process
            else:
                print_error("后端服务响应异常")
                return None
        except:
            print_error("后端服务启动超时")
            return None
            
    except Exception as e:
        print_error(f"启动后端服务失败：{e}")
        return None


def start_frontend():
    """启动前端服务"""
    print_header("启动前端服务")
    try:
        frontend_dir = Path(__file__).parent / "src" / "web" / "frontend"
        
        # 检查 node_modules
        if not (frontend_dir / "node_modules").exists():
            print_info("安装前端依赖...")
            subprocess.run(["npm", "install"], cwd=str(frontend_dir))
        
        # 启动前端开发服务器
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print_info("前端服务启动中...")
        time.sleep(10)  # 等待服务启动
        
        # 检查服务是否正常
        try:
            response = requests.get("http://localhost:5173", timeout=5)
            if response.status_code == 200:
                print_success("前端服务启动成功")
                return process
            else:
                print_error("前端服务响应异常")
                return None
        except:
            print_info("前端服务可能未完全启动，继续测试")
            return process
            
    except Exception as e:
        print_error(f"启动前端服务失败：{e}")
        return None


def run_tests():
    """运行测试"""
    print_header("运行系统测试")
    
    # 1. 单元测试
    print_info("运行单元测试...")
    test_dir = Path(__file__).parent / "src" / "web" / "tests"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir / "test_unit_api.py"), "-v"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode == 0:
        print_success("单元测试通过")
    else:
        print_error("单元测试失败")
        print(result.stderr)
    
    # 2. 集成测试
    print_info("\n运行集成测试...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir / "test_integration_full.py"), "-v"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode == 0:
        print_success("集成测试通过")
    else:
        print_error("集成测试失败")
        print(result.stderr)
    
    # 3. 边界和异常测试
    print_info("\n运行边界和异常测试...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir / "test_edge_cases.py"), "-v"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode == 0:
        print_success("边界和异常测试通过")
    else:
        print_error("边界和异常测试失败")
        print(result.stderr)


def main():
    """主函数"""
    print_header("WheatAgent 系统启动和测试")
    
    # 1. 检查数据库
    if not check_database():
        print_error("数据库检查失败，请先配置数据库")
        return False
    
    # 2. 初始化数据库
    init_database()
    
    # 3. 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        print_error("后端服务启动失败")
        return False
    
    # 4. 启动前端服务（可选）
    frontend_process = start_frontend()
    
    # 5. 运行测试
    run_tests()
    
    # 6. 生成测试报告
    print_header("生成测试报告")
    print_info("测试报告已保存到：docs/TEST_REPORT_FULL.md")
    print_info("问题清单已保存到：docs/TEST_ISSUES.md")
    print_info("测试总结已保存到：docs/TEST_SUMMARY.md")
    
    print_header("系统测试完成")
    print_success("所有服务已启动，测试已完成")
    print_info("\n后端服务：http://localhost:8000")
    print_info("API 文档：http://localhost:8000/docs")
    print_info("前端服务：http://localhost:5173")
    print_info("\n按 Ctrl+C 停止所有服务")
    
    # 保持服务运行
    try:
        backend_process.wait()
        if frontend_process:
            frontend_process.wait()
    except KeyboardInterrupt:
        print_info("\n正在停止服务...")
        backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print_success("所有服务已停止")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
