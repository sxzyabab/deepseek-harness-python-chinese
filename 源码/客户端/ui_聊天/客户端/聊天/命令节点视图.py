"""命令节点视图与手动压缩节点视图。

对齐上游 `ui-chat/src/client/chat/CommandNodeView.tsx`。公开面仅中文名。
属性与节点为 dict。
"""
from .回退命令卡 import 回退命令卡#回退卡
from .压缩命令卡 import 压缩命令卡#压缩卡

__all__=['命令节点视图','手动压缩节点视图']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 命令节点视图:
    """委托回退命令卡。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.卡=回退命令卡()#卡

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """命令。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        return 自身.卡({'node':数据,'t':翻译})#渲

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 手动压缩节点视图:
    """委托压缩命令卡。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.卡=压缩命令卡()#卡

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """手动压缩。"""
        return 自身.卡(自身.属性)#渲

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
