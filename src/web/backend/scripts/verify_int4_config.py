"""
INT4 量化配置验证脚本

验证 Qwen3-VL 模型的 INT4 量化是否正确配置和生效。
检查内容包括：
1. 环境变量和配置文件
2. bitsandbytes 安装状态
3. 模型加载时的量化配置
4. 显存使用情况
5. 量化效果验证

使用方法：
    python scripts/verify_int4_config.py
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_section(title: str) -> None:
    """
    打印分节标题。

    参数:
        title: 分节标题文本
    """
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_result(name: str, status: bool, detail: str = "") -> None:
    """
    打印验证结果。

    参数:
        name: 验证项名称
        status: 验证状态（True=通过，False=失败）
        detail: 详细信息
    """
    status_icon = "✅" if status else "❌"
    print(f"  {status_icon} {name}")
    if detail:
        print(f"      {detail}")


def check_environment() -> Tuple[bool, Dict[str, Any]]:
    """
    检查运行环境。

    返回:
        Tuple[bool, Dict]: (是否全部通过, 环境信息字典)
    """
    print_section("1. 环境检查")
    results = {}
    all_passed = True

    # 检查 Python 版本
    python_version = sys.version_info
    python_ok = python_version >= (3, 8)
    results['python_version'] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    print_result("Python 版本", python_ok, f"当前: {results['python_version']}")
    all_passed = all_passed and python_ok

    # 检查 CUDA 可用性
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        results['cuda_available'] = cuda_available
        if cuda_available:
            results['cuda_version'] = torch.version.cuda
            results['gpu_name'] = torch.cuda.get_device_name(0)
            results['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print_result("CUDA 可用", True, f"版本: {results['cuda_version']}")
            print_result("GPU 设备", True, f"{results['gpu_name']} ({results['gpu_memory']:.1f} GB)")
        else:
            print_result("CUDA 可用", False, "CUDA 不可用，INT4 量化需要 GPU 支持")
            all_passed = False
    except ImportError:
        print_result("PyTorch 安装", False, "PyTorch 未安装")
        results['cuda_available'] = False
        all_passed = False

    return all_passed, results


def check_bitsandbytes() -> Tuple[bool, Dict[str, Any]]:
    """
    检查 bitsandbytes 安装和配置。

    返回:
        Tuple[bool, Dict]: (是否可用, 安装信息字典)
    """
    print_section("2. bitsandbytes 检查")
    results = {}
    all_passed = True

    try:
        import bitsandbytes as bnb
        import torch
        results['bnb_version'] = bnb.__version__
        print_result("bitsandbytes 安装", True, f"版本: {results['bnb_version']}")

        # 检查是否支持 INT4
        try:
            from transformers import BitsAndBytesConfig
            config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
            results['int4_support'] = True
            print_result("INT4 量化支持", True, "BitsAndBytesConfig 配置成功")
        except Exception as e:
            results['int4_support'] = False
            print_result("INT4 量化支持", False, f"配置失败: {e}")
            all_passed = False

    except ImportError as e:
        results['bnb_installed'] = False
        print_result("bitsandbytes 安装", False, f"未安装: {e}")
        print("      安装命令: pip install bitsandbytes")
        all_passed = False

    return all_passed, results


def check_config_files() -> Tuple[bool, Dict[str, Any]]:
    """
    检查配置文件中的 INT4 设置。

    返回:
        Tuple[bool, Dict]: (配置是否正确, 配置信息字典)
    """
    print_section("3. 配置文件检查")
    results = {}
    all_passed = True

    try:
        from app.core.ai_config import ai_config

        # 检查 QWEN_LOAD_IN_4BIT 配置
        load_in_4bit = ai_config.QWEN_LOAD_IN_4BIT
        results['QWEN_LOAD_IN_4BIT'] = load_in_4bit
        print_result("QWEN_LOAD_IN_4BIT", load_in_4bit, f"值: {load_in_4bit}")

        if not load_in_4bit:
            print("      ⚠️ 建议: 设置 QWEN_LOAD_IN_4BIT = True 以启用 INT4 量化")
            all_passed = False

        # 检查模型路径
        model_path = ai_config.QWEN_MODEL_PATH
        results['model_path'] = str(model_path)
        model_exists = model_path.exists()
        print_result("模型路径存在", model_exists, f"路径: {model_path}")

        if not model_exists:
            print("      ⚠️ 模型路径不存在，无法验证实际量化效果")
            all_passed = False

        # 检查其他相关配置
        results['QWEN_DEVICE'] = ai_config.QWEN_DEVICE
        print_result("QWEN_DEVICE", True, f"值: {ai_config.QWEN_DEVICE}")

    except ImportError as e:
        print_result("配置文件加载", False, f"导入失败: {e}")
        all_passed = False
    except Exception as e:
        print_result("配置文件检查", False, f"检查失败: {e}")
        all_passed = False

    return all_passed, results


def check_quantization_config() -> Tuple[bool, Dict[str, Any]]:
    """
    检查 BitsAndBytesConfig 配置是否正确。

    返回:
        Tuple[bool, Dict]: (配置是否正确, 配置详情字典)
    """
    print_section("4. BitsAndBytesConfig 配置检查")
    results = {}
    all_passed = True

    try:
        import torch
        from transformers import BitsAndBytesConfig

        # 创建 INT4 量化配置
        config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

        results['load_in_4bit'] = config.load_in_4bit
        results['bnb_4bit_quant_type'] = config.bnb_4bit_quant_type
        results['bnb_4bit_compute_dtype'] = str(config.bnb_4bit_compute_dtype)
        results['bnb_4bit_use_double_quant'] = config.bnb_4bit_use_double_quant

        print_result("load_in_4bit", config.load_in_4bit == True, f"值: {config.load_in_4bit}")
        print_result("bnb_4bit_quant_type", config.bnb_4bit_quant_type == "nf4", f"值: {config.bnb_4bit_quant_type}")
        print_result("bnb_4bit_compute_dtype", True, f"值: {config.bnb_4bit_compute_dtype}")
        print_result("bnb_4bit_use_double_quant", config.bnb_4bit_use_double_quant == True, f"值: {config.bnb_4bit_use_double_quant}")

        # 检查是否包含不应该存在的 INT8 参数
        has_int8_param = hasattr(config, 'llm_int8_enable_fp32_cpu_offload')
        if has_int8_param:
            int8_value = getattr(config, 'llm_int8_enable_fp32_cpu_offload', None)
            # 只有当 INT8 参数被显式设置为 True 时才报告冲突
            if int8_value is True:
                print_result("INT8 参数检查", False, "⚠️ 检测到 INT8 参数被启用，可能导致配置冲突")
                results['has_int8_conflict'] = True
                all_passed = False
            else:
                print_result("INT8 参数检查", True, "无 INT8 参数冲突")
                results['has_int8_conflict'] = False
        else:
            print_result("INT8 参数检查", True, "无 INT8 参数冲突")
            results['has_int8_conflict'] = False

    except Exception as e:
        print_result("BitsAndBytesConfig 检查", False, f"检查失败: {e}")
        all_passed = False

    return all_passed, results


def verify_model_loading() -> Tuple[bool, Dict[str, Any]]:
    """
    验证模型加载和量化效果。

    返回:
        Tuple[bool, Dict]: (验证是否成功, 验证结果字典)
    """
    print_section("5. 模型加载验证")
    results = {}
    all_passed = True

    try:
        from app.core.ai_config import ai_config

        model_path = ai_config.QWEN_MODEL_PATH
        if not model_path.exists():
            print_result("模型加载", False, "模型路径不存在，跳过加载验证")
            return False, {'error': 'model_path_not_found'}

        print("  正在加载模型，请稍候...")

        # 记录加载前显存
        import torch
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            mem_before = torch.cuda.memory_allocated() / 1024**2
            results['mem_before_mb'] = mem_before

        # 加载模型
        from app.services.qwen_service import QwenService
        service = QwenService(
            model_path=model_path,
            device="cuda",
            load_in_4bit=True,
            auto_load=True,
            cpu_offload=False
        )

        if not service.is_loaded:
            print_result("模型加载", False, "模型加载失败")
            return False, {'error': 'model_load_failed'}

        print_result("模型加载", True, "模型加载成功")

        # 检查显存使用
        if torch.cuda.is_available():
            mem_after = torch.cuda.memory_allocated() / 1024**2
            mem_peak = torch.cuda.max_memory_allocated() / 1024**2
            results['mem_after_mb'] = mem_after
            results['mem_peak_mb'] = mem_peak
            results['mem_used_mb'] = mem_after - results.get('mem_before_mb', 0)

            print_result("显存使用", True, f"已用: {results['mem_used_mb']:.0f} MB, 峰值: {mem_peak:.0f} MB")

            # INT4 量化的 2B 模型应该使用约 2-3GB 显存
            if results['mem_used_mb'] < 4000:
                print_result("INT4 量化效果", True, f"显存使用 {results['mem_used_mb']:.0f} MB，符合 INT4 量化预期")
            else:
                print_result("INT4 量化效果", False, f"显存使用 {results['mem_used_mb']:.0f} MB，可能未正确应用 INT4 量化")
                all_passed = False

        # 检查模型量化状态
        model_info = service.get_model_info()
        results['model_info'] = model_info
        print_result("量化配置", model_info.get('features', {}).get('int4_quantization', False),
                    f"INT4 量化: {model_info.get('features', {}).get('int4_quantization', False)}")

        # 清理
        del service
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    except Exception as e:
        print_result("模型加载验证", False, f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    return all_passed, results


def generate_report(env_results: Dict, bnb_results: Dict,
                   config_results: Dict, quant_results: Dict,
                   model_results: Dict) -> None:
    """
    生成验证报告。

    参数:
        env_results: 环境检查结果
        bnb_results: bitsandbytes 检查结果
        config_results: 配置文件检查结果
        quant_results: 量化配置检查结果
        model_results: 模型加载验证结果
    """
    print_section("验证报告摘要")

    checks = [
        ("环境检查", env_results.get('passed', False)),
        ("bitsandbytes", bnb_results.get('passed', False)),
        ("配置文件", config_results.get('passed', False)),
        ("量化配置", quant_results.get('passed', False)),
        ("模型加载", model_results.get('passed', False))
    ]

    passed_count = sum(1 for _, passed in checks if passed)
    total_count = len(checks)

    for name, passed in checks:
        print_result(name, passed)

    print(f"\n  总计: {passed_count}/{total_count} 项通过")

    if passed_count == total_count:
        print("\n  🎉 所有验证项目通过！INT4 量化配置正确。")
    else:
        print("\n  ⚠️ 部分验证项目未通过，请检查上述问题。")


def main() -> None:
    """
    主函数：执行所有验证步骤。

    验证流程：
    1. 检查运行环境（Python、CUDA、GPU）
    2. 检查 bitsandbytes 安装状态
    3. 检查配置文件中的 INT4 设置
    4. 检查 BitsAndBytesConfig 配置
    5. 验证模型加载和量化效果
    6. 生成验证报告
    """
    print("\n" + "="*60)
    print("  INT4 量化配置验证脚本")
    print("  Qwen3-VL-2B-Instruct")
    print("="*60)

    # 1. 环境检查
    env_passed, env_results = check_environment()
    env_results['passed'] = env_passed

    # 2. bitsandbytes 检查
    bnb_passed, bnb_results = check_bitsandbytes()
    bnb_results['passed'] = bnb_passed

    # 3. 配置文件检查
    config_passed, config_results = check_config_files()
    config_results['passed'] = config_passed

    # 4. 量化配置检查
    quant_passed, quant_results = check_quantization_config()
    quant_results['passed'] = quant_passed

    # 5. 模型加载验证（可选，需要模型存在）
    model_passed, model_results = verify_model_loading()
    model_results['passed'] = model_passed

    # 6. 生成报告
    generate_report(env_results, bnb_results, config_results, quant_results, model_results)


if __name__ == "__main__":
    main()
