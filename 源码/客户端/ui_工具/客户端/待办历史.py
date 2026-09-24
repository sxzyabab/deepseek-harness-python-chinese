from ...ui_对话.客户端.约定.槽 import 对话错误

__all__=['待办基线','待办历史','待办写入定义','待办调用定义','待办历史视图','登记待办历史']

def 待办基线(待办表=None):
    """一次调用前已记录的列表；首次已加载写入前缺席。"""
    return {'todos':待办表}

待办写入定义={
    'kind':'tool-todo-write',
    'match':None,
    'start':None,
    'update':None,
    'publication':None,
}

def 匹配待办写入(事件):
    """todo/write 起步。事件为 dict。"""
    if 事件['type']!='todo/write':
        return None
    return {'id':str(事件['seq']),'role':'start'}

def 起步待办写入(_上下文,匹配):
    """取出写入列表。"""
    if 匹配['event']['type']!='todo/write':
        raise 对话错误('tool-todo-write requires todo/write')
    return 匹配['event']['data']['todos']

def 保持状态(上下文):
    """状态不变。上下文为 dict。"""
    return 上下文['state']

def 无发布(_上下文):
    """不发布视图节点。"""
    return 'none'

待办写入定义['match']=匹配待办写入
待办写入定义['start']=起步待办写入
待办写入定义['update']=保持状态
待办写入定义['publication']=无发布

def 匹配待办调用(事件):
    """根或嵌套 todo_write 起步。"""
    种=事件['type']
    数据=事件['data'] if 'data' in 事件 else {}
    if 种=='tool/call' and 数据['name']=='todo_write':
        return {'id':str(数据['callId']),'role':'start'}
    if 种=='tool/ptc-dispatch-start' and 数据['name']=='todo_write':
        return {'id':str(数据['subCallId']),'role':'start'}
    return None

def 起步待办调用(_上下文,_匹配,读取):
    """前一次 tool-todo-write 状态。"""
    先前=读取.previous('tool-todo-write')
    return {'todos':先前['state'] if 先前 is not None and 'state' in 先前 else None}

def 构建待办调用节点(上下文):
    """状态缺席则不建节点。"""
    if 上下文['state'] is None:
        return None
    return {'key':上下文['key'],'kind':上下文['kind'],'id':上下文['id'],'target':'tool-todo-history','data':上下文['state']}

待办调用定义={
    'kind':'tool-todo-call',
    'target':'tool-todo-history',
    'match':匹配待办调用,
    'start':起步待办调用,
    'update':保持状态,
    'buildViewNode':构建待办调用节点,
}

def 创建待办历史():
    """增量查找快照；后续写入保留更早基线。"""
    调用表={}
    def 替换(输入):
        """整表替换。输入为 dict。"""
        nonlocal 调用表
        调用表={}
        for 节点 in 输入['nodes']:
            调用表[节点['id']]=节点['data']
        return 调用表
    def 应用(输入):
        """写入变更。"""
        nonlocal 调用表
        写入=输入['upserts']
        if len(写入)>0:
            调用表=dict(调用表)
            for 节点 in 写入:
                调用表[节点['id']]=节点['data']
        return 调用表
    return {'empty':调用表,'replace':替换,'apply':应用}

待办历史视图={
    'target':'tool-todo-history',
    'create':创建待办历史,
}

def 登记待办历史(上下文):
    """安装已记录写入索引与调用前驱目标。"""
    上下文.uiConversation.events.register(待办写入定义)
    上下文.uiConversation.events.register(待办调用定义)
    上下文.uiConversation.views.register(待办历史视图)
