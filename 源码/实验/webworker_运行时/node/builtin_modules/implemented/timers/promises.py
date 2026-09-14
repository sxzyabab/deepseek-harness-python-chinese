import threading#事件等待
from ..abort_error import 中止错误,已中止,若已中止则抛出#本包中止原语

__all__=[#中文公开名与Node英文挂名
    '设超时','设立即',
    'setTimeout','setImmediate','scheduler','__esModule','default',
]#公开结束

def 取信号(选项):#从选项取 Event
    """选项是 dict；缺席键表示无信号。"""
    if 选项 is None:#无选项
        return None#无信号
    if 'signal' not in 选项:#未给信号
        return None#无信号
    return 选项['signal']#Event

def 设超时(延迟毫秒=None,值=None,选项=None):#延迟后返回
    """阻塞到延迟结束；信号中止时抛 AbortError。"""
    信号=取信号(选项)#中止事件
    若已中止则抛出(信号)#入口已中止
    秒=0.0 if 延迟毫秒 is None else 延迟毫秒/1000.0#毫秒转秒
    if 信号 is None:#无中止
        threading.Event().wait(秒)#纯延迟
        return 值#到期值
    if 信号.wait(秒):#等待期间置位
        raise 中止错误()#取消
    return 值#到期值

def 设立即(值=None):#下一拍返回
    """零延迟后返回。"""
    return 设超时(0,值)#零延迟

def 等待(延迟毫秒=None,选项=None):#scheduler.wait
    """等待指定毫秒。"""
    return 设超时(延迟毫秒,None,选项)#委托设超时

def 让出():#scheduler.yield
    """让出一拍。"""
    return 设超时(0)#零延迟

setTimeout=设超时#Node面
setImmediate=设立即#Node面
scheduler={'wait':等待,'yield':让出}#调度辅助
__esModule=True#CJS互操作
default={'setTimeout':设超时,'setImmediate':设立即,'scheduler':scheduler}#默认导出
