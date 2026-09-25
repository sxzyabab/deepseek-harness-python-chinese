"""分叉动作：一条会话菜单项。"""

__all__=['分叉会话菜单项']#仅中文公开名

class 分叉会话菜单项:#菜单 order 300
    """在会话最后完成轮次分叉；子会话经 Host 列表落在源旁。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """菜单行。"""
        属性=自身.属性#props
        快捷=属性['useShortcuts'](lambda 行表:next((行 for 行 in 行表 if 行['id']=='session.fork'),None))#快捷
        翻译=属性['t']#文案
        def 选定():
            """关菜单后分叉。"""
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            属性['forkSession'](属性['sessionId'])#分叉
        return {#菜单项
            'type':'MenuItemButton',#种类
            'shortcut':快捷,#快捷
            'icon':'IconBranchOutlineRegular',#图标
            'label':翻译('menu.fork'),#文案
            'onSelect':选定,#选定
        }#项结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
