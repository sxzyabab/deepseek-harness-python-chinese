from ...模型后端.llm.异常 import 装备错误#导入harness错误基类

class 会话引用错误(装备错误):#可供宿主协议错误映射的带类型会话引用失败
    '可供宿主协议错误映射的带类型会话引用失败'
    def __init__(自身,消息,码,选项=None):#记下稳定路由码与可选cause
        '记下给人读的诊断、稳定路由码与可选 cause'
        装备错误.__init__(自身,消息,码,选项)#交给装备错误基类
        自身.name='SessionReferenceError'#固定错误名
