from ...模块.客户端.通告 import 取握手窗口
from .高亮 import 支持高亮

__all__=['使用视口高亮']

激活表={}
观察=None

def 观察器(窗口):
    '全文档一份。相交过一次就不再观察'
    global 观察
    if 观察 is not None:
        return 观察
    构造=getattr(窗口,'IntersectionObserver',None)
    if 构造 is None:
        return None
    def 回调(记录,观察者):
        '第一次进入视口就激活并卸掉'
        for 条 in 记录:
            if 条.isIntersecting is not True:
                continue
            目标=条.target
            函数=激活表.get(目标)
            if 函数 is None:
                continue
            del 激活表[目标]
            观察者.unobserve(目标)
            函数()
        if len(激活表)==0:
            观察者.disconnect()
            global 观察
            观察=None
    观察=构造(回调)
    return 观察

def 使用视口高亮(元素,语言,激活):
    '支持的语言第一次进视口才激活。没有 IntersectionObserver 就立刻激活。返回拆除函数'
    if not 支持高亮(语言):
        return lambda: None
    if 元素 is None:
        return lambda: None
    窗口=元素.ownerDocument.defaultView if hasattr(元素,'ownerDocument') else 取握手窗口()
    器=观察器(窗口)
    if 器 is None:
        激活()
        return lambda: None
    激活表[元素]=激活
    器.observe(元素)
    def 拆除():
        '还没激活就取消观察'
        if 元素 in 激活表:
            del 激活表[元素]
        if 观察 is not None:
            观察.unobserve(元素)
    return 拆除
