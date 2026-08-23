"""把 pi-ai 助手事件翻译成 harness 流式协议。

对齐上游 `llm-pi-ai/src/stream.ts`。公开面仅中文名；无英文别名。
"""
import json#JSON 序列化
import re#正则
from .. import llm#语言模型服务
from ...依赖 import pi_ai#外部依赖胶水（pi-ai SDK）
from .回放 import 转派回放状态#回放状态投影

__all__=('映射用量','分类派爱错误','映射停止原因','转流块')#仅中文公开名

def 映射用量(用量):
    """映射 pi-ai 用量（推理已被 pi-ai 折进输出）。"""
    输入=用量['input'] if isinstance(用量,dict) else 用量.input#输入
    输出=用量['output'] if isinstance(用量,dict) else 用量.output#输出含推理
    缓存读=用量['cacheRead'] if isinstance(用量,dict) else 用量.cacheRead#缓存读
    缓存写=用量['cacheWrite'] if isinstance(用量,dict) else 用量.cacheWrite#缓存写
    计数={'inputTokens':输入,'outputTokens':输出}#harness计数
    if 缓存读>0:#零缓存读不占字段，避免把空缓存写进用量
        计数['cacheReadTokens']=缓存读#非零才带缓存读
    if 缓存写>0:#零缓存写同样省略
        计数['cacheWriteTokens']=缓存写#非零才带缓存写
    return 计数#用量

def 分类派爱错误(消息):
    """按文本分类派爱错误。"""
    if re.search(r'\b(?:401|403)\b',消息):#命中 401/403 则归认证失败
        return 'AUTH'#认证失败
    if llm.是否配额超出错误(消息):#配额措辞优先于其它 4xx
        return llm.配额超出码#配额耗尽
    if re.search(r'\b429\b|rate.?limit',消息,re.I):#429 或速率限制措辞
        return 'RATE_LIMIT'#速率限制
    if re.search(r'\b400\b|invalid.?request',消息,re.I):#400 或非法请求措辞
        return 'INVALID_REQUEST'#坏请求
    if re.search(r'\b5\d\d\b',消息):#5xx 归服务端
        return 'SERVER'#服务端错误
    if re.search(r'\btime(?:d)?\s*out\b|timeout',消息,re.I):#超时措辞
        return 'TIMEOUT'#超时
    if re.search(r'stream ended (?:before|without)\b',消息,re.I):#流在 done 前结束，当传输截断
        return 'TRANSPORT'#流截断
    if re.search(r'\b(?:network|connection|socket|fetch)\b|\bECONN[A-Z]+\b',消息,re.I):#网络/连接/套接字失败
        return 'TRANSPORT'#传输失败
    if re.search(r'\b(?:other side closed|HTTP2 request did not get a response|WebSocket closed unexpectedly)\b',消息,re.I):#对端关闭、HTTP2 无响应、WebSocket 意外关闭
        return 'TRANSPORT'#对端关闭、HTTP2无响应、WebSocket意外关闭
    if re.search(r'\bterminated\b|premature close',消息,re.I):#进程被终止或过早关闭
        return 'TRANSPORT'#terminated或过早关闭
    return 'PI_AI_ERROR'#其余派爱错误

def 映射停止原因(消息,上下文窗口=None):
    """把终止派爱事件映射成 harness 结束原因。"""
    派溢出=pi_ai.isContextOverflow(消息,上下文窗口)#派爱溢出判定
    结束原因=消息['stopReason'] if isinstance(消息,dict) else 消息.stopReason#结束原因
    错误消息=消息.get('errorMessage') if isinstance(消息,dict) else getattr(消息,'errorMessage',None)#错误消息
    线束溢出=结束原因=='error' and 错误消息 is not None and llm.是否上下文窗口超出错误(错误消息)#harness溢出措辞
    if 派溢出 or 线束溢出:#派爱判定或 harness 措辞任一命中都当上下文溢出
        模型=消息['model'] if isinstance(消息,dict) else 消息.model#模型
        文案=错误消息 if 错误消息 is not None else 'pi-ai detected context overflow for model "'+str(模型)+'"'#消息或默认文案
        return {
            'kind':'error',#错误结束
            'failure':{'message':文案,'code':llm.上下文窗口超出码},#失败事实
        }#上下文溢出错误
    if 结束原因=='stop':#正常完成；空内容块要改报空响应，不能当 stop
        内容=消息['content'] if isinstance(消息,dict) else 消息.content#内容块
        if len(内容)==0:#完成却没有内容块，对调用方是空响应错误
            模型=消息['model'] if isinstance(消息,dict) else 消息.model#模型
            return {
                'kind':'error',#错误结束
                'failure':{
                    'message':'model "'+str(模型)+'" returned a completed response with no content',#空响应文案
                    'code':llm.空响应码,#空响应码
                },#失败事实
            }#空响应错误
        return {'kind':'stop'}#正常停止
    if 结束原因=='length':#输出触达长度上限
        return {'kind':'max-tokens'}#长度截断
    if 结束原因=='toolUse':#模型要调工具
        return {'kind':'tool-calls'}#工具调用
    if 结束原因=='aborted':#上游流被中止，带 ABORTED 失败事实
        文案=错误消息 if 错误消息 is not None else 'pi-ai stream aborted'#中止文案
        return {'kind':'aborted','failure':{'message':文案,'code':'ABORTED'}}#中止
    if 结束原因=='error':#其余错误按文案再分类稳定码
        文本=错误消息 if 错误消息 is not None else 'pi-ai stream error'#错误文本
        return {'kind':'error','failure':{'message':文本,'code':分类派爱错误(文本)}}#按文本分类
    return None#封闭联合之外

def 读事件(事件,键,默认=None):
    """读取事件字段。"""
    if isinstance(事件,dict):#事件可能是映射或对象
        return 事件[键] if 键 in 事件 else 默认#字典
    return getattr(事件,键,默认)#对象

def 转流块(事件们,上下文窗口=None):
    """把 pi-ai 事件流翻译成 StreamChunk。"""
    工具标识={}#下标到调用id与名字
    已终止=False#是否见到终止事件
    for 事件 in 事件们:#按派爱事件顺序翻译；start 无 harness 块，done/error 终止
        类型=读事件(事件,'type')#事件类型
        下标=读事件(事件,'contentIndex')#块下标
        if 类型=='start':#回合开始没有对应 harness 块
            continue#无harness块
        if 类型=='text_start':#文本块开始，先发 block-start
            yield {'type':'block-start','index':下标,'blockType':'text'}#块开始
            continue#text_start结束
        if 类型=='text_delta':#文本增量
            yield {'type':'text-delta','index':下标,'text':读事件(事件,'delta')}#文本增量
            continue#text_delta结束
        if 类型=='text_end':#文本块结束，带已组装正文
            yield {'type':'block-end','index':下标,'block':{'type':'text','text':读事件(事件,'content')}}#带已组装文本
            continue#text_end结束
        if 类型=='thinking_start':#推理块开始
            yield {'type':'block-start','index':下标,'blockType':'reasoning'}#块开始
            continue#thinking_start结束
        if 类型=='thinking_delta':#推理增量
            yield {'type':'reasoning-delta','index':下标,'text':读事件(事件,'delta')}#推理增量
            continue#thinking_delta结束
        if 类型=='thinking_end':#推理块结束，带已组装推理正文
            yield {'type':'block-end','index':下标,'block':{'type':'reasoning','text':读事件(事件,'content')}}#带已组装推理
            continue#thinking_end结束
        if 类型=='toolcall_start':#工具调用开始；从 partial 记下 id 与名字，供后续增量用
            部分=读事件(事件,'partial')#部分消息
            部分内容=读事件(部分,'content') if 部分 is not None else None#部分内容
            部分块=None#该下标的部分块
            if 部分内容 is not None and 下标 is not None and 下标<len(部分内容):#partial 里有这一块才取
                部分块=部分内容[下标]#该下标的部分块
            调用=''#调用id或空
            名字=''#工具名或空
            部分类型=读事件(部分块,'type') if 部分块 is not None else None#部分块类型
            if 部分类型=='toolCall':#确认是工具调用块才抄 id 与名字
                调用=读事件(部分块,'id','')#调用id
                名字=读事件(部分块,'name','')#工具名
            工具标识[下标]={'id':调用,'name':名字}#记下id与名字
            yield {'type':'block-start','index':下标,'blockType':'tool-call'}#块开始
            continue#toolcall_start结束
        if 类型=='toolcall_delta':#工具调用参数增量；有非空名字才带上
            已知=工具标识.get(下标)#已记下的id与名字
            增量={'type':'tool-call-delta','index':下标,'id':llm.调用标识('' if 已知 is None else 已知['id']),'argumentsDelta':读事件(事件,'delta')}#工具调用增量
            if 已知 is not None and 已知.get('name') is not None and len(已知['name'])>0:#有非空名字才写进增量
                增量['name']=已知['name']#有非空名字才带上
            yield 增量#工具调用增量
            continue#toolcall_delta结束
        if 类型=='toolcall_end':#工具调用结束，参数序列化回原始 JSON
            工具调用=读事件(事件,'toolCall')#已组装工具调用
            参数=读事件(工具调用,'arguments')#已解析参数
            yield {
                'type':'block-end',#块结束
                'index':下标,#块下标
                'block':{
                    'type':'tool-call',#工具调用
                    'id':llm.调用标识(读事件(工具调用,'id')),#调用id
                    'name':读事件(工具调用,'name'),#工具名
                    'arguments':json.dumps(参数,separators=(',',':'),ensure_ascii=False),#序列化回原始JSON
                },#已组装工具调用
            }#块结束
            continue#toolcall_end结束
        if 类型=='done':#正常终止：先发用量，再发 finish，并投影回放状态
            助手=读事件(事件,'message')#助手消息
            yield {'type':'usage','usage':映射用量(读事件(助手,'usage'))}#先发用量
            yield {'type':'finish','reason':映射停止原因(助手,上下文窗口),'replayState':转派回放状态(助手)}#再发finish
            已终止=True#见到终止
            return#翻译结束
        if 类型=='error':#流内错误：先发用量再发 finish，不带回放状态
            错误=读事件(事件,'error')#错误助手消息
            yield {'type':'usage','usage':映射用量(读事件(错误,'usage'))}#先发用量
            yield {'type':'finish','reason':映射停止原因(错误,上下文窗口)}#错误结束
            已终止=True#见到终止
            return#翻译结束
    if not 已终止:#流耗尽却没见到 done/error，当作流被截断
        raise llm.大模型错误('pi-ai event stream ended without done/error','STREAM_CLOSED')#没有终止事件
