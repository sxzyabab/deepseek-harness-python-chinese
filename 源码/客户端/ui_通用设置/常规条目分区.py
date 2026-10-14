
__all__=['常规条目分区','样式表']#仅中文公开名

from nicegui import ui as 界面

样式表='''#对齐 GeneralSection.module.css
.section{display:flex;flex-direction:column;width:100%}
.section > :global([data-slot='settings.general.item']) > :last-child{border-bottom:none}
'''#样式表结束

class 常规条目分区:#常规设置条目列
    '一列渲染功能自有条目贡献'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        if 'renderSlot' in 自身.属性:#有子槽才画
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '画出分区列'
        界面.add_css(样式表)
        渲染槽=自身.属性['renderSlot']#子槽渲染
        with 界面.column().classes('section'):
            渲染槽('settings.general.item',{})#条目自己画

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
