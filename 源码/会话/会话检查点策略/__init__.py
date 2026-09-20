"""语义耐久检查点策略。"""
from ...内核.工具 import 工具体前中止#取消前派发原因码

包名='@deepseek-ai/dsh-session-checkpoint-policy'
名称='session-checkpoint-policy'
依赖=['llm','sessionPersistence','sessions','tools']

__all__=['包名','名称','依赖','应用','默认']

class 检查点策略错误(Exception):
    """会话检查点策略包的异常基类。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:
        return False
    return 信号._事件.is_set()

def 派发前中止结果():
    """工具派发前已中止时返回的错误结果载荷。"""
    return {'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],'isError':True,'error':{'message':'tool call aborted before dispatch','info':{'name':'AbortError','code':工具体前中止}}}

def 应用(上下文):
    """在模型流、顶层工具与 pre-step 边界刷持久化。"""
    def 模型流(选项,下一步):
        """有 sessionId 时先 flush 再下游。"""
        会话标识=选项['sessionId'] if 'sessionId' in 选项 else None
        if 会话标识 is None:
            return 下一步()
        会话=上下文.sessions.get(会话标识)
        if 会话 is None:
            return 下一步()
        def 生成器():
            """先耐久再拉流。"""
            上下文.sessions.flush(会话).等待()
            for 块 in 下一步():
                yield 块
        return 生成器()
    上下文.监听('llm/stream',模型流)
    def 工具执行(执行上下文,下一步):
        """顶层工具派发前 flush。"""
        if 执行上下文['agent'] is None or 执行上下文['parent'] is not None:
            return 下一步()
        上下文.sessions.flush(执行上下文['agent'].session).等待()
        if 已中止(执行上下文['signal']):
            return 派发前中止结果()
        return 下一步()
    上下文.监听('tools/execute',工具执行)
    def 步骤前(载荷,下一步):
        """每步请求前刷上一步提交。"""
        上下文.sessions.flush(载荷['agent'].session).等待()
        return 下一步()
    上下文.监听('agent/pre-step',步骤前)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
