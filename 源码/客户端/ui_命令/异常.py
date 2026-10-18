def 目录等待中止原因(信号):
    '把目录等待的中止收成异常。信号上的原因已是异常则原样交回'
    原因=getattr(信号,'reason',None)#AbortSignal.reason
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样
    return Exception('command directory wait aborted')#否则收成 Error
