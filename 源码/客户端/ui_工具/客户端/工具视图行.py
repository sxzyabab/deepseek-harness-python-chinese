import json
from nicegui import ui as 界面
from .调用模型 import 派生工具行

__all__=['提问行','待办行','已答摘要','待办摘要','提问工具视图','待办工具视图']

会话命名空间='conversation'

def 缺省翻译(键,_插值=None):
    '原样返回键'
    return 键

def 是答案(值):
    '对象即为答案条目候选'
    return isinstance(值,dict)

def 已答摘要(文本,翻译):
    '从结果 JSON 计已答数；无效则 None'
    try:
        解析=json.loads(文本)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(解析,dict):
        return None
    答案列表=解析['answers'] if 'answers' in 解析 else None
    if not isinstance(答案列表,list) or not all(是答案(a) for a in 答案列表):
        return None
    已答=0
    for a in 答案列表:
        选=a['selected'] if 'selected' in a else None
        自=a['custom'] if 'custom' in a else None
        if (isinstance(选,list) and len(选)>0) or (isinstance(自,str) and 自!=''):
            已答+=1
    return 翻译('ask.answered',{'answered':已答,'total':len(答案列表)})

def 计划摘要(条目表):
    'done、total、activeContent、activeExtra'
    已做=0
    活跃内容=None
    活跃额外=0
    for 项 in 条目表:
        态=项['status'] if 'status' in 项 else None
        if 态=='completed':
            已做+=1
        elif 态=='in_progress':
            if 活跃内容 is None:
                活跃内容=项['content'] if 'content' in 项 else None
            else:
                活跃额外+=1
    return {'done':已做,'total':len(条目表),'activeContent':活跃内容,'activeExtra':活跃额外}

def 待办摘要(参数原文,翻译):
    'text 可截断；extra 为并行活跃数'
    try:
        解析=json.loads(参数原文)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(解析,dict):
        return None
    表=解析['todos'] if 'todos' in 解析 else None
    if not isinstance(表,list) or not all(isinstance(i,dict) for i in 表):
        return None
    计=计划摘要(表)
    头=翻译('todo.completed',{'done':计['done'],'total':计['total']})
    if 计['activeContent'] is None:
        return {'text':头,'extra':计['activeExtra']}
    return {'text':头+' · '+str(计['activeContent']),'extra':计['activeExtra']}

class 提问行:
    '提问交互一行摘要。槽位只调用构造，键齐了就画'
    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'block' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '派生摘要与状态'
        p=自身.属性
        块=p['block']
        翻译=p['t'] if 't' in p else 缺省翻译
        工具名=p['toolName'] if 'toolName' in p and p['toolName'] else 'ask_user_question'
        切片=dict(块)
        if 'toolName' not in 切片 and 'name' not in 切片:
            切片['toolName']=工具名
        模型=派生工具行(切片)
        已结算='kind' in 块
        错=块['error'] if 已结算 and 'error' in 块 else None
        码=错['code'] if 错 is not None and 'code' in 错 else None
        摘要=模型['summary']
        状态=模型['state']
        if 码=='ASK_CANCELLED':
            摘要=翻译('ask.cancelled')
        elif 码=='ASK_ABORTED':
            摘要=翻译('ask.interrupted')
            状态='stopped'
        elif 模型['state']=='running':
            摘要=翻译('ask.waiting')
        elif 已结算 and 模型['state']=='ok':
            内容=块['content'] if 'content' in 块 and 块['content'] is not None else []
            文本=''.join((b['text'] if 'text' in b and b['text'] is not None else '') for b in 内容 if isinstance(b,dict) and 'type' in b and b['type']=='text')
            计=已答摘要(文本,翻译)
            摘要=计 if 计 is not None else 模型['summary']
        with 界面.column().classes('ask-question-row'):
            界面.label(翻译('ask.rowTitle'))
            if isinstance(摘要,str) and 摘要!='':
                界面.label(摘要)
            正文=模型['body']
            if isinstance(正文,str) and 正文!='':
                界面.label(正文)
            输出=模型['output']
            if isinstance(输出,str) and 输出!='':
                界面.label(输出)
            检查=p['inspect'] if 'inspect' in p else None
            if callable(检查):
                界面.button(on_click=检查).props('icon=search flat round')

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 待办行:
    '计划更新一行摘要。槽位只调用构造，键齐了就画'
    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'block' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '派生摘要'
        p=自身.属性
        块=p['block']
        翻译=p['t'] if 't' in p else 缺省翻译
        工具名=p['toolName'] if 'toolName' in p and p['toolName'] else 'todo_write'
        已结算='kind' in 块
        if 已结算:
            调用=块['call'] if 'call' in 块 else None
            参数原文=调用['argsRaw'] if 调用 is not None and 'argsRaw' in 调用 and 调用['argsRaw'] is not None else ''
        else:
            参数原文=块['argsRaw'] if 'argsRaw' in 块 and 块['argsRaw'] is not None else ''
        切片={'toolName':工具名,'argsRaw':参数原文}
        if 'kind' in 块:
            切片['kind']=块['kind']
        if 'content' in 块:
            切片['content']=块['content']
        if 'error' in 块:
            切片['error']=块['error']
        if 'isError' in 块:
            切片['isError']=块['isError']
        if 'call' in 块:
            切片['call']=块['call']
        模型=派生工具行(切片)
        两半=待办摘要(参数原文,翻译)
        摘要=两半 if 两半 is not None else {'text':模型['summary'],'extra':0}
        with 界面.column().classes('todo-row'):
            界面.label(翻译('todo.rowTitle'))
            if isinstance(摘要['text'],str) and 摘要['text']!='':
                界面.label(摘要['text'])
            if 摘要['extra']>0:
                界面.label('+'+str(摘要['extra']))
            错摘=模型['errorSummary']
            if isinstance(错摘,str) and 错摘!='':
                界面.label(错摘)
            检查=p['inspect'] if 'inspect' in p else None
            if callable(检查):
                界面.button(on_click=检查).props('icon=search flat round')

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 提问工具视图应用(上下文):
    '登记 ask_user_question toolview'
    def 登记():
        '按键条目'
        return 上下文.slots.register({
            'name':'tool.call.toolview','key':'ask_user_question','locale':会话命名空间,
        },提问行)
    上下文.slots.inject('tool.call.toolview',登记)

提问工具视图={'name':'ask-question-toolview','inject':['slots'],'apply':提问工具视图应用}

def 待办工具视图应用(上下文):
    '登记 todo_write toolview'
    def 登记():
        '按键条目'
        return 上下文.slots.register({
            'name':'tool.call.toolview','key':'todo_write','locale':会话命名空间,
        },待办行)
    上下文.slots.inject('tool.call.toolview',登记)

待办工具视图={'name':'todo-toolview','inject':['slots'],'apply':待办工具视图应用}
