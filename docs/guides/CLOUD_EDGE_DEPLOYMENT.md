# 基于多模态融合的小麦病害诊断系统 - 云边协同部署文档

**版本**: V12.0
**生成日期**: 2026-04-05
**最后审查**: 2026-04-05 (V7 文档标准化)
**项目**: 基于多模态融合的小麦病害诊断系统 - 云边协同部署方案

---

## 1. 概述

### 1.1 部署架构

本系统采用**云边协同**部署架构，充分发挥云端和边缘端的优势:

| 部署位置 | 优势 | 适用场景 |
|---------|------|---------|
| **云端** | 强大算力、集中管理、大规模训练 | 模型训练、批量处理、高并发服务 |
| **边缘端** | 低延迟、离线运行、数据隐私 | 实时诊断、田间检测、网络受限场景 |

### 1.2 部署模式

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        云边协同部署架构                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                            ☁️ 云端 (Cloud)                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Kubernetes Cluster (K8s 集群)                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │  训练节点     │  │  API 服务节点  │  │  知识图谱节点  │          │    │
│  │  │  (GPU×8)     │  │  (GPU×4)     │  │  (Neo4j)     │          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │              云端功能                                      │   │    │
│  │  │  • 模型训练与微调                                         │   │    │
│  │  │  • 大规模批量处理                                         │   │    │
│  │  │  • 知识图谱管理与更新                                      │   │    │
│  │  │  • 用户管理与权限控制                                      │   │    │
│  │  │  • 数据分析与可视化                                        │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                       │                       │                          │
│           ┌───────────┘                       └───────────┐             │
│           │                                               │             │
│           ▼                                               ▼             │
│    ┌─────────────┐                                 ┌─────────────┐      │
│    │  4G/5G/WiFi │                                 │  4G/5G/WiFi │      │
│    └─────────────┘                                 └─────────────┘      │
│           │                                               │             │
│           ▼                                               ▼             │
│  ┌─────────────────┐                             ┌─────────────────┐    │
│  │  📱 边缘端 A     │                             │  📱 边缘端 B     │    │
│  │  (Jetson Nano)  │                             │ (Raspberry Pi)  │    │
│  │                 │                             │                 │    │
│  │  • 实时诊断      │                             │  • 实时诊断      │    │
│  │  • 离线推理      │                             │  • 离线推理      │    │
│  │  • 数据采集      │                             │  • 数据采集      │    │
│  │  • 本地缓存      │                             │  • 本地缓存      │    │
│  └─────────────────┘                             └─────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 云边协同机制

**协同方式**:
| 协同类型 | 说明 | 实现方式 |
|---------|------|---------|
| **模型同步** | 云端训练，边缘推理 | 模型版本管理 + 增量更新 |
| **数据同步** | 边缘采集，云端训练 | 数据脱敏 + 断点续传 |
| **知识同步** | 云端更新，边缘同步 | 知识图谱快照 + 增量同步 |
| **任务协同** | 云端调度，边缘执行 | 任务队列 + 负载均衡 |

---

## 2. 云端部署

### 2.1 部署架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        云端部署架构 (Kubernetes)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Load Balancer (Nginx Ingress)                  │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    API Gateway (Kong/Traefik)                     │   │
│  │         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │   │
│  │         │  限流熔断   │  │  认证鉴权   │  │  日志监控   │        │   │
│  │         └─────────────┘  └─────────────┘  └─────────────┘        │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                         │
│           ┌───────────────────┼───────────────────┐                    │
│           │                   │                   │                    │
│           ▼                   ▼                   ▼                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│  │  Training Service│ │ Diagnosis Service│ │ Knowledge Service│         │
│  │  (PyTorch)       │ │ (FastAPI)        │ │ (Neo4j)          │         │
│  │  Replicas: 2     │ │ Replicas: 4      │ │ Replicas: 3      │         │
│  │  GPU: 8×A100     │ │ GPU: 4×T4        │ │ CPU: 4 Core      │         │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Storage & Database                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │  本地文件存储 │  │  PostgreSQL │  │   Redis     │               │   │
│  │  │ (模型/图像)   │  │ (业务数据)   │  │  (缓存)      │               │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 最小部署配置

**硬件要求**:
| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| **CPU** | 8 核 | 16 核 |
| **内存** | 32GB | 64GB |
| **GPU** | 1×T4 (16GB) | 4×T4 (16GB) |
| **存储** | 500GB SSD | 2TB NVMe |
| **网络** | 1Gbps | 10Gbps |

**软件要求**:
- Ubuntu 20.04+ / CentOS 7+
- Docker 24+
- Kubernetes 1.28+
- NVIDIA Driver 520+
- CUDA 12.0+

### 2.3 Docker Compose 部署

**快速部署 (开发/测试环境)**:

```yaml
# deploy/docker-compose.yml
version: '3.9'

services:
  # API 服务
  api:
    image: iwdda/api:latest
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=neo4j://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=neo4j_password
      - REDIS_URL=redis://redis:6379
      - MODEL_PATH=/models
    volumes:
      - ./models:/models
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      - neo4j
      - redis
    restart: unless-stopped

  # Web 界面
  web:
    image: iwdda/web:latest
    ports:
      - "7860:7860"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped

  # Neo4j 知识图谱
  neo4j:
    image: neo4j:5.12
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/neo4j_password
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=2G
      - NEO4J_dbms_memory_heap_max__size=4G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - ./checkpoints/knowledge_graph:/import
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # 本地文件存储 (模型/图像)
  # MinIO已弃用，使用本地文件存储
  # volumes映射上传目录即可

  # 训练服务
  training:
    image: iwdda/training:latest
    environment:
      - UPLOAD_DIR=/app/uploads
    volumes:
      - ./datasets:/datasets
      - ./runs:/runs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  redis_data:
  # minio_data: (已弃用)

networks:
  default:
    driver: bridge
```

**部署命令**:
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down

# 清理数据 (谨慎使用)
docker-compose down -v
```

### 2.4 Kubernetes 部署

**生产环境部署**:

#### Namespace 配置
```yaml
# deploy/k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: iwdda
  labels:
    name: iwdda
    environment: production
```

#### ConfigMap 配置
```yaml
# deploy/k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: iwdda-config
  namespace: iwdda
data:
  # 应用配置
  APP_ENV: "production"
  APP_DEBUG: "false"
  APP_LOG_LEVEL: "info"
  
  # Neo4j 配置
  NEO4J_URI: "neo4j://neo4j-service:7687"
  NEO4J_DATABASE: "neo4j"
  
  # Redis 配置
  REDIS_URL: "redis://redis-service:6379"
  
  # MinIO 配置（已弃用，使用本地文件存储）
  # MINIO_ENDPOINT: "minio-service:9000"
  # MINIO_BUCKET: "models"
  
  # 模型配置
  MODEL_CACHE_DIR: "/cache/models"
  MAX_BATCH_SIZE: "32"
  
  # 性能配置
  INFERENCE_TIMEOUT: "30"
  MAX_CONCURRENT_REQUESTS: "100"

  # V5 新增: SSE 流式配置
  SSE_TIMEOUT_SECONDS: "120"
  SSE_HEARTBEAT_INTERVAL: "15"
  SSE_BACKPRESSURE_QUEUE_SIZE: "100"

  # V5 新增: 诊断限流配置
  MAX_CONCURRENT_DIAGNOSIS: "3"
  MAX_DIAGNOSIS_QUEUE_SIZE: "10"
  DIAGNOSIS_QUEUE_TIMEOUT: "300"

  # V5 新增: GPU 监控配置
  GPU_MEMORY_THRESHOLD: "0.90"
```

#### Secret 配置
```yaml
# deploy/k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: iwdda-secret
  namespace: iwdda
type: Opaque
stringData:
  # Neo4j 凭证
  NEO4J_USER: "neo4j"
  NEO4J_PASSWORD: "secure_neo4j_password"
  
  # MinIO 凭证（已弃用）
  # MINIO_ACCESS_KEY: "minio_access_key"
  # MINIO_SECRET_KEY: "minio_secret_key"
  
  # API Key
  API_SECRET_KEY: "your_api_secret_key"
  
  # JWT 密钥
  JWT_SECRET: "your_jwt_secret"
```

#### API 服务 Deployment
```yaml
# deploy/k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: iwdda
  labels:
    app: api-service
    version: v1
spec:
  replicas: 4
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
        version: v1
    spec:
      containers:
      - name: api
        image: iwdda/api:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: NEO4J_USER
          valueFrom:
            secretKeyRef:
              name: iwdda-secret
              key: NEO4J_USER
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: iwdda-secret
              key: NEO4J_PASSWORD
        envFrom:
        - configMapRef:
            name: iwdda-config
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
            nvidia.com/gpu: "1"
          limits:
            cpu: "4"
            memory: "8Gi"
            nvidia.com/gpu: "1"
        volumeMounts:
        - name: model-cache
          mountPath: /cache/models
        - name: logs
          mountPath: /app/logs
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      - name: logs
        emptyDir: {}
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: gpu-type
                operator: In
                values:
                - nvidia-t4
                - nvidia-a100
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: iwdda
spec:
  selector:
    app: api-service
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
  namespace: iwdda
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: gpu_utilization
      target:
        type: AverageValue
        averageValue: "70"
```

#### Neo4j StatefulSet
```yaml
# deploy/k8s/neo4j-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: iwdda
spec:
  serviceName: neo4j
  replicas: 3
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.12-enterprise
        ports:
        - containerPort: 7687
          name: bolt
        - containerPort: 7474
          name: http
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: iwdda-secret
              key: NEO4J_PASSWORD
        - name: NEO4J_ACCEPT_LICENSE_AGREEMENT
          value: "eval"
        resources:
          requests:
            cpu: "2"
            memory: "8Gi"
          limits:
            cpu: "4"
            memory: "16Gi"
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
        - name: neo4j-logs
          mountPath: /logs
        livenessProbe:
          httpGet:
            path: /browser
            port: 7474
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /browser
            port: 7474
          initialDelaySeconds: 30
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
  - metadata:
      name: neo4j-logs
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j-service
  namespace: iwdda
spec:
  selector:
    app: neo4j
  ports:
  - port: 7687
    targetPort: 7687
    name: bolt
  - port: 7474
    targetPort: 7474
    name: http
  clusterIP: None
  type: ClusterIP
```

#### 训练服务 Job
```yaml
# deploy/k8s/training-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: training-job
  namespace: iwdda
spec:
  template:
    spec:
      containers:
      - name: training
        image: iwdda/training:v1.0.0
        command: ["python", "scripts/training/train.py"]
        env:
        - name: MINIO_ENDPOINT
          value: "minio-service:9000"
        envFrom:
        - configMapRef:
            name: iwdda-config
        - secretRef:
            name: iwdda-secret
        resources:
          requests:
            cpu: "8"
            memory: "32Gi"
            nvidia.com/gpu: "8"
          limits:
            cpu: "16"
            memory: "64Gi"
            nvidia.com/gpu: "8"
        volumeMounts:
        - name: dataset
          mountPath: /datasets
        - name: runs
          mountPath: /runs
      volumes:
      - name: dataset
        persistentVolumeClaim:
          claimName: dataset-pvc
      - name: runs
        persistentVolumeClaim:
          claimName: runs-pvc
      restartPolicy: OnFailure
  backoffLimit: 3
```

#### Ingress 配置
```yaml
# deploy/k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iwdda-ingress
  namespace: iwdda
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.iwdda.example.com
    - web.iwdda.example.com
    secretName: iwdda-tls
  rules:
  - host: api.iwdda.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
  - host: web.iwdda.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 7860
```

---

## 3. 边缘端部署

### 3.1 边缘设备支持

**支持的设备**:
| 设备 | CPU | GPU | 内存 | 存储 | 适用场景 |
|------|-----|-----|------|------|---------|
| **NVIDIA Jetson Nano** | 4 核 ARM | 128-core Maxwell | 4GB | 16GB+ | 田间实时检测 |
| **NVIDIA Jetson Orin Nano** | 6 核 ARM | 1024-core Ampere | 8GB | 64GB+ | 高精度实时检测 |
| **Raspberry Pi 4B** | 4 核 ARM | Mali-G31 | 4/8GB | 32GB+ | 轻量级检测 |
| **Intel NUC** | 4-8 核 x86 | Iris Xe | 16-32GB | 512GB+ | 边缘服务器 |

### 3.2 Jetson Nano 部署

**系统要求**:
- JetPack 4.6+ (Ubuntu 18.04)
- CUDA 10.2+
- cuDNN 8.2+
- TensorRT 8.2+

**部署步骤**:

#### 1. 系统准备
```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3-pip python3-venv git wget

# 创建虚拟环境
python3 -m venv /opt/iwdda
source /opt/iwdda/bin/activate

# 升级 pip
pip install --upgrade pip
```

#### 2. 安装深度学习框架
```bash
# 安装 PyTorch (Jetson 预编译版本)
wget https://nvidia.box.com/shared/static/ncgzus5o23ww9y042n5z9rk6vrxnh3wh.whl -O torch-1.10.0-cp36-cp36m-linux_aarch64.whl
pip install numpy torch-1.10.0-cp36-cp36m-linux_aarch64.whl

# 安装 torchvision
pip install torchvision==0.11.1

# 安装其他依赖
pip install ultralytics transformers gradio fastapi
```

#### 3. 部署应用
```bash
# 克隆项目
cd /opt/iwdda
git clone https://github.com/your-repo/WheatAgent.git .

# 安装项目依赖
pip install -e .

# 下载模型 (从云端或本地)
python scripts/download_models.py --edge

# 配置边缘模式
cp configs/wheat_agent.yaml configs/wheat_agent_edge.yaml
# 修改配置：启用量化、降低批次大小
```

#### 4. 配置 systemd 服务
```ini
# /etc/systemd/system/iwdda.service
[Unit]
Description=小麦病害诊断系统边缘服务
After=network.target

[Service]
Type=simple
User=iwdda
Group=iwdda
WorkingDirectory=/opt/iwdda
Environment="PATH=/opt/iwdda/bin"
ExecStart=/opt/iwdda/bin/python run_web.py --config configs/wheat_agent_edge.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable iwdda
sudo systemctl start iwdda

# 查看状态
sudo systemctl status iwdda

# 查看日志
sudo journalctl -u iwdda -f
```

### 3.3 Raspberry Pi 部署

**系统要求**:
- Raspberry Pi OS (64-bit)
- Python 3.9+
- 4GB+ 内存 (推荐 8GB)

**部署步骤**:

#### 1. 系统优化
```bash
# 增加 swap 空间 (推荐 4GB)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# 修改：CONF_SWAPSIZE=4096
sudo dphys-swapfile swapon
sudo dphys-swapfile setup

# 超频 (可选，提升性能)
sudo nano /boot/config.txt
# 添加:
# over_voltage=6
# arm_freq=2000
# gpu_freq=750
```

#### 2. 安装依赖
```bash
# 系统依赖
sudo apt install -y python3-pip python3-venv libatlas-base-dev

# 虚拟环境
python3 -m venv /opt/iwdda
source /opt/iwdda/bin/activate

# 安装 PyTorch (ARM 优化版本)
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# 安装其他依赖
pip install ultralytics transformers gradio
```

#### 3. 模型优化
```bash
# 导出 ONNX 模型 (CPU 优化)
python scripts/deployment/export_onnx.py \
  --model models/wheat_disease_v10_yolov8s/weights/best.pt \
  --output models/wheat_disease_v10_yolov8s.onnx \
  --opset 11 \
  --simplify

# 使用 OpenVINO 优化 (Intel 设备)
pip install openvino-dev
mo --input_model models/wheat_disease_v10_yolov8s.onnx \
  --output_dir models/openvino/
```

### 3.4 边缘优化配置

**边缘优化配置文件**:
```yaml
# configs/edge_optimization.yaml
edge:
  # 设备配置
  device: "cuda"  # cuda / cpu / mps
  device_id: 0
  
  # 模型量化
  quantization:
    vision:
      enabled: true
      precision: "fp16"  # fp16 / int8
    cognition:
      enabled: true
      precision: "int4"  # int4 / int8
  
  # 模型剪枝
  pruning:
    enabled: true
    sparsity: 0.3  # 30% 稀疏度
  
  # 推理优化
  inference:
    batch_size: 1
    threads: 4
    inter_op_threads: 2
    intra_op_threads: 4
  
  # 缓存策略
  cache:
    enabled: true
    max_size: 500  # 最多缓存 500 张图像
    ttl: 1800  # 30 分钟过期
  
  # 内存管理
  memory:
    max_memory: 3.5  # 最大显存使用 (GB)
    garbage_collection: true
    gc_interval: 300  # 5 分钟一次 GC
  
  # 性能监控
  monitoring:
    enabled: true
    log_interval: 60  # 60 秒记录一次
    metrics:
      - latency
      - fps
      - memory_usage
      - temperature
```

**边缘推理引擎**:
```python
# src/web/backend/edge_inference.py
class EdgeInferenceEngine:
    """边缘推理引擎"""
    
    def __init__(self, config_path: str):
        """初始化边缘推理引擎"""
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        self.cache = LRUCache(max_size=self.config['cache']['max_size'])
        self.monitor = PerformanceMonitor()
    
    def _load_model(self) -> nn.Module:
        """加载优化后的模型"""
        # 1. 尝试加载 TensorRT 引擎
        if self.config['device'] == 'cuda':
            try:
                return self._load_tensorrt()
            except Exception:
                pass
        
        # 2. 尝试加载 ONNX Runtime
        try:
            return self._load_onnx()
        except Exception:
            pass
        
        # 3. 回退到 PyTorch
        return self._load_pytorch()
    
    def _load_tensorrt(self) -> TRTEngine:
        """加载 TensorRT 引擎"""
        engine_path = self.config['model']['tensorrt_path']
        return TRTEngine(engine_path)
    
    def _load_onnx(self) -> ONNXRuntime:
        """加载 ONNX Runtime"""
        model_path = self.config['model']['onnx_path']
        session_options = onnxruntime.SessionOptions()
        session_options.graph_optimization_level = \
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        if self.config['device'] == 'cuda':
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        else:
            providers = ['CPUExecutionProvider']
        
        return onnxruntime.InferenceSession(
            model_path, 
            sess_options=session_options,
            providers=providers
        )
    
    def _load_pytorch(self) -> TorchModel:
        """加载 PyTorch 模型"""
        model_path = self.config['model']['pytorch_path']
        model = torch.jit.load(model_path)
        
        # 应用量化
        if self.config['quantization']['vision']['enabled']:
            model = torch.quantization.quantize_dynamic(
                model, 
                {torch.nn.Linear}, 
                dtype=torch.qint8
            )
        
        return model
    
    def infer(self, image: Image) -> DetectionResult:
        """执行推理"""
        # 1. 检查缓存
        image_hash = self._compute_hash(image)
        if image_hash in self.cache:
            return self.cache[image_hash]
        
        # 2. 执行推理
        with self.monitor.track('inference'):
            result = self._run_inference(image)
        
        # 3. 缓存结果
        self.cache[image_hash] = result
        
        # 4. 记录性能指标
        self.monitor.record('fps', 1.0 / self.monitor.last_latency)
        
        return result
    
    def _run_inference(self, image: Image) -> DetectionResult:
        """运行推理"""
        # 预处理
        input_tensor = self._preprocess(image)
        
        # 推理
        if isinstance(self.model, TRTEngine):
            outputs = self.model.infer(input_tensor)
        elif isinstance(self.model, onnxruntime.InferenceSession):
            outputs = self.model.run(None, {'input': input_tensor})[0]
        else:
            with torch.no_grad():
                outputs = self.model(input_tensor)
        
        # 后处理
        result = self._postprocess(outputs)
        
        return result
```

---

## 4. 云边协同配置

### 4.1 模型同步

**模型版本管理**:
```python
# src/web/backend/model_sync.py
class ModelSyncManager:
    """模型同步管理器"""
    
    def __init__(self, cloud_url: str, edge_id: str):
        self.cloud_url = cloud_url
        self.edge_id = edge_id
        self.local_models = {}
        self.remote_models = {}
    
    def sync_models(self):
        """同步模型"""
        # 1. 获取云端模型列表
        self.remote_models = self._fetch_remote_models()
        
        # 2. 比较版本
        updates = self._compare_versions()
        
        # 3. 下载更新
        for model_name, version in updates:
            self._download_model(model_name, version)
        
        # 4. 验证完整性
        self._verify_models()
    
    def _fetch_remote_models(self) -> Dict:
        """获取云端模型列表"""
        response = requests.get(
            f"{self.cloud_url}/api/v1/models",
            headers={"Edge-ID": self.edge_id}
        )
        return response.json()
    
    def _compare_versions(self) -> List[Tuple[str, str]]:
        """比较版本，返回需要更新的模型"""
        updates = []
        for model_name, remote_version in self.remote_models.items():
            local_version = self.local_models.get(model_name, "0.0.0")
            if self._is_newer(remote_version, local_version):
                updates.append((model_name, remote_version))
        return updates
    
    def _download_model(self, model_name: str, version: str):
        """下载模型 (支持断点续传)"""
        model_url = f"{self.cloud_url}/api/v1/models/{model_name}/{version}"
        local_path = f"models/{model_name}/{version}"
        
        # 检查已下载部分
        start_pos = 0
        if os.path.exists(local_path):
            start_pos = os.path.getsize(local_path)
        
        # 下载
        headers = {"Range": f"bytes={start_pos}-"}
        response = requests.get(model_url, headers=headers, stream=True)
        
        with open(local_path, 'ab') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
```

### 4.2 数据同步

**边缘数据上传**:
```python
# src/web/backend/data_sync.py
class DataSyncManager:
    """数据同步管理器"""
    
    def __init__(self, cloud_url: str, edge_id: str):
        self.cloud_url = cloud_url
        self.edge_id = edge_id
        self.upload_queue = Queue()
    
    def upload_data(self, data_type: str, data: Dict):
        """上传数据到云端"""
        # 1. 数据脱敏
        sanitized_data = self._sanitize_data(data)
        
        # 2. 添加到上传队列
        self.upload_queue.put({
            'type': data_type,
            'data': sanitized_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # 3. 异步上传
        threading.Thread(target=self._upload_worker, daemon=True).start()
    
    def _sanitize_data(self, data: Dict) -> Dict:
        """数据脱敏"""
        # 移除敏感信息
        if 'location' in data:
            data['location'] = self._blur_location(data['location'])
        
        # 压缩图像
        if 'image' in data:
            data['image'] = self._compress_image(data['image'])
        
        return data
    
    def _upload_worker(self):
        """上传工作线程"""
        while not self.upload_queue.empty():
            item = self.upload_queue.get()
            
            try:
                # 上传到云端
                response = requests.post(
                    f"{self.cloud_url}/api/v1/data/upload",
                    json=item,
                    headers={"Edge-ID": self.edge_id}
                )
                
                if response.status_code == 200:
                    # 上传成功，从队列移除
                    self.upload_queue.task_done()
                else:
                    # 上传失败，稍后重试
                    time.sleep(60)
            
            except Exception as e:
                logging.error(f"Upload failed: {e}")
                time.sleep(60)
```

### 4.3 配置管理

**边缘配置文件**:
```yaml
# configs/edge_config.yaml
edge:
  # 设备信息
  device_id: "edge-001"
  device_type: "jetson_nano"
  location: "field_a"
  
  # 云端连接
  cloud:
    url: "https://api.iwdda.example.com"
    api_key: "your_edge_api_key"
    sync_interval: 300  # 5 分钟同步一次
  
  # 本地配置
  local:
    model_cache_dir: "/opt/iwdda/models"
    data_cache_dir: "/opt/iwdda/data"
    log_dir: "/var/log/iwdda"
  
  # 同步策略
  sync:
    models:
      auto_update: true
      update_hour: 3  # 凌晨 3 点更新
    data:
      upload_enabled: true
      upload_interval: 60  # 60 秒上传一次
      batch_size: 10
    knowledge:
      sync_enabled: true
      sync_interval: 3600  # 1 小时同步一次
  
  # 离线模式
  offline:
    enabled: true
    max_offline_days: 7  # 最多离线 7 天
    fallback_model: "models/wheat_disease_v10_yolov8s/weights/best.pt"
```

---

## 5. 监控与运维

### 5.1 监控指标

**系统监控**:
```yaml
# deploy/monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'iwdda-api'
    static_configs:
      - targets: ['api-service:8000']
    metrics_path: '/metrics'
  
  - job_name: 'iwdda-edge'
    static_configs:
      - targets: ['edge-001:9100', 'edge-002:9100']
    metrics_path: '/metrics'
  
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j-service:7474']
```

**Grafana 仪表盘**:
```json
{
  "dashboard": {
    "title": "小麦病害诊断系统监控",
    "panels": [
      {
        "title": "API 请求延迟",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "GPU 使用率",
        "targets": [
          {
            "expr": "nvidia_smi_gpu_utilization"
          }
        ]
      },
      {
        "title": "边缘设备在线状态",
        "targets": [
          {
            "expr": "edge_device_online"
          }
        ]
      }
    ]
  }
}
```

### 5.2 日志管理

**日志收集**:
```yaml
# deploy/logging/fluentd.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: iwdda
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      <parse>
        @type json
      </parse>
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
    </filter>
    
    <match **>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix iwdda-logs
    </match>
```

---

## 6. 故障排除

### 6.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| **边缘设备离线** | 网络故障、电源问题 | 检查网络连接、重启设备 |
| **模型加载失败** | 显存不足、版本不兼容 | 降低批次大小、更新驱动 |
| **推理速度慢** | CPU/GPU 负载高 | 优化模型、减少并发 |
| **数据同步失败** | 网络不稳定、存储空间不足 | 检查网络、清理存储 |

### 6.2 诊断命令

```bash
# 检查 Docker 容器状态
docker ps -a

# 查看 Kubernetes Pod 状态
kubectl get pods -n iwdda

# 查看服务日志
kubectl logs -f api-service-xxx -n iwdda

# 检查 GPU 状态
nvidia-smi

# 检查 Neo4j 状态
cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n)"

# 检查边缘设备连接
curl https://api.iwdda.example.com/api/v1/health
```

---

## 7. 总结

小麦病害诊断系统云边协同部署方案提供了灵活的部署选项:

1. **云端部署**: 支持 Docker Compose 和 Kubernetes，适合大规模生产环境
2. **边缘部署**: 优化 Jetson Nano 和 Raspberry Pi，适合田间实时检测
3. **云边协同**: 模型同步、数据同步、配置管理，实现云端和边缘的无缝协作
4. **监控运维**: 完善的监控指标和日志管理，确保系统稳定运行

未来，我们将继续优化:
- 边缘设备支持 (更多硬件平台)
- 自动扩缩容 (基于负载自动调整资源)
- 联邦学习 (多边缘设备协作训练)
- 5G 集成 (利用 5G 低延迟特性)

---

*文档生成时间：2026-03-09*  
*版本：v1.0*
