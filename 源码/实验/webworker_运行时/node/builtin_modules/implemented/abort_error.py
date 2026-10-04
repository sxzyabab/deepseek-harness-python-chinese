from ....异常 import 中止错误

__all__=['中止错误','已中止','若已中止则抛出']

def 已中止(信号):
    '信号是否已中止；信号是 threading.Event'
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    '已中止则抛出 AbortError'
    if 已中止(信号):
        raise 中止错误()
