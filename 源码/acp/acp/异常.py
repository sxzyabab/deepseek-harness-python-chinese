class ACP线路错误(Exception):
    '本包异常基类'

class 请求错误(ACP线路错误):
    'ACP 线路错误，保留 code 与可选 data'
    def __init__(自身,码,消息,数据=None):
        '记下错误码、消息与可选载荷'
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.data=数据#可选 data
        自身.name='RequestError'#固定名

    @staticmethod
    def 非法参数(数据,细节):
        '把非法参数细节保留在线路错误消息里'
        return 请求错误(-32602,细节,数据)#invalid params

    @staticmethod
    def 内部错误(数据,细节):
        '把失败细节保留为内部错误'
        return 请求错误(-32603,细节,数据)#internal error

class ACP内容错误(Exception):
    '稳定 ACP 请求失败分类，不含原始二进制'
    def __init__(自身,消息,种类,原因=None):
        '记下无内联二进制的协议细节'
        super().__init__(消息)
        自身.name='AcpContentError'
        自身.kind=种类
        if 原因 is not None:
            自身.__cause__=原因
