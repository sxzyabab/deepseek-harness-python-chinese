def 失败说明(错误):
    '把失败收成诊断句。异常用消息，其余用字符串'
    if isinstance(错误,BaseException):
        if len(错误.args)>0 and isinstance(错误.args[0],str) and 错误.args[0]!='':
            return 错误.args[0]
        return str(错误)
    return str(错误)

__all__=[
    '失败说明','检查器错误','Client源远程错误','Client运行时远程错误','检查器查询远程错误',
    '客户端源目录错误','客户端运行时执行错误','宿主cdp桥不可用错误','宿主cdp桥原因',
]

class 检查器错误(Exception):#检查器错误基类
    '检查器包内错误基类'
    def __init__(自身,消息):#构造
        '记下英文诊断'
        super().__init__(消息)#基类
        自身.消息=消息#诊断

class Client源远程错误(Exception):#Client源远程错误
    'Client 源目录有意返回的错误'
    def __init__(自身,码,信息):#构造
        '保存错误码'
        super().__init__(信息)#基类
        自身.code=码#错误码

class Client运行时远程错误(Exception):#Client Runtime远程错误
    'Client Runtime 执行器有意返回的错误'
    def __init__(自身,码,信息):#构造
        '保存错误码'
        super().__init__(信息)#基类
        自身.code=码#错误码

class 检查器查询远程错误(Exception):#远程查询错误
    'Worker 查询处理器故意返回的失败'
    def __init__(自身,code,message):#错误码与信息
        '保存错误码与信息'
        super().__init__(message)#设置消息
        自身.code=code#错误码

class 客户端源目录错误(Exception):#Client源目录错误
    'Client 源传输序列化的有意错误'
    def __init__(自身,code,message):#绑定错误码
        '保存码与信息'
        super().__init__(message)#基类
        自身.code=code#错误码
        自身.message=message#信息

class 客户端运行时执行错误(Exception):#Client运行时执行错误
    '经类型化 Client Runtime 错误结果返回的失败'
    def __init__(自身,code,message):#绑定错误码
        '保存错误码与信息'
        super().__init__(message)#基类消息
        自身.code=code#错误码
        自身.message=message#信息

宿主cdp桥原因='Host Runtime is attached directly from the Inspector Worker'#拒绝原因

class 宿主cdp桥不可用错误(Exception):#Host CDP桥不可用
    'Host Runtime 使用 Worker 侧 Node inspector session，而非 source RPC'
    def __init__(自身,操作):#构造
        '保存操作名'
        super().__init__(f'inspector protocol: {操作} cannot use the Host source bridge; {宿主cdp桥原因}')#消息
