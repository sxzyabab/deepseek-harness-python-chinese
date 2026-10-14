from nicegui import ui as 界面
from ..主题设置 import 字号规格#各角色字号边界

__all__=['字号行','样式表']

样式表='''
.字号条{display:flex;align-items:center;gap:8px;width:100%;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2);flex-wrap:nowrap}
.字号文{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.字号标题{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.字号说明{font-size:12px;font-weight:400;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.字号控{display:inline-flex;align-items:center;gap:8px;flex:none}
.字号丸{position:relative;display:inline-flex;align-items:center;justify-content:center;min-width:72px;height:36px;border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-module-platform)}
.字号值{min-width:18px;text-align:center;font-size:14px;line-height:22px;font-variant-numeric:tabular-nums;color:var(--dsw-alias-label-primary)}
.字号单位{font-size:14px;line-height:22px;color:var(--dsw-alias-label-secondary)}
.字号箭{position:absolute;right:8px;display:flex;flex-direction:column;gap:2px;opacity:0}
.字号丸:hover .字号箭,.字号丸:focus-within .字号箭{opacity:1}
button.q-btn.字号钮{width:17px;min-width:17px;height:12px;min-height:12px;padding:0;border-radius:var(--dsw-radius-xs);background:color-mix(in srgb, var(--dsw-alias-bg-layer-1) 75%, transparent) !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important;font-size:8px;line-height:12px}
button.q-btn.字号钮:hover{background:var(--dsw-alias-bg-layer-1) !important}
button.q-btn.字号更多{width:28px;min-width:28px;height:28px;min-height:28px;padding:0;border-radius:var(--dsw-radius-sm);background:transparent !important;color:var(--dsw-alias-label-secondary) !important;box-shadow:none !important}
button.q-btn.字号更多.字号更多开{transform:rotate(180deg)}
'''

样式已登记=False

def 登记样式():
    '字号行样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表, shared=True)
    样式已登记=True

class 字号行:
    '通用区字号行；显示已持久化字号。字体设置组调用渲染，构造不画'
    def __init__(自身,属性):
        '记下翻译、写字号与 store 钩'
        自身.属性=属性

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 角色(自身):
        '缺省改正文'
        角色=自身.属性.get('role')
        if 角色 in 字号规格:
            return 角色
        return 'text'

    def 当前字号(自身):
        '优先读 fontSizes，否则读旧的 fontSize'
        用存储=自身.属性['useStore']
        角色=自身.角色()
        def 选字号(快照):
            '该角色的 px'
            分角色=快照.get('fontSizes') if isinstance(快照,dict) else None
            if isinstance(分角色,dict) and 角色 in 分角色:
                return 分角色[角色]
            return 快照['fontSize']
        return 用存储(选字号)

    def 文案键(自身,翻译,后缀):
        '分角色键没有词条时退回旧的单字号键'
        角色=自身.角色()
        键='fontSize.'+角色+'.'+后缀
        if 翻译(键)==键:
            return 'fontSize.'+后缀
        return 键

    def 渲染(自身):
        '画出字号步进；正文行可带展开更多字体的按钮'
        登记样式()
        翻译=自身.属性['t']
        设字号=自身.属性['setFontSize']
        角色=自身.角色()
        规格=字号规格[角色]
        字号=自身.当前字号()
        def 增大():
            '加一'
            设字号(字号+1)
        def 减小():
            '减一'
            设字号(字号-1)
        with 界面.element('div').classes('字号条'):
            with 界面.element('div').classes('字号文'):
                界面.label(翻译(自身.文案键(翻译,'title'))).classes('字号标题')
                界面.label(翻译(自身.文案键(翻译,'description'))).classes('字号说明')
            with 界面.element('div').classes('字号控'):
                with 界面.element('div').classes('字号丸'):
                    界面.label(str(字号)).classes('字号值')
                    with 界面.column().classes('字号箭'):
                        加钮=界面.button('▲', on_click=增大).props('flat no-caps aria-label="'+翻译(自身.文案键(翻译,'increase'))+'"').classes('字号钮').style('color: var(--dsw-alias-label-primary) !important')
                        减钮=界面.button('▼', on_click=减小).props('flat no-caps aria-label="'+翻译(自身.文案键(翻译,'decrease'))+'"').classes('字号钮').style('color: var(--dsw-alias-label-primary) !important')
                        if 字号>=规格['max']:
                            加钮.disable()
                        if 字号<=规格['min']:
                            减钮.disable()
                界面.label(翻译('fontSize.unit')).classes('字号单位')
                展开=自身.属性.get('expander')
                if isinstance(展开,dict):
                    def 点展开():
                        '切换更多字体区域'
                        展开['onToggle']()
                        开=展开.get('open') is True
                        更多钮.props('flat no-caps aria-label="'+翻译('fontSize.more')+'" title="'+翻译('fontSize.more')+'" aria-expanded='+('true' if 开 else 'false')+' aria-controls='+str(展开.get('controls') or ''))
                        if 开:
                            更多钮.classes(add='字号更多开')
                        else:
                            更多钮.classes(remove='字号更多开')
                    更多钮=界面.button('▾', on_click=点展开).props('flat no-caps aria-label="'+翻译('fontSize.more')+'" title="'+翻译('fontSize.more')+'" aria-expanded=false aria-controls='+str(展开.get('controls') or '')).classes('字号更多')

    def __call__(自身,属性=None):
        '对齐 React 组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
