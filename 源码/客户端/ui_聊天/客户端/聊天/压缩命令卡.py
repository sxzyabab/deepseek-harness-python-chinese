"""压缩命令卡：命令 + 压缩摘要。

对齐上游 `ui-chat/src/client/chat/CompactionCommandCard.tsx`。公开面仅中文名。
"""
from .压缩项 import 压缩项#压缩项
from .通用命令卡 import 通用命令卡#命令卡

__all__=['压缩命令卡']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 压缩命令卡:#手动压缩卡
    """命令卡叠压缩项。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.命令=通用命令卡()#命令
        自身.压缩=压缩项()#压缩

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """命令+压缩。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        数据=取字段(节点,'data') or 节点#数据
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        命令=取字段(数据,'command') or 数据#命令
        压缩=取字段(数据,'compaction')#压缩
        return {'type':'compaction-command-card','command':自身.命令({'node':命令,'t':翻译}),'compaction':自身.压缩({'node':压缩,'title':翻译('message.compaction.commandTitle'),'t':翻译}) if 压缩 else None}#卡

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
