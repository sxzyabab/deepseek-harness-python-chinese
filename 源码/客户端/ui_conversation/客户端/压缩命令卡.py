"""`/compact` 命令行与成功检查点披露。

对齐上游 `ui-conversation/src/client/chat/CompactionCommandCard.tsx`。公开面仅中文名。
无检查点的结果走通用命令卡。
"""
from .压缩项 import 压缩项#检查点标记
from .通用命令卡 import 通用命令卡#回退卡

__all__=['压缩命令卡']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 压缩命令卡:#手动压缩生命周期
    """有 compaction 则压缩项；否则通用卡。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.压缩视图=压缩项()#检查点
        自身.通用视图=通用命令卡()#回退

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """按是否有检查点分发。"""
        属性=自身.属性#props
        节点=取字段(属性,'node')#命令
        压缩=取字段(属性,'compaction')#检查点
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        if 压缩 is not None:#有检查点
            回退摘要=取字段(取字段(节点,'outcome'),'text') if 取字段(节点,'outcome') is not None else None#摘要
            return 自身.压缩视图({#压缩项
                'node':压缩,#节点
                'title':'compact',#标题
                'fallbackSummary':回退摘要,#回退
                't':翻译,#文案
            })#渲
        if 取字段(节点,'outcome') is not None:#已结
            return 自身.通用视图({'node':节点,'t':翻译})#通用
        return 自身.通用视图({#跑中
            'node':节点,#节点
            't':翻译,#文案
            'runningSummary':翻译('message.compaction.running'),#跑文
        })#渲

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
