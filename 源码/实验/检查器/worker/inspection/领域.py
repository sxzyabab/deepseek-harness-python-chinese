__all__=['检查器realm描述','检查器realm上下文','检查器realm会话','检查器realm']

class 检查器realm描述:
    '一个活动 realm 代数的稳定描述'
    def __init__(自身,realmId,sourceId,generation,kind,label):
        '保存稳定身份字段'
        自身.realmId=realmId
        自身.sourceId=sourceId
        自身.generation=generation
        自身.kind=kind
        自身.label=label


class 检查器realm上下文:
    '一个 realm 的执行上下文所有权'
    def __init__(自身,kind,id=None,uniqueId=None,origin=None):
        'native 或 synthetic 上下文'
        自身.kind=kind
        自身.id=id
        自身.uniqueId=uniqueId
        自身.origin=origin


class 检查器realm会话:
    '绑定到一个 realm 与一个 DevTools 连接的能力'
    def __init__(自身,descriptor,context,runtime,console,sources,debugger,nativeDomains,close):
        '装配会话能力与关闭回调'
        自身.descriptor=descriptor
        自身.context=context
        自身.runtime=runtime
        自身.console=console
        自身.sources=sources
        自身.debugger=debugger
        自身.nativeDomains=nativeDomains
        自身._关闭=close

    def 关闭(自身):
        '拆除每一个连接拥有的后端资源'
        自身._关闭()


class 检查器realm:
    '可为每个 DevTools 连接创建隔离状态的活动 realm'
    def __init__(自身,descriptor,context,capabilities):
        '保存描述、上下文与能力集'
        自身.descriptor=descriptor
        自身.context=context
        自身.capabilities=capabilities

    def 打开会话(自身):
        '返回一个 DevTools 连接的隔离后端状态'
        raise NotImplementedError
