"""未被认领的 append-surface 回退。

对齐上游 `ui-conversation/src/client/conversation-nodes/fallback.ts`。公开面仅中文名。
"""
from .公共 import 聊天节点#聊天节点工厂
from .面辅助 import 取字段,是追加面事件#面辅助

__all__=['未知回退定义','登记未知会话回退']#仅中文公开名

def 未知匹配(事件):#append-surface 才匹配
    """以序号为 id。"""
    if 是追加面事件(事件):#追加面
        return {'id':str(取字段(事件,'seq')),'role':'start'}#开
    return None#不匹配

def 未知开始(_上下文,匹配项):#从匹配事件造 unknown 初态
    """事件类型与载荷。"""
    事件=取字段(匹配项,'event')#事件
    return {#unknown 初态
        'kind':'unknown',#渲染器 kind
        'seq':取字段(事件,'seq'),#序号
        'time':取字段(事件,'time'),#时刻
        'type':取字段(事件,'type'),#事件类型
        'data':取字段(事件,'data'),#载荷
    }#结束

def 未知更新(上下文,_匹配项=None):#更新时沿用已有状态
    """原样。"""
    return 取字段(上下文,'state')#态

def 未知建视图(上下文):#用状态序号作锚点造 unknown 节点
    """尚无状态则不产出。"""
    态=取字段(上下文,'state')#态
    if 态 is None:#无
        return None#无节点
    return 聊天节点(上下文,'unknown',取字段(态,'seq'),态)#节点

未知回退定义={#未认领 append-surface 的回退
    'kind':'unknown-surface','target':'chat',#kind/目标
    'match':未知匹配,'start':未知开始,'update':未知更新,'buildViewNode':未知建视图,#生命周期
}#结束

def 登记未知会话回退(上下文):#把回退 Definition 登记到会话事件
    """registerFallback。"""
    上下文.conversationEvents.registerFallback(未知回退定义)#登记回退
