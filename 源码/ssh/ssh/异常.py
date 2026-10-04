class ssh错误(Exception):#本包异常基类
    'SSH 辅助协议失败'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 远程操作错误(ssh错误):#带码远端错误
    '保留类型化文件系统或沙箱码'
    def __init__(自身,消息,码=None):#记下英文消息与码
        '用原样英文消息构造'
        super().__init__(消息)#英文消息
        自身.name='RemoteOperationError'#固定名
        自身.code=码#可选码
