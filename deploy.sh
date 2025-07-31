 #!/bin/bash

echo "部署ASR API服务..."

# 安装依赖
apt update
apt install -y python3 python3-pip nginx ffmpeg

# 创建应用目录
mkdir -p /var/www/asr-api
cd /var/www/asr-api

# 安装Python依赖
pip3 install flask requests gunicorn

# 创建Nginx配置
cat > /etc/nginx/sites-available/asr-api << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 禁用缓冲
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/asr-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 创建systemd服务
cat > /etc/systemd/system/asr-api.service << 'EOF'
[Unit]
Description=ASR API Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/asr-api
ExecStart=/usr/local/bin/gunicorn -c gunicorn_config.py production_api:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log /tmp /var/www/asr-api

# 资源限制
LimitNOFILE=65536
MemoryMax=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF

# 创建日志目录
mkdir -p /var/log/asr-api
chown -R www-data:www-data /var/log/asr-api

# 启动服务
systemctl daemon-reload
systemctl enable asr-api
systemctl start asr-api
systemctl restart nginx

echo "部署完成!"
echo "API地址: http://your-domain.com/transcribe"
echo "健康检查: http://your-domain.com/health"
echo ""
echo "请记得修改域名配置:"
echo "nano /etc/nginx/sites-available/asr-api"