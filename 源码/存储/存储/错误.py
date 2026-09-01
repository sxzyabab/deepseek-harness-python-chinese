"""存储枢纽与后端面向错误词汇。"""
__all__=['存储错误码','存储错误']#仅中文公开名

存储错误码=(#稳定判别码
    'backend-not-found',
    'form-not-mounted',
    'duplicate-backend',
    'duplicate-mount',
    'version-mismatch',
    'malformed-medium',
    'closed',
)#错误码结束

class 存储错误(Exception):#枢纽与后端实现抛出的错误
    """枢纽与后端实现抛出的错误。`code` 是消费方可依赖的稳定契约；`message` 为诊断文本。"""
    name='StorageError'#错误名
    def __init__(自身,码,消息,原因=None):#构造存储错误
        super().__init__(消息)#基类消息
        自身.code=码#稳定判别码
        if 原因 is not None:#有链式原因
            自身.__cause__=原因#挂上原因
