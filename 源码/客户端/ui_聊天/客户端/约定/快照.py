__all__=['空聊天快照','聊天节点源']


class 聊天节点源:
    '带 getSnapshot 和 subscribe 的节点源'
    def __init__(自身,取快照,订阅):
        '记下读和订'
        自身.getSnapshot=取快照
        自身.subscribe=订阅

空列表=[]


def 空退订():
    '空源没有监听可拆'
    return


def 空订阅(监听=None):
    '空源不通知'
    return 空退订


def 空节点快照():
    '还没有节点'
    return None


def 空底快照():
    '还没有贴底'
    return False


def 空过程快照():
    '还没有回合过程'
    return None


def 空回合节点快照():
    '这一回合还没有节点'
    return 空列表


def 取空节点(键=None):
    '按键取节点。空快照始终没有'
    return None


def 空节点源(键=None):
    '单个节点的空源'
    return {'getSnapshot':空节点快照,'subscribe':空订阅}


def 空底源(键=None):
    '贴底标记的空源'
    return {'getSnapshot':空底快照,'subscribe':空订阅}


def 空回合节点源(键=None):
    '一回合节点列表的空源'
    return {'getSnapshot':空回合节点快照,'subscribe':空订阅}


def 空过程源(键=None):
    '回合过程的空源'
    return {'getSnapshot':空过程快照,'subscribe':空订阅}


def 空节点值():
    '全部节点。空快照是空列表'
    return 空列表


def 空取回合(回合=None):
    '按回合取位置。空快照没有'
    return 空列表


def 空取步(回合=None,步=None):
    '按步骤取位置。空快照没有'
    return 空列表


def 空导航项():
    '导航项。空快照没有'
    return 空列表


空聊天快照={
    'order':空列表,
    'nodes':{
        'get':取空节点,
        'source':空节点源,
        'bottomSource':空底源,
        'turnDataSource':空回合节点源,
        'processSource':空过程源,
        'values':空节点值,
    },
    'locations':{
        'getTurn':空取回合,
        'getStep':空取步,
    },
    'navigation':{
        'items':空导航项,
    },
    'timeline':{'turnOrder':空列表,'turns':{}},
    'legacy':{
        'nodes':空列表,
        'turnTimings':{},
        'turnEnds':{},
        'partial':None,
        'runningCalls':空列表,
    },
}
