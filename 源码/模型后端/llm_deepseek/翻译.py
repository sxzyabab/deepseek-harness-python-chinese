"""把深求服务推送载荷翻译成 harness 块。

对齐上游 `llm-deepseek/src/translate.ts`。公开面仅中文名；无英文别名。
"""
import json#JSON解码
from ..llm import 调用标识,空响应码,大模型错误#调用id、空响应码与大模型错误
from .事件流 import 结束哨兵#服务推送结束哨兵

__all__=('映射结束原因','映射用量','关闭块','翻译')#仅中文公开名

解码=json.loads#JSON解码

def 映射结束原因(原因):#映射结束原因
    """把线路 finish_reason 词表映射到 harness 结束原因。"""
    if 原因=='stop':#正常停止
        return {'kind':'stop'}#正常停止
    if 原因=='tool_calls':#工具调用
        return {'kind':'tool-calls'}#工具调用
    if 原因=='length':#长度截断
        return {'kind':'max-tokens'}#长度截断
    return {
        'kind':'error',#未知则当错误
        'failure':{'message':'model stopped: '+原因,'code':原因.upper()},#大写code
    }#content_filter等

def 映射用量(用量):
    """映射线路用量字段。缓存命中从 inputTokens 里减去。"""
    详情=用量.get('prompt_tokens_details') or {}#兼容命中
    缓存命中=详情.get('cached_tokens')#优先 details
    if 缓存命中 is None:#没有 details
        缓存命中=用量.get('prompt_cache_hit_tokens')#回落到线路命中
    补全详情=用量.get('completion_tokens_details') or {}#补全细节
    推理=补全详情.get('reasoning_tokens')#推理令牌
    结果={
        'inputTokens':用量['prompt_tokens']-(缓存命中 or 0),#去掉命中后的输入
        'outputTokens':用量['completion_tokens'],#补全
    }#互不相交计数
    if 缓存命中 is not None:#有命中
        结果['cacheReadTokens']=缓存命中#有命中才带上
    if 推理 is not None:#有推理
        结果['reasoningTokens']=推理#有推理才带上
    return 结果#用量

def 关闭块(块):
    """为一块打开块组装最终内容块。"""
    if 块['kind']=='text':#文本
        return {'type':'text','text':块['text']}#文本
    if 块['kind']=='reasoning':#推理
        return {'type':'reasoning','text':块['text']}#推理
    return {
        'type':'tool-call',#工具调用
        'id':调用标识(块.get('callId') or ''),#缺 id 则空串品牌化
        'name':块.get('name') or '',#缺名则空串
        'arguments':块['text'],#累积参数
    }#工具调用结束

def 翻译(载荷序列):
    """消费服务推送数据载荷（以 [DONE] 结尾）并让出流块。"""
    下一标=0#下一个下标
    文本块=None#打开的文本块
    推理块=None#打开的推理块
    工具块={}#线路 index 到工具块
    顺序=[]#打开顺序
    推迟结束=None#推迟的结束原因
    推迟用量=None#推迟的用量
    def 打开(种类):
        """打开一块并记下顺序。"""
        nonlocal 下一标#下标递增
        块={'index':下一标,'kind':种类,'text':''}#新块
        下一标+=1#前进下标
        顺序.append(块)#记下顺序
        return 块#打开块
    for 载荷 in 载荷序列:#逐条载荷
        if 载荷==结束哨兵:#结束哨兵
            for 块 in 顺序:#按打开顺序
                yield {'type':'block-end','index':块['index'],'block':关闭块(块)}#按打开顺序关闭
            if 推迟用量:#有用量
                yield {'type':'usage','usage':推迟用量}#有用量才让出
            原因=推迟结束 if 推迟结束 is not None else {'kind':'stop'}#缺省当 stop
            if 原因.get('kind')=='stop' and len(顺序)==0:#空响应
                原因={
                    'kind':'error',#退化空响应
                    'failure':{
                        'message':'model returned a completed response with no content',#空响应文案
                        'code':空响应码,#空响应码
                    },#失败事实
                }#空响应结束
            yield {'type':'finish','reason':原因}#终止 finish
            return#翻译结束
        try:#解码 JSON
            块=解码(载荷)#按线路块查看
        except Exception:#畸形
            raise 大模型错误('malformed SSE payload: '+载荷[:120],'MALFORMED_RESPONSE')#畸形 JSON
        for 选择 in 块.get('choices') or []:#逐个选择
            增量=选择.get('delta') or {}#增量
            推理=增量.get('reasoning_content')#推理增量
            if isinstance(推理,str) and len(推理)>0:#有推理文本
                if 推理块 is None:#尚未打开
                    推理块=打开('reasoning')#打开推理块
                    yield {'type':'block-start','index':推理块['index'],'blockType':'reasoning'}#块开始
                推理块['text']+=推理#累积
                yield {'type':'reasoning-delta','index':推理块['index'],'text':推理}#推理增量
            内容=增量.get('content')#可见文本
            if isinstance(内容,str) and len(内容)>0:#有文本
                if 文本块 is None:#尚未打开
                    文本块=打开('text')#打开文本块
                    yield {'type':'block-start','index':文本块['index'],'blockType':'text'}#块开始
                文本块['text']+=内容#累积
                yield {'type':'text-delta','index':文本块['index'],'text':内容}#文本增量
            for 调用 in 增量.get('tool_calls') or []:#工具调用增量
                工具=工具块.get(调用['index'])#已有则用
                if 工具 is None:#新开
                    工具=打开('tool-call')#打开工具块
                    工具块[调用['index']]=工具#记下线路 index
                    yield {'type':'block-start','index':工具['index'],'blockType':'tool-call'}#块开始
                if 调用.get('id') is not None:#有 id
                    工具['callId']=调用['id']#有 id 则记下
                函数=调用.get('function') or {}#可选函数片段
                if 函数.get('name') is not None:#有名字
                    工具['name']=函数['name']#有名字则记下
                片段=函数.get('arguments') or ''#参数片段
                工具['text']+=片段#累积参数
                增量块={
                    'type':'tool-call-delta',#工具增量
                    'index':工具['index'],#下标
                    'id':调用标识(工具.get('callId') or ''),#调用 id
                    'argumentsDelta':片段,#参数片段
                }#工具调用增量
                if 工具.get('name') is not None:#有名字
                    增量块['name']=工具['name']#有名字才带上
                yield 增量块#让出工具增量
            if isinstance(选择.get('finish_reason'),str):#有结束原因
                推迟结束=映射结束原因(选择['finish_reason'])#推迟到 DONE
        if 块.get('usage'):#有用量
            推迟用量=映射用量(块['usage'])#记下最新用量
    raise 大模型错误('SSE payload stream ended without [DONE]','STREAM_CLOSED')#没有哨兵
