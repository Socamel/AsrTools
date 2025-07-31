 # ASR API 服务

生产环境视频转录API服务，支持Make.com和Airtable集成。

## 文件说明

- `production_api.py` - 生产环境API服务主文件
- `app.py` - 开发环境API服务（简化版）
- `requirements.txt` - Python依赖
- `deploy.sh` - 部署脚本
- `gunicorn_config.py` - Gunicorn配置
- `asr-api.service` - systemd服务配置
- `nginx_asr_api.conf` - Nginx配置
- `bk_asr/` - ASR引擎模块

## 快速部署

```bash
# 1. 上传文件到VPS
# 2. 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 3. 修改域名
# 编辑 /etc/nginx/sites-available/asr-api
# 将 your-domain.com 替换为实际域名

# 4. 重启服务
systemctl restart asr-api
systemctl restart nginx
```

## API使用

```bash
# 转录视频
curl -X POST http://your-domain.com/transcribe \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'

# 健康检查
curl http://your-domain.com/health

# API文档
curl http://your-domain.com/
```

## 响应格式

```json
{
  "success": true,
  "transcript": "转录的文本内容...",
  "transcript_srt": "SRT格式字幕...",
  "segments_count": 10,
  "total_duration": 120.5,
  "processing_time": 45.2,
  "video_url": "https://example.com/video.mp4",
  "timestamp": "2024-01-01T12:00:00",
  "message": "转录成功"
}
```

## Make.com配置

1. **HTTP请求**:
   - URL: `http://your-domain.com/transcribe`
   - Method: POST
   - Body: `{"video_url": "{{video_url_from_airtable}}"}`

2. **响应处理**:
   - 成功: `{{transcript}}`
   - 失败: `{{error}}`

## 服务管理

```bash
# 查看状态
systemctl status asr-api

# 重启服务
systemctl restart asr-api

# 查看日志
journalctl -u asr-api -f

# 查看应用日志
tail -f /var/log/asr-api/asr_api.log
```

## 开发环境

如需在开发环境运行，使用简化版本：

```bash
pip install flask requests
python app.py
```
```

### 5. example.py
```python
from bk_asr import JianYingASR


if __name__ == '__main__':
    audio_file = "resources/test.mp3"
    asr = JianYingASR(audio_file)
    result = asr.run()
    result.to_srt()
    print(result.to_srt())
```

创建完这些文件后，您的项目就完整了，可以正常部署和使用！