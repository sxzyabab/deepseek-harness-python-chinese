import reprlib
from ...模型后端.llm import 装备错误

__all__=['团队错误','错误文案']

class 团队错误(装备错误):
    """Team 域抛出的稳定失败。"""
    def __init__(自身,消息,码,选项=None):
        """记下文案与稳定错误码。"""
        装备错误.__init__(自身,消息,码,选项)
        自身.name='TeamError'

def 错误文案(错误):
    """渲染任意抛出值，不替换原拒绝。"""
    if isinstance(错误,装备错误):
        return str(错误.message)
    if isinstance(错误,BaseException):
        return str(错误)
    if isinstance(错误,str):
        return 错误
    return reprlib.repr(错误)
