# 一键启动脚本
# 同时启动前端和后端服务

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  小麦病害诊断系统 - 一键启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "启动时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# 获取脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
$frontendDir = Join-Path $scriptDir "frontend"

Write-Host "后端目录：$backendDir" -ForegroundColor Gray
Write-Host "前端目录：$frontendDir" -ForegroundColor Gray
Write-Host ""

# 检查服务状态
Write-Host "[1/3] 检查服务端口占用情况..." -ForegroundColor Yellow

# 检查 8000 端口（后端）
$backendPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($backendPort) {
    Write-Host "⚠ 后端端口 8000 已被占用 (PID: $($backendPort.OwningProcess))" -ForegroundColor Yellow
} else {
    Write-Host "✓ 后端端口 8000 可用" -ForegroundColor Green
}

# 检查 5173 端口（前端）
$frontendPort = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($frontendPort) {
    Write-Host "⚠ 前端端口 5173 已被占用 (PID: $($frontendPort.OwningProcess))" -ForegroundColor Yellow
} else {
    Write-Host "✓ 前端端口 5173 可用" -ForegroundColor Green
}

Write-Host ""

# 启动后端服务
Write-Host "[2/3] 启动后端服务..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:backendDir
    Write-Host "启动后端服务..." -ForegroundColor Cyan
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
Write-Host "✓ 后端服务启动中 (Job ID: $($backendJob.Id))" -ForegroundColor Green

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端服务
Write-Host "[3/3] 启动前端服务..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:frontendDir
    Write-Host "启动前端服务..." -ForegroundColor Cyan
    npm run dev
}
Write-Host "✓ 前端服务启动中 (Job ID: $($frontendJob.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后端服务：http://localhost:8000" -ForegroundColor Cyan
Write-Host "API 文档：http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "前端服务：http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键停止所有服务..." -ForegroundColor Yellow

# 等待用户输入
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 停止所有服务
Write-Host ""
Write-Host "正在停止服务..." -ForegroundColor Yellow
Stop-Job -Job $backendJob, $frontendJob
Remove-Job -Job $backendJob, $frontendJob
Write-Host "✓ 所有服务已停止" -ForegroundColor Green
