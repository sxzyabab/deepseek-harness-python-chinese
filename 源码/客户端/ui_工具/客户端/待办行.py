import json
from .文案 import 会话命名空间
from .调用模型 import 派生工具行
from .计划摘要 import 计划摘要
from .工具行 import 工具行

__all__=['待办行','待办工具视图','是否计划条目','汇总']

def 是否计划条目(值):
    '来自未校验模型 JSON 的列表项'
    return isinstance(值,dict)

def 汇总(文本,翻译):
    '非法字段时 None，行回退通用摘要'
    try:
        解析=json.loads(文本)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(解析,dict):
        return None
    待办列表=解析['todos'] if 'todos' in 解析 else None
    if not isinstance(待办列表,list) or not all(是否计划条目(项) for 项 in 待办列表):
        return None
    摘要=计划摘要(待办列表)
    头=翻译('todo.completed',{'done':摘要['done'],'total':摘要['total']})
    活跃=摘要['activeContent']
    文本半=头 if 活跃 is None else 头+' · '+活跃
    return {'text':文本半,'extra':摘要['activeExtra']}

class 待办行:
    '整行切换调用的输入输出。槽位只调用构造，键齐了就画'

    def __init__(自身,属性):
        '记下合成 props，并挂上空的工具行。工具行由渲染画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.行=工具行()
        if 'block' in 自身.属性 and 't' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 渲染(自身):
        '派生摘要与状态后交给工具行'
        属性=自身.属性
        工具名=属性['toolName'] if 'toolName' in 属性 and 属性['toolName'] else 'todo_write'
        块=属性['block']
        翻译=属性['t']
        检查=属性['inspect'] if 'inspect' in 属性 else None
        模型=派生工具行(工具名,块)
        已结算='kind' in 块
        if 已结算:
            调用=块['call'] if 'call' in 块 else None
            原始=调用['argsRaw'] if 调用 is not None and 'argsRaw' in 调用 and 调用['argsRaw'] is not None else ''
        else:
            原始=块['argsRaw'] if 'argsRaw' in 块 and 块['argsRaw'] is not None else ''
        两半=汇总(原始,翻译)
        摘要=两半 if 两半 is not None else {'text':模型['summary'],'extra':0}
        额外=摘要['extra']
        行属性={
            't':翻译,
            'variant':模型['variant'],
            'toolName':工具名,
            'icon':'checklist',
            'title':翻译('todo.rowTitle'),
            'summary':摘要['text'],
            'summarySuffix':('+'+str(额外)) if 额外>0 else None,
            'body':模型['body'],
            'output':模型['output'],
            'errorSummary':模型['errorSummary'],
            'state':模型['state'],
            'inspect':检查,
        }
        return 自身.行(行属性)

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

待办工具视图={
    'name':'todo-toolview',
    'inject':['slots'],
}

def 应用待办工具视图(上下文):
    '把待办行写入按键视图槽'
    def 登记():
        '登记 todo_write 键'
        return 上下文.slots.register({
            'name':'tool.call.toolview','key':'todo_write','locale':会话命名空间,
        },待办行)
    上下文.slots.inject('tool.call.toolview',登记)

待办工具视图['apply']=应用待办工具视图
