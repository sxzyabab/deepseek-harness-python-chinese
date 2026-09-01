"""语义耐久检查点策略（对齐上游 session-checkpoint-policy）。"""
from ...内核.工具 import 工具体前中止#取消前派发原因码
名称='session-checkpoint-policy'#Cordis 插件名
注入=['llm','sessionPersistence','sessions','tools']#依赖
name=名称#Cordis 插件名
inject=注入#Cordis 依赖
__all__=['名称','注入','应用','默认']#公开面

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    """可等待则等待。"""
    if callable(getattr(值,'wait',None)):#Future
        return 值.wait()#等待
    if callable(getattr(值,'等待',None)):#中文
        return 值.等待()#等待
    return 值#同步

def 已中止(信号):#是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无
        return False#否
    return getattr(信号,'aborted',False) or getattr(信号,'已中止',False)#旗标

def 派发前中止结果():#工具派发前取消结果
    """对齐 abortedBeforeDispatchResult。"""
    return {'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],'isError':True,'error':{'message':'tool call aborted before dispatch','info':{'name':'AbortError','code':工具体前中止}}}#结果

def 应用(上下文):#安装检查点监听器
    """在模型流、顶层工具与 pre-step 边界刷持久化。"""
    def 模型流(选项,下一步):#llm/stream
        """有 sessionId 时先 flush 再下游。"""
        会话标识=取字段(选项,'sessionId')#会话 id
        if 会话标识 is None:#无会话
            return 下一步()#原样
        会话=上下文.sessions.get(会话标识)#活会话
        if 会话 is None:#无活会话
            return 下一步()#原样
        def 生成器():#异步生成器包装
            """先耐久再拉流。"""
            解开(上下文.sessions.flush(会话))#刷盘
            for 块 in 下一步():#下游
                yield 块#转发
        return 生成器()#包装流
    上下文.on('llm/stream',模型流)#挂监听
    def 工具执行(执行上下文,下一步):#tools/execute
        """顶层工具派发前 flush。"""
        if 取字段(执行上下文,'agent') is None or 取字段(执行上下文,'parent') is not None:#嵌套
            return 下一步()#原样
        解开(上下文.sessions.flush(取字段(执行上下文,'agent').session))#刷盘
        信号=取字段(执行上下文,'signal')#信号
        if 已中止(信号):#已取消
            return 派发前中止结果()#标准结果
        return 下一步()#继续
    上下文.on('tools/execute',工具执行)#挂监听
    def 步骤前(载荷,下一步):#agent/pre-step
        """每步请求前刷上一步提交。"""
        解开(上下文.sessions.flush(取字段(载荷,'agent').session))#刷盘
        return 下一步()#继续
    上下文.on('agent/pre-step',步骤前)#挂监听

apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
默认=应用#中文默认导出
