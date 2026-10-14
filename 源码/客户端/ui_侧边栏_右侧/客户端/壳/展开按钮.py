
__all__=['展开按钮','样式表']#仅中文公开名

from nicegui import ui as 界面

样式表='''#对齐 ExpandButton.module.css
.placeholder{display:inline-block;flex:none;width:32px;height:32px}
.button{display:inline-flex;flex:none;align-items:center;justify-content:center;width:32px;height:32px;padding:0;color:var(--dsw-alias-label-secondary);background:transparent;border:none;border-radius:8px;cursor:pointer}
button.q-btn.button{width:32px;height:32px;min-height:32px;padding:0;color:var(--dsw-alias-label-secondary) !important;background:transparent !important;box-shadow:none !important}
.button:hover,button.q-btn.button:hover{color:var(--dsw-alias-label-primary) !important;background:var(--dsw-alias-interactive-bg-hover) !important}
.icon{display:inline-flex;transform:scaleX(-1)}
'''#样式表结束

界面.add_css(样式表,shared=True)

面板标记='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M13.5 1.5H2.5C1.94772 1.5 1.5 1.94772 1.5 2.5V13.5C1.5 14.0523 1.94772 14.5 2.5 14.5H13.5C14.0523 14.5 14.5 14.0523 14.5 13.5V2.5C14.5 1.94772 14.0523 1.5 13.5 1.5Z" stroke="currentColor" stroke-width="1"/><path d="M5.5 1.5V14.5" stroke="currentColor" stroke-width="1"/></svg>'#左栏图标，镜像后指向右栏


class 展开按钮:#头栏角席展开控件
    '收起时按钮；展开时同尺寸占位'

    def __init__(自身,属性):
        '记下合成 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if 属性 is not None else {}#props
        if 'sessionId' in 自身.属性 and 'useStore' in 自身.属性 and 't' in 自身.属性 and 'actions' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#最新

    def _已展开(自身):
        '当前会话是否展开'
        属性=自身.属性#props
        会话=属性['sessionId']#会话
        用存储=属性['useStore']#选择器
        def 选(态):
            '读展开'
            表=态['bySession'] if 'bySession' in 态 else {}#表
            表面=表[会话] if 会话 in 表 else None#表面
            if 表面 is None:#尚未物化
                return False#收起
            return 表面['layout']['expanded'] is True#展开
        return 用存储(选) is True#布尔

    def 展开(自身):
        '请求展开'
        属性=自身.属性#props
        属性['actions']['setExpanded'](属性['sessionId'],True)#展开

    def 渲染(自身):
        '收起时画镜像面板按钮；展开时同尺寸占位'
        属性=自身.属性#props
        if 'sessionId' not in 属性 or 'useStore' not in 属性 or 't' not in 属性 or 'actions' not in 属性:#份额未齐
            return
        if 自身._已展开():#已开
            界面.element('span').classes('placeholder')#占位
            return#收起钮不出现
        翻译=属性['t']#文案
        名=翻译('chrome.expandAria')#无障碍名
        钮=界面.button(on_click=自身.展开).classes('button').props('flat dense aria-label="'+名+'" title="'+翻译('chrome.expand')+'"')#按钮
        钮.props('data-sidebar-right-expand')#标记
        with 钮:#镜像图标
            界面.html(面板标记,sanitize=False).classes('icon')#面板标
