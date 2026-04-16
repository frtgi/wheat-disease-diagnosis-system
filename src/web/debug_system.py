"""
系统调试和问题诊断脚本
检查系统各组件的运行状态和配置
"""
import sys
import socket
import subprocess
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

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def check_port(port, host='localhost'):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_service(name, port):
    """检查服务是否运行"""
    if check_port(port):
        print_success(f"{name} 正在运行 (端口：{port})")
        return True
    else:
        print_error(f"{name} 未运行 (端口：{port})")
        return False

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if Path(file_path).exists():
        print_success(f"{description}: {file_path}")
        return True
    else:
        print_error(f"{description} 不存在：{file_path}")
        return False

def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    if Path(dir_path).is_dir():
        print_success(f"{description}: {dir_path}")
        return True
    else:
        print_error(f"{description} 不存在：{dir_path}")
        return False

def check_python_package(package_name):
    """检查 Python 包是否安装"""
    try:
        __import__(package_name)
        print_success(f"Python 包已安装：{package_name}")
        return True
    except ImportError:
        print_error(f"Python 包未安装：{package_name}")
        return False

def check_node_package(package_name):
    """检查 Node.js 包是否安装"""
    try:
        result = subprocess.run(
            ['npm', 'list', package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Node.js 包已安装：{package_name}")
            return True
        else:
            print_error(f"Node.js 包未安装：{package_name}")
            return False
    except Exception:
        print_error(f"Node.js 包检查失败：{package_name}")
        return False

def main():
    """主诊断函数"""
    print_header("WheatAgent Web 系统诊断")
    
    issues = []
    
    # 1. 检查后端服务
    print_header("1. 后端服务检查")
    backend_running = check_service("后端 API", 8000)
    if not backend_running:
        issues.append("后端 API 未运行，请执行：cd src/web/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    # 2. 检查前端服务
    print_header("2. 前端服务检查")
    frontend_running = check_service("前端服务", 3000)
    if not frontend_running:
        issues.append("前端服务未运行，请执行：cd src/web/frontend && npm run dev")
    
    # 3. 检查数据库
    print_header("3. 数据库服务检查")
    mysql_running = check_service("MySQL", 3306)
    if not mysql_running:
        issues.append("MySQL 未运行，请启动 MySQL 服务")
    
    # 4. 检查 Redis
    print_header("4. Redis 服务检查")
    redis_running = check_service("Redis", 6379)
    if not redis_running:
        issues.append("Redis 未运行，请执行：redis-server")
    
    # 5. 检查后端文件结构
    print_header("5. 后端文件结构检查")
    check_file_exists("src/web/backend/app/main.py", "后端主文件")
    check_file_exists("src/web/backend/app/core/config.py", "后端配置文件")
    check_file_exists("src/web/backend/app/core/database.py", "数据库配置")
    check_file_exists("src/web/backend/app/core/redis_client.py", "Redis 客户端")
    check_file_exists("src/web/backend/app/services/diagnosis.py", "诊断服务")
    check_file_exists("src/web/backend/app/services/cache.py", "缓存服务")
    check_file_exists("src/web/backend/requirements.txt", "后端依赖")
    
    # 6. 检查前端文件结构
    print_header("6. 前端文件结构检查")
    check_file_exists("src/web/frontend/package.json", "前端 package.json")
    check_file_exists("src/web/frontend/src/main.ts", "前端入口文件")
    check_file_exists("src/web/frontend/src/App.vue", "前端 App 组件")
    check_file_exists("src/web/frontend/src/router/index.ts", "路由配置")
    check_file_exists("src/web/frontend/index.html", "前端 HTML")
    
    # 7. 检查数据库初始化
    print_header("7. 数据库初始化检查")
    check_file_exists("src/database/init.sql", "数据库初始化脚本")
    check_file_exists("src/database/migrations/add_indexes.sql", "数据库索引迁移脚本")
    
    # 8. 检查后端依赖
    print_header("8. 后端 Python 依赖检查")
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pymysql', 
        'redis', 'python_jose', 'passlib', 'pydantic'
    ]
    for package in required_packages:
        check_python_package(package)
    
    # 9. 检查前端依赖（简化检查）
    print_header("9. 前端 Node.js 依赖检查")
    check_node_package("vue")
    check_node_package("element-plus")
    check_node_package("axios")
    
    # 10. 检查环境变量配置
    print_header("10. 环境变量配置检查")
    env_file = Path("src/web/backend/.env")
    if env_file.exists():
        print_success(f".env 文件存在：{env_file}")
        # 读取并检查关键配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'DATABASE_HOST' in content:
                print_success("DATABASE_HOST 已配置")
            else:
                print_warning("DATABASE_HOST 未配置")
            
            if 'REDIS_HOST' in content:
                print_success("REDIS_HOST 已配置")
            else:
                print_warning("REDIS_HOST 未配置")
            
            if 'JWT_SECRET_KEY' in content:
                print_success("JWT_SECRET_KEY 已配置")
            else:
                print_warning("JWT_SECRET_KEY 未配置")
    else:
        print_error(".env 文件不存在")
        issues.append("后端 .env 文件不存在，请创建并配置环境变量")
    
    # 11. 总结
    print_header("诊断总结")
    
    if issues:
        print_warning(f"发现 {len(issues)} 个问题：\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}\n")
        
        print_info("请按照上述提示修复问题后重新启动系统")
    else:
        print_success("所有检查通过！系统运行正常")
    
    print_header("诊断完成")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
