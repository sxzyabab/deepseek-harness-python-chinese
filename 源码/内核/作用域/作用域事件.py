"""为 dsh-scope 不变量生成的作用域事件路由主体解析器。

对齐上游 `scoped-events.generated.ts`。勿手改；上游以 `pnpm run gen-scoped-events` 重新生成后再同步本表。
公开面仅中文名；无英文公开别名。事件名字符串为 Cordis 运行时字面量，保持上游原样。
"""

__all__=('未登记','按事件取主体解析器')#仅中文公开名；解析辅助与表为包内细节

未登记=object()#对应 TS 查表得到的 undefined；与 None（仅检查载体）区分

def 取参数零智能体(参数):#从载荷取 agent
    """从载荷取出 agent 路由主体。"""
    return 参数[0]['agent']#载荷.agent

def 取参数一作用域(参数):#从组装上下文取 scope
    """从组装上下文取出 scope 路由主体。"""
    return 参数[1]['scope']#组装上下文.scope

主体解析器表={#事件名 → 解析器|None
    'agent/created':取参数零智能体,#载荷.agent
    'agent/disposed':取参数零智能体,#载荷.agent
    'agent/error':取参数零智能体,#载荷.agent
    'agent/inbox/claimed':取参数零智能体,#载荷.agent
    'agent/inbox/discarded':取参数零智能体,#载荷.agent
    'agent/inbox/inserted':取参数零智能体,#载荷.agent
    'agent/pre-step':取参数零智能体,#载荷.agent
    'agent/request':取参数零智能体,#载荷.agent
    'agent/request-error':取参数零智能体,#载荷.agent
    'agent/session-start':取参数零智能体,#载荷.agent
    'agent/status':取参数零智能体,#载荷.agent
    'agent/turn-stopping':取参数零智能体,#载荷.agent
    'approval/request':取参数零智能体,#载荷.agent
    'goal/changed':取参数零智能体,#载荷.agent
    'session/created':None,#载荷无法暴露外部路由键
    'session/disposed':None,#仅检查载体存在
    'session/event':None,#仅检查载体存在
    'session/flush':None,#仅检查载体存在
    'subagent/end':None,#仅检查载体存在
    'subagent/start':None,#仅检查载体存在
    'system-prompt/assemble':取参数一作用域,#组装上下文.scope
    'tools/code-dispatch-log':取参数零智能体,#载荷.agent
    'tools/execute':取参数零智能体,#载荷.agent
    'tools/post-execute':取参数零智能体,#载荷.agent
    'tools/pre-execute':取参数零智能体,#载荷.agent
    'tools/result':取参数零智能体,#载荷.agent
}#主体解析器表结束

def 按事件取主体解析器(事件):#按事件名取解析器
    """解析一条作用域事件载荷点名的路由键。

    解析器为 None 表示只检查载体是否存在；未登记则返回未登记，事件不受作用域过滤。
    """
    if 事件 not in 主体解析器表:#未登记
        return 未登记#不受作用域过滤
    return 主体解析器表[事件]#None 或解析函数
