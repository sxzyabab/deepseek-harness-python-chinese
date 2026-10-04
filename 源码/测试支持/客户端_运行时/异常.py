class 客户端测试运行时错误(Exception):#本包组装失败
    '客户端测试运行时失败'

    def __init__(自身,消息,cause=None):#构造
        '记下英文消息并可选挂上原因'
        super().__init__(消息)#消息原样英文
        if cause is not None:#有原因
            自身.__cause__=cause#链式

#上游 @deepseek-ai/dsh-typert-protocol RemoteError；包尚未迁完时内联
class 远程错误(Exception):#远程错误
    'Remote 面失败'

    def __init__(自身,码,消息,细节=None,cause=None):#构造
        '记下码、消息与细节'
        super().__init__(消息)#基类
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details=细节 or {}#细节
        if cause is not None:#有 cause
            自身.__cause__=cause#链式
