'翻译请求用的取消通道、截止和配置读取'
import threading
from ...基础设施.通用工具 import 启动守护线程
from ...工具.超时.异常 import 超时原因

__all__=['中止信号','中止控制器','合并信号','截止','已中止','若已中止则抛出','取原因','取信号超时','码元数','读易失']

class 中止信号:
    '同时满足持久化的 is_set/原因 和语言模型的 _事件/_异常'
    def __init__(自身):
        '创建一条尚未中止的通道'
        自身._事件=threading.Event()
        自身._异常=None
        自身.原因=None

    def is_set(自身):
        '持久化按 Event 读中止'
        return 自身._事件.is_set()

    def 触发(自身,原因=None):
        '只采纳第一次原因'
        if 自身._事件.is_set():
            return
        if isinstance(原因,BaseException):
            自身._异常=原因
            自身.原因=原因
        elif 原因 is not None:
            包装=RuntimeError(str(原因))
            自身._异常=包装
            自身.原因=包装
        自身._事件.set()

class 中止控制器:
    '持有一条中止信号'
    def __init__(自身):
        '新建未中止的信号'
        自身.信号=中止信号()

    def 中止(自身,原因=None):
        '触发信号'
        自身.信号.触发(原因)

class 合并信号:
    '任一来源中止即中止；不另开线程'
    def __init__(自身,*来源):
        '记下要观察的来源'
        自身._来源=来源
        自身._事件=自身

    def is_set(自身):
        '任一来源已中止'
        for 源 in 自身._来源:
            if 已中止(源):
                return True
        return False

    @property
    def 原因(自身):
        '第一个已中止来源的原因'
        for 源 in 自身._来源:
            if 已中止(源):
                return 取原因(源)
        return None

    @property
    def _异常(自身):
        '语言模型读取的异常；不是异常则没有'
        原因=自身.原因
        if isinstance(原因,BaseException):
            return 原因
        return None

def 已中止(信号):
    '无信号视为未中止；兼容 Event、本包信号和语言模型信号'
    if 信号 is None:
        return False
    探测=getattr(信号,'is_set',None)
    if callable(探测):
        return bool(探测())
    事件=getattr(信号,'_事件',None)
    if 事件 is not None and 事件 is not 信号 and callable(getattr(事件,'is_set',None)):
        return bool(事件.is_set())
    return False

def 取原因(信号):
    '已中止时返回原因，否则 None'
    if not 已中止(信号):
        return None
    原因=getattr(信号,'原因',None)
    if 原因 is not None:
        return 原因
    return getattr(信号,'_异常',None)

def 若已中止则抛出(信号):
    '已中止则抛出承载的异常'
    if not 已中止(信号):
        return
    原因=取原因(信号)
    if isinstance(原因,BaseException):
        raise 原因
    if 原因 is not None:
        raise RuntimeError(str(原因))
    raise RuntimeError('The operation was aborted')

def 取信号超时(信号,码):
    '信号原因是指定码的超时原因时返回它'
    原因=取原因(信号)
    if isinstance(原因,超时原因) and 原因.code==码:
        return 原因
    return None

def 码元数(文本):
    '按 UTF-16 码元计长度，一个辅助平面字符算两个'
    return len(文本.encode('utf-16-le'))//2

def 读易失(字段):
    '字典、列表和字符串本身就是值；只有其余对象的 get 才是易失读取'
    if isinstance(字段,(dict,list,str,bytes,bytearray)):
        return 字段
    取值=getattr(字段,'get',None)
    if callable(取值):
        return 取值()
    return 字段

class 截止句柄:
    '在超时或上游中止时触发自己的信号；释放后监视线程退出'
    def __init__(自身,来源,超时毫秒,码):
        '启动定时器和一条短轮询'
        自身.信号=中止信号()
        自身.码=码
        自身.超时毫秒=超时毫秒
        自身._来源=来源
        自身._停=threading.Event()
        自身._定时=threading.Timer(超时毫秒/1000.0,自身._到期)
        自身._定时.daemon=True
        自身._定时.start()
        启动守护线程(自身._监视)

    def _到期(自身):
        '定时器到点，记超时原因'
        自身.信号.触发(超时原因(自身.码,自身.超时毫秒))
        自身._停.set()

    def _监视(自身):
        '上游中止则抄下原因；释放或本信号中止则退出'
        while not 自身._停.is_set():
            for 源 in 自身._来源:
                if 已中止(源):
                    自身.信号.触发(取原因(源))
                    自身._定时.cancel()
                    自身._停.set()
                    return
            if 已中止(自身.信号):
                自身._停.set()
                return
            自身._停.wait(0.05)

    def 释放(自身):
        '停掉定时器和监视'
        自身._停.set()
        自身._定时.cancel()

    def __enter__(自身):
        '进入 with'
        return 自身

    def __exit__(自身,类型,值,栈):
        '离开 with 时释放'
        自身.释放()
        return False

def 截止(上游,超时毫秒,码):
    '把一个或一组上游信号收成带超时的截止句柄'
    if isinstance(上游,(list,tuple)):
        来源=tuple(上游)
    else:
        来源=(上游,)
    return 截止句柄(来源,超时毫秒,码)
