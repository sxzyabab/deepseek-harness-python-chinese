"""按 form 解析上下文展开体。

对齐上游 `ui-chat/src/client/chat/ContextBody.tsx`。公开面仅中文名。
"""

__all__=['上下文体']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 上下文体:#展开体解析
    """按 form 选渲染形态；缺席不透明。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构
        """解析包：summary / body / rendered。"""
        属性=自身.属性#props
        形态=取字段(属性,'form')#form
        内容=取字段(属性,'content')#内容
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        摘要=''#摘要
        if isinstance(内容,list):#块
            摘要=''.join(取字段(块,'text') or '' for 块 in 内容 if 取字段(块,'type')=='text')[:80]#截
        elif isinstance(内容,str):#串
            摘要=内容[:80]#截
        return {'summary':摘要 or 翻译('message.extraBlock'),'body':内容,'rendered':形态 or 'opaque','form':形态,'cssModule':'上下文体.module.css'}#包

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
