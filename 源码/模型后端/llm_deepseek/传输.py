"""把 HTTP 与带内 Messages 错误归一成提供方中立失败。"""
import math,re,time
from ..llm import 大模型错误,是否上下文窗口超出错误,是否配额超出错误
from ..llm.标识构造 import 提供方请求标识

__all__=['提供方错误详情','提供方错误']

数字延迟=re.compile(r'^\d+(?:\.\d+)?$',re.ASCII)

def 提供方错误详情(原始):
    """只读 Files 有界恢复用到的提供方错误字段。"""
    错误=原始['error'] if isinstance(原始,dict) and 'error' in 原始 else None
    if not isinstance(错误,dict):
        return ''
    段=[]
    for 键 in ('code','type','message'):
        值=错误[键] if 键 in 错误 else None
        if isinstance(值,str):
            段.append(值)
    return ' '.join(段)

def 取头(头,名):
    """大小写不敏感取头。"""
    if 头 is None:
        return None
    if hasattr(头,'get'):
        值=头.get(名)
        if 值 is not None:
            return 值
        for 键 in 头.keys() if hasattr(头,'keys') else []:
            if str(键).lower()==名.lower():
                return 头[键]
    return None

def 提供方错误(原始,状态,头=None):
    """分类提供方错误，不信任任意响应字段。"""
    信封=原始 if isinstance(原始,dict) else {}
    错误=信封['error'] if isinstance(信封.get('error'),dict) else {}
    消息=错误['message'] if isinstance(错误.get('message'),str) else 'DeepSeek Messages request failed ('+(str(状态) if 状态 is not None else 'stream error')+')'
    类型=错误['type'] if isinstance(错误.get('type'),str) else ''
    码字段=错误['code'] if isinstance(错误.get('code'),str) else ''
    详情=类型+' '+码字段+' '+消息
    if 状态==401 or 状态==403 or 类型 in ('authentication_error','permission_error'):
        码='AUTH'
    elif 是否配额超出错误(详情) or 状态==402:
        码='QUOTA'
    elif 状态==429 or 类型=='rate_limit_error':
        码='RATE_LIMIT'
    elif 是否上下文窗口超出错误(详情):
        码='CONTEXT_WINDOW_EXCEEDED'
    elif 状态==400 or 状态==413 or 类型=='invalid_request_error':
        码='INVALID_REQUEST'
    elif (状态 is not None and 状态>=500) or 类型 in ('api_error','overloaded_error'):
        码='SERVER'
    else:
        码='SERVER' if 状态 is None else 'HTTP_'+str(状态)
    重试=取头(头,'retry-after')
    if 重试 is None:
        延迟=float('nan')
    elif 数字延迟.search(str(重试)) is not None:
        延迟=float(重试)*1000
    else:
        延迟=time.mktime(time.strptime(str(重试),'%a, %d %b %Y %H:%M:%S GMT'))*1000-time.time()*1000
    请求号=取头(头,'request-id') or 取头(头,'x-request-id') or 取头(头,'x-deepseek-request-id')
    选项={}
    if 状态 is not None:
        选项['status']=状态
    if 请求号:
        选项['requestId']=提供方请求标识(请求号)
    if math.isfinite(延迟) and 延迟>0:
        选项['providerRetryAfterMs']=延迟
    return 大模型错误(消息,码,选项)
