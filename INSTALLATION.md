# 📦 IWDDA 安装部署指南

本文档详细说明如何在不同环境下安装和部署 IWDDA 系统。

## 📋 目录

- [系统要求](#系统要求)
- [环境准备](#环境准备)
- [依赖安装](#依赖安装)
- [Neo4j 配置](#neo4j-配置)
- [数据集准备](#数据集准备)
- [系统启动](#系统启动)
- [常见问题](#常见问题)

---

## 💻 系统要求

### 最低配置

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows 10+, Linux (Ubuntu 18.04+), macOS 10.15+ |
| Python | 3.8 或更高版本 |
| RAM | 8 GB |
| 磁盘空间 | 10 GB 可用空间 |
| GPU | 无（仅 CPU 模式） |

### 推荐配置

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows 11, Ubuntu 20.04+ |
| Python | 3.9 或 3.10 |
| RAM | 16 GB 或更高 |
| 磁盘空间 | 20 GB SSD |
| GPU | NVIDIA GPU (CUDA 11.0+)，显存 ≥ 6GB |
| CPU | 4 核或更高 |

### GPU 加速支持

- **NVIDIA GPU**: 需要 CUDA 11.0+ 和 cuDNN 8.0+
- **Apple Silicon (M1/M2)**: 支持 MPS 加速
- **其他 GPU**: 仅支持 CPU 模式

---

## 🔧 环境准备

### 1. 安装 Python

#### Windows
```bash
# 下载 Python 3.9 或 3.10
# https://www.python.org/downloads/

# 验证安装
python --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# 验证安装
python3 --version
```

#### macOS
```bash
# 使用 Homebrew 安装
brew install python@3.9

# 验证安装
python3 --version
```

### 2. 创建虚拟环境

```bash
# 进入项目目录
cd WheatAgent

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

# 验证虚拟环境
which python  # 应该显示 venv 目录下的 python
```

### 3. 升级 pip

```bash
pip install --upgrade pip
```

---

## 📚 依赖安装

### 1. 安装 PyTorch

根据您的系统选择合适的 PyTorch 版本：

#### CUDA 11.8 (推荐用于 NVIDIA GPU)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### CUDA 12.1
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### CPU 版本（无 GPU）
```bash
pip install torch torchvision torchaudio
```

#### Apple Silicon (M1/M2)
```bash
pip install torch torchvision torchaudio
```

### 2. 安装项目依赖

创建 `requirements.txt` 文件（如果不存在）：

```bash
# 安装核心依赖
pip install ultralytics transformers neo4j gradio

# 安装其他依赖
pip install opencv-python pillow numpy

# 安装开发依赖（可选）
pip install jupyter matplotlib tensorboard
```

或使用批量安装：

```bash
pip install -r requirements.txt
```

### 3. 验证安装

```bash
# 检查 PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')"

# 检查 CUDA
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"

# 检查其他依赖
python -c "import ultralytics, transformers, neo4j, gradio; print('All dependencies OK!')"
```

---

## 🗄️ Neo4j 配置

### 方案 1: Docker 部署（推荐）

#### 安装 Docker

**Windows:**
- 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**macOS:**
- 下载 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

#### 启动 Neo4j 容器

```bash
# 拉取 Neo4j 镜像
docker pull neo4j:5.15

# 启动容器
docker run -d \
  --name wheat-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/123456789s \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j-data:/data \
  -v neo4j-logs:/logs \
  neo4j:5.15

# 查看容器状态
docker ps
```

#### 访问 Neo4j 浏览器界面

打开浏览器访问：`http://localhost:7474`

- 用户名: `neo4j`
- 密码: `123456789s`

### 方案 2: 本地安装

#### Windows

1. 下载 [Neo4j Desktop](https://neo4j.com/download/)
2. 安装并启动 Neo4j Desktop
3. 创建新项目，设置密码为 `123456789s`

#### Linux

```bash
# 添加 Neo4j 仓库
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# 安装 Neo4j
sudo apt update
sudo apt install neo4j

# 启动服务
sudo systemctl start neo4j
sudo systemctl enable neo4j

# 设置密码
neo4j-admin set-initial-password 123456789s
```

#### macOS

```bash
# 使用 Homebrew 安装
brew install neo4j

# 启动服务
neo4j start

# 设置密码
neo4j-admin set-initial-password 123456789s
```

### 验证 Neo4j 连接

```bash
# 使用 Python 测试连接
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', '123456789s'))
driver.verify_connectivity()
print('Neo4j connection successful!')
driver.close()
"
```

---

## 📊 数据集准备

### 1. 下载预训练模型

```bash
# 下载 YOLOv8 预训练权重（首次运行会自动下载）
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 2. 准备小麦病害数据集

#### 数据集结构

```
datasets/wheat_data/
├── images/
│   ├── train/          # 训练图片
│   │   ├── aphid_0.jpg
│   │   ├── aphid_1.jpg
│   │   └── ...
│   └── val/            # 验证图片
│       ├── aphid_0.jpg
│       └── ...
└── labels/
    ├── train/          # 训练标签 (YOLO 格式)
    │   ├── aphid_0.txt
    │   ├── aphid_1.txt
    │   └── ...
    └── val/            # 验证标签
        ├── aphid_0.txt
        └── ...
```

#### 标签格式 (YOLO 格式)

每个 `.txt` 文件对应一张图片，格式为：
```
<class_id> <x_center> <y_center> <width> <height>
```

其中坐标为归一化值（0-1之间）。

示例：
```
6 0.5 0.5 0.9 0.9
```
表示类别 6（条锈病），中心在 (0.5, 0.5)，宽度 0.9，高度 0.9。

### 3. 创建数据集配置文件

编辑 `configs/wheat_disease.yaml`：

```yaml
# 数据集根目录（相对于项目根目录）
path: ../datasets/wheat_data

# 训练和验证集路径
train: images/train
val: images/val

# 类别数量
nc: 17

# 类别名称
names:
  0: 蚜虫 (Aphids)
  1: 螨虫 (Mites)
  2: 茎蝇 (Stem Fly)
  3: 锈病 (Rust)
  4: 茎锈病 (Stem Rust)
  5: 叶锈病 (Leaf Rust)
  6: 条锈病 (Stripe Rust)
  7: 黑粉病 (Smuts)
  8: 根腐病 (Common Root Rot)
  9: 叶斑病 (Spot Blotch)
  10: 小麦爆发病 (Wheat Blast)
  11: 赤霉病 (Fusarium Head Blight)
  12: 壳针孢叶斑病 (Septoria Leaf Blotch)
  13: 斑点叶斑病 (Speckled Leaf Blotch)
  14: 褐斑病 (Brown Spot)
  15: 白粉病 (Powdery Mildew)
  16: 健康 (Healthy)
```

### 4. 验证数据集

```bash
# 运行数据集验证
python -c "
import os
from pathlib import Path

data_root = Path('datasets/wheat_data')
img_train = list((data_root / 'images' / 'train').glob('*.jpg'))
lbl_train = list((data_root / 'labels' / 'train').glob('*.txt'))

print(f'训练图片数量: {len(img_train)}')
print(f'训练标签数量: {len(lbl_train)}')
print(f'数据集完整性: {'✅' if len(img_train) == len(lbl_train) else '❌'}')
"
```

---

## 🚀 系统启动

### 1. 初始化知识图谱

首次运行时，系统会自动初始化知识图谱。也可以手动初始化：

```bash
python -c "
from src.graph.graph_engine import KnowledgeAgent
kg = KnowledgeAgent(password='123456789s')
print('知识图谱初始化完成！')
kg.close()
"
```

### 2. 启动 Web 界面

```bash
# 启动 Gradio Web 服务
python app.py
```

访问 `http://localhost:7860` 使用 Web 界面。

### 3. 命令行测试

```bash
# 运行测试脚本
python main.py
```

或使用 Python 交互式测试：

```python
from main import WheatDoctor

# 初始化系统
doctor = WheatDoctor()

# 执行诊断
result = doctor.run_diagnosis(
    image_path="data/images/test_wheat.jpg",
    user_text="叶片上有黄色条纹"
)

# 打印结果
print(result)
```

### 4. 训练模型（可选）

```bash
# 训练 YOLOv8 模型
python src/vision/train.py
```

---

## ❓ 常见问题

### 问题 1: CUDA out of memory

**症状：**
```
RuntimeError: CUDA out of memory
```

**解决方案：**

1. 减小 batch size：
```python
# 编辑 src/vision/train.py
results = model.train(
    batch=8,  # 从 16 改为 8 或 4
    ...
)
```

2. 减小图像尺寸：
```python
results = model.train(
    imgsz=416,  # 从 512 改为 416
    ...
)
```

3. 使用 CPU 模式：
```python
results = model.train(
    device='cpu',
    ...
)
```

### 问题 2: Neo4j 连接失败

**症状：**
```
neo4j.exceptions.ServiceUnavailable: Unable to connect to neo4j at bolt://localhost:7687
```

**解决方案：**

1. 检查 Neo4j 是否运行：
```bash
# Docker
docker ps | grep neo4j

# 或本地服务
sudo systemctl status neo4j  # Linux
```

2. 检查端口是否被占用：
```bash
netstat -an | grep 7687
```

3. 验证密码是否正确：
```bash
# 确保密码为 123456789s
```

### 问题 3: 模型下载失败

**症状：**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**解决方案：**

项目已内置 SSL 补丁，如果仍有问题：

```bash
# 设置环境变量
set ULTRALYTICS_OFFLINE=true

# 或手动下载模型
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### 问题 4: BERT 模型下载慢

**症状：**
```
下载 bert-base-chinese 模型很慢或失败
```

**解决方案：**

使用国内镜像：
```bash
# 设置 HuggingFace 镜像
set HF_ENDPOINT=https://hf-mirror.com
```

或手动下载模型：
```bash
# 下载模型到本地
git clone https://huggingface.co/bert-base-chinese
```

### 问题 5: Gradio 端口冲突

**症状：**
```
OSError: [Errno 48] Address already in use
```

**解决方案：**

修改 `app.py` 中的端口：
```python
demo.launch(server_name="0.0.0.0", server_port=7861)  # 改为其他端口
```

### 问题 6: 数据集路径错误

**症状：**
```
FileNotFoundError: [Errno 2] No such file or directory: 'datasets/wheat_data'
```

**解决方案：**

1. 检查路径是否正确：
```bash
ls -la datasets/wheat_data
```

2. 修改配置文件：
```yaml
# configs/wheat_disease.yaml
path: /absolute/path/to/datasets/wheat_data  # 使用绝对路径
```

### 问题 7: Windows 路径问题

**症状：**
```
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes
```

**解决方案：**

使用原始字符串或正斜杠：
```python
# 错误
path = "C:\Users\Name\file.txt"

# 正确
path = r"C:\Users\Name\file.txt"
path = "C:/Users/Name/file.txt"
```

---

## 🔍 验证安装

运行完整的系统检查：

```bash
python check_env.py
```

或手动检查：

```python
import torch
import ultralytics
import transformers
import neo4j
import gradio

print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA Available: {torch.cuda.is_available()}")
print(f"✅ Ultralytics: {ultralytics.__version__}")
print(f"✅ Transformers: {transformers.__version__}")
print(f"✅ Neo4j: {neo4j.__version__}")
print(f"✅ Gradio: {gradio.__version__}")

# 测试 Neo4j 连接
driver = neo4j.GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', '123456789s'))
driver.verify_connectivity()
print("✅ Neo4j 连接成功")
driver.close()

print("\n🎉 所有组件安装成功！")
```

---

## 📞 获取帮助

如果遇到其他问题：

1. 查看 [项目文档](README.md)
2. 提交 [Issue](https://github.com/your-repo/WheatAgent/issues)
3. 联系项目维护者

---

<div align="center">

**安装完成后，请阅读 [使用指南](API_USAGE.md) 开始使用 IWDDA！**

</div>
