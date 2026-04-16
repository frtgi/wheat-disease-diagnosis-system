"""
WheatAgent 项目兼容性测试脚本
测试内容：
1. Python 环境测试 - 验证 Python 3.10 环境兼容性
2. CUDA 环境测试 - 检测 CUDA 是否可用，验证 GPU 模型和推理功能
3. 依赖版本测试 - 检查关键依赖版本，验证版本兼容性
"""
import sys
import os
import platform
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class CompatibilityTest:
    """兼容性测试类"""
    
    def __init__(self):
        self.results = {
            "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python_environment": {},
            "cuda_environment": {},
            "dependency_versions": {},
            "overall_status": "unknown"
        }
        self.passed_tests = 0
        self.failed_tests = 0
        self.warning_tests = 0
    
    def print_header(self, title: str):
        """打印测试标题"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_test(self, test_name: str, status: str, message: str = ""):
        """打印测试结果"""
        status_icons = {
            "pass": "✅",
            "fail": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        icon = status_icons.get(status, "❓")
        print(f"  {icon} {test_name}: {message}")
        
        if status == "pass":
            self.passed_tests += 1
        elif status == "fail":
            self.failed_tests += 1
        elif status == "warning":
            self.warning_tests += 1
    
    def test_python_environment(self) -> Dict[str, Any]:
        """
        测试 Python 环境兼容性
        验证 Python 版本是否为 3.10，并检查系统环境
        """
        self.print_header("1. Python 环境测试")
        
        results = {}
        
        # 测试 Python 版本
        python_version = sys.version_info
        version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        
        if python_version.major == 3 and python_version.minor == 10:
            self.print_test("Python 版本", "pass", f"Python {version_str} (符合要求)")
            results["python_version"] = {"status": "pass", "version": version_str}
        elif python_version.major == 3 and python_version.minor >= 10:
            self.print_test("Python 版本", "warning", f"Python {version_str} (高于要求，可能兼容)")
            results["python_version"] = {"status": "warning", "version": version_str}
        else:
            self.print_test("Python 版本", "fail", f"Python {version_str} (需要 Python 3.10+)")
            results["python_version"] = {"status": "fail", "version": version_str}
        
        # 测试系统平台
        system_info = f"{platform.system()} {platform.release()}"
        self.print_test("操作系统", "info", system_info)
        results["os_info"] = system_info
        
        # 测试架构
        arch = platform.machine()
        self.print_test("系统架构", "info", arch)
        results["architecture"] = arch
        
        # 测试 Conda 环境
        conda_env = os.environ.get("CONDA_DEFAULT_ENV", "未检测到")
        if conda_env == "wheatagent-py310":
            self.print_test("Conda 环境", "pass", f"{conda_env} (正确)")
            results["conda_env"] = {"status": "pass", "name": conda_env}
        elif conda_env != "未检测到":
            self.print_test("Conda 环境", "warning", f"{conda_env} (建议使用 wheatagent-py310)")
            results["conda_env"] = {"status": "warning", "name": conda_env}
        else:
            self.print_test("Conda 环境", "info", "未使用 Conda 环境")
            results["conda_env"] = {"status": "info", "name": None}
        
        # 测试 Python 路径
        python_path = sys.executable
        self.print_test("Python 路径", "info", python_path)
        results["python_path"] = python_path
        
        self.results["python_environment"] = results
        return results
    
    def test_cuda_environment(self) -> Dict[str, Any]:
        """
        测试 CUDA 环境
        检测 CUDA 是否可用，验证 GPU 模型和推理功能
        """
        self.print_header("2. CUDA 环境测试")
        
        results = {}
        
        try:
            import torch
            
            # 测试 PyTorch 版本
            torch_version = torch.__version__
            self.print_test("PyTorch 版本", "info", torch_version)
            results["torch_version"] = torch_version
            
            # 测试 CUDA 是否可用
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                self.print_test("CUDA 可用性", "pass", "CUDA 可用")
                results["cuda_available"] = True
                
                # 测试 CUDA 版本
                cuda_version = torch.version.cuda
                self.print_test("CUDA 版本", "info", f"CUDA {cuda_version}")
                results["cuda_version"] = cuda_version
                
                # 测试 cuDNN 版本
                cudnn_version = torch.backends.cudnn.version()
                self.print_test("cuDNN 版本", "info", f"cuDNN {cudnn_version}")
                results["cudnn_version"] = cudnn_version
                
                # 测试 GPU 数量
                gpu_count = torch.cuda.device_count()
                self.print_test("GPU 数量", "info", f"{gpu_count} 个 GPU")
                results["gpu_count"] = gpu_count
                
                # 测试 GPU 信息
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    gpu_capability = torch.cuda.get_device_capability(i)
                    
                    self.print_test(f"GPU {i} 型号", "info", gpu_name)
                    self.print_test(f"GPU {i} 显存", "info", f"{gpu_memory:.2f} GB")
                    self.print_test(f"GPU {i} 计算能力", "info", f"{gpu_capability[0]}.{gpu_capability[1]}")
                    
                    results[f"gpu_{i}"] = {
                        "name": gpu_name,
                        "memory_gb": round(gpu_memory, 2),
                        "compute_capability": f"{gpu_capability[0]}.{gpu_capability[1]}"
                    }
                
                # 测试 GPU 推理功能
                try:
                    device = torch.device("cuda:0")
                    test_tensor = torch.randn(1000, 1000, device=device)
                    result_tensor = torch.matmul(test_tensor, test_tensor)
                    del test_tensor, result_tensor
                    torch.cuda.empty_cache()
                    self.print_test("GPU 推理测试", "pass", "GPU 推理功能正常")
                    results["gpu_inference"] = {"status": "pass"}
                except Exception as e:
                    self.print_test("GPU 推理测试", "fail", f"GPU 推理失败: {str(e)}")
                    results["gpu_inference"] = {"status": "fail", "error": str(e)}
                
                # 测试 GPU 内存状态
                memory_allocated = torch.cuda.memory_allocated(0) / (1024**3)
                memory_reserved = torch.cuda.memory_reserved(0) / (1024**3)
                self.print_test("GPU 内存使用", "info", 
                               f"已分配: {memory_allocated:.2f} GB, 已保留: {memory_reserved:.2f} GB")
                results["gpu_memory"] = {
                    "allocated_gb": round(memory_allocated, 2),
                    "reserved_gb": round(memory_reserved, 2)
                }
                
            else:
                self.print_test("CUDA 可用性", "fail", "CUDA 不可用，请检查 CUDA 安装")
                results["cuda_available"] = False
                
                # 检查 CPU 模式是否可用
                try:
                    test_tensor = torch.randn(100, 100)
                    result_tensor = torch.matmul(test_tensor, test_tensor)
                    del test_tensor, result_tensor
                    self.print_test("CPU 推理测试", "warning", "仅 CPU 模式可用，性能将受限")
                    results["cpu_inference"] = {"status": "warning"}
                except Exception as e:
                    self.print_test("CPU 推理测试", "fail", f"CPU 推理失败: {str(e)}")
                    results["cpu_inference"] = {"status": "fail", "error": str(e)}
            
            # 测试 CUDA 环境变量
            cuda_path = os.environ.get("CUDA_PATH", "未设置")
            cuda_home = os.environ.get("CUDA_HOME", "未设置")
            
            self.print_test("CUDA_PATH", "info", cuda_path)
            self.print_test("CUDA_HOME", "info", cuda_home)
            results["cuda_path"] = cuda_path
            results["cuda_home"] = cuda_home
            
        except ImportError:
            self.print_test("PyTorch 导入", "fail", "PyTorch 未安装")
            results["torch_installed"] = False
        
        self.results["cuda_environment"] = results
        return results
    
    def test_dependency_versions(self) -> Dict[str, Any]:
        """
        测试依赖版本
        检查关键依赖版本，验证版本兼容性
        """
        self.print_header("3. 依赖版本测试")
        
        results = {}
        
        # 定义关键依赖及其最低版本要求
        required_packages = {
            "torch": {"min_version": "2.0.0", "critical": True},
            "torchvision": {"min_version": "0.15.0", "critical": True},
            "transformers": {"min_version": "4.30.0", "critical": True},
            "ultralytics": {"min_version": "8.0.0", "critical": True},
            "fastapi": {"min_version": "0.109.0", "critical": True},
            "uvicorn": {"min_version": "0.27.0", "critical": False},
            "sqlalchemy": {"min_version": "2.0.0", "critical": False},
            "pydantic": {"min_version": "2.5.0", "critical": True},
            "redis": {"min_version": "5.0.0", "critical": False},
            "numpy": {"min_version": "1.24.0", "critical": True},
            "pillow": {"min_version": "10.0.0", "critical": False},
            "opencv-python": {"min_version": "4.8.0", "critical": True},
            "accelerate": {"min_version": "0.20.0", "critical": True},
            "bitsandbytes": {"min_version": "0.41.0", "critical": True},
            "peft": {"min_version": "0.5.0", "critical": True},
            "neo4j": {"min_version": "5.0.0", "critical": False},
            "gradio": {"min_version": "4.0.0", "critical": False},
            "celery": {"min_version": "5.3.0", "critical": False},
            "minio": {"min_version": "7.1.0", "critical": False},
        }
        
        for package_name, requirements in required_packages.items():
            try:
                # 特殊处理包名
                import_name = package_name.replace("-", "_")
                if package_name == "opencv-python":
                    import cv2
                    version = cv2.__version__
                elif package_name == "pillow":
                    import PIL
                    version = PIL.__version__
                elif package_name == "bitsandbytes":
                    import bitsandbytes as bnb
                    version = bnb.__version__
                else:
                    module = __import__(import_name)
                    version = getattr(module, "__version__", "未知")
                
                # 版本比较
                min_version = requirements["min_version"]
                is_critical = requirements["critical"]
                
                try:
                    from packaging import version as pkg_version
                    if pkg_version.parse(str(version)) >= pkg_version.parse(min_version):
                        status = "pass"
                        msg = f"版本 {version} (>= {min_version})"
                    else:
                        status = "warning" if not is_critical else "fail"
                        msg = f"版本 {version} (需要 >= {min_version})"
                except ImportError:
                    status = "info"
                    msg = f"版本 {version} (无法验证版本要求)"
                
                self.print_test(package_name, status, msg)
                results[package_name] = {
                    "installed": True,
                    "version": str(version),
                    "required": min_version,
                    "status": status
                }
                
            except ImportError:
                is_critical = requirements["critical"]
                status = "fail" if is_critical else "warning"
                self.print_test(package_name, status, "未安装")
                results[package_name] = {
                    "installed": False,
                    "required": requirements["min_version"],
                    "status": status
                }
        
        # 测试特定模块导入
        self.print_header("4. 核心模块导入测试")
        
        core_modules = [
            ("src.vision.vision_engine", "视觉引擎"),
            ("src.perception.yolo_engine", "YOLO 引擎"),
            ("src.cognition.qwen_engine", "Qwen 引擎"),
            ("src.fusion.fusion_engine", "融合引擎"),
            ("src.graph.graph_engine", "图谱引擎"),
        ]
        
        for module_path, module_name in core_modules:
            try:
                __import__(module_path)
                self.print_test(module_name, "pass", "导入成功")
                results[f"module_{module_path}"] = {"status": "pass"}
            except ImportError as e:
                self.print_test(module_name, "warning", f"导入失败: {str(e)[:50]}")
                results[f"module_{module_path}"] = {"status": "warning", "error": str(e)}
        
        self.results["dependency_versions"] = results
        return results
    
    def test_model_loading(self) -> Dict[str, Any]:
        """
        测试模型加载功能
        验证 YOLO 和 Qwen 模型是否可以正常加载
        """
        self.print_header("5. 模型加载测试")
        
        results = {}
        
        # 测试 YOLO 模型
        try:
            from ultralytics import YOLO
            
            model_path = "./models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt"
            if os.path.exists(model_path):
                self.print_test("YOLO 模型文件", "info", f"找到模型: {model_path}")
                try:
                    model = YOLO(model_path)
                    self.print_test("YOLO 模型加载", "pass", "模型加载成功")
                    results["yolo_model"] = {"status": "pass", "path": model_path}
                    del model
                except Exception as e:
                    self.print_test("YOLO 模型加载", "fail", f"加载失败: {str(e)[:50]}")
                    results["yolo_model"] = {"status": "fail", "error": str(e)}
            else:
                self.print_test("YOLO 模型文件", "warning", f"模型文件不存在: {model_path}")
                results["yolo_model"] = {"status": "warning", "path": model_path}
        except ImportError:
            self.print_test("YOLO 模块", "warning", "ultralytics 未安装")
            results["yolo_model"] = {"status": "warning", "error": "ultralytics not installed"}
        
        # 测试 Transformers 模型
        try:
            import torch
            from transformers import AutoTokenizer
            
            model_path = "./models/Qwen3-VL-4B-Instruct"
            if os.path.exists(model_path):
                self.print_test("Qwen 模型文件", "info", f"找到模型目录: {model_path}")
                try:
                    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                    self.print_test("Qwen Tokenizer 加载", "pass", "Tokenizer 加载成功")
                    results["qwen_tokenizer"] = {"status": "pass", "path": model_path}
                    del tokenizer
                except Exception as e:
                    self.print_test("Qwen Tokenizer 加载", "warning", f"加载失败: {str(e)[:50]}")
                    results["qwen_tokenizer"] = {"status": "warning", "error": str(e)}
            else:
                self.print_test("Qwen 模型文件", "warning", f"模型目录不存在: {model_path}")
                results["qwen_tokenizer"] = {"status": "warning", "path": model_path}
        except ImportError:
            self.print_test("Transformers 模块", "warning", "transformers 未安装")
            results["qwen_tokenizer"] = {"status": "warning", "error": "transformers not installed"}
        
        self.results["model_loading"] = results
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        
        total_tests = self.passed_tests + self.failed_tests + self.warning_tests
        
        if self.failed_tests > 0:
            overall_status = "fail"
        elif self.warning_tests > 0:
            overall_status = "warning"
        else:
            overall_status = "pass"
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "warnings": self.warning_tests,
            "overall_status": overall_status
        }
        
        self.results["overall_status"] = overall_status
        
        return self.results
    
    def print_summary(self):
        """打印测试摘要"""
        self.print_header("测试摘要")
        
        total_tests = self.passed_tests + self.failed_tests + self.warning_tests
        
        print(f"\n  总测试数: {total_tests}")
        print(f"  ✅ 通过: {self.passed_tests}")
        print(f"  ❌ 失败: {self.failed_tests}")
        print(f"  ⚠️  警告: {self.warning_tests}")
        
        if self.failed_tests > 0:
            status = "❌ 测试失败"
            color = "\033[91m"
        elif self.warning_tests > 0:
            status = "⚠️  测试通过（有警告）"
            color = "\033[93m"
        else:
            status = "✅ 所有测试通过"
            color = "\033[92m"
        
        print(f"\n  {color}总体状态: {status}\033[0m")
        print("=" * 70)
    
    def save_report(self, output_path: str):
        """保存测试报告到文件"""
        report = self.generate_report()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存到: {output_path}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🚀" * 35)
        print("  WheatAgent 兼容性测试")
        print("  测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🚀" * 35)
        
        self.test_python_environment()
        self.test_cuda_environment()
        self.test_dependency_versions()
        self.test_model_loading()
        
        self.print_summary()
        
        return self.generate_report()


def main():
    """主函数"""
    tester = CompatibilityTest()
    
    try:
        results = tester.run_all_tests()
        
        # 保存报告
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "compatibility_test_report.json"
        )
        tester.save_report(report_path)
        
        return results
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
