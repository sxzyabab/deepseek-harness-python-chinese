"""常规设置分区：叠放功能贡献的条目。

对齐上游 `ui-settings-general/src/client/GeneralSection.tsx`。公开面仅中文名。
"""

__all__=['常规条目分区','样式表']#仅中文公开名

样式表='''#对齐 GeneralSection.module.css
.section{display:flex;flex-direction:column;width:100%}
.section > :global([data-slot='settings.general.item']) > :last-child{border-bottom:none}
'''#样式表结束

class 常规条目分区:#常规设置条目列
    """一列渲染功能自有条目贡献。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出分区列。"""
        渲染槽=自身.属性['renderSlot']#子槽渲染
        条目=渲染槽('settings.general.item',{})#条目
        return {'type':'general-section','items':条目,'css':样式表}#视图

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
