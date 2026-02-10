# CUDA Toolkit 12.1 安装脚本
# 自动下载并安装CUDA Toolkit

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CUDA Toolkit 12.1 安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# CUDA 12.1 下载链接
$cudaUrl = "https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_531.14_windows.exe"
$installerPath = "$env:TEMP\cuda_12.1.0_531.14_windows.exe"

# 检查是否已安装
$cudaPath = $env:CUDA_PATH
if ($cudaPath -and (Test-Path $cudaPath)) {
    Write-Host "`n✅ CUDA Toolkit 已安装: $cudaPath" -ForegroundColor Green
    
    # 检查版本
    $versionFile = Join-Path $cudaPath "version.json"
    if (Test-Path $versionFile) {
        $versionInfo = Get-Content $versionFile | ConvertFrom-Json
        $version = $versionInfo.cuda.version
        Write-Host "   版本: $version" -ForegroundColor Green
    }
    
    Write-Host "`n无需重新安装" -ForegroundColor Yellow
    exit 0
}

# 下载CUDA Toolkit
Write-Host "`n📥 下载CUDA Toolkit 12.1..." -ForegroundColor Yellow
Write-Host "下载链接: $cudaUrl" -ForegroundColor Gray
Write-Host "保存路径: $installerPath" -ForegroundColor Gray

try {
    # 使用.NET WebClient下载（支持进度显示）
    $webClient = New-Object System.Net.WebClient
    
    # 注册进度事件
    Register-ObjectEvent -InputObject $webClient -EventName DownloadProgressChanged -Action {
        $percent = $EventArgs.ProgressPercentage
        Write-Progress -Activity "下载CUDA Toolkit" -Status "$percent% 完成" -PercentComplete $percent
    } | Out-Null
    
    # 下载文件
    $webClient.DownloadFileAsync($cudaUrl, $installerPath)
    
    # 等待下载完成
    while ($webClient.IsBusy) {
        Start-Sleep -Milliseconds 100
    }
    
    Write-Progress -Activity "下载CUDA Toolkit" -Completed
    Write-Host "`n✅ 下载完成" -ForegroundColor Green
}
catch {
    Write-Host "`n❌ 下载失败: $_" -ForegroundColor Red
    Write-Host "请手动下载安装:" -ForegroundColor Yellow
    Write-Host "https://developer.nvidia.com/cuda-downloads"
    exit 1
}

# 运行安装程序
Write-Host "`n🔧 启动CUDA Toolkit安装程序..." -ForegroundColor Yellow
Write-Host "安装参数: /s /nouninstall" -ForegroundColor Gray

# 静默安装参数
$installArgs = "/s /nouninstall"

try {
    $process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Host "`n✅ CUDA Toolkit 12.1 安装成功" -ForegroundColor Green
        
        # 刷新环境变量
        Write-Host "`n🔄 刷新环境变量..." -ForegroundColor Yellow
        $env:CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1"
        $env:PATH = "$env:CUDA_PATH\bin;$env:PATH"
        
        Write-Host "`n📊 验证安装..." -ForegroundColor Yellow
        nvcc --version
        
        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host "CUDA Toolkit 12.1 安装完成!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "`n请重启终端以应用环境变量更改" -ForegroundColor Yellow
    }
    else {
        Write-Host "`n❌ 安装失败，退出代码: $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "`n❌ 安装失败: $_" -ForegroundColor Red
    exit 1
}
finally {
    # 清理下载文件
    if (Test-Path $installerPath) {
        Remove-Item $installerPath -Force
        Write-Host "`n🗑️ 清理临时文件" -ForegroundColor Gray
    }
}
