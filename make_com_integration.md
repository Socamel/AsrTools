 # Make.com 集成配置指南

## 场景设置

### 1. 触发器 (Trigger)
- **应用**: Airtable
- **事件**: Watch Records
- **配置**:
  - Base: 选择您的Airtable数据库
  - Table: 包含视频URL的表格
  - 筛选条件: 当新记录添加或特定字段更新时

### 2. 数据获取 (Data Structure)
- **应用**: Airtable
- **操作**: Get a Record
- **配置**:
  - 获取视频URL字段
  - 获取其他相关字段（如标题、描述等）

### 3. HTTP请求 (HTTP)
- **应用**: HTTP
- **操作**: Make an HTTP request
- **配置**:
  ```
  URL: https://your-domain.com/transcribe
  Method: POST
  Headers:
    Content-Type: application/json
  Body (JSON):
  {
    "video_url": "{{video_url_from_airtable}}"
  }
  ```

### 4. 错误处理 (Router)
- **条件**: HTTP响应状态码 != 200
- **分支1**: 成功处理
- **分支2**: 错误处理

### 5. 成功处理分支
- **应用**: Airtable
- **操作**: Update a Record
- **配置**:
  - 更新转录文本字段: `{{transcript}}`
  - 更新处理状态字段: "completed"
  - 更新处理时间字段: `{{processing_time}}`
  - 更新时间戳字段: `{{timestamp}}`

### 6. 错误处理分支
- **应用**: Airtable
- **操作**: Update a Record
- **配置**:
  - 更新处理状态字段: "failed"
  - 更新错误信息字段: `{{error}}`

## Airtable 表格结构建议

| 字段名 | 类型 | 描述 |
|--------|------|------|
| ID | Auto Number | 自动编号 |
| Video URL | URL | 视频URL |
| Title | Single line text | 视频标题 |
| Status | Single select | 处理状态 (pending/completed/failed) |
| Transcript | Long text | 转录文本 |
| SRT Content | Long text | SRT格式字幕 |
| Processing Time | Number | 处理时间(秒) |
| Error Message | Long text | 错误信息 |
| Created Time | Date | 创建时间 |
| Updated Time | Date | 更新时间 |

## 完整Make.com场景示例

```
Airtable (Watch Records) 
    ↓
Airtable (Get a Record)
    ↓
HTTP (POST /transcribe)
    ↓
Router (Check Response)
    ↓
├─ 成功 → Airtable (Update Record - Success)
└─ 失败 → Airtable (Update Record - Error)
```

## 测试步骤

1. **准备测试数据**
   - 在Airtable中添加一条包含视频URL的记录
   - 确保Status字段为"pending"

2. **运行场景**
   - 在Make.com中手动运行场景
   - 检查HTTP请求是否成功

3. **验证结果**
   - 检查Airtable中的记录是否更新
   - 验证转录文本是否正确

## 故障排除

### 常见问题

1. **HTTP请求失败**
   - 检查API服务器是否运行
   - 验证域名和SSL证书
   - 检查防火墙设置

2. **转录失败**
   - 检查视频URL是否可访问
   - 验证视频格式是否支持
   - 查看服务器日志

3. **Airtable更新失败**
   - 检查字段权限设置
   - 验证字段类型匹配
   - 确认API密钥有效

### 日志查看

```bash
# 查看API服务日志
sudo journalctl -u asr-api -f

# 查看Nginx访问日志
sudo tail -f /var/log/nginx/asr_api_access.log

# 查看应用日志
sudo tail -f /var/log/asr-api/asr_api.log
```