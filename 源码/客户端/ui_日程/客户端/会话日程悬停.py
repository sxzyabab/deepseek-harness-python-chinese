'会话行悬停卡里的活动任务，最多两条'
from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ..异常 import 页面失败文案
from .日历图标 import 日历图标
from .会话日程状态 import 会话悬停上限,选取会话日程事实
from .日程格式 import 格式化日程频率,下次运行片段,排序日程记录,任务名
from . import 标记样式

__all__=['会话日程悬停','会话悬停上限']

def 缺省翻译(键,_参数=None):
    '无文案席时回传键'
    return 键

class 会话日程悬停:
    '槽位只调用构造。时钟在挂上时取一次'
    def __init__(自身,属性=None):
        '记下时刻。键齐了才在构造末尾画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.现在=当前毫秒()
        自身._已订=False
        自身._绘制中=False
        自身._待重画=False
        if 'sessionId' in 自身.属性 and 'useCatalog' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保订阅(自身):
        '目录变化时重画悬停段'
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
        '先占壳。悬停样式与标记共用模块顶层登记。'
        标记样式.样式表
        自身._绘制中=True
        try:
            自身.确保订阅()
            if getattr(自身,'_壳',None) is None:
                自身._壳=界面.column().classes('日程标记根 tasks')
            自身.重画()
        finally:
            自身._绘制中=False
        if 自身._待重画:
            自身._待重画=False
            自身.重画()

    def 重画(自身):
        '名称、频率和下次运行。没有活动任务时留空。'
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
            # 目录读失败时悬停卡不列出任务，说明里不留路径
            页面失败文案(原因)
            壳.style('display:none')
            return
        事实=选取会话日程事实(快照,属性['sessionId'] if 'sessionId' in 属性 else None)
        if 事实['hasActive'] is not True:
            壳.style('display:none')
            return
        壳.style('display:flex')
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else 缺省翻译
        排序=排序日程记录(事实['records'],自身.现在)
        展示=排序[:会话悬停上限]
        其余=len(排序)-len(展示)
        with 壳:
            for 记录 in 展示:
                计划于=记录['scheduledAt'] if isinstance(记录,dict) and 'scheduledAt' in 记录 else ''
                片段=下次运行片段(计划于,翻译('time.locale'),自身.现在,翻译)
                with 界面.element('div').classes('task'):
                    with 界面.element('span').classes('taskIcon'):
                        日历图标({'size':12}).渲染()
                    with 界面.element('span').classes('taskBody'):
                        界面.label(任务名(记录)).classes('taskName')
                        with 界面.element('span').classes('taskTiming'):
                            界面.label(格式化日程频率(记录,翻译)+' · '+片段['absolute']+' ')
                            界面.label(片段['relative']).classes('taskRelative')
            if 其余>0:
                界面.label(翻译('hover.more',{'count':其余})).classes('omitted')

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
