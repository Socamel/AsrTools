 # Gunicorn配置文件
import multiprocessing

# 服务器配置
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# 超时配置
timeout = 300  # 5分钟超时
keepalive = 2
graceful_timeout = 30

# 日志配置
accesslog = "/var/log/asr_api_access.log"
errorlog = "/var/log/asr_api_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程配置
preload_app = True
daemon = False

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190