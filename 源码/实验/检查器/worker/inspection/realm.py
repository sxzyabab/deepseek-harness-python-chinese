"""Worker 拥有的活动 Host 与 Client JavaScript realm 生命周期模型。"""
#对齐上游 worker/inspection/realm.ts

__all__=['检查器realm描述','检查器realm上下文','检查器realm会话','检查器realm']#仅中文公开名

class 检查器realm描述:#realm描述
    """一个活动 realm 代数的稳定描述。"""
    def __init__(自身,realmId,sourceId,generation,kind,label):#构造
        """保存稳定身份字段。"""
        自身.realmId=realmId#realm id
        自身.sourceId=sourceId#源id
        自身.generation=generation#代数
        自身.kind=kind#种类 host|client
        自身.label=label#标签

class 检查器realm上下文:#realm上下文
    """一个 realm 的执行上下文所有权。"""
    def __init__(自身,kind,id=None,uniqueId=None,origin=None):#构造
        """native 或 synthetic 上下文。"""
        自身.kind=kind#native|synthetic
        自身.id=id#数字id
        自身.uniqueId=uniqueId#唯一id
        自身.origin=origin#origin

class 检查器realm会话:#realm会话
    """绑定到一个 realm 与一个 DevTools 连接的能力。"""
    def __init__(自身,descriptor,context,runtime,console,sources,debugger,nativeDomains,close):#构造
        """装配会话能力与关闭回调。"""
        自身.descriptor=descriptor#描述
        自身.context=context#上下文
        自身.runtime=runtime#Runtime能力
        自身.console=console#Console能力
        自身.sources=sources#源能力
        自身.debugger=debugger#Debugger能力
        自身.nativeDomains=nativeDomains#原生域能力
        自身._关闭=close#关闭回调

    def 关闭(自身):#关闭
        """释放每一个连接拥有的后端资源。"""
        自身._关闭()#回调

class 检查器realm:#检查器realm
    """可为每个 DevTools 连接创建隔离状态的活动 realm。"""
    def __init__(自身,descriptor,context,capabilities):#构造
        """保存描述、上下文与能力集。"""
        自身.descriptor=descriptor#描述
        自身.context=context#上下文
        自身.capabilities=capabilities#能力集

    def 打开会话(自身):#打开会话
        """返回一个 DevTools 连接的隔离后端状态。"""
        raise NotImplementedError#由子类实现
