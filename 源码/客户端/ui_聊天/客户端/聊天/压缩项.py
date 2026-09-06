"""压缩落点标记行：披露摘要。

对齐上游 `ui-chat/src/client/chat/CompactionItem.tsx`。公开面仅中文名。
属性与节点为 dict。
"""

__all__=['压缩项']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 压缩项:
    """默认可折叠；无 summary 不可展开。"""
    def __init__(自身,属性=None):
        """记下 props 与展开。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已展开=False#展开

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        """可展开才翻。"""
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        if 'summary' not in 节点 or 节点['summary'] is None:#不可
            return#停
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        """标记行。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        标题=属性['title'] if 'title' in 属性 else None#命令题
        回退摘要=属性['fallbackSummary'] if 'fallbackSummary' in 属性 else None#回退
        可展='summary' in 节点 and 节点['summary'] is not None#可展
        打开=可展 is True and 自身.已展开 is True#开
        项数=节点['shadowedItemCount'] if 'shadowedItemCount' in 节点 else None#项
        令牌=节点['shadowedTokenCount'] if 'shadowedTokenCount' in 节点 else None#令牌
        if 项数 is not None and 令牌 is not None:#有计数
            摘要=翻译('message.compaction.completed',{'items':项数,'tokens':令牌})#完成
        elif 回退摘要 is not None:#回退
            摘要=回退摘要#回退
        elif 可展 is True:#可展
            摘要=翻译('message.compaction.expand')#展开提示
        else:#不可用
            摘要=翻译('message.compaction.unavailable')#不可用
        题出=标题 if 标题 is not None else 翻译('message.compaction')#题
        体=节点['summary'] if 打开 is True and 'summary' in 节点 else None#体
        return {'type':'compaction-item','title':题出,'summary':摘要,'expandable':可展,'open':打开,'body':体,'onToggle':自身.切换,'cssModule':'消息项.module.css'}#视图

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
