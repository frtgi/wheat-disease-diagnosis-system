# Python 3.10 + GPU 环境配置指南

## 状态总结

✅ **已完成**:
- Python 3.10 conda环境已创建 (`wheatagent-py310`)
- 项目配置文件已更新

⏳ **待完成**:
- 安装PyTorch GPU版本
- 安装项目依赖
- 验证GPU可用性

---

## 手动安装步骤

### 步骤1: 激活Python 3.10环境

```powershell
conda activate wheatagent-py310
```

### 步骤2: 安装PyTorch GPU版本

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**说明**:
- CUDA 12.1版本
- 约2-3GB下载量
- 安装时间约5-10分钟

### 步骤3: 安装项目依赖

```powershell
pip install -r requirements.txt
```

### 步骤4: 验证GPU安装

```powershell
python check_gpu.py
```

---

## 快速启动脚本

已创建 `activate_env.bat`，双击即可激活环境。

或者手动执行：
```powershell
conda activate wheatagent-py310
python scripts/train_all_models.py --stage all
```

---

## 验证清单

- [ ] Python 3.10环境已激活
- [ ] PyTorch GPU版本安装成功
- [ ] CUDA可用
- [ ] 训练脚本可正常运行

---

## 常见问题

### Q1: PyTorch安装失败
**解决方案**: 使用conda安装
```powershell
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

### Q2: CUDA不可用
**检查项**:
1. NVIDIA驱动是否安装
2. GPU是否支持CUDA
3. 是否需要重启终端

### Q3: 显存不足
**解决方案**: 减小batch_size
```powershell
python scripts/train_all_models.py --stage yolo --batch-size 4
```

---

## 下一步

完成上述安装后，即可使用GPU加速训练：

```powershell
# 激活环境
conda activate wheatagent-py310

# 运行训练
python scripts/train_all_models.py --stage all
```

---

**创建时间**: 2026-02-10  
**环境名称**: wheatagent-py310  
**Python版本**: 3.10
