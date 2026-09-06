"""消息 IconActions：时钟、分叉、运行时长。

对齐上游 `ui-chat/src/client/chat/MessageIconActions.tsx`。公开面仅中文名。
属性与节点为 dict。
"""
from .消息铬 import 格式化消息时钟,格式化运行时长#时间标签
from .用日历日 import 用日历日#日席位

__all__=['消息图标动作']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 消息图标动作:
    """时钟 + 可选分叉。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """动作行。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        时间=节点['time'] if 'time' in 节点 else None#时间
        if 时间 is None and 'finalNode' in 节点 and 节点['finalNode'] is not None:#定稿时间
            终=节点['finalNode']#定稿
            时间=终['time'] if 'time' in 终 else None#时间
        日=用日历日()#日席位（稳定时钟）
        时钟=格式化消息时钟(时间,翻译) if 时间 is not None else None#时钟
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        属不可=属性['branchUnavailable'] if 'branchUnavailable' in 属性 else None#属不可
        节不可=节点['branchUnavailable'] if 'branchUnavailable' in 节点 else None#节不可
        不可用=属不可 is True or 节不可 is True#不可用
        时长=属性['durationMs'] if 'durationMs' in 属性 else None#时长
        运行=翻译('message.ranFor',{'duration':格式化运行时长(时长 if 时长 is not None else 0,翻译)}) if 时长 is not None else None#运行
        序号=节点['seq'] if 'seq' in 节点 else None#序号
        def 点分叉():
            """分叉到该序号。"""
            分叉(序号)#分叉
        可分=分叉 is not None and 不可用 is False#可分
        return {'type':'message-icon-actions','clock':时钟,'day':日,'ranFor':运行,'branchLabel':翻译('message.branch'),'branchUnavailable':不可用,'branchHint':翻译('message.branchUnavailable') if 不可用 is True else None,'onBranch':点分叉 if 可分 is True else None,'cssModule':'消息图标动作.module.css'}#行

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
