"""因输出 token 上限结束的回合通知。

对齐上游 `ui-conversation/src/client/conversation-nodes/turn-max-tokens.ts`。公开面仅中文名。
"""
from .节点工厂 import 聊天合成序号偏移,聊天节点#公共
from ..服务 import 对话错误#本包异常

__all__=['回合顶格定义','登记回合顶格会话节点']#仅中文公开名

def 读位置(上下文):
    """起点或首匹配的位置。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    if 起点 is not None and 'location' in 起点:
        return 起点['location']#起点位置
    匹配列表=上下文['matches'] if 'matches' in 上下文 else []#匹配
    if len(匹配列表)>0 and 'location' in 匹配列表[0]:
        return 匹配列表[0]['location']#首匹配
    return None#无

def 末步(上下文):
    """所属回合最后一步的步骤号。"""
    位置=读位置(上下文)#位置
    if 位置 is None or 位置['kind'] not in ('turn','step'):
        return 0#零
    回合=位置['turn']#回合
    步列表=回合['steps'] if 'steps' in 回合 else []#步
    if len(步列表)==0:
        return 0#零
    末=步列表[-1]#末步
    return 末['step'] if 'step' in 末 else 0#末步号

def 通知锚(上下文,序号):
    """有收束助手则夹在助手与回合尾之间。"""
    位置=读位置(上下文)#位置
    if 位置 is None or 位置['kind'] not in ('turn','step'):
        return 序号#用 turn/end
    回合数据=位置['turn']['data'] if 'data' in 位置['turn'] else None#回合 data
    if 回合数据 is None or 'turn-tail' not in 回合数据:
        return 序号#截断点
    尾=回合数据['turn-tail']#turn-tail
    if 尾 is None or 'closing' not in 尾:
        return 序号#截断点
    收束=尾['closing']#收束助手
    if 收束 is None:
        return 序号#截断点
    终=收束['finalNode'] if 'finalNode' in 收束 else {}#终态
    锚=终['seq'] if 'seq' in 终 else 序号#seq
    return 锚+聊天合成序号偏移['maxTokensNotice']#夹中间

def 自匹配取态(匹配项):
    """从 max-tokens 的 turn/end 取状态。"""
    事件=匹配项['event']#事件
    if 事件['type']!='turn/end':
        return None#无
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    原因=数据['reason'] if 'reason' in 数据 else None#原因
    if 原因 is None or 原因['kind']!='max-tokens':
        return None#无
    return {'turn':数据['turn'],'seq':事件['seq'],'time':事件['time']}#态

def 回合顶格匹配(事件):
    """max-tokens 的 turn/end。"""
    if 事件['type']!='turn/end':
        return None#其余
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    原因=数据['reason'] if 'reason' in 数据 else None#原因
    if 原因 is None or 原因['kind']!='max-tokens':
        return None#其余
    return {'id':str(数据['turn']),'role':'start'}#开

def 回合顶格开始(_上下文,匹配项):
    """用 max-tokens 的 turn/end 开节点。"""
    态=自匹配取态(匹配项)#取
    if 态 is None:
        raise 对话错误('turn-max-tokens start requires a max-tokens turn/end')#硬失败
    return 态#记下

def 回合顶格更新(上下文,_匹配项=None):
    """后续不改。"""
    return 上下文['state'] if 'state' in 上下文 else None#态

def 回合顶格建视图(上下文):
    """无状态则不渲染。"""
    态=上下文['state'] if 'state' in 上下文 else None#态
    if 态 is None:
        return None#不渲染
    节点={'kind':'turn-max-tokens','seq':态['seq'],'time':态['time'],'turn':态['turn'],'step':末步(上下文)}#载荷
    return 聊天节点(上下文,'turn-max-tokens',通知锚(上下文,态['seq']),节点)#节点

回合顶格定义={#输出 token 上限结束回合的通知
    'kind':'turn-max-tokens','target':'chat',#kind/目标
    'match':回合顶格匹配,'start':回合顶格开始,'update':回合顶格更新,'buildViewNode':回合顶格建视图,#生命周期
}#结束

def 登记回合顶格会话节点(上下文):
    """注册截断通知贡献。"""
    上下文.conversationEvents.register(回合顶格定义)#登记
