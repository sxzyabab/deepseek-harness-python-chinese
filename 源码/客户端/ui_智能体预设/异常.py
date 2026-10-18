'名册、切换和保存的失败写在页面快照的 error 上。本包没有单独的异常类'

def 远程消息(错误):
    '远程错误取 message，异常取消息，其余转成字符串'
    if isinstance(错误,BaseException):#异常
        return str(错误)#消息
    if isinstance(错误,dict):#字典
        消息=错误.get('message')#message
        if isinstance(消息,str):#有
            return 消息#原文
    消息=getattr(错误,'message',None)#对象
    if isinstance(消息,str):#有
        return 消息#原文
    return str(错误)#其余
