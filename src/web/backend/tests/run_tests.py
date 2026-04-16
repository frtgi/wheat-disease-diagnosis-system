"""
运行测试
python -m pytest tests/ -v
"""
import pytest
import sys

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "tests/"]))
