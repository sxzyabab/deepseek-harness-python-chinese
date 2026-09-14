from .节点工厂 import 聊天错误,聊天合成序号偏移,聊天节点#公共

__all__=['回合顶格定义','登记回合顶格会话节点']#仅中文公开名

def 末步(上下文):#所属回合最后一步的步骤号
    """非回合/步骤则 0。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    if 起点 is not None and 'location' in 起点:#有起点
        位置=起点['location']#位置
    elif len(匹配列表)>0 and 'location' in 匹配列表[0]:#首匹配
        位置=匹配列表[0]['location']#位置
    else:#无
        位置=None#无
    if 位置 is None or 'kind' not in 位置 or 位置['kind'] not in ('turn','step'):#非
        return 0#零
    回合=位置['turn'] if 'turn' in 位置 else None#回合
    步列表=回合['steps'] if 回合 is not None and 'steps' in 回合 and 回合['steps'] is not None else []#步
    if len(步列表)==0:#空
        return 0#零
    末=步列表[-1]#末步
    return 末['step'] if 'step' in 末 else 0#末步

def 通知锚(上下文,序号):#通知在 Chat 序列中的锚点 seq
    """有收束助手则夹在助手与回合尾之间。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    if 起点 is not None and 'location' in 起点:#有起点
        位置=起点['location']#位置
    elif len(匹配列表)>0 and 'location' in 匹配列表[0]:#首匹配
        位置=匹配列表[0]['location']#位置
    else:#无
        位置=None#无
    if 位置 is None or 'kind' not in 位置 or 位置['kind'] not in ('turn','step'):#非
        return 序号#用 turn/end
    回合=位置['turn'] if 'turn' in 位置 else None#回合
    回合数据=回合['data'] if 回合 is not None and 'data' in 回合 else None#回合 data
    尾=回合数据['turn-tail'] if 回合数据 is not None and 'turn-tail' in 回合数据 else None#turn-tail
    收束=尾['closing'] if 尾 is not None and 'closing' in 尾 else None#收束助手
    if 收束 is None:#无收束
        return 序号#截断点
    终=收束['finalNode'] if 'finalNode' in 收束 and 收束['finalNode'] is not None else {}#终态
    终序号=终['seq'] if 'seq' in 终 else 序号#终态序号
    return 终序号+聊天合成序号偏移['maxTokensNotice']#夹中间

def 自匹配取态(匹配项):#从 max-tokens 的 turn/end 取状态
    """非该原因则 None。"""
    事件=匹配项['event']#事件
    if 事件['type']!='turn/end':#非
        return None#无
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    原因=数据['reason'] if 'reason' in 数据 else None#原因
    if 原因 is None or 'kind' not in 原因 or 原因['kind']!='max-tokens':#非
        return None#无
    return {'turn':数据['turn'] if 'turn' in 数据 else None,'seq':事件['seq'],'time':事件['time'] if 'time' in 事件 else None}#态

def 回合顶格匹配(事件):#判定事件是否属于本节点
    """max-tokens 的 turn/end。"""
    if 事件['type']!='turn/end':#非
        return None#其余
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    原因=数据['reason'] if 'reason' in 数据 else None#原因
    if 原因 is not None and 'kind' in 原因 and 原因['kind']=='max-tokens':#上限结束
        return {'id':str(数据['turn']),'role':'start'}#开
    return None#其余

def 回合顶格开始(_上下文,匹配项):#用 max-tokens 的 turn/end 开节点
    """非该事件则抛。"""
    态=自匹配取态(匹配项)#取
    if 态 is None:#非
        raise 聊天错误('turn-max-tokens start requires a max-tokens turn/end')#硬失败
    return 态#记下

def 回合顶格更新(上下文,_匹配项=None):#后续不改
    """原样。"""
    return 上下文['state']#态

def 回合顶格建视图(上下文):#组装可见 Chat 节点
    """无状态则不渲染。"""
    态=上下文['state'] if 'state' in 上下文 else None#态
    if 态 is None:#无
        return None#不渲染
    节点={'kind':'turn-max-tokens','seq':态['seq'],'time':态['time'],'turn':态['turn'],'step':末步(上下文)}#载荷
    return 聊天节点(上下文,'turn-max-tokens',通知锚(上下文,态['seq']),节点)#节点

回合顶格定义={#输出 token 上限结束回合的通知
    'kind':'turn-max-tokens','target':'chat',#kind/目标
    'match':回合顶格匹配,'start':回合顶格开始,'update':回合顶格更新,'buildViewNode':回合顶格建视图,#生命周期
}#结束

def 登记回合顶格会话节点(上下文):#注册截断通知贡献
    """挂到 uiConversation.events。"""
    上下文.uiConversation.events.register(回合顶格定义)#登记
