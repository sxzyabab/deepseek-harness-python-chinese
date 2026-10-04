from ...模型后端.llm.异常 import 装备错误 as 框架错误#Harness 风格错误

class 授权错误(框架错误):
    '授权失败的结构化错误'
    def __init__(自身,消息,码,选项=None):
        '记下消息与稳定码'
        super().__init__(消息,码,选项)#基类
        自身.name='AuthorizationError'#错误名

class 授权拒绝错误(授权错误):
    '提示被人类拒绝时使用'
    def __init__(自身,消息='the authorization prompt was declined'):
        'DECLINED 码'
        super().__init__(消息,'DECLINED')#基类
        自身.name='AuthorizationDeclinedError'#错误名
