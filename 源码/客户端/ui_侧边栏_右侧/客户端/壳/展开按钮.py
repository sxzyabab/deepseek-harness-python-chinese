"""会话头角席展开钮：面板收起时的入口。

对齐上游 `ui-sidebar-right/src/client/shell/ExpandButton.tsx`。公开面仅中文名。
与面板共享每会话存储；展开时占位同尺寸，避免头栏跳动。
"""

__all__=['展开按钮','样式表']#仅中文公开名

样式表='''#对齐 ExpandButton.module.css
.placeholder{display:inline-block;flex:none;width:32px;height:32px}
.button{display:inline-flex;flex:none;align-items:center;justify-content:center;width:32px;height:32px;padding:0;color:var(--dsw-alias-label-secondary);background:transparent;border:none;border-radius:8px;cursor:pointer}
.button:hover{color:var(--dsw-alias-label-primary);background:var(--dsw-alias-interactive-bg-hover)}
.icon{transform:scaleX(-1)}
'''#样式表结束


class 展开按钮:#头栏角席展开控件
    """收起时按钮；展开时同尺寸占位。"""

    def __init__(自身,属性):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def _已展开(自身):
        """当前会话是否展开。"""
        属性=自身.属性#props
        会话=属性['sessionId']#会话
        用存储=属性['useStore']#选择器
        def 选(态):
            """读展开。"""
            表=态['bySession'] if 'bySession' in 态 else {}#表
            表面=表[会话] if 会话 in 表 else None#表面
            if 表面 is None:#尚未物化
                return False#收起
            return 表面['layout']['expanded'] is True#展开
        return 用存储(选) is True#布尔

    def 展开(自身):
        """请求展开。"""
        属性=自身.属性#props
        属性['actions']['setExpanded'](属性['sessionId'],True)#展开

    def 渲染(自身):
        """结构树。"""
        if 自身._已展开():#已开
            return {'type':'span','className':'placeholder','props':{'aria-hidden':True,'data-sidebar-right-expand-placeholder':True}}#占位
        翻译=自身.属性['t']#文案
        文=翻译('chrome.expand')#文案
        return {#按钮
            'type':'button',
            'className':'button',
            'props':{'aria-label':文,'title':文,'data-sidebar-right-expand':True},
            'onClick':自身.展开,
            'children':[{'type':'icon','className':'icon','props':{'name':'IconPanelLeftOutline16'}}],
        }#按钮结束
