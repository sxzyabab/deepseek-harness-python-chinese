"""翻译 Messages 事件，保住块顺序与累计用量。"""
import json
from ..llm import 大模型错误
from ..llm.标识构造 import 调用标识
from .回放 import 对象,回放状态

__all__=['字符串','翻译']

用量键={
    'input_tokens':'inputTokens',
    'output_tokens':'outputTokens',
    'cache_read_input_tokens':'cacheReadTokens',
    'cache_creation_input_tokens':'cacheWriteTokens',
}

def 字符串(值):
    """从提供方 JSON 解码必填字符串。"""
    if not isinstance(值,str):
        raise 大模型错误('DeepSeek Messages expected a string field','MALFORMED_RESPONSE')
    return 值

def 畸形(细节):
    """流畸形。"""
    raise 大模型错误('DeepSeek Messages stream: '+细节,'MALFORMED_RESPONSE')

def 取下标(事件):
    """块下标。"""
    下标=事件.get('index')
    if (not isinstance(下标,int)) or isinstance(下标,bool) or 下标<0:
        畸形('invalid block index')
    return 下标

def 更新用量(用量,原始):
    """累加用量字段。"""
    字段=对象(原始)
    for 线路,本地 in 用量键.items():
        值=字段.get(线路)
        if 值 is None:
            continue
        if (not isinstance(值,int)) or isinstance(值,bool) or 值<0:
            畸形('invalid '+线路)
        用量[本地]=值

def 开始块(事件,下标):
    """content_block_start。"""
    原生=对象(事件.get('content_block'))
    种类=原生.get('type')
    if 种类=='text':
        内容={'type':'text','text':字符串(原生.get('text'))}
        回放={'type':'text'}
    elif 种类=='thinking':
        内容={'type':'reasoning','text':字符串(原生.get('thinking'))}
        回放={'type':'reasoning'}
        if 原生.get('signature') is not None:
            回放['signature']=字符串(原生.get('signature'))
    elif 种类=='tool_use':
        内容={'type':'tool-call','id':调用标识(字符串(原生.get('id'))),'name':字符串(原生.get('name')),'arguments':json.dumps(对象(原生.get('input')),ensure_ascii=False,separators=(',',':'),allow_nan=False)}
        if not 内容['id'] or not 内容['name']:
            畸形('empty tool identity')
        回放={'type':'tool-call'}
    else:
        raise 大模型错误('DeepSeek Messages does not support response block '+str(种类),'UNSUPPORTED_CONTENT')
    return {'index':下标,'content':内容,'replay':回放,'closed':False,'json':''}

def 增量块(块,原始):
    """content_block_delta。"""
    增量=对象(原始)
    内容=块['content']
    种类=增量.get('type')
    if 种类=='text_delta' and 内容['type']=='text':
        文本=字符串(增量.get('text'))
        内容['text']+=文本
        return {'type':'text-delta','index':块['index'],'text':文本}
    if 种类=='thinking_delta' and 内容['type']=='reasoning':
        文本=字符串(增量.get('thinking'))
        内容['text']+=文本
        return {'type':'reasoning-delta','index':块['index'],'text':文本}
    if 种类=='signature_delta' and 内容['type']=='reasoning':
        块['replay']['signature']=(块['replay'].get('signature') or '')+字符串(增量.get('signature'))
        return None
    if 种类=='input_json_delta' and 内容['type']=='tool-call':
        参数增量=字符串(增量.get('partial_json'))
        块['json']+=参数增量
        return {'type':'tool-call-delta','index':块['index'],'id':内容['id'],'argumentsDelta':参数增量}
    畸形('unsupported delta '+str(种类)+' for '+内容['type'])

def 停止原因(原始):
    """finish reason。"""
    if 原始=='end_turn' or 原始=='stop_sequence':
        return {'kind':'stop'}
    if 原始=='tool_use':
        return {'kind':'tool-calls'}
    if 原始=='max_tokens':
        return {'kind':'max-tokens'}
    畸形('unsupported stop reason '+str(原始))

def 翻译(事件流,模型):
    """把已分帧解码的 SSE 数据译成 Harness 流协议。"""
    块表={}
    用量={'inputTokens':0,'outputTokens':0}
    已开始=False
    原因=None
    for 事件 in 事件流:
        类型=事件.get('type')
        if 类型=='message_start':
            if 已开始:
                畸形('duplicate message_start')
            更新用量(用量,对象(事件.get('message')).get('usage'))
            已开始=True
            continue
        if 类型 not in ('content_block_start','content_block_delta','content_block_stop','message_delta','message_stop'):
            continue
        if not 已开始:
            畸形('event precedes message_start')
        if 类型=='content_block_start':
            线路下标=取下标(事件)
            if 线路下标 in 块表 or 原因 is not None:
                畸形('block starts after settlement or repeats an index')
            块=开始块(事件,len(块表))
            块表[线路下标]=块
            yield {'type':'block-start','index':块['index'],'blockType':块['content']['type']}
            if 块['content']['type']=='text' or 块['content']['type']=='reasoning':
                if 块['content']['text']:
                    yield {'type':'text-delta' if 块['content']['type']=='text' else 'reasoning-delta','index':块['index'],'text':块['content']['text']}
            else:
                yield {'type':'tool-call-delta','index':块['index'],'id':块['content']['id'],'name':块['content']['name'],'argumentsDelta':''}
        elif 类型=='content_block_delta' or 类型=='content_block_stop':
            块=块表.get(取下标(事件))
            if 块 is None or 块['closed']:
                畸形('delta/stop without an open block')
            if 类型=='content_block_delta':
                块结果=增量块(块,事件.get('delta'))
                if 块结果 is not None:
                    yield 块结果
            else:
                块['closed']=True
                if 块['content']['type']=='tool-call' and len(块['json'])>0:
                    块['content']['arguments']=块['json']
                yield {'type':'block-end','index':块['index'],'block':dict(块['content'])}
        elif 类型=='message_delta':
            增量=对象(事件.get('delta'))
            if 增量.get('stop_reason') is not None:
                原因=停止原因(增量.get('stop_reason'))
            if 事件.get('usage') is not None:
                更新用量(用量,事件.get('usage'))
        else:
            if 原因 is None or any(not 块['closed'] for 块 in 块表.values()):
                畸形('message_stop without settled blocks and stop reason')
            if len(块表)==0 and 原因['kind']=='stop':
                raise 大模型错误('DeepSeek Messages returned no content','EMPTY_RESPONSE')
            if 原因['kind']!='max-tokens':
                for 块 in 块表.values():
                    内容=块['content']
                    if 内容['type']!='tool-call':
                        continue
                    try:
                        解析=json.loads(内容['arguments'])
                    except Exception:
                        畸形('tool input is invalid JSON')
                    对象(解析)
            用量['totalTokens']=用量['inputTokens']+用量['outputTokens']+(用量.get('cacheReadTokens') or 0)+(用量.get('cacheWriteTokens') or 0)
            yield {'type':'usage','usage':用量}
            yield {'type':'finish','reason':原因,'replayState':回放状态(模型,[块['replay'] for 块 in 块表.values()])}
            return
    raise 大模型错误('DeepSeek Messages stream ended before message_stop','STREAM_CLOSED')
