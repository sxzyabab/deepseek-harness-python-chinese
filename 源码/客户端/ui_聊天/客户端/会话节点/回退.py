from .节点工厂 import 聊天节点#聊天节点工厂
from .事件面 import 是追加面事件#面辅助

__all__=['未知回退定义','登记未知会话回退']#仅中文公开名

def 未知匹配(事件):#append-surface 才匹配
    """以序号为 id；排除瞬态 live-chunk。"""
    if 事件.get('type')=='assistant/live-chunk':#瞬态直播块
        return None#不认领
    if 是追加面事件(事件):#追加面
        return {'id':str(事件['seq']),'role':'start'}#开
    return None#不匹配

def 未知开始(_上下文,匹配项):#从匹配事件造 unknown 初态
    """事件类型与载荷。"""
    事件=匹配项['event']#事件
    return {#unknown 初态
        'kind':'unknown',#渲染器 kind
        'seq':事件['seq'],#序号
        'time':事件['time'] if 'time' in 事件 else None,#时刻
        'type':事件['type'],#事件类型
        'data':事件['data'] if 'data' in 事件 else None,#载荷
    }#结束

def 未知更新(上下文,_匹配项=None):#更新时沿用已有状态
    """原样。"""
    return 上下文['state'] if 'state' in 上下文 else None#态

def 未知建视图(上下文):#用状态序号作锚点造 unknown 节点
    """尚无状态则不产出。"""
    态=上下文['state'] if 'state' in 上下文 else None#态
    if 态 is None:#无
        return None#无节点
    return 聊天节点(上下文,'unknown',态['seq'],态)#节点

未知回退定义={#未认领 append-surface 的回退
    'kind':'unknown-surface','target':'chat',#kind/目标
    'match':未知匹配,'start':未知开始,'update':未知更新,'buildViewNode':未知建视图,#生命周期
}#结束

def 登记未知会话回退(上下文):#把回退 Definition 登记到会话事件
    """registerFallback。"""
    上下文.uiConversation.events.registerFallback(未知回退定义)#登记回退
