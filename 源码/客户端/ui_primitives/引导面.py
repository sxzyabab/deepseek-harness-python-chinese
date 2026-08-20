"""首跑全视口接管面。

对齐上游 `ui-primitives/src/OnboardingSurface.tsx`。公开面仅中文名。
遮罩传送到 body；挂载期间把 #root 置 inert。
"""

__all__=['引导面']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 引导面:#引导接管铬
    """一步内容居中舞台；宿主负责 portal 与 inert。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """产出遮罩+舞台视图。"""
        属性=自身.属性#props
        return {#接管
            'type':'onboarding-surface',#类型
            'children':取字段(属性,'children'),#步骤内容
            'inertRoot':True,#挂载期 inert #root
            'portal':'body',#传送目标
            'cssModule':'引导面.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
