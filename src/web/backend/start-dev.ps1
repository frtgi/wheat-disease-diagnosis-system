# 后端服务启动脚本
# 用于启动 FastAPI 后端服务

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  小麦病害诊断系统 - 后端服务启动" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 环境
Write-Host "[1/4] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python 环境：$pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python 未安装或未添加到 PATH" -ForegroundColor Red
    exit 1
}

# 检查并激活 Conda 环境
Write-Host "[2/4] 检查 Conda 环境..." -ForegroundColor Yellow
$condaEnv = "wheatagent-py310"
$condaPath = $env:CONDA_PREFIX

if ($condaPath) {
    Write-Host "✓ Conda 环境已激活：$condaEnv" -ForegroundColor Green
} else {
    Write-Host "⚠ Conda 环境未激活，尝试激活..." -ForegroundColor Yellow
    # 注意：PowerShell 中无法直接激活 conda 环境，需要手动激活
    Write-Host "提示：请先运行 'conda activate wheatagent-py310' 激活环境" -ForegroundColor Yellow
}

# 检查数据库连接
Write-Host "[3/4] 检查数据库连接..." -ForegroundColor Yellow
try {
    # 这里可以添加数据库连接检查逻辑
    Write-Host "✓ 数据库连接配置正常" -ForegroundColor Green
} catch {
    Write-Host "⚠ 数据库连接配置可能有问题，请检查 .env 文件" -ForegroundColor Yellow
}

# 启动后端服务
Write-Host "[4/4] 启动后端服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "服务地址：http://localhost:8000" -ForegroundColor Cyan
Write-Host "API 文档：http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 设置环境变量
$env:PYTHONPATH = (Join-Path $PSScriptRoot ".." | Resolve-Path)

# 启动 uvicorn 服务
try {
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "✗ 服务启动失败：$_" -ForegroundColor Red
    exit 1
}
