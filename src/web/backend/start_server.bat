@echo off
echo ========================================
echo WheatAgent FastAPI 后端服务
echo ========================================
echo.
echo 启动服务器...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
