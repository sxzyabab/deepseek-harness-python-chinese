__all__=('未登记','按事件取主体解析器')

未登记=object()#对应 TS 查表得到的 undefined；与 None（仅检查载体）区分

def 取参数零智能体(参数):
    """从载荷取出 agent 路由主体。"""
    return 参数[0]['agent']

def 取参数一作用域(参数):
    """从组装上下文取出 scope 路由主体。"""
    return 参数[1]['scope']

主体解析器表={
    'agent/assistant-stream':取参数零智能体,
    'agent/created':取参数零智能体,
    'agent/disposed':取参数零智能体,
    'agent/error':取参数零智能体,
    'agent/inbox/claimed':取参数零智能体,
    'agent/inbox/discarded':取参数零智能体,
    'agent/inbox/inserted':取参数零智能体,
    'agent/pre-step':取参数零智能体,
    'agent/request':取参数零智能体,
    'agent/request-error':取参数零智能体,
    'agent/status':取参数零智能体,
    'agent/turn-stopping':取参数零智能体,
    'approval/request':取参数零智能体,
    'goal/changed':取参数零智能体,
    'session/created':None,#载荷无法暴露外部路由键
    'session/disposed':None,#仅检查载体存在
    'session/event':None,#仅检查载体存在
    'session/flush':None,#仅检查载体存在
    'subagent/end':None,#仅检查载体存在
    'subagent/start':None,#仅检查载体存在
    'system-prompt/assemble':取参数一作用域,
    'tools/execute':取参数零智能体,
    'tools/post-execute':取参数零智能体,
    'tools/pre-execute':取参数零智能体,
    'tools/ptc-dispatch-log':取参数零智能体,
    'tools/result':取参数零智能体,
    'user-questions/request':取参数零智能体,
}

def 按事件取主体解析器(事件):
    """解析一条作用域事件载荷点名的路由键。

    解析器为 None 表示只检查载体是否存在；未登记则返回未登记，事件不受作用域过滤。
    """
    if 事件 not in 主体解析器表:
        return 未登记
    return 主体解析器表[事件]
