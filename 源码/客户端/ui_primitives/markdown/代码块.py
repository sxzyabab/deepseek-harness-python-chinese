"""围栏/程序体/详情原文共用代码面。

对齐上游 `ui-primitives/src/markdown/CodeBlock.tsx`。公开面仅中文名。
高亮由宿主语法表完成；本组件产出 banner+原文材料。
"""
from ..复制反馈 import 复制反馈#复制反馈

__all__=['代码块']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 代码块:#代码面
    """尾换行仅作终止符；复制写 trimmed。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """banner+plain/highlighted 材料。"""
        属性=自身.属性#props
        代码=取字段(属性,'code') or ''#源
        修剪=代码[:-1] if 代码.endswith('\n') else 代码#剥终止
        语言=取字段(属性,'lang')#语法提示
        自身.反馈.置文本(修剪)#可复制
        return {#视图
            'type':'code-block',#类型
            'code':修剪,#源
            'lang':语言,#语言
            'html':None,#宿主高亮后填
            'copied':自身.反馈.已复制,#反馈
            'copyLabel':取字段(属性,'copyLabel','复制'),#闲
            'copiedLabel':取字段(属性,'copiedLabel','复制成功'),#成
            'onCopy':自身.反馈.复制,#复制
            'className':取字段(属性,'className'),#类
            'cssModule':'代码块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
