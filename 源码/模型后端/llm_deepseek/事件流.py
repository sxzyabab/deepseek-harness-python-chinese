"""SSE 分帧；JSON 错误仍是提供方失败。"""
import json
from ..llm import 大模型错误
from .回放 import 对象
from .传输 import 提供方错误

__all__=['解析sse']

def 解析sse(响应,活动):
    """解码完整 SSE 帧，未终止尾不当成事件。"""
    数据行=[]
    事件类型=None
    for 原始 in 响应.iter_lines(decode_unicode=True):
        活动()
        if 原始 is None:
            continue
        行=原始
        if 行.startswith(':'):
            活动()
            continue
        if 行=='':
            if len(数据行)>0:
                try:
                    原始对象=json.loads('\n'.join(数据行))
                except Exception:
                    raise 大模型错误('DeepSeek Messages SSE contains invalid JSON','MALFORMED_RESPONSE')
                事件=对象(原始对象)
                类型=事件.get('type')
                if not isinstance(类型,str) or (事件类型 is not None and 事件类型!=类型):
                    raise 大模型错误('DeepSeek Messages SSE event type mismatch','MALFORMED_RESPONSE')
                if 类型=='error':
                    raise 提供方错误(事件,None)
                yield 事件
            数据行=[]
            事件类型=None
            continue
        if 行.startswith('event:'):
            事件类型=行[6:].lstrip()
        elif 行.startswith('data:'):
            数据行.append(行[5:].lstrip())
    if len(数据行)>0:
        raise 大模型错误('DeepSeek Messages SSE contains invalid JSON','MALFORMED_RESPONSE')
