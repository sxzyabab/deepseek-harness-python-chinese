import json
from ...ui_基础界面组件.icons import 图标清单14
from .文案 import 会话命名空间,中文文案
from .计划摘要 import 计划摘要
from .待办历史 import 登记待办历史
from .待办差异模型 import 待办差异模型
from .调用模型 import 工具行模型
from .工具行 import 工具行
from .槽 import 槽名工具调用视图

__all__=['待办行','待办工具视图']

def 是条目(值):
    '列表项是对象才继续汇总'
    return isinstance(值,dict)

class 待办行:
    '计划更新一行。取消的调用不显示成已完成'
    def __new__(类,属性):
        '派生摘要和与上次清单的差异'
        模型=工具行模型(属性['toolName'],属性['block'])
        历史=None
        if 'useTodoHistory' in 属性 and 属性['useTodoHistory'] is not None:
            def 取基线(快照,调用标识=属性['block']['callId']):
                '这次调用之前的清单'
                if 快照 is None:
                    return None
                if hasattr(快照,'get'):
                    return 快照.get(调用标识)
                if isinstance(快照,dict):
                    return 快照.get(调用标识)
                return None
            历史=属性['useTodoHistory'](取基线)
        还有更早=False
        if 'useSession' in 属性 and 属性['useSession'] is not None:
            def 取还有(快照):
                '更早历史是否还没加载'
                if isinstance(快照,dict):
                    return 快照.get('hasMore') is True
                return getattr(快照,'hasMore',False) is True
            还有更早=属性['useSession'](取还有)
        差异=待办差异模型(属性['block'],历史,还有更早)
        摘要=汇总(模型['bodyRaw'])
        if 摘要 is None:
            摘要={'text':模型['summary'],'extra':0}
        尾段=[]
        if 差异 is not None and 差异.get('summary'):
            尾段.append(差异['summary'])
        if 摘要['extra']>0:
            尾段.append('+'+str(摘要['extra']))
        后缀=' · '.join(尾段)
        return 工具行({
            'window':属性['window'],
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':属性['toolName'],
            'icon':图标清单14({'window':属性['window']}),
            'title':中文文案(模型['titleKey']),
            'summary':摘要['text'],
            'summarySuffix':后缀 if 后缀!='' else None,
            'bodyRaw':模型['bodyRaw'],
            'output':模型['output'],
            'details':None if 差异 is None else 差异['details'],
            'errorSummary':模型['errorSummary'],
            'state':模型['state'],
            'inspect':属性.get('inspect'),
        })

def 汇总(参数原文):
    '非法字段时 None，行回退通用摘要'
    if 参数原文 is None:
        return None
    try:
        已解析=json.loads(参数原文)
    except json.JSONDecodeError:
        return None
    if not isinstance(已解析,dict):
        return None
    待办=已解析.get('todos')
    if not isinstance(待办,list):
        return None
    for 项 in 待办:
        if not 是条目(项):
            return None
    计划=计划摘要(待办)
    头=中文文案('todo.completed',{'done':计划['done'],'total':计划['total']})
    if 计划['activeContent'] is None:
        文=头
    else:
        文=头+' · '+计划['activeContent']
    return {'text':文,'extra':计划['activeExtra']}

def 应用待办工具视图(上下文,配置=None):
    '登记待办历史和 todo_write 行'
    登记待办历史(上下文)
    def 登记():
        '按会话注入历史钩子'
        def 注入(会话标识):
            '这一会话的 tool-todo-history'
            return {'hooks':{'todoHistory':上下文.uiConversation.binding(会话标识).target('tool-todo-history')}}
        return 上下文.slots.register({
            'name':槽名工具调用视图,
            'key':'todo_write',
            'locale':会话命名空间,
            'inject':注入,
        },待办行)
    上下文.slots.inject(槽名工具调用视图,登记)

待办工具视图={
    'name':'todo-toolview',
    'inject':['slots','uiConversation'],
    'apply':应用待办工具视图,
}
