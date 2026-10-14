'按月翻页的日期格'
from nicegui import ui as 界面
from datetime import datetime as 日期时间
from .选择器弹出 import 选择器弹出

__all__=['日期选择']

def _解析(值):
    'YYYY-MM-DD'
    if not isinstance(值,str) or len(值)<10:
        return None
    try:
        return 日期时间.strptime(值[:10],'%Y-%m-%d')
    except ValueError:
        return None

class 日期选择:
    '父组件调用渲染。点日期把 YYYY-MM-DD 交给 onPick'
    def __init__(自身,属性=None):
        '记下当前月'
        自身.属性=属性 if isinstance(属性,dict) else {}
        解析=_解析(自身.属性['value'] if 'value' in 自身.属性 else '')
        基准=解析 if 解析 is not None else 日期时间.now()
        自身.年=基准.year
        自身.月=基准.month
        自身.打开=False

    def 更新(自身,属性):
        '刷新值，不重置已经翻到的月份'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按钮打开月历'
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('schedule-date')
        自身.重画()

    def 重画(自身):
        '月历在弹出层里'
        壳=自身._壳
        壳.clear()
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        值=属性['value'] if 'value' in 属性 and isinstance(属性['value'],str) else ''
        def 切换():
            '开合月历'
            自身.打开=not 自身.打开
            自身.重画()
        def 翻(步):
            '上一月或下一月'
            月=自身.月+步
            年=自身.年
            if 月<1:
                月=12
                年-=1
            elif 月>12:
                月=1
                年+=1
            自身.月=月
            自身.年=年
            自身.重画()
        def 选(日):
            '写成 ISO 日期'
            回调=属性['onPick'] if 'onPick' in 属性 else None
            if callable(回调):
                回调(f'{自身.年:04d}-{自身.月:02d}-{日:02d}')
            自身.打开=False
            自身.重画()
        def 格子():
            '本月每一天'
            with 界面.row():
                界面.button(翻译('timing.prevMonth'), on_click=lambda:翻(-1)).props('flat')
                界面.label(f'{自身.年}-{自身.月:02d}')
                界面.button(翻译('timing.nextMonth'), on_click=lambda:翻(1)).props('flat')
            首=日期时间(自身.年,自身.月,1)
            if 自身.月==12:
                下月=日期时间(自身.年+1,1,1)
            else:
                下月=日期时间(自身.年,自身.月+1,1)
            天数=(下月-首).days
            with 界面.row().style('flex-wrap:wrap;max-width:280px'):
                for 日 in range(1,天数+1):
                    界面.button(str(日), on_click=lambda 日=日:选(日)).props('flat')
        with 壳:
            界面.button(值 if 值!='' else 翻译('timing.date'), on_click=切换).props('outline')
            选择器弹出({'open':自身.打开,'label':翻译('timing.date'),'children':格子,'onClose':切换}).渲染()

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
