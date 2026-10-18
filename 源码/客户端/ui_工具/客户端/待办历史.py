__all__=['待办写入定义','待办调用定义','待办历史视图','登记待办历史']

def 匹配待办写入(事件):
    'todo/write 起步'
    if 事件.get('type')=='todo/write':
        return {'id':str(事件['seq']),'role':'start'}
    return None

def 起步待办写入(_上下文,匹配):
    '取出写入列表'
    if 匹配['event']['type']!='todo/write':
        raise RuntimeError('tool-todo-write requires todo/write')
    return 匹配['event']['data']['todos']

def 保持状态(上下文):
    '状态不变'
    return 上下文['state']

def 无发布(_上下文):
    '不发布视图节点'
    return 'none'

def 匹配待办调用(事件):
    '根或嵌套 todo_write 起步'
    if 事件.get('type')=='tool/call' and isinstance(事件.get('data'),dict) and 事件['data'].get('name')=='todo_write':
        return {'id':str(事件['data']['callId']),'role':'start'}
    if 事件.get('type')=='tool/ptc-dispatch-start' and isinstance(事件.get('data'),dict) and 事件['data'].get('name')=='todo_write':
        return {'id':str(事件['data']['subCallId']),'role':'start'}
    return None

def 起步待办调用(_上下文,_匹配,读取):
    '前一次 tool-todo-write 状态'
    先前=读取.previous('tool-todo-write')
    待办=None
    if 先前 is not None:
        待办=先前['state'] if isinstance(先前,dict) else getattr(先前,'state',None)
    return {'todos':待办}

def 构建待办调用节点(上下文):
    '状态缺席则不建节点'
    if 上下文.get('state') is None:
        return None
    return {
        'key':上下文['key'],
        'kind':上下文['kind'],
        'id':上下文['id'],
        'target':'tool-todo-history',
        'data':上下文['state'],
    }

待办写入定义={
    'kind':'tool-todo-write',
    'match':匹配待办写入,
    'start':起步待办写入,
    'update':保持状态,
    'publication':无发布,
}
待办调用定义={
    'kind':'tool-todo-call',
    'target':'tool-todo-history',
    'match':匹配待办调用,
    'start':起步待办调用,
    'update':保持状态,
    'buildViewNode':构建待办调用节点,
}

def 创建待办历史():
    '增量查找快照。后续写入保留更早基线'
    调用表={}
    def 替换(载荷):
        '整表替换'
        nonlocal 调用表
        节点表=载荷['nodes']
        调用表={}
        for 节点 in 节点表:
            调用表[节点['id']]=节点['data']
        return 调用表
    def 应用(载荷):
        '有更新才复制'
        nonlocal 调用表
        更新=载荷['upserts']
        if len(更新)>0:
            调用表=dict(调用表)
            for 节点 in 更新:
                调用表[节点['id']]=节点['data']
        return 调用表
    return {'empty':调用表,'replace':替换,'apply':应用}

待办历史视图={
    'target':'tool-todo-history',
    'create':创建待办历史,
}

def 登记待办历史(上下文):
    '安装已记录写入索引与调用前驱目标'
    上下文.uiConversation.events.register(待办写入定义)
    上下文.uiConversation.events.register(待办调用定义)
    上下文.uiConversation.views.register(待办历史视图)
