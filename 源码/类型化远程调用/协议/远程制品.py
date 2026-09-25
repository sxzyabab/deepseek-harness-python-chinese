__all__=['透传模式','严格编解码','调用描述符','远程贡献','远程错误','取远程错误']#公开面

class 透传模式:#边界透传解析
    """把线路值原样交回；结构校验由宿主方法边界负责。"""
    def parse(自身,值):#解析
        """原样返回。"""
        return 值#透传

def 严格编解码(类型符号,模式=None):#构造严格编解码
    """mode=strict + typeSymbol + schema。"""
    if 模式 is None:#缺省透传
        模式=透传模式()#透传
    return {'mode':'strict','typeSymbol':类型符号,'schema':模式}#编解码

def 调用描述符(#组装一条 InvocationDescriptor
    标识,服务,命名空间,方法,参数列表,结果编解码,源码位置,
    实现=None,调用=None,作用域=None,取消=None,模式=None,上行=None,
):#结束签名
    """拼一条可挂载的调用描述符。"""
    if 调用 is None:#缺省直接调用
        调用={'kind':'direct'}#直接
    描述符={#描述符主体
        'id':标识,#稳定 id
        'service':服务,#服务键
        'namespace':命名空间,#命名空间
        'method':方法,#方法名
        'invocation':调用,#调用约定
        'parameters':list(参数列表),#参数表
        'result':结果编解码,#结果编解码
        'sourceLocation':源码位置,#源码位置
    }#主体结束
    if 实现 is not None:#有实现别名
        描述符['implementation']=实现#实现名
    if 作用域 is not None:#有 scope
        描述符['scope']=作用域#作用域
    if 取消 is not None:#有取消
        描述符['cancellation']=取消#取消
    if 模式 is not None:#stream 投递
        描述符['mode']=模式
    if 上行 is not None:#Client→Host 上行编解码
        描述符['uplink']=上行
    return 描述符#描述符

def 远程贡献(包名,描述符列表):#组装 TYPERT_REMOTE
    """package + descriptors。"""
    return {'package':包名,'descriptors':list(描述符列表)}#贡献

class 远程错误(Exception):
    """一次远程调用失败：稳定码、诊断与结构化细节。判别按 code。"""
    def __init__(自身,code,message,details,原因=None):
        """code/message/details 为线路字段；原因仅同进程存活。"""
        super().__init__(message)
        自身.name='RemoteError'
        自身.code=code
        自身.message=message
        自身.details=details
        自身.isDSHRemoteError=True
        if 原因 is not None:
            自身.__cause__=原因

def 取远程错误(值):
    """结构识别跨模块抛出的远程错误；不按类型。"""
    if 值 is None:
        return None
    if getattr(值,'isDSHRemoteError',None) is True and isinstance(getattr(值,'code',None),str):
        return 值
    return None
