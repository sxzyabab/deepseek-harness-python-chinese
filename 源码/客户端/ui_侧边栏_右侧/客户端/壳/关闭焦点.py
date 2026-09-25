"""页操作替换停靠/浮动窗格元素后的焦点连续性。
开/关前用同步刷 DOM 提交，再把焦点落到仍可见的窗格。
"""
from ..焦点 import 可见侧栏窗格#可见窗格查找

__all__=['开页并聚焦窗格','关页并聚焦窗格']#仅中文公开名

def 开页并聚焦窗格(文档,会话标识,打开):
    """打开或拆分选中的页，在 DOM 提交后聚焦该窗格。
    文档为拥有输入焦点的产品文档；会话标识为正在打开页的会话；
    打开为同步操作，返回选中窗格，未变则为 None。
    """
    窗格标识=[None]#闭包箱
    def 提交():
        """同步刷 DOM 内执行打开。"""
        窗格标识[0]=打开()#记下窗格
    if hasattr(文档,'flushSync'):#有刷同步
        文档.flushSync(提交)#同步刷
    else:#无则直跑
        提交()#直跑
    if 窗格标识[0] is not None:#有窗格
        窗=可见侧栏窗格(文档,会话标识,窗格标识[0])#可见窗
        if 窗 is not None:#有
            窗.focus({'preventScroll':True})#聚焦

def 关页并聚焦窗格(文档,会话标识,窗格标识,关闭):
    """先提交聚焦页的移除，再聚焦仍存活的可见窗格。
    文档为拥有输入焦点的产品文档；会话标识为正在关页的会话；
    窗格标识为正关闭的窗格，若幸存则优先；关闭为同步清理与布局移除。
    """
    先前=文档.activeElement#关前焦点
    拥有方=先前.closest('[data-sidebar-right-session]') if 先前 is not None else None#会话根
    源=先前.closest('[data-dockkit-pane], [data-dockkit-float]') if 先前 is not None else None#窗格容器
    源窗格=None#源窗格 id
    if 源 is not None:#有源
        源窗格=getattr(源.dataset,'dockkitPane',None) or getattr(源.dataset,'dockkitFloat',None)#id
    拥有会话=getattr(拥有方.dataset,'sidebarRightSession',None) if 拥有方 is not None else None#会话
    保留=拥有会话==会话标识 and 源窗格==窗格标识#关前焦点在本窗
    if hasattr(文档,'flushSync'):#有刷同步
        文档.flushSync(关闭)#同步刷关闭
    else:#无则直跑
        关闭()#直跑
    当前=文档.activeElement#关后焦点
    if (not 保留) or (当前 is not 文档.body and 当前 is not 先前):#无需再焦
        return#止
    窗=可见侧栏窗格(文档,会话标识,窗格标识)#可见窗
    if 窗 is not None:#有
        窗.focus({'preventScroll':True})#聚焦
