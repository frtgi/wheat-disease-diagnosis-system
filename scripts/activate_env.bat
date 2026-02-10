@echo off
echo ============================================
echo 激活WheatAgent Python 3.10 GPU环境
echo ============================================
echo.
conda activate wheatagent-py310
echo.
echo 环境已激活！
echo.
echo 可用命令:
echo   python check_gpu.py              - 检查GPU环境
echo   python scripts/train_all_models.py --stage all  - 运行训练
echo.
cmd /k
