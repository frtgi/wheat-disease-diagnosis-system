# 基于多模态融合的小麦病害诊断系统 - 端口分配规范

**版本**: V12.0
**生成日期**: 2026-04-05
**项目**: 基于多模态融合的小麦病害诊断系统

本文档定义了基于多模态融合的小麦病害诊断系统的端口分配标准，确保各服务之间无冲突运行。

---

## 一、端口分配总览

| 端口范围 | 服务类型 | 说明 |
|---------|---------|------|
| 80/443 | Web 前端 | HTTP/HTTPS 入口 |
| 8000 | API 网关 | FastAPI 主服务 |
| 8001-8010 | AI 模型服务 | 视觉、语言、融合模型 |
| 3306 | 数据库 | MySQL |
| 6379 | 缓存 | Redis |
| 9000 | 对象存储 | 已弃用 |

---

## 二、详细端口分配表

### 2.1 Web 前端服务

#### 端口 80 - HTTP 服务

| 属性 | 值 |
|-----|-----|
| **端口号** | 80 |
| **服务名称** | Nginx/Apache HTTP |
| **协议** | HTTP |
| **用途说明** | 提供 Web 前端的 HTTP 访问入口，处理静态资源请求和反向代理 |

**配置示例 (Nginx):**

```nginx
server {
    listen 80;
    server_name wheat-agent.local;

    location / {
        root /var/www/wheat-agent/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 端口 443 - HTTPS 服务

| 属性 | 值 |
|-----|-----|
| **端口号** | 443 |
| **服务名称** | Nginx/Apache HTTPS |
| **协议** | HTTPS |
| **用途说明** | 提供 Web 前端的安全 HTTPS 访问入口，支持 SSL/TLS 加密 |

**配置示例 (Nginx):**

```nginx
server {
    listen 443 ssl http2;
    server_name wheat-agent.local;

    ssl_certificate /etc/nginx/ssl/wheat-agent.crt;
    ssl_certificate_key /etc/nginx/ssl/wheat-agent.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        root /var/www/wheat-agent/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name wheat-agent.local;
    return 301 https://$server_name$request_uri;
}
```

---

### 2.2 API 网关服务

#### 端口 8000 - FastAPI 主服务

| 属性 | 值 |
|-----|-----|
| **端口号** | 8000 |
| **服务名称** | FastAPI Main API |
| **协议** | HTTP/REST |
| **用途说明** | 系统主 API 网关，处理所有业务请求路由、认证授权、请求转发 |

**配置示例 (FastAPI):**

```python
import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="小麦病害诊断系统 API",
    description="智能小麦病害诊断系统 API",
    version="1.0.0"
)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        reload=False
    )
```

**配置示例 (环境变量):**

```bash
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

---

### 2.3 AI 模型服务

#### 端口 8001 - YOLO 视觉检测服务

| 属性 | 值 |
|-----|-----|
| **端口号** | 8001 |
| **服务名称** | YOLO Vision Service |
| **协议** | HTTP/gRPC |
| **用途说明** | 小麦病害图像检测服务，基于 YOLOv8 模型进行病虫害识别 |

**配置示例:**

```python
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="YOLO Vision Service")

@app.post("/detect")
async def detect_disease(image_path: str):
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

#### 端口 8002 - Qwen 多模态服务

| 属性 | 值 |
|-----|-----|
| **端口号** | 8002 |
| **服务名称** | Qwen VL Service |
| **协议** | HTTP/gRPC |
| **用途说明** | 通义千问多模态大模型服务，提供图像理解和自然语言处理能力 |

**配置示例:**

```python
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Qwen VL Service")

@app.post("/analyze")
async def analyze_image(image_path: str, question: str):
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

#### 端口 8003 - 多模态融合服务

| 属性 | 值 |
|-----|-----|
| **端口号** | 8003 |
| **服务名称** | Fusion Service |
| **协议** | HTTP/gRPC |
| **用途说明** | 多模态融合推理服务，整合视觉和语言模型输出，生成综合诊断结果 |

**配置示例:**

```python
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Fusion Service")

@app.post("/fuse")
async def fuse_results(vision_result: dict, text_result: dict):
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

#### 端口 8004-8010 - 预留扩展服务

| 端口 | 服务名称 | 用途说明 |
|-----|---------|---------|
| 8004 | Knowledge Graph Service | 知识图谱推理服务 |
| 8005 | LLaVA Service | LLaVA 视觉语言模型服务 |
| 8006 | MiniCPM Service | MiniCPM 轻量级模型服务 |
| 8007 | Training Service | 模型训练服务 |
| 8008 | Evaluation Service | 模型评估服务 |
| 8009 | Reserved | 预留 |
| 8010 | Reserved | 预留 |

---

### 2.4 数据库服务

#### 端口 3306 - MySQL 数据库

| 属性 | 值 |
|-----|-----|
| **端口号** | 3306 |
| **服务名称** | MySQL Database |
| **协议** | MySQL Protocol |
| **用途说明** | 关系型数据库，存储用户数据、诊断记录、知识库等结构化数据 |

**配置示例 (my.cnf):**

```ini
[mysqld]
port = 3306
bind-address = 0.0.0.0
max_connections = 200
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[client]
port = 3306
```

**配置示例 (Docker):**

```yaml
services:
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: wheat_agent
    volumes:
      - mysql_data:/var/lib/mysql
```

---

### 2.5 缓存服务

#### 端口 6379 - Redis 缓存

| 属性 | 值 |
|-----|-----|
| **端口号** | 6379 |
| **服务名称** | Redis Cache |
| **协议** | Redis Protocol |
| **用途说明** | 高性能缓存服务，用于会话管理、热点数据缓存、消息队列 |

**配置示例 (redis.conf):**

```conf
port 6379
bind 0.0.0.0
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

**配置示例 (Python 连接):**

```python
import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)
```

---

### 2.6 对象存储服务（已弃用）

> **注意**: MinIO对象存储已弃用，系统使用本地文件存储。端口9000/9001不再需要。

#### ~~端口 9000 - MinIO 对象存储~~（已弃用）

| 属性 | 值 |
|-----|-----|
| **端口号** | ~~9000~~ |
| **服务名称** | ~~MinIO Object Storage~~ |
| **状态** | 已弃用，使用本地文件存储 |

**替代方案**: 使用本地文件存储，配置 `UPLOAD_DIR=./uploads`

---

## 三、端口冲突解决方案

### 3.1 检测端口占用

**Windows 系统:**

```powershell
netstat -ano | findstr :8000
```

**Linux/macOS 系统:**

```bash
lsof -i :8000
netstat -tlnp | grep 8000
```

### 3.2 终止占用进程

**Windows 系统:**

```powershell
taskkill /PID <进程ID> /F
```

**Linux/macOS 系统:**

```bash
kill -9 <进程ID>
```

### 3.3 修改服务端口

当标准端口被占用时，可通过以下方式修改：

**方式一：环境变量配置**

```bash
export API_PORT=18000
export MYSQL_PORT=13306
export REDIS_PORT=16379
```

**方式二：配置文件修改**

```yaml
services:
  api:
    ports:
      - "18000:8000"
  mysql:
    ports:
      - "13306:3306"
  redis:
    ports:
      - "16379:6379"
```

### 3.4 端口冲突处理流程

```
1. 检测端口占用情况
      ↓
2. 确认占用进程是否为必要服务
      ↓
   ┌─────────────┬─────────────┐
   │             │             │
   ↓             ↓             ↓
终止进程    修改本服务端口   使用替代端口
   │             │             │
   └─────────────┴─────────────┘
                 ↓
3. 验证服务正常运行
                 ↓
4. 更新相关配置文档
```

---

## 四、Docker 环境端口映射

### 4.1 Docker Compose 完整配置

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api

  api:
    build: ./src/api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://root:${MYSQL_PASSWORD}@mysql:3306/wheat_agent
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis

  yolo-service:
    build: ./src/perception
    ports:
      - "8001:8001"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  qwen-service:
    build: ./src/cognition
    ports:
      - "8002:8002"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  fusion-service:
    build: ./src/fusion
    ports:
      - "8003:8003"

  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: wheat_agent
    volumes:
      - mysql_data:/var/lib/mysql
      - ./src/database/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  mysql_data:
  redis_data:
  minio_data:
```

### 4.2 Docker 端口映射规则

| 映射格式 | 说明 |
|---------|------|
| `80:80` | 主机端口:容器端口 |
| `8000-8010:8000-8010` | 端口范围映射 |
| `127.0.0.1:8000:8000` | 绑定到特定接口 |

---

## 五、Kubernetes 环境端口配置

### 5.1 Service 配置示例

```yaml
apiVersion: v1
kind: Service
metadata:
  name: wheat-agent-api
  namespace: wheat-agent
spec:
  type: ClusterIP
  ports:
    - name: http
      port: 8000
      targetPort: 8000
      protocol: TCP
  selector:
    app: wheat-agent-api

---
apiVersion: v1
kind: Service
metadata:
  name: wheat-agent-nginx
  namespace: wheat-agent
spec:
  type: LoadBalancer
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
    - name: https
      port: 443
      targetPort: 443
      protocol: TCP
  selector:
    app: wheat-agent-nginx

---
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: wheat-agent
spec:
  type: ClusterIP
  ports:
    - port: 3306
      targetPort: 3306
  selector:
    app: mysql

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: wheat-agent
spec:
  type: ClusterIP
  ports:
    - port: 6379
      targetPort: 6379
  selector:
    app: redis

---
# MinIO Service 已弃用（使用本地文件存储）
```

### 5.2 Deployment 配置示例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wheat-agent-api
  namespace: wheat-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wheat-agent-api
  template:
    metadata:
      labels:
        app: wheat-agent-api
    spec:
      containers:
        - name: api
          image: wheat-agent/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: wheat-agent-secrets
                  key: database-url
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yolo-service
  namespace: wheat-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: yolo-service
  template:
    metadata:
      labels:
        app: yolo-service
    spec:
      containers:
        - name: yolo
          image: wheat-agent/yolo:latest
          ports:
            - containerPort: 8001
          resources:
            limits:
              nvidia.com/gpu: 1
```

### 5.3 Ingress 配置示例

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wheat-agent-ingress
  namespace: wheat-agent
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - wheat-agent.example.com
      secretName: wheat-agent-tls
  rules:
    - host: wheat-agent.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: wheat-agent-nginx
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: wheat-agent-api
                port:
                  number: 8000
```

---

## 六、端口安全建议

### 6.1 访问控制

| 端口 | 访问策略 | 说明 |
|-----|---------|------|
| 80/443 | 公开访问 | 通过 Nginx 反向代理 |
| 8000 | 内部访问 | 仅允许 Nginx 和内部服务访问 |
| 8001-8010 | 内部访问 | 仅允许 API 网关访问 |
| 3306 | 内部访问 | 仅允许应用服务访问 |
| 6379 | 内部访问 | 仅允许应用服务访问 |
| 9000 | ~~已弃用~~ | ~~MinIO已弃用，使用本地文件存储~~ |

### 6.2 防火墙配置示例

**Windows 防火墙:**

```powershell
New-NetFirewallRule -DisplayName "小麦病害诊断系统 API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "小麦病害诊断系统 MySQL" -Direction Inbound -LocalPort 3306 -Protocol TCP -Action Block
```

**Linux iptables:**

```bash
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -j DROP
```

---

## 七、附录

### 7.1 端口快速查询表

```
┌─────────────────────────────────────────────────────────┐
│                    小麦病害诊断系统端口分配                    │
├─────────┬───────────────────────┬───────────────────────┤
│  端口   │       服务名称        │        用途           │
├─────────┼───────────────────────┼───────────────────────┤
│   80    │ Nginx HTTP            │ Web 前端入口          │
│  443    │ Nginx HTTPS           │ Web 安全入口          │
│ 8000    │ FastAPI Main          │ API 网关              │
│ 8001    │ YOLO Service          │ 视觉检测              │
│ 8002    │ Qwen VL Service       │ 多模态理解            │
│ 8003    │ Fusion Service        │ 多模态融合            │
│ 8004    │ Knowledge Graph       │ 知识图谱              │
│ 8005    │ LLaVA Service         │ 视觉语言模型          │
│ 8006    │ MiniCPM Service       │ 轻量级模型            │
│ 8007    │ Training Service      │ 模型训练              │
│ 8008    │ Evaluation Service    │ 模型评估              │
│ 8009    │ Reserved              │ 预留                  │
│ 8010    │ Reserved              │ 预留                  │
│ 3306    │ MySQL                 │ 关系型数据库          │
│ 6379    │ Redis                 │ 缓存服务              │
│ 9000    │ ~~已弃用~~             │ ~~MinIO已弃用~~       │
│ 9001    │ ~~已弃用~~             │ ~~MinIO已弃用~~       │
└─────────┴───────────────────────┴───────────────────────┘
```

### 7.2 版本历史

| 版本 | 日期 | 修改内容 |
|-----|------|---------|
| v1.0 | 2024-01-01 | 初始版本 |
| v1.2 | 2026-04-16 | V12 文档同步 — 标记MinIO端口为已弃用 |

---

**文档维护者:** 小麦病害诊断系统开发团队  
**最后更新:** 2024年
