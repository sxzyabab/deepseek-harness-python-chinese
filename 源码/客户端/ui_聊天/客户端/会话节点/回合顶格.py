"""因输出 token 上限结束的回合通知。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-max-tokens.ts`。公开面仅中文名。
"""
from .公共 import 聊天合成序号偏移,聊天节点#公共
from .面辅助 import 取字段#字段

__all__=['回合顶格定义','登记回合顶格会话节点']#仅中文公开名

def 末步(上下文):#所属回合最后一步的步骤号
    """非回合/步骤则 0。"""
    起点=取字段(上下文,'start')#起点
    匹配们=取字段(上下文,'matches') or []#匹配
    位置=取字段(起点,'location') if 起点 is not None else (取字段(匹配们[0],'location') if 匹配们 else None)#位置
    if 取字段(位置,'kind') not in ('turn','step'):#非
        return 0#零
    步们=取字段(取字段(位置,'turn'),'steps') or []#步
    return 取字段(步们[-1],'step',0) if 步们 else 0#末步

def 通知锚(上下文,序号):#通知在 Chat 序列中的锚点 seq
    """有收束助手则夹在助手与回合尾之间。"""
    起点=取字段(上下文,'start')#起点
    匹配们=取字段(上下文,'matches') or []#匹配
    位置=取字段(起点,'location') if 起点 is not None else (取字段(匹配们[0],'location') if 匹配们 else None)#位置
    if 取字段(位置,'kind') not in ('turn','step'):#非
        return 序号#用 turn/end
    回合数据=取字段(取字段(位置,'turn'),'data')#回合 data
    尾=回合数据.get('turn-tail') if hasattr(回合数据,'get') else None#turn-tail
    if 尾 is None and 回合数据 is not None and hasattr(回合数据,'get'):#Map 面
        尾=回合数据.get('turn-tail')#再取
    收束=取字段(尾,'closing') if 尾 is not None else None#收束助手
    if 收束 is None:#无收束
        return 序号#截断点
    终=取字段(收束,'finalNode') or {}#终态
    return 取字段(终,'seq',序号)+聊天合成序号偏移['maxTokensNotice']#夹中间

def 自匹配取态(匹配项):#从 max-tokens 的 turn/end 取状态
    """非该原因则 None。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='turn/end':#非
        return None#无
    数据=取字段(事件,'data') or {}#载荷
    if 取字段(取字段(数据,'reason'),'kind')!='max-tokens':#非
        return None#无
    return {'turn':取字段(数据,'turn'),'seq':取字段(事件,'seq'),'time':取字段(事件,'time')}#态

def 回合顶格匹配(事件):#判定事件是否属于本节点
    """max-tokens 的 turn/end。"""
    if 取字段(事件,'type')=='turn/end' and 取字段(取字段(取字段(事件,'data'),'reason'),'kind')=='max-tokens':#上限结束
        return {'id':str(取字段(取字段(事件,'data'),'turn')),'role':'start'}#开
    return None#其余

def 回合顶格开始(_上下文,匹配项):#用 max-tokens 的 turn/end 开节点
    """非该事件则抛。"""
    态=自匹配取态(匹配项)#取
    if 态 is None:#非
        raise Exception('turn-max-tokens start requires a max-tokens turn/end')#硬失败
    return 态#记下

def 回合顶格更新(上下文,_匹配项=None):#后续不改
    """原样。"""
    return 取字段(上下文,'state')#态

def 回合顶格建视图(上下文):#组装可见 Chat 节点
    """无状态则不渲染。"""
    态=取字段(上下文,'state')#态
    if 态 is None:#无
        return None#不渲染
    节点={'kind':'turn-max-tokens','seq':态['seq'],'time':态['time'],'turn':态['turn'],'step':末步(上下文)}#载荷
    return 聊天节点(上下文,'turn-max-tokens',通知锚(上下文,态['seq']),节点)#节点

回合顶格定义={#输出 token 上限结束回合的通知
    'kind':'turn-max-tokens','target':'chat',#kind/目标
    'match':回合顶格匹配,'start':回合顶格开始,'update':回合顶格更新,'buildViewNode':回合顶格建视图,#生命周期
}#结束

def 登记回合顶格会话节点(上下文):#注册截断通知贡献
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(回合顶格定义)#登记
