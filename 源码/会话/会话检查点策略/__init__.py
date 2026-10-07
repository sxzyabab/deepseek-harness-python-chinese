'语义耐久检查点策略'
from ...内核.工具 import 工具体前中止#取消前派发原因码
from ...基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from .异常 import 检查点策略错误#本包异常

def 已中止(信号):
    '信号按 Event 定死。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 已置位

包名='@deepseek-ai/dsh-session-checkpoint-policy'
名称='session-checkpoint-policy'
依赖=['llm','sessionPersistence','sessions','tools']

__all__=['包名','名称','依赖','应用','默认']

def 派发前中止结果():
    '工具派发前已中止时返回的错误结果载荷'
    return {'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],'isError':True,'error':{'message':'tool call aborted before dispatch','info':{'name':'AbortError','code':工具体前中止}}}

def 应用(上下文):
    '在模型流、顶层工具与 pre-step 边界刷持久化'
    def 模型流(选项,下一步):
        '有 sessionId 时返回先 flush 再下游的迭代器'
        会话标识=选项['sessionId'] if 'sessionId' in 选项 else None
        if 会话标识 is None:
            return 下一步()
        会话=上下文.sessions.get(会话标识)
        if 会话 is None:
            return 下一步()
        def 检查点后流():
            '迭代时先刷耐久，再让出下游块'
            上下文.sessions.flush(会话)#同步耐久屏障，失败直接抛出
            yield from 下一步()
        return 检查点后流()
    上下文.监听('llm/stream',模型流)
    def 工具执行(执行上下文,下一步):
        '顶层工具派发前 flush，返回期约'
        执行前=期约()#返回期约，解决值是工具结果
        def 派发(刷新结果=None):
            '耐久已刷：已中止则给派发前中止结果，否则接下游'
            try:
                if 已中止(执行上下文['signal']):
                    执行前.解决(派发前中止结果())
                    return
                执行前.解决(下一步())
            except BaseException as 错误:#下游同步失败收进结果
                执行前.拒绝(错误)
        if 执行上下文['agent'] is None or 执行上下文['parent'] is not None:
            try:
                执行前.解决(下一步())#非顶层调用不刷
            except BaseException as 错误:#下游同步失败收进结果
                执行前.拒绝(错误)
            return 执行前
        上下文.sessions.flush(执行上下文['agent'].session).然后(派发,执行前.拒绝)
        return 执行前
    上下文.监听('tools/execute',工具执行)
    def 步骤前(载荷,下一步):
        '每步请求前刷上一步提交，返回期约'
        步骤前结果=期约()#返回期约，解决值是下游决定
        def 已刷新(刷新结果=None):
            '耐久已刷：接下游'
            try:
                步骤前结果.解决(下一步())
            except BaseException as 错误:#下游同步失败收进结果
                步骤前结果.拒绝(错误)
        上下文.sessions.flush(载荷['agent'].session).然后(已刷新,步骤前结果.拒绝)
        return 步骤前结果
    上下文.监听('agent/pre-step',步骤前)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
