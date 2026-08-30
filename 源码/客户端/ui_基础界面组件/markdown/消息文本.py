"""用户/转向字面文本原语；助手输出走 Markdown文本。

对齐上游 `ui-primitives/src/markdown/MessageText.tsx`。公开面仅中文名。
"""

__all__=['消息文本']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 消息文本:#字面文本
    """结构化视图。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """产出文本块。"""
        return {#视图
            'type':'message-text',#类型
            'text':取字段(自身.属性,'text') or '',#正文
            'cssModule':'消息文本.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
