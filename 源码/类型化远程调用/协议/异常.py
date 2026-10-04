__all__=('查找策略失败','远程错误','协议消息错误')#仅中文公开名

class 查找策略失败(Exception):#lookup 策略拒绝错误
    'lookup 策略拒绝，其带类型的载荷属于当前边界适配器'
    def __init__(自身,失败载荷):#用适配器失败构造
        '包装一次适配器失败，不暴露被拒绝的身份'
        super().__init__('Typert lookup policy rejected the requested identity')#固定英文消息
        自身.name='TypertLookupFailure'#错误名
        自身.failure=失败载荷#适配器失败载荷

class 远程错误(Exception):
    """一次远程调用失败：稳定码、诊断与结构化细节。
    判别按 code
    """
    def __init__(自身,code,message,details,原因=None):
        'code/message/details 为线路字段；原因仅同进程存活'
        super().__init__(message)
        自身.name='RemoteError'
        自身.code=code
        自身.message=message
        自身.details=details
        自身.isDSHRemoteError=True
        if 原因 is not None:
            自身.__cause__=原因

class 协议消息错误(Exception):
    '只带一条消息的协议拒绝'
