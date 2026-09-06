"""语义耐久检查点策略（对齐上游 session-checkpoint-policy）。"""
from ...内核.工具 import 工具体前中止#取消前派发原因码
名称='session-checkpoint-policy'#Cordis 插件名
注入=['llm','sessionPersistence','sessions','tools']#依赖
__all__=['名称','注入','应用']#公开面

class 检查点策略错误(Exception):
    """会话检查点策略包的异常基类。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 派发前中止结果():
    """对齐 abortedBeforeDispatchResult。"""
    return {'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],'isError':True,'error':{'message':'tool call aborted before dispatch','info':{'name':'AbortError','code':工具体前中止}}}#结果

def 应用(上下文):
    """在模型流、顶层工具与 pre-step 边界刷持久化。"""
    def 模型流(选项,下一步):
        """有 sessionId 时先 flush 再下游。"""
        会话标识=选项['sessionId'] if 'sessionId' in 选项 else None#会话 id
        if 会话标识 is None:#无会话
            return 下一步()#原样
        会话=上下文.sessions.get(会话标识)#活会话
        if 会话 is None:#无活会话
            return 下一步()#原样
        def 生成器():
            """先耐久再拉流。"""
            上下文.sessions.flush(会话).等待()#刷盘
            for 块 in 下一步():#下游
                yield 块#转发
        return 生成器()#包装流
    上下文.监听('llm/stream',模型流)#挂监听
    def 工具执行(执行上下文,下一步):
        """顶层工具派发前 flush。"""
        if 执行上下文['agent'] is None or 执行上下文['parent'] is not None:#嵌套
            return 下一步()#原样
        上下文.sessions.flush(执行上下文['agent'].session).等待()#刷盘
        if 已中止(执行上下文['signal']):#已取消
            return 派发前中止结果()#标准结果
        return 下一步()#继续
    上下文.监听('tools/execute',工具执行)#挂监听
    def 步骤前(载荷,下一步):
        """每步请求前刷上一步提交。"""
        上下文.sessions.flush(载荷['agent'].session).等待()#刷盘
        return 下一步()#继续
    上下文.监听('agent/pre-step',步骤前)#挂监听

apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出槽
