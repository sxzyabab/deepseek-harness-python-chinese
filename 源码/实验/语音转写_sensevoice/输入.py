from ..语音转写.波形 import 校验波形

__all__=['语言表','语音输入错误','校验输入']

语言表=['auto','zh','en','yue','ja','ko']

class 语音输入错误(Exception):
    """原生推理前拒绝的请求；已加载工作者可复用。"""

def 校验输入(音频,语言,最大字节):
    """校验录音后再碰原生识别器。"""
    if 语言 not in 语言表:
        raise 语音输入错误('Unsupported SenseVoice language')
    if len(音频)>最大字节:
        raise 语音输入错误('Speech audio exceeds the worker byte limit')
    try:
        return 校验波形(音频,最大字节/32000)
    except Exception as 错误:
        包装=语音输入错误('Invalid speech WAV')
        包装.__cause__=错误
        raise 包装
