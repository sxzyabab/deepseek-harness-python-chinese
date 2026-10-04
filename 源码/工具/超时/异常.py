class 超时原因(Exception):#能力拥有的超时中止原因
    """内部中止原因，携带能力拥有的码与已到截止。
    提供方在返回调用方之前经取超时翻译"""
    def __init__(自身,码,超时毫秒):#记下超时码与截止毫秒
        '记下能力拥有的超时码与已到截止毫秒'
        super().__init__(码+' after '+str(超时毫秒)+'ms')#拼出英文诊断文案，字面量不翻译
        自身.name='TimeoutReason'#固定错误名为TimeoutReason
        自身.code=码#能力拥有的超时码
        自身.timeoutMs=超时毫秒#已到截止毫秒

class 已中止错误(Exception):#无具体原因的中止
    '信号已中止且未携带原因异常'
    def __init__(自身):#固定英文消息
        '用原样英文消息构造'
        super().__init__('The operation was aborted')#英文消息

class 超时错误(Exception):#本包校验失败
    '超时库入参非法'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息
