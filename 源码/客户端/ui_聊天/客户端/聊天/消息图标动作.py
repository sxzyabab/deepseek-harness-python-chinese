"""消息 IconActions：时钟、分叉、运行时长。

对齐上游 `ui-chat/src/client/chat/MessageIconActions.tsx`。公开面仅中文名。
"""
from .消息铬 import 格式化消息时钟,格式化运行时长#时间标签
from .用日历日 import 用日历日#日席位

__all__=['消息图标动作']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 消息图标动作:#IconActions 行
    """时钟 + 可选分叉。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """动作行。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        时间=取字段(节点,'time') or 取字段(取字段(节点,'finalNode'),'time')#时间
        日=用日历日()#日席位（稳定时钟）
        时钟=格式化消息时钟(时间,翻译) if 时间 is not None else None#时钟
        分叉=取字段(属性,'forkAt')#分叉
        不可用=bool(取字段(属性,'branchUnavailable') or 取字段(节点,'branchUnavailable'))#不可用
        return {'type':'message-icon-actions','clock':时钟,'day':日,'ranFor':翻译('message.ranFor',{'duration':格式化运行时长(取字段(属性,'durationMs') or 0,翻译)}) if 取字段(属性,'durationMs') is not None else None,'branchLabel':翻译('message.branch'),'branchUnavailable':不可用,'branchHint':翻译('message.branchUnavailable') if 不可用 else None,'onBranch':(lambda:分叉(取字段(节点,'seq'))) if callable(分叉) and not 不可用 else None,'cssModule':'消息图标动作.module.css'}#行

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
