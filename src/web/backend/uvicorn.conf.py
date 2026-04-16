"""
Uvicorn 配置文件
优化后端服务性能和稳定性
Windows 兼容版本
"""
import sys
import multiprocessing

# workers 数量：建议 CPU 核心数 * 2 + 1
# Windows 上建议使用单 worker 避免多进程问题
workers = 1 if sys.platform == "win32" else multiprocessing.cpu_count() * 2 + 1

# 绑定地址和端口
host = "0.0.0.0"
port = 8000

# Windows 不支持 uvloop，使用默认事件循环
if sys.platform != "win32":
    loop = "uvloop"
    http = "httptools"
else:
    loop = "asyncio"
    http = "auto"

# 保持连接超时时间（秒）- 增加以避免连接重置
timeout_keep_alive = 60

# 通知超时时间（秒）
timeout_notify = 60

# 请求头大小限制
limit_max_headers = 65536

# 请求体大小限制（字节）- 50MB
limit_max_request_size = 52428800

# 响应体大小限制（字节）- 100MB
limit_max_response_size = 104857600

# 访问日志
accesslog = "-"

# 错误日志
errorlog = "-"

# 日志级别
loglevel = "info"

# 启用重新加载（仅开发环境）
reload = False

# 重新加载延迟
reload_delay = 0.25

# 工作类
worker_class = "uvicorn.workers.UvicornWorker"

# 每个 worker 的连接数
worker_connections = 1000

# 后台任务
backlog = 2048

# 额外的超时配置
# Graceful shutdown timeout
graceful_timeout = 30
