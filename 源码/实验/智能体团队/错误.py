"""类型化的 Agent Teams 失败。

对齐上游 `agent-team/src/error.ts`。公开面仅中文名。
"""
import reprlib#有界单行渲染
from ...模型后端.llm import 装备错误#Harness 错误基类

__all__=['团队错误','错误文案']#仅中文公开名

class 团队错误(装备错误):#Team 域稳定失败
    """Team 域抛出的稳定失败。"""
    def __init__(自身,消息,码,选项=None):#构造
        """记下文案与稳定错误码。"""
        装备错误.__init__(自身,消息,码,选项)#交给装备错误
        自身.name='TeamError'#固定名字

def 错误文案(错误):#渲染任意抛出值
    """渲染任意抛出值，不替换原拒绝。"""
    if isinstance(错误,BaseException):#异常取消息
        文案=getattr(错误,'message',None)#可选 message 字段
        if 文案 is not None:#有字段
            return str(文案)#字段文案
        return str(错误)#异常字符串
    if isinstance(错误,str):#字符串原样
        return 错误#原样
    return reprlib.repr(错误)#其它用有界 repr
