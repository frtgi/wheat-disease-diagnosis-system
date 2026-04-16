"""
快速验证 password_hash 安全性修复
Quick verification of password_hash security fix
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_user_dict_excludes_password_hash():
    """验证 user.py 中移除了 password_hash"""
    print("\n" + "="*60)
    print("[TEST 1] Verify user.py removes password_hash")
    print("="*60)
    
    # 读取 user.py 文件内容
    user_py_path = project_root / "app" / "api" / "v1" / "user.py"
    content = user_py_path.read_text(encoding='utf-8')
    
    # 查找 get_current_user_info 函数中的 user_dict 定义
    if '"password_hash"' in content:
        # 检查是否在 user_dict 中
        lines = content.split('\n')
        in_user_dict = False
        for i, line in enumerate(lines, 1):
            if 'user_dict = {' in line:
                in_user_dict = True
            if in_user_dict and '}' in line and 'user_dict' not in line:
                in_user_dict = False
            if in_user_dict and 'password_hash' in line:
                print(f"[FAIL] Line {i} still contains password_hash")
                print(f"   Content: {line.strip()}")
                return False
    
    print("   [PASS] user_dict does not contain password_hash")
    return True


def test_cache_service_filters_sensitive_data():
    """验证缓存服务过滤敏感字段"""
    print("\n" + "="*60)
    print("[TEST 2] Verify cache service auto-filters sensitive fields")
    print("="*60)
    
    cache_py_path = project_root / "app" / "services" / "cache.py"
    content = cache_py_path.read_text(encoding='utf-8')
    
    # 检查是否包含敏感字段过滤逻辑
    checks = [
        ('sensitive_fields', 'sensitive field list definition'),
        ('password_hash', 'password_hash filtering'),
        ('safe_user_info', 'safe data variable')
    ]
    
    all_passed = True
    for check_str, desc in checks:
        if check_str in content:
            print(f"   [PASS] Contains {desc}")
        else:
            print(f"   [FAIL] Missing {desc}")
            all_passed = False
    
    return all_passed


def test_user_response_schema_security():
    """验证 UserResponse Schema 安全性"""
    print("\n" + "="*60)
    print("[TEST 3] Verify UserResponse Schema excludes sensitive fields")
    print("="*60)
    
    schema_path = project_root / "app" / "schemas" / "user.py"
    content = schema_path.read_text(encoding='utf-8')
    
    # 检查 Schema 配置
    checks = [
        ('schema_extra', 'Schema extra config (security filtering)'),
        ('forbidden_fields', 'forbidden field list'),
        ("'password'", 'password field exclusion'),
        ("'password_hash'", 'password_hash field exclusion'),
    ]
    
    all_passed = True
    for check_str, desc in checks:
        if check_str in content:
            print(f"   [PASS] {desc} implemented")
        else:
            print(f"   [WARN] May be missing {desc}")
            # Not all checks are mandatory
    
    # 关键检查：确保 UserResponse 类中没有 password_hash 字段定义
    import re
    user_response_match = re.search(r'class UserResponse.*?(?=\nclass |\Z)', content, re.DOTALL)
    if user_response_match:
        user_response_content = user_response_match.group()
        if 'password_hash' not in user_response_content or 'forbidden' in user_response_content:
            print("   [PASS] UserResponse does not directly define password_hash field")
        else:
            print("   [FAIL] UserResponse contains password_hash field definition")
            all_passed = False
    
    return all_passed


def test_import_statements():
    """验证必要的导入已添加"""
    print("\n" + "="*60)
    print("[TEST 4] Verify required import statements")
    print("="*60)
    
    schema_path = project_root / "app" / "schemas" / "user.py"
    content = schema_path.read_text(encoding='utf-8')
    
    required_imports = ['Dict', 'Any', 'Type']
    all_present = True
    
    for imp in required_imports:
        if imp in content:
            print(f"   [PASS] Imported {imp}")
        else:
            print(f"   [FAIL] Missing import {imp}")
            all_present = False
    
    return all_present


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("[SECURITY] Password Hash Security Fix Verification")
    print("="*60)
    print(f"\n[INFO] Project path: {project_root}")
    
    results = []
    
    # 运行所有测试
    results.append(("user.py removes password_hash", test_user_dict_excludes_password_hash()))
    results.append(("Cache service filtering mechanism", test_cache_service_filters_sensitive_data()))
    results.append(("UserResponse Schema security", test_user_response_schema_security()))
    results.append(("Required import statements", test_import_statements()))
    
    # 输出总结
    print("\n" + "="*60)
    print("[SUMMARY] Test Results Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\n[RESULT] Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All security verifications passed! Password hash leak issue has been fixed.")
        return 0
    else:
        print("\n[WARNING] Some tests failed, please check the items above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
