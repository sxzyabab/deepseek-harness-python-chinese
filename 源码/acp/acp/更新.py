"""由已提交 DSH 会话事件派生的标准 ACP 更新。"""
import json
from .内容 import 助手块转ACP

__all__=['助手更新列表','工具调用更新','工具结果更新']

def 助手更新列表(上下文,会话,事件):
    """按块序转换一条已提交助手消息及其上下文用量。"""
    更新=[]
    消息=事件['data']['message']
    内容=消息['content'] if 'content' in 消息 else []
    for 块 in 内容:
        if ('type' in 块) and 块['type']=='reasoning':
            文本=块['text'] if 'text' in 块 else ''
            if len(文本)>0:
                更新.append({
                    'sessionUpdate':'agent_thought_chunk',
                    'messageId':消息['id'],
                    'content':{'type':'text','text':文本},
                })
            continue
        转换=助手块转ACP(上下文,块)
        if 转换 is not None:
            更新.append({
                'sessionUpdate':'agent_message_chunk',
                'messageId':消息['id'],
                'content':转换,
            })
    用量=用量更新(上下文,会话,事件)
    if 用量 is not None:
        更新.append(用量)
    return 更新

def 工具调用更新(事件):
    """从耐久调用事实开始一次通用 ACP 工具生命周期。"""
    数据=事件['data']
    return {
        'sessionUpdate':'tool_call',
        'toolCallId':数据['callId'],
        'title':数据['name'],
        'kind':'other',
        'status':'in_progress',
        'rawInput':解析工具参数(数据['arguments']),
    }

def 工具结果更新(上下文,事件):
    """用已提交的面向模型结果结束一次通用 ACP 工具生命周期。"""
    消息=事件['data']['message']
    内容=[]
    for 块 in 消息.get('content') or []:
        转换=助手块转ACP(上下文,块)
        if 转换 is not None:
            内容.append({'type':'content','content':转换})
    return {
        'sessionUpdate':'tool_call_update',
        'toolCallId':消息['toolCallId'],
        'status':'failed' if 消息.get('isError') is True else 'completed',
        'content':内容,
    }

def 用量更新(上下文,会话,事件):
    """仅当 DSH 同时有用量与容量事实时报告当前上下文占用。"""
    用量=事件['data'].get('usage')
    if 用量 is None:
        return None
    上下文信息=会话.请求上下文()
    容量=None if 上下文信息 is None else (上下文信息['contextWindow'] if 'contextWindow' in 上下文信息 else None)
    计量=上下文.获取服务('tokenMeter')
    if 容量 is None or 计量 is None:
        return None
    return {
        'sessionUpdate':'usage_update',
        'used':计量.测量(会话)['totalTokens'],
        'size':容量,
    }

def 解析工具参数(值):
    """畸形模型输出保留为不透明输入，不丢调用更新。"""
    try:
        return json.loads(值)
    except Exception:
        return 值
