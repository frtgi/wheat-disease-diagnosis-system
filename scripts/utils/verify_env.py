"""
IWDDA 环境验证脚本

验证项目环境是否正确配置，包括 Python 版本、PyTorch、CUDA 和核心依赖包。

使用方法:
    python scripts/utils/verify_env.py
"""
import sys
import os


def print_header(title):
    """
    打印标题头
    
    Args:
        title: 标题文本
    """
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title):
    """
    打印分节标题
    
    Args:
        title: 分节标题
    """
    print(f"\n>>> {title}")


def check_python_version():
    """
    检查 Python 版本是否符合要求
    
    Returns:
        bool: 版本是否符合要求
    """
    print_section("Python 版本检查")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"    当前版本: Python {version_str}")
    
    if version.major == 3 and version.minor >= 10:
        print("    状态: ✅ 符合要求 (Python 3.10+)")
        return True
    else:
        print("    状态: ❌ 不符合要求 (需要 Python 3.10+)")
        return False


def check_pytorch():
    """
    检查 PyTorch 安装和 CUDA 支持
    
    Returns:
        dict: PyTorch 相关信息
    """
    print_section("PyTorch 检查")
    
    result = {
        "installed": False,
        "version": None,
        "cuda_available": False,
        "cuda_version": None,
        "gpu_name": None
    }
    
    try:
        import torch
        result["installed"] = True
        result["version"] = torch.__version__
        print(f"    PyTorch 版本: {torch.__version__}")
        
        result["cuda_available"] = torch.cuda.is_available()
        print(f"    CUDA 可用: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            result["cuda_version"] = torch.version.cuda
            print(f"    CUDA 版本: {torch.version.cuda}")
            
            result["gpu_name"] = torch.cuda.get_device_name(0)
            print(f"    GPU 设备: {torch.cuda.get_device_name(0)}")
            
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"    GPU 显存: {gpu_memory:.2f} GB")
            
            print("    状态: ✅ PyTorch GPU 支持正常")
        else:
            print("    状态: ⚠️ CUDA 不可用，仅支持 CPU")
            
    except ImportError:
        print("    状态: ❌ PyTorch 未安装")
        
    return result


def check_core_packages():
    """
    检查核心依赖包
    
    Returns:
        dict: 包检查结果
    """
    print_section("核心依赖包检查")
    
    packages = [
        ("ultralytics", "YOLOv8 核心"),
        ("transformers", "LLaVA 支持"),
        ("neo4j", "知识图谱驱动"),
        ("cv2", "OpenCV 图像处理"),
        ("gradio", "Web 界面"),
        ("numpy", "数值计算"),
        ("pandas", "数据处理"),
    ]
    
    results = {}
    
    for package_name, description in packages:
        try:
            if package_name == "cv2":
                import cv2
                version = cv2.__version__
            else:
                module = __import__(package_name)
                version = getattr(module, "__version__", "未知")
            
            print(f"    ✅ {package_name:15s} {version:15s} - {description}")
            results[package_name] = {"installed": True, "version": version}
        except ImportError:
            print(f"    ❌ {package_name:15s} {'未安装':15s} - {description}")
            results[package_name] = {"installed": False, "version": None}
    
    return results


def check_optional_packages():
    """
    检查可选依赖包
    
    Returns:
        dict: 可选包检查结果
    """
    print_section("可选依赖包检查")
    
    packages = [
        ("peft", "LoRA 微调"),
        ("bitsandbytes", "量化支持"),
        ("accelerate", "加速库"),
        ("tensorrt", "TensorRT 加速"),
    ]
    
    results = {}
    
    for package_name, description in packages:
        try:
            module = __import__(package_name)
            version = getattr(module, "__version__", "已安装")
            print(f"    ✅ {package_name:15s} {version:15s} - {description}")
            results[package_name] = {"installed": True, "version": version}
        except ImportError:
            print(f"    ⚪ {package_name:15s} {'未安装':15s} - {description} (可选)")
            results[package_name] = {"installed": False, "version": None}
    
    return results


def check_project_structure():
    """
    检查项目目录结构
    
    Returns:
        bool: 结构是否完整
    """
    print_section("项目目录结构检查")
    
    required_dirs = [
        "src",
        "src/vision",
        "src/cognition",
        "src/graph",
        "src/fusion",
        "configs",
        "scripts",
        "models",
        "datasets",
    ]
    
    required_files = [
        "requirements.txt",
        "configs/wheat_disease.yaml",
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        full_path = os.path.join(os.path.dirname(__file__), "..", "..", dir_path)
        if os.path.isdir(full_path):
            print(f"    ✅ 目录存在: {dir_path}")
        else:
            print(f"    ❌ 目录缺失: {dir_path}")
            all_ok = False
    
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
        if os.path.isfile(full_path):
            print(f"    ✅ 文件存在: {file_path}")
        else:
            print(f"    ❌ 文件缺失: {file_path}")
            all_ok = False
    
    return all_ok


def check_model_files():
    """
    检查模型文件
    
    Returns:
        dict: 模型文件状态
    """
    print_section("模型文件检查")
    
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    
    model_paths = [
        ("最佳模型 (v5 Phase2)", "models/wheat_disease_v5_optimized_phase2/weights/best.pt"),
        ("最新模型 (v9)", "models/wheat_disease_v9_final/fine_tune_1/weights/best.pt"),
        ("LLaVA 模型", "models/agri_llava/model.pt"),
    ]
    
    results = {}
    
    for name, rel_path in model_paths:
        full_path = os.path.join(project_root, rel_path)
        if os.path.isfile(full_path):
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"    ✅ {name}: {size_mb:.2f} MB")
            results[name] = {"exists": True, "size_mb": size_mb}
        else:
            print(f"    ⚪ {name}: 不存在")
            results[name] = {"exists": False, "size_mb": 0}
    
    return results


def generate_report(results):
    """
    生成环境检查报告
    
    Args:
        results: 检查结果字典
    """
    print_header("环境检查报告")
    
    total_checks = 0
    passed_checks = 0
    
    for category, items in results.items():
        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, dict) and "installed" in value:
                    total_checks += 1
                    if value["installed"]:
                        passed_checks += 1
                elif isinstance(value, bool):
                    total_checks += 1
                    if value:
                        passed_checks += 1
    
    if total_checks > 0:
        pass_rate = (passed_checks / total_checks) * 100
        print(f"\n    检查通过率: {passed_checks}/{total_checks} ({pass_rate:.1f}%)")
    
    if passed_checks == total_checks:
        print("\n    🎉 环境配置完美！可以开始开发。")
    elif pass_rate >= 80:
        print("\n    ✅ 环境基本正常，部分可选组件未安装。")
    else:
        print("\n    ⚠️ 环境存在问题，请检查上述失败项。")


def main():
    """
    主函数：执行所有环境检查
    """
    print_header("IWDDA 环境验证工具")
    print(f"    检查时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    results["python"] = check_python_version()
    results["pytorch"] = check_pytorch()
    results["core_packages"] = check_core_packages()
    results["optional_packages"] = check_optional_packages()
    results["project_structure"] = check_project_structure()
    results["model_files"] = check_model_files()
    
    generate_report(results)
    
    print("\n" + "=" * 60)
    print("  检查完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
