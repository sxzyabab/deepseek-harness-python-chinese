"""命令节点视图与手动压缩节点视图。

对齐上游 `ui-chat/src/client/chat/CommandNodeView.tsx`。公开面仅中文名。
"""
from .通用命令卡 import 通用命令卡#通用卡
from .压缩命令卡 import 压缩命令卡#压缩卡

__all__=['命令节点视图','手动压缩节点视图']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 命令节点视图:#command 键
    """委托通用命令卡。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.卡=通用命令卡()#卡

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构
        """命令。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        return 自身.卡({'node':取字段(节点,'data') or 节点,'t':取字段(属性,'t',lambda 键,_=None:键)})#渲

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 手动压缩节点视图:#manual-compaction 键
    """委托压缩命令卡。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.卡=压缩命令卡()#卡

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构
        """手动压缩。"""
        return 自身.卡(自身.属性)#渲

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
