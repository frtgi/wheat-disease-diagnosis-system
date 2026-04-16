@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
call conda activate wheat_agent
python tests/test_system_integration.py
pause
