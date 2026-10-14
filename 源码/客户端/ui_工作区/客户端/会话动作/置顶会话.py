'置顶动作：会话菜单项与行悬停按钮，共用注入行为'

from nicegui import ui as 界面

__all__=['读置顶态','置顶会话菜单项','置顶会话行按钮']#仅中文公开名

def 读置顶态(会话标识,用已置顶,用已归档):
    '行的置顶与归档成员，各一次 Set 查找'
    return {#态
        'pinned':用已置顶(lambda 集:会话标识 in 集),#已置顶
        'archived':用已归档(lambda 集:会话标识 in 集),#已归档
    }#态结束

class 置顶会话菜单项:#菜单 order 100
    '按当前态置顶或取消；已归档行返回 None'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        '菜单行；已归档不提供'
        属性=自身.属性#props
        if 'sessionId' not in 属性 or 'usePinned' not in 属性 or 'useArchived' not in 属性 or 't' not in 属性 or 'useMenuOpenState' not in 属性:
            return#缺席位
        态=读置顶态(属性['sessionId'],属性['usePinned'],属性['useArchived'])#态
        if 态['archived']:#已归档
            return#不提供
        已钉=态['pinned']#钉
        动作键='unpinSession' if 已钉 else 'pinSession'#钉或取消
        if 动作键 not in 属性:#无动作
            return
        翻译=属性['t']#文案
        def 选定():
            '关菜单后钉/取消'
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            属性[动作键](属性['sessionId'])#动作
        界面.button(翻译('menu.unpinSession' if 已钉 else 'menu.pinSession'), on_click=选定)

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

class 置顶会话行按钮:#悬停 order 200，最右
    '落在静止态钉标位置；已归档行返回 None'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        '行按钮；已归档不提供'
        属性=自身.属性#props
        if 'sessionId' not in 属性 or 'usePinned' not in 属性 or 'useArchived' not in 属性 or 't' not in 属性:
            return#缺席位
        态=读置顶态(属性['sessionId'],属性['usePinned'],属性['useArchived'])#态
        if 态['archived']:#已归档
            return#不提供
        已钉=态['pinned']#钉
        动作键='unpinSession' if 已钉 else 'pinSession'#钉或取消
        if 动作键 not in 属性:#无动作
            return
        翻译=属性['t']#文案
        def 点击():
            '钉/取消'
            属性[动作键](属性['sessionId'])#动作
        文=翻译('menu.unpinSession' if 已钉 else 'menu.pinSession')
        界面.button(文, on_click=点击).tooltip(翻译('actions.unpin' if 已钉 else 'actions.pin'))

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
