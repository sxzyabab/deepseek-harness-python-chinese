'会话 Header 的下载菜单，以及可选的会话反馈'
from nicegui import ui as 界面
from .对话框 import 会话日志下载对话框,读下载

__all__=['会话日志下载页眉动作','快照仓']

样式表='''
button.q-btn.导出会话更多{width:28px;min-width:28px;height:28px;padding:0;color:var(--dsw-alias-label-secondary) !important;background:transparent !important;box-shadow:none !important}
.导出会话菜单{min-width:180px;padding:4px;background:var(--dsw-specific-menu);border-radius:var(--dsw-radius-lg);box-shadow:var(--dsw-elevation-prominent)}
button.q-btn.导出会话项{min-height:36px;padding:6px 10px;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:14px;justify-content:flex-start}
'''

界面.add_css(样式表,shared=True)

class 快照仓:
    'getSnapshot / set / subscribe；反馈插件是否仍在'
    def __init__(自身,初值):
        '记下初值'
        自身._状态=初值
        自身._监听=set()

    def getSnapshot(自身):
        '当前值'
        return 自身._状态

    def set(自身,次值):
        '写入并通知'
        自身._状态=次值
        for 监听 in list(自身._监听):
            监听()

    def subscribe(自身,监听):
        '返回退订'
        自身._监听.add(监听)
        def 退订():
            '去掉这一个监听'
            自身._监听.discard(监听)
        return 退订

def 读反馈(属性):
    '注入面 hooks.feedbackAvailable；缺键与显式 False 都是没有反馈项'
    钩=属性['hooks'] if 'hooks' in 属性 and 属性['hooks'] is not None else {}
    存储=钩['feedbackAvailable'] if isinstance(钩,dict) and 'feedbackAvailable' in 钩 else None
    if 存储 is not None:
        return 存储.getSnapshot() is True
    if 'useFeedbackAvailable' in 属性 and 属性['useFeedbackAvailable'] is not None:
        return 属性['useFeedbackAvailable'](lambda 值:值) is True
    return False

class 会话日志下载页眉动作:
    '更多菜单：下载会话日志，反馈插件在时多一项'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画'
        自身.属性=属性
        自身.已打开=False
        自身.对话框=会话日志下载对话框(属性)
        自身._画=None
        自身._已订阅=False
        if 'sessionId' in 属性 and 't' in 属性 and 'request' in 属性 and 'dismiss' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性
        自身.对话框.更新(属性)

    def 关菜单(自身):
        '收起菜单'
        自身.已打开=False

    def 刷新(自身):
        '菜单开关变化时重画'
        if 自身._画 is not None:
            自身._画.refresh()

    def 切菜单(自身):
        '开或关'
        自身.已打开=not 自身.已打开
        自身.刷新()

    def 条目(自身):
        '当前会话的下载条目'
        状态=读下载(自身.属性)
        按会话=状态['bySession'] if isinstance(状态,dict) and 'bySession' in 状态 and 状态['bySession'] is not None else {}
        标识=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None
        return 按会话[str(标识)] if str(标识) in 按会话 else None

    def 选中(自身,标识):
        '下载或打开反馈草稿'
        自身.已打开=False
        if 标识=='feedback':
            自身.属性['openFeedback'](自身.属性['sessionId'])
        else:
            自身.属性['request'](自身.属性['sessionId'])
        自身.刷新()

    def _画体(自身):
        '菜单按钮、菜单项和共享对话框'
        翻译=自身.属性['t']
        条目=自身.条目()
        忙碌=条目 is not None and 条目.get('status')=='downloading'
        项=[{'id':'download','label':翻译('menu.download'),'icon':'download','disabled':忙碌}]
        if 读反馈(自身.属性) is True:
            项.append({'id':'feedback','label':翻译('menu.feedback'),'icon':'send'})
        界面.button(icon='more_horiz', on_click=自身.切菜单).props('flat round').classes('导出会话更多').tooltip(翻译('header.more'))
        if 自身.已打开:
            with 界面.column().classes('导出会话菜单'):
                for 条 in 项:
                    def 点条(标识=条['id']):
                        '选中这一项'
                        自身.选中(标识)
                    图标=条['icon'] if 'icon' in 条 else None
                    钮=界面.button(条['label'], icon=图标, on_click=点条).props('flat no-caps align=left').classes('导出会话项')
                    if 'disabled' in 条 and 条['disabled'] is True:
                        钮.disable()
        自身.对话框.渲染()

    def 渲染(自身):
        '订阅下载与反馈可用性后再画'
        if 自身._画 is None:
            @界面.refreshable
            def 画():
                '状态变化时重画菜单和对话框'
                自身._画体()
            自身._画=画
        if not 自身._已订阅:
            自身._已订阅=True
            钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}
            for 名 in ('sessionLogDownload','feedbackAvailable'):
                存储=钩[名] if isinstance(钩,dict) and 名 in 钩 else None
                if 存储 is not None and hasattr(存储,'subscribe'):
                    存储.subscribe(lambda:自身._画.refresh())
        自身._画()

    def __call__(自身,属性=None):
        '对齐调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
