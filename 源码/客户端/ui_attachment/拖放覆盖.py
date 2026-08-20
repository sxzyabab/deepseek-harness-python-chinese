"""全页拖放邀请覆盖。



对齐上游 `ui-attachment/src/DropOverlay.tsx`。公开面仅中文名。

装饰层：不抢指针；禁用时去掉说明行。

"""



__all__=['拖放覆盖']#仅中文公开名



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



class 拖放覆盖:#全视口拖放邀请

    """文件拖到页面上方时的邀请层。"""

    def __init__(自身,属性):#构造

        """记下 props。"""

        自身.属性=属性#合成 props



    def 更新(自身,属性):#props 变更

        """刷新。"""

        自身.属性=属性#最新



    def 卸载(自身):#卸载

        """无状态。"""

        return#空



    def 视图(自身):#读视图模型

        """投影标题与说明。"""

        文案=取字段(自身.属性,'labels') or {}#文案

        禁用=bool(取字段(自身.属性,'disabled'))#禁用

        return {#视图

            'disabled':禁用,#禁用

            'title':取字段(文案,'title'),#标题

            'desc':None if 禁用 else 取字段(文案,'desc'),#说明

            'illustration':'disabled' if 禁用 else 'upload',#插图键

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


