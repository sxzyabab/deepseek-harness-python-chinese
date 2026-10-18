'关或开之后，等页面更新完再把焦点放回还在的窗'
from ..焦点 import 可见侧栏窗格

__all__=['打开并聚焦窗格','关闭并聚焦窗格']


def 打开并聚焦窗格(文档,会话标识,打开):
    '先做打开，再聚焦它选中的窗'
    窗格标识=打开()
    if 窗格标识 is None:
        return
    窗=可见侧栏窗格(文档,会话标识,窗格标识)
    if 窗 is not None:
        窗.focus({'preventScroll':True})


def 关闭并聚焦窗格(文档,会话标识,窗格标识,关闭):
    '先关掉。焦点还在原处或 body 上时，聚焦还在的窗'
    之前=文档.activeElement
    拥有=None if 之前 is None else 之前.closest('[data-sidebar-right-session]')
    来源=None if 之前 is None else 之前.closest('[data-dockkit-pane], [data-dockkit-float]')
    会话相同=False
    if 拥有 is not None:
        数据=getattr(拥有,'dataset',None)
        读到=None if 数据 is None else getattr(数据,'sidebarRightSession',None)
        if 读到 is None:
            读到=拥有.getAttribute('data-sidebar-right-session')
        会话相同=读到==会话标识
    来源标识=None
    if 来源 is not None:
        数据=getattr(来源,'dataset',None)
        来源标识=None if 数据 is None else getattr(数据,'dockkitPane',None)
        if 来源标识 is None and 数据 is not None:
            来源标识=getattr(数据,'dockkitFloat',None)
        if 来源标识 is None:
            来源标识=来源.getAttribute('data-dockkit-pane')
            if 来源标识 is None:
                来源标识=来源.getAttribute('data-dockkit-float')
    保留=会话相同 and 来源标识==窗格标识
    关闭()
    if not 保留:
        return
    if 文档.activeElement is not 文档.body and 文档.activeElement is not 之前:
        return
    窗=可见侧栏窗格(文档,会话标识,窗格标识)
    if 窗 is not None:
        窗.focus({'preventScroll':True})
