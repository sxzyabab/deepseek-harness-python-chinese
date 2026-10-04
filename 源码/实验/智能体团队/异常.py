import reprlib
from ...模型后端.llm.异常 import 装备错误

__all__=['团队错误','错误文案','任务图错误']

class 团队错误(装备错误):
    'Team 域抛出的稳定失败'
    def __init__(自身,消息,码,选项=None):
        '记下文案与稳定错误码'
        装备错误.__init__(自身,消息,码,选项)
        自身.name='TeamError'

def 错误文案(错误):
    '渲染任意抛出值，不替换原拒绝'
    if isinstance(错误,装备错误):
        return str(错误.message)
    if isinstance(错误,BaseException):
        return str(错误)
    if isinstance(错误,str):
        return 错误
    return reprlib.repr(错误)

class 任务图错误(团队错误):#包私有图失败
    '包私有的任务依赖失败，供命令错误映射保留'
    def __init__(自身,消息,违例):#构造
        '记下文案与稳定违例类别'
        团队错误.__init__(自身,消息,'TEAM_TASK_GRAPH')#基类
        自身.违例=违例#违例种类
