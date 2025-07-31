 from .JianYingASR import JianYingASR

__all__ = ["JianYingASR"]


def transcribe(audio_file, platform="JianYingASR"):
    """转录音频文件
    
    Args:
        audio_file: 音频文件路径
        platform: ASR平台，目前只支持JianYingASR
    
    Returns:
        ASRData对象
    """
    if platform not in __all__:
        raise ValueError(f"不支持的平台: {platform}，目前只支持: {__all__}")
    
    asr = globals()[platform](audio_file)
    return asr.run()