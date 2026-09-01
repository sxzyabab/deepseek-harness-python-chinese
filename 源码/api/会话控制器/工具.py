"""会话控制器公共辅助。"""
__all__=['取字段','解开','远程错误','远程错误消息','信号已中止']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if hasattr(值,'wait') and callable(值.wait):#可等待
        return 值.wait()#等待
    return 值#同步值

class 远程错误(Exception):#Typert Remote 失败
    """对齐上游 RemoteError。"""
    def __init__(自身,码,消息,详情=None,*,cause=None):#构造
        """记下 code/message/details。"""
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details=详情 or {}#详情
        if cause is not None:#原因
            自身.__cause__=cause#链接

def 远程错误消息(错误):#取消息
    """把未知错误收成字符串。"""
    if isinstance(错误,BaseException):#异常
        return str(错误)#消息
    return str(错误)#原样

def 信号已中止(信号):#读中止
    """AbortSignal 是否已中止。"""
    if 信号 is None:#无
        return False#未中止
    return bool(getattr(信号,'aborted',False))#aborted
