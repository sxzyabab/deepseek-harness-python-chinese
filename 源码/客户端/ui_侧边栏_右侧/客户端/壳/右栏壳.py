'右栏槽：main 的键是 conversation 时才画出 rightbar.session'

from nicegui import ui as 界面
from ...异常 import 异常原文

__all__=['右栏壳']

样式表='.右栏挂点{display:contents}.右栏会话{display:contents}'
界面.add_css(样式表,shared=True)

def 主面是会话(属性):
    '活动面板为空时，main 的键才是 conversation'
    用面板=属性['usePanelInfo'] if 'usePanelInfo' in 属性 else None
    if not callable(用面板):
        return True#直接打开的页面没有面板钩子，主栏只有会话
    def 选(信息):
        'activePanelId 恰为 None 才是会话界面'
        if isinstance(信息,dict):
            if 'activePanelId' not in 信息:
                return False
            return 信息['activePanelId'] is None
        if not hasattr(信息,'activePanelId'):
            return False
        return getattr(信息,'activePanelId') is None
    return 用面板(选) is True

def 读视图(属性):
    '会话视图表；钩子未就绪则为空'
    用视图=属性['useViews'] if 'useViews' in 属性 else None
    if not callable(用视图):
        return []
    值=用视图(lambda 快照:快照)
    if isinstance(值,(list,tuple)):
        return list(值)
    return []

class 右栏壳:
    'rightbar 槽。只在会话界面把当前会话交给 rightbar.session'

    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身._已挂=set()
        自身._已订=False
        自身._上次会话=None
        自身.根=None
        if 自身._键齐():
            自身.渲染()

    def _键齐(自身):
        '要能判断主面，并有视图和子槽'
        属性=自身.属性
        return (
            'usePanelInfo' in 属性 and callable(属性['usePanelInfo'])
            and 'useViews' in 属性 and callable(属性['useViews'])
            and 'renderSlot' in 属性 and callable(属性['renderSlot'])
        )

    def _订阅面板(自身):
        '主面键变化时重画。布局尺寸变化不重画。'
        if 自身._已订 is True:
            return
        用面板=自身.属性['usePanelInfo']
        订=getattr(用面板,'_subscribe',None)
        if not callable(订):
            return
        def 变更():
            '只在是否会话界面发生变化时重画'
            try:
                现在=主面是会话(自身.属性)
            except Exception as 错误:
                界面.label(异常原文(错误))
                return
            if 现在==自身._上次会话:
                return
            自身.重画()
        订(变更)
        自身._已订=True

    def 重画(自身):
        '清掉挂点里的旧席，再按当前主面画'
        if 自身.根 is not None:
            try:
                自身.根.clear()
            except Exception as 错误:
                界面.label(异常原文(错误))
                return
        自身.渲染()

    def 渲染(自身):
        '会话界面才画 rightbar.session。其它主面留空挂点。'
        自身._订阅面板()
        属性=自身.属性
        if 自身.根 is None:
            自身.根=界面.element('div').classes('右栏挂点')
        try:
            是会话=主面是会话(属性)
        except Exception as 错误:
            自身._上次会话=None
            with 自身.根:
                界面.label(异常原文(错误))
            return
        自身._上次会话=是会话
        if 是会话 is not True:
            return
        try:
            视图=读视图(属性)
        except Exception as 错误:
            with 自身.根:
                界面.label(异常原文(错误))
            return
        画=属性['renderSlot']
        提供=属性['SessionProvider'] if 'SessionProvider' in 属性 else None
        挂=属性['mountView'] if 'mountView' in 属性 else None
        with 自身.根:
            for 项 in 视图:
                if not isinstance(项,dict):
                    continue
                引用=项['reference'] if 'reference' in 项 else None
                标识=项['sessionId'] if 'sessionId' in 项 else None
                if callable(挂) and 引用 is not None and 标识 not in 自身._已挂:
                    try:
                        挂(引用)
                    except Exception as 错误:
                        界面.label(异常原文(错误))
                        continue
                    自身._已挂.add(标识)
                if 项.get('selected') is not True:
                    continue
                盒=界面.element('div').classes('右栏会话')
                if 标识 is not None:
                    盒.props('data-sidebar-right-session="'+str(标识).replace('"','')+'"')
                def 画席(钉项=项):
                    '把几何交给会话席。席在自己的构造里画出。'
                    画('rightbar.session',{
                        'width':属性['width'] if 'width' in 属性 else None,
                        'viewportWidth':属性['viewportWidth'] if 'viewportWidth' in 属性 else None,
                        'canShow':属性['canShow'] if 'canShow' in 属性 else True,
                        'active':True,
                        'retainTab':钉项['retainTab'] if 'retainTab' in 钉项 else None,
                    })
                with 盒:
                    try:
                        if callable(提供) and 引用 is not None:
                            提供({'session':引用,'children':画席})
                        else:
                            画席()
                    except Exception as 错误:
                        界面.label(异常原文(错误))

    def __call__(自身):
        '再画一次'
        自身.重画()
