# 前端服务启动脚本
# 用于启动 Vue3 前端开发服务器

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  小麦病害诊断系统 - 前端服务启动" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Node.js 环境
Write-Host "[1/4] 检查 Node.js 环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    $npmVersion = npm --version 2>&1
    Write-Host "✓ Node.js 版本：$nodeVersion" -ForegroundColor Green
    Write-Host "✓ npm 版本：$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js 未安装或未添加到 PATH" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host "[2/4] 检查项目依赖..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "✓ 依赖已安装" -ForegroundColor Green
} else {
    Write-Host "⚠ 依赖未安装，正在安装..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
}

# 检查环境配置
Write-Host "[3/4] 检查环境配置..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ 环境配置文件存在" -ForegroundColor Green
} else {
    Write-Host "⚠ 环境配置文件不存在" -ForegroundColor Yellow
}

# 启动前端服务
Write-Host "[4/4] 启动前端服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "服务地址：http://localhost:5173" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 启动开发服务器
try {
    npm run dev
} catch {
    Write-Host "✗ 服务启动失败：$_" -ForegroundColor Red
    exit 1
}
