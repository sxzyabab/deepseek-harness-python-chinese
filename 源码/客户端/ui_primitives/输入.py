"""单行输入原子。

对齐上游 `ui-primitives/src/Input.tsx`。公开面仅中文名。
Composer 文本域不在此；本原子用于搜索框与行内表单。
"""

__all__=['输入']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 输入:#文本输入
    """可选前导图标的单行输入。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """包装+原生 input 属性透传。"""
        属性=自身.属性#props
        透传={键:值 for 键,值 in 属性.items() if 键 not in ('icon','className')}#透传
        return {#输入
            'type':'input',#类型
            'icon':取字段(属性,'icon'),#图标
            'className':取字段(属性,'className'),#类
            'inputProps':透传,#原生属性
            'cssModule':'输入.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
