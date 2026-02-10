@echo off
echo ============================================
echo 以管理员身份运行CUDA安装
echo ============================================
echo.

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 已获取管理员权限
    echo.
    echo 正在运行CUDA安装脚本...
    python install_cuda.py
) else (
    echo ❌ 需要管理员权限
    echo.
    echo 请右键点击此文件，选择"以管理员身份运行"
    echo.
    pause
)
