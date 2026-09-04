"""压缩落点标记行：披露摘要。

对齐上游 `ui-chat/src/client/chat/CompactionItem.tsx`。公开面仅中文名。
"""

__all__=['压缩项']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 压缩项:#compaction 流标记
    """默认可折叠；无 summary 不可展开。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与展开。"""
        自身.属性=属性 or {}#合成
        自身.已展开=False#展开

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 切换(自身):#展开切换
        """可展开才翻。"""
        节点=取字段(自身.属性,'node') or {}#节点
        if 取字段(节点,'summary') is None:#不可
            return#停
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):#结构树
        """标记行。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        标题=取字段(属性,'title')#命令题
        回退摘要=取字段(属性,'fallbackSummary')#回退
        可展=取字段(节点,'summary') is not None#可展
        打开=可展 and 自身.已展开#开
        项数=取字段(节点,'shadowedItemCount')#项
        令牌=取字段(节点,'shadowedTokenCount')#令牌
        if 项数 is not None and 令牌 is not None:#有计数
            摘要=翻译('message.compaction.completed',{'items':项数,'tokens':令牌})#完成
        elif 回退摘要 is not None:#回退
            摘要=回退摘要#回退
        elif 可展:#可展
            摘要=翻译('message.compaction.expand')#展开提示
        else:#不可用
            摘要=翻译('message.compaction.unavailable')#不可用
        return {'type':'compaction-item','title':标题 if 标题 is not None else 翻译('message.compaction'),'summary':摘要,'expandable':可展,'open':打开,'body':取字段(节点,'summary') if 打开 else None,'onToggle':自身.切换,'cssModule':'消息项.module.css'}#视图

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
