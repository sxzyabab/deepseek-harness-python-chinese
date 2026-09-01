"""域数据形态的错误词汇。"""
__all__=['域错误码','无效记录细节','域错误']#仅中文公开名

域错误码=(#判别码
    'already-open','facet-unsupported','invalid-record','missing-key','closed',
)#错误码结束

class 域错误(Exception):#域层抛出的错误
    """域层抛出的错误。后端失败原样以 `存储错误` 传出。"""
    name='DomainError'#错误名
    def __init__(自身,码,消息,细节=None,原因=None):#构造域错误
        super().__init__(消息)#基类消息
        自身.code=码#稳定判别码
        自身.detail=细节#无效记录位置
        if 原因 is not None:#链式原因
            自身.__cause__=原因#挂上原因
