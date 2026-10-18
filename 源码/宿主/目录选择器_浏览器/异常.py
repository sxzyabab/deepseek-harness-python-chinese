'浏览后端不另定义异常类。中止原因和文件系统失败的文本在这里，目录选择器错误仍由目录选择缝抛出'
__all__=['已中止','作为错误','失败文本','若中止则抛']#同目录公开名


def 已中止(信号):
    '没有信号视为未中止。AbortSignal 看 aborted，threading.Event 看 is_set'
    if 信号 is None:#没有寿命
        return False#未中止
    if getattr(信号,'aborted',False):#AbortSignal
        return True#已中止
    置位=getattr(信号,'is_set',None)#Event
    if callable(置位):#有置位方法
        return bool(置位())#是否已置位
    return False#没有这两种面


def 作为错误(原因):
    '已经是异常则原样返回。没有原因时用固定句。其余转成异常'
    if isinstance(原因,BaseException):#异常原样
        return 原因#同一对象
    if 原因 is None:#没有原因
        return Exception('The operation was aborted.')#固定句
    return Exception(str(原因))#文本原因


def 失败文本(错误):
    '异常取消息，其余转成文本'
    if isinstance(错误,BaseException):#异常
        文本=str(错误)#消息
    else:#其它抛出
        文本=str(错误)#转文本
    return 文本#说明用的文本


def 若中止则抛(信号):
    '已中止则抛出原因。没有信号或未中止则返回'
    if not 已中止(信号):#还活着
        return None#继续
    raise 作为错误(getattr(信号,'reason',None))#中止原因
