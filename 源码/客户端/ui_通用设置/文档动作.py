__all__=['文档动作','样式表']#仅中文公开名

from nicegui import ui as 界面

样式表='''#对齐 SettingsDocumentAction.module.css
.action{display:flex;min-width:0;align-items:center;gap:8px}
.error{max-width:180px;overflow:hidden;color:var(--dsw-alias-state-error-primary);font-size:12px;line-height:18px;text-overflow:ellipsis;white-space:nowrap}
'''#样式表结束

class 文档动作:
    '元数据确认有文档后才渲染'
    def __init__(自身,属性):
        '记下 props 并触发首读'
        自身.属性=属性#合成 props
        if 'controller' in 属性:
            属性['controller'].load()#首读
        if 't' in 自身.属性 and 'useSnapshot' in 自身.属性:#槽位份额齐了
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性#最新

    def 读状态(自身):
        '经 useSnapshot 选择器'
        用快照=自身.属性['useSnapshot']#选择器
        def 原样(快照):
            '整表'
            return 快照#快照
        return 用快照(原样)#快照

    def 渲染(自身):
        '未就绪不画'
        界面.add_css(样式表)
        翻译=自身.属性['t']#文案
        状态=自身.读状态()#状态
        if 状态['status']!='ready':#未就绪
            return#不渲染
        控制器=自身.属性['controller']#仓库
        def 打开文档():
            '调仓库 open'
            控制器.open()#打开
        with 界面.row().classes('action'):
            钮=界面.button(翻译('openDocument'), on_click=打开文档)
            if 状态['opening']:
                钮.disable()
            if 状态['error'] is not None:
                界面.label(翻译('openDocument.error')).classes('error')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
