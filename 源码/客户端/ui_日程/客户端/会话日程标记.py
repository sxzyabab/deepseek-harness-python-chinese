'会话行前面的时钟：这一会话还有活动任务'
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from .日历图标 import 日历图标
from .会话日程状态 import 选取会话日程事实
from . import 标记样式

__all__=['会话日程标记']

def 缺省翻译(键,_参数=None):
    '无文案席时回传键'
    return 键

class 会话日程标记:
    '槽位只调用构造。没有活动任务时留空'
    def __init__(自身,属性=None):
        '记下 props。键齐了才在构造末尾画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身._已订=False
        自身._绘制中=False
        自身._待重画=False
        if 'sessionId' in 自身.属性 and 'useCatalog' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保订阅(自身):
        '目录变化时重画标记'
        if 自身._已订:
            return
        用=自身.属性['useCatalog'] if 'useCatalog' in 自身.属性 else None
        订=getattr(用,'_subscribe',None)
        if not callable(订):
            return
        自身._已订=True
        def 变(*_参数):
            '重画'
            if 自身._绘制中:
                自身._待重画=True
                return
            if getattr(自身,'_壳',None) is not None:
                自身.重画()
        订(变)

    def 渲染(自身):
        '先占壳。标记样式在模块顶层登记。'
        标记样式.样式表
        自身._绘制中=True
        try:
            自身.确保订阅()
            if getattr(自身,'_壳',None) is None:
                自身._壳=界面.element('span').classes('日程标记根 mark')
                自身._壳.on('click.stop',lambda _事件:None)
            自身.重画()
        finally:
            自身._绘制中=False
        if 自身._待重画:
            自身._待重画=False
            自身.重画()

    def 重画(自身):
        '时钟和仅供辅助技术读的数量。没有活动任务时不占格子。'
        壳=自身._壳
        壳.clear()
        属性=自身.属性
        用=属性['useCatalog'] if 'useCatalog' in 属性 else None
        if not callable(用):
            壳.style('display:none')
            return
        try:
            快照=用(lambda 当前:当前)
        except Exception as 原因:
            # 目录读失败时这一行不画标记，说明里不留路径
            页面失败文案(原因)
            壳.style('display:none')
            return
        事实=选取会话日程事实(快照,属性['sessionId'] if 'sessionId' in 属性 else None)
        if 事实['hasActive'] is not True:
            壳.style('display:none')
            return
        壳.style('display:inline-flex')
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else 缺省翻译
        with 壳:
            日历图标({'size':14}).渲染()
            界面.label(翻译('mark.aria',{'count':len(事实['records'])})).classes('visuallyHidden')

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
