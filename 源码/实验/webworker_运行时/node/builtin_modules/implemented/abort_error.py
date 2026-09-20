__all__=['中止错误','已中止','若已中止则抛出']

class 中止错误(Exception):
    """携带 Node 稳定错误码的取消错误；中止原因作异常属性，不挂在信号上。"""
    def __init__(自身,原因=None):
        """记下 AbortError 面与可选原因。"""
        super().__init__('The operation was aborted')
        自身.name='AbortError'
        自身.code='ABORT_ERR'
        自身.原因=原因

def 已中止(信号):
    """信号是否已中止；信号是 threading.Event。"""
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    """已中止则抛出 AbortError。"""
    if 已中止(信号):
        raise 中止错误()
