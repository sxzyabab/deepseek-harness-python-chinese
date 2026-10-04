__all__=(#仅中文公开名
    'SDK客户端错误','传输已关闭错误','请求超时错误','SDK协议错误','SDK拆除错误',
)#公开面结束

class SDK客户端错误(Exception):
    '本包异常基类'

class 传输已关闭错误(SDK客户端错误):
    '运行时子进程已消失或不可用'
    def __init__(自身,消息):
        '记下失败描述，含任何 stderr 尾部'
        super().__init__(消息)#交给基类
        自身.name='TransportClosedError'#固定错误名

class 请求超时错误(SDK客户端错误):
    '某次请求超过了 requestTimeoutMs'
    def __init__(自身,消息):
        '记下哪个方法超时'
        super().__init__(消息)#交给基类
        自身.name='RequestTimeoutError'#固定错误名

class SDK协议错误(SDK客户端错误):
    '运行时给出了文档协议之外的应答'
    def __init__(自身,消息):
        '记下协议违规描述'
        super().__init__(消息)#交给基类
        自身.name='SdkProtocolError'#固定错误名

class SDK拆除错误(Exception):
    '拆除阶梯失败'
