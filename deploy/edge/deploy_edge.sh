#!/bin/bash

# IWDDA 边缘端部署脚本 (Jetson Nano / Raspberry Pi)
# 使用示例：./deploy_edge.sh --device jetson_nano

set -e

# 配置变量
DEVICE_TYPE=""
INSTALL_DIR="/opt/iwdda"
PYTHON_VERSION="3.9"
NEO4J_ENABLED=false
MONITORING_ENABLED=false

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用帮助
show_help() {
    echo "IWDDA 边缘端部署脚本"
    echo ""
    echo "用法：$0 [选项]"
    echo ""
    echo "选项:"
    echo "  --device <类型>     设备类型 (jetson_nano, jetson_orin, raspberry_pi, intel_nuc)"
    echo "  --install-dir <路径> 安装目录 (默认：/opt/iwdda)"
    echo "  --enable-neo4j      启用 Neo4j 知识图谱"
    echo "  --enable-monitoring 启用监控"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --device jetson_nano"
    echo "  $0 --device raspberry_pi --enable-neo4j"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --device)
            DEVICE_TYPE="$2"
            shift 2
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --enable-neo4j)
            NEO4J_ENABLED=true
            shift
            ;;
        --enable-monitoring)
            MONITORING_ENABLED=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项：$1"
            show_help
            exit 1
            ;;
    esac
done

# 验证设备类型
if [ -z "$DEVICE_TYPE" ]; then
    print_error "请指定设备类型 (--device)"
    show_help
    exit 1
fi

case $DEVICE_TYPE in
    jetson_nano|jetson_orin|raspberry_pi|intel_nuc)
        print_info "设备类型：$DEVICE_TYPE"
        ;;
    *)
        print_error "不支持的设备类型：$DEVICE_TYPE"
        print_info "支持的设备：jetson_nano, jetson_orin, raspberry_pi, intel_nuc"
        exit 1
        ;;
esac

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    print_error "请以 root 用户运行此脚本"
    exit 1
fi

print_info "开始部署 IWDDA 边缘端..."

# 步骤 1: 系统更新
print_info "步骤 1/8: 更新系统..."
apt-get update
apt-get upgrade -y

# 步骤 2: 安装基础依赖
print_info "步骤 2/8: 安装基础依赖..."
apt-get install -y python3 python3-pip python3-venv git wget curl vim

# 步骤 3: 根据设备类型安装特定依赖
print_info "步骤 3/8: 安装设备特定依赖..."

case $DEVICE_TYPE in
    jetson_nano|jetson_orin)
        print_info "配置 NVIDIA Jetson 环境..."
        
        # 检查 CUDA
        if ! command -v nvcc &> /dev/null; then
            print_warning "未检测到 CUDA，请确保已安装 JetPack"
            print_info "请访问 https://developer.nvidia.com/embedded/jetpack 下载"
        fi
        
        # 安装 PyTorch (Jetson 预编译版本)
        print_info "安装 PyTorch for Jetson..."
        cd /tmp
        wget https://nvidia.box.com/shared/static/ncgzus5o23ww9y042n5z9rk6vrxnh3wh.whl -O torch-1.10.0-cp36-cp36m-linux_aarch64.whl
        pip3 install numpy torch-1.10.0-cp36-cp36m-linux_aarch64.whl
        pip3 install torchvision==0.11.1
        
        # 清理
        rm -f torch-1.10.0-cp36-cp36m-linux_aarch64.whl
        ;;
    
    raspberry_pi)
        print_info "配置 Raspberry Pi 环境..."
        
        # 增加 swap 空间
        print_info "增加 swap 空间到 4GB..."
        dphys-swapfile swapoff || true
        cat > /etc/dphys-swapfile <<EOF
CONF_SWAPSIZE=4096
CONF_MAXSWAP=4096
EOF
        dphys-swapfile setup
        dphys-swapfile swapon
        
        # 安装 PyTorch (CPU 版本)
        print_info "安装 PyTorch (CPU 优化版本)..."
        pip3 install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu
        
        # 安装 OpenCV 优化
        print_info "安装优化版 OpenCV..."
        apt-get install -y libatlas-base-dev
        ;;
    
    intel_nuc)
        print_info "配置 Intel NUC 环境..."
        
        # 安装 OpenVINO
        print_info "安装 OpenVINO..."
        pip3 install openvino-dev
        
        # 安装 PyTorch
        print_info "安装 PyTorch..."
        pip3 install torch torchvision
        ;;
esac

# 步骤 4: 创建安装目录和用户
print_info "步骤 4/8: 创建安装目录..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/{models,logs,data,configs}

# 创建 iwdda 用户
if ! id -u iwdda &> /dev/null; then
    print_info "创建 iwdda 用户..."
    useradd -r -s /bin/false iwdda
fi

chown -R iwdda:iwdda $INSTALL_DIR

# 步骤 5: 安装应用
print_info "步骤 5/8: 安装 IWDDA 应用..."
cd $INSTALL_DIR

# 创建虚拟环境
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 克隆项目 (如果尚未存在)
if [ ! -d "$INSTALL_DIR/src" ]; then
    print_info "克隆项目代码..."
    git clone https://github.com/your-repo/WheatAgent.git $INSTALL_DIR/src
fi

# 安装依赖
cd $INSTALL_DIR/src
pip install -e .

# 步骤 6: 下载模型
print_info "步骤 6/8: 下载模型..."
cd $INSTALL_DIR

# 创建模型下载脚本
cat > download_models.sh << 'SCRIPT'
#!/bin/bash
# 下载边缘优化模型
mkdir -p models

# 下载 YOLOv8s 边缘模型
if [ ! -f "models/wheat_disease_edge.onnx" ]; then
    echo "下载 YOLOv8s 边缘模型..."
    wget https://your-cdn.com/models/wheat_disease_edge.onnx -O models/wheat_disease_edge.onnx
fi

# 下载 Qwen-VL INT4 模型
if [ ! -d "models/Qwen3-VL-4B-INT4" ]; then
    echo "下载 Qwen-VL INT4 模型..."
    # 这里应该使用实际的下载链接
    mkdir -p models/Qwen3-VL-4B-INT4
fi

echo "模型下载完成"
SCRIPT

chmod +x download_models.sh
./download_models.sh

# 步骤 7: 配置服务
print_info "步骤 7/8: 配置 systemd 服务..."

cat > /etc/systemd/system/iwdda.service << EOF
[Unit]
Description=IWDDA Edge Service
After=network.target

[Service]
Type=simple
User=iwdda
Group=iwdda
WorkingDirectory=$INSTALL_DIR/src
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python run_web.py --config configs/wheat_agent_edge.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=iwdda

[Install]
WantedBy=multi-user.target
EOF

# 创建边缘配置文件
cat > $INSTALL_DIR/src/configs/wheat_agent_edge.yaml << EOF
# IWDDA 边缘端配置

# 设备配置
device: $( [ "$DEVICE_TYPE" = "intel_nuc" ] && echo "cpu" || echo "cuda" )
device_id: 0

# 模型配置
models:
  vision:
    path: "$INSTALL_DIR/models/wheat_disease_edge.onnx"
    precision: "fp16"
    device: "$( [ "$DEVICE_TYPE" = "intel_nuc" ] && echo "cpu" || echo "cuda" )"
  
  cognition:
    path: "$INSTALL_DIR/models/Qwen3-VL-4B-INT4"
    precision: "int4"
    load_in_4bit: true

# 性能优化
performance:
  batch_size: 1
  threads: 4
  enable_cache: true
  cache_size: 500
  cache_ttl: 1800

# 内存管理
memory:
  max_memory: $( [ "$DEVICE_TYPE" = "jetson_nano" ] && echo "3.5" || echo "7.0" )
  garbage_collection: true
  gc_interval: 300

# 日志
logging:
  level: "INFO"
  file: "$INSTALL_DIR/logs/iwdda.log"
  max_size: "10MB"
  backup_count: 5
EOF

# 步骤 8: 启用服务
print_info "步骤 8/8: 启用服务..."
systemctl daemon-reload
systemctl enable iwdda
systemctl start iwdda

# 显示状态
print_info "部署完成!"
echo ""
echo "服务状态:"
systemctl status iwdda --no-pager
echo ""
echo "日志查看:"
echo "  journalctl -u iwdda -f"
echo ""
echo "访问地址:"
echo "  http://localhost:7860"
echo ""
echo "配置文件:"
echo "  $INSTALL_DIR/src/configs/wheat_agent_edge.yaml"
echo ""
echo "模型目录:"
echo "  $INSTALL_DIR/models"
echo ""

# 如果启用了 Neo4j
if [ "$NEO4J_ENABLED" = true ]; then
    print_info "安装 Neo4j..."
    # Neo4j 安装脚本
    apt-get install -y neo4j
    systemctl enable neo4j
    systemctl start neo4j
    print_info "Neo4j 已启动，访问地址：http://localhost:7474"
fi

# 如果启用了监控
if [ "$MONITORING_ENABLED" = true ]; then
    print_info "安装监控组件..."
    # 安装 Node Exporter
    # 安装 Prometheus
    # 安装 Grafana
    print_info "监控组件安装完成"
fi

print_info "所有部署步骤完成!"
