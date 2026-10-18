'shell.overlay 上的共享原生平台页'
from ...模块.客户端.通告 import 取握手窗口
from .平台覆盖层 import 平台覆盖层
from .文案 import 中文

__all__=['账号平台宿主']

def 读全量(钩):
    '钩子选出整份快照'
    if 钩 is None:
        return None
    def 全量(快照):
        '原样返回'
        return 快照
    return 钩(全量)

class 账号平台宿主:
    '没有请求时不画。有请求时交出平台覆盖层'
    def __init__(自身,属性):
        '记下原生桥和当前请求'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.覆盖=None
        自身.已订=False
        自身.退订=None
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '绘制中再来一次只记一笔'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画出(自身):
        '请求是 null 时拿掉覆盖层'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        请求=读全量(属性.get('usePage'))
        if not isinstance(请求,dict):
            if 自身.覆盖 is not None:
                自身.覆盖.拆除()
                自身.覆盖=None
            自身.订上()
            return
        覆盖属性={
            'window':窗口,
            'bridge':属性.get('platform'),
            'page':请求.get('page'),
            'backLabel':中文['backToHarness'],
            'loadingLabel':中文['loading'],
            'failureLabel':中文['platformFailed'],
            'retryLabel':中文['platformRetry'],
            'onClose':属性.get('closePage'),
        }
        if 自身.覆盖 is None:
            自身.覆盖=平台覆盖层(覆盖属性)
        else:
            自身.覆盖.更新(覆盖属性)
            自身.覆盖.渲染()
        自身.订上()

    def 订上(自身):
        '请求变化时重画'
        if 自身.已订:
            return
        钩=自身.属性.get('usePage')
        订=getattr(钩,'_subscribe',None) if 钩 is not None else None
        if callable(订) is not True:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()
        自身.退订=订(变更)
        自身.已订=True

    def 拆除(自身):
        '卸下覆盖层和订阅'
        if 自身.覆盖 is not None:
            自身.覆盖.拆除()
            自身.覆盖=None
        if 自身.退订 is not None:
            自身.退订()
            自身.退订=None
        自身.已订=False
