# CUDA Toolkit 安装指南

## 问题诊断

错误信息：
```
[WinError 126] 找不到指定的模块。Error loading "caffe2_nvrtc.dll"
```

**根本原因**: CUDA Toolkit 未安装

## 检查结果

| 组件 | 状态 | 说明 |
|------|------|------|
| NVIDIA驱动 | ✅ | 已安装 (版本 591.59) |
| CUDA Toolkit | ❌ | 未安装 |
| Visual C++ | ✅ | 已安装 |

## 解决方案

### 方案1: 自动安装（推荐）

运行PowerShell脚本自动下载安装：

```powershell
# 以管理员身份运行PowerShell
powershell -ExecutionPolicy Bypass -File install_cuda_toolkit.ps1
```

**注意**: 下载文件约3GB，安装时间约10-15分钟

### 方案2: 手动安装

#### 步骤1: 下载CUDA Toolkit 12.1

访问官方下载页面：
https://developer.nvidia.com/cuda-12-1-0-download-archive

或直接下载：
```
https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_531.14_windows.exe
```

#### 步骤2: 运行安装程序

1. 双击下载的安装程序
2. 选择"精简"安装模式
3. 等待安装完成
4. 重启终端

#### 步骤3: 验证安装

```powershell
nvcc --version
```

应显示：
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Mon Apr  3 17:47:16 UTC 2023
Cuda compilation tools, release 12.1, V12.1.66
```

### 方案3: 使用conda安装CUDA（替代方案）

如果不想安装完整的CUDA Toolkit，可以使用conda安装：

```powershell
conda activate wheatagent-py310
conda install cuda -c nvidia
```

**注意**: 这只会安装CUDA运行时库，不包含开发工具

## 安装后验证

### 1. 检查CUDA环境变量

```powershell
$env:CUDA_PATH
```

应显示：
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1
```

### 2. 检查PyTorch CUDA可用性

```powershell
python check_gpu.py
```

应显示：
```
✅ CUDA可用
   CUDA版本: 12.1
   GPU数量: 1
   GPU 0: NVIDIA GeForce RTX XXXX
```

### 3. 运行训练脚本

```powershell
python scripts/train_all_models.py --stage all
```

## 常见问题

### Q1: 安装过程中提示"驱动版本不兼容"
**解决**: 先更新NVIDIA驱动到最新版本

### Q2: 安装后仍提示DLL错误
**解决**: 
1. 重启终端
2. 重启系统
3. 检查环境变量是否正确设置

### Q3: 磁盘空间不足
**解决**: CUDA Toolkit需要约4GB磁盘空间，确保C盘有足够空间

### Q4: 下载速度慢
**解决**: 使用国内镜像或迅雷等下载工具

## 替代方案: 使用CPU训练

如果无法安装CUDA Toolkit，可以临时使用CPU版本：

```powershell
python fix_cuda_dll.py --cpu
```

这将：
- 卸载PyTorch GPU版本
- 安装PyTorch CPU版本
- 训练速度较慢但可正常运行

## 下一步

完成CUDA Toolkit安装后：

1. 重启终端
2. 激活环境：`conda activate wheatagent-py310`
3. 验证GPU：`python check_gpu.py`
4. 运行训练：`python scripts/train_all_models.py --stage all`

---

**创建时间**: 2026-02-10  
**CUDA版本**: 12.1  
**PyTorch版本**: 2.x
