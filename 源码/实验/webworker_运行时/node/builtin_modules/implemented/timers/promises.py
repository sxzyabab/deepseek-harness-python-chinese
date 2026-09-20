import threading
from ..abort_error import 中止错误,已中止,若已中止则抛出

__all__=[
    'setTimeout','setImmediate','scheduler','__esModule','default',
]

def 取信号(选项):
    """选项是 dict；缺席键表示无信号。"""
    if 选项 is None:
        return None
    if 'signal' not in 选项:
        return None
    return 选项['signal']

def 设超时(延迟毫秒=None,值=None,选项=None):
    """阻塞到延迟结束；信号中止时抛 AbortError。"""
    信号=取信号(选项)
    若已中止则抛出(信号)
    秒=0.0 if 延迟毫秒 is None else 延迟毫秒/1000.0
    if 信号 is None:
        threading.Event().wait(秒)
        return 值
    if 信号.wait(秒):
        raise 中止错误()
    return 值

def 设立即(值=None):
    """零延迟后返回。"""
    return 设超时(0,值)

def 等待(延迟毫秒=None,选项=None):
    """等待指定毫秒。"""
    return 设超时(延迟毫秒,None,选项)

def 让出():
    """让出一拍。"""
    return 设超时(0)

setTimeout=设超时
setImmediate=设立即
scheduler={'wait':等待,'yield':让出}
__esModule=True
default={'setTimeout':设超时,'setImmediate':设立即,'scheduler':scheduler}
