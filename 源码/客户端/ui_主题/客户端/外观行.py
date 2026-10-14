from nicegui import ui as 界面

__all__=['外观行','样式表','立方顺序']

立方顺序=(
    {'id':'light','labelKey':'appearance.light','标':'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8.00007 11.8117C10.1052 11.8117 11.8117 10.1052 11.8117 8.00007C11.8117 5.89499 10.1052 4.18848 8.00007 4.18848C5.89499 4.18848 4.18848 5.89499 4.18848 8.00007C4.18848 10.1052 5.89499 11.8117 8.00007 11.8117Z" stroke="currentColor" stroke-width="1.3"/><path d="M13.3899 8H15.1499" stroke="currentColor" stroke-width="1.3"/><path d="M11.8115 11.8115L13.0556 13.0556" stroke="currentColor" stroke-width="1.3"/><path d="M8 13.3901V15.1501" stroke="currentColor" stroke-width="1.3"/><path d="M4.18868 11.8115L2.94458 13.0556" stroke="currentColor" stroke-width="1.3"/><path d="M2.6101 8H0.850098" stroke="currentColor" stroke-width="1.3"/><path d="M4.18868 4.18856L2.94458 2.94446" stroke="currentColor" stroke-width="1.3"/><path d="M8 2.6101V0.850098" stroke="currentColor" stroke-width="1.3"/><path d="M11.8115 4.18856L13.0556 2.94446" stroke="currentColor" stroke-width="1.3"/></svg>'},
    {'id':'dark','labelKey':'appearance.dark','标':'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M14.1127 8.70663C14.2576 8.60602 14.4627 8.71355 14.4386 8.88834C14.2901 9.96567 13.8731 10.9912 13.2229 11.8692C12.479 12.8735 11.4613 13.6421 10.2917 14.0829C9.1222 14.5236 7.85038 14.6179 6.62865 14.3543C5.40692 14.0907 4.28709 13.4805 3.40332 12.5967C2.51955 11.7129 1.90931 10.5931 1.64572 9.37135C1.38212 8.14962 1.47635 6.87779 1.91711 5.70825C2.35787 4.5387 3.12647 3.52103 4.13083 2.77714C5.00878 2.12689 6.03433 1.70994 7.11166 1.5614C7.28645 1.5373 7.39397 1.74238 7.29337 1.88734C6.68703 2.76099 6.37885 3.81241 6.42313 4.88345C6.47392 6.11194 6.98471 7.27645 7.85413 8.14587C8.72355 9.01529 9.88805 9.52608 11.1166 9.57687C12.1876 9.62114 13.239 9.31296 14.1127 8.70663Z" stroke="currentColor" stroke-width="1.3"/></svg>'},
    {'id':'system','labelKey':'appearance.system','标':'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M13.5 2.5H2.5C1.94772 2.5 1.5 2.94772 1.5 3.5V11.5C1.5 12.0523 1.94772 12.5 2.5 12.5H13.5C14.0523 12.5 14.5 12.0523 14.5 11.5V3.5C14.5 2.94772 14.0523 2.5 13.5 2.5Z" stroke="currentColor" stroke-width="1.3"/><path d="M5 14.5H11" stroke="currentColor" stroke-width="1.3"/></svg>'},
)

样式表='''
.外观组{display:flex;flex-direction:column;align-items:stretch;gap:8px;width:100%;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2)}
.外观标题{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.外观立方排{display:flex;flex-direction:row;align-items:stretch;gap:8px;flex-wrap:wrap;width:100%}
button.q-btn.外观立方{box-sizing:border-box;flex:1 1 180px;min-width:0;min-height:82px;padding:20px 32px;border:0.5px solid var(--dsw-alias-border-l4) !important;border-radius:var(--dsw-radius-xl);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:14px;line-height:22px}
button.q-btn.外观立方 .q-btn__content{flex-direction:column;align-items:center;justify-content:center;gap:4px;flex-wrap:nowrap}
button.q-btn.外观立方 svg{width:16px;height:16px;stroke-width:1.3}
button.q-btn.外观立方:hover:not(.外观选中){background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.外观立方.外观选中{background:var(--dsw-alias-bg-module-platform) !important;border-color:var(--dsw-static-neutral-bluish-400) !important}
'''

样式已登记=False

def 登记样式():
    '外观立方样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表, shared=True)
    样式已登记=True

class 外观行:
    '设置通用区外观行。槽位只调用构造'

    def __init__(自身,属性):
        '记下翻译、写偏好与 store 钩'
        自身.属性=属性
        if 't' in 属性 and 'setTheme' in 属性 and 'useStore' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 当前偏好(自身):
        '从 useStore 选择 preference'
        用存储=自身.属性['useStore']
        def 选偏好(快照):
            'preference'
            return 快照['preference']
        return 用存储(选偏好)

    def 渲染(自身):
        '画出外观立方'
        登记样式()
        翻译=自身.属性['t']
        设主题=自身.属性['setTheme']#注入面键名
        偏好=自身.当前偏好()
        with 界面.column().classes('外观组'):
            界面.label(翻译('appearance.title')).classes('外观标题')
            with 界面.element('div').classes('外观立方排'):
                for 项 in 立方顺序:
                    标识=项['id']
                    def 点击(选=标识):
                        '写入该偏好'
                        设主题(选)
                    钮=界面.button(on_click=点击).props('flat no-caps aria-pressed="'+('true' if 偏好==标识 else 'false')+'"').classes('外观立方').style('color: var(--dsw-alias-label-primary) !important')
                    with 钮:
                        界面.html(项['标'],sanitize=False)
                        界面.label(翻译(项['labelKey']))
                    if 偏好==标识:
                        钮.classes(add='外观选中')

    def __call__(自身,属性=None):
        '对齐 React 组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
