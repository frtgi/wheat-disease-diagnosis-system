# PowerShell script: Setup CUDA and PyTorch environment variables
# Optimized for RTX 3050 Laptop GPU with 4GB VRAM

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CUDA and PyTorch Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set PyTorch memory allocation strategy
Write-Host "Setting PyTorch memory allocation..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:128,garbage_collection_threshold:0.6", "User")
Write-Host "   OK: PYTORCH_CUDA_ALLOC_CONF" -ForegroundColor Green

# Disable CUDA synchronization
Write-Host "Setting CUDA launch mode..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("CUDA_LAUNCH_BLOCKING", "0", "User")
Write-Host "   OK: CUDA_LAUNCH_BLOCKING" -ForegroundColor Green

# Set OMP threads
Write-Host "Setting OMP threads..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("OMP_NUM_THREADS", "4", "User")
Write-Host "   OK: OMP_NUM_THREADS" -ForegroundColor Green

# Set MKL threads
Write-Host "Setting MKL threads..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("MKL_NUM_THREADS", "4", "User")
Write-Host "   OK: MKL_NUM_THREADS" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please restart PowerShell or IDE for changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next step: Run training with:" -ForegroundColor Green
Write-Host "   python train_fast.py --epochs 50" -ForegroundColor White
