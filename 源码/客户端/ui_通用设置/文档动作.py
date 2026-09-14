__all__=['文档动作','样式表']#仅中文公开名

样式表='''#对齐 SettingsDocumentAction.module.css
.action{display:flex;min-width:0;align-items:center;gap:8px}
.error{max-width:180px;overflow:hidden;color:var(--dsw-alias-state-error-primary);font-size:12px;line-height:18px;text-overflow:ellipsis;white-space:nowrap}
'''#样式表结束

class 文档动作:
    """元数据确认有文档后才渲染。"""
    def __init__(自身,属性):
        """记下 props 并触发首读。"""
        自身.属性=属性#合成 props
        属性['controller'].load()#首读

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性#最新

    def 读状态(自身):
        """经 useSnapshot 选择器。"""
        用快照=自身.属性['useSnapshot']#选择器
        def 原样(快照):
            """整表。"""
            return 快照#快照
        return 用快照(原样)#快照

    def 渲染(自身):
        """未就绪返回 None。"""
        翻译=自身.属性['t']#文案
        状态=自身.读状态()#状态
        if 状态['status']!='ready':#未就绪
            return None#不渲染
        控制器=自身.属性['controller']#仓库
        def 打开文档():
            """调仓库 open。"""
            控制器.open()#打开
        return {#视图
            'type':'settings-document-action',#类型
            'error':None if 状态['error'] is None else 翻译('openDocument.error'),#错误文案
            'opening':状态['opening'],#打开中
            'label':翻译('openDocument'),#按钮文案
            'onOpen':打开文档,#打开
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
