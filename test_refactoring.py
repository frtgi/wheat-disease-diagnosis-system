# -*- coding: utf-8 -*-
"""
重构验证脚本

验证重构后的代码是否正常工作
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_preprocessing_module():
    """测试预处理模块"""
    print("\n" + "=" * 60)
    print("测试预处理模块")
    print("=" * 60)
    
    try:
        from src.utils.preprocessing import (
            preprocess_image,
            get_preprocessor,
            create_preprocessor,
            BackendType,
            PreprocessConfig,
            PreprocessResult
        )
        print("[OK] 预处理模块导入成功")
        
        config = PreprocessConfig(target_size=(640, 640))
        print(f"[OK] PreprocessConfig 创建成功: {config.target_size}")
        
        backend = BackendType.AUTO
        print(f"[OK] BackendType 枚举正常: {backend.value}")
        
        print("[OK] 所有预处理模块测试通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] 预处理模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qwen_interface():
    """测试 Qwen 接口规范"""
    print("\n" + "=" * 60)
    print("测试 Qwen 接口规范")
    print("=" * 60)
    
    try:
        from src.cognition.qwen_interface import (
            QwenModelInterface,
            QwenDiagnosisResult,
            create_diagnosis_result
        )
        print("[OK] Qwen 接口模块导入成功")
        
        result = create_diagnosis_result(
            success=True,
            disease_name="条锈病",
            confidence=0.85
        )
        print(f"[OK] QwenDiagnosisResult 创建成功: {result.disease_name}")
        
        print("[OK] 所有 Qwen 接口测试通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] Qwen 接口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utils_exports():
    """测试 utils 模块导出"""
    print("\n" + "=" * 60)
    print("测试 utils 模块导出")
    print("=" * 60)
    
    try:
        from src.utils import (
            ImagePreprocessor,
            PreprocessConfig,
            PreprocessResult,
            BackendType,
            preprocess_image,
            get_preprocessor,
            create_preprocessor
        )
        print("[OK] utils 模块导出正常")
        return True
        
    except Exception as e:
        print(f"[ERROR] utils 模块导出测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("WheatAgent 重构验证测试")
    print("=" * 60)
    
    results = {
        "预处理模块": test_preprocessing_module(),
        "Qwen 接口": test_qwen_interface(),
        "utils 导出": test_utils_exports()
    }
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有测试通过！重构成功！")
    else:
        print("[WARNING] 部分测试失败，请检查错误信息")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
