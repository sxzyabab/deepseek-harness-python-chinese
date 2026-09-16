"""翻译消息协议事件，保持块顺序与累计用量。"""
import json#工具 JSON
from ....llm import 大模型错误,调用标识#错误与调用 id
from .回放 import 校验对象,回放状态#对象与信封

__all__=('断言字符串','翻译')#仅中文公开名

用量键={
    'input_tokens':'inputTokens',#输入
    'output_tokens':'outputTokens',#输出
    'cache_read_input_tokens':'cacheReadTokens',#缓存读
    'cache_creation_input_tokens':'cacheWriteTokens',#缓存写
}#线路到本地

内容事件=('content_block_start','content_block_delta','content_block_stop','message_delta','message_stop')#内容事件

def 断言字符串(值):
    """解码提供方 JSON 的必需字符串。"""
    if not isinstance(值,str):#非串
        raise 大模型错误('DeepSeek Messages expected a string field','MALFORMED_RESPONSE')#畸形
    return 值#串

def 畸形(细节):
    """流畸形。"""
    raise 大模型错误('DeepSeek Messages stream: '+细节,'MALFORMED_RESPONSE')#畸形

def 安全整数(值):
    """排除 bool 的非负安全整数。"""
    return (not isinstance(值,bool) and isinstance(值,int) and 值>=0 and abs(值)<=9007199254740991)#安全

def 事件下标(事件):
    """读取块下标。"""
    下标=事件.get('index')#下标
    if not 安全整数(下标):#非法
        return 畸形('invalid block index')#畸形
    return 下标#下标

def 更新用量(用量,原始):
    """把线路用量叠进累计用量。"""
    字段=校验对象(原始)#对象
    for 线路,本地 in 用量键.items():#逐字段
        if 线路 not in 字段:#缺席
            continue#下一项
        值=字段[线路]#值
        if not 安全整数(值):#非法
            return 畸形('invalid '+线路)#畸形
        用量[本地]=值#写入

def 开始块(事件,下标):
    """从 content_block_start 打开一块。"""
    原生=校验对象(事件.get('content_block'))#原生块
    种类=原生.get('type')#种类
    if 种类=='text':#文本
        内容={'type':'text','text':断言字符串(原生.get('text'))}#文本
        回放={'type':'text'}#回放
    elif 种类=='thinking':#思考
        内容={'type':'reasoning','text':断言字符串(原生.get('thinking'))}#推理
        回放={'type':'reasoning'}#回放
        if 原生.get('signature') is not None:#有签名
            回放['signature']=断言字符串(原生.get('signature'))#签名
    elif 种类=='tool_use':#工具
        内容={
            'type':'tool-call',#工具调用
            'id':调用标识(断言字符串(原生.get('id'))),#id
            'name':断言字符串(原生.get('name')),#名
            'arguments':json.dumps(校验对象(原生.get('input')),ensure_ascii=False,separators=(',',':')),#入参
        }#内容
        if not 内容['id'] or not 内容['name']:#空身份
            return 畸形('empty tool identity')#畸形
        回放={'type':'tool-call'}#回放
    else:#其余
        raise 大模型错误('DeepSeek Messages does not support response block '+str(种类),'UNSUPPORTED_CONTENT')#不支持
    return {'index':下标,'content':内容,'replay':回放,'closed':False,'json':''}#打开块

def 增量块(块,原始):
    """把增量叠进打开块。"""
    增量=校验对象(原始)#增量
    内容=块['content']#内容
    种类=增量.get('type')#种类
    if 种类=='text_delta' and 内容['type']=='text':#文本
        文本=断言字符串(增量.get('text'))#文本
        内容['text']+=文本#累积
        return {'type':'text-delta','index':块['index'],'text':文本}#增量
    if 种类=='thinking_delta' and 内容['type']=='reasoning':#思考
        文本=断言字符串(增量.get('thinking'))#文本
        内容['text']+=文本#累积
        return {'type':'reasoning-delta','index':块['index'],'text':文本}#增量
    if 种类=='signature_delta' and 内容['type']=='reasoning':#签名
        块['replay']['signature']=(块['replay'].get('signature') or '')+断言字符串(增量.get('signature'))#累积
        return None#无流块
    if 种类=='input_json_delta' and 内容['type']=='tool-call':#工具 JSON
        片段=断言字符串(增量.get('partial_json'))#片段
        块['json']+=片段#累积
        return {'type':'tool-call-delta','index':块['index'],'id':内容['id'],'argumentsDelta':片段}#增量
    return 畸形('unsupported delta '+str(种类)+' for '+内容['type'])#不支持

def 停止原因(原始):
    """映射 stop_reason。"""
    if 原始=='end_turn' or 原始=='stop_sequence':#正常
        return {'kind':'stop'}#停止
    if 原始=='tool_use':#工具
        return {'kind':'tool-calls'}#工具
    if 原始=='max_tokens':#上限
        return {'kind':'max-tokens'}#上限
    return 畸形('unsupported stop reason '+str(原始))#不支持

def 翻译(事件序列,模型):
    """把已成帧解码事件翻译成 harness 流协议。"""
    块表={}#线路下标→块
    用量={'inputTokens':0,'outputTokens':0}#累计
    已开始=False#message_start
    原因=None#结束原因
    for 事件 in 事件序列:#逐事件
        种类=事件.get('type')#种类
        if 种类=='message_start':#开始
            if 已开始:#重复
                return 畸形('duplicate message_start')#畸形
            更新用量(用量,校验对象(事件.get('message')).get('usage'))#用量
            已开始=True#记下
            continue#下一
        if 种类 not in 内容事件:#其它事件
            continue#放过
        if not 已开始:#未开始
            return 畸形('event precedes message_start')#畸形
        if 种类=='content_block_start':#开块
            线路下标=事件下标(事件)#线路下标
            if 线路下标 in 块表 or 原因 is not None:#重复或已结算
                return 畸形('block starts after settlement or repeats an index')#畸形
            块=开始块(事件,len(块表))#打开
            块表[线路下标]=块#记下
            yield {'type':'block-start','index':块['index'],'blockType':块['content']['type']}#开始
            if 块['content']['type']=='text' or 块['content']['type']=='reasoning':#文本或推理
                if 块['content']['text']:#有初值
                    yield {'type':'text-delta' if 块['content']['type']=='text' else 'reasoning-delta','index':块['index'],'text':块['content']['text']}#初值
            else:#工具
                yield {'type':'tool-call-delta','index':块['index'],'id':块['content']['id'],'name':块['content']['name'],'argumentsDelta':''}#身份
        elif 种类=='content_block_delta' or 种类=='content_block_stop':#增量或关
            块=块表.get(事件下标(事件))#打开块
            if 块 is None or 块['closed']:#无打开块
                return 畸形('delta/stop without an open block')#畸形
            if 种类=='content_block_delta':#增量
                流块=增量块(块,事件.get('delta'))#增量
                if 流块 is not None:#有流块
                    yield 流块#让出
            else:#关闭
                块['closed']=True#关闭
                if 块['content']['type']=='tool-call' and len(块['json'])>0:#有累积 JSON
                    块['content']['arguments']=块['json']#覆盖
                yield {'type':'block-end','index':块['index'],'block':dict(块['content'])}#结束
        elif 种类=='message_delta':#消息增量
            增量=校验对象(事件.get('delta'))#增量
            if 增量.get('stop_reason') is not None:#有原因
                原因=停止原因(增量['stop_reason'])#记下
            if 事件.get('usage') is not None:#有用量
                更新用量(用量,事件['usage'])#叠用量
        else:#message_stop
            if 原因 is None or any(not 块['closed'] for 块 in 块表.values()):#未结算
                return 畸形('message_stop without settled blocks and stop reason')#畸形
            if len(块表)==0 and 原因.get('kind')=='stop':#空响应
                raise 大模型错误('DeepSeek Messages returned no content','EMPTY_RESPONSE')#空
            if 原因.get('kind')!='max-tokens':#非截断则校验工具 JSON
                for 块 in 块表.values():#逐块
                    内容=块['content']#内容
                    if 内容['type']!='tool-call':#非工具
                        continue#下一块
                    try:#JSON
                        解析=json.loads(内容['arguments'])#解码
                    except (json.JSONDecodeError,TypeError,ValueError,UnicodeDecodeError):#非法
                        return 畸形('tool input is invalid JSON')#畸形
                    校验对象(解析)#对象
            用量['totalTokens']=用量['inputTokens']+用量['outputTokens']+(用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 else 0)+(用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 else 0)#合计
            yield {'type':'usage','usage':用量}#用量
            yield {'type':'finish','reason':原因,'replayState':回放状态(模型,[块['replay'] for 块 in 块表.values()])}#结束
            return#完成
    raise 大模型错误('DeepSeek Messages stream ended before message_stop','STREAM_CLOSED')#截断
