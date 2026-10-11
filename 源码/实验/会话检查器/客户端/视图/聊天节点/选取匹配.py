'检查器 Chat 选取器可替换的、元素到记录的匹配规则'

from .文档对象 import 已显示,在聊天内,数据集

__all__=['匹配聊天元素','匹配聊天节点行']

def 最近(元素,选择器,根):
    '最近的、仍在该 Chat 内且已显示的匹配元素'
    找到=元素.closest(选择器)
    if 找到 is not None and 在聊天内(找到,根) and 已显示(找到):
        return 找到
    return None

def 匹配聊天元素(元素,根):
    '工具调用盒和 Node 部位优先于 Group 或 Turn 容器；不比较渲染文本'
    if not 在聊天内(元素,根) or not 已显示(根) or 元素.closest('[hidden]') is not None:
        return None
    节点=最近(元素,'[data-chat-node-key]',根)
    调用=最近(元素,'[data-chat-call-id]',根)
    组=最近(元素,'[data-chat-group-key]',根)
    回合元素=最近(元素,'[data-chat-turn]',根)
    盒=调用 or 节点 or 组 or 回合元素
    if 盒 is None:
        return None
    回合值=None if 回合元素 is None else 数据集(回合元素,'chatTurn')
    回合=None
    if 回合值 not in (None,''):
        try:
            数=int(回合值) if str(回合值).isdigit() or (isinstance(回合值,str) and 回合值.lstrip('-').isdigit()) else float(回合值)
        except (TypeError,ValueError):
            数=None
        if isinstance(数,int) and not isinstance(数,bool) and 数>=0:
            回合=数
        elif isinstance(数,float) and 数.is_integer() and 数>=0 and abs(数)<=9007199254740991:
            回合=int(数)
    目标={}
    if 节点 is not None and 数据集(节点,'chatNodeKey') is not None:
        目标['nodeKey']=数据集(节点,'chatNodeKey')
    if 节点 is not None and 数据集(节点,'chatGroupPart') is not None:
        目标['groupPart']=数据集(节点,'chatGroupPart')
    if 节点 is not None and 数据集(节点,'chatFlowKind') is not None:
        目标['nodeKind']=数据集(节点,'chatFlowKind')
    if 调用 is not None and 数据集(调用,'chatCallId') is not None:
        目标['callId']=数据集(调用,'chatCallId')
    if 组 is not None and 数据集(组,'chatGroupKey') is not None:
        目标['groupKey']=数据集(组,'chatGroupKey')
    if 回合 is not None:
        目标['turn']=回合
    return {'element':盒,'target':目标}

def 匹配聊天节点行(目标,行表):
    '优先精确 Node 部位，再退到 Node、Group、Step 或 Turn 行'
    条目=list(行表.items()) if hasattr(行表,'items') else list(行表)
    if 目标.get('nodeKey') is not None:
        节点=[项 for 项 in 条目 if 项[1].get('nodeKey')==目标['nodeKey']]
        精确=None
        for 项 in 节点:
            if 项[1].get('groupPart')==目标.get('groupPart'):
                精确=项
                break
        if 精确 is None and len(节点)>0:
            精确=节点[0]
        if 精确 is not None:
            return 精确[0]
    if 目标.get('groupKey') is not None:
        for 项 in 条目:
            if 项[1].get('groupKey')==目标['groupKey'] and 项[1].get('nodeKey') is None:
                return 项[0]
    if 目标.get('turn') is None:
        return None
    回合=[项 for 项 in 条目 if 项[1].get('turn')==目标['turn']]
    if 目标.get('step') is None:
        return None if len(回合)==0 else 回合[0][0]
    for 项 in 回合:
        if 项[1].get('step')==目标['step']:
            return 项[0]
    return None if len(回合)==0 else 回合[0][0]
