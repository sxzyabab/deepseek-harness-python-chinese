import threading
from ..异常 import 布局错误

__all__=['布局控制器','面板信息源']


class 面板信息源:
    '根存储里的主面板选择。在屏会话读 activePanelId'
    def __init__(自身,实例):
        '记下和根登记共用的那一份存储'
        自身.实例=实例

    def 取快照(自身):
        '读 panelInfo。下次写入前是存储里的那一份'
        return 自身.实例.getSnapshot()['panelInfo']

    def 订阅(自身,监听):
        '存储变更时通知。退订函数由存储交回'
        return 自身.实例.subscribe(监听)

    getSnapshot=取快照
    subscribe=订阅


class 布局控制器:
    '别的插件用来切主面板、侧栏和右栏。panelInfo 与 usePanelInfo 是同一份选择'
    def __init__(自身,面板,有主面板,面板信息):
        '面板是根存储的动作。有主面板检查主槽。面板信息给在屏会话读'
        自身.面板=面板
        自身.有主面板=有主面板
        自身.panelInfo=面板信息
        自身.导航=threading.Event()

    def 选择面板(自身,面板标识):
        '选一个已登记的主面板，或用空标识回到对话。没登记就抛错，当前选择不动'
        if 面板标识 is not None and not 自身.有主面板(面板标识):
            raise 布局错误('layout.selectPanel: main panel "'+str(面板标识)+'" is not registered')
        自身.导航.set()
        自身.面板['selectPanel'](面板标识)

    def 开始导航(自身):
        '作废上一笔导航，返回新的未置位事件。置位表示已被下一笔或卸载打断'
        自身.导航.set()
        自身.导航=threading.Event()
        return 自身.导航

    def 拆除(自身):
        '布局卸下时作废还没走完的导航'
        自身.导航.set()

    def 切换侧栏(自身):
        '关闭和默认宽度之间切换'
        自身.面板['toggleSidebar']()

    def 打开右侧栏(自身,要轨,全屏):
        '报告右栏的轨道和全屏，不改它自己的展开记录'
        自身.面板['openRightbar'](要轨,全屏)

    def 关闭右侧栏(自身):
        '报告右栏已藏起：没有轨道，也没有拖柄'
        自身.面板['closeRightbar']()

    selectPanel=选择面板
    beginNavigation=开始导航
    dispose=拆除
    toggleSidebar=切换侧栏
    openRightbar=打开右侧栏
    closeRightbar=关闭右侧栏
