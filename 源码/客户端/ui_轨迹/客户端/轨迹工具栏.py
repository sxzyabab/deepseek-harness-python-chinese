import importlib.resources as 包资源
from nicegui import ui as 界面

__all__=['轨迹工具栏','样式表','样式文件']

样式文件='轨迹工具栏.module.css'

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except Exception:
        raise OSError('样式读不到') from None

样式表=_读样式(样式文件)
界面.add_css(样式表,shared=True)

def 缺省翻译(键,*_位置参数,**_关键字参数):
    '没有文案函数时原样返回键'
    return 键

class 轨迹工具栏:
    '时长开关、折叠轮次与调用、搜索。父级调用渲染，构造时不画'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '画出粘性工具栏'
        p=自身.属性
        翻译=p['t'] if 't' in p and p['t'] is not None else 缺省翻译
        实测=bool(p['actualDuration']) if 'actualDuration' in p else False
        实际时=bool(p['actualTime']) if 'actualTime' in p else False
        全轮折=bool(p['allTurnsCollapsed']) if 'allTurnsCollapsed' in p else False
        全助折=bool(p['allAssistantsCollapsed']) if 'allAssistantsCollapsed' in p else False
        查询=p['searchQuery'] if 'searchQuery' in p and p['searchQuery'] is not None else ''
        def 改时长(事件):
            '切换实测时长'
            回调=p['onActualDurationChange'] if 'onActualDurationChange' in p else None
            if 回调 is not None:
                回调(事件.value)
        def 改时间(事件):
            '切换实际时间'
            回调=p['onActualTimeChange'] if 'onActualTimeChange' in p else None
            if 回调 is not None:
                回调(事件.value)
        def 折轮():
            '折叠或展开全部轮次'
            回调=p['onToggleAllTurns'] if 'onToggleAllTurns' in p else None
            if 回调 is not None:
                回调()
        def 折调用():
            '折叠或展开全部调用'
            回调=p['onToggleAllAssistants'] if 'onToggleAllAssistants' in p else None
            if 回调 is not None:
                回调()
        def 改查询(事件):
            '写入搜索'
            回调=p['onSearchQueryChange'] if 'onSearchQueryChange' in p else None
            if 回调 is not None:
                回调(事件.value)
        with 界面.row().classes('trajectory-toolbar'):
            界面.label(翻译('toolbar.aria'))
            界面.switch(翻译('toolbar.useActualDuration') if 实测 else 翻译('toolbar.useEqualWidth'), value=实测, on_change=改时长)
            界面.switch(翻译('toolbar.actualTime'), value=实际时, on_change=改时间)
            界面.button(翻译('toolbar.collapseTurns') if 全轮折 else 翻译('toolbar.expandTurns'), on_click=折轮)
            界面.button(翻译('toolbar.collapseCalls') if 全助折 else 翻译('toolbar.expandCalls'), on_click=折调用)
            界面.input(翻译('toolbar.search'), value=查询, placeholder=翻译('toolbar.searchPlaceholder'), on_change=改查询)

    def __call__(自身,属性=None):
        '有新 props 先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
