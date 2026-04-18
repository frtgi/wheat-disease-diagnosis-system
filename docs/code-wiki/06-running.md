# 运行方式文档

## 环境要求

### 硬件要求
- **CPU**: 至少 4 核
- **内存**: 至少 8GB RAM
- **GPU**: 推荐 NVIDIA GPU（用于模型推理）
- **存储空间**: 至少 50GB 可用空间

### 软件要求
- **后端**:
  - Python 3.8+
  - pip
  - CUDA 11.7+（如果使用 GPU）

- **前端**:
  - Node.js 16+
  - npm 8+

- **数据库**:
  - MySQL 8.0+
  - Redis 7.0+
  - Neo4j 5.0+

- **其他**:
  - Docker（用于容器化部署）
  - Docker Compose（用于多容器管理）

## 本地开发环境搭建

### 1. 克隆仓库

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. 后端环境搭建

#### 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 安装依赖

```bash
# 进入后端目录
cd src/web/backend

# 安装核心依赖
pip install -r requirements.txt

# 安装机器学习依赖（如果需要）
pip install torch torchvision
pip install ultralytics  # YOLOv8
pip install transformers
pip install neo4j-driver
```

#### 配置环境变量

创建 `.env` 文件，配置以下环境变量：

```env
# 应用配置
APP_ENV=development
APP_DEBUG=true

# 数据库配置
DATABASE_URL=mysql://username:password@localhost:3306/wheat_disease

# Redis 配置
REDIS_URL=redis://localhost:6379

# Neo4j 配置
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# 模型配置
MODEL_PATH=./models

# API 密钥
API_SECRET_KEY=your_secret_key
```

### 3. 前端环境搭建

#### 安装依赖

```bash
# 进入前端目录
cd src/web/frontend

# 安装依赖
npm install
```

#### 配置环境变量

创建 `.env` 文件，配置以下环境变量：

```env
# API 地址
VITE_API_URL=http://localhost:8000

# 构建模式
VITE_MODE=development
```

## 启动服务

### 1. 启动后端服务

#### 使用启动脚本

```bash
# 进入后端目录
cd src/web/backend

# 运行启动脚本
# Windows
start_server.bat
# Linux/Mac
bash start_server.sh  # 如果没有此脚本，使用下面的命令

# 或者直接运行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 服务地址
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 2. 启动前端服务

#### 使用启动脚本

```bash
# 进入前端目录
cd src/web/frontend

# 运行启动脚本
# Windows
start-dev.ps1
# Linux/Mac
npm run dev
```

#### 服务地址
- 前端服务：http://localhost:5173

## Docker 部署

### 1. 准备 Docker 环境

确保已安装 Docker 和 Docker Compose：

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version
```

### 2. 配置环境变量

创建 `.env` 文件，配置以下环境变量：

```env
# Neo4j 密码
NEO4J_PASSWORD=your_neo4j_password

# Redis 密码
REDIS_PASSWORD=your_redis_password

# MinIO 配置
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your_minio_secret_key

# API 密钥
API_SECRET_KEY=your_api_secret_key

# Grafana 配置
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 3. 启动服务

```bash
# 进入部署目录
cd deploy

# 启动所有服务
docker-compose up -d

# 启动特定服务（例如只启动 API 和 Web）
docker-compose up -d api web

# 启动包含监控的服务
docker-compose --profile monitoring up -d

# 启动包含训练服务的服务
docker-compose --profile training up -d
```

### 4. 访问服务

- **API 服务**：http://localhost:8000
- **Web 界面**：http://localhost:7860
- **Neo4j 管理界面**：http://localhost:7474
- **MinIO 管理界面**：http://localhost:9001
- **Prometheus**：http://localhost:9090
- **Grafana**：http://localhost:3000

### 5. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止特定服务
docker-compose stop api web
```

## 边缘部署

### 1. 准备边缘设备

- 确保边缘设备满足硬件要求
- 安装必要的依赖（Python、CUDA 等）

### 2. 优化模型

```bash
# 进入部署目录
cd src/deploy

# 运行边缘优化脚本
python edge_optimizer.py --model_path ./models --output_path ./edge_models
```

### 3. 部署到边缘设备

```bash
# 使用部署脚本
bash deploy/edge/deploy_edge.sh --device_ip <device-ip> --model_path ./edge_models
```

## 常见问题和解决方案

### 1. 依赖安装失败

**问题**：安装依赖时出现错误

**解决方案**：
- 确保 Python 版本正确（3.8+）
- 使用虚拟环境隔离依赖
- 对于 GPU 依赖，确保 CUDA 版本与 PyTorch 版本匹配

### 2. 服务启动失败

**问题**：后端服务启动失败

**解决方案**：
- 检查数据库连接是否正确
- 检查环境变量配置是否完整
- 查看日志输出，定位具体错误

### 3. 模型加载失败

**问题**：模型加载时出现错误

**解决方案**：
- 确保模型文件存在且路径正确
- 检查模型文件完整性
- 对于 GPU 模型，确保 CUDA 可用

### 4. 前端无法连接后端

**问题**：前端无法连接到后端 API

**解决方案**：
- 检查后端服务是否正常运行
- 检查前端配置的 API 地址是否正确
- 检查网络防火墙设置

### 5. 性能问题

**问题**：系统响应缓慢

**解决方案**：
- 启用 Redis 缓存
- 优化模型推理速度
- 调整服务配置，增加并发处理能力

## 性能优化建议

### 1. 模型优化

- 使用模型量化（int8、int4）减少模型大小和推理时间
- 对于边缘设备，使用 TensorRT 加速推理
- 启用模型缓存，减少重复加载时间

### 2. 服务优化

- 使用异步处理提高并发能力
- 启用 Redis 缓存减少数据库查询
- 调整 uvicorn 工作进程数量

### 3. 数据库优化

- 为常用查询添加索引
- 使用连接池减少数据库连接开销
- 定期清理过期数据

### 4. 部署优化

- 使用容器化部署提高一致性
- 配置资源限制，避免资源争用
- 使用负载均衡处理高并发请求

## 监控与维护

### 1. 日志管理

- 后端日志：`src/web/backend/logs/`
- 前端日志：浏览器控制台
- Docker 容器日志：`docker logs <container-id>`

### 2. 健康检查

- API 健康检查：http://localhost:8000/api/v1/health
- 服务状态监控：使用 Prometheus 和 Grafana

### 3. 定期维护

- 备份数据库和模型文件
- 更新依赖到最新版本
- 清理缓存和临时文件

## 开发工作流

### 1. 代码修改

- 后端修改后，服务会自动重载（使用 `--reload` 选项）
- 前端修改后，页面会自动刷新

### 2. 测试

- 后端测试：`cd src/web/backend && pytest`
- 前端测试：`cd src/web/frontend && npm test`
- 集成测试：`cd tests && python -m pytest integration/`

### 3. 部署流程

1. 开发和测试
2. 构建 Docker 镜像
3. 部署到测试环境
4. 测试验证
5. 部署到生产环境
