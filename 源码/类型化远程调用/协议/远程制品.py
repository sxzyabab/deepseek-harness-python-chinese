__all__=['透传模式','严格编解码','调用描述符','远程贡献','取远程错误']

class 透传模式:
    '把线路值原样交回。结构是否合法由宿主方法边界负责'
    def parse(自身,值):
        '原样返回'
        return 值

def 严格编解码(类型符号,模式=None):
    'mode 为 strict。未给模式时用透传'
    if 模式 is None:
        模式=透传模式()
    return {'mode':'strict','typeSymbol':类型符号,'schema':模式}

def 调用描述符(
    标识,服务,命名空间,方法,参数列表,结果编解码,源码位置,
    实现=None,调用=None,作用域=None,取消=None,模式=None,上行=None,
):
    '拼一条调用描述符。值为 None 的可选键不写入，以免和显式空值混成一类'
    if 调用 is None:
        调用={'kind':'direct'}
    描述符={
        'id':标识,
        'service':服务,
        'namespace':命名空间,
        'method':方法,
        'invocation':调用,
        'parameters':list(参数列表),
        'result':结果编解码,
        'sourceLocation':源码位置,
    }
    if 实现 is not None:
        描述符['implementation']=实现
    if 作用域 is not None:
        描述符['scope']=作用域
    if 取消 is not None:
        描述符['cancellation']=取消
    if 模式 is not None:
        描述符['mode']=模式
    if 上行 is not None:
        描述符['uplink']=上行
    return 描述符

def 远程贡献(包名,描述符列表):
    'package 与 descriptors。描述符列表允许为空'
    return {'package':包名,'descriptors':list(描述符列表)}

def 取远程错误(值):
    '用 isDSHRemoteError 与 code 识别远程错误，不看异常类型'
    if 值 is None:
        return None
    if getattr(值,'isDSHRemoteError',None) is True and isinstance(getattr(值,'code',None),str):
        return 值
    return None
