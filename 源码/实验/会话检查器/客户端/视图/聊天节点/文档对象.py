'实验检查器自己的 DOM 查找，使用已有的 Slot 和 Chat 属性'

__all__=['已显示','主聊天根','在聊天内','查找聊天目标','矩形字典','数据集']

def 矩形字典(值):
    '把 DOMRect 收成字段表'
    if isinstance(值,dict):
        return 值
    return {'left':值.left,'top':值.top,'right':值.right,'bottom':值.bottom,'width':值.width,'height':值.height}

def 数据集(元素,键):
    'dataset 上的驼峰字段'
    集=元素.dataset
    if isinstance(集,dict):
        return 集.get(键)
    return getattr(集,键,None)

def 已显示(元素):
    '元素已挂载，且祖先没有把它藏起来；不展开它'
    if not 元素.isConnected or 元素.closest('[hidden]') is not None:
        return False
    父=元素
    while 父 is not None:
        样式=getComputedStyle(父)
        if 样式.display=='none' or 样式.visibility=='hidden':
            return False
        父=父.parentElement
    return True

def 主聊天根():
    '已显示的主 Chat 外层流列，不进入侧栏或嵌套视图'
    候选=list(document.querySelectorAll('[data-slot="main.conversation"] [data-slot="conversation.view"] [data-chat-flow]'))
    for 元素 in 候选:
        if 元素.closest('[data-sidebar-right-session], [data-step-process-body]') is None and 已显示(元素):
            return 元素
    return None

def 在聊天内(元素,根):
    '候选属于选中的 Chat 列及其自己的 Conversation 视图'
    return 根.contains(元素) and 元素.closest('[data-sidebar-right-session]') is None and 元素.closest('[data-slot="conversation.view"]') is 根.closest('[data-slot="conversation.view"]')

def 查找聊天目标(根,目标表):
    '枚举精确和近似出现，不改变它们的显示状态'
    字段=('chatCallId','chatNodeKey','chatGroupKey','chatTurn')
    索引={名:{} for 名 in 字段}
    for 元素 in 根.querySelectorAll('[data-chat-call-id], [data-chat-node-key], [data-chat-group-key], [data-chat-turn]'):
        if not 在聊天内(元素,根):
            continue
        for 名 in 字段:
            值=数据集(元素,名)
            if 值 is None:
                continue
            命中=索引[名].get(值)
            if 命中 is None:
                索引[名][值]=[元素]
            else:
                命中.append(元素)
    找到=[]
    见过=set()
    def 加入(名,值,部位=None):
        '按字段和可选 group 部位收集'
        if 值 is None:
            return
        for 元素 in 索引[名].get(值) or []:
            if 部位 is not None and 数据集(元素,'chatGroupPart')!=部位:
                continue
            if 元素 not in 见过:
                见过.add(元素)
                找到.append(元素)
    回合集=[]
    优先回合=None
    for 目标 in 目标表:
        if 目标.get('turn') is not None:
            优先回合=目标['turn']
            break
    已加优先=False
    for 下标,目标 in enumerate(目标表):
        if 下标>0 and 优先回合 is not None and 目标.get('turn')!=优先回合 and not 已加优先:
            加入('chatTurn',str(优先回合))
            已加优先=True
        加入('chatCallId',目标.get('callId'))
        加入('chatNodeKey',目标.get('nodeKey'),目标.get('groupPart'))
        加入('chatNodeKey',目标.get('nodeKey'))
        加入('chatCallId',目标.get('rootCallId'))
        加入('chatGroupKey',目标.get('groupKey'))
        if 目标.get('turn') is not None and 目标['turn'] not in 回合集:
            回合集.append(目标['turn'])
    for 回合 in 回合集:
        if not 已加优先 or 回合!=优先回合:
            加入('chatTurn',str(回合))
    return 找到
