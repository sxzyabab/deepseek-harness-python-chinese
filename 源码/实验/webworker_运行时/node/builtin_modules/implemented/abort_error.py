"""构建可中止内置 API 共用的 Node 风格取消错误。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/abort-error.ts`。
公开面仅中文名。文件名下划线以便 Python import。
本包中止原语也落在此文件：信号一律 threading.Event。
"""
__all__=['中止错误','已中止','若已中止则抛出']#仅中文公开名

class 中止错误(Exception):#Node AbortError
    """携带 Node 稳定错误码的取消错误；中止原因作异常属性，不挂在信号上。"""
    def __init__(自身,原因=None):#构造
        """记下 AbortError 面与可选原因。"""
        super().__init__('The operation was aborted')#基类消息
        自身.name='AbortError'#Node 面 name
        自身.code='ABORT_ERR'#稳定错误码
        自身.原因=原因#原因对象

def 已中止(信号):#信号是否已中止
    """信号是否已中止；信号是 threading.Event。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件置位

def 若已中止则抛出(信号):#已中止则抛
    """已中止则抛出 AbortError。"""
    if 已中止(信号):#已置位
        raise 中止错误()#抛取消
