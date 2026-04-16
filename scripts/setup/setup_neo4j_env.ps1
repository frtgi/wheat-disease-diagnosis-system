# ============================================================
# Neo4j 环境变量配置脚本 (PowerShell)
# 用途: 设置 Neo4j 图数据库连接所需的环境变量
# 使用方法: 
#   1. 以管理员身份运行 PowerShell
#   2. 执行: .\setup_neo4j_env.ps1
#   3. 根据提示输入配置信息
# ============================================================

param(
    [string]$Action = "setup",
    [string]$Uri = "bolt://localhost:7687",
    [string]$User = "neo4j",
    [string]$Password = "",
    [string]$Database = "neo4j",
    [int]$MaxPoolSize = 50,
    [int]$ConnectionTimeout = 30,
    [switch]$SystemWide = $false
)

function Write-Header {
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 69) -ForegroundColor Cyan
    Write-Host "|                    Neo4j 环境变量配置工具                         |" -ForegroundColor Cyan
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 69) -ForegroundColor Cyan
    Write-Host ""
}

function Show-CurrentConfig {
    Write-Host "当前 Neo4j 环境变量配置:" -ForegroundColor Yellow
    Write-Host ("-" * 50)
    
    $envVars = @(
        "NEO4J_URI",
        "NEO4J_USER", 
        "NEO4J_PASSWORD",
        "NEO4J_DATABASE",
        "NEO4J_MAX_CONNECTION_POOL_SIZE",
        "NEO4J_CONNECTION_TIMEOUT"
    )
    
    foreach ($var in $envVars) {
        $value = [Environment]::GetEnvironmentVariable($var, "User")
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($var, "Machine")
        }
        if ($value) {
            if ($var -eq "NEO4J_PASSWORD") {
                Write-Host "  $var = ******" -ForegroundColor Green
            } else {
                Write-Host "  $var = $value" -ForegroundColor Green
            }
        } else {
            Write-Host "  $var = <未设置>" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

function Set-Neo4jEnvVars {
    param(
        [string]$Uri,
        [string]$User,
        [string]$Password,
        [string]$Database,
        [int]$MaxPoolSize,
        [int]$ConnectionTimeout,
        [bool]$SystemWide
    )
    
    $target = if ($SystemWide) { "Machine" } else { "User" }
    $scopeText = if ($SystemWide) { "系统级" } else { "用户级" }
    
    Write-Host "正在设置${scopeText}环境变量..." -ForegroundColor Yellow
    
    try {
        [Environment]::SetEnvironmentVariable("NEO4J_URI", $Uri, $target)
        [Environment]::SetEnvironmentVariable("NEO4J_USER", $User, $target)
        [Environment]::SetEnvironmentVariable("NEO4J_PASSWORD", $Password, $target)
        [Environment]::SetEnvironmentVariable("NEO4J_DATABASE", $Database, $target)
        [Environment]::SetEnvironmentVariable("NEO4J_MAX_CONNECTION_POOL_SIZE", $MaxPoolSize.ToString(), $target)
        [Environment]::SetEnvironmentVariable("NEO4J_CONNECTION_TIMEOUT", $ConnectionTimeout.ToString(), $target)
        
        Write-Host "✅ 环境变量设置成功!" -ForegroundColor Green
        
        if ($SystemWide) {
            Write-Host ""
            Write-Host "注意: 系统级环境变量已设置，需要重启终端或重新登录才能生效。" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ 设置环境变量失败: $_" -ForegroundColor Red
        if ($SystemWide) {
            Write-Host "提示: 设置系统级环境变量需要管理员权限。" -ForegroundColor Yellow
        }
    }
}

function Remove-Neo4jEnvVars {
    param([bool]$SystemWide)
    
    $target = if ($SystemWide) { "Machine" } else { "User" }
    $scopeText = if ($SystemWide) { "系统级" } else { "用户级" }
    
    Write-Host "正在删除${scopeText}Neo4j环境变量..." -ForegroundColor Yellow
    
    $envVars = @(
        "NEO4J_URI",
        "NEO4J_USER", 
        "NEO4J_PASSWORD",
        "NEO4J_DATABASE",
        "NEO4J_MAX_CONNECTION_POOL_SIZE",
        "NEO4J_CONNECTION_TIMEOUT"
    )
    
    try {
        foreach ($var in $envVars) {
            [Environment]::SetEnvironmentVariable($var, $null, $target)
        }
        Write-Host "✅ 环境变量已删除!" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 删除环境变量失败: $_" -ForegroundColor Red
    }
}

function Test-Neo4jConnection {
    Write-Host "正在测试 Neo4j 连接..." -ForegroundColor Yellow
    
    $uri = [Environment]::GetEnvironmentVariable("NEO4J_URI", "User")
    if (-not $uri) {
        $uri = [Environment]::GetEnvironmentVariable("NEO4J_URI", "Machine")
    }
    $uri = $uri ?? "bolt://localhost:7687"
    
    $host_part = $uri -replace "bolt://", "" -replace ":7687", ""
    $port = 7687
    
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect($host_part, $port, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(5000)
        
        if ($wait) {
            try {
                $tcp.EndConnect($connect)
                Write-Host "✅ Neo4j 服务可达: $host_part`:$port" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Neo4j 连接失败: $_" -ForegroundColor Red
            }
        }
        else {
            Write-Host "❌ Neo4j 连接超时: 无法连接到 $host_part`:$port" -ForegroundColor Red
        }
        $tcp.Close()
    }
    catch {
        Write-Host "❌ 连接测试失败: $_" -ForegroundColor Red
    }
}

function Interactive-Setup {
    Write-Host "请输入 Neo4j 配置信息 (直接回车使用默认值):" -ForegroundColor Cyan
    Write-Host ""
    
    $inputUri = Read-Host "  Neo4j URI [$Uri]"
    if ($inputUri) { $Uri = $inputUri }
    
    $inputUser = Read-Host "  用户名 [$User]"
    if ($inputUser) { $User = $inputUser }
    
    $inputPassword = Read-Host "  密码 [输入新密码]"
    if ($inputPassword) { $Password = $inputPassword }
    
    $inputDatabase = Read-Host "  数据库名 [$Database]"
    if ($inputDatabase) { $Database = $inputDatabase }
    
    $inputMaxPool = Read-Host "  最大连接池大小 [$MaxPoolSize]"
    if ($inputMaxPool) { $MaxPoolSize = [int]$inputMaxPool }
    
    $inputTimeout = Read-Host "  连接超时(秒) [$ConnectionTimeout]"
    if ($inputTimeout) { $ConnectionTimeout = [int]$inputTimeout }
    
    $systemWideInput = Read-Host "  设置为系统级环境变量? (y/N)"
    $SystemWide = ($systemWideInput -eq "y" -or $systemWideInput -eq "Y")
    
    Write-Host ""
    Write-Host "配置摘要:" -ForegroundColor Yellow
    Write-Host "  URI: $Uri"
    Write-Host "  用户: $User"
    Write-Host "  密码: ******"
    Write-Host "  数据库: $Database"
    Write-Host "  最大连接池: $MaxPoolSize"
    Write-Host "  连接超时: $ConnectionTimeout 秒"
    Write-Host "  作用范围: $(if($SystemWide){'系统级'}else{'用户级'})"
    Write-Host ""
    
    $confirm = Read-Host "确认设置? (Y/n)"
    if ($confirm -ne "n" -and $confirm -ne "N") {
        Set-Neo4jEnvVars -Uri $Uri -User $User -Password $Password -Database $Database `
            -MaxPoolSize $MaxPoolSize -ConnectionTimeout $ConnectionTimeout -SystemWide $SystemWide
    }
    else {
        Write-Host "已取消设置。" -ForegroundColor Yellow
    }
}

# 主程序
Write-Header

switch ($Action.ToLower()) {
    "setup" {
        if (-not $Password) {
            Interactive-Setup
        }
        else {
            Set-Neo4jEnvVars -Uri $Uri -User $User -Password $Password -Database $Database `
                -MaxPoolSize $MaxPoolSize -ConnectionTimeout $ConnectionTimeout -SystemWide $SystemWide
        }
    }
    "show" {
        Show-CurrentConfig
    }
    "test" {
        Test-Neo4jConnection
    }
    "remove" {
        $confirm = Read-Host "确认删除所有 Neo4j 环境变量? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            Remove-Neo4jEnvVars -SystemWide $SystemWide
        }
    }
    default {
        Write-Host "用法:" -ForegroundColor Yellow
        Write-Host "  .\setup_neo4j_env.ps1 -Action setup    # 交互式设置"
        Write-Host "  .\setup_neo4j_env.ps1 -Action show     # 显示当前配置"
        Write-Host "  .\setup_neo4j_env.ps1 -Action test     # 测试连接"
        Write-Host "  .\setup_neo4j_env.ps1 -Action remove   # 删除环境变量"
        Write-Host ""
        Write-Host "快速设置示例:" -ForegroundColor Yellow
        Write-Host "  .\setup_neo4j_env.ps1 -Uri 'bolt://localhost:7687' -User 'neo4j' -Password 'yourpassword'"
    }
}

Write-Host ""
Write-Host "完成!" -ForegroundColor Green
