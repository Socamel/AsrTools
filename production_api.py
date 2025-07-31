#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境ASR API服务
支持Make.com集成和Airtable输出
"""

import os
import tempfile
import logging
import requests
import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# 添加bk_asr模块到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bk_asr.JianYingASR import JianYingASR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/asr_api.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# 配置
class Config:
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = '/tmp/asr_uploads'
    CACHE_FOLDER = '/tmp/asr_cache'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'flac', 'm4a'}

app.config.from_object(Config)

# 创建必要的目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CACHE_FOLDER'], exist_ok=True)

def video2audio(input_file: str, output: str = "") -> bool:
    """将视频转换为音频文件"""
    try:
        if not output:
            output = input_file.rsplit(".", 1)[0] + ".mp3"
        
        cmd = [
            'ffmpeg', '-i', input_file, 
            '-vn', '-acodec', 'mp3', '-ar', '16000', '-ac', '1', '-y', output
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logging.info(f"视频转换成功: {input_file} -> {output}")
            return True
        else:
            logging.error(f"视频转换失败: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"视频转换异常: {str(e)}")
        return False

def download_video(url: str, save_path: str) -> bool:
    """从URL下载视频文件"""
    try:
        logging.info(f"开始下载视频: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"视频下载完成: {save_path}")
        return True
    except Exception as e:
        logging.error(f"视频下载失败: {str(e)}")
        return False

def transcribe_video(video_path: str) -> dict:
    """使用剪映ASR转录视频"""
    try:
        # 检查文件类型，如果不是音频则转换
        audio_exts = ['.mp3', '.wav', '.flac', '.m4a']
        if not any(video_path.lower().endswith(ext) for ext in audio_exts):
            temp_audio = video_path.rsplit(".", 1)[0] + ".mp3"
            if not video2audio(video_path, temp_audio):
                raise Exception("音频转换失败")
            audio_path = temp_audio
        else:
            audio_path = video_path
        
        # 使用剪映ASR进行转录
        logging.info(f"开始转录: {audio_path}")
        asr = JianYingASR(audio_path, use_cache=True)
        result = asr.run()
        
        # 获取不同格式的结果
        transcript_text = result.to_txt()
        transcript_srt = result.to_srt()
        
        # 清理临时音频文件
        if audio_path != video_path and os.path.exists(audio_path):
            os.remove(audio_path)
        
        logging.info("转录完成")
        
        return {
            'text': transcript_text,
            'srt': transcript_srt,
            'segments_count': len(result.segments),
            'total_duration': sum(seg.end_time - seg.start_time for seg in result.segments) / 1000
        }
        
    except Exception as e:
        logging.error(f"转录失败: {str(e)}")
        raise

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """转录API端点 - 支持Make.com集成"""
    start_time = time.time()
    
    try:
        # 获取请求数据
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        video_url = data.get('video_url')
        if not video_url:
            return jsonify({
                'success': False,
                'error': '缺少video_url参数',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])
        
        try:
            # 从URL下载视频
            video_filename = secure_filename(f"video_{int(time.time())}.mp4")
            video_path = os.path.join(temp_dir, video_filename)
            
            if not download_video(video_url, video_path):
                return jsonify({
                    'success': False,
                    'error': '视频下载失败',
                    'timestamp': datetime.now().isoformat()
                }), 500
            
            # 转录视频
            result = transcribe_video(video_path)
            
            processing_time = time.time() - start_time
            
            # 返回Make.com友好的格式
            response_data = {
                'success': True,
                'transcript': result['text'],
                'transcript_srt': result['srt'],
                'segments_count': result['segments_count'],
                'total_duration': result['total_duration'],
                'processing_time': round(processing_time, 2),
                'video_url': video_url,
                'timestamp': datetime.now().isoformat(),
                'message': '转录成功'
            }
            
            logging.info(f"转录完成 - 处理时间: {processing_time:.2f}秒")
            return jsonify(response_data)
            
        finally:
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        processing_time = time.time() - start_time
        logging.error(f"API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}',
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'ASR API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    """API文档"""
    return jsonify({
        'name': 'ASR API服务',
        'version': '1.0.0',
        'description': '视频转录API服务，支持Make.com集成',
        'endpoints': {
            'POST /transcribe': {
                'description': '转录视频为文本',
                'request_body': {
                    'video_url': '视频URL地址'
                },
                'response': {
                    'success': '布尔值',
                    'transcript': '转录文本',
                    'transcript_srt': 'SRT格式字幕',
                    'segments_count': '分段数量',
                    'total_duration': '总时长(秒)',
                    'processing_time': '处理时间(秒)',
                    'timestamp': '时间戳'
                }
            },
            'GET /health': '健康检查'
        },
        'make_com_integration': {
            'webhook_url': 'https://your-domain.com/transcribe',
            'method': 'POST',
            'content_type': 'application/json',
            'body': {
                'video_url': '{{video_url_from_airtable}}'
            }
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 检查ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logging.info("ffmpeg已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("ffmpeg未安装")
        sys.exit(1)
    
    # 生产环境配置
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logging.info(f"启动ASR API服务 - {host}:{port}")
    app.run(host=host, port=port, debug=False)