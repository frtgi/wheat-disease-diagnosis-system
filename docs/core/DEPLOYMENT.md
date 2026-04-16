# 基于多模态融合的小麦病害诊断系统 — 生产部署指南

> **版本**: V12.0 | **日期**: 2026-04-05
>
> 🎯 **目标读者**: DevOps工程师 / 系统管理员 / IT运维人员

---

## 目录

- [环境依赖矩阵](#1-环境依赖矩阵)
- [部署前检查清单](#2-部署前检查清单)
- [Step 1: 环境准备](#step-1-环境准备)
- [Step 2: 数据库初始化](#step-2-数据库初始化)
- [Step 3: AI 模型下载](#step-3-ai-模型下载)
- [Step 4: 配置文件](#step-4-配置文件)
- [Step 5: 服务启动](#step-5-服务启动)
- [Step 6: 健康验证](#step-6-健康验证)
- [生产环境优化](#生产环境优化)
- [故障排查手册](#故障排查手册)
- [备份与恢复](#备份与恢复)

---

## 1. 环境依赖矩阵

### 必需组件

| 组件 | 最低版本 | 推荐版本 | 用途 | 验证命令 |
|------|---------|---------|------|----------|
| **Python** | 3.10 | 3.10.12 | 后端运行时 | `python --version` |
| **MySQL** | 8.0 | 8.0.36 | 主数据库 | `mysql --version` |
| **Redis** | 7.0 | 7.2.4 | 缓存/会话/任务队列 | `redis-server --version` |
| **Node.js** | 18 | 20 LTS | 前端构建 | `node --version` |
| **npm** | 9 | 10 | 包管理 | `npm --version` |

### Python 核心依赖（来自 requirements.txt）

| 包名 | 最低版本 | 用途 |
|------|---------|------|
| fastapi | >=0.109.0 | Web 框架 |
| uvicorn | >=0.27.0 | ASGI 服务器 |
| sqlalchemy | >=2.0.0 | ORM 框架 |
| pymysql | >=1.1.0 | MySQL 异步驱动 |
| redis | >=5.0.0 | Redis 客户端 |
| python-jose[cryptography] | >=3.3.0 | JWT 认证 |
| passlib[bcrypt] | >=1.7.4 | 密码哈希 |
| python-multipart | >=0.0.6 | 文件上传支持 |
| pydantic[email] | >=2.5.0 | 数据验证 |
| ~~celery~~ | ~~>=5.3.0~~ | ~~已弃用，使用SSE流式响应~~ |
| ~~minio~~ | ~~>=7.1.0~~ | ~~已弃用，使用本地文件存储~~ |
| python-dotenv | >=1.0.0 | 环境变量管理 |
| slowapi | >=0.1.9 | API 限流 |
| psutil | >=5.9.0 | 系统监控 |

### 可选组件（影响功能可用性）

| 组件 | 最低版本 | 用途 | 不安装的影响 |
|------|---------|------|-------------|
| **Neo4j** | 5.x | 知识图谱 (GraphRAG) | 知识增强功能不可用，基础诊断正常 |
| **NVIDIA Driver** | 525+ | GPU 加速推理 | 仅 CPU 模式，速度较慢 (~3x 慢) |
| **CUDA Toolkit** | 12.1+ | PyTorch GPU 后端 | 自动降级为 CPU 推理 |
| **cuDNN** | 8.x | GPU 深度加速库 | 性能下降约 20% |
| **MinIO** | - | 已弃用 | 系统使用本地文件存储 |
| **Docker** | 24+ | 容器化部署 | 仅原生部署 |
| **Kubernetes** | 1.28+ | 容器编排 (生产环境) | 仅 Docker Compose 部署 |

### AI 模型依赖

| 模型 | 大小 | 用途 | 下载方式 |
|------|------|------|---------|
| **PyTorch (CUDA)** | ~2.5GB | GPU 推理后端 | pip install torch --index-url https://download.pytorch.org/whl/cu121 |
| **bitsandbytes** | ~100MB | INT4 量化支持 | pip install bitsandbytes>=0.41.0 |
| **YOLOv8s** | ~50MB | 病害目标检测 (16类) | Ultralytics Hub 自动下载或手动预下载 |
| **Qwen3-VL-2B-Instruct** | ~2.6GB (INT4) / ~8GB (FP16) | 多模态理解 | HuggingFace / ModelScope |

### 硬件要求

| 场景 | CPU | 内存 | GPU | 存储 | 适用 |
|------|-----|------|-----|------|------|
| **开发测试** | 4核 | 8 GB | 无 | 20 GB | 本地开发 |
| **小型生产** | 8核 | 16 GB | GTX 1660+ (6GB) | 50 GB | 小型农场/合作社 |
| **标准生产** | 16核 | 32 GB | RTX 3090/4090 (24GB) | 100 GB | 县级农技中心 |
| **大规模** | 32核+ | 64 GB+ | A100 (80GB) | 500 GB+ | 省级平台 |

### 显存需求参考

| 配置模式 | 显存占用 | 推理速度 | 适用场景 |
|---------|---------|---------|---------|
| BF16（无量化） | ~9.8GB | 快 | 高性能 GPU (RTX 3090+) |
| INT8 量化 | ~5.5GB | 中等 | 中端 GPU (RTX 3060) |
| INT4 量化 | ~2.6GB | 较慢 | 入门 GPU (GTX 1660) |
| CPU 模式 | 系统内存 | 最慢 | 无 GPU 环境 |

---

## 2. 部署前检查清单

请逐项确认以下条件满足后再开始部署：

### 2.1 系统环境 ☐
- [ ] 操作系统: Windows Server 2019+/Ubuntu 22.04+/CentOS 8+
- [ ] 磁盘剩余空间 > 20GB（不含模型文件）
- [ ] 已配置网络（固定 IP 或域名解析）
- [ ] 已开放端口: 8000(FastAPI), 3306(MySQL), 6379(Redis), 7474(Neo4j HTTP), 7687(Neo4j Bolt)

### 2.2 软件依赖 ☐
- [ ] Python 3.10+ 已安装 (`python --version`)
- [ ] pip 已更新至最新 (`pip install --upgrade pip`)
- [ ] Conda 已安装 (`conda --version`) - 用于环境隔离
- [ ] MySQL 8.0+ 服务运行中 (`systemctl status mysql` 或 Windows 服务管理器)
- [ ] Redis 7.0+ 服务运行中 (`redis-cli ping` 返回 PONG)
- [ ] Node.js 18+ 已安装 (`node --version`)
- [ ] npm 9+ 已安装 (`npm --version`)
- [ ] Git 已安装 (`git --version`)

### 2.3 数据库准备 ☐
- [ ] MySQL 已创建数据库: `CREATE DATABASE wheat_agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
- [ ] 已创建专用数据库用户（不建议使用 root）
- [ ] 用户拥有 SELECT/INSERT/UPDATE/DELETE/CREATE/INDEX/ALTER 权限
- [ ] MySQL 字符集配置为 utf8mb4（支持中文和特殊字符）

### 2.4 可选服务准备 ☐
- [ ] Neo4j 5.x 服务运行中（如需知识图谱功能）
- [ ] ~~MinIO 服务运行中~~（已弃用，系统使用本地文件存储）
- [ ] NVIDIA Driver + CUDA Toolkit + cuDNN 已安装（如需 GPU 加速）

### 2.5 AI 模型准备（可选，首次启动时可跳过）☐
- [ ] YOLOv8 权重文件已下载（~50MB，首次运行时自动下载也可）
- [ ] 如使用 GPU: NVIDIA 驱动 525+ + CUDA 12.1+ + cuDNN 8.x 已安装
- [ ] 如使用 Qwen: 模型文件已下载（~2.6GB INT4 或 ~8GB FP16，懒加载模式可延后）
- [ ] PyTorch CUDA 版本已安装 (`python -c "import torch; print(torch.cuda.is_available())"` 返回 True)

---

## Step 1: 环境准备

### 1.1 创建 Conda 环境

```bash
# 创建专用环境
conda create -n wheatagent-py310 python=3.10 -y
conda activate wheatagent-py310

# 验证
python --version  # 应显示 Python 3.10.x
```

### 1.2 安装后端依赖

```bash
cd WheatAgent/src/web/backend

# 安装基础依赖
pip install -r requirements.txt

# 如需 GPU 支持（推荐生产环境）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装 INT4 量化支持（减少显存占用）
pip install bitsandbytes>=0.41.0

# 验证关键依赖
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
```

### 1.3 安装前端依赖

```bash
cd WheatAgent/src/web/frontend

# 安装依赖（国内用户建议使用镜像）
npm install
# 或使用淘宝镜像: npm install --registry=https://registry.npmmirror.com

# 验证
npm run build  # 测试构建是否成功
```

### 1.4 目录结构确认

确保以下目录存在并有正确的权限：

```
WheatAgent/
├── src/web/backend/          # 后端代码
│   ├── app/                  # 应用主目录
│   ├── models/               # AI 模型文件
│   ├── uploads/              # 上传文件存储
│   ├── logs/                 # 日志文件
│   └── requirements.txt      # Python 依赖
├── src/web/frontend/         # 前端代码
│   ├── dist/                 # 构建产物
│   └── package.json          # Node.js 依赖
└── configs/                  # 配置文件
```

---

## Step 2: 数据库初始化

### 2.1 MySQL 初始化

```bash
# 连接 MySQL
mysql -u root -p

# 创建数据库（注意字符集必须为 utf8mb4）
CREATE DATABASE wheat_agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建专用用户（请替换密码为强密码）
CREATE USER 'wheatagent'@'%' IDENTIFIED BY 'YourStrongPasswordHere!2026';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON wheat_agent_db.* TO 'wheatagent'@'%';
FLUSH PRIVILEGES;

# 验证连接
mysql -u wheatagent -p -e "SELECT 1" wheat_agent_db
```

### 2.2 自动建表

系统首次启动时会通过 SQLAlchemy + Alembic 自动创建所有 **12 张表**：

| 表名 | 用途 | 说明 |
|------|------|------|
| users | 用户信息 | 3角色 (farmer/technician/admin)，软删除 |
| diagnoses | 诊断记录 | 主表，关联用户/疾病/图像 |
| diagnosis_confidences | 多候选置信度 | 一对多关系，支持多疾病候选 |
| diseases | 病害知识库 | 5分类 (fungal/bacterial/viral/pest/nutritional) |
| knowledge_graph | 知识图谱三元组 | GraphRAG 数据源 |
| image_metadata | 图像元数据 | SHA256去重，本地文件存储 |
| audit_logs | 审计日志 | 14种操作类型追踪 |
| password_reset_tokens | 密码重置令牌 | 安全认证增强 |
| refresh_tokens | 刷新令牌 | JWT 双令牌机制 |
| login_attempts | 登录尝试记录 | 防暴力破解 |
| user_sessions | 会话管理 | 多设备会话控制 |

**无需手动执行 SQL**，启动时自动建表。

### 2.3 Neo4j 初始化（可选）

```bash
# 启动 Neo4j 后访问 http://localhost:7474
# 默认账号: neo4j / 密码: neo4j（首次登录需修改）

# 导入知识图谱数据（详见 GRAPH_RAG_SPEC.md）
# 当前规模: 106实体, 178三元组
# 实体类型: disease/symptom/pest/treatment/growth_stage
```

---

## Step 3: AI 模型下载

### 3.1 YOLOv8 视觉模型

**模型用途**: 小麦病害目标检测（16类病害/虫害/健康）

```bash
# 方式 A: 首次推理时自动下载（推荐新手使用）
# 系统会在首次调用 YOLO 时从 Ultralytics Hub 下载 yolov8s.pt (~50MB)

# 方式 B: 手动预下载（推荐生产环境）
pip install ultralytics
yolo detect predict model=yolov8s.pt source=test.jpg

# 方式 C: 使用项目内置的微调模型（最佳精度）
# 模型路径: models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt
# 在 .env 中配置: YOLO_MODEL_PATH=models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt
```

**支持的检测类别**:
```
Yellow Rust(条锈病), Brown Rust(叶锈病), Black Rust(秆锈病),
Mildew(白粉病), Fusarium Head Blight(赤霉病),
Septoria(壳针孢叶斑病), Tan spot(褐斑病),
Leaf Blight(叶枯病), Blast(稻瘟病),
Aphid(蚜虫), Mite(螨虫), Stem fly(茎蝇),
Common Root Rot(根腐病), Smut(黑粉病),
Healthy(健康)
```

### 3.2 Qwen3-VL 多模态模型

**模型用途**: 图文联合理解、推理链生成、病害语义分析

```bash
# 方式一：HuggingFace 自动下载（国际网络）
# 首次请求时自动下载到 ~/.cache/huggingface/hub/
# 约 2.6GB (INT4) 或 ~8GB (FP16)

# 方式二：ModelScope 下载（国内推荐）
pip install modelscope
python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen3-VL-2B-Instruct', cache_dir='./models')
"

# 方式三：Git LFS 下载
cd models
git lfs install
git clone https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct
```

**模型特性**:
- 支持懒加载（Lazy Loading）：服务启动时不占用显存
- 首次诊断请求时按需加载
- 支持 INT4/BF16/FP16 三种精度模式
- 可通过 `/api/v1/diagnosis/admin/ai/preload` 手动预热

### 3.3 PyTorch GPU 环境（可选但强烈推荐）

```bash
# 验证 CUDA 可用性
python -c "
import torch
print(f'PyTorch 版本: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA 版本: {torch.version.cuda}')
    print(f'GPU 数量: {torch.cuda.device_count()}')
    print(f'GPU 名称: {torch.cuda.get_device_name(0)}')
    print(f'显存总量: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')
"
```

**预期输出示例**:
```
PyTorch 版本: 2.2.0
CUDA 可用: True
CUDA 版本: 12.1
GPU 数量: 1
GPU 名称: NVIDIA GeForce RTX 4090
显存总量: 24.0 GB
```

---

## Step 4: 配置文件

### 4.1 创建 .env 文件

在 `src/web/backend/` 下创建 `.env` 文件（**生产环境务必修改所有密码和密钥**）：

```bash
# ==================== 应用基础配置 ====================
APP_NAME=基于多模态融合的小麦病害诊断系统
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO
JSON_LOG_FORMAT=True

# ==================== 数据库配置 ====================
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=wheatagent
DATABASE_PASSWORD=YourStrongPasswordHere!2026
DATABASE_NAME=wheat_agent_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# ==================== Redis 配置 ====================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ==================== JWT 配置（安全关键）====================
# ⚠️ 生产环境必须使用随机生成的 32+ 字符密钥
# 生成命令: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars!!!
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ==================== CORS 配置 ====================
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","https://your-domain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=600

# ==================== AI 模型配置 ====================
QWEN_MODEL_PATH=/path/to/Qwen3-VL-2B-Instruct  # 留空则使用默认 HuggingFace 路径
YOLO_MODEL_PATH=yolov8s.pt                       # 留空则自动下载或使用默认路径

# ==================== 融合诊断权重配置 ====================
FUSION_DEGRADATION_FACTOR=0.9
FUSION_VISUAL_WEIGHT=0.4
FUSION_TEXTUAL_WEIGHT=0.35
FUSION_KNOWLEDGE_WEIGHT=0.25

# ==================== 缓存配置 ====================
INFERENCE_CACHE_TTL=86400
INFERENCE_CACHE_ENABLED=true
INFERENCE_CACHE_ENABLE_SIMILAR_SEARCH=true
INFERENCE_CACHE_SIMILARITY_THRESHOLD=5

# ==================== 限流配置 ====================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_DIAGNOSIS=10/minute
RATE_LIMIT_UPLOAD=20/minute

# ==================== SSE 流式传输配置 ====================
SSE_TIMEOUT_SECONDS=120
SSE_HEARTBEAT_INTERVAL=15
SSE_BACKPRESSURE_QUEUE_SIZE=100

# ==================== GPU 并发控制配置 ====================
MAX_CONCURRENT_DIAGNOSIS=3
MAX_DIAGNOSIS_QUEUE_SIZE=10
DIAGNOSIS_QUEUE_TIMEOUT=300
GPU_MEMORY_THRESHOLD=0.90

# ==================== Neo4j 配置（可选）====================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30

# ==================== MinIO 对象存储配置（已弃用，使用本地文件存储）====================
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
# MINIO_BUCKET_NAME=wheatagent

# ==================== Celery 任务队列配置（已弃用，使用SSE流式响应）====================
# CELERY_BROKER_URL=redis://localhost:6379/1
# CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 4.2 前端环境变量配置

在 `src/web/frontend/` 下创建 `.env.production`:

```env
# API 基础地址（生产环境改为实际域名或 IP）
VITE_API_BASE_URL=http://your-server-ip:8000

# 应用标题
VITE_APP_TITLE=WheatAgent 小麦病害智能诊断系统
```

修改 `vite.config.ts` 配置（如需要代理）:

```typescript
export default defineConfig({
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 4.3 敏感信息安全

⚠️ **生产环境务必执行以下安全措施**:

1. **JWT_SECRET_KEY**
   - 使用随机生成的 32+ 字符密钥
   - 生成命令: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - 定期轮换（建议每 90 天）

2. **数据库密码**
   - 使用强密码（大小写字母+数字+特殊符号，长度≥12位）
   - 不使用 root 用户连接应用数据库
   - 限制用户 IP 白名单（如可能）

3. **文件权限** (Linux)
   ```bash
   chmod 600 .env                    # 仅所有者可读写
   chown wheatagent:wheatagent .env  # 修改所有者
   ```

4. **版本控制**
   ```bash
   # 确保 .gitignore 包含以下内容:
   echo ".env" >> .gitignore
   echo "*.log" >> .gitignore
   echo "__pycache__/" >> .gitignore
   echo "uploads/" >> .gitignore
   ```

---

## Step 5: 服务启动

### 5.1 开发模式

适用于本地开发和调试。

```bash
# 终端 1: 启动后端
cd WheatAgent/src/web/backend
conda activate wheatagent-py310
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2: 启动前端（另开窗口）
cd WheatAgent/src/web/frontend
npm run dev
```

**访问地址**:
- 前端界面: http://localhost:5173
- API 文档 (Swagger UI): http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/v1/health
- Prometheus 指标: http://localhost:8000/metrics

### 5.2 生产模式（Gunicorn + Uvicorn）

适用于生产环境部署。

```bash
cd WheatAgent/src/web/backend
conda activate wheatagent-py310

# 使用 Gunicorn 管理 Uvicorn Worker 进程
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile -
```

**参数说明**:
- `-w 4`: Worker 进程数（建议 CPU 核数 × 2 + 1）
- `-k uvicorn.workers.UvicornWorker`: 使用 Uvicorn Worker 类
- `--timeout 120`: SSE 长连接超时时间（秒）
- `--keepalive 5`: HTTP Keep-Alive 超时
- `--access-logfile -`: 访问日志输出到标准输出
- `--error-logfile -`: 错误日志输出到标准输出

### 5.3 Docker Compose 部署（可选）

适用于容器化部署场景。

```bash
# 进入部署目录
cd deploy

# 启动所有服务（含 MySQL/Redis/Neo4j）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f api

# 仅重启某个服务
docker-compose restart api

# 停止所有服务
docker-compose down

# 停止并删除数据卷（⚠️ 会丢失数据）
docker-compose down -v
```

**Docker Compose 服务端口映射**:

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| Web 前端 (Nginx) | 80 | 80 | 静态文件服务 |
| API 后端 | 8000 | 8000 | FastAPI 服务 |
| MySQL | 3306 | 3306 | 业务数据库 |
| Redis | 6379 | 6379 | 缓存/会话 |
| Neo4j HTTP | 7474 | 7474 | 图数据库 Web UI |
| Neo4j Bolt | 7687 | 7687 | 图数据库连接 |
| ~~MinIO Console~~ | ~~9001~~ | ~~9001~~ | ~~已弃用，使用本地文件存储~~ |

### 5.4 前端生产构建

```bash
cd WheatAgent/src/web/frontend

# 构建生产版本
npm run build

# 构建产物位于 dist/ 目录
# 将 dist/ 目录部署到 Nginx 的静态文件目录
ls -la dist/

# 预期输出:
# index.html
# assets/
#   index-[hash].js
#   index-[hash].css
```

---

## Step 6: 健康验证

部署完成后，依次检查以下端点以确保所有组件正常运行。

### 6.1 基础健康检查

```bash
# 1. 应用基本状态
curl http://localhost:8000/api/v1/health
# 预期返回:
# {"status":"healthy","timestamp":"...","version":"1.0.0",...}

# 2. 数据库连接测试
curl http://localhost:8000/api/v1/health/database
# 预期返回:
# {"database":"connected","pool_size":10,...}

# 3. Redis 连接测试
curl http://localhost:8000/api/v1/health/redis
# 预期返回:
# {"redis":"connected"}
```

### 6.2 AI 服务状态检查

```bash
# 4. AI 模型状态（包含 YOLO/Qwen 加载状态）
curl http://localhost:8000/api/v1/diagnosis/health/ai
# 预期返回:
# {
#   "yolo": {"status": "ready", "model": "yolov8s.pt", ...},
#   "qwen": {"status": "lazy", "model": null, ...},  # lazy 表示懒加载
#   ...
# }

# 5. Prometheus 监控指标
curl http://localhost:8000/metrics
# 预期返回大量 metrics 格式的指标数据
```

### 6.3 功能验证

```bash
# 6. API 文档可访问性
curl -I http://localhost:8000/docs
# 预期: HTTP/1.1 200 OK

# 7. 静态文件上传目录
curl -I http://localhost:8000/uploads/
# 预期: HTTP/1.1 200 OK 或 404（空目录）
```

### 6.4 健康验证清单

- [ ] 基础健康检查返回 `{"status":"healthy"}`
- [ ] 数据库连接正常（`database: connected`）
- [ ] Redis 连接正常（`redis: connected`）
- [ ] YOLO 模型状态为 `ready` 或 `lazy`（均可接受）
- [ ] Qwen 模型状态为 `lazy`（懒加载）或 `ready`（预加载）
- [ ] API 文档页面可正常打开 (http://localhost:8000/docs)
- [ ] 前端页面可正常访问（如已部署前端）
- [ ] 无明显错误日志输出

**全部检查通过后，部署成功！** 🎉

---

## 生产环境优化

### Gunicorn 配置调优

创建 `gunicorn.conf.py` 配置文件（位于 `src/web/backend/`）:

```python
"""Gunicorn 生产环境配置文件"""

import multiprocessing
import os

# 服务器绑定地址
bind = "0.0.0.0:8000"

# Worker 进程数（CPU 核数 × 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# Worker 类（Uvicorn 异步 Worker）
worker_class = "uvicorn.workers.UvicornWorker"

# Worker 数量（每个 Worker 内部的线程数）
threads = 2

# 超时设置（SSE 长连接需要较长超时）
timeout = 120
graceful_timeout = 30
keepalive = 5

# 日志配置
accesslog = "/var/log/wheatagent/access.log"
errorlog = "/var/log/wheatagent/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 最大请求数（达到后重启 Worker，防止内存泄漏）
max_requests = 10000
max_requests_jitter = 1000

# 预加载应用（节省内存，但热更新失效）
preload_app = False

# 安全设置
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
```

**使用自定义配置启动**:

```bash
gunicorn app.main:app -c gunicorn.conf.py
```

### Nginx 反向代理配置

创建 Nginx 配置文件 `/etc/nginx/sites-available/wheatagent`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 前端静态文件
    location / {
        root /opt/wheatagent/frontend/dist;
        try_files $uri $uri/ /index.html;

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 长连接支持（关键配置）
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        # WebSocket 升级支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 大文件上传支持
        client_max_body_size 20M;
    }

    # 上传文件静态服务
    location /uploads/ {
        alias /opt/wheatagent/backend/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # 健康检查端点（无需认证）
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }

    # Prometheus 指标端点（限制内网访问）
    location /metrics {
        proxy_pass http://127.0.0.1:8000;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }

    # 错误页面
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

**启用配置**:

```bash
# 创建软链接到 sites-enabled
sudo ln -s /etc/nginx/sites-available/wheatagent /etc/nginx/sites-enabled/

# 测试配置语法
sudo nginx -t

# 重载 Nginx 使配置生效
sudo systemctl reload nginx

# 或重启
sudo systemctl restart nginx
```

### HTTPS 配置（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# 自动获取并配置 SSL 证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期（通常已自动配置）
sudo certbot renew --dry-run
```

### systemd 系统服务配置

创建 `/etc/systemd/system/wheatagent.service`:

```ini
[Unit]
Description=WheatAgent AI Diagnosis Service
Documentation=https://github.com/your-repo/WheatAgent
After=network.target mysql.service redis.service
Requires=mysql.service redis.service

[Service]
Type=simple
User=wheatagent
Group=wheatagent
WorkingDirectory=/opt/wheatagent/backend

# Conda 环境路径
Environment="PATH=/opt/conda/envs/wheatagent-py310/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONDONTWRITEBYTECODE=1"

# 启动命令（使用 Gunicorn）
ExecStart=/opt/conda/envs/wheatagent-py310/bin/gunicorn app.main:app \
  -c /opt/wheatagent/backend/gunicorn.conf.py

# 重启策略
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

# 资源限制
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/wheatagent/backend/logs
ReadWritePaths=/opt/wheatagent/backend/uploads

# 日志输出
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wheatagent

[Install]
WantedBy=multi-user.target
```

**管理系统服务**:

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable wheatagent

# 启动服务
sudo systemctl start wheatagent

# 查看服务状态
sudo systemctl status wheatagent

# 查看实时日志
sudo journalctl -u wheatagent -f

# 停止服务
sudo systemctl stop wheatagent

# 重启服务
sudo systemctl restart wheatagent
```

### 日志轮转配置 (Logrotate)

创建 `/etc/logrotate.d/wheatagent`:

```
/var/log/wheatagent/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 wheatagent wheatagent
    postrotate
        systemctl reload wheatagent > /dev/null 2>&1 || true
    endscript
}
```

---

## 故障排查手册

### 问题 1: 服务启动失败 — ModuleNotFoundError

**症状**: `ModuleNotFoundError: No module named 'xxx'`

**原因**: Python 依赖未安装完整或使用了错误的 Conda 环境

**解决方案**:
```bash
# 1. 确认当前环境
conda info --envs
conda activate wheatagent-py310

# 2. 重新安装依赖
cd WheatAgent/src/web/backend
pip install -r requirements.txt

# 3. 如果缺少 PyTorch GPU 支持
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 验证关键模块
python -c "import fastapi, uvicorn, sqlalchemy, redis"
```

**预防措施**: 在 `gunicorn.conf.py` 中设置 `preload_app = True` 可提前发现缺失依赖。

---

### 问题 2: 数据库连接失败 — Connection refused

**症状**: `Can't connect to MySQL server on 'localhost'` 或 `Connection refused`

**原因**: MySQL 未启动或 `.env` 中数据库配置错误

**排查步骤**:
```bash
# 1. 检查 MySQL 服务状态
# Linux
sudo systemctl status mysql
# Windows (PowerShell)
Get-Service -Name '*mysql*'

# 2. 检查端口监听
netstat -tlnp | grep 3306  # Linux
netstat -ano | findstr :3306  # Windows

# 3. 测试数据库连通性
mysql -u wheatagent -p -h 127.0.0.1 -P 3306 -e "SELECT 1"

# 4. 检查 .env 配置
grep DATABASE_HOST .env
grep DATABASE_PORT .env
grep DATABASE_USER .env
```

**解决方案**:
```bash
# 启动 MySQL 服务
sudo systemctl start mysql  # Linux
net start MySQL80           # Windows

# 检查防火墙
sudo ufw allow 3306         # Linux
# Windows 防火墙需在高级设置中添加入站规则
```

---

### 问题 3: Redis 连接失败

**症状**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**原因**: Redis 服务未启动或配置错误

**解决方案**:
```bash
# 1. 启动 Redis
sudo systemctl start redis     # Linux
redis-server &                 # 手动启动

# 2. 验证连接
redis-cli ping
# 预期返回: PONG

# 3. 检查 Redis 配置
grep REDIS_HOST .env
grep REDIS_PORT .env
```

**Redis 持久化建议**:
```bash
# 编辑 redis.conf，确保启用 RDB 持久化
save 900 1      # 900 秒内至少 1 个 key 变更则快照
save 300 10     # 300 秒内至少 10 个 key 变更
save 60 10000   # 60 秒内至少 10000 个 key 变更
```

---

### 问题 4: AI 模型加载慢或失败

**症状**: 首次诊断请求超时或报错 `Model download failed`

**原因**: 网络不通（无法访问 HuggingFace）/ GPU 驱动问题 / 磁盘空间不足

**解决方案**:

**情况 A: 网络问题（中国大陆常见）**
```bash
# 1. 测试网络连通性
ping huggingface.co
# 如果超时，使用镜像源

# 2. 设置 HuggingFace 镜像（临时）
export HF_ENDPOINT=https://hf-mirror.com

# 3. 或永久设置（写入 .env）
echo "HF_ENDPOINT=https://hf-mirror.com" >> ~/.bashrc

# 4. 使用 ModelScope 下载（国内推荐）
pip install modelscope
python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen3-VL-2B-Instruct', cache_dir='./models')
"
```

**情况 B: GPU 驱动问题**
```bash
# 1. 检查 NVIDIA 驱动
nvidia-smi
# 如果显示 "NVIDIA-SMI has failed"，说明驱动未正确安装

# 2. 检查 CUDA 版本
nvcc --version
# 应显示 CUDA 12.1+

# 3. 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"
# 如果返回 False，重新安装 PyTorch GPU 版本
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**情况 C: 磁盘空间不足**
```bash
# 检查磁盘空间
df -h

# 清理缓存（如有必要）
rm -rf ~/.cache/huggingface/hub/
rm -rf ~/.cache/pip/
```

**降级方案（CPU 模式）**:
如果 GPU 无法使用，系统会自动降级为 CPU 推理：
```yaml
# configs/wheat_agent.yaml（如存在）
vision:
  device: "cpu"
```
CPU 模式速度较慢（约 3x），但功能完全可用。

---

### 问题 5: 诊断请求返回 503 Service Unavailable

**症状**: POST `/api/v1/diagnosis/fusion` 返回 503 或超时

**原因**: GPU 显存不足 / 并发已满 / 模型未加载完成

**排查步骤**:
```bash
# 1. 检查 GPU 状态
nvidia-smi
# 关注: GPU利用率、显存使用率、温度

# 2. 检查并发限制
grep MAX_CONCURRENT_DIAGNOSIS .env
# 默认值: 3（同时最多 3 个诊断任务）

# 3. 检查模型加载状态
curl http://localhost:8000/api/v1/diagnosis/health/ai
# 查看 yolo 和 qwen 的 status 字段

# 4. 检查诊断队列
curl http://localhost:8000/api/v1/diagnosis/cache/stats
```

**解决方案**:

**方案 A: 预热模型（减少首次请求延迟）**
```bash
# 管理员接口预热 AI 模型
curl -X POST http://localhost:8000/api/v1/diagnosis/admin/ai/preload \
  -H "Authorization: Bearer <admin_token>"
```

**方案 B: 调整并发限制**
```bash
# 编辑 .env
MAX_CONCURRENT_DIAGNOSIS=5  # 增加到 5（需要更多显存）
DIAGNOSIS_QUEUE_TIMEOUT=300  # 增加队列超时时间
```

**方案 C: 降低显存使用**
```bash
# 启用 INT4 量化（减少 ~70% 显存）
# 在 qwen_config.py 或环境变量中设置
export QWEN_LOAD_IN_4BIT=true
```

---

### 问题 6: SSE 流断连或无响应

**症状**: 前端进度条卡住、长时间无更新、浏览器控制台显示 EventSource error

**原因**: Nginx 代理缓冲了 SSE 事件 / 超时设置过短 / 网络中断

**解决方案**:

**步骤 1: 检查 Nginx 配置**
```nginx
# 确保在 /api/ location 块中有以下配置:
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    
    # 关键: 禁用缓冲
    proxy_buffering off;
    proxy_cache off;
    
    # 增加超时时间
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    
    # 支持 HTTP/1.1（SSE 需要）
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

**步骤 2: 检查后端 SSE 配置**
```bash
# 检查 .env 中的 SSE 配置
grep SSE_TIMEOUT_SECONDS .env       # 默认 120 秒
grep SSE_HEARTBEAT_INTERVAL .env    # 默认 15 秒（心跳保活）

# 如需延长超时
SSE_TIMEOUT_SECONDS=300
```

**步骤 3: 检查浏览器兼容性**
- 现代浏览器均支持 EventSource API
- 如遇 IE11 兼容问题，考虑使用 polyfill 或改用 WebSocket

**调试技巧**:
```bash
# 直接测试 SSE 端点（绕过前端）
curl -N http://localhost:8000/api/v1/diagnosis/fusion/stream?image_url=test.jpg

# 预期看到持续的事件流:
# data: {"type":"progress","data":{"percent":10,...}}
# data: {"type":"heartbeat",...}
# data: {"type":"complete",...}
```

---

### 问题 7: 上传图片报错 413 Request Entity Too Large

**症状**: 上传图片时返回 `413 Request Entity Too Large`

**原因**: Nginx 或 FastAPI 默认限制了请求体大小

**解决方案**:

**Nginx 层面**:
```nginx
# 在 http/server/location 块中添加:
client_max_body_size 20M;  # 允许最大 20MB 文件上传
```

**FastAPI/Uvicorn 层面**:
```python
# 在 main.py 中（已有默认配置，但可调整）
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

# 或通过中间件设置
```

**验证修复**:
```bash
# 测试 Nginx 配置
sudo nginx -t
sudo systemctl reload nginx

# 测试大文件上传
curl -X POST http://localhost:8000/api/v1/upload/image \
  -F "file=@large_image.jpg" \
  -H "Authorization: Bearer <token>"
```

---

### 问题 8: 前端页面空白或白屏

**症状**: 浏览器访问前端 URL 显示空白页，控制台有错误

**原因**: API 地址配置错误 / CORS 跨域问题 / 静态资源加载失败

**排查步骤**:

**步骤 1: 检查浏览器控制台**
- 按 F12 打开开发者工具
- 查看 Console 标签页的错误信息
- 查看 Network 标签页是否有红色失败的请求

**步骤 2: 检查前端环境变量**
```bash
# 检查 .env.production
cat src/web/frontend/.env.production | grep VITE_API_BASE_URL
# 确保 URL 正确且可访问
```

**步骤 3: 检查 CORS 配置**
```bash
# 检查后端 .env
grep CORS_ORIGINS .env
# 确保包含前端域名，例如:
CORS_ORIGINS=["http://localhost:5173","http://your-domain.com"]
```

**步骤 4: 检查 Nginx 静态文件配置**
```bash
# 确认 dist/ 目录已正确部署
ls -la /opt/wheatagent/frontend/dist/index.html

# 测试静态文件访问
curl -I http://your-domain.com/
# 预期: HTTP/1.1 200 OK
```

**步骤 5: 检查 Vue Router 模式**
```javascript
// vite.config.ts 或 router/index.ts
// 如果使用 history 模式，确保 Nginx 配置了 try_files
// 如果使用 hash 模式，无需额外配置
```

---

### 问题 9: Token 过期频繁或登录状态丢失

**症状**: 用户操作过程中突然被踢出登录，提示 Token 过期

**原因**: Access Token 默认 30 分钟过期 / Refresh Token 失效 / 时区不同步

**解决方案**:

**方案 A: 检查 Token 有效期配置**
```bash
# 检查 .env
grep JWT_EXPIRE_HOURS .env
# 默认值: 24（小时）
```

**方案 B: 实现 Token 自动刷新**
前端应实现 Refresh Token 机制：
```typescript
// Axios 拦截器示例
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // 使用 Refresh Token 获取新的 Access Token
      const newToken = await refreshToken();
      // 重试原请求
      error.config.headers.Authorization = `Bearer ${newToken}`;
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);
```

**方案 C: 检查服务器时间同步**
```bash
# 确保服务器时间准确（JWT 依赖时间戳）
timedatectl status
# 如果不准确，启用 NTP 同步
sudo timedatectl set-ntp true
```

**方案 D: 检查 Token 黑名单**
```bash
# 如果用户频繁掉线，检查是否有逻辑错误导致 Token 被加入黑名单
# 查看审计日志
curl http://localhost:8000/api/v1/logs?action=logout \
  -H "Authorization: Bearer <admin_token>"
```

---

### 问题 10: 日志文件过大导致磁盘空间不足

**症状**: `/var/log` 或 `logs/` 目录占用大量磁盘空间

**原因**: 未配置日志轮转 / 日志级别设置为 DEBUG

**解决方案**:

**步骤 1: 配置日志轮转（Logrotate）**

参见上文「日志轮转配置」章节。

**步骤 2: 调整日志级别**
```bash
# 生产环境不要使用 DEBUG 级别
# 编辑 .env
LOG_LEVEL=INFO  # 或 WARNING（仅记录警告和错误）
JSON_LOG_FORMAT=True  # 结构化日志便于分析
```

**步骤 3: 清理旧日志**
```bash
# 查看日志目录大小
du -sh /var/log/wheatagent/
du -sh logs/

# 手动清理旧日志（保留最近 7 天）
find /var/log/wheatagent/ -name "*.log" -mtime +7 -delete
find logs/ -name "*.log" -mtime +7 -delete
```

**步骤 4: 使用结构化日志分析工具**
```bash
# 安装 jq 用于 JSON 日志查询
sudo apt-get install jq -y

# 查询最近的错误日志
cat /var/log/wheatagent/error.log | jq 'select(.levelname=="ERROR")' | tail -20

# 统计错误类型
cat /var/log/wheatagent/error.log | jq -r '.message' | sort | uniq -c | sort -rn | head -10
```

---

### 问题 11: Conda 环境问题 — GPU 识别失败

**症状**: 模型加载失败，`torch.cuda.is_available()` 返回 False，显存仅 0.3GB

**原因**: 使用了错误的 Python 环境（base 环境 Python 3.13 + CPU PyTorch）

**解决方案**:
```bash
# 1. 列出所有 Conda 环境
conda info --envs

# 2. 激活正确的环境
conda activate wheatagent-py310

# 3. 验证 Python 版本
python --version
# 必须是 Python 3.10.x

# 4. 验证 PyTorch CUDA
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
print(f'GPU count: {torch.cuda.device_count()}')
"

# 5. 如果仍然不可用，重新安装 PyTorch GPU 版本
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**预防措施**:
- 在 systemd 服务文件中明确指定 Conda 环境路径
- 在 shell profile 中添加 `conda activate wheatagent-py310`
- 不要在 base 环境中安装 GPU 相关包

---

### 问题 12: 权限问题 — 文件读写错误

**症状**: `PermissionError: [Errno 13] Permission denied` 或日志无法写入

**原因**: 文件/目录权限不正确，运行用户无写权限

**解决方案**:

**Linux 系统**:
```bash
# 1. 创建专用用户（如尚未创建）
sudo useradd -r -s /bin/false wheatagent

# 2. 设置目录所有权
sudo chown -R wheatagent:wheatagent /opt/wheatagent/

# 3. 设置目录权限
sudo chmod -R 755 /opt/wheatagent/
sudo chmod -R 777 /opt/wheatagent/backend/logs/      # 日志目录需可写
sudo chmod -R 777 /opt/wheatagent/backend/uploads/    # 上传目录需可写
sudo chmod -R 755 /opt/wheatagent/backend/models/     # 模型目录只读即可

# 4. 验证权限
ls -la /opt/wheatagent/backend/
# 预期:
# drwxr-xr-x  2 wheatagent wheatagent 4096 logs
# drwxr-xr-x  2 wheatagent wheatagent 4096 uploads
# drwxr-xr-x  3 wheatagent wheatagent 4096 models
```

**Windows 系统**:
```powershell
# 1. 检查当前用户对目录的权限
icacls D:\Project\WheatAgent\src\web\backend\logs

# 2. 授予写入权限
icacls D:\Project\WheatAgent\src\web\backend\logs /grant Everyone:(OI)(CI)F

# 3. 或者以管理员身份运行 IDE/终端
```

**SELinux 问题** (CentOS/RHEL):
```bash
# 如果 SELinux 阻止了文件访问
sudo setsebool -P httpd_can_network_connect 1
sudo chcon -R -t httpd_sys_content_t /opt/wheatagent/frontend/dist/
```

---

### 问题 13: 端口冲突 — Address already in use

**症状**: 启动时报错 `OSError: [Errno 98] Address already in use` 或 `Error: listen EADDRINUSE`

**原因**: 端口已被其他进程占用

**解决方案**:

**Linux**:
```bash
# 1. 查找占用端口的进程
lsof -i :8000
# 或
ss -tlnp | grep :8000

# 2. 终止进程（PID 从上一步获取）
kill -9 <PID>

# 3. 或修改启动端口
python -m uvicorn app.main:app --port 8001
```

**Windows**:
```powershell
# 1. 查找占用端口的进程
netstat -ano | findstr :8000

# 2. 终止进程（PID 从上一步获取）
taskkill /PID <PID> /F

# 3. 或修改启动端口
python -m uvicorn app.main:app --port 8001
```

**修改默认端口**:
```bash
# 后端: 通过命令行参数或 gunicorn.conf.py
--bind 0.0.0.0:8001

# 前端: 修改 vite.config.ts
server: { port: 5174 }
```

---

### 问题 14: Neo4j 连接失败

**症状**: `ServiceUnavailable: Failed to connect to Neo4j` 或知识增强功能不可用

**原因**: Neo4j 服务未启动 / Bolt 协议未启用 / 认证失败

**解决方案**:
```bash
# 1. 启动 Neo4j 服务
sudo systemctl start neo4j

# 2. 检查状态
sudo systemctl status neo4j
# 预期: active (running)

# 3. 验证 Bolt 连接
cypher-shell -u neo4j -p <password> "RETURN 1 AS test;"
# 预期: test
#   1

# 4. 检查 Neo4j 配置
# /etc/neo4j/neo4j.conf
dbms.connector.bolt.enabled=true
dbms.connector.bolt.listen_address=0.0.0.0:7687
dbms.connector.http.enabled=true
dbms.connector.http.listen_address=0.0.0.0:7474

# 5. 重启 Neo4j 使配置生效
sudo systemctl restart neo4j

# 6. 验证 Web UI
# 浏览器访问: http://localhost:7474
# 默认账号: neo4j / neo4j（首次登录需修改密码）
```

**降级方案**:
如果不使用知识图谱功能，可以暂时禁用 Neo4j：
```bash
# 在 .env 中注释掉 NEO4J_* 配置项
# 系统会自动跳过 GraphRAG 模块，基础诊断功能正常
```

---

### 问题 15: 内存泄漏或性能逐渐下降

**症状**: 服务运行一段时间后响应变慢，内存持续增长

**原因**: 对象未释放 / 缓存无限增长 / Worker 进程内存泄漏

**解决方案**:

**步骤 1: 监控内存使用**
```bash
# 实时查看进程内存
watch -n 1 'ps aux | grep gunicorn | grep -v grep'

# 或使用 psutil（Python 脚本）
python -c "
import psutil
for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
    if 'gunicorn' in proc.info['name']:
        print(f\"PID: {proc.info['pid']}, RSS: {proc.info['memory_info'].rss / 1024 / 1024:.1f} MB\")
"
```

**步骤 2: 配置 Gunicorn Worker 自动重启**
```python
# gunicorn.conf.py
max_requests = 10000            # 每个 Worker 处理 10000 请求后重启
max_requests_jitter = 1000      # 随机偏移，避免所有 Worker 同时重启
```

**步骤 3: 清理缓存**
```bash
# 管理员接口清空推理缓存
curl -X POST http://localhost:8000/api/v1/diagnosis/cache/clear \
  -H "Authorization: Bearer <admin_token>"
```

**步骤 4: 检查推理缓存 TTL**
```bash
# 确保设置了合理的缓存过期时间
grep INFERENCE_CACHE_TTL .env
# 默认: 1800（30分钟）
# 如果内存紧张，可缩短至 3600（1小时）
```

**长期方案**:
- 定期重启服务（可通过 cron 或 systemd timer 实现）
- 使用 Prometheus + Grafana 监控内存趋势
- 进行性能分析定位泄漏点（使用 memory_profiler 或 tracemalloc）

---

## 备份与恢复

### 数据库备份策略

#### MySQL 自动备份脚本

创建 `/opt/wheatagent/scripts/backup_mysql.sh`:

```bash
#!/bin/bash
"""MySQL 自动备份脚本 - 建议通过 Cron 定时执行"""

set -e

# 配置
BACKUP_DIR="/backup/mysql"
DB_USER="wheatagent"
DB_PASS="YourStrongPasswordHere!2026"
DB_NAME="wheat_agent_db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份（压缩）
echo "[$(date)] 开始备份数据库..."
mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --hex-blob \
  | gzip > "$BACKUP_DIR/wheat_agent_db_${DATE}.sql.gz"

# 验证备份文件
if [ -f "$BACKUP_DIR/wheat_agent_db_${DATE}.sql.gz" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/wheat_agent_db_${DATE}.sql.gz" | cut -f1)
    echo "[$(date)] 备份成功: wheat_agent_db_${DATE}.sql.gz ($BACKUP_SIZE)"
else
    echo "[$(date)] ❌ 备份失败!"
    exit 1
fi

# 清理过期备份（保留最近 30 天）
echo "[$(date)] 清理过期备份..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
CLEANED_COUNT=$(find "$BACKUP_DIR" -name "*.sql.gz" | wc -l)
echo "[$(date)] 当前备份文件数: $CLEANED_COUNT"

echo "[$(date)] ✅ 备份任务完成"
```

**设置定时任务**:
```bash
# 赋予执行权限
chmod +x /opt/wheatagent/scripts/backup_mysql.sh

# 编辑 Crontab（每天凌晨 2 点执行）
crontab -e
# 添加以下行:
0 2 * * * /opt/wheatagent/scripts/backup_mysql.sh >> /var/log/wheatagent/backup.log 2>&1

# 验证定时任务
crontab -l
```

#### Neo4j 备份（可选）

```bash
# 备份 Neo4j 数据库
neo4j-admin database dump neo4j --to=/backup/neo4j_$(date +%Y%m%d).dump --force

# 恢复 Neo4j 数据库
# 1. 先停止 Neo4j
sudo systemctl stop neo4j

# 2. 恢复数据库
neo4j-admin database load neo4j --from=/backup/neo4j_20260405.dump --force

# 3. 启动 Neo4j
sudo systemctl start neo4j
```

#### Redis 持久化配置

确保 Redis 开启了 RDB 和/或 AOF 持久化:

```bash
# 编辑 /etc/redis/redis.conf

# RDB 快照（默认已开启）
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir /var/lib/redis

# AOF 日志（更持久但性能略低）
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec  # 每秒同步一次
```

### 文件备份

```bash
# 备份上传的图像文件
tar -czvf /backup/uploads_$(date +%Y%m%d).tar.gz /opt/wheatagent/backend/uploads/

# 备份模型文件（较大，首次后可不再重复备份）
tar -czvf /backup/models_$(date +%Y%m%d).tar.gz /opt/wheatagent/backend/models/

# 备份配置文件（重要！）
cp /opt/wheatagent/backend/.env /backup/.env.backup_$(date +%Y%m%d)
cp /opt/wheatagent/backend/gunicorn.conf.py /backup/gunicorn.conf.py.backup
```

### 恢复流程

#### 场景 1: 数据库损坏或数据丢失

```bash
# 1. 停止服务
sudo systemctl stop wheatagent

# 2. 选择最新的备份文件
ls -lt /backup/mysql/*.sql.gz | head -1
# 例如: /backup/mysql/wheat_agent_db_20260405_020000.sql.gz

# 3. 恢复数据库
gunzip < /backup/mysql/wheat_agent_db_20260405_020000.sql.gz | mysql -u wheatagent -p wheat_agent_db

# 4. 验证恢复结果
mysql -u wheatagent -p -e "SELECT COUNT(*) FROM diagnoses;" wheat_agent_db
mysql -u wheatagent -p -SELECT COUNT(*) FROM users;" wheat_agent_db

# 5. 重启服务
sudo systemctl start wheatagent

# 6. 验证服务健康
sleep 10
curl http://localhost:8000/api/v1/health
```

#### 场景 2: 服务器迁移

```bash
# 1. 在新服务器上完成 Steps 1-4（环境准备到配置文件）

# 2. 从旧服务器传输备份文件
scp old-server:/backup/mysql/latest.sql.gz .
scp old-server:/backup/uploads_latest.tar.gz .
scp old-server:/backup/.env.backup_YYYYMMDD .

# 3. 恢复数据库（同上）

# 4. 恢复上传文件
tar -xzvf uploads_latest.tar.gz -C /opt/wheatagent/backend/

# 5. 恢复配置文件
cp .env.backup_YYYYMMDD /opt/wheatagent/backend/.env
chmod 600 /opt/wheatagent/backend/.env

# 6. 启动服务并验证
sudo systemctl start wheatagent
curl http://localhost:8000/api/v1/health
```

#### 场景 3: 完全灾难恢复

```bash
# 1. 准备全新的服务器（相同 OS 版本）

# 2. 按照 Steps 1-6 完成全新部署

# 3. 恢复所有备份:
#    - MySQL 数据库
#    - Neo4j 数据库（如使用）
#    - Redis AOF/RDB 文件（如使用）
#    - 上传图像文件
#    - 模型文件
#    - 配置文件（.env, gunicorn.conf.py 等）

# 4. 全面验证
#    - 所有健康检查端点
#    - 用户登录功能
#    - AI 诊断功能（提交测试图片）
#    - 知识库浏览（如使用 Neo4j）
#    - 报告生成功能
```

### 备份验证

定期验证备份的可恢复性非常重要！

```bash
# 每月执行一次恢复演练（在测试环境中）
# 1. 创建测试数据库
mysql -u root -p -e "CREATE DATABASE wheat_agent_test CHARACTER SET utf8mb4;"

# 2. 恢复备份到测试库
gunzip < /backup/mysql/latest.sql.gz | mysql -u wheatagent -p wheat_agent_test

# 3. 验证数据完整性
mysql -u wheatagent -p wheat_agent_test -e "
  SELECT CONCAT('users: ', COUNT(*)) FROM users
  UNION ALL
  SELECT CONCAT('diagnoses: ', COUNT(*)) FROM diagnoses
  UNION ALL
  SELECT CONCAT('images: ', COUNT(*)) FROM image_metadata;
"

# 4. 清理测试库
mysql -u root -p -e "DROP DATABASE wheat_agent_test;"
```

---

## 附录

### A. 快速命令参考卡

```bash
# ===== 服务管理 =====
conda activate wheatagent-py310              # 激活环境
python -m uvicorn app.main:app --reload ...  # 开发模式启动
gunicorn app.main:app -c gunicorn.conf.py    # 生产模式启动
sudo systemctl status wheatagent             # 查看服务状态

# ===== 健康检查 =====
curl http://localhost:8000/api/v1/health                     # 基础健康
curl http://localhost:8000/api/v1/health/database            # 数据库状态
curl http://localhost:8000/api/v1/diagnosis/health/ai        # AI 模型状态
curl http://localhost:8000/metrics                           # Prometheus 指标

# ===== 日志查看 =====
tail -f /var/log/wheatagent/access.log                       # 访问日志
tail -f /var/log/wheatagent/error.log                        # 错误日志
sudo journalctl -u wheatagent -f                             # 系统服务日志
docker-compose logs -f api                                   # Docker 日志

# ===== 监控命令 =====
watch -n 1 nvidia-smi                                        # GPU 实时监控
htop                                                          # 系统资源
df -h                                                         # 磁盘使用
netstat -tlnp                                                # 端口监听
free -h                                                       # 内存使用

# ===== 备份恢复 =====
mysqldump -u wheatagent -p wheat_agent_db | gzip > backup.sql.gz  # 备份
gunzip < backup.sql.gz | mysql -u wheatagent -p wheat_agent_db     # 恢复
```

### B. 端口清单

| 端口 | 服务 | 用途 | 是否必须开放 |
|------|------|------|-------------|
| 80 | Nginx | 前端 HTTP 访问 | ✅ 是 |
| 443 | Nginx | 前端 HTTPS 访问 | 推荐 |
| 8000 | FastAPI/Gunicorn | 后端 API 服务 | ✅ 是（内部）|
| 3306 | MySQL | 数据库连接 | ⚠️ 仅内部 |
| 6379 | Redis | 缓存/会话 | ⚠️ 仅内部 |
| 7474 | Neo4j HTTP | 图数据库 Web UI | 可选 |
| 7687 | Neo4j Bolt | 图数据库连接协议 | 可选 |
| 9000 | ~~MinIO~~ | ~~已弃用~~ | ~~使用本地文件存储~~ |
| 9001 | ~~MinIO Console~~ | ~~已弃用~~ | ~~使用本地文件存储~~ |

### C. 配置项快速索引（55+ 项完整列表详见 V7_PROJECT_ANALYSIS.md 第 7 章）

| 分类 | 关键配置项 | 默认值 | 说明 |
|------|-----------|--------|------|
| **基础** | APP_ENV, DEBUG, LOG_LEVEL | production, False, INFO | 应用基础设置 |
| **数据库** | DATABASE_*, DB_POOL_* | localhost, 3306, pool=10 | MySQL 连接池 |
| **Redis** | REDIS_* | localhost:6379/0 | 缓存/会话 |
| **JWT** | JWT_SECRET_KEY, JWT_EXPIRE_HOURS | auto-gen, 24h | 认证令牌 |
| **CORS** | CORS_ORIGINS | localhost:5173,3000 | 跨域控制 |
| **AI 模型** | QWEN_MODEL_PATH, YOLO_MODEL_PATH | auto-download | 模型路径 |
| **融合诊断** | FUSION_*_WEIGHT | 0.4/0.35/0.25 | 多模态权重 |
| **限流** | RATE_LIMIT_* | 60/10/20 per min | API 频率控制 |
| **SSE** | SSE_TIMEOUT, SSE_HEARTBEAT | 120s, 15s | 流式传输 |
| **GPU 控制** | MAX_CONCURRENT_DIAGNOSIS, GPU_MEMORY_THRESHOLD | 3, 0.90 | 并发与显存 |
| **Neo4j** | NEO4J_* | bolt://localhost:7687 | 知识图谱 |
| **MinIO** | MINIO_* | ~~已弃用~~ | ~~使用本地文件存储~~ |
| **Celery** | CELERY_BROKER_URL | ~~已弃用~~ | ~~使用SSE流式响应~~ |

### D. 常用维护操作时间表

| 频率 | 操作 | 命令/说明 |
|------|------|----------|
| **每日** | 数据库自动备份 | Cron 任务 (02:00) |
| **每日** | 检查磁盘空间 | `df -h` (阈值 > 85%) |
| **每周** | 检查日志异常 | `grep ERROR error.log \| wc -l` |
| **每周** | 清理旧日志 | Logrotate 自动处理 |
| **每月** | 备份验证演练 | 测试环境恢复备份 |
| **每月** | 更新依赖包 | `pip list --outdated` |
| **每季度** | JWT 密钥轮换 | 更新 JWT_SECRET_KEY |
| **每季度** | 安全审计 | 检查 CVE 漏洞 |
| **按需** | 模型升级 | 替换 YOLO/Qwen 模型文件 |
| **按需** | 扩容调整 | 增加 Worker/优化配置 |

---

> 📌 **更多帮助文档**:
> - 项目总览: [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md)
> - API 参考: [API_REFERENCE.md](./API_REFERENCE.md)
> - 用户手册: [USER_GUIDE.md](./USER_GUIDE.md)
> - 环境管理: [ENVIRONMENT_MANAGEMENT.md](./ENVIRONMENT_MANAGEMENT.md)
> - 测试指南: [TEST_GUIDE.md](./TEST_GUIDE.md)
> - 云边端部署: [CLOUD_EDGE_DEPLOYMENT.md](./CLOUD_EDGE_DEPLOYMENT.md)
> - 知识图谱: [GRAPH_RAG_SPEC.md](./GRAPH_RAG_SPEC.md)
> - 性能基准: [BASELINE_PERFORMANCE.md](../src/web/backend/benchmarks/BASELINE_PERFORMANCE.md)

---

*文档版本: V12.0 (Production Grade)*
*最后更新: 2026-04-05*
*适用范围: WheatAgent V12.0+*
*维护者: DevOps Team*
