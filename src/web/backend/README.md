# WheatAgent 后端服务

## 环境要求

- Python >= 3.10
- Node.js >= 18 (前端)
- MySQL >= 8.0
- Redis >= 7.0
- CUDA 11.8/12.1 (GPU 推理环境，可选)

## 依赖安装

### 分层依赖说明

项目采用分层依赖管理，位于 `requirements/` 目录：

| 文件 | 用途 | 适用场景 |
|------|------|---------|
| `base.txt` | Web 后端基础依赖 | 所有环境必装 |
| `ml-gpu.txt` | GPU 推理依赖 | NVIDIA GPU 生产环境 |
| `ml-cpu.txt` | CPU 推理依赖 | 无 GPU / 开发调试 |
| `dev.txt` | 开发工具依赖 | 本地开发 |

### 安装方式

```bash
# 进入后端目录
cd src/web/backend

# === 场景 1: 仅运行 Web API（无 AI 推理）===
pip install -r requirements/base.txt

# === 场景 2: GPU 推理环境（生产推荐）===
# 前置: 已安装 CUDA Toolkit 和 cuDNN
pip install -r requirements/ml-gpu.txt

# === 场景 3: CPU 推理环境（开发/无 GPU）===
# 注意: 推理速度较慢，仅建议用于测试
pip install -r requirements/ml-cpu.txt

# === 场景 4: 完整开发环境（含测试工具）===
pip install -r requirements/dev.txt
```

### 版本锁定策略

- **精确范围**: 使用 `>=x.y.z,<a.b.c` 格式锁定版本范围，避免不兼容升级
- **兼容性保证**: PyTorch 与 torchvision 版本严格配对（2.1.x ↔ 0.16.x/0.17.x）
- **Transformers 锁定**: 限制在 4.36~4.39 范围，避免 API 破坏性变更
- **Ultralytics 锁定**: 固定在 8.0.x 版本，确保 YOLOv8 行为一致

### Conda 环境配置（推荐）

```bash
# 创建 conda 环境
conda create -n wheatagent-py310 python=3.10 -y
conda activate wheatagent-py310

# 安装 PyTorch（根据硬件选择）
# GPU 版本 (CUDA 12.1)
conda install pytorch==2.1.0 torchvision==0.16.0 pytorch-cuda=12.1 -c pytorch -c nvidia -y

# 或 CPU 版本
conda install pytorch==2.1.0 torchvision==0.16.0 cpuonly -c pytorch -y

# 安装剩余依赖
pip install -r requirements/ml-gpu.txt   # 或 ml-cpu.txt
```

## 快速启动

### 方法 1：使用启动脚本（推荐）
```bash
start_server.bat
```

### 方法 2：使用命令行
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方法 3：直接运行 main.py
```bash
python app/main.py
```

## 访问地址

- API 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

## API 端点

### 用户管理
- POST /api/v1/users/register - 用户注册
- POST /api/v1/users/login - 用户登录
- GET /api/v1/users/me - 获取当前用户信息
- GET /api/v1/users/{user_id} - 获取用户信息
- PUT /api/v1/users/{user_id} - 更新用户信息

### 诊断管理
- POST /api/v1/diagnoses/ - 创建诊断记录
- GET /api/v1/diagnoses/ - 获取诊断列表
- GET /api/v1/diagnoses/{diagnosis_id} - 获取诊断详情
- PUT /api/v1/diagnoses/{diagnosis_id} - 更新诊断记录
- DELETE /api/v1/diagnoses/{diagnosis_id} - 删除诊断记录

### 疾病知识
- POST /api/v1/knowledge/ - 创建疾病知识
- GET /api/v1/knowledge/search - 搜索疾病知识
- GET /api/v1/knowledge/categories - 获取疾病分类
- GET /api/v1/knowledge/{disease_id} - 获取疾病详情
- PUT /api/v1/knowledge/{disease_id} - 更新疾病知识
- DELETE /api/v1/knowledge/{disease_id} - 删除疾病知识

### 统计信息
- GET /api/v1/stats/overview - 获取概览统计
- GET /api/v1/stats/diagnoses - 获取诊断统计
- GET /api/v1/stats/users - 获取用户统计

## 配置说明

1. 复制 `.env.example` 为 `.env`
2. 修改配置文件中的数据库、Redis 等连接信息

```bash
cp .env.example .env
```

## 环境变量

- `DATABASE_HOST`: MySQL 主机地址
- `DATABASE_PORT`: MySQL 端口
- `DATABASE_NAME`: 数据库名称
- `DATABASE_USER`: 数据库用户名
- `DATABASE_PASSWORD`: 数据库密码
- `REDIS_HOST`: Redis 主机地址
- `REDIS_PORT`: Redis 端口
- `JWT_SECRET_KEY`: JWT 密钥（生产环境请修改）
- `JWT_EXPIRE_HOURS`: JWT 令牌有效期（小时）
