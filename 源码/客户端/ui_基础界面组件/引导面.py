__all__=['引导面']#仅中文公开名

class 引导面:#引导接管铬
    """一步内容居中舞台；宿主负责 portal 与 inert。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """产出遮罩+舞台视图。"""
        属性=自身.属性#props
        return {#接管
            'type':'onboarding-surface',#类型
            'children':属性['children'] if 'children' in 属性 else None,#步骤内容
            'inertRoot':True,#挂载期 inert #root
            'portal':'body',#传送目标
            'cssModule':'引导面.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
