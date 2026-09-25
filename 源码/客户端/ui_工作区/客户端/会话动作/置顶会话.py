"""置顶动作：会话菜单项与行悬停按钮，共用注入行为。
置顶与归档在 Host 互斥；已归档行不提供本动作。
"""

__all__=['读置顶态','置顶会话菜单项','置顶会话行按钮']#仅中文公开名

def 读置顶态(会话标识,用已置顶,用已归档):
    """行的置顶与归档成员，各一次 Set 查找。"""
    return {#态
        'pinned':用已置顶(lambda 集:会话标识 in 集),#已置顶
        'archived':用已归档(lambda 集:会话标识 in 集),#已归档
    }#态结束

class 置顶会话菜单项:#菜单 order 100
    """按当前态置顶或取消；已归档行返回 None。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """菜单行，或已归档时 None。"""
        属性=自身.属性#props
        态=读置顶态(属性['sessionId'],属性['usePinned'],属性['useArchived'])#态
        if 态['archived']:#已归档
            return None#不提供
        已钉=态['pinned']#钉
        翻译=属性['t']#文案
        def 选定():
            """关菜单后钉/取消。"""
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            (属性['unpinSession'] if 已钉 else 属性['pinSession'])(属性['sessionId'])#动作
        return {#菜单项
            'type':'MenuItemButton',#种类
            'icon':'IconPinFillRegular' if 已钉 else 'IconPinOutlineRegular',#图标
            'label':翻译('menu.unpinSession' if 已钉 else 'menu.pinSession'),#文案
            'onSelect':选定,#选定
        }#项结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 置顶会话行按钮:#悬停 order 200，最右
    """落在静止态钉标位置；已归档行返回 None。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """行按钮，或已归档时 None。"""
        属性=自身.属性#props
        态=读置顶态(属性['sessionId'],属性['usePinned'],属性['useArchived'])#态
        if 态['archived']:#已归档
            return None#不提供
        已钉=态['pinned']#钉
        翻译=属性['t']#文案
        def 点击():
            """钉/取消。"""
            (属性['unpinSession'] if 已钉 else 属性['pinSession'])(属性['sessionId'])#动作
        return {#按钮
            'type':'button','className':'iconButton',#钮
            'props':{#属性
                'aria-label':翻译('menu.unpinSession' if 已钉 else 'menu.pinSession'),#aria
                'title':翻译('actions.unpin' if 已钉 else 'actions.pin'),#tooltip
            },#属性结束
            'icon':'IconPinFillRegular' if 已钉 else 'IconPinOutlineRegular',#图标
            'iconSize':14,#尺寸
            'onClick':点击,#点击
        }#按钮结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
